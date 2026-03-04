import React from 'react';
import { Download, Share2 } from 'lucide-react';

/**
 * ViewEmployeesHeader - Header section for View Employees screen
 * 
 * Renders:
 * - Back link
 * - Title with skill name pill
 * - Subtitle with employee count and tip
 * - Export button
 * - KPI strip (2 cards: Avg proficiency, Certification Coverage)
 * - Search section with results count
 * 
 * Props:
 * - skillId: number - The skill ID
 * - skillName: string - The skill name
 * - onBack: function - Callback when back is clicked
 * - onExport: function - Callback when export is clicked
 * - employeeResults: array - Current employee results for filtering (used for KPI computation)
 * - onSearchChange: function - Callback when search input changes
 * - searchValue: string - Current search value
 * - onClear: function - Callback when clear is clicked
 * - isLoading: boolean - Loading state for employee data
 */
const ViewEmployeesHeader = ({
  skillId: _skillId,
  skillName,
  onBack,
  onExport,
  employeeResults = [],
  onSearchChange,
  searchValue = '',
  onClear,
  isLoading = false
}) => {
  // Compute KPIs from employeeResults — guaranteed skill-scoped
  const total = employeeResults.length;

  // 1. Avg Proficiency (proficiency_level is 1–5 per selected skill)
  const avgProficiency = total > 0
    ? employeeResults.reduce((sum, emp) => sum + (emp.proficiency_level ?? 0), 0) / total
    : null;

  // 2. Cert Coverage % (emp.certified is boolean set by skill_employees_list_service.py)
  const certifiedCount = employeeResults.filter(emp => emp.certified).length;
  const certCoveragePct = total > 0
    ? Math.round((certifiedCount / total) * 100)
    : 0;

  // Determine tag styling for avg proficiency
  const getAvgProficiencyTag = (avg) => {
    if (avg === null || avg === undefined) return { text: '—', className: 'tag' };
    if (avg >= 4.0) return { text: 'Strong', className: 'tagHealthy' };
    if (avg >= 3.0) return { text: 'Good', className: 'tagHealthy' };
    if (avg >= 2.0) return { text: 'Needs depth', className: 'tagWarn' };
    return { text: 'Low', className: 'tagRisk' };
  };

  // Determine tag styling for cert coverage
  const getCertCoverageTag = (pct) => {
    if (pct === 0) return { text: 'Gap', className: 'tagRisk' };
    if (pct >= 50) return { text: 'Strong', className: 'tagHealthy' };
    if (pct >= 25) return { text: 'Partial', className: 'tagWarn' };
    return { text: 'Few', className: 'tagWarn' };
  };

  const avgTag = getAvgProficiencyTag(avgProficiency);
  const certTag = getCertCoverageTag(certCoveragePct);

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
              <strong>{isLoading ? '...' : total}</strong> employees found
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

      {/* KPI Strip - 2 cards */}
      <div className="ve-insight-strip" style={{ gridTemplateColumns: '1fr 1fr' }}>
        {/* Avg proficiency */}
        <div className="ve-kpi">
          <div className="ve-kpi-top">
            <div>
              <div className="ve-kpi-label">Avg proficiency</div>
              <div className="ve-kpi-value">
                {isLoading ? '...' : (avgProficiency?.toFixed(1) ?? '—')}
              </div>
            </div>
            <span className={`ve-tag ${avgTag.className}`}>{avgTag.text}</span>
          </div>
        </div>

        {/* Certification Coverage */}
        <div className="ve-kpi">
          <div className="ve-kpi-top">
            <div>
              <div className="ve-kpi-label">Certification Coverage</div>
              <div className="ve-kpi-value">
                {isLoading ? '...' : `${certCoveragePct}%`}
              </div>
            </div>
            <span className={`ve-tag ${certTag.className}`}>{certTag.text}</span>
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
