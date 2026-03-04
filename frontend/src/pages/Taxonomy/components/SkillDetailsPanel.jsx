import React, { useState, useEffect } from 'react';
import { Info, Users, Award, ArrowRight, ArrowLeft } from 'lucide-react';
import { skillApi } from '../../../services/api/skillApi';
import TalentExportMenu from '../../../components/TalentExportMenu';
import talentExportService from '../../../services/talentExportService';
import EmployeeProfileDrawer from '../../../components/EmployeeProfileDrawer';
import SkillDetailHeader from './SkillDetailHeader';
import SkillCapabilitySnapshot from './SkillCapabilitySnapshot';
import SkillProficiencyBreakdown from './SkillProficiencyBreakdown';
import SkillContextCard from './SkillContextCard';
import ViewEmployeesHeader from './ViewEmployeesHeader';
import '../CapabilityOverview.css';

const SkillDetailsPanel = ({ 
  skill, 
  showViewAll = false, 
  onViewAll, 
  onBackToSummary,
  categoryCoverage = null,
  categoryCoverageLoading = false,
  categoryCoverageError = null,
  kpiData = null,
  kpiLoading = false,
  kpiError = null,
  employeeCount = null,
  categoryDistribution = []
}) => {
  const [summaryData, setSummaryData] = useState(null);
  const [snapshotData, setSnapshotData] = useState(null);
  const [proficiencyData, setProficiencyData] = useState(null);
  const [leadingSubSegmentData, setLeadingSubSegmentData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSnapshotLoading, setIsSnapshotLoading] = useState(false);
  const [isProficiencyLoading, setIsProficiencyLoading] = useState(false);
  const [isLeadingSubSegmentLoading, setIsLeadingSubSegmentLoading] = useState(false);
  const [error, setError] = useState(null);
  const [employeeResults, setEmployeeResults] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [_isExporting, setIsExporting] = useState(false);
  const [_exportError, setExportError] = useState(null);
  
  // Drawer state (matches TalentResultsTable pattern)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedEmployeeIndex, setSelectedEmployeeIndex] = useState(0);
  
  // Search state for View Employees header
  const [searchValue, setSearchValue] = useState('');
  
  // Handle View Profile click - open drawer
  const handleViewProfile = (index) => {
    setSelectedEmployeeIndex(index);
    setIsDrawerOpen(true);
  };
  
  // Handle drawer navigation (prev/next)
  const handleDrawerNavigate = (newIndex) => {
    setSelectedEmployeeIndex(newIndex);
  };
  // Fetch skill summary when skill changes
  useEffect(() => {
    // Normalize skill ID - handle both 'id' (from mock data) and 'skill_id' (from API)
    const skillId = skill?.skill_id || skill?.id;
    
    if (!skill || !skillId) {
      setSummaryData(null);
      setSnapshotData(null);
      setProficiencyData(null);
      setLeadingSubSegmentData(null);
      return;
    }

    const fetchSummary = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await skillApi.getSkillSummary(skillId);
        setSummaryData(data);
      } catch (err) {
        console.error('Error fetching skill summary:', err);
        setError(err.message || 'Failed to load skill data');
        setSummaryData(null);
      } finally {
        setIsLoading(false);
      }
    };

    const fetchSnapshot = async () => {
      setIsSnapshotLoading(true);
      try {
        const data = await skillApi.getCapabilitySnapshot(skillId);
        setSnapshotData(data);
      } catch (err) {
        console.error('Error fetching capability snapshot:', err);
        setSnapshotData(null);
      } finally {
        setIsSnapshotLoading(false);
      }
    };

    const fetchProficiency = async () => {
      setIsProficiencyLoading(true);
      try {
        const data = await skillApi.getProficiencyBreakdown(skillId);
        setProficiencyData(data);
      } catch (err) {
        console.error('Error fetching proficiency breakdown:', err);
        setProficiencyData(null);
      } finally {
        setIsProficiencyLoading(false);
      }
    };

    const fetchLeadingSubSegment = async () => {
      setIsLeadingSubSegmentLoading(true);
      try {
        const data = await skillApi.getLeadingSubSegment(skillId);
        setLeadingSubSegmentData(data);
      } catch (err) {
        console.error('Error fetching leading sub-segment:', err);
        setLeadingSubSegmentData(null);
      } finally {
        setIsLeadingSubSegmentLoading(false);
      }
    };

    fetchSummary();
    fetchSnapshot();
    fetchProficiency();
    fetchLeadingSubSegment();
  }, [skill]);

  // Fetch employee details when "View All" is shown
  useEffect(() => {
    const skillId = skill?.skill_id || skill?.id;
    
    if (showViewAll && skillId) {
      const fetchEmployees = async () => {
        setIsLoading(true);
        try {
          const response = await skillApi.getEmployeesList(skillId);
          setEmployeeResults(response.employees || []);
        } catch (err) {
          console.error('Error fetching employees:', err);
          setError(err.message || 'Failed to load employees');
          setEmployeeResults([]);
        } finally {
          setIsLoading(false);
        }
      };
      fetchEmployees();
    }
  }, [showViewAll, skill]);

  // Clear selection when results change
  useEffect(() => {
    setSelectedIds(new Set());
  }, [employeeResults]);

  const _handleSelectionChange = (newSelection) => {
    setSelectedIds(newSelection);
  };

  const handleExportAll = async () => {
    setIsExporting(true);
    setExportError(null);
    
    try {
      // Create a mock filters object with just the skill name
      const filters = {
        skills: [skill.name],
        subSegment: 'all',
        team: '',
        role: '',
        proficiency: { min: 0, max: 5 },
        experience: { min: 0, max: 20 }
      };
      await talentExportService.exportAllTalent(filters, `skill_${skill.name.replace(/\s+/g, '_')}_all`);
    } catch (err) {
      console.error('Export all failed:', err);
      setExportError(err.message || 'Failed to export results');
    } finally {
      setIsExporting(false);
    }
  };

  const _handleExportSelected = async () => {
    setIsExporting(true);
    setExportError(null);
    
    try {
      const selectedEmployeeIds = Array.from(selectedIds);
      const filters = {
        skills: [skill.name],
        subSegment: 'all',
        team: '',
        role: '',
        proficiency: { min: 0, max: 5 },
        experience: { min: 0, max: 20 }
      };
      await talentExportService.exportSelectedTalent(filters, selectedEmployeeIds, `skill_${skill.name.replace(/\s+/g, '_')}_selected`);
    } catch (err) {
      console.error('Export selected failed:', err);
      setExportError(err.message || 'Failed to export selected results');
    } finally {
      setIsExporting(false);
    }
  };

  const handleViewAllClick = () => {
    if (onViewAll) {
      onViewAll();
    }
  };

  const handleBackClick = () => {
    if (onBackToSummary) {
      onBackToSummary();
    }
  };

  // Derived max skill count for bar width calculation
  const maxSkillCount = categoryDistribution[0]?.skill_count || 1;

  if (!skill) {
    return (
      <div className="co-card capability-overview co-details-panel">
        {/* SECTION A: Detail Header */}
        <div className="co-detail-header">
          <div>
            <h2 className="co-detail-title">Organisation Capability Summary</h2>
            <p className="co-detail-sub">
              Snapshot of skill distribution across all sub-segments
              <span className="co-scope-badge">ADT · AU</span>
            </p>
          </div>
          {/* Note: Toggle buttons (Summary/Gaps/Trends) intentionally omitted per requirements */}
        </div>

        {/* SECTION B: Horizontal Divider */}
        <div className="co-detail-divider"></div>

        {/* SECTIONS C-F: Scrollable Insight Area */}
        <div className="co-insight-area">
          <div className="co-insight-grid">
            {/* SECTION C: Two highlight cards */}
            {/* Card 1: Most populated */}
            <div className="co-insight-card">
              <div className="co-ic-label">Most populated</div>
              <div className="co-ic-value med">
                {categoryCoverageLoading ? (
                  'Loading...'
                ) : categoryCoverageError ? (
                  '—'
                ) : categoryCoverage?.most_populated_category ? (
                  categoryCoverage.most_populated_category.category_name
                ) : (
                  'No employees in scope'
                )}
              </div>
              <div className="co-ic-sub good">
                {categoryCoverage?.most_populated_category?.skill_count 
                  ? `${categoryCoverage.most_populated_category.skill_count} skills · highest employee concentration`
                  : ''}
              </div>
            </div>

            {/* Card 2: Least populated */}
            <div className="co-insight-card">
              <div className="co-ic-label">Least populated</div>
              <div className="co-ic-value med">
                {categoryCoverageLoading ? (
                  'Loading...'
                ) : categoryCoverageError ? (
                  '—'
                ) : categoryCoverage?.least_populated_category ? (
                  categoryCoverage.least_populated_category.category_name
                ) : (
                  'No employees in scope'
                )}
              </div>
              <div className="co-ic-sub warn">
                {categoryCoverage?.least_populated_category?.skill_count 
                  ? `${categoryCoverage.least_populated_category.skill_count} skills · smaller bench vs peers`
                  : ''}
              </div>
            </div>

            {/* SECTION D: Skill distribution by category (full width) */}
            <div className="co-insight-card full">
              <div className="co-ic-label">Skill distribution by category</div>
              <div className="co-bar-chart">
                {categoryDistribution.length === 0 ? (
                  <div className="co-bar-row">
                    <span className="co-bar-row-label">No data available</span>
                  </div>
                ) : (
                  categoryDistribution.map((cat, idx) => (
                    <div className="co-bar-row" key={cat.category_id}>
                      <span className="co-bar-row-label">{cat.category_name}</span>
                      <div className="co-bar-track">
                        <div 
                          className={`co-bar-fill ${idx < 3 ? 'hi' : ''}`}
                          style={{ width: `${(cat.skill_count / maxSkillCount) * 100}%` }}
                        />
                      </div>
                      <span className={`co-bar-count ${idx < 3 ? 'hi' : ''}`}>{cat.skill_count}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* SECTION E: Two KPI cards - Avg proficiency + Certification coverage */}
            <div className="co-insight-card">
              <div className="co-ic-label">Avg proficiency</div>
              <div className="co-ic-value">
                {kpiLoading ? (
                  '...'
                ) : kpiError ? (
                  '—'
                ) : kpiData?.avg_proficiency != null ? (
                  <>
                    {kpiData.avg_proficiency.toFixed(2)}
                    <span className="co-ic-suffix"> / 5</span>
                  </>
                ) : (
                  '—'
                )}
              </div>
              <div className="co-ic-sub">
                Across {employeeCount ?? '—'} mapped employees
              </div>
            </div>

            <div className="co-insight-card">
              <div className="co-ic-label">Certification coverage</div>
              <div className="co-ic-value">
                {kpiLoading ? (
                  '...'
                ) : kpiError ? (
                  '—'
                ) : kpiData?.total_certifications ?? '—'}
              </div>
              <div className="co-ic-sub">Active certs in scope</div>
            </div>
          </div>

          {/* SECTION F: What to explore */}
          <div className="co-explore-card">
            <div className="co-ic-label">What to explore</div>
            <div className="co-explore-content">
              → Click any <strong>category in the tree</strong> to see employee depth and proficiency distribution<br />
              → Use <strong>search</strong> to jump directly to a technology or skill<br />
              → Switch to <strong>Gaps view</strong> to identify under-resourced areas
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show "View All" results view (View C: Employee List)
  if (showViewAll) {
    // Normalize skill ID - handle both 'id' (from mock data) and 'skill_id' (from API)
    const _skillId = skill?.skill_id || skill?.id;
    const skillName = skill?.name || 'Skill';
    
    // Get category/subcategory for breadcrumb
    const categoryLabel = (typeof skill.category === 'object' ? skill.category?.category_name : skill.category) || '';
    const subcategoryLabel = skill.subcategory || '';
    
    // Filter employees based on search (local filtering)
    const filteredEmployees = searchValue.trim() 
      ? employeeResults.filter(emp => {
          const searchLower = searchValue.toLowerCase();
          return (
            emp.employee_name?.toLowerCase().includes(searchLower) ||
            emp.team_name?.toLowerCase().includes(searchLower) ||
            emp.sub_segment?.toLowerCase().includes(searchLower) ||
            emp.project_name?.toLowerCase().includes(searchLower)
          );
        })
      : employeeResults;
    
    // Compute KPI values from employeeResults (unfiltered) — guaranteed skill-scoped
    const totalEmployees = employeeResults.length;
    const certifiedCount = employeeResults.filter(e => e.certified).length;
    const avgProficiency = totalEmployees > 0 
      ? (employeeResults.reduce((sum, e) => sum + (e.proficiency_level || 0), 0) / totalEmployees).toFixed(1)
      : '—';
    const uniqueTeams = new Set(employeeResults.map(e => e.team_name).filter(Boolean)).size;
    const certCoverage = totalEmployees > 0 ? Math.round((certifiedCount / totalEmployees) * 100) : 0;
    
    // Helper context strings
    const avgProfContext = avgProficiency !== '—' && parseFloat(avgProficiency) < 3.0 ? 'warn' : 'ok';
    const _certContext = certifiedCount === 0 ? 'alert' : 'ok';
    const teamsContext = uniqueTeams === totalEmployees ? 'All unique' : `${uniqueTeams} teams`;
    const certCoverageContext = certCoverage === 0 ? 'alert' : certCoverage < 50 ? 'warn' : 'ok';
    
    // Helper to get proficiency level CSS class
    const getProficiencyDotClass = (level) => {
      const levelMap = {
        1: 'dp-level-dot--novice',
        2: 'dp-level-dot--beginner',
        3: 'dp-level-dot--competent',
        4: 'dp-level-dot--proficient',
        5: 'dp-level-dot--expert'
      };
      return levelMap[level] || 'dp-level-dot--novice';
    };
    
    return (
      <div className="co-card capability-overview co-details-panel">
        {/* Top Bar: Back + Breadcrumb + Export */}
        <div className="dp-top-bar">
          <button className="dp-back-btn" onClick={handleBackClick}>
            <ArrowLeft size={14} /> Back
          </button>
          
          {(categoryLabel || subcategoryLabel) && (
            <div className="dp-breadcrumb">
              {categoryLabel && <span>{categoryLabel}</span>}
              {categoryLabel && subcategoryLabel && <span className="sep">›</span>}
              {subcategoryLabel && <span>{subcategoryLabel}</span>}
              {(categoryLabel || subcategoryLabel) && <span className="sep">›</span>}
              <span className="current">{skillName}</span>
            </div>
          )}
          
          <button className="dp-export-btn" onClick={handleExportAll}>
            ↓ Export list
          </button>
        </div>

        {/* Skill Header */}
        <div className="dp-skill-header">
          <div className="dp-skill-title-row">
            <span className="dp-skill-label">Employees with</span>
            <span className="dp-skill-badge">{skillName}</span>
            <span className="dp-result-count">
              <strong>{totalEmployees}</strong> {totalEmployees === 1 ? 'employee' : 'employees'}
            </span>
          </div>
          
          {/* KPI Strip */}
          <div className="dp-kpi-strip">
            <div className="dp-kpi-cell">
              <div className="dp-kpi-label">Avg Proficiency</div>
              <div className="dp-kpi-value">{avgProficiency}</div>
              <div className={`dp-kpi-context ${avgProfContext}`}>
                {avgProficiency !== '—' && parseFloat(avgProficiency) < 3.0 ? 'Below 3.0 target' : 'On target'}
              </div>
            </div>
            
            <div className="dp-kpi-cell">
              <div className="dp-kpi-label">Teams covered</div>
              <div className="dp-kpi-value">{uniqueTeams}</div>
              <div className="dp-kpi-context ok">{teamsContext}</div>
            </div>
            <div className="dp-kpi-cell">
              <div className="dp-kpi-label">Cert coverage</div>
              <div className="dp-kpi-value">{certCoverage}%</div>
              <div className={`dp-kpi-context ${certCoverageContext}`}>
                {certifiedCount} of {totalEmployees} employees
              </div>
            </div>
          </div>
        </div>

        {/* Search Row */}
        <div className="dp-search-row">
          <input
            className="dp-search-input"
            type="text"
            placeholder="Search employee, role, team, sub-segment…"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </div>

        {/* Table Area */}
        {isLoading ? (
          <div className="dp-loading">
            <div className="dp-spinner"></div>
            <p className="dp-loading-text">Loading employees...</p>
          </div>
        ) : error ? (
          <div className="dp-error">
            <p className="dp-error-title">Failed to load employees</p>
            <p className="dp-error-text">{error}</p>
          </div>
        ) : filteredEmployees.length === 0 ? (
          <div className="dp-empty">
            <Users className="dp-empty-icon" />
            <p className="dp-empty-text">No employees found with this skill</p>
          </div>
        ) : (
          <div className="dp-table-area">
            <table className="dp-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Level</th>
                  <th>Sub-Segment</th>
                  <th>Project</th>
                  <th>Team</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map((emp, index) => (
                  <tr key={emp.employee_id} onClick={() => handleViewProfile(index)}>
                    <td>
                      <div className="dp-emp-name">{emp.employee_name}</div>
                      <div className="dp-emp-meta">
                        Updated {emp.skill_last_updated_days !== null ? `${emp.skill_last_updated_days} days ago` : '—'}
                      </div>
                    </td>
                    <td>
                      <div className="dp-level-cell">
                        <span className={`dp-level-dot ${getProficiencyDotClass(emp.proficiency_level)}`}></span>
                        {emp.proficiency_label}
                      </div>
                    </td>
                    <td>{emp.sub_segment || '—'}</td>
                    <td>{emp.project_name || '—'}</td>
                    <td>{emp.team_name || '—'}</td>
                    <td>
                      <button
                        className="dp-view-btn"
                        onClick={(e) => { e.stopPropagation(); handleViewProfile(index); }}
                      >
                        View Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Employee Profile Drawer */}
        <EmployeeProfileDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          employeeId={filteredEmployees[selectedEmployeeIndex]?.employee_id}
          employees={filteredEmployees.map(emp => ({ id: emp.employee_id, name: emp.employee_name }))}
          currentIndex={selectedEmployeeIndex}
          onNavigate={handleDrawerNavigate}
        />
      </div>
    );
  }
  // Show summary view (default - View B)
  const categoryName = (typeof skill.category === 'object' ? skill.category?.category_name : skill.category) || 'General';
  const skillEmployeeCount = snapshotData?.employee_count ?? summaryData?.employee_count ?? 0;
  
  return (
    <div className="co-card capability-overview co-details-panel">
      {/* Skill Detail Header */}
      <SkillDetailHeader
        categoryName={categoryName}
        subCategoryName={skill.subcategory}
        skillName={skill.name}
        employeeCount={skillEmployeeCount}
        onViewEmployees={handleViewAllClick}
        isDisabled={isLoading || isSnapshotLoading}
      />

      {/* Body Grid: Left (Snapshot + Proficiency) | Right (Context) */}
      <div className="co-body-grid">
        {/* Left Column */}
        <div className="co-body-left">
          {/* Capability Snapshot - 3 KPI Cards */}
          <SkillCapabilitySnapshot
            employeeCount={snapshotData?.employee_count ?? 0}
            certifiedCount={snapshotData?.certified_count ?? 0}
            teamCount={snapshotData?.team_count ?? 0}
            isLoading={isSnapshotLoading}
          />

          {/* Proficiency Breakdown */}
          <SkillProficiencyBreakdown
            counts={proficiencyData?.counts ?? null}
            avg={proficiencyData?.avg ?? null}
            median={proficiencyData?.median ?? null}
            total={proficiencyData?.total ?? 0}
            isLoading={isProficiencyLoading}
          />

         
        </div>

        {/* Right Column */}
        <div className="co-body-right">
          <SkillContextCard
            categoryName={categoryName}
            subCategoryName={skill.subcategory}
            leadingSubSegmentName={leadingSubSegmentData?.leading_sub_segment_name ?? '—'}
            isLoading={isSnapshotLoading || isLeadingSubSegmentLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default SkillDetailsPanel;
