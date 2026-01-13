import "./PovertyImpactTable.css";

/**
 * Table showing poverty rate impacts by year.
 */
export default function PovertyImpactTable({ data, title, policyName = "the selected policy" }) {
  if (!data || data.length === 0) {
    return (
      <div className="poverty-table-container">
        <h3 className="chart-title">{title || "Poverty impact"}</h3>
        <div className="chart-empty">No data available</div>
      </div>
    );
  }

  // Group data by year
  const byYear = {};
  data.forEach((row) => {
    const year = row.year;
    if (!byYear[year]) {
      byYear[year] = {};
    }
    byYear[year][row.metric] = row.value;
  });

  const years = Object.keys(byYear).sort();

  const formatRate = (value) => {
    if (value == null) return "—";
    return `${value.toFixed(2)}%`;
  };

  const formatChange = (value) => {
    if (value == null) return "—";
    const sign = value >= 0 ? "+" : "";
    return `${sign}${(value).toFixed(3)}pp`;
  };

  return (
    <div className="poverty-table-container">
      <h3 className="chart-title">{title || "Poverty rate impact by year"}</h3>
      <p className="chart-description">
        Change in poverty rates under {policyName} compared to baseline.
      </p>

      <div className="table-wrapper">
        <table className="poverty-table">
          <thead>
            <tr>
              <th rowSpan={2}>Year</th>
              <th colSpan={3}>Overall poverty rate</th>
              <th colSpan={3}>Child poverty rate</th>
            </tr>
            <tr>
              <th>Baseline</th>
              <th>Reform</th>
              <th>Change</th>
              <th>Baseline</th>
              <th>Reform</th>
              <th>Change</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => {
              const d = byYear[year];
              return (
                <tr key={year}>
                  <td className="year-cell">{year}–{(parseInt(year) + 1).toString().slice(-2)}</td>
                  <td>{formatRate(d.poverty_rate_baseline)}</td>
                  <td>{formatRate(d.poverty_rate_reform)}</td>
                  <td className="change-cell">{formatChange(d.poverty_rate_change)}</td>
                  <td>{formatRate(d.child_poverty_rate_baseline)}</td>
                  <td>{formatRate(d.child_poverty_rate_reform)}</td>
                  <td className="change-cell">{formatChange(d.child_poverty_rate_change)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="table-note">
        Poverty rates shown as percentage of population. Change shown in percentage points (pp).
      </p>
    </div>
  );
}
