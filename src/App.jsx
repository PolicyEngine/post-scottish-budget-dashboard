import { useState, useEffect } from "react";
import Dashboard from "./components/Dashboard";
import HouseholdCalculator from "./components/HouseholdCalculator";
import "./App.css";

const POLICIES = [
  { id: "scp_baby_boost", name: "SCP baby boost" },
  { id: "income_tax_threshold_uplift", name: "Income tax threshold uplift" },
];

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedPolicy, setSelectedPolicy] = useState("scp_baby_boost");

  // Initialize from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get("tab");
    if (tabParam === "personal") {
      setActiveTab("personal");
    }
  }, []);

  // Update URL when tab changes
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (activeTab === "personal") {
      params.set("tab", "personal");
    } else {
      params.delete("tab");
    }
    const newUrl = params.toString()
      ? `?${params.toString()}`
      : window.location.pathname;
    window.history.replaceState({}, "", newUrl);
  }, [activeTab]);

  return (
    <div className="app">
      <header className="title-row">
        <div className="title-row-inner">
          <h1>Scottish Budget 2026</h1>
          <div className="policy-selector">
            {POLICIES.map((policy) => (
              <label key={policy.id} className="policy-option">
                <input
                  type="radio"
                  name="policy"
                  value={policy.id}
                  checked={selectedPolicy === policy.id}
                  onChange={(e) => setSelectedPolicy(e.target.value)}
                />
                <span>{policy.name}</span>
              </label>
            ))}
          </div>
        </div>
      </header>
      <main className="main-content">
        {/* Tab navigation */}
        <div className="tab-navigation">
          <button
            className={`tab-button ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <rect x="3" y="3" width="7" height="9" />
              <rect x="14" y="3" width="7" height="5" />
              <rect x="14" y="12" width="7" height="9" />
              <rect x="3" y="16" width="7" height="5" />
            </svg>
            Population impact
          </button>
          <button
            className={`tab-button ${activeTab === "personal" ? "active" : ""}`}
            onClick={() => setActiveTab("personal")}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            Personal impact
          </button>
        </div>

        {activeTab === "personal" ? (
          <div className="personal-impact-container">
            <HouseholdCalculator />
          </div>
        ) : (
          <Dashboard selectedPolicy={selectedPolicy} />
        )}
      </main>
    </div>
  );
}

export default App;
