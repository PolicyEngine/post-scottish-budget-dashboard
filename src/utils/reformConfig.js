/**
 * Scottish Budget 2026-27 reform configuration.
 *
 * Parameter values extracted from reforms.py - this is the source of truth.
 * We send these parameters to the PolicyEngine hosted API.
 */

// Local backend API (uses policyengine_uk directly)
export const API_BASE_URL = "http://localhost:5001";

// Year for calculations
export const YEAR = 2026;

// SCP constants (from reforms.py)
export const SCP_STANDARD_RATE = 27.15; // £/week
export const SCP_BABY_RATE = 40.0; // £/week for babies under 1
export const SCP_BABY_BOOST = SCP_BABY_RATE - SCP_STANDARD_RATE; // £12.85/week extra
export const WEEKS_IN_YEAR = 52;
export const SCP_BABY_BOOST_ANNUAL = SCP_BABY_BOOST * WEEKS_IN_YEAR; // £668.20/year

// Income threshold for SCP eligibility (approximate - UC-like means test)
export const SCP_INCOME_THRESHOLD = 30000;

/**
 * Income tax threshold uplift reform parameters.
 * From reforms.py _income_tax_threshold_uplift_modifier:
 * - Basic rate (20%) threshold: £3,966 above PA
 * - Intermediate rate (21%) threshold: £16,956 above PA
 */
export const INCOME_TAX_REFORM = {
  "gov.hmrc.income_tax.rates.scotland.rates[1].threshold": {
    "2026-01-01.2100-12-31": 3966,
  },
  "gov.hmrc.income_tax.rates.scotland.rates[2].threshold": {
    "2026-01-01.2100-12-31": 16956,
  },
};

/**
 * Combined Scottish Budget 2026-27 reform (income tax only - SCP is client-side).
 */
export const SCOTTISH_BUDGET_REFORM = {
  ...INCOME_TAX_REFORM,
};

/**
 * Reform metadata for UI display.
 */
export const REFORMS = [
  {
    id: "scp_baby_boost",
    name: "SCP baby boost (£40/week)",
    description: "Extra £12.85/week for babies under 1",
    color: "#2C6496",
    // This is calculated client-side, not via API
    isClientSide: true,
  },
  {
    id: "income_tax_threshold_uplift",
    name: "Income tax threshold uplift (7.4%)",
    description: "7.4% increase in basic and intermediate thresholds",
    color: "#29AB87",
    // This uses API with parameter changes
    isClientSide: false,
    parameters: INCOME_TAX_REFORM,
  },
];

/**
 * Create a household situation for the PolicyEngine API.
 */
export function createHouseholdSituation(inputs) {
  const { employment_income, is_married, partner_income, children_ages } = inputs;

  const people = {
    adult1: {
      age: { [YEAR]: 35 },
      employment_income: { [YEAR]: employment_income },
    },
  };

  const members = ["adult1"];

  if (is_married) {
    people.adult2 = {
      age: { [YEAR]: 33 },
      employment_income: { [YEAR]: partner_income },
    };
    members.push("adult2");
  }

  // Add children
  children_ages.forEach((age, index) => {
    const childId = `child${index + 1}`;
    people[childId] = {
      age: { [YEAR]: age },
    };
    members.push(childId);
  });

  return {
    people,
    benunits: {
      benunit: {
        members,
      },
    },
    households: {
      household: {
        members,
        region: { [YEAR]: "SCOTLAND" },
      },
    },
  };
}

/**
 * Calculate SCP baby boost impact (client-side).
 * From reforms.py: boost applies to households receiving SCP with babies under 1.
 */
export function calculateScpBabyBoost(inputs) {
  const { employment_income, partner_income, children_ages } = inputs;

  // Count babies under 1
  const babiesCount = children_ages.filter((age) => age < 1).length;
  if (babiesCount === 0) return 0;

  // Estimate SCP eligibility (low income + children)
  const totalIncome = employment_income + (partner_income || 0);
  const hasChildren = children_ages.length > 0;
  const likelyEligible = hasChildren && totalIncome < SCP_INCOME_THRESHOLD;

  if (!likelyEligible) return 0;

  // £12.85/week × 52 weeks × number of babies
  return SCP_BABY_BOOST_ANNUAL * babiesCount;
}
