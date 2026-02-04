import { useState, useEffect } from 'react';
import { Search, ChevronRight, BarChart3, Filter } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import EmployeesInScopeCard from './components/EmployeesInScopeCard.jsx';
import SkillDistributionTable from './components/SkillDistributionTable.jsx';
import SkillUpdateActivity from './components/SkillUpdateActivity.jsx';
import OrgCoverageTable from './components/OrgCoverageTable.jsx';
import LoadingState from '../../components/LoadingState.jsx';
import PageHeader from '../../components/PageHeader.jsx';
import { dashboardApi } from '../../services/api/dashboardApi.js';
import { dropdownApi } from '../../services/api/dropdownApi.js';

const DashboardPage = () => {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true); // Initial page load only
  const [dataLoading, setDataLoading] = useState(false); // For filter-triggered data refresh
  const [dashboardFilters, setDashboardFilters] = useState({
    subSegment: '',
    project: '',
    team: ''
  });
  
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
  const [orgCoverage, setOrgCoverage] = useState([]);
  const [updateActivity, setUpdateActivity] = useState({});
  const [activityDays, setActivityDays] = useState(90);
  const [activityLoading, setActivityLoading] = useState(false);// Load sub-segments on component mount
  useEffect(() => {
    const initializeDashboard = async () => {
      setLoading(true);
      try {
        await Promise.all([
          loadSubSegments(),
          loadOrganizationCoverage()
        ]);
        // Load initial dashboard data
        await loadDashboardData();
        await loadSkillUpdateActivity();
      } catch (error) {
        console.error('Failed to initialize dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeDashboard();
  }, []);
  // Reload dashboard data when filters change (excluding org coverage)
  useEffect(() => {
    // Skip on initial mount (handled above)
    if (loading) return;
    
    loadDashboardData();
    loadSkillUpdateActivity();
  }, [dashboardFilters]);
  // Load dashboard data function
  const loadDashboardData = async () => {
    setDataLoading(true);
    try {
      const [metricsData, skillData] = await Promise.all([
        dashboardApi.getDashboardMetrics(dashboardFilters),
        dashboardApi.getSkillDistribution(dashboardFilters)
      ]);

      setMetrics(metricsData);
      setSkillDistribution(skillData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setDataLoading(false);
    }
  };

  // Load sub-segments dropdown data
  const loadSubSegments = async () => {
    setDropdownLoading(prev => ({ ...prev, subSegments: true }));
    try {
      const subSegments = await dropdownApi.getSubSegments();
      setDropdownData(prev => ({ ...prev, subSegments }));
    } catch (error) {
      console.error('Failed to load sub-segments:', error);
    } finally {
      setDropdownLoading(prev => ({ ...prev, subSegments: false }));
    }
  };

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

  // Load organization coverage data (once on mount, ignores filters)
  const loadOrganizationCoverage = async () => {
    try {
      const coverageData = await dashboardApi.getOrgCoverage();
      setOrgCoverage(coverageData);
    } catch (error) {
      console.error('Failed to load organization coverage:', error);
    }
  };

  // Load skill update activity data
  const loadSkillUpdateActivity = async (days = activityDays) => {
    setActivityLoading(true);
    try {
      const activityData = await dashboardApi.getSkillUpdateActivity(dashboardFilters, days);
      setUpdateActivity(activityData);
    } catch (error) {
      console.error('Failed to load skill update activity:', error);
    } finally {
      setActivityLoading(false);
    }
  };

  // Handle time window change for activity section
  const handleActivityDaysChange = (days) => {
    setActivityDays(days);
    loadSkillUpdateActivity(days);
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

  const handleSegmentSelect = (segment) => {
    setDashboardFilters({ ...dashboardFilters, subSegment: segment, project: '', team: '' });
  };

  const handleAdvancedQueryClick = () => {
    navigate('/query');
  };
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
    setDashboardFilters({ subSegment: '', project: '', team: '' });
    setDropdownData(prev => ({ ...prev, projects: [], teams: [] }));
  };
  if (loading) {
    return <LoadingState message="Loading dashboard..." />;
  }

  return (
    <div className="min-h-screen bg-[#f8fafc]">
      <PageHeader 
        title="Dashboard"
        subtitle="Competency overview and situational awareness"
      />
      
      <div className="p-8">
        <div className="max-w-screen-2xl mx-auto">
          {/* Primary Action - Launch Advanced Query */}
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg p-6 mb-8 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                  <Search className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold">Find Talent by Skills & Organization</h2>
                <p className="text-blue-100 text-sm mt-1">Launch advanced query builder for complex multi-dimensional search</p>
              </div>
            </div>
            <button
              onClick={handleAdvancedQueryClick}
              className="px-6 py-3 bg-white text-blue-700 rounded-lg hover:bg-blue-50 font-semibold shadow-md transition-all flex items-center space-x-2"
            >
              <span>Advanced Query</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* SEPARATOR - Dashboard Analytics Begin Here */}
        <div className="border-t-2 border-slate-300 mb-8 pt-8">
          <div className="flex items-center space-x-2 mb-6">
            <BarChart3 className="w-5 h-5 text-slate-600" />
            <h2 className="text-xl font-semibold text-slate-900">Dashboard Analytics</h2>
            <span className="text-xs text-slate-500 ml-2">(Use filters below to scope your view)</span>
          </div>

          {/* Dashboard Context Filters */}
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Filter className="w-5 h-5 text-slate-600" />
                <h3 className="font-semibold text-slate-900">Dashboard Context Filters</h3>
                <span className="text-xs text-slate-500 ml-2">(Controls all analytics below)</span>
              </div>
              {(dashboardFilters.subSegment || dashboardFilters.project || dashboardFilters.team) && (
                <button
                  onClick={clearFilters}
                  className="text-xs text-red-600 hover:text-red-700 font-medium"
                >
                  Clear All Filters
                </button>
              )}
            </div>
            
            <div className="grid grid-cols-3 gap-4">              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-2">Sub-Segment</label>
                <select 
                  value={dashboardFilters.subSegment}
                  onChange={(e) => handleSubSegmentChange(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={dropdownLoading.subSegments}
                >
                  <option value="">All Sub-Segments</option>
                  {dropdownData.subSegments.map((subSegment) => (
                    <option key={subSegment.id} value={subSegment.id}>
                      {subSegment.name}
                    </option>
                  ))}
                </select>
                {dropdownLoading.subSegments && (
                  <div className="text-xs text-slate-500 mt-1">Loading...</div>
                )}
              </div>              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-2">Project</label>
                <select 
                  value={dashboardFilters.project}
                  onChange={(e) => handleProjectChange(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={!dashboardFilters.subSegment || dropdownLoading.projects}
                >
                  <option value="">All Projects</option>
                  {dropdownData.projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
                {dropdownLoading.projects && (
                  <div className="text-xs text-slate-500 mt-1">Loading...</div>
                )}
              </div>              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-2">Team</label>
                <select 
                  value={dashboardFilters.team}
                  onChange={(e) => handleTeamChange(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={!dashboardFilters.project || dropdownLoading.teams}
                >
                  <option value="">All Teams</option>
                  {dropdownData.teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
                {dropdownLoading.teams && (
                  <div className="text-xs text-slate-500 mt-1">Loading...</div>
                )}
              </div>
            </div>

            {/* Active Context Indicator */}
            <div className="mt-4 pt-4 border-t border-slate-200">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-medium text-slate-600">Current View:</span>
                <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                  {filteredScope} • {totalEmployees} Employees
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Employees in Scope Metric */}
        <div className="grid grid-cols-1 gap-4 mb-6">
          <EmployeesInScopeCard 
            totalEmployees={totalEmployees}
            filteredScope={filteredScope}
            scopeLevel={scopeLevel}
          />
        </div>

        {/* Core Section: Skill Distribution with Proficiency */}
        <SkillDistributionTable 
          skillDistribution={skillDistribution}
          topSkillsCount={topSkillsCount}          scopeLevel={scopeLevel}
        />

        {/* Skill Update Activity */}
        <SkillUpdateActivity 
          activityData={updateActivity}
          loading={activityLoading}
          onDaysChange={handleActivityDaysChange}
        />

        {/* Organizational Skill Coverage Table */}
        <OrgCoverageTable
          coverageData={orgCoverage}
          onSegmentSelect={handleSegmentSelect}
        />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
