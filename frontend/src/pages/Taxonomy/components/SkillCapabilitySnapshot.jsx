/**
 * SkillCapabilitySnapshot - Presentational component for skill KPI cards
 * 
 * Displays 3 KPI cards under "Capability Snapshot" section:
 * 1. Employees (in scope) - Employees mapped to this skill
 * 2. Certified (count) - Employees with certification for this skill
 * 3. Teams (usage) - Distinct teams with employees having this skill
 * 
 * Props:
 * - employeeCount: number - Count of employees
 * - certifiedCount: number - Count of certified employees
 * - teamCount: number - Count of distinct teams
 * - isLoading: boolean - Loading state
 * 
 * This is a stateless presentational component with no business logic or API calls.
 */
import React from 'react';
import '../CapabilityOverview.css';

const SkillCapabilitySnapshot = ({
  employeeCount = 0,
  certifiedCount = 0,
  teamCount = 0,
  isLoading = false
}) => {
  // Loading skeleton
  if (isLoading) {
    return (
      <div className="co-capability-snapshot">
        <p className="co-snapshot-title">Capability Snapshot</p>
        <div className="co-snapshot-kpis">
          {[1, 2, 3].map((i) => (
            <div key={i} className="co-snapshot-kpi co-snapshot-kpi--loading">
              <div className="co-snapshot-kpi-label">
                <span className="co-skeleton" style={{ width: '60px' }}></span>
                <span className="co-skeleton" style={{ width: '40px' }}></span>
              </div>
              <p className="co-snapshot-kpi-value">
                <span className="co-skeleton" style={{ width: '40px', height: '24px' }}></span>
              </p>
              <div className="co-snapshot-kpi-hint">
                <span className="co-skeleton" style={{ width: '100%' }}></span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="co-capability-snapshot">
      <p className="co-snapshot-title">Capability Snapshot</p>
      
      <div className="co-snapshot-kpis">
        {/* Employees KPI */}
        <div className="co-snapshot-kpi">
          <div className="co-snapshot-kpi-label">
            <span>Employees</span>
            <span>in scope</span>
          </div>
          <p className="co-snapshot-kpi-value">{employeeCount}</p>
          <div className="co-snapshot-kpi-hint">
            Employees mapped to this skill within current filters.
          </div>
        </div>

        {/* Certified KPI */}
        <div className="co-snapshot-kpi">
          <div className="co-snapshot-kpi-label">
            <span>Certified</span>
            <span>count</span>
          </div>
          <p className="co-snapshot-kpi-value">{certifiedCount}</p>
          <div className="co-snapshot-kpi-hint">
            Employees with a certification tagged to this skill.
          </div>
        </div>

        {/* Teams KPI */}
        <div className="co-snapshot-kpi">
          <div className="co-snapshot-kpi-label">
            <span>Teams</span>
            <span>usage</span>
          </div>
          <p className="co-snapshot-kpi-value">{teamCount}</p>
          <div className="co-snapshot-kpi-hint">
            Distinct teams with expertise in this technology.
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillCapabilitySnapshot;
