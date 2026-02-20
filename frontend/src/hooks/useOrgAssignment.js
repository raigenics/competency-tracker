/**
 * useOrgAssignment Hook
 * 
 * Handles cascading dropdown logic for organizational assignment in Add Employee drawer.
 * Implements role-based locking and preselection based on user's RBAC context.
 * 
 * Cascade: Segment -> Sub-segment -> Project -> Team
 * 
 * Role-based behavior:
 * - SUPER_ADMIN: All enabled, cascade normally
 * - SEGMENT_HEAD: Segment locked, rest cascade
 * - SUBSEGMENT_HEAD: Segment + Sub-segment locked
 * - PROJECT_MANAGER: Segment + Sub-segment + Project locked
 * - TEAM_LEAD: All locked (no selection possible)
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { dropdownApi } from '../services/api/dropdownApi.js';
import { getRbacContext, RBAC_ROLES } from '../config/featureFlags.js';

// ========== DIAGNOSTIC LOGGING - START ==========
const DDL_T0 = performance.now();
const ddlLog = (dropdown, msg, extra = {}) => {
  const t = (performance.now() - DDL_T0).toFixed(1);
  console.log(`[DDL][${dropdown}] t=${t}ms ${msg}`, extra);
};
let segmentApiCallCount = 0;
let subSegmentApiCallCount = 0;
let projectApiCallCount = 0;
let teamApiCallCount = 0;
let effectRunCounts = { segments: 0, subSegments: 0, projects: 0, teams: 0 };
// ========== DIAGNOSTIC LOGGING - END ==========

/**
 * @param {Object} config - Optional configuration object
 * @param {boolean} config.isEditMode - If true, skips initial API calls (bootstrap will provide data)
 * @returns {Object} Organizational assignment state and handlers
 */
export function useOrgAssignment({ isEditMode = false } = {}) {
  // Log on every render to track isEditMode
  console.log('[useOrgAssignment] render', { isEditMode });
  
  // Get current user's role and scope
  const { role, scope } = getRbacContext();
  
  // Flag to suppress cascade effects during edit mode loading
  const isLoadingForEditRef = useRef(false);
  
  // Bootstrap guard refs - track which parent ID the current options belong to
  // Used to prevent redundant API calls when bootstrap already loaded options
  // This survives React StrictMode's double-effect execution
  const subSegmentsForSegmentIdRef = useRef(null);
  const projectsForSubSegmentIdRef = useRef(null);
  const teamsForProjectIdRef = useRef(null);
  
  // Selected values
  const [selectedSegmentId, setSelectedSegmentId] = useState(null);
  const [selectedSubSegmentId, setSelectedSubSegmentId] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [selectedTeamId, setSelectedTeamId] = useState(null);
  
  // Dropdown options
  const [segments, setSegments] = useState([]);
  const [subSegments, setSubSegments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [teams, setTeams] = useState([]);
  
  // Loading states
  const [loading, setLoading] = useState({
    segments: false,
    subSegments: false,
    projects: false,
    teams: false
  });
  
  // Error state
  const [error, setError] = useState(null);
  
  // Determine which fields are locked based on role
  const isLocked = useMemo(() => ({
    segment: role === RBAC_ROLES.SEGMENT_HEAD || 
             role === RBAC_ROLES.SUBSEGMENT_HEAD || 
             role === RBAC_ROLES.PROJECT_MANAGER || 
             role === RBAC_ROLES.TEAM_LEAD,
    subSegment: role === RBAC_ROLES.SUBSEGMENT_HEAD || 
                role === RBAC_ROLES.PROJECT_MANAGER || 
                role === RBAC_ROLES.TEAM_LEAD,
    project: role === RBAC_ROLES.PROJECT_MANAGER || 
             role === RBAC_ROLES.TEAM_LEAD,
    team: role === RBAC_ROLES.TEAM_LEAD
  }), [role]);
  
  // Determine which fields are disabled (locked or no parent selection)
  const isDisabled = {
    segment: isLocked.segment,
    subSegment: isLocked.subSegment || (!selectedSegmentId && !isLocked.subSegment),
    project: isLocked.project || (!selectedSubSegmentId && !isLocked.project),
    team: isLocked.team || (!selectedProjectId && !isLocked.team)
  };

  // Load segments on mount (skip if in edit mode - bootstrap provides segments)
  useEffect(() => {
    effectRunCounts.segments++;
    ddlLog('SEGMENT', 'useEffect-fired', { runCount: effectRunCounts.segments, isEditMode, isLoadingForEdit: isLoadingForEditRef.current });
    
    // Skip if in edit mode (bootstrap will provide segments)
    if (isEditMode) {
      ddlLog('SEGMENT', 'skipped - isEditMode=true (bootstrap will provide)');
      // Also set suppression flag so cascade effects are blocked
      isLoadingForEditRef.current = true;
      return;
    }
    
    loadSegments();
  }, [isEditMode]);

  /**
   * Apply role-based preselection from user's scope
   * IMPORTANT: Must be defined BEFORE the useEffect that references it to avoid TDZ error
   */
  const applyRoleBasedPreselection = useCallback(() => {
    if (!scope) return;
    
    // For roles with locked fields, preselect from scope
    if (scope.segment_id && isLocked.segment) {
      setSelectedSegmentId(scope.segment_id);
    }
    
    if (scope.sub_segment_id && isLocked.subSegment) {
      setSelectedSubSegmentId(scope.sub_segment_id);
    }
    
    if (scope.project_id && isLocked.project) {
      setSelectedProjectId(scope.project_id);
    }
    
    if (scope.team_id && isLocked.team) {
      setSelectedTeamId(scope.team_id);
    }
  }, [scope, isLocked]);

  // Apply preselection based on role scope
  useEffect(() => {
    ddlLog('PRESELECT', 'useEffect-fired', { role, scope, segmentsCount: segments.length, isEditMode, isLoadingForEdit: isLoadingForEditRef.current });
    
    // Skip role-based preselection in edit mode (edit values take priority)
    if (isEditMode || isLoadingForEditRef.current) {
      ddlLog('PRESELECT', 'skipped - edit mode (isEditMode=' + isEditMode + ')');
      return;
    }
    
    applyRoleBasedPreselection();
  }, [role, scope, segments, isEditMode, applyRoleBasedPreselection]);

  // Cascade: Load sub-segments when segment changes
  useEffect(() => {
    effectRunCounts.subSegments++;
    ddlLog('SUBSEGMENT', 'useEffect-fired', { 
      runCount: effectRunCounts.subSegments, 
      selectedSegmentId,
      isLoadingForEdit: isLoadingForEditRef.current,
      guardRef: subSegmentsForSegmentIdRef.current,
      optionsCount: subSegments.length
    });
    
    // Skip cascade if loading for edit mode (loadForEditMode handles this)
    if (isLoadingForEditRef.current) {
      ddlLog('SUBSEGMENT', 'skipped - edit mode loading in progress');
      return;
    }
    
    // Skip if bootstrap already loaded options for this segment (survives StrictMode)
    if (selectedSegmentId && 
        subSegmentsForSegmentIdRef.current === selectedSegmentId && 
        subSegments.length > 0) {
      ddlLog('SUBSEGMENT', 'skipped - bootstrap options already loaded', {
        forSegmentId: subSegmentsForSegmentIdRef.current
      });
      return;
    }
    
    if (selectedSegmentId) {
      loadSubSegments(selectedSegmentId);
    } else {
      ddlLog('SUBSEGMENT', 'clearing (no segment selected)');
      setSubSegments([]);
      setSelectedSubSegmentId(null);
      subSegmentsForSegmentIdRef.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Cascade effect intentionally triggers only on selectedSegmentId change
  }, [selectedSegmentId]);

  // Cascade: Load projects when sub-segment changes
  useEffect(() => {
    effectRunCounts.projects++;
    ddlLog('PROJECT', 'useEffect-fired', { 
      runCount: effectRunCounts.projects, 
      selectedSubSegmentId,
      isLoadingForEdit: isLoadingForEditRef.current,
      guardRef: projectsForSubSegmentIdRef.current,
      optionsCount: projects.length
    });
    
    // Skip cascade if loading for edit mode (loadForEditMode handles this)
    if (isLoadingForEditRef.current) {
      ddlLog('PROJECT', 'skipped - edit mode loading in progress');
      return;
    }
    
    // Skip if bootstrap already loaded options for this sub-segment (survives StrictMode)
    if (selectedSubSegmentId && 
        projectsForSubSegmentIdRef.current === selectedSubSegmentId && 
        projects.length > 0) {
      ddlLog('PROJECT', 'skipped - bootstrap options already loaded', {
        forSubSegmentId: projectsForSubSegmentIdRef.current
      });
      return;
    }
    
    if (selectedSubSegmentId) {
      loadProjects(selectedSubSegmentId);
    } else {
      ddlLog('PROJECT', 'clearing (no sub-segment selected)');
      setProjects([]);
      setSelectedProjectId(null);
      projectsForSubSegmentIdRef.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Cascade effect intentionally triggers only on selectedSubSegmentId change
  }, [selectedSubSegmentId]);

  // Cascade: Load teams when project changes
  useEffect(() => {
    effectRunCounts.teams++;
    ddlLog('TEAM', 'useEffect-fired', { 
      runCount: effectRunCounts.teams, 
      selectedProjectId,
      isLoadingForEdit: isLoadingForEditRef.current,
      guardRef: teamsForProjectIdRef.current,
      optionsCount: teams.length
    });
    
    // Skip cascade if loading for edit mode (loadForEditMode handles this)
    if (isLoadingForEditRef.current) {
      ddlLog('TEAM', 'skipped - edit mode loading in progress');
      return;
    }
    
    // Skip if bootstrap already loaded options for this project (survives StrictMode)
    if (selectedProjectId && 
        teamsForProjectIdRef.current === selectedProjectId && 
        teams.length > 0) {
      ddlLog('TEAM', 'skipped - bootstrap options already loaded', {
        forProjectId: teamsForProjectIdRef.current
      });
      return;
    }
    
    if (selectedProjectId) {
      loadTeams(selectedProjectId);
    } else {
      ddlLog('TEAM', 'clearing (no project selected)');
      setTeams([]);
      setSelectedTeamId(null);
      teamsForProjectIdRef.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Cascade effect intentionally triggers only on selectedProjectId change
  }, [selectedProjectId]);

  /**
   * Load all segments
   */
  const loadSegments = async () => {
    segmentApiCallCount++;
    ddlLog('SEGMENT', 'load-start', { apiCallCount: segmentApiCallCount });
    const startTime = performance.now();
    
    setLoading(prev => ({ ...prev, segments: true }));
    setError(null);
    try {
      ddlLog('SEGMENT', 'api-call-start');
      const data = await dropdownApi.getSegments();
      const duration = (performance.now() - startTime).toFixed(1);
      ddlLog('SEGMENT', 'api-call-end', { duration: duration + 'ms', optionsCount: data?.length || 0 });
      setSegments(data || []);
    } catch (err) {
      console.error('Failed to load segments:', err);
      ddlLog('SEGMENT', 'api-error', { error: err.message });
      setError('Failed to load segments');
      setSegments([]);
    } finally {
      setLoading(prev => ({ ...prev, segments: false }));
      ddlLog('SEGMENT', 'load-end', { totalDuration: (performance.now() - startTime).toFixed(1) + 'ms' });
    }
  };

  /**
   * Load sub-segments for a segment
   */
  const loadSubSegments = async (segmentId) => {
    subSegmentApiCallCount++;
    ddlLog('SUBSEGMENT', 'load-start', { segmentId, apiCallCount: subSegmentApiCallCount });
    const startTime = performance.now();
    ddlLog('SUBSEGMENT', 'selected-id-before-options', { selectedSubSegmentId });
    
    setLoading(prev => ({ ...prev, subSegments: true }));
    try {
      ddlLog('SUBSEGMENT', 'api-call-start', { segmentId });
      const data = await dropdownApi.getSubSegmentsBySegment(segmentId);
      const duration = (performance.now() - startTime).toFixed(1);
      ddlLog('SUBSEGMENT', 'api-call-end', { duration: duration + 'ms', optionsCount: data?.length || 0 });
      setSubSegments(data || []);
      // Track which segment these options belong to (for cascade guard)
      subSegmentsForSegmentIdRef.current = segmentId;
      ddlLog('SUBSEGMENT', 'selected-id-after-options', { selectedSubSegmentId });
    } catch (err) {
      console.error('Failed to load sub-segments:', err);
      ddlLog('SUBSEGMENT', 'api-error', { error: err.message });
      setSubSegments([]);
      subSegmentsForSegmentIdRef.current = null;
    } finally {
      setLoading(prev => ({ ...prev, subSegments: false }));
      ddlLog('SUBSEGMENT', 'load-end', { totalDuration: (performance.now() - startTime).toFixed(1) + 'ms' });
    }
  };

  /**
   * Load projects for a sub-segment
   */
  const loadProjects = async (subSegmentId) => {
    projectApiCallCount++;
    ddlLog('PROJECT', 'load-start', { subSegmentId, apiCallCount: projectApiCallCount });
    const startTime = performance.now();
    ddlLog('PROJECT', 'selected-id-before-options', { selectedProjectId });
    
    setLoading(prev => ({ ...prev, projects: true }));
    try {
      ddlLog('PROJECT', 'api-call-start', { subSegmentId });
      const data = await dropdownApi.getProjects(subSegmentId);
      const duration = (performance.now() - startTime).toFixed(1);
      ddlLog('PROJECT', 'api-call-end', { duration: duration + 'ms', optionsCount: data?.length || 0 });
      setProjects(data || []);
      // Track which sub-segment these options belong to (for cascade guard)
      projectsForSubSegmentIdRef.current = subSegmentId;
      ddlLog('PROJECT', 'selected-id-after-options', { selectedProjectId });
    } catch (err) {
      console.error('Failed to load projects:', err);
      ddlLog('PROJECT', 'api-error', { error: err.message });
      setProjects([]);
      projectsForSubSegmentIdRef.current = null;
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
      ddlLog('PROJECT', 'load-end', { totalDuration: (performance.now() - startTime).toFixed(1) + 'ms' });
    }
  };

  /**
   * Load teams for a project
   */
  const loadTeams = async (projectId) => {
    teamApiCallCount++;
    ddlLog('TEAM', 'load-start', { projectId, apiCallCount: teamApiCallCount });
    const startTime = performance.now();
    ddlLog('TEAM', 'selected-id-before-options', { selectedTeamId });
    
    setLoading(prev => ({ ...prev, teams: true }));
    try {
      ddlLog('TEAM', 'api-call-start', { projectId });
      const data = await dropdownApi.getTeams(projectId);
      const duration = (performance.now() - startTime).toFixed(1);
      ddlLog('TEAM', 'api-call-end', { duration: duration + 'ms', optionsCount: data?.length || 0 });
      setTeams(data || []);
      // Track which project these options belong to (for cascade guard)
      teamsForProjectIdRef.current = projectId;
      ddlLog('TEAM', 'selected-id-after-options', { selectedTeamId });
    } catch (err) {
      console.error('Failed to load teams:', err);
      ddlLog('TEAM', 'api-error', { error: err.message });
      setTeams([]);
      teamsForProjectIdRef.current = null;
    } finally {
      setLoading(prev => ({ ...prev, teams: false }));
      ddlLog('TEAM', 'load-end', { totalDuration: (performance.now() - startTime).toFixed(1) + 'ms' });
    }
  };

  /**
   * Handle segment selection
   */
  const handleSegmentChange = useCallback((segmentId) => {
    if (isLocked.segment) return;
    ddlLog('HANDLER', 'handleSegmentChange', { segmentId });
    
    // Clear edit mode suppression - user is now manually changing dropdowns
    isLoadingForEditRef.current = false;
    
    setSelectedSegmentId(segmentId ? Number(segmentId) : null);
    // Clear downstream selections
    setSelectedSubSegmentId(null);
    setSelectedProjectId(null);
    setSelectedTeamId(null);
    // Clear guard refs so cascade effects will fetch new options
    subSegmentsForSegmentIdRef.current = null;
    projectsForSubSegmentIdRef.current = null;
    teamsForProjectIdRef.current = null;
  }, [isLocked.segment]);

  /**
   * Handle sub-segment selection
   */
  const handleSubSegmentChange = useCallback((subSegmentId) => {
    if (isLocked.subSegment) return;
    ddlLog('HANDLER', 'handleSubSegmentChange', { subSegmentId });
    
    // Clear edit mode suppression - user is now manually changing dropdowns
    isLoadingForEditRef.current = false;
    
    setSelectedSubSegmentId(subSegmentId ? Number(subSegmentId) : null);
    // Clear downstream selections
    setSelectedProjectId(null);
    setSelectedTeamId(null);
    // Clear guard refs so cascade effects will fetch new options
    projectsForSubSegmentIdRef.current = null;
    teamsForProjectIdRef.current = null;
  }, [isLocked.subSegment]);

  /**
   * Handle project selection
   */
  const handleProjectChange = useCallback((projectId) => {
    if (isLocked.project) return;
    ddlLog('HANDLER', 'handleProjectChange', { projectId });
    
    // Clear edit mode suppression - user is now manually changing dropdowns
    isLoadingForEditRef.current = false;
    
    setSelectedProjectId(projectId ? Number(projectId) : null);
    // Clear downstream selection
    setSelectedTeamId(null);
    // Clear guard ref so cascade effect will fetch new options
    teamsForProjectIdRef.current = null;
  }, [isLocked.project]);

  /**
   * Handle team selection
   */
  const handleTeamChange = useCallback((teamId) => {
    if (isLocked.team) return;
    ddlLog('HANDLER', 'handleTeamChange', { teamId });
    
    // Clear edit mode suppression - user is now manually changing dropdowns
    isLoadingForEditRef.current = false;
    
    setSelectedTeamId(teamId ? Number(teamId) : null);
  }, [isLocked.team]);

  /**
   * Reset all selections
   */
  const reset = useCallback(() => {
    if (!isLocked.segment) setSelectedSegmentId(null);
    if (!isLocked.subSegment) setSelectedSubSegmentId(null);
    if (!isLocked.project) setSelectedProjectId(null);
    if (!isLocked.team) setSelectedTeamId(null);
    
    // Clear guard refs
    subSegmentsForSegmentIdRef.current = null;
    projectsForSubSegmentIdRef.current = null;
    teamsForProjectIdRef.current = null;
    
    // Clear edit mode loading flag (allows cascade effects to run normally)
    isLoadingForEditRef.current = false;
    
    // Reapply role-based preselection
    applyRoleBasedPreselection();
  }, [isLocked, applyRoleBasedPreselection]);

  /**
   * Load org hierarchy for Edit mode - SEQUENTIAL loading.
   * Ensures each dropdown's options are loaded BEFORE setting its value.
   * This prevents cascade effects from clearing already-set values.
   * 
   * @param {Object} orgIds - { segmentId, subSegmentId, projectId, teamId }
   * @returns {Promise<void>}
   */
  const loadForEditMode = useCallback(async ({ segmentId, subSegmentId, projectId, teamId }) => {
    ddlLog('EDIT_MODE', 'loadForEditMode-called', { segmentId, subSegmentId, projectId, teamId });
    const totalStart = performance.now();
    
    // Allow loading with any available org IDs (not all employees have teams)
    if (!segmentId && !subSegmentId && !projectId && !teamId) {
      ddlLog('EDIT_MODE', 'skipped - no org IDs provided');
      return;
    }
    
    // Set flag to suppress cascade effects during edit loading
    isLoadingForEditRef.current = true;
    ddlLog('EDIT_MODE', 'cascade-suppression-enabled');
    
    try {
      // Step 1: Ensure segments are loaded (uses cache/single-flight)
      ddlLog('EDIT_MODE', 'step1-segments', { currentCount: segments.length });
      let segmentsData = segments;
      if (segments.length === 0) {
        const segStart = performance.now();
        ddlLog('EDIT_MODE', 'segments-need-load');
        setLoading(prev => ({ ...prev, segments: true }));
        segmentsData = await dropdownApi.getSegments();
        ddlLog('EDIT_MODE', 'segments-loaded', { count: segmentsData?.length, duration: (performance.now() - segStart).toFixed(1) + 'ms' });
        setSegments(segmentsData || []);
        setLoading(prev => ({ ...prev, segments: false }));
      } else {
        ddlLog('EDIT_MODE', 'segments-already-loaded', { count: segments.length });
      }
      
      // Step 2: Set segment and load sub-segments
      if (segmentId) {
        ddlLog('EDIT_MODE', 'step2-setting-segment', { segmentId, currentSelectedSegmentId: selectedSegmentId });
        setSelectedSegmentId(Number(segmentId));
        
        const subSegStart = performance.now();
        ddlLog('EDIT_MODE', 'step2-loading-subSegments', { forSegmentId: segmentId });
        setLoading(prev => ({ ...prev, subSegments: true }));
        const subSegmentsData = await dropdownApi.getSubSegmentsBySegment(segmentId);
        ddlLog('EDIT_MODE', 'step2-subSegments-loaded', { count: subSegmentsData?.length, duration: (performance.now() - subSegStart).toFixed(1) + 'ms' });
        setSubSegments(subSegmentsData || []);
        setLoading(prev => ({ ...prev, subSegments: false }));
      }
      
      // Step 3: Set sub-segment and load projects
      if (subSegmentId) {
        ddlLog('EDIT_MODE', 'step3-setting-subSegment', { subSegmentId, currentSelectedSubSegmentId: selectedSubSegmentId });
        setSelectedSubSegmentId(Number(subSegmentId));
        
        const projStart = performance.now();
        ddlLog('EDIT_MODE', 'step3-loading-projects', { forSubSegmentId: subSegmentId });
        setLoading(prev => ({ ...prev, projects: true }));
        const projectsData = await dropdownApi.getProjects(subSegmentId);
        ddlLog('EDIT_MODE', 'step3-projects-loaded', { count: projectsData?.length, duration: (performance.now() - projStart).toFixed(1) + 'ms' });
        setProjects(projectsData || []);
        setLoading(prev => ({ ...prev, projects: false }));
      }
      
      // Step 4: Set project and load teams
      if (projectId) {
        ddlLog('EDIT_MODE', 'step4-setting-project', { projectId, currentSelectedProjectId: selectedProjectId });
        setSelectedProjectId(Number(projectId));
        
        const teamStart = performance.now();
        ddlLog('EDIT_MODE', 'step4-loading-teams', { forProjectId: projectId });
        setLoading(prev => ({ ...prev, teams: true }));
        const teamsData = await dropdownApi.getTeams(projectId);
        ddlLog('EDIT_MODE', 'step4-teams-loaded', { count: teamsData?.length, duration: (performance.now() - teamStart).toFixed(1) + 'ms' });
        setTeams(teamsData || []);
        setLoading(prev => ({ ...prev, teams: false }));
      }
      
      // Step 5: Set team (options already loaded in step 4)
      if (teamId) {
        ddlLog('EDIT_MODE', 'step5-setting-team', { teamId, currentSelectedTeamId: selectedTeamId });
        setSelectedTeamId(Number(teamId));
      }
      
      ddlLog('EDIT_MODE', 'loadForEditMode-complete', { 
        totalDuration: (performance.now() - totalStart).toFixed(1) + 'ms',
        finalSelections: { segmentId, subSegmentId, projectId, teamId }
      });
    } catch (err) {
      ddlLog('EDIT_MODE', 'loadForEditMode-ERROR', { error: err.message, totalDuration: (performance.now() - totalStart).toFixed(1) + 'ms' });
      console.error('Failed to load org hierarchy for edit:', err);
      throw err;
    } finally {
      // Clear flag to re-enable cascade effects
      isLoadingForEditRef.current = false;
      ddlLog('EDIT_MODE', 'cascade-suppression-disabled');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- selectedIds are only used for diagnostic logging, not logic
  }, [segments]);

  /**
   * @deprecated Use loadForEditMode instead for Edit mode.
   * Prefill selections with a team ID (for edit mode).
   * Loads the org hierarchy backwards from team.
   * @param {number} teamId - The team ID to prefill
   */
  const prefillFromTeamId = useCallback(async (teamId) => {
    if (!teamId) return;
    
    try {
      // Load teams first to get the team's project_id
      // We need to search through the hierarchy to find the full path
      const teamData = await dropdownApi.getTeams(null); // Get all teams
      const team = teamData.find(t => t.team_id === teamId);
      
      if (!team) {
        console.warn('Team not found for prefill:', teamId);
        return;
      }
      
      // Load projects to find the project and get its sub_segment_id
      const projectData = await dropdownApi.getProjects(null);
      const project = projectData.find(p => p.project_id === team.project_id);
      
      if (!project) {
        console.warn('Project not found for prefill');
        return;
      }
      
      // Load sub-segments to find the sub-segment and get its segment_id
      const subSegmentData = await dropdownApi.getSubSegments(null);
      const subSegment = subSegmentData.find(s => s.sub_segment_id === project.sub_segment_id);
      
      if (!subSegment) {
        console.warn('Sub-segment not found for prefill');
        return;
      }
      
      // Now set all the selections in order
      setSelectedSegmentId(subSegment.segment_id);
      setSelectedSubSegmentId(subSegment.sub_segment_id);
      setSelectedProjectId(project.project_id);
      setSelectedTeamId(teamId);
    } catch (err) {
      console.error('Failed to prefill org assignment:', err);
    }
  }, []);

  return {
    // Current selections
    selectedSegmentId,
    selectedSubSegmentId,
    selectedProjectId,
    selectedTeamId,
    
    // Dropdown options
    segments,
    subSegments,
    projects,
    teams,
    
    // Loading states
    loading,
    
    // Error
    error,
    
    // Lock states (based on role)
    isLocked,
    
    // Disabled states (locked or no parent selection)
    isDisabled,
    
    // Handlers
    handleSegmentChange,
    handleSubSegmentChange,
    handleProjectChange,
    handleTeamChange,
    
    // Utility
    reset,
    
    /**
     * Suppress cascade effects during edit mode initialization.
     * Call this when awaiting bootstrap data to prevent premature API calls.
     */
    suppressCascades: () => {
      ddlLog('SUPPRESS', 'suppressCascades-called');
      isLoadingForEditRef.current = true;
    },
    loadForEditMode,   // Sequential loading for Edit mode
    prefillFromTeamId, // @deprecated - use loadForEditMode instead
    
    /**
     * Set all dropdown options and selections from bootstrap response.
     * Bypasses API calls entirely - used with edit-bootstrap endpoint.
     * 
     * @param {Object} options - { segments, sub_segments, projects, teams }
     * @param {Object} selections - { segmentId, subSegmentId, projectId, teamId }
     */
    setFromBootstrap: (options, selections) => {
      // ddlLog('BOOTSTRAP', 'setFromBootstrap-called', { 
      //   segments: options.segments?.length,
      //   subSegments: options.sub_segments?.length,
      //   projects: options.projects?.length,
      //   teams: options.teams?.length,
      //   selections 
      // });
      ddlLog('BOOTSTRAP', 'incoming', {
        selections,
        optionCounts: {
          subSegments: options.sub_segments?.length,
          projects: options.projects?.length,
          teams: options.teams?.length,
        },
        selectionExistsInOptions: {
          subSegment: options.sub_segments?.some(
            s => s.sub_segment_id === Number(selections.subSegmentId)
          ),
          project: options.projects?.some(
            p => p.project_id === Number(selections.projectId)
          ),
          team: options.teams?.some(
            t => t.team_id === Number(selections.teamId)
          ),
        }
      });

      
      // Suppress cascade effects during bootstrap
      isLoadingForEditRef.current = true;
      
      // Set all dropdown options at once
      // IMPORTANT: Normalize field names to match what dropdown API returns (id, name)
      // Bootstrap returns segment_id/segment_name, but dropdowns expect id/name
      setSegments(options.segments?.map(s => ({
        id: s.segment_id,
        name: s.segment_name
      })) || []);
      
      setSubSegments(options.sub_segments?.map(ss => ({
        id: ss.sub_segment_id,
        name: ss.sub_segment_name,
        segment_id: ss.segment_id  // Keep for filtering
      })) || []);
      
      setProjects(options.projects?.map(p => ({
        id: p.project_id,
        name: p.project_name,
        sub_segment_id: p.sub_segment_id  // Keep for filtering
      })) || []);
      
      setTeams(options.teams?.map(t => ({
        id: t.team_id,
        name: t.team_name,
        project_id: t.project_id  // Keep for filtering
      })) || []);
      
      // Set all selections at once
      if (selections.segmentId) setSelectedSegmentId(Number(selections.segmentId));
      if (selections.subSegmentId) setSelectedSubSegmentId(Number(selections.subSegmentId));
      if (selections.projectId) setSelectedProjectId(Number(selections.projectId));
      if (selections.teamId) setSelectedTeamId(Number(selections.teamId));
      
      // Set guard refs to indicate which parent ID the options belong to
      // This prevents cascade effects from re-fetching (survives StrictMode)
      subSegmentsForSegmentIdRef.current = selections.segmentId ? Number(selections.segmentId) : null;
      projectsForSubSegmentIdRef.current = selections.subSegmentId ? Number(selections.subSegmentId) : null;
      teamsForProjectIdRef.current = selections.projectId ? Number(selections.projectId) : null;
      
      ddlLog('BOOTSTRAP', 'guard-refs-set', {
        subSegmentsForSegmentId: subSegmentsForSegmentIdRef.current,
        projectsForSubSegmentId: projectsForSubSegmentIdRef.current,
        teamsForProjectId: teamsForProjectIdRef.current
      });
      
      // DO NOT clear isLoadingForEditRef here - keep cascades suppressed
      // The guard refs prevent duplicate API calls
      // isLoadingForEditRef will be cleared when user manually changes a dropdown
      ddlLog('BOOTSTRAP', 'setFromBootstrap-complete', { isLoadingForEdit: isLoadingForEditRef.current });
    },
    
    // For testing
    loadSegments,
    loadSubSegments,
    loadProjects,
    loadTeams
  };
}

export default useOrgAssignment;
