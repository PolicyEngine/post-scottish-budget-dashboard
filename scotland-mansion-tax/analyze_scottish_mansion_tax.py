#!/usr/bin/env python3
"""
Scottish Mansion Tax Analysis

Analyzes the impact of Scotland's proposed council tax reform for high-value
properties (£1m+), announced in the Scottish Budget 2026-27.

Policy details:
- From April 2028, two new council tax bands for properties over £1m
- Band I: £1m - £2m
- Band J: £2m+
- Rates to be set by individual councils
- Scottish Government estimates £16m revenue

Data sources:
- Registers of Scotland Property Market Report 2024-25
- Savills/Rettie research reports
- Scottish Housing News analysis
"""

import pandas as pd
from pathlib import Path

# Scottish Government revenue estimate
SCOTTISH_GOV_REVENUE_ESTIMATE = 16_000_000  # £16 million

# £1m+ sales data from Registers of Scotland Property Market Report 2024-25
# Source: https://www.ros.gov.uk/data-and-statistics/property-market-statistics/property-market-report-2024-25
MILLION_PLUS_SALES_2024 = {
    "total": 391,  # RoS official figure

    # Top postcodes from Scottish Housing News / Scotsman analysis
    # EH = Edinburgh, G = Glasgow, KY = Fife
    "by_postcode": {
        "EH3": 53,   # New Town & West End
        "EH4": 49,   # Barnton, Cramond, Cammo
        "EH9": 28,   # Marchmont, Grange (estimated)
        "EH10": 25,  # Morningside (estimated)
        "EH12": 20,  # Corstorphine (estimated)
        "KY16": 22,  # St Andrews
        "EH39": 18,  # North Berwick
        "G61": 15,   # Bearsden
        "EH30": 12,  # South Queensferry (estimated)
        "AB15": 10,  # Aberdeen West (estimated)
        "Other": 139,  # Remaining sales
    },

    # Local authority distribution (estimated from postcode data)
    # Edinburgh accounts for 50%+ per RoS reports
    "by_council": {
        "City of Edinburgh": 200,      # >50% of total
        "East Lothian": 35,            # North Berwick area
        "Fife": 30,                    # St Andrews
        "East Dunbartonshire": 25,     # Bearsden
        "Aberdeen City": 20,           # Aberdeen
        "Aberdeenshire": 15,           # Aberdeenshire
        "Glasgow City": 15,            # Glasgow
        "Perth and Kinross": 12,       # Perth area
        "Stirling": 10,                # Stirling
        "Highland": 10,                # Highlands
        "East Renfrewshire": 10,       # Newton Mearns
        "Scottish Borders": 8,         # Borders
        "South Ayrshire": 7,           # Ayrshire coast
        "Argyll and Bute": 6,          # Argyll
        "Midlothian": 5,               # Midlothian
        "West Lothian": 5,             # West Lothian
    }
}

# Band breakdown from Savills 2024 Scotland £1m+ Market Analysis
# Source: https://www.savills.co.uk/research_articles/229130/372275-0
# 2024: 416 sales £1m-£2m, 50 sales £2m+ (total 466)
BAND_DISTRIBUTION = {
    "Band I (£1m-£2m)": 416 / 466,  # 89% of £1m+ sales
    "Band J (£2m+)": 50 / 466,      # 11% of £1m+ sales
}


def analyze():
    """Main analysis: estimate Scottish mansion tax impact by council area."""
    print("=" * 70)
    print("Scottish Mansion Tax Analysis")
    print("Based on Scottish Budget 2026-27 and public property data")
    print("=" * 70)

    print("\n📊 Policy Overview:")
    print("  - Effective: April 2028")
    print("  - Threshold: £1 million")
    print("  - Band I: £1m - £2m")
    print("  - Band J: £2m+")
    print(f"  - Revenue estimate: £{SCOTTISH_GOV_REVENUE_ESTIMATE/1e6:.0f}m (Scottish Government)")

    total_sales = MILLION_PLUS_SALES_2024["total"]
    print(f"\n📈 2024 £1m+ Sales Overview:")
    print(f"  - Total £1m+ sales: ~{total_sales}")
    print(f"  - Band I (£1m-£2m): ~{int(total_sales * BAND_DISTRIBUTION['Band I (£1m-£2m)'])}")
    print(f"  - Band J (£2m+): ~{int(total_sales * BAND_DISTRIBUTION['Band J (£2m+)'])}")

    # Calculate council-level impact
    council_data = MILLION_PLUS_SALES_2024["by_council"]
    total_council_sales = sum(council_data.values())

    results = []
    for council, sales in council_data.items():
        share = sales / total_council_sales
        allocated_revenue = share * SCOTTISH_GOV_REVENUE_ESTIMATE
        band_i_sales = int(sales * BAND_DISTRIBUTION["Band I (£1m-£2m)"])
        band_j_sales = int(sales * BAND_DISTRIBUTION["Band J (£2m+)"])

        results.append({
            "council": council,
            "total_sales_1m_plus": sales,
            "band_i_sales": band_i_sales,
            "band_j_sales": band_j_sales,
            "share_pct": round(share * 100, 2),
            "allocated_revenue": round(allocated_revenue, 0),
        })

    df = pd.DataFrame(results)
    df = df.sort_values("total_sales_1m_plus", ascending=False)

    # Top postcodes
    print("\n📍 Top Postcodes (£1m+ sales in 2024):")
    postcode_data = MILLION_PLUS_SALES_2024["by_postcode"]
    for postcode, count in sorted(postcode_data.items(), key=lambda x: -x[1])[:10]:
        if postcode != "Other":
            print(f"  {postcode}: {count} sales")

    # Council breakdown
    print("\n🏛️  Impact by Council Area:")
    print("-" * 70)
    print(f"{'Council':<30} {'Sales':>8} {'Share':>8} {'Revenue':>12}")
    print("-" * 70)

    for _, row in df.head(15).iterrows():
        print(f"{row['council']:<30} {row['total_sales_1m_plus']:>8} "
              f"{row['share_pct']:>7.1f}% £{row['allocated_revenue']/1e6:>9.2f}m")

    print("-" * 70)
    print(f"{'TOTAL':<30} {df['total_sales_1m_plus'].sum():>8} "
          f"{'100.0':>7}% £{df['allocated_revenue'].sum()/1e6:>9.2f}m")

    return df


def main():
    """Run analysis and save results."""
    df = analyze()

    # Save results
    output_file = "scottish_mansion_tax_impact.csv"
    df.to_csv(output_file, index=False)

    print("\n" + "=" * 70)
    print("Results Summary:")
    print(f"  - {len(df)} council areas analyzed")
    print(f"  - {df['total_sales_1m_plus'].sum()} total £1m+ sales (2024)")
    print(f"  - £{df['allocated_revenue'].sum()/1e6:.0f}m total allocated revenue")
    print(f"\nTop 5 councils by impact:")
    for _, row in df.head(5).iterrows():
        print(f"  {row['council']}: {row['total_sales_1m_plus']} sales, "
              f"£{row['allocated_revenue']/1e6:.2f}m ({row['share_pct']:.1f}%)")

    print(f"\nGenerated: {output_file}")
    print("=" * 70)

    return df


if __name__ == "__main__":
    main()
