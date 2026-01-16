"""Scottish Budget 2026-27 reform definitions.

This module defines the policy reforms for the Scottish Budget analysis.

Reforms use parameter_changes and simulation_modifier to apply policy changes
via policyengine-uk's built-in reform system.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


# Constants for income tax threshold uplift
# The announced increases for 2026-27 (absolute amounts above baseline)
# Basic: £15,398 → £16,537 = +£1,139
# Intermediate: £27,492 → £29,527 = +£2,035
# These translate to threshold-above-PA increases of:
INCOME_TAX_BASIC_INCREASE = 1_069  # £3,966 - £2,897 (2026 baseline)
INCOME_TAX_INTERMEDIATE_INCREASE = 1_665  # £16,956 - £15,291 (2026 baseline)

# Default years for microsim analysis
DEFAULT_YEARS = [2026, 2027, 2028, 2029, 2030]


@dataclass
class Reform:
    """A policy reform definition."""

    id: str
    name: str
    description: str
    parameter_changes: dict = field(default_factory=dict)
    baseline_parameter_changes: Optional[dict] = None
    simulation_modifier: Optional[Callable] = None
    baseline_simulation_modifier: Optional[Callable] = None
    applied_before_data_load: bool = False  # Set True for params that trigger structural reforms

    def to_scenario(self):
        """Convert to PolicyEngine Scenario."""
        from policyengine_uk.utils.scenario import Scenario

        if self.simulation_modifier and self.parameter_changes:
            return Scenario(
                simulation_modifier=self.simulation_modifier,
                parameter_changes=self.parameter_changes,
                applied_before_data_load=self.applied_before_data_load,
            )
        elif self.simulation_modifier:
            return Scenario(
                simulation_modifier=self.simulation_modifier,
                applied_before_data_load=self.applied_before_data_load,
            )
        elif self.parameter_changes:
            return Scenario(
                parameter_changes=self.parameter_changes,
                applied_before_data_load=self.applied_before_data_load,
            )
        return None

    def to_baseline_scenario(self):
        """Convert baseline changes to PolicyEngine Scenario."""
        from policyengine_uk.utils.scenario import Scenario

        if self.baseline_simulation_modifier and self.baseline_parameter_changes:
            return Scenario(
                simulation_modifier=self.baseline_simulation_modifier,
                parameter_changes=self.baseline_parameter_changes,
            )
        elif self.baseline_simulation_modifier:
            return Scenario(simulation_modifier=self.baseline_simulation_modifier)
        elif self.baseline_parameter_changes:
            return Scenario(parameter_changes=self.baseline_parameter_changes)
        return None


def apply_income_tax_threshold_uplift_for_year(sim, year: int) -> None:
    """Apply Scottish income tax threshold uplift for a single year.

    From Scottish Budget 2026-27:
    - Basic rate (20%) threshold: £15,398 -> £16,537 (+£1,139 absolute)
    - Intermediate rate (21%) threshold: £27,492 -> £29,527 (+£2,035 absolute)

    Args:
        sim: PolicyEngine simulation object
        year: The year to apply the uplift for
    """
    params = sim.tax_benefit_system.parameters
    scotland_rates = params.gov.hmrc.income_tax.rates.scotland.rates

    # Get baseline thresholds
    baseline_basic = scotland_rates.brackets[1].threshold(f"{year}-01-01")
    baseline_intermediate = scotland_rates.brackets[2].threshold(f"{year}-01-01")

    # Apply the announced increases
    scotland_rates.brackets[1].threshold.update(
        period=f"{year}-01-01",
        value=baseline_basic + INCOME_TAX_BASIC_INCREASE,
    )
    scotland_rates.brackets[2].threshold.update(
        period=f"{year}-01-01",
        value=baseline_intermediate + INCOME_TAX_INTERMEDIATE_INCREASE,
    )


def _income_tax_modifier(sim):
    """Apply income tax threshold uplift via simulation_modifier."""
    for year in DEFAULT_YEARS:
        apply_income_tax_threshold_uplift_for_year(sim, year)
    return sim


def _scp_baby_boost_modifier(sim):
    """Enable the SCP baby bonus reform from policyengine-uk.

    Sets gov.contrib.scotland.scottish_child_payment.in_effect to True,
    which activates the built-in baby bonus (£12.85/week extra for under 1s).
    """
    params = sim.tax_benefit_system.parameters
    scp_reform = params.gov.contrib.scotland.scottish_child_payment

    for year in DEFAULT_YEARS:
        scp_reform.in_effect.update(period=f"{year}-01-01", value=True)

    return sim


def _combined_modifier(sim):
    """Apply both SCP baby boost and income tax threshold uplift.

    Order matters: income tax params must be set BEFORE SCP calculations,
    because SCP modifier calls sim.calculate() which triggers the full
    simulation with whatever parameters are currently set.
    """
    _income_tax_modifier(sim)  # Set params first (no calculations)
    _scp_baby_boost_modifier(sim)  # Then calculate with new params
    return sim


def get_scottish_budget_reforms() -> list[Reform]:
    """Get list of Scottish Budget 2026-27 reforms.

    Returns a list of Reform objects:
    - SCP baby boost: Uses simulation_modifier to directly apply PE-UK's structural reform
    - Income tax: Uses simulation_modifier to directly modify thresholds
    - Combined: Uses simulation_modifier for both reforms

    Returns:
        List of Reform objects for analysis.
    """
    reforms = []

    # Combined reform (both policies together) - listed first
    # Uses simulation_modifier to apply BOTH reforms after data load
    # (Directly applies SCP structural reform + income tax threshold changes)
    reforms.append(
        Reform(
            id="combined",
            name="Both policies combined",
            description=(
                "Full Scottish Budget 2026-27 package: SCP Premium for under-ones (£40/week) "
                "and income tax threshold uplift (7.4%) applied together."
            ),
            simulation_modifier=_combined_modifier,
        )
    )

    # SCP Premium for under-ones (£40/week for babies under 1)
    # Uses simulation_modifier to directly apply the structural reform from policyengine-uk
    reforms.append(
        Reform(
            id="scp_baby_boost",
            name="SCP Premium for under-ones (£40/week)",
            description=(
                "New SCP Premium for under-ones: £40/week for babies under 1 "
                "(up from £27.15/week). Announced in Scottish Budget 2026-27."
            ),
            simulation_modifier=_scp_baby_boost_modifier,
        )
    )

    # Scottish income tax threshold uplift (7.4%)
    # Uses simulation_modifier to directly modify Scottish rate thresholds
    reforms.append(
        Reform(
            id="income_tax_threshold_uplift",
            name="Income tax threshold uplift (7.4%)",
            description=(
                "Scottish basic and intermediate rate thresholds increased by 7.4%. "
                "Basic rate starts at £16,537, intermediate at £29,527."
            ),
            simulation_modifier=_income_tax_modifier,
        )
    )

    return reforms


# Policy metadata for dashboard
POLICIES = [
    {
        "id": "combined",
        "name": "Both policies combined",
        "description": "Full Scottish Budget 2026-27 package",
        "explanation": """
            The complete Scottish Budget 2026-27 package combines both policy reforms:
            the SCP Premium for under-ones (£40/week for babies under 1) and the income tax
            threshold uplift (7.4% increase to basic and intermediate thresholds). Together,
            these measures deliver targeted support to families with young children while
            also providing tax relief to working Scots.
        """,
    },
    {
        "id": "scp_baby_boost",
        "name": "SCP Premium for under-ones (£40/week)",
        "description": "New SCP Premium for under-ones: £40/week for babies under 1",
        "explanation": """
            The new SCP Premium for under-ones increases the Scottish Child Payment to
            £40/week for families with babies under 1 year old, up from the standard rate
            of £27.15/week. This delivers the strongest package of support for families
            with young children anywhere in the UK, as announced by Finance Secretary
            Shona Robison on 13 January 2026.
        """,
    },
    {
        "id": "income_tax_threshold_uplift",
        "name": "Income tax threshold uplift (7.4%)",
        "description": "Scottish basic and intermediate rate thresholds increased by 7.4%",
        "explanation": """
            The Scottish basic and intermediate income tax rate thresholds are raised by 7.4%.
            The basic rate (20%) threshold rises from £15,398 to £16,537, and the intermediate
            rate (21%) threshold rises from £27,492 to £29,527. The higher rate (42%) remains
            unchanged at £43,663. This means people pay the lower 19% starter rate on more of
            their income.
        """,
    },
]

PRESETS = [
    {
        "id": "scottish-budget-2026",
        "name": "Scottish Budget 2026",
        "policies": ["scp_baby_boost", "income_tax_threshold_uplift"],
    },
]
