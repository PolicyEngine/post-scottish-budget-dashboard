/**
 * Scottish Budget 2026-27 reform configuration.
 */

// Backend API URL - Modal deployment
export const API_BASE_URL = import.meta.env.VITE_API_URL || "https://policyengine--scottish-budget-api-flask-app.modal.run";

/**
 * Reform metadata for UI display.
 * Includes both household-positive (uplifts, SCP) and household-negative (freezes) reforms.
 */
export const REFORMS = [
  // Income tax threshold uplifts (benefit households)
  {
    id: "income_tax_basic_uplift",
    name: "Basic rate threshold +7.4%",
    description: "Basic rate (20%) threshold: £14,877 → £16,537",
    color: "#0D9488",  // Teal 600
    type: "positive",
  },
  {
    id: "income_tax_intermediate_uplift",
    name: "Intermediate rate threshold +7.4%",
    description: "Intermediate rate (21%) threshold: £26,562 → £29,527",
    color: "#14B8A6",  // Teal 500
    type: "positive",
  },
  // Income tax threshold freezes (cost households - revenue raising)
  {
    id: "higher_rate_freeze",
    name: "Higher rate threshold freeze",
    description: "Higher rate (42%) threshold frozen at £31,092 through 2028-29",
    color: "#F97316",  // Orange 500
    type: "negative",
  },
  {
    id: "advanced_rate_freeze",
    name: "Advanced rate threshold freeze",
    description: "Advanced rate (45%) threshold frozen at £62,430 through 2028-29",
    color: "#FB923C",  // Orange 400
    type: "negative",
  },
  {
    id: "top_rate_freeze",
    name: "Top rate threshold freeze",
    description: "Top rate (48%) threshold frozen at £125,140 through 2028-29",
    color: "#FDBA74",  // Orange 300
    type: "negative",
  },
  // Scottish Child Payment
  {
    id: "scp_inflation",
    name: "SCP inflation adjustment",
    description: "SCP uprated from £27.15 to £28.20/week (+3.9%)",
    color: "#2DD4BF",  // Teal 400
    type: "positive",
  },
  {
    id: "scp_baby_boost",
    name: "SCP Premium for under-ones",
    description: "Extra £11.80/week for babies under 1 (£40/week total from mid-2027)",
    color: "#5EEAD4",  // Teal 300
    type: "positive",
  },
];
