import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Loader2 } from 'lucide-react';
import SkillDistributionTable from './components/SkillDistributionTable.jsx';
import SkillUpdateActivity from './components/SkillUpdateActivity.jsx';
import RoleDistribution from './components/RoleDistribution';
import DataFreshnessKpi from './components/DataFreshnessKpi.jsx';
import PageHeader from '../../components/PageHeader';
import { dashboardApi } from '../../services/api/dashboardApi.js';
import { dropdownApi } from '../../services/api/dropdownApi.js';
import useDashboardStore from './dashboardStore.js';
import { DEFAULT_DASHBOARD_CONTEXT } from '../../config/featureFlags.js';
import './Dashboard.css';

// ─────────────────────────────────────────────────────────────────────────────
// LOCAL SKELETON COMPONENTS
// Minimal skeleton placeholders for initial load - keeps shell visible.
// ─────────────────────────────────────────────────────────────────────────────
const skeletonStyle = {
  background: 'linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)',
  backgroundSize: '200% 100%',
  animation: 'shimmer 1.5s infinite',
  borderRadius: '6px',
};

// Inject shimmer keyframes once
if (typeof document !== 'undefined' && !document.getElementById('dashboard-skeleton-keyframes')) {
  const style = document.createElement('style');
  style.id = 'dashboard-skeleton-keyframes';
  style.textContent = `@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }`;
  document.head.appendChild(style);
}

const SkeletonBox = ({ width = '100%', height = '20px', style: extraStyle = {} }) => (
  <div style={{ ...skeletonStyle, width, height, ...extraStyle }} />
);

const KpiSkeleton = () => (
  <div className="db-kpi" style={{ minHeight: 120 }}>
    <div className="meta" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
      <SkeletonBox width="120px" height="14px" />
      <SkeletonBox width="60px" height="14px" />
    </div>
    <SkeletonBox width="80px" height="36px" style={{ marginBottom: 8 }} />
    <SkeletonBox width="200px" height="12px" />
  </div>
);

const TableSkeleton = ({ rows = 5 }) => (
  <section className="db-card" style={{ gridColumn: '1 / span 2' }}>
    <div className="db-card-h">
      <SkeletonBox width="180px" height="18px" />
    </div>
    <div className="db-card-b" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonBox key={i} width="100%" height="16px" />
      ))}
    </div>
  </section>
);

const ChartSkeleton = ({ height = 200 }) => (
  <section className="db-card">
    <div className="db-card-h">
      <SkeletonBox width="140px" height="18px" />
    </div>
    <div className="db-card-b">
      <SkeletonBox width="100%" height={`${height}px`} />
    </div>
  </section>
);

const DashboardPage = () => {
  const isInitialized = useRef(false); // Track first successful load
  const loadingTimerRef = useRef(null); // Timer for flicker avoidance

  // Zustand cache for navigation persistence (similar to Skill Coverage)
  const isCacheValid = useDashboardStore(s => s.isCacheValid);
  const cachedPayload = useDashboardStore(s => s.cachedPayload);
  const setCachedPayload = useDashboardStore(s => s.setCachedPayload);
  
  const navigate = useNavigate();
  
  // Check cache validity once on mount (avoid calling function in useState)
  const initialCacheValid = useRef(isCacheValid());

  const [loading, setLoading] = useState(!initialCacheValid.current); // Skip loading if cache valid
  const [showLoadingUI, setShowLoadingUI] = useState(false); // Flicker avoidance: only show skeleton after 200ms
  const [isFetching, setIsFetching] = useState(false); // For filter-triggered data refresh (keeps UI visible)

  // Flicker avoidance: delay showing loading UI by 200ms to avoid flash on fast loads
  useEffect(() => {
    if (loading) {
      loadingTimerRef.current = setTimeout(() => {
        setShowLoadingUI(true);
      }, 200);
    } else {
      // Clear timer and hide loading UI immediately when done
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
      setShowLoadingUI(false);
    }
    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
    };
  }, [loading]);
  const [dashboardFilters, setDashboardFilters] = useState({
    segment: DEFAULT_DASHBOARD_CONTEXT.SEGMENT_ID,
    subSegment: '',
    project: '',
    team: ''
  });

  // Empty state: shown when DEFAULT segment has no sub-segments or is invalid
  // Prevents loading org-wide data when segment scoping is required
  const [isEmptyState, setIsEmptyState] = useState(false);
  
  // Dropdown data state
  const [dropdownData, setDropdownData] = useState({
    subSegments: [],
    projects: [],
    teams: []
  });
  
  // Dropdown loading states
  const [dropdownLoading, setDropdownLoading] = useState({
    subSegments: false,
    projects: false,
    teams: false
  });
  // Data state
  const [metrics, setMetrics] = useState({});
  const [skillDistribution, setSkillDistribution] = useState([]);
  const [updateActivity, setUpdateActivity] = useState({});
  const [activityDays, setActivityDays] = useState(90);
  const activityDaysRef = useRef(90); // mirrors activityDays for stable callback reference
  const [activityLoading, setActivityLoading] = useState(false);
  
  // Data Freshness state (fetched together with activity data)
  const [dataFreshness, setDataFreshness] = useState(null);
  const [freshnessLoading, setFreshnessLoading] = useState(false);

  // Load dashboard data function - wrapped in useCallback for proper deps
  const loadDashboardData = useCallback(async () => {
    try {
      const [metricsData, skillData] = await Promise.all([
        dashboardApi.getDashboardMetrics(dashboardFilters),
        dashboardApi.getSkillDistribution(dashboardFilters)
      ]);

      setMetrics(metricsData);
      setSkillDistribution(skillData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  }, [dashboardFilters]);

  // Load skill update activity - wrapped in useCallback for proper deps
  const loadSkillUpdateActivity = useCallback(
    async (days, skipFreshnessLoading = false) => {
      const daysToUse = days ?? activityDaysRef.current;  // use ref, not state
      setActivityLoading(true);
      if (!skipFreshnessLoading) setFreshnessLoading(true);
      try {
        // Fetch both activity and freshness data in parallel (same filter logic)
        const FRESHNESS_WINDOW_DAYS = 90; // fixed, never follows activity dropdown
        const [activityData, freshnessData] = await Promise.all([
          dashboardApi.getSkillUpdateActivity(dashboardFilters, daysToUse),
          dashboardApi.getDataFreshness(dashboardFilters, FRESHNESS_WINDOW_DAYS)
        ]);
        setUpdateActivity(activityData);
        setDataFreshness(freshnessData);
      } catch (error) {
        console.error('Failed to load skill update activity:', error);
        // On error, set freshness to null so UI shows "—"
        setDataFreshness(null);
      } finally {
        setActivityLoading(false);
        if (!skipFreshnessLoading) setFreshnessLoading(false);
      }
    },
    [dashboardFilters]
  );  // activityDays removed — ref keeps value stable

// Load sub-segments on component mount (runs only once)
  useEffect(() => {
    const initializeDashboard = async () => {
      // Check if we have valid cached data (TTL 60s) - skip fetch if so
      if (initialCacheValid.current && cachedPayload) {
        // Hydrate local state from cache
        setMetrics(cachedPayload.metrics || {});
        setSkillDistribution(cachedPayload.skillDistribution || []);
        setUpdateActivity(cachedPayload.updateActivity || {});
        setDataFreshness(cachedPayload.dataFreshness || null);
        setDropdownData(cachedPayload.dropdownData || { subSegments: [], projects: [], teams: [] });
        setActivityDays(cachedPayload.activityDays || 90);
        activityDaysRef.current = cachedPayload.activityDays || 90;
        isInitialized.current = true;
        setLoading(false);
        return; // Skip API calls
      }

      setLoading(true);
      try {
        // Load sub-segments for the default segment
        // If no sub-segments exist OR segment is invalid, show empty state and skip data load
        const segmentId = DEFAULT_DASHBOARD_CONTEXT.SEGMENT_ID;
        
        if (!segmentId) {
          // Invalid/missing segment ID - show empty state
          setIsEmptyState(true);
          setLoading(false);
          return;
        }
        
        // Fetch sub-segments for the default segment
        const subSegments = await dropdownApi.getSubSegmentsBySegment(segmentId);
        setDropdownData(prev => ({ ...prev, subSegments }));
        
        if (!subSegments || subSegments.length === 0) {
          // No sub-segments for this segment - show empty state
          // Do NOT load dashboard data to avoid returning org-wide data
          setIsEmptyState(true);
          isInitialized.current = true;
          setLoading(false);
          return;
        }
        
        // Segment has sub-segments - proceed with normal dashboard load
        setIsEmptyState(false);
        await loadDashboardData();
        await loadSkillUpdateActivity();
        isInitialized.current = true; // Mark as initialized after first successful load
      } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        // On error, show empty state to avoid showing stale/incorrect data
        setIsEmptyState(true);
      } finally {
        setLoading(false);
      }
    };

    initializeDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - only run once on mount

  // Save to cache when data changes (after successful load)
  useEffect(() => {
    // Only cache after initialization is complete and we have data
    if (!isInitialized.current || loading) return;
    
    // Build payload from current state
    const payload = {
      metrics,
      skillDistribution,
      updateActivity,
      dataFreshness,
      dropdownData,
      activityDays
    };
    
    setCachedPayload(payload);
  }, [metrics, skillDistribution, updateActivity, dataFreshness, dropdownData, activityDays, loading, setCachedPayload]);

  // Reload dashboard data when filters change (subsequent loads)
  useEffect(() => {
    // Skip on initial mount (handled above)
    if (!isInitialized.current) return;
    
    const refreshData = async () => {
      setIsFetching(true);
      try {
        await Promise.all([
          loadDashboardData(),
          loadSkillUpdateActivity()
        ]);
      } finally {
        setIsFetching(false);
      }
    };

    refreshData();
  }, [dashboardFilters, loadDashboardData, loadSkillUpdateActivity]);

  // Load projects for selected sub-segment
  const loadProjects = async (subSegmentId) => {
    if (!subSegmentId) {
      setDropdownData(prev => ({ ...prev, projects: [], teams: [] }));
      return;
    }

    setDropdownLoading(prev => ({ ...prev, projects: true }));
    try {
      const projects = await dropdownApi.getProjects(subSegmentId);
      setDropdownData(prev => ({ ...prev, projects, teams: [] }));
    } catch (error) {
      console.error('Failed to load projects:', error);
      setDropdownData(prev => ({ ...prev, projects: [], teams: [] }));
    } finally {
      setDropdownLoading(prev => ({ ...prev, projects: false }));
    }
  };

  // Load teams for selected project
  const loadTeams = async (projectId) => {
    if (!projectId) {
      setDropdownData(prev => ({ ...prev, teams: [] }));
      return;
    }

    setDropdownLoading(prev => ({ ...prev, teams: true }));
    try {
      const teams = await dropdownApi.getTeams(projectId);
      setDropdownData(prev => ({ ...prev, teams }));
    } catch (error) {
      console.error('Failed to load teams:', error);
      setDropdownData(prev => ({ ...prev, teams: [] }));
    } finally {
      setDropdownLoading(prev => ({ ...prev, teams: false }));
    }
  };

  // Handle time window change for activity section
  const handleActivityDaysChange = (days) => {
    setActivityDays(days);
    activityDaysRef.current = days;  // keep ref in sync
    loadSkillUpdateActivity(days, true); // skip freshness loading — window is fixed at 90 days
  };

  // Determine scope level and employee count
  const getScopeLevel = () => {
    if (dashboardFilters.team) return 'team';
    if (dashboardFilters.project) return 'project';
    if (dashboardFilters.subSegment) return 'subsegment';
    return 'organization';
  };

  // Get filtered scope display text
  const getFilteredScope = () => {
    if (dashboardFilters.team) {
      const team = dropdownData.teams.find(t => t.id === parseInt(dashboardFilters.team));
      return team ? `Team: ${team.name}` : 'Team: Unknown';
    }
    if (dashboardFilters.project) {
      const project = dropdownData.projects.find(p => p.id === parseInt(dashboardFilters.project));
      return project ? `Project: ${project.name}` : 'Project: Unknown';
    }
    if (dashboardFilters.subSegment) {
      const subSegment = dropdownData.subSegments.find(s => s.id === parseInt(dashboardFilters.subSegment));
      return subSegment ? `Sub-Segment: ${subSegment.name}` : 'Sub-Segment: Unknown';
    }
    return 'Organization-Wide';
  };

  const scopeLevel = getScopeLevel();
  const totalEmployees = metrics.total_employees || 0;

  // Determine how many top skills to show
  const topSkillsCount = scopeLevel === 'team' ? 5 : 10;

  const filteredScope = getFilteredScope();

  // Handle sub-segment filter change
  const handleSubSegmentChange = (subSegmentId) => {
    // Reset dependent filters
    setDashboardFilters({
      subSegment: subSegmentId,
      project: '',
      team: ''
    });
    
    // Load projects if sub-segment is selected
    if (subSegmentId) {
      loadProjects(subSegmentId);
    } else {
      // Clear projects and teams if "All Sub-Segments" selected
      setDropdownData(prev => ({ ...prev, projects: [], teams: [] }));
    }
  };

  // Handle project filter change
  const handleProjectChange = (projectId) => {
    // Reset dependent filters
    setDashboardFilters(prev => ({
      ...prev,
      project: projectId,
      team: ''
    }));
    
    // Load teams if project is selected
    if (projectId) {
      loadTeams(projectId);
    } else {
      // Clear teams if "All Projects" selected
      setDropdownData(prev => ({ ...prev, teams: [] }));
    }
  };

  // Handle team filter change
  const handleTeamChange = (teamId) => {
    setDashboardFilters(prev => ({
      ...prev,
      team: teamId
    }));
  };

  const clearFilters = () => {
    setDashboardFilters({ segment: DEFAULT_DASHBOARD_CONTEXT.SEGMENT_ID, subSegment: '', project: '', team: '' });
    setDropdownData(prev => ({ ...prev, projects: [], teams: [] }));
  };

  // Do not use page-level loading return; keep shell rendered for better UX.
  // Skeleton placeholders are shown inline instead of replacing entire content.

  // Determine if we should show skeletons (loading AND past the 200ms delay)
  const showSkeletons = loading && showLoadingUI;

  // Show empty state when:
  // - DEFAULT segment has no sub-segments / invalid segment (isEmptyState=true)
  // - OR segment is valid but has no employees in scope (totalEmployees===0)
  const showEmptyState = !loading && (isEmptyState || totalEmployees === 0);

  return (
    <div className="dashboard-page">
      {/* Main content area with padding */}
      <main 
        className={showEmptyState ? 'empty-state-main' : ''} 
        style={{ padding: '0 26px 40px' }}
      >
        <PageHeader
          title="Dashboard"
          subtitle="Competency overview and situational awareness — scoped by your org filters"
          // actions={
          //   <>
          //     <span className="db-pill">Last updated: just now</span>
          //     <button className="db-btn ghost">Export</button>
          //   </>
          // }
        />

        {/* EMPTY STATE - shown when no sub-segments exist for segment OR no employees in scope */}
        {showEmptyState && (
          <>
            {/* Muted scope banner */}
            <div className="scope-banner">
              <span className="scope-banner-label">Current scope</span>
              <span className="scope-pill">Organization-Wide</span>
              <span className="scope-banner-note">Filters available once employees are added</span>
            </div>

            {/* Empty content */}
            <div className="empty-content">
              <div className="empty-icon-bg">
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                  <rect x="5" y="20" width="6" height="10" rx="2" fill="#e8e5e0"/>
                  <rect x="15" y="13" width="6" height="17" rx="2" fill="#c4c1bb"/>
                  <rect x="25" y="7" width="6" height="23" rx="2" fill="#1a3a5c" opacity="0.35"/>
                  <circle cx="28" cy="5" r="2.5" fill="#2d5f8a" opacity="0.5"/>
                </svg>
              </div>

              <div className="empty-heading">Your dashboard is ready</div>
              <div className="empty-body">
                Add employees and their skills to start seeing proficiency coverage,
                team distribution, and skill trends across your organisation.
              </div>

              <div className="action-row">
                <button className="btn-primary" onClick={() => navigate('/system/import')}>
                  Go to Import Data
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"/>
                    <polyline points="12 5 19 12 12 19"/>
                  </svg>
                </button>
                <button className="btn-secondary" onClick={() => navigate('/employees')}>
                  Go to Employee Management
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"/>
                    <polyline points="12 5 19 12 12 19"/>
                  </svg>
                </button>
              </div>
              <div className="btn-nav-hint">Both pages are also accessible from the Governance section in the side navigation</div>

              {/* Setup progress checklist */}
              <div className="checklist">
                <div className="check-item done">
                  <div className="check-dot"></div>
                  Organisation structure configured
                </div>
                <div className="check-item done">
                  <div className="check-dot"></div>
                  Skill library ready
                </div>
                <div className="check-item">
                  <div className="check-dot"></div>
                  Employees added
                </div>
                <div className="check-item">
                  <div className="check-dot"></div>
                  Skills mapped
                </div>
              </div>

              {/* Prerequisite notice */}
              <div className="prereq-notice">
                <svg className="prereq-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <div className="prereq-body">
                  <div className="prereq-title">Before importing employees</div>
                  <div className="prereq-text">
                    Ensure your master data is set up first. Employee imports require your
                    organisation structure, skill library, and role catalog to already exist
                    in the system — otherwise assignments will fail.
                    Set these up from the <strong>Governance section in the side navigation</strong>.
                  </div>
                  <div className="prereq-links">
                    <button className="prereq-link" onClick={() => navigate('/governance/org-structure')}>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                      Organization Structure
                    </button>
                    <button className="prereq-link" onClick={() => navigate('/governance/skill-library')}>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                      Skill Library
                    </button>
                    <button className="prereq-link" onClick={() => navigate('/governance/role-catalog')}>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                      Role Catalog
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* HERO CTA (smaller, not dominating) */}
        {/* <section className="db-hero">
          <div className="db-hero-left">
            <div className="db-hero-badge">
              <Search size={18} style={{ color: 'var(--db-brand-700)' }} />
            </div>
            <div style={{ minWidth: 0 }}>
              <h3>Find Talent by Skills & Organization</h3>
              <p>Use advanced query builder for multi-dimensional search.</p>
            </div>
          </div>
          <button className="db-btn primary" onClick={handleAdvancedQueryClick}>
            Launch
          </button>
        </section> */}

        {/* MAIN GRID - hidden when empty state is shown */}
        {!showEmptyState && (
        <div className="db-grid">
          {/* LEFT COLUMN - Dashboard Context Filters */}
          <section className="db-card db-filters-card">
            <div className="db-card-h">
              <div className="left">
                <h4>Dashboard Context Filters</h4>
                <p>These filters control all analytics below</p>
              </div>
              <button className="db-btn ghost" onClick={clearFilters}>Reset</button>
            </div>
            <div className="db-card-b">
              <div className="db-filters">
                <div>
                  <label>Sub-Segment</label>
                  <select 
                    value={dashboardFilters.subSegment}
                    onChange={(e) => handleSubSegmentChange(e.target.value)}
                    disabled={loading || dropdownLoading.subSegments}
                  >
                    <option value="">All Sub-Segments</option>
                    {dropdownData.subSegments.map((subSegment) => (
                      <option key={subSegment.id} value={subSegment.id}>
                        {subSegment.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label>Project</label>
                  <select 
                    value={dashboardFilters.project}
                    onChange={(e) => handleProjectChange(e.target.value)}
                    disabled={loading || !dashboardFilters.subSegment || dropdownLoading.projects}
                  >
                    <option value="">All Projects</option>
                    {dropdownData.projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label>Team</label>
                  <select 
                    value={dashboardFilters.team}
                    onChange={(e) => handleTeamChange(e.target.value)}
                    disabled={loading || !dashboardFilters.project || dropdownLoading.teams}
                  >
                    <option value="">All Teams</option>
                    {dropdownData.teams.map((team) => (
                      <option key={team.id} value={team.id}>
                        {team.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="db-apply-row">
                  {/* Apply button - auto-applies on change; button disabled during fetch */}
                  
                  {isFetching && (
                    <div className="db-inline-loading">
                      <Loader2 size={14} className="db-spinner" />
                      <span>Updating results...</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="db-scope">
                <div className="mini">Current view</div>
                <div className="tag">{filteredScope} • {totalEmployees} Employees</div>
              </div>
            </div>
          </section>

          {/* RIGHT COLUMN - KPIs */}
          <section className="db-kpis">
            {showSkeletons ? (
              <>
                <KpiSkeleton />
                <KpiSkeleton />
              </>
            ) : (
              <>
                {/* KPI 1: Employees in Scope - bound to existing data */}
                <div className="db-kpi">
                  <div className="meta">
                    <span>Employees in Scope</span>
                    <span className="db-badge">Scope: {scopeLevel.charAt(0).toUpperCase() + scopeLevel.slice(1)}</span>
                  </div>
                  <div className="value">{totalEmployees}</div>
                  <p className="sub">Includes active employees matching the applied filters</p>
                </div>

                {/* KPI 2: Data Freshness - Dynamic from API */}
                <DataFreshnessKpi 
                  value={dataFreshness?.freshness_percent ?? null}
                  windowDays={dataFreshness?.window_days ?? 90}
                  loading={freshnessLoading}
                />
              </>
            )}
          </section>

          {/* TOP SKILLS TABLE */}
          {showSkeletons ? (
            <TableSkeleton rows={5} />
          ) : (
            <SkillDistributionTable 
              skillDistribution={skillDistribution}
              topSkillsCount={topSkillsCount}
              scopeLevel={scopeLevel}
            />
          )}

          {/* SKILL UPDATE ACTIVITY */}
          {showSkeletons ? (
            <ChartSkeleton height={180} />
          ) : (
            <SkillUpdateActivity 
              activityData={updateActivity}
              loading={activityLoading}
              onDaysChange={handleActivityDaysChange}
              employeesInScope={totalEmployees}
            />
          )}

          {/* ROLE DISTRIBUTION - spans both columns */}
          <div style={{ gridColumn: '1 / span 2' }}>
            {showSkeletons ? (
              <ChartSkeleton height={220} />
            ) : (
              <RoleDistribution
                dashboardFilters={dashboardFilters}
                dropdownData={dropdownData}
              />
            )}
          </div>
        </div>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;