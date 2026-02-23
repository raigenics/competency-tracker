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
  categoryCoverageError = null
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
  };  if (!skill) {
    return (
      <div className="co-card capability-overview co-details-panel">
        {/* Panel Header */}
        <div className="co-panel-header">
          <div className="co-panel-header-title">
            <h2>Details</h2>
            <span className="co-panel-breadcrumb">Summary → Skill insight</span>
          </div>
          <p className="co-panel-subtitle">Select a skill to view employee coverage, proficiency, and certifications.</p>
        </div>

        {/* Default Detail Content */}
        <div className="co-detail">
          <h3>Sub-Segments Capability Summary</h3>
          <p>This view shows mapped capabilities for the selected sub-segments. Use the tree and search to explore active skills quickly.</p>

          <div className="co-summary-grid">
            {/* Most populated category card */}
            <div className="co-summary-card">
              <div className="co-summary-card-label">Most populated category</div>
              <div className="co-summary-card-value">
                {categoryCoverageLoading ? (
                  'Loading...'
                ) : categoryCoverageError ? (
                  '—'
                ) : categoryCoverage?.most_populated_category ? (
                  categoryCoverage.most_populated_category.category_name
                ) : (
                  '—'
                )}
              </div>
              <div className="co-summary-card-hint">
                {categoryCoverageLoading || categoryCoverageError || !categoryCoverage?.most_populated_category
                  ? (categoryCoverageError ? 'No data available' : 'Highest employee concentration')
                  : 'Highest employee concentration'
                }
              </div>
            </div>

            {/* Least populated category card */}
            <div className="co-summary-card">
              <div className="co-summary-card-label">Least populated category</div>
              <div className="co-summary-card-value">
                {categoryCoverageLoading ? (
                  'Loading...'
                ) : categoryCoverageError ? (
                  '—'
                ) : categoryCoverage?.least_populated_category ? (
                  categoryCoverage.least_populated_category.category_name
                ) : (
                  '—'
                )}
              </div>
              <div className="co-summary-card-hint">
                {categoryCoverageLoading || categoryCoverageError || !categoryCoverage?.least_populated_category
                  ? (categoryCoverageError ? 'No data available' : 'Smaller bench compared to others')
                  : 'Smaller bench compared to others'
                }
              </div>
            </div>
          </div>

          {/* Hint list */}
          <ul className="co-hint-list">
            <li className="co-hint-item">
              <span className="co-hint-bullet"></span>
              <span className="co-hint-text">
                Use search to jump to technologies instantly
                <span className="co-hint-subtext">Auto-expands relevant categories and highlights matches</span>
              </span>
            </li>
            <li className="co-hint-item">
              <span className="co-hint-bullet"></span>
              <span className="co-hint-text">
                Expand categories to compare skill density by area
                <span className="co-hint-subtext">Counts show employees mapped per skill</span>
              </span>
            </li>
          </ul>
        </div>
      </div>
    );
  }

  // Show "View All" results view (View C: Employee List)
  if (showViewAll) {
    // Normalize skill ID - handle both 'id' (from mock data) and 'skill_id' (from API)
    const skillId = skill?.skill_id || skill?.id;
    
    // Truncate skill name to max 10 characters for column header
    const skillName = skill?.name || 'Skill';
    const truncatedSkillName = skillName.length > 10 ? `${skillName.slice(0, 10)}...` : skillName;
    
    // Filter employees based on search (local filtering)
    const filteredEmployees = searchValue.trim() 
      ? employeeResults.filter(emp => {
          const searchLower = searchValue.toLowerCase();
          return (
            emp.employee_name?.toLowerCase().includes(searchLower) ||
            emp.team_name?.toLowerCase().includes(searchLower) ||
            emp.sub_segment?.toLowerCase().includes(searchLower)
          );
        })
      : employeeResults;
    
    // Helper to get proficiency level CSS class
    const getProficiencyDotClass = (level) => {
      const levelMap = {
        1: 'co-level-dot--novice',
        2: 'co-level-dot--beginner',
        3: 'co-level-dot--competent',
        4: 'co-level-dot--proficient',
        5: 'co-level-dot--expert'
      };
      return levelMap[level] || 'co-level-dot--novice';
    };
    
    const handleClearSearch = () => {
      setSearchValue('');
    };
    
    return (
      <div className="co-card capability-overview">
        {/* View Employees Header Component */}
        <ViewEmployeesHeader
          skillId={skillId}
          skillName={skill.name}
          onBack={handleBackClick}
          onExport={handleExportAll}
          employeeResults={filteredEmployees}
          onSearchChange={setSearchValue}
          searchValue={searchValue}
          onClear={handleClearSearch}
        />

        {/* Results Table */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <div style={{ 
              width: '32px', 
              height: '32px', 
              border: '4px solid #2563eb', 
              borderTopColor: 'transparent', 
              borderRadius: '50%', 
              margin: '0 auto 16px',
              animation: 'spin 1s linear infinite'
            }}></div>
            <p style={{ color: '#64748b' }}>Loading employees...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <p style={{ color: '#dc2626', marginBottom: '8px' }}>Failed to load employees</p>
            <p style={{ fontSize: '14px', color: '#64748b' }}>{error}</p>
          </div>
        ) : filteredEmployees.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <Users style={{ width: '48px', height: '48px', margin: '0 auto 16px', color: '#9ca3af' }} />
            <p style={{ color: '#64748b' }}>No employees found with this skill</p>
          </div>
        ) : (
          <table className="co-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th className="co-skill-header">
                  <strong title={skillName}>{truncatedSkillName}</strong> Level
                </th>
                <th>Sub-Segment</th>
                <th>Team</th>
                <th>Certification</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredEmployees.map((emp, index) => (
                <tr key={emp.employee_id}>
                  <td>
                    <div className="co-empname">{emp.employee_name}</div>
                    <div className="co-empsub">
                      Skill updated: {emp.skill_last_updated_days !== null ? `${emp.skill_last_updated_days} days ago` : '—'}
                    </div>
                  </td>
                  <td>
                    <div className="co-level">
                      <span className={`co-level-dot ${getProficiencyDotClass(emp.proficiency_level)}`}></span>
                      <span>{emp.proficiency_label}</span>
                    </div>
                  </td>
                  <td>{emp.sub_segment || '—'}</td>
                  <td>{emp.team_name || '—'}</td>
                  <td>
                    <span className={`co-cert ${emp.certified ? 'co-cert--yes' : 'co-cert--no'}`}>
                      {emp.certified ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleViewProfile(index)}
                      className="co-link"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                    >
                      View Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
  const employeeCount = snapshotData?.employee_count ?? summaryData?.employee_count ?? 0;
  
  return (
    <div className="co-card capability-overview">
      {/* Skill Detail Header */}
      <SkillDetailHeader
        categoryName={categoryName}
        subCategoryName={skill.subcategory}
        skillName={skill.name}
        employeeCount={employeeCount}
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
