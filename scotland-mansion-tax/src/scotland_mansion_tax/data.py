"""
Data loading and downloading module.

Handles:
- Council Tax Band H data from NRS dwelling estimates (aggregated from Data Zone level)
- Data Zone to Constituency mapping via SSPL (Scottish Statistics Postcode Lookup)
- NRS constituency population data
- Wealth factor calculations based on actual Band H (best proxy for £1m+ properties)
"""

import json
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Dict
from zipfile import ZipFile

import pandas as pd

# URLs for data sources
NRS_DWELLING_URL = (
    "https://www.nrscotland.gov.uk/media/bhjk5m00/dwelling-est-by-2011-dz-05-24.xlsx"
)
SSPL_URL = "https://www.nrscotland.gov.uk/media/rpvjxnpv/sspl-2025-2.zip"
MAPIT_SPC_URL = "https://mapit.mysociety.org/areas/SPC"


def get_data_dir() -> Path:
    """Get the data directory, creating if necessary.

    Searches in order:
    1. ./data (relative to current working directory)
    2. Package installation directory (for installed packages)
    """
    cwd_data = Path.cwd() / "data"
    if cwd_data.exists():
        return cwd_data

    pkg_data = Path(__file__).parent.parent.parent.parent / "data"
    if pkg_data.exists():
        return pkg_data

    cwd_data.mkdir(exist_ok=True)
    return cwd_data


def download_dwelling_estimates(data_dir: Path = None, verbose: bool = True) -> bool:
    """Download NRS dwelling estimates by Data Zone.

    Contains Council Tax Band A-H counts for each of Scotland's ~7,000 Data Zones.
    This is the source for actual Band H data (not available pre-aggregated at
    constituency level).

    Source: National Records of Scotland - Small Area Statistics 2024
    https://www.nrscotland.gov.uk/publications/small-area-statistics-on-households-and-dwellings-2024/

    Args:
        data_dir: Directory to save data to. Defaults to package data dir.
        verbose: Print progress messages.

    Returns:
        True if download succeeded, False otherwise.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    output_file = data_dir / "dwelling_estimates_by_dz.xlsx"

    if verbose:
        print("   Downloading NRS dwelling estimates (~16 MB)...")

    try:
        req = urllib.request.Request(
            NRS_DWELLING_URL,
            headers={"User-Agent": "scotland-mansion-tax/1.0"},
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            data = response.read()
        output_file.write_bytes(data)
        if verbose:
            print(f"   ✓ Downloaded dwelling estimates ({len(data) / 1e6:.1f} MB)")
        return True
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Download failed: {e}")
        return False


def download_dz_lookup(data_dir: Path = None, verbose: bool = True) -> bool:
    """Download SSPL for Data Zone to Constituency mapping.

    The Scottish Statistics Postcode Lookup (SSPL) contains mappings from
    postcodes to various geographies including Data Zones and Scottish
    Parliament Constituencies. We extract the unique DZ → Constituency mapping.

    Source: National Records of Scotland - SSPL 2025/2
    https://www.nrscotland.gov.uk/publications/scottish-statistics-postcode-lookup-20252/

    Args:
        data_dir: Directory to save data to. Defaults to package data dir.
        verbose: Print progress messages.

    Returns:
        True if download succeeded, False otherwise.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    lookup_file = data_dir / "dz_to_constituency_lookup.csv"

    if verbose:
        print("   Downloading SSPL postcode lookup (~95 MB compressed)...")

    try:
        req = urllib.request.Request(
            SSPL_URL,
            headers={"User-Agent": "scotland-mansion-tax/1.0"},
        )
        with urllib.request.urlopen(req, timeout=180) as response:
            zip_data = BytesIO(response.read())

        with ZipFile(zip_data) as zf:
            with zf.open("singlerecord.csv") as f:
                df = pd.read_csv(
                    f,
                    usecols=[
                        "DataZone2011Code",
                        "ScottishParliamentaryConstituency2021Code",
                    ],
                )

        # Get unique DZ to Constituency mappings
        lookup = df.drop_duplicates().dropna()
        lookup.columns = ["DataZone", "ConstituencyCode"]
        lookup.to_csv(lookup_file, index=False)

        if verbose:
            print(f"   ✓ Extracted {len(lookup)} Data Zone → Constituency mappings")
        return True
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Download failed: {e}")
        return False


def download_constituency_names(data_dir: Path = None, verbose: bool = True) -> bool:
    """Download constituency names from MapIt API.

    MapIt (by mySociety) provides a mapping from GSS codes to constituency names.

    Source: https://mapit.mysociety.org/

    Args:
        data_dir: Directory to save data to. Defaults to package data dir.
        verbose: Print progress messages.

    Returns:
        True if download succeeded, False otherwise.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    names_file = data_dir / "constituency_names.csv"

    if verbose:
        print("   Downloading constituency names from MapIt...")

    try:
        req = urllib.request.Request(
            MAPIT_SPC_URL,
            headers={"Accept": "application/json", "User-Agent": "scotland-mansion-tax/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        constituencies = []
        for area_id, info in data.items():
            code = info.get("codes", {}).get("gss", "")
            name = info.get("name", "")
            if code.startswith("S16"):
                constituencies.append({"Code": code, "Name": name})

        df = pd.DataFrame(constituencies)
        df.to_csv(names_file, index=False)

        if verbose:
            print(f"   ✓ Downloaded {len(df)} constituency names")
        return True
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Download failed: {e}")
        return False


def load_wealth_factors(
    data_dir: Path = None, verbose: bool = True
) -> Dict[str, float]:
    """Load wealth factors from Council Tax Band H data.

    Band H (>£212k in 1991, ~>£1.06m in 2024) is the best proxy for £1m+ properties.

    Data sources:
    - NRS Small Area Statistics 2024: Dwelling estimates by 2011 Data Zone
    - SSPL 2025/2: Data Zone to Constituency lookup

    Args:
        data_dir: Directory containing data files. Defaults to package data dir.
        verbose: Print progress messages.

    Returns:
        Dict mapping constituency name -> wealth factor.

    Raises:
        RuntimeError: If required data files cannot be downloaded.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    dwelling_file = data_dir / "dwelling_estimates_by_dz.xlsx"
    lookup_file = data_dir / "dz_to_constituency_lookup.csv"
    names_file = data_dir / "constituency_names.csv"

    # Download missing files - fail if unavailable
    if not dwelling_file.exists():
        if verbose:
            print("   Dwelling estimates not found locally.")
        if not download_dwelling_estimates(data_dir, verbose):
            raise RuntimeError(
                "Failed to download NRS dwelling estimates.\n"
                "This data is required for wealth-adjusted analysis.\n\n"
                "Please run 'scotland-mansion-tax download --all' or download manually from:\n"
                f"  {NRS_DWELLING_URL}"
            )

    if not lookup_file.exists():
        if verbose:
            print("   Data Zone lookup not found locally.")
        if not download_dz_lookup(data_dir, verbose):
            raise RuntimeError(
                "Failed to download Data Zone lookup.\n"
                "This data is required for wealth-adjusted analysis.\n\n"
                "Please run 'scotland-mansion-tax download --all' or download manually from:\n"
                f"  {SSPL_URL}"
            )

    if not names_file.exists():
        download_constituency_names(data_dir, verbose)  # Optional, just for display

    if verbose:
        print("   Loading Band H data from NRS dwelling estimates...")

    # Load 2023 dwelling data with Band H counts
    df = pd.read_excel(dwelling_file, sheet_name="2023", header=4)
    df.columns = df.columns.str.replace("\n", " ").str.strip()

    dz_data = df[
        ["Data Zone code", "Total number of dwellings", "Council Tax band: H"]
    ].copy()
    dz_data.columns = ["DataZone", "TotalDwellings", "BandH"]
    dz_data = dz_data.dropna(subset=["DataZone"])

    # Load DZ to Constituency lookup
    lookup = pd.read_csv(lookup_file)

    # Merge and aggregate to constituency level
    merged = dz_data.merge(lookup, on="DataZone", how="left")

    constituency_data = merged.groupby("ConstituencyCode").agg(
        {"TotalDwellings": "sum", "BandH": "sum"}
    ).reset_index()

    # Calculate Scotland averages and wealth factors
    scotland_band_h = constituency_data["BandH"].sum()
    scotland_total = constituency_data["TotalDwellings"].sum()
    scotland_avg_pct = scotland_band_h / scotland_total

    if verbose:
        print(
            f"   Scotland Band H: {scotland_band_h:,} properties "
            f"({scotland_avg_pct * 100:.2f}% of {scotland_total:,} dwellings)"
        )

    # Load constituency names - needed for output keys
    if names_file.exists():
        names = pd.read_csv(names_file)
        name_lookup = dict(zip(names["Code"], names["Name"]))
    else:
        name_lookup = {}

    # Calculate wealth factors (keyed by constituency NAME for compatibility with analysis.py)
    wealth_factors = {}
    for _, row in constituency_data.iterrows():
        pct = row["BandH"] / row["TotalDwellings"] if row["TotalDwellings"] > 0 else 0
        factor = pct / scotland_avg_pct if scotland_avg_pct > 0 else 1.0
        code = row["ConstituencyCode"]
        # Use name if available, fall back to code
        name = name_lookup.get(code, code)
        wealth_factors[name] = round(factor, 2)

    if verbose:
        # Create reverse lookup (name -> code) for accessing constituency_data
        code_lookup = {v: k for k, v in name_lookup.items()}
        sorted_factors = sorted(wealth_factors.items(), key=lambda x: x[1], reverse=True)
        print("   Top 5 by Band H concentration (actual £1m+ proxy):")
        for name, factor in sorted_factors[:5]:
            code = code_lookup.get(name, name)
            rows = constituency_data[constituency_data["ConstituencyCode"] == code]
            if len(rows) > 0:
                row = rows.iloc[0]
                pct = row["BandH"] / row["TotalDwellings"] * 100
                print(f"      {name}: {factor:.2f}x ({pct:.2f}% Band H)")

        print("   Bottom 3 by Band H concentration:")
        for name, factor in sorted_factors[-3:]:
            code = code_lookup.get(name, name)
            rows = constituency_data[constituency_data["ConstituencyCode"] == code]
            if len(rows) > 0:
                row = rows.iloc[0]
                pct = row["BandH"] / row["TotalDwellings"] * 100
                print(f"      {name}: {factor:.2f}x ({pct:.2f}% Band H)")

    return wealth_factors


def load_population_data(data_dir: Path = None, verbose: bool = True) -> pd.DataFrame:
    """Load NRS constituency population data.

    Args:
        data_dir: Directory containing data files. Defaults to package data dir.
        verbose: Print progress messages.

    Returns:
        DataFrame with constituency and population columns.

    Raises:
        FileNotFoundError: If population data file not found.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    pop_file = data_dir / "constituency_population.csv"

    if not pop_file.exists():
        if verbose:
            print("⚠️  Population data not found. Checking for Excel source...")

        # Extract from Excel if CSV doesn't exist
        xlsx_file = data_dir / "nrs_constituency_population.xlsx"
        if xlsx_file.exists():
            if verbose:
                print("   Extracting from NRS Excel file...")
            df = pd.read_excel(xlsx_file, sheet_name="2021", skiprows=2)
            df.columns = ["constituency", "code", "sex", "total"] + [
                f"age_{i}" for i in range(len(df.columns) - 4)
            ]
            df_pop = df[df["sex"] == "Persons"][["constituency", "total"]].copy()
            df_pop.columns = ["constituency", "population"]
            df_pop = df_pop.dropna()
            df_pop["population"] = df_pop["population"].astype(int)
            df_pop.to_csv(pop_file, index=False)
            if verbose:
                print(f"   ✓ Saved {len(df_pop)} constituencies to {pop_file}")
        else:
            raise FileNotFoundError(
                f"Population data not found. Expected one of:\n"
                f"  - {pop_file}\n"
                f"  - {xlsx_file}\n\n"
                f"Run 'scotland-mansion-tax download --all' to download required data."
            )

    return pd.read_csv(pop_file)


def download_all(data_dir: Path = None, verbose: bool = True) -> bool:
    """Download all required data files.

    Args:
        data_dir: Directory to save data to. Defaults to package data dir.
        verbose: Print progress messages.

    Returns:
        True if all downloads succeeded, False otherwise.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    success = True

    if verbose:
        print("Downloading required data files...")
        print()

    # 1. NRS Dwelling Estimates (for Band H data)
    if verbose:
        print("1. NRS Dwelling Estimates (Band H data by Data Zone):")
    dwelling_file = data_dir / "dwelling_estimates_by_dz.xlsx"
    if dwelling_file.exists():
        if verbose:
            print("   ✓ Already present")
    else:
        if not download_dwelling_estimates(data_dir, verbose):
            success = False

    if verbose:
        print()

    # 2. SSPL Data Zone Lookup
    if verbose:
        print("2. Data Zone to Constituency lookup (SSPL):")
    lookup_file = data_dir / "dz_to_constituency_lookup.csv"
    if lookup_file.exists():
        if verbose:
            print("   ✓ Already present")
    else:
        if not download_dz_lookup(data_dir, verbose):
            success = False

    if verbose:
        print()

    # 3. Constituency Names
    if verbose:
        print("3. Constituency names (MapIt):")
    names_file = data_dir / "constituency_names.csv"
    if names_file.exists():
        if verbose:
            print("   ✓ Already present")
    else:
        if not download_constituency_names(data_dir, verbose):
            # Not critical - just for display
            if verbose:
                print("   ⚠️ Optional - analysis will use codes instead of names")

    if verbose:
        print()

    # 4. Population data
    pop_file = data_dir / "constituency_population.csv"
    if verbose:
        print("4. Population data (NRS):")
    if pop_file.exists():
        if verbose:
            print("   ✓ Already present")
    else:
        if verbose:
            print("   ⚠️ Not found - include in repo or download manually from NRS")
        success = False

    # 5. GeoJSON boundaries
    geojson_file = data_dir / "scottish_parliament_constituencies.geojson"
    if verbose:
        print()
        print("5. Constituency boundaries (GeoJSON):")
    if geojson_file.exists():
        if verbose:
            print("   ✓ Already present")
    else:
        if verbose:
            print("   ⚠️ Not found - include in repo")
        success = False

    return success
