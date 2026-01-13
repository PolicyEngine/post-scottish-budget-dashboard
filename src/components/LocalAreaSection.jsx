import { useState, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import "./LocalAreaSection.css";

// Scottish constituencies with sample data
const SCOTTISH_CONSTITUENCIES = [
  { name: "Aberdeen North", region: "North East Scotland", households: 42000, avgGain: 320, povertyReduction: 1.2 },
  { name: "Aberdeen South", region: "North East Scotland", households: 44000, avgGain: 280, povertyReduction: 0.9 },
  { name: "Aberdeenshire North and Moray East", region: "North East Scotland", households: 48000, avgGain: 295, povertyReduction: 1.0 },
  { name: "Airdrie and Shotts", region: "Central Scotland", households: 39000, avgGain: 410, povertyReduction: 1.8 },
  { name: "Alloa and Grangemouth", region: "Mid Scotland and Fife", households: 41000, avgGain: 355, povertyReduction: 1.4 },
  { name: "Angus and Perthshire Glens", region: "North East Scotland", households: 46000, avgGain: 265, povertyReduction: 0.8 },
  { name: "Arbroath and Broughty Ferry", region: "North East Scotland", households: 43000, avgGain: 340, povertyReduction: 1.3 },
  { name: "Argyll, Bute and South Lochaber", region: "Highlands and Islands", households: 38000, avgGain: 290, povertyReduction: 1.0 },
  { name: "Ayr", region: "South Scotland", households: 40000, avgGain: 380, povertyReduction: 1.5 },
  { name: "Bathgate and Linlithgow", region: "Lothian", households: 45000, avgGain: 310, povertyReduction: 1.1 },
  { name: "Caithness, Sutherland and Ross", region: "Highlands and Islands", households: 35000, avgGain: 305, povertyReduction: 1.2 },
  { name: "Central Ayrshire", region: "South Scotland", households: 41000, avgGain: 395, povertyReduction: 1.6 },
  { name: "Coatbridge and Bellshill", region: "Central Scotland", households: 42000, avgGain: 425, povertyReduction: 1.9 },
  { name: "Cowdenbeath and Kirkcaldy", region: "Mid Scotland and Fife", households: 44000, avgGain: 385, povertyReduction: 1.5 },
  { name: "Cumbernauld and Kirkintilloch", region: "Central Scotland", households: 43000, avgGain: 350, povertyReduction: 1.3 },
  { name: "Dumbarton", region: "West Scotland", households: 39000, avgGain: 365, povertyReduction: 1.4 },
  { name: "Dumfriesshire", region: "South Scotland", households: 37000, avgGain: 285, povertyReduction: 0.9 },
  { name: "Dundee Central", region: "North East Scotland", households: 38000, avgGain: 430, povertyReduction: 2.0 },
  { name: "Dunfermline and Dollar", region: "Mid Scotland and Fife", households: 47000, avgGain: 295, povertyReduction: 1.0 },
  { name: "East Kilbride", region: "Central Scotland", households: 45000, avgGain: 340, povertyReduction: 1.2 },
  { name: "Edinburgh East and Musselburgh", region: "Lothian", households: 48000, avgGain: 375, povertyReduction: 1.4 },
  { name: "Edinburgh North and Leith", region: "Lothian", households: 52000, avgGain: 345, povertyReduction: 1.2 },
  { name: "Edinburgh South", region: "Lothian", households: 46000, avgGain: 260, povertyReduction: 0.7 },
  { name: "Edinburgh South West", region: "Lothian", households: 49000, avgGain: 285, povertyReduction: 0.9 },
  { name: "Edinburgh West", region: "Lothian", households: 47000, avgGain: 250, povertyReduction: 0.6 },
  { name: "Falkirk", region: "Central Scotland", households: 43000, avgGain: 365, povertyReduction: 1.4 },
  { name: "Glasgow East", region: "Glasgow", households: 41000, avgGain: 485, povertyReduction: 2.4 },
  { name: "Glasgow North", region: "Glasgow", households: 44000, avgGain: 440, povertyReduction: 2.1 },
  { name: "Glasgow North East", region: "Glasgow", households: 40000, avgGain: 510, povertyReduction: 2.6 },
  { name: "Glasgow South", region: "Glasgow", households: 45000, avgGain: 395, povertyReduction: 1.7 },
  { name: "Glasgow South West", region: "Glasgow", households: 42000, avgGain: 470, povertyReduction: 2.3 },
  { name: "Glasgow West", region: "Glasgow", households: 43000, avgGain: 365, povertyReduction: 1.5 },
  { name: "Glenrothes and Mid Fife", region: "Mid Scotland and Fife", households: 42000, avgGain: 375, povertyReduction: 1.5 },
  { name: "Gordon and Buchan", region: "North East Scotland", households: 47000, avgGain: 255, povertyReduction: 0.7 },
  { name: "Hamilton and Clyde Valley", region: "Central Scotland", households: 44000, avgGain: 405, povertyReduction: 1.7 },
  { name: "Inverclyde and Renfrewshire West", region: "West Scotland", households: 40000, avgGain: 390, povertyReduction: 1.6 },
  { name: "Inverness, Skye and West Ross-shire", region: "Highlands and Islands", households: 43000, avgGain: 310, povertyReduction: 1.1 },
  { name: "Kilmarnock", region: "South Scotland", households: 41000, avgGain: 400, povertyReduction: 1.7 },
  { name: "Livingston", region: "Lothian", households: 46000, avgGain: 335, povertyReduction: 1.2 },
  { name: "Lothian East", region: "Lothian", households: 50000, avgGain: 270, povertyReduction: 0.8 },
  { name: "Midlothian", region: "Lothian", households: 44000, avgGain: 325, povertyReduction: 1.1 },
  { name: "Moray West, Nairn and Strathspey", region: "Highlands and Islands", households: 40000, avgGain: 285, povertyReduction: 0.9 },
  { name: "Motherwell, Wishaw and Carluke", region: "Central Scotland", households: 46000, avgGain: 420, povertyReduction: 1.8 },
  { name: "Na h-Eileanan an Iar", region: "Highlands and Islands", households: 12000, avgGain: 295, povertyReduction: 1.0 },
  { name: "North Ayrshire and Arran", region: "South Scotland", households: 38000, avgGain: 385, povertyReduction: 1.6 },
  { name: "North East Fife", region: "Mid Scotland and Fife", households: 41000, avgGain: 260, povertyReduction: 0.7 },
  { name: "Orkney and Shetland", region: "Highlands and Islands", households: 22000, avgGain: 275, povertyReduction: 0.8 },
  { name: "Paisley and Renfrewshire North", region: "West Scotland", households: 43000, avgGain: 360, povertyReduction: 1.4 },
  { name: "Paisley and Renfrewshire South", region: "West Scotland", households: 41000, avgGain: 405, povertyReduction: 1.7 },
  { name: "Perth and Kinross-shire", region: "Mid Scotland and Fife", households: 45000, avgGain: 265, povertyReduction: 0.8 },
  { name: "Rutherglen", region: "Glasgow", households: 42000, avgGain: 390, povertyReduction: 1.6 },
  { name: "Stirling and Strathallan", region: "Mid Scotland and Fife", households: 44000, avgGain: 290, povertyReduction: 0.9 },
  { name: "West Aberdeenshire and Kincardine", region: "North East Scotland", households: 46000, avgGain: 245, povertyReduction: 0.6 },
  { name: "West Dunbartonshire", region: "West Scotland", households: 39000, avgGain: 420, povertyReduction: 1.9 },
];

// Scottish regions for grouping
const SCOTTISH_REGIONS = [
  "All regions",
  "Central Scotland",
  "Glasgow",
  "Highlands and Islands",
  "Lothian",
  "Mid Scotland and Fife",
  "North East Scotland",
  "South Scotland",
  "West Scotland",
];

export default function LocalAreaSection() {
  const [selectedConstituency, setSelectedConstituency] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("All regions");
  const [sortBy, setSortBy] = useState("avgGain");
  const [sortOrder, setSortOrder] = useState("desc");

  // Filter constituencies by region
  const filteredConstituencies = useMemo(() => {
    let filtered = [...SCOTTISH_CONSTITUENCIES];
    if (selectedRegion !== "All regions") {
      filtered = filtered.filter(c => c.region === selectedRegion);
    }
    return filtered.sort((a, b) => {
      const multiplier = sortOrder === "desc" ? -1 : 1;
      return (a[sortBy] - b[sortBy]) * multiplier;
    });
  }, [selectedRegion, sortBy, sortOrder]);

  // Get selected constituency data
  const constituencyData = selectedConstituency
    ? SCOTTISH_CONSTITUENCIES.find(c => c.name === selectedConstituency)
    : null;

  // Prepare chart data for regional comparison
  const regionalData = useMemo(() => {
    const regionStats = {};
    SCOTTISH_CONSTITUENCIES.forEach(c => {
      if (!regionStats[c.region]) {
        regionStats[c.region] = { region: c.region, totalGain: 0, count: 0, totalPovertyReduction: 0 };
      }
      regionStats[c.region].totalGain += c.avgGain;
      regionStats[c.region].totalPovertyReduction += c.povertyReduction;
      regionStats[c.region].count += 1;
    });
    return Object.values(regionStats).map(r => ({
      region: r.region.replace("and ", "& "),
      avgGain: Math.round(r.totalGain / r.count),
      povertyReduction: +(r.totalPovertyReduction / r.count).toFixed(1),
    })).sort((a, b) => b.avgGain - a.avgGain);
  }, []);

  // Top and bottom constituencies
  const topConstituencies = [...SCOTTISH_CONSTITUENCIES]
    .sort((a, b) => b.avgGain - a.avgGain)
    .slice(0, 5);
  const bottomConstituencies = [...SCOTTISH_CONSTITUENCIES]
    .sort((a, b) => a.avgGain - b.avgGain)
    .slice(0, 5);

  return (
    <div className="local-area-section">
      {/* Constituency Selector */}
      <div className="section-box">
        <h3 className="chart-title">Select a constituency</h3>
        <p className="chart-description">
          Choose a Scottish constituency to see the estimated impact of the budget on households in that area.
        </p>
        <div className="constituency-controls">
          <select
            className="chart-select"
            value={selectedRegion}
            onChange={(e) => {
              setSelectedRegion(e.target.value);
              setSelectedConstituency("");
            }}
          >
            {SCOTTISH_REGIONS.map(region => (
              <option key={region} value={region}>{region}</option>
            ))}
          </select>
          <select
            className="chart-select constituency-select"
            value={selectedConstituency}
            onChange={(e) => setSelectedConstituency(e.target.value)}
          >
            <option value="">Select constituency...</option>
            {filteredConstituencies.map(c => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>

        {/* Constituency Details */}
        {constituencyData && (
          <div className="constituency-details">
            <h4 className="constituency-name">{constituencyData.name}</h4>
            <p className="constituency-region">{constituencyData.region}</p>
            <div className="constituency-metrics">
              <div className="metric-card">
                <span className="metric-label">Average household gain</span>
                <span className="metric-value">£{constituencyData.avgGain}/year</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Poverty rate reduction</span>
                <span className="metric-value">{constituencyData.povertyReduction}pp</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Households</span>
                <span className="metric-value">{(constituencyData.households / 1000).toFixed(0)}k</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Regional Comparison Chart */}
      <div className="section-box">
        <h3 className="chart-title">Regional comparison</h3>
        <p className="chart-description">
          Average household gain by Scottish region. Urban areas like Glasgow see larger gains due to
          higher concentrations of households affected by the two-child limit.
        </p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={regionalData} layout="vertical" margin={{ top: 20, right: 30, left: 150, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis type="number" tickFormatter={(v) => `£${v}`} />
              <YAxis type="category" dataKey="region" width={140} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value, name) => {
                  if (name === "avgGain") return [`£${value}`, "Avg. gain"];
                  return [value, name];
                }}
              />
              <Bar dataKey="avgGain" fill="#319795" name="Avg. gain" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top and Bottom Constituencies */}
      <div className="charts-row">
        <div className="section-box">
          <h3 className="chart-title">Highest impact constituencies</h3>
          <p className="chart-description">
            Constituencies with the largest average household gains from the budget.
          </p>
          <div className="constituency-list">
            {topConstituencies.map((c, i) => (
              <div key={c.name} className="constituency-item">
                <span className="rank">{i + 1}</span>
                <div className="constituency-info">
                  <span className="name">{c.name}</span>
                  <span className="region">{c.region}</span>
                </div>
                <span className="gain">£{c.avgGain}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="section-box">
          <h3 className="chart-title">Lowest impact constituencies</h3>
          <p className="chart-description">
            Constituencies with the smallest average household gains from the budget.
          </p>
          <div className="constituency-list">
            {bottomConstituencies.map((c, i) => (
              <div key={c.name} className="constituency-item">
                <span className="rank">{SCOTTISH_CONSTITUENCIES.length - 4 + i}</span>
                <div className="constituency-info">
                  <span className="name">{c.name}</span>
                  <span className="region">{c.region}</span>
                </div>
                <span className="gain">£{c.avgGain}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
