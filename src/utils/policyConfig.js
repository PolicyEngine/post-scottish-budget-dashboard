// Policy configuration for Scottish Budget dashboard

export const POLICY_COLORS = {
  "SCP inflation adjustment": "#6B46C1",                // Purple 600 (SCP base)
  "SCP Premium for under-ones": "#0D9488",              // Teal 600 (spending/benefit)
  "Income tax threshold uplift": "#F59E0B",             // Amber 500 (tax cut)
};

export const POLICY_IDS = {
  scp_inflation: "scp_inflation",
  scp_baby_boost: "scp_baby_boost",
  income_tax_threshold_uplift: "income_tax_threshold_uplift",
};

export const POLICY_NAMES = {
  scp_inflation: "SCP inflation adjustment",
  scp_baby_boost: "SCP Premium for under-ones",
  income_tax_threshold_uplift: "Income tax threshold uplift",
};

export const ALL_POLICY_IDS = ["scp_inflation", "scp_baby_boost", "income_tax_threshold_uplift"];

export const ALL_POLICY_NAMES = ["SCP inflation adjustment", "SCP Premium for under-ones", "Income tax threshold uplift"];
