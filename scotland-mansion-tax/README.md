# Scottish Mansion Tax Analysis

Analysis of Scotland's proposed council tax reform for £1m+ properties ([Scottish Budget 2026-27](https://www.gov.scot/publications/scottish-budget-2026-27/)), estimated by Scottish Parliament constituency.

**Live map**: [policyengine.github.io/scotland-mansion-tax](https://policyengine.github.io/scotland-mansion-tax/scottish_mansion_tax_map.html)

## Quick Start

```bash
# Install
git clone https://github.com/PolicyEngine/scotland-mansion-tax.git
cd scotland-mansion-tax
pip install -e .

# Run full pipeline
scotland-mansion-tax run

# Or run individual steps
scotland-mansion-tax download --all
scotland-mansion-tax analyze --output results.csv
scotland-mansion-tax visualize --output-dir ./output
```

## Policy Summary

| Detail | Value |
|--------|-------|
| **Effective date** | 1 April 2028 |
| **Threshold** | £1 million |
| **Band I** | £1m - £2m (89% of properties) |
| **Band J** | £2m+ (11% of properties) |
| **Affected households** | <1% of Scottish households |
| **Rates announced?** | No - rates not yet confirmed |

## Results

| Metric | Value | Source |
|--------|-------|--------|
| £1m+ property stock | [11,481](https://www.savills.com/insight-and-opinion/savills-news/339380/1-in-40-homes-now-valued-£1-million-or-more--according-to-savills) | Savills (2022) |
| £1m+ sales/year | [391](https://www.ros.gov.uk/data-and-statistics/property-market-statistics/property-market-report-2024-25) | RoS (2024-25) |
| Edinburgh share | >50% | [RoS](https://www.ros.gov.uk/__data/assets/pdf_file/0006/299184/Registers-of-Scotland-Property-Market-Report-2024-25-June.pdf) |
| **Estimated revenue** | **£18.5m/year** | Analysis |

### Revenue Calculation

Since Scotland hasn't announced rates, we use [UK Autumn Budget 2025 rates](https://www.gov.uk/government/publications/high-value-council-tax-surcharge/high-value-council-tax-surcharge) as benchmark:

| Band | UK Rate | Est. Stock | Revenue |
|------|---------|------------|---------|
| Band I (£1m-£2m) | £1,500/yr | 10,252 (89%) | £15.4m |
| Band J (£2m+) | £2,500/yr | 1,229 (11%) | £3.1m |
| **Total** | | **11,481** | **£18.5m** |

*Band split (89%/11%) from [Savills 2024 Scotland £1m+ Market Analysis](https://www.savills.co.uk/research_articles/229130/372275-0): 416 sales £1m-£2m, 50 sales £2m+.*

```
Revenue = Stock × Average Rate = 11,481 × £1,607 = £18.5m
```

*Finance Secretary verbally estimated [£16m](https://www.lbc.co.uk/article/wealthy-scots-in-snp-sights-as-budget-proposes-mansion-house-tax-and-a-tax-on-pr-5HjdQg9_2/). Our estimate uses UK benchmark rates.*

### Rate Uncertainty

> **Important**: Scotland has not announced rates. Our £18.5m estimate uses UK benchmark rates. Actual revenue will depend on rates Scotland chooses.

| Scenario | Band I | Band J | Avg Rate | Revenue |
|----------|--------|--------|----------|---------|
| **UK benchmark** | £1,500 | £2,500 | £1,607 | **£18.5m** |
| Mid estimate | £1,350 | £2,250 | £1,447 | £16.6m |
| Matches £16m target | £1,200 | £2,000 | £1,286 | £14.8m |
| Conservative | £1,000 | £1,750 | £1,080 | £12.4m |

*Revenue range: £12.4m - £18.5m depending on rates chosen.*

### Top 10 Constituencies

| Rank | Constituency | Revenue | Band H Factor |
|------|-------------|---------|---------------|
| 1 | Edinburgh Central | £2.57m | 4.85× |
| 2 | Edinburgh Southern | £2.37m | 5.26× |
| 3 | Edinburgh Pentlands | £1.53m | 3.50× |
| 4 | East Lothian | £1.51m | 1.96× |
| 5 | Edinburgh Western | £1.37m | 2.90× |
| 6 | Strathkelvin and Bearsden | £1.08m | 1.72× |
| 7 | North East Fife | £0.84m | 1.45× |
| 8 | Aberdeen South and North Kincardine | £0.71m | 4.44× |
| 9 | Edinburgh Northern and Leith | £0.61m | 1.85× |
| 10 | Aberdeenshire West | £0.47m | 1.68× |

**Key finding**: Edinburgh Central leads with £2.57m, reflecting its high Band H concentration (2.74% vs 0.57% Scotland average). Edinburgh constituencies account for ~47% of total revenue.

## Methodology

### Data Challenge

| | England/Wales | Scotland |
|--|---------------|----------|
| Data source | Land Registry | Registers of Scotland |
| Availability | Free, postcode-level | Paid, council-level only |
| Methodology | Direct property analysis | Weighted distribution |

Scotland's RoS charges for transaction data and only publishes council-level aggregates.

### Our Approach

1. **Stock → Revenue**: 11,481 properties × £1,607 avg rate = £18.5m total
2. **Sales → Distribution**: Use [391 sales by council](https://www.ros.gov.uk/data-and-statistics/property-market-statistics/property-market-report-2024-25) for geographic shares
3. **Council → Constituency**: Distribute within councils using **wealth-adjusted weights**:
   - Base: [NRS population weights](https://www.nrscotland.gov.uk/publications/scottish-parliamentary-constituency-population-estimates/)
   - Adjustment: **Council Tax Band H data** as £1m+ property proxy
   - Formula: `Weight = (Population × Wealth Factor) / Council Total`
   - Wealth Factor = constituency Band H % ÷ Scotland average Band H %

### Why Band H?

Scotland's council tax bands are based on 1991 property values. Using [UK House Price Index data](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-april-2025):

| Date | Scotland Avg Price |
|------|-------------------|
| April 1991 | £36,558 |
| December 2024 | £181,936 |
| **Multiplier** | **4.98×** |

This means Band H threshold (>£212k in 1991) equals approximately **£1.06m in 2024** - closely aligning with the mansion tax's £1m+ threshold.

| Band | 1991 Value | ~2024 Equivalent |
|------|------------|------------------|
| F | £80k-£106k | ~£400k-£530k |
| G | £106k-£212k | ~£530k-£1.06m |
| **H** | >£212k | **>£1.06m** |

Band H is the best available proxy for £1m+ properties. The grouped "Band F-H" data dilutes the signal with £400k-£1m properties that aren't affected by the mansion tax.

### Wealth Factors from Band H Data

Band H data is aggregated from ~7,000 Data Zones to constituency level:

| Constituency | Band H % | Factor | Notes |
|--------------|----------|--------|-------|
| Edinburgh Southern | 2.97% | 5.26× | Highest concentration |
| Edinburgh Central | 2.74% | 4.85× | New Town, Stockbridge |
| Eastwood | 2.60% | 4.59× | Affluent Glasgow suburb |
| Aberdeen South | 2.51% | 4.44× | Oil industry wealth |
| Edinburgh Pentlands | 1.98% | 3.50× | |
| Scotland average | 0.57% | 1.00× | 16,011 Band H properties |
| Glasgow Pollok | 0.00% | 0.00× | No £1m+ properties |

Stock tells us **how many** properties; sales tells us **where** they are; Band H data tells us **how £1m+ properties are distributed within councils**.

## Comparison with UK Mansion Tax

| | [uk-mansion-tax](https://github.com/PolicyEngine/uk-mansion-tax) | scotland-mansion-tax |
|--|-----------------|----------------------|
| Threshold | £2m+ | £1m+ |
| Revenue | £400m (OBR) | £18.5m (analysis) |
| Data | Property-level | Council-level |
| Top area | Cities of London & Westminster | Edinburgh Central |

## Data Sources

| Data | Source | Year |
|------|--------|------|
| £1m+ property stock | [Savills](https://www.savills.com/insight-and-opinion/savills-news/339380/1-in-40-homes-now-valued-£1-million-or-more--according-to-savills) | 2022 |
| £1m+ sales | [Registers of Scotland](https://www.ros.gov.uk/data-and-statistics/property-market-statistics/property-market-report-2024-25) | 2024-25 |
| Population | [NRS](https://www.nrscotland.gov.uk/publications/scottish-parliamentary-constituency-population-estimates/) | 2022 |
| Band H dwellings | [NRS Dwelling Estimates](https://www.nrscotland.gov.uk/publications/estimates-of-dwellings-and-households-in-scotland-2023/) | 2023 |
| Data Zone mapping | [SSPL 2025/2](https://www.gov.scot/publications/scottish-spending-proposals-lookup-2/) | 2025 |
| House price multiplier | [UK HPI](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-april-2025) | 1991-2024 |
| Policy rates | [UK Budget 2025](https://www.gov.uk/government/publications/high-value-council-tax-surcharge/high-value-council-tax-surcharge) | 2025 |

## Limitations

1. **Modeled estimates**: Constituency figures are modeled estimates, not direct observations
2. **Single year data**: Sales data from single year (2024-25); may vary annually
3. **Stock-sales assumption**: Assumes stock distributed geographically like sales
4. **No behavioral response**: Does not model potential property market changes
5. **Temporal mismatch**: Stock data (2022) predates sales data (2024-25) by ~2 years. Scottish house prices rose ~5-10% over this period, so actual 2024 stock may be higher than 11,481
6. **Council estimates**: RoS reports 391 total sales but only provides aggregates. Council-level breakdown estimated from postcode data; totals 429 due to different source methodologies
7. **Rate uncertainty**: Scotland has not announced rates. Revenue estimates use UK benchmark rates (£1,500/£2,500); actual revenue could range from £12.4m to £18.5m
8. **Band H as proxy**: While Band H (>£212k in 1991, ~£1.06m today) is the best available proxy for £1m+ properties, it may not perfectly capture all mansion tax-affected properties. The Scottish Government's £5m allocation for targeted revaluation acknowledges that 1991-based banding is increasingly disconnected from current values
