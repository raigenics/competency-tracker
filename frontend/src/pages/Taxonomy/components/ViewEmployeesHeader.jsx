import React, { useState, useEffect } from 'react';
import { Download, Share2 } from 'lucide-react';
import { skillApi } from '../../../services/api/skillApi';

/**
 * ViewEmployeesHeader - Header section for View Employees screen
 * 
 * Renders:
 * - Back link
 * - Title with skill name pill
 * - Subtitle with employee count and tip
 * - Export button
 * - KPI strip (3 cards: Avg proficiency, Certified, Teams)
 * - Search section with results count
 * 
 * Props:
 * - skillId: number - The skill ID
 * - skillName: string - The skill name
 * - onBack: function - Callback when back is clicked
 * - onExport: function - Callback when export is clicked
 * - employeeResults: array - Current employee results for filtering
 * - onSearchChange: function - Callback when search input changes
 * - searchValue: string - Current search value
 * - onClear: function - Callback when clear is clicked
 */
const ViewEmployeesHeader = ({
  skillId,
  skillName,
  onBack,
  onExport,
  employeeResults = [],
  onSearchChange,
  searchValue = '',
  onClear
}) => {
  const [summaryData, setSummaryData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch employees summary when skillId changes
  useEffect(() => {
    // Check for null/undefined, but allow skillId = 0 as valid
    if (skillId == null) {
      setSummaryData(null);
      return;
    }

    const fetchSummary = async () => {
      setIsLoading(true);
      try {
        const data = await skillApi.getEmployeesSummary(skillId);
        setSummaryData(data);
      } catch (err) {
        console.error('[ViewEmployeesHeader] Error fetching employees summary:', err);
        setSummaryData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, [skillId]);

  // Determine tag styling for avg proficiency
  const getAvgProficiencyTag = (avg) => {
    if (avg === null || avg === undefined) return { text: '—', className: 'tag' };
    if (avg >= 4.0) return { text: 'Strong', className: 'tagHealthy' };
    if (avg >= 3.0) return { text: 'Good', className: 'tagHealthy' };
    if (avg >= 2.0) return { text: 'Needs depth', className: 'tagWarn' };
    return { text: 'Low', className: 'tagRisk' };
  };

  // Determine tag styling for certified count
  const getCertifiedTag = (count, total) => {
    if (count === 0) return { text: 'Gap', className: 'tagRisk' };
    const ratio = total > 0 ? count / total : 0;
    if (ratio >= 0.5) return { text: 'Strong', className: 'tagHealthy' };
    if (ratio >= 0.25) return { text: 'Partial', className: 'tagWarn' };
    return { text: 'Few', className: 'tagWarn' };
  };

  // Determine tag styling for team count
  const getTeamsTag = (count) => {
    if (count >= 3) return { text: 'Distributed', className: 'tagHealthy' };
    if (count === 2) return { text: 'Limited', className: 'tagWarn' };
    if (count === 1) return { text: 'Single team', className: 'tagRisk' };
    return { text: 'None', className: 'tagRisk' };
  };

  const avgTag = getAvgProficiencyTag(summaryData?.avg_proficiency);
  const certTag = getCertifiedTag(summaryData?.certified_count ?? 0, summaryData?.employee_count ?? 0);
  const teamsTag = getTeamsTag(summaryData?.team_count ?? 0);

  return (
    <>
      {/* Header */}
      <div className="ve-header">
        <div className="ve-header-left">
          {/* Back link row */}
          <div className="ve-crumb-row">
            <button 
              type="button"
              onClick={onBack}
              className="ve-back-link"
            >
              ← Back
            </button>
          </div>

          {/* Title row */}
          <div className="ve-title-row">
            <h1 className="ve-title">Employees with</h1>
            <span className="ve-skill-pill">{skillName}</span>
          </div>

          {/* Subtitle */}
          <div className="ve-sub">
            <span>
              <strong>{isLoading ? '...' : (summaryData?.employee_count ?? employeeResults.length)}</strong> employees found
            </span>
            <span className="ve-meta-dot"></span>
            <span className="ve-hint">Tip: Click a row to expand</span>
          </div>
        </div>

        <div className="ve-header-right">
          <button 
            type="button"
            onClick={onExport}
            className="ve-btn ve-btn-ghost"
          >
            <Download size={14} />
            Export
          </button>
        </div>
      </div>

      {/* KPI Strip - 3 cards */}
      <div className="ve-insight-strip">
        {/* Avg proficiency */}
        <div className="ve-kpi">
          <div className="ve-kpi-top">
            <div>
              <div className="ve-kpi-label">Avg proficiency</div>
              <div className="ve-kpi-value">
                {isLoading ? '...' : (summaryData?.avg_proficiency?.toFixed(1) ?? '—')}
              </div>
            </div>
            <span className={`ve-tag ${avgTag.className}`}>{avgTag.text}</span>
          </div>
        </div>

        {/* Certified */}
        <div className="ve-kpi">
          <div className="ve-kpi-top">
            <div>
              <div className="ve-kpi-label">Certified</div>
              <div className="ve-kpi-value">
                {isLoading ? '...' : (summaryData?.certified_count ?? 0)}
              </div>
            </div>
            <span className={`ve-tag ${certTag.className}`}>{certTag.text}</span>
          </div>
        </div>

        {/* Teams */}
        <div className="ve-kpi">
          <div className="ve-kpi-top">
            <div>
              <div className="ve-kpi-label">Teams</div>
              <div className="ve-kpi-value">
                {isLoading ? '...' : (summaryData?.team_count ?? 0)}
              </div>
            </div>
            <span className={`ve-tag ${teamsTag.className}`}>{teamsTag.text}</span>
          </div>
        </div>
      </div>

      {/* Controls - Search section */}
      <div className="ve-controls">
        <div className="ve-left-controls">
          <div className="ve-search" role="search">
            <span>🔎</span>
            <input 
              type="text"
              placeholder="Search employee, role, team, sub-segment…"
              value={searchValue}
              onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            />
          </div>
        </div>

        <div className="ve-right-controls">
          <span className="ve-hint">
            Showing <span>{employeeResults.length}</span> results
          </span>
          <button 
            type="button"
            onClick={onClear}
            className="ve-btn"
          >
            Clear
          </button>
        </div>
      </div>
    </>
  );
};

export default ViewEmployeesHeader;
