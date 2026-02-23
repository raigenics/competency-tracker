/**
 * DataFreshnessKpi - KPI card for Data Freshness metric
 * 
 * Displays the percentage of employees with at least one skill update
 * in the specified time window.
 * 
 * Data Freshness Calculation:
 * - freshness_percent = (employees_with_update / employees_in_scope) * 100
 * - Filters applied: sub_segment_id, project_id, team_id (same as Skill Update Activity)
 * - Rounding: 1 decimal place
 * 
 * @param {Object} props
 * @param {number|null} props.value - Freshness percentage (0-100), null when loading/error
 * @param {number} props.windowDays - Time window in days (default: 90)
 * @param {boolean} props.loading - Whether data is being fetched
 */
const DataFreshnessKpi = ({ 
  value = null,
  windowDays = 90,
  loading = false
}) => {
  // Display value: show "—" when loading or no data, otherwise show percentage
  const displayValue = loading || value === null ? '—' : `${value}%`;
  
  return (
    <div className="db-kpi">
      <div className="meta">
        <span>Data Freshness</span>
        <span className="db-badge">Window: {windowDays} days</span>
      </div>
      <div className="value">{displayValue}</div>
      <p className="sub">Employees with at least one update in last {windowDays} days</p>
    </div>
  );
};

export default DataFreshnessKpi;
