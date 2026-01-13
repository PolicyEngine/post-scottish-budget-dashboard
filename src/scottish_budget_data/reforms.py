"""Scottish Budget 2026-27 reform definitions.

This module defines the policy reforms for the Scottish Budget analysis.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional
import numpy as np


# Constants for SCP baby boost
WEEKS_IN_YEAR = 52
SCP_STANDARD_RATE = 27.15  # £/week (current rate from Apr 2025)
SCP_BABY_RATE = 40.00  # £/week for babies under 1 (from Scottish Budget 2026)
SCP_BABY_BOOST = SCP_BABY_RATE - SCP_STANDARD_RATE  # Extra £12.85/week


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

    def to_scenario(self):
        """Convert to PolicyEngine Scenario."""
        from policyengine_uk.utils.scenario import Scenario

        if self.simulation_modifier and self.parameter_changes:
            return Scenario(
                simulation_modifier=self.simulation_modifier,
                parameter_changes=self.parameter_changes,
            )
        elif self.simulation_modifier:
            return Scenario(simulation_modifier=self.simulation_modifier)
        elif self.parameter_changes:
            return Scenario(parameter_changes=self.parameter_changes)
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


def _scp_baby_boost_modifier(sim):
    """Apply Scottish Child Payment baby boost for children under 1.

    The Scottish Budget 2026-27 increased SCP to £40/week for babies under 1,
    up from the standard £27.15/week. This modifier adds the extra payment
    directly to the scottish_child_payment variable for eligible families.

    The boost applies to:
    - Households in Scotland (already receiving SCP)
    - With children under 1 year old
    - Receiving qualifying benefits (checked via existing SCP > 0)
    """
    for year in [2026, 2027, 2028, 2029, 2030]:
        # Get current SCP values (already filters for Scotland + qualifying benefits)
        current_scp = sim.calculate("scottish_child_payment", year)

        # Get person-level age to count babies
        age = sim.calculate("age", year, map_to="person")
        is_baby = np.array(age) < 1

        # Map babies to benefit units
        person_benunit_id = sim.calculate("benunit_id", year, map_to="person")
        benunit_id = sim.calculate("benunit_id", year, map_to="benunit")

        # Count babies per benefit unit
        babies_per_benunit = np.zeros(len(benunit_id))
        bu_id_to_idx = {bu_id: idx for idx, bu_id in enumerate(benunit_id)}

        for person_bu_id, baby in zip(person_benunit_id, is_baby):
            if baby and person_bu_id in bu_id_to_idx:
                babies_per_benunit[bu_id_to_idx[person_bu_id]] += 1

        # Calculate baby boost (£12.85/week extra × 52 weeks per baby)
        annual_boost = babies_per_benunit * SCP_BABY_BOOST * WEEKS_IN_YEAR

        # Only apply boost to families already receiving SCP (i.e., in Scotland + qualifying)
        already_receives_scp = np.array(current_scp) > 0
        baby_boost = np.where(already_receives_scp, annual_boost, 0)

        # Add boost to current SCP
        new_scp = np.array(current_scp) + baby_boost
        sim.set_input("scottish_child_payment", year, new_scp)

    return sim


def get_scottish_budget_reforms() -> list[Reform]:
    """Get list of Scottish Budget 2026-27 reforms.

    Returns:
        List of Reform objects for analysis.
    """
    reforms = []

    # Two-child limit abolition (Scotland top-up to fully offset)
    # This effectively removes the two-child limit for Scottish households
    reforms.append(
        Reform(
            id="two_child_limit_abolition",
            name="Two-child limit abolition",
            description="Abolish the two-child limit on benefits for Scottish households",
            parameter_changes={
                "gov.dwp.universal_credit.elements.child.limit.child_count": {
                    "2026-01-01": float("inf"),
                },
                "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
                    "2026-01-01": float("inf"),
                },
            },
        )
    )

    # SCP Baby Boost (£40/week for babies under 1)
    reforms.append(
        Reform(
            id="scp_baby_boost",
            name="SCP baby boost (£40/week)",
            description=(
                "Scottish Child Payment boosted to £40/week for babies under 1 "
                "(up from £27.15/week). Announced in Scottish Budget 2026-27."
            ),
            simulation_modifier=_scp_baby_boost_modifier,
        )
    )

    # Combined Scottish Budget (all measures)
    reforms.append(
        Reform(
            id="scottish_budget_2026_combined",
            name="Scottish Budget 2026 (combined)",
            description=(
                "All Scottish Budget 2026-27 measures combined: "
                "two-child limit abolition and SCP baby boost to £40/week"
            ),
            parameter_changes={
                "gov.dwp.universal_credit.elements.child.limit.child_count": {
                    "2026-01-01": float("inf"),
                },
                "gov.dwp.tax_credits.child_tax_credit.limit.child_count": {
                    "2026-01-01": float("inf"),
                },
            },
            simulation_modifier=_scp_baby_boost_modifier,
        )
    )

    return reforms


# Policy metadata for dashboard
POLICIES = [
    {
        "id": "two_child_limit_abolition",
        "name": "Two-child limit abolition",
        "description": "Abolish the two-child limit on benefits",
        "explanation": """
            The two-child limit restricts Universal Credit and Child Tax Credit payments
            to a maximum of two children per family. The Scottish Government's top-up
            payment effectively abolishes this limit for Scottish households, allowing
            families to receive full child-related benefit payments for all children.
        """,
    },
    {
        "id": "scp_baby_boost",
        "name": "SCP baby boost (£40/week)",
        "description": "Scottish Child Payment boosted to £40/week for babies under 1",
        "explanation": """
            The Scottish Child Payment is boosted to £40/week for families with babies
            under 1 year old, up from the standard rate of £27.15/week. This delivers
            the strongest package of support for families with young children anywhere
            in the UK, as announced by Finance Secretary Shona Robison on 13 January 2026.
        """,
    },
]

PRESETS = [
    {
        "id": "scottish-budget-2026",
        "name": "Scottish Budget 2026",
        "policies": ["two_child_limit_abolition", "scp_baby_boost"],
    },
]
