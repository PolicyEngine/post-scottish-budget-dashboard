"""
Core analysis module for Scottish Mansion Tax calculations.

Revenue Calculation:
    Revenue = Stock × Average Rate
            = 11,481 × £1,607
            = £18.5m

    Where:
    - Stock (11,481): Total £1m+ properties in Scotland (Savills, 2022)
    - Average Rate (£1,607): (89% × £1,500) + (11% × £2,500)
    - Band split from Savills 2024: 416 sales £1m-£2m, 50 sales £2m+

    Sales data (391 from RoS) is only used for GEOGRAPHIC DISTRIBUTION,
    not for calculating total revenue.
"""

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from scotland_mansion_tax.data import load_population_data, load_wealth_factors

# Surcharge rates (benchmark - Scotland rates not yet announced)
# Source: https://www.gov.uk/government/publications/high-value-council-tax-surcharge
BAND_I_SURCHARGE = 1_500  # £1,500/year for £1m-£2m properties
BAND_J_SURCHARGE = 2_500  # £2,500/year for £2m+ properties

# Stock estimate from Savills (February 2023)
# Source: https://www.savills.com/insight-and-opinion/savills-news/339380/
ESTIMATED_STOCK = 11_481  # Exact figure from Savills research

# Band distribution (from Savills 2024 data)
# Source: https://www.savills.co.uk/research_articles/229130/372275-0
# 2024: 416 sales £1m-£2m, 50 sales £2m+ (total 466)
BAND_I_RATIO = 416 / 466  # £1m-£2m = 89.3%
BAND_J_RATIO = 50 / 466  # £2m+ = 10.7%

# Council-level £1m+ sales estimates
# Primary source: Registers of Scotland Property Market Report 2024-25
# https://www.ros.gov.uk/data-and-statistics/property-market-statistics/property-market-report-2024-25
ROS_REPORTED_TOTAL = 391  # Official RoS figure for validation reference

COUNCIL_DATA = {
    "City of Edinburgh": 200,  # >50% per RoS; EH3 (53) + EH4 (49) + EH9/10/12 (~98)
    "East Lothian": 35,  # North Berwick area (EH39: 18 + surrounding)
    "Fife": 30,  # St Andrews (KY16: 22 + surrounding)
    "East Dunbartonshire": 25,  # Bearsden (G61: 15 + surrounding)
    "Aberdeen City": 20,  # AB15 and central Aberdeen
    "Aberdeenshire": 15,  # Rural Aberdeenshire
    "Glasgow City": 15,  # G12, G41 areas
    "Perth and Kinross": 12,  # Perth, Auchterarder
    "Stirling": 10,  # Bridge of Allan, Dunblane
    "Highland": 10,  # Inverness, rural Highlands
    "East Renfrewshire": 10,  # Newton Mearns (G77)
    "Scottish Borders": 8,  # Melrose, Kelso
    "South Ayrshire": 7,  # Ayr coastal
    "Argyll and Bute": 6,  # Helensburgh, Oban
    "Midlothian": 5,  # Dalkeith area
    "West Lothian": 5,  # Linlithgow
    "South Lanarkshire": 3,
    "North Lanarkshire": 2,
    "Renfrewshire": 2,
    "Inverclyde": 1,
    "Falkirk": 1,
    "Clackmannanshire": 1,
    "Dumfries and Galloway": 1,
    "Dundee City": 1,
    "Angus": 1,
    "Moray": 1,
    "North Ayrshire": 1,
    "West Dunbartonshire": 1,
    "East Ayrshire": 0,
    "Eilean Siar": 0,
    "Orkney Islands": 0,
    "Shetland Islands": 0,
}

# Constituency to council mapping (Scottish Parliament 2021 boundaries)
CONSTITUENCY_COUNCIL_MAPPING = {
    # City of Edinburgh - 6 constituencies
    "Edinburgh Central": "City of Edinburgh",
    "Edinburgh Western": "City of Edinburgh",
    "Edinburgh Southern": "City of Edinburgh",
    "Edinburgh Pentlands": "City of Edinburgh",
    "Edinburgh Northern and Leith": "City of Edinburgh",
    "Edinburgh Eastern": "City of Edinburgh",
    # East Lothian - 1 constituency
    "East Lothian": "East Lothian",
    # Fife - 5 constituencies
    "North East Fife": "Fife",
    "Dunfermline": "Fife",
    "Cowdenbeath": "Fife",
    "Kirkcaldy": "Fife",
    "Mid Fife and Glenrothes": "Fife",
    # East Dunbartonshire
    "Strathkelvin and Bearsden": "East Dunbartonshire",
    # Aberdeen City - 3 constituencies
    "Aberdeen Central": "Aberdeen City",
    "Aberdeen Donside": "Aberdeen City",
    "Aberdeen South and North Kincardine": "Aberdeen City",
    # Aberdeenshire - 3 constituencies
    "Aberdeenshire West": "Aberdeenshire",
    "Aberdeenshire East": "Aberdeenshire",
    "Banffshire and Buchan Coast": "Aberdeenshire",
    # Glasgow City - 9 constituencies
    "Glasgow Kelvin": "Glasgow City",
    "Glasgow Cathcart": "Glasgow City",
    "Glasgow Anniesland": "Glasgow City",
    "Glasgow Southside": "Glasgow City",
    "Glasgow Pollok": "Glasgow City",
    "Glasgow Maryhill and Springburn": "Glasgow City",
    "Glasgow Provan": "Glasgow City",
    "Glasgow Shettleston": "Glasgow City",
    "Rutherglen": "Glasgow City",
    # Perth and Kinross - 2 constituencies
    "Perthshire North": "Perth and Kinross",
    "Perthshire South and Kinross-shire": "Perth and Kinross",
    # Stirling - 1 constituency
    "Stirling": "Stirling",
    # Highland - 3 constituencies
    "Inverness and Nairn": "Highland",
    "Caithness, Sutherland and Ross": "Highland",
    "Skye, Lochaber and Badenoch": "Highland",
    # East Renfrewshire - 1 constituency
    "Eastwood": "East Renfrewshire",
    # Scottish Borders - 2 constituencies
    "Ettrick, Roxburgh and Berwickshire": "Scottish Borders",
    "Midlothian South, Tweeddale and Lauderdale": "Scottish Borders",
    # South Ayrshire - 2 constituencies
    "Ayr": "South Ayrshire",
    "Carrick, Cumnock and Doon Valley": "South Ayrshire",
    # Argyll and Bute - 1 constituency
    "Argyll and Bute": "Argyll and Bute",
    # Midlothian - 1 constituency
    "Midlothian North and Musselburgh": "Midlothian",
    # West Lothian - 2 constituencies
    "Linlithgow": "West Lothian",
    "Almond Valley": "West Lothian",
    # South Lanarkshire - 4 constituencies
    "East Kilbride": "South Lanarkshire",
    "Clydesdale": "South Lanarkshire",
    "Hamilton, Larkhall and Stonehouse": "South Lanarkshire",
    "Uddingston and Bellshill": "South Lanarkshire",
    # North Lanarkshire - 4 constituencies
    "Motherwell and Wishaw": "North Lanarkshire",
    "Airdrie and Shotts": "North Lanarkshire",
    "Coatbridge and Chryston": "North Lanarkshire",
    "Cumbernauld and Kilsyth": "North Lanarkshire",
    # Renfrewshire - 3 constituencies
    "Paisley": "Renfrewshire",
    "Renfrewshire North and West": "Renfrewshire",
    "Renfrewshire South": "Renfrewshire",
    # Inverclyde - 1 constituency
    "Greenock and Inverclyde": "Inverclyde",
    # Falkirk - 2 constituencies
    "Falkirk East": "Falkirk",
    "Falkirk West": "Falkirk",
    # Clackmannanshire
    "Clackmannanshire and Dunblane": "Clackmannanshire",
    # Dumfries and Galloway - 2 constituencies
    "Dumfriesshire": "Dumfries and Galloway",
    "Galloway and West Dumfries": "Dumfries and Galloway",
    # Dundee City - 2 constituencies
    "Dundee City East": "Dundee City",
    "Dundee City West": "Dundee City",
    # Angus - 2 constituencies
    "Angus North and Mearns": "Angus",
    "Angus South": "Angus",
    # Moray - 1 constituency
    "Moray": "Moray",
    # North Ayrshire - 2 constituencies
    "Cunninghame North": "North Ayrshire",
    "Cunninghame South": "North Ayrshire",
    # East Ayrshire - 1 constituency
    "Kilmarnock and Irvine Valley": "East Ayrshire",
    # West Dunbartonshire - 2 constituencies
    "Dumbarton": "West Dunbartonshire",
    "Clydebank and Milngavie": "West Dunbartonshire",
    # Island councils
    "Na h-Eileanan an Iar": "Eilean Siar",
    "Orkney Islands": "Orkney Islands",
    "Shetland Islands": "Shetland Islands",
}

# Expected number of constituencies
EXPECTED_CONSTITUENCIES = 73


def calculate_wealth_adjusted_weights(
    population_df: pd.DataFrame, wealth_factors: Dict[str, float]
) -> Dict[str, dict]:
    """Calculate wealth-adjusted weights within each council.

    Weight = (Population × Wealth Factor) / Sum(Population × Wealth Factor for council)

    Args:
        population_df: DataFrame with constituency populations.
        wealth_factors: Dict mapping constituency -> wealth factor.

    Returns:
        Dict mapping constituency -> {council, population, wealth_factor, weight}.
    """
    weights = {}

    # Group constituencies by council with adjusted values
    council_data = {}
    for constituency, council in CONSTITUENCY_COUNCIL_MAPPING.items():
        if council not in council_data:
            council_data[council] = []

        # Find population for this constituency
        pop_row = population_df[population_df["constituency"] == constituency]
        if len(pop_row) == 0:
            raise ValueError(f"No population data for {constituency}")
        pop = pop_row["population"].values[0]

        # Get wealth adjustment factor
        if constituency not in wealth_factors:
            raise ValueError(f"No wealth factor for {constituency}")
        wealth_factor = wealth_factors[constituency]

        # Adjusted value = population × wealth factor
        adjusted_value = pop * wealth_factor

        council_data[council].append((constituency, pop, wealth_factor, adjusted_value))

    # Calculate weights within each council using adjusted values
    for council, constituencies in council_data.items():
        total_adjusted = sum(adj for _, _, _, adj in constituencies)
        for constituency, pop, wealth_factor, adjusted_value in constituencies:
            # Weight based on adjusted value, not raw population
            weight = (
                adjusted_value / total_adjusted
                if total_adjusted > 0
                else 1 / len(constituencies)
            )
            weights[constituency] = {
                "council": council,
                "population": pop,
                "wealth_factor": wealth_factor,
                "weight": weight,
            }

    return weights


def analyze_constituencies(
    data_dir: Optional[Path] = None, verbose: bool = True
) -> pd.DataFrame:
    """Distribute council-level estimates to constituencies using wealth-adjusted weights.

    Args:
        data_dir: Directory containing data files. Defaults to package data dir.
        verbose: Print progress messages.

    Returns:
        DataFrame with constituency-level analysis results.
    """
    if verbose:
        print("=" * 70)
        print("Scottish Mansion Tax Analysis by Parliament Constituency")
        print("Using wealth-adjusted weights (population × Band H factor)")
        print("=" * 70)

    # Load population data
    if verbose:
        print("\n📊 Loading NRS population data...")
    population_df = load_population_data(data_dir, verbose)
    if verbose:
        print(f"   ✓ Loaded {len(population_df)} constituencies")

    # Load wealth factors from Council Tax Band H data
    if verbose:
        print("\n💎 Loading Council Tax Band H data (wealth proxy)...")
    wealth_factors = load_wealth_factors(data_dir, verbose)
    if verbose:
        print(f"   ✓ Loaded wealth factors for {len(wealth_factors)} constituencies")

    # Calculate wealth-adjusted weights
    if verbose:
        print("\n📈 Calculating wealth-adjusted weights...")
    weights = calculate_wealth_adjusted_weights(population_df, wealth_factors)

    # Calculate total sales for normalization
    total_sales = sum(COUNCIL_DATA.values())

    results = []

    for constituency, data in weights.items():
        council = data["council"]
        weight = data["weight"]
        population = data["population"]
        wealth_factor = data["wealth_factor"]

        # Get council's total sales
        if council not in COUNCIL_DATA:
            raise ValueError(f"Council {council} not in COUNCIL_DATA")
        council_sales = COUNCIL_DATA[council]

        # Allocate to constituency based on wealth-adjusted weight
        constituency_sales = council_sales * weight

        # Calculate share of total
        share = constituency_sales / total_sales if total_sales > 0 else 0

        # Band breakdown
        band_i_sales = constituency_sales * BAND_I_RATIO
        band_j_sales = constituency_sales * BAND_J_RATIO

        # Calculate implied revenue from sales using UK rates
        implied_from_sales = (band_i_sales * BAND_I_SURCHARGE) + (
            band_j_sales * BAND_J_SURCHARGE
        )

        rounded_sales = round(constituency_sales)
        results.append(
            {
                "constituency": constituency,
                "council": council,
                "population": population,
                "wealth_factor": wealth_factor,
                "weight": round(weight, 4),
                "estimated_sales": rounded_sales,
                "band_i_sales": round(band_i_sales),
                "band_j_sales": round(band_j_sales),
                "share_pct": round(share * 100, 2) if rounded_sales > 0 else 0,
                "implied_from_sales": round(implied_from_sales)
                if rounded_sales > 0
                else 0,
            }
        )

    df = pd.DataFrame(results)
    df = df.sort_values("estimated_sales", ascending=False)

    # Calculate total revenue using simple formula: Stock × Average Rate
    avg_rate = BAND_I_RATIO * BAND_I_SURCHARGE + BAND_J_RATIO * BAND_J_SURCHARGE
    total_stock_revenue = ESTIMATED_STOCK * avg_rate  # 11,481 × £1,607 = £18.5m

    # Allocate total revenue proportionally by each constituency's share
    df["allocated_revenue"] = (df["share_pct"] / 100 * total_stock_revenue).round(0)

    if verbose:
        # Print summary
        print(f"\n📊 Total constituencies: {len(df)}")
        print(
            f"📈 Total £1m+ sales: {df['estimated_sales'].sum():.0f} (for geographic distribution)"
        )
        print(f"🏠 Estimated £1m+ stock: {ESTIMATED_STOCK:,} (Savills)")
        print(f"\n💰 Revenue calculation:")
        print(f"   Band I rate: £{BAND_I_SURCHARGE:,}/year ({BAND_I_RATIO:.1%} of properties)")
        print(f"   Band J rate: £{BAND_J_SURCHARGE:,}/year ({BAND_J_RATIO:.1%} of properties)")
        print(f"   Average rate: £{avg_rate:,.0f}/year")
        print(
            f"   Formula: Stock × Avg Rate = {ESTIMATED_STOCK:,} × £{avg_rate:,.0f} = £{total_stock_revenue/1e6:.1f}m"
        )

        print("\n🏛️  Top 10 Constituencies by Impact:")
        print("-" * 90)
        print(f"{'Constituency':<40} {'Council':<20} {'Sales':>6} {'Revenue':>12}")
        print("-" * 90)

        for _, row in df.head(10).iterrows():
            council_short = (
                row["council"][:19] if len(row["council"]) > 19 else row["council"]
            )
            print(
                f"{row['constituency']:<40} {council_short:<20} "
                f"{row['estimated_sales']:>6} £{row['allocated_revenue']/1e6:>10.2f}m"
            )

        # Edinburgh subtotal
        edinburgh_df = df[df["council"] == "City of Edinburgh"]
        print(f"\n📍 Edinburgh Total (6 constituencies):")
        print(
            f"   {edinburgh_df['estimated_sales'].sum():.0f} sales, "
            f"£{edinburgh_df['allocated_revenue'].sum()/1e6:.1f}m "
            f"({edinburgh_df['share_pct'].sum():.1f}%)"
        )

    return df


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Get summary statistics from analysis results.

    Args:
        df: DataFrame from analyze_constituencies()

    Returns:
        Dictionary with summary statistics.
    """
    avg_rate = BAND_I_RATIO * BAND_I_SURCHARGE + BAND_J_RATIO * BAND_J_SURCHARGE

    edinburgh_df = df[df["council"] == "City of Edinburgh"]

    return {
        "total_constituencies": len(df),
        "constituencies_with_sales": len(df[df["estimated_sales"] > 0]),
        "total_sales": df["estimated_sales"].sum(),
        "estimated_stock": ESTIMATED_STOCK,
        "total_revenue": df["allocated_revenue"].sum(),
        "average_rate": avg_rate,
        "edinburgh_revenue": edinburgh_df["allocated_revenue"].sum(),
        "edinburgh_share_pct": edinburgh_df["share_pct"].sum(),
        "top_constituency": df.iloc[0]["constituency"],
        "top_constituency_revenue": df.iloc[0]["allocated_revenue"],
    }
