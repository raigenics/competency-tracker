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
import { useState, useEffect, useCallback } from 'react';
import { dropdownApi } from '../services/api/dropdownApi.js';
import { getRbacContext, RBAC_ROLES } from '../config/featureFlags.js';

/**
 * @returns {Object} Organizational assignment state and handlers
 */
export function useOrgAssignment() {
  // Get current user's role and scope
  const { role, scope } = getRbacContext();
  
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
  const isLocked = {
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
  };
  
  // Determine which fields are disabled (locked or no parent selection)
  const isDisabled = {
    segment: isLocked.segment,
    subSegment: isLocked.subSegment || (!selectedSegmentId && !isLocked.subSegment),
    project: isLocked.project || (!selectedSubSegmentId && !isLocked.project),
    team: isLocked.team || (!selectedProjectId && !isLocked.team)
  };

  // Load segments on mount
  useEffect(() => {
    loadSegments();
  }, []);

  // Apply preselection based on role scope
  useEffect(() => {
    applyRoleBasedPreselection();
  }, [role, scope, segments]);

  // Cascade: Load sub-segments when segment changes
  useEffect(() => {
    if (selectedSegmentId) {
      loadSubSegments(selectedSegmentId);
    } else {
      setSubSegments([]);
      setSelectedSubSegmentId(null);
    }
  }, [selectedSegmentId]);

  // Cascade: Load projects when sub-segment changes
  useEffect(() => {
    if (selectedSubSegmentId) {
      loadProjects(selectedSubSegmentId);
    } else {
      setProjects([]);
      setSelectedProjectId(null);
    }
  }, [selectedSubSegmentId]);

  // Cascade: Load teams when project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadTeams(selectedProjectId);
    } else {
      setTeams([]);
      setSelectedTeamId(null);
    }
  }, [selectedProjectId]);

  /**
   * Load all segments
   */
  const loadSegments = async () => {
    setLoading(prev => ({ ...prev, segments: true }));
    setError(null);
    try {
      const data = await dropdownApi.getSegments();
      setSegments(data || []);
    } catch (err) {
      console.error('Failed to load segments:', err);
      setError('Failed to load segments');
      setSegments([]);
    } finally {
      setLoading(prev => ({ ...prev, segments: false }));
    }
  };

  /**
   * Load sub-segments for a segment
   */
  const loadSubSegments = async (segmentId) => {
    setLoading(prev => ({ ...prev, subSegments: true }));
    try {
      const data = await dropdownApi.getSubSegmentsBySegment(segmentId);
      setSubSegments(data || []);
    } catch (err) {
      console.error('Failed to load sub-segments:', err);
      setSubSegments([]);
    } finally {
      setLoading(prev => ({ ...prev, subSegments: false }));
    }
  };

  /**
   * Load projects for a sub-segment
   */
  const loadProjects = async (subSegmentId) => {
    setLoading(prev => ({ ...prev, projects: true }));
    try {
      const data = await dropdownApi.getProjects(subSegmentId);
      setProjects(data || []);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setProjects([]);
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
    }
  };

  /**
   * Load teams for a project
   */
  const loadTeams = async (projectId) => {
    setLoading(prev => ({ ...prev, teams: true }));
    try {
      const data = await dropdownApi.getTeams(projectId);
      setTeams(data || []);
    } catch (err) {
      console.error('Failed to load teams:', err);
      setTeams([]);
    } finally {
      setLoading(prev => ({ ...prev, teams: false }));
    }
  };

  /**
   * Apply role-based preselection from user's scope
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

  /**
   * Handle segment selection
   */
  const handleSegmentChange = useCallback((segmentId) => {
    if (isLocked.segment) return;
    setSelectedSegmentId(segmentId ? Number(segmentId) : null);
    // Clear downstream selections
    setSelectedSubSegmentId(null);
    setSelectedProjectId(null);
    setSelectedTeamId(null);
  }, [isLocked.segment]);

  /**
   * Handle sub-segment selection
   */
  const handleSubSegmentChange = useCallback((subSegmentId) => {
    if (isLocked.subSegment) return;
    setSelectedSubSegmentId(subSegmentId ? Number(subSegmentId) : null);
    // Clear downstream selections
    setSelectedProjectId(null);
    setSelectedTeamId(null);
  }, [isLocked.subSegment]);

  /**
   * Handle project selection
   */
  const handleProjectChange = useCallback((projectId) => {
    if (isLocked.project) return;
    setSelectedProjectId(projectId ? Number(projectId) : null);
    // Clear downstream selection
    setSelectedTeamId(null);
  }, [isLocked.project]);

  /**
   * Handle team selection
   */
  const handleTeamChange = useCallback((teamId) => {
    if (isLocked.team) return;
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
    
    // Reapply role-based preselection
    applyRoleBasedPreselection();
  }, [isLocked, applyRoleBasedPreselection]);

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
    
    // For testing
    loadSegments,
    loadSubSegments,
    loadProjects,
    loadTeams
  };
}

export default useOrgAssignment;
