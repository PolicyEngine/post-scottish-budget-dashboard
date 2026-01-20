"""
Scotland Mansion Tax Analysis

Analysis of Scotland's proposed council tax reform for £1m+ properties
(Scottish Budget 2026-27) by Scottish Parliament constituency.
"""

__version__ = "0.1.0"
__author__ = "PolicyEngine"

from scotland_mansion_tax.analysis import analyze_constituencies
from scotland_mansion_tax.data import (
    download_all,
    load_population_data,
    load_wealth_factors,
)

__all__ = [
    "analyze_constituencies",
    "download_all",
    "load_population_data",
    "load_wealth_factors",
]
