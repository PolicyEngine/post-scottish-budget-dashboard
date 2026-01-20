#!/usr/bin/env python3
"""
Unit tests for Scottish Mansion Tax Analysis.

10 essential tests covering data loading, calculations, and output correctness.
"""

import pytest

from scotland_mansion_tax.analysis import (
    BAND_I_RATIO,
    BAND_I_SURCHARGE,
    BAND_J_RATIO,
    BAND_J_SURCHARGE,
    CONSTITUENCY_COUNCIL_MAPPING,
    COUNCIL_DATA,
    ESTIMATED_STOCK,
    analyze_constituencies,
)
from scotland_mansion_tax.data import load_population_data, load_wealth_factors


def test_population_data_loads():
    """Population data loads with 73 constituencies."""
    df = load_population_data(verbose=False)
    assert len(df) == 73
    assert "constituency" in df.columns
    assert "population" in df.columns


def test_wealth_factors_load():
    """Wealth factors load and are non-negative."""
    factors = load_wealth_factors(verbose=False)
    assert len(factors) > 0
    assert all(f >= 0 for f in factors.values())


def test_output_has_73_constituencies():
    """Output contains all 73 unique constituencies."""
    df = analyze_constituencies(verbose=False)
    assert len(df) == 73
    assert df["constituency"].nunique() == 73


def test_weights_sum_to_one_per_council():
    """Weights within each council sum to 1.0."""
    df = analyze_constituencies(verbose=False)
    for council in df["council"].unique():
        weight_sum = df[df["council"] == council]["weight"].sum()
        assert abs(weight_sum - 1.0) < 0.001, f"{council} weights sum to {weight_sum}"


def test_total_revenue():
    """Total revenue matches expected ~£18.5m."""
    df = analyze_constituencies(verbose=False)
    total_revenue = df["allocated_revenue"].sum()
    expected = ESTIMATED_STOCK * (
        BAND_I_RATIO * BAND_I_SURCHARGE + BAND_J_RATIO * BAND_J_SURCHARGE
    )
    # 2% tolerance due to integer rounding of sales
    assert abs(total_revenue - expected) / expected < 0.02


def test_share_percentages_sum_to_100():
    """Share percentages sum to ~100%."""
    df = analyze_constituencies(verbose=False)
    df_with_sales = df[df["estimated_sales"] > 0]
    # 2% tolerance due to integer rounding of sales
    assert abs(df_with_sales["share_pct"].sum() - 100.0) < 2.0


def test_band_split_matches_ratios():
    """Band I/J sales match expected 89%/11% ratios."""
    df = analyze_constituencies(verbose=False)
    total_band_i = df["band_i_sales"].sum()
    total_band_j = df["band_j_sales"].sum()
    total = total_band_i + total_band_j
    assert abs(total_band_i / total - BAND_I_RATIO) < 0.01
    assert abs(total_band_j / total - BAND_J_RATIO) < 0.01


def test_required_columns_present():
    """Output has all required columns."""
    df = analyze_constituencies(verbose=False)
    required = [
        "constituency", "council", "population", "wealth_factor", "weight",
        "estimated_sales", "allocated_revenue",
    ]
    for col in required:
        assert col in df.columns, f"Missing: {col}"


def test_no_negative_values():
    """No negative values in numeric columns."""
    df = analyze_constituencies(verbose=False)
    for col in ["population", "weight", "estimated_sales", "allocated_revenue"]:
        assert (df[col] >= 0).all(), f"Negative values in {col}"


def test_all_councils_mapped():
    """All councils have constituencies mapped."""
    assert len(CONSTITUENCY_COUNCIL_MAPPING) == 73
    assert set(COUNCIL_DATA.keys()).issubset(set(CONSTITUENCY_COUNCIL_MAPPING.values()))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
