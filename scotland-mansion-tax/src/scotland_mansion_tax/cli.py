"""
Command-line interface for Scotland Mansion Tax analysis.

Usage:
    scotland-mansion-tax download --all
    scotland-mansion-tax analyze --output results.csv
    scotland-mansion-tax visualize --input results.csv --output-dir ./output
"""

from pathlib import Path

import click

from scotland_mansion_tax import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """Scotland Mansion Tax Analysis CLI.

    Analyze Scotland's proposed council tax reform for £1m+ properties
    by Scottish Parliament constituency.
    """
    pass


@main.command()
@click.option(
    "--all",
    "download_all",
    is_flag=True,
    help="Download all required data files",
)
@click.option(
    "--council-tax",
    is_flag=True,
    help="Download Council Tax Band data from statistics.gov.scot",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory to save data files (default: ./data)",
)
def download(download_all: bool, council_tax: bool, data_dir: Path):
    """Download required data files."""
    from scotland_mansion_tax.data import download_all as do_download_all
    from scotland_mansion_tax.data import download_council_tax_data, get_data_dir

    if data_dir is None:
        data_dir = get_data_dir()
    else:
        data_dir.mkdir(parents=True, exist_ok=True)

    if download_all:
        click.echo("Downloading all required data files...")
        success = do_download_all(data_dir)
        if success:
            click.echo("\n✅ All data files ready!")
        else:
            click.echo("\n⚠️ Some data files could not be downloaded.")
            raise SystemExit(1)
    elif council_tax:
        click.echo("Downloading Council Tax Band data...")
        success = download_council_tax_data(data_dir)
        if success:
            click.echo("✅ Council Tax data downloaded!")
        else:
            click.echo("❌ Download failed.")
            raise SystemExit(1)
    else:
        click.echo("Specify --all or --council-tax to download data.")
        raise SystemExit(1)


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="scottish_parliament_constituency_impact.csv",
    help="Output CSV file path",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing data files",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress progress output",
)
def analyze(output: Path, data_dir: Path, quiet: bool):
    """Run mansion tax analysis by constituency.

    Calculates revenue distribution across all 73 Scottish Parliament
    constituencies using wealth-adjusted weights.
    """
    from scotland_mansion_tax.analysis import analyze_constituencies, get_summary_stats

    verbose = not quiet

    try:
        df = analyze_constituencies(data_dir, verbose=verbose)
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        click.echo("\nRun 'scotland-mansion-tax download --all' to download required data.")
        raise SystemExit(1)

    # Save results
    df.to_csv(output, index=False)
    if verbose:
        click.echo(f"\n✅ Results saved to: {output}")

        # Print summary
        stats = get_summary_stats(df)
        click.echo(f"\nSummary:")
        click.echo(f"  Total revenue: £{stats['total_revenue']/1e6:.1f}m")
        click.echo(f"  Constituencies with sales: {stats['constituencies_with_sales']}")
        click.echo(f"  Edinburgh share: {stats['edinburgh_share_pct']:.1f}%")
        click.echo(f"  Top constituency: {stats['top_constituency']} (£{stats['top_constituency_revenue']/1e6:.2f}m)")


@main.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    type=click.Path(exists=True, path_type=Path),
    default="scottish_parliament_constituency_impact.csv",
    help="Input CSV file from analyze command",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default="output",
    help="Directory to save visualization outputs",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress progress output",
)
def visualize(input_file: Path, output_dir: Path, quiet: bool):
    """Generate visualizations from analysis results.

    Creates bar charts, pie charts, and HTML reports.
    """
    import pandas as pd

    from scotland_mansion_tax.visualization import generate_all_visualizations

    verbose = not quiet

    if verbose:
        click.echo(f"Loading data from: {input_file}")

    df = pd.read_csv(input_file)

    if verbose:
        click.echo(f"Loaded {len(df)} constituencies")

    outputs = generate_all_visualizations(df, output_dir, verbose=verbose)

    if verbose:
        click.echo(f"\n✅ Generated {len(outputs)} visualization files in: {output_dir}")


@main.command()
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default="output",
    help="Directory to save all outputs",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing data files",
)
def run(output_dir: Path, data_dir: Path):
    """Run full analysis pipeline: download, analyze, visualize.

    This is a convenience command that runs all steps in sequence.
    """
    import pandas as pd

    from scotland_mansion_tax.analysis import analyze_constituencies, get_summary_stats
    from scotland_mansion_tax.data import download_all as do_download_all
    from scotland_mansion_tax.data import get_data_dir
    from scotland_mansion_tax.visualization import generate_all_visualizations

    if data_dir is None:
        data_dir = get_data_dir()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo("=" * 60)
    click.echo("Scotland Mansion Tax Analysis - Full Pipeline")
    click.echo("=" * 60)

    # Step 1: Download data
    click.echo("\n📥 Step 1: Checking/downloading data...")
    do_download_all(data_dir, verbose=True)

    # Step 2: Run analysis
    click.echo("\n📊 Step 2: Running analysis...")
    try:
        df = analyze_constituencies(data_dir, verbose=True)
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        raise SystemExit(1)

    # Save CSV
    csv_path = output_dir / "constituency_impact.csv"
    df.to_csv(csv_path, index=False)
    click.echo(f"\n   ✓ Saved: {csv_path}")

    # Step 3: Generate visualizations
    click.echo("\n🎨 Step 3: Generating visualizations...")
    generate_all_visualizations(df, output_dir, verbose=True)

    # Summary
    stats = get_summary_stats(df)
    click.echo("\n" + "=" * 60)
    click.echo("✅ Pipeline complete!")
    click.echo("=" * 60)
    click.echo(f"\nResults:")
    click.echo(f"  Total revenue: £{stats['total_revenue']/1e6:.1f}m")
    click.echo(f"  Top: {stats['top_constituency']} (£{stats['top_constituency_revenue']/1e6:.2f}m)")
    click.echo(f"  Edinburgh share: {stats['edinburgh_share_pct']:.1f}%")
    click.echo(f"\nOutputs saved to: {output_dir}/")


if __name__ == "__main__":
    main()
