/**
 * Org Hierarchy API client
 * Handles API calls for Organization Hierarchy data
 */
import httpClient from './httpClient';

/**
 * @typedef {Object} TeamNode
 * @property {number} team_id
 * @property {string} team_name
 */

/**
 * @typedef {Object} ProjectNode
 * @property {number} project_id
 * @property {string} project_name
 * @property {TeamNode[]} teams
 */

/**
 * @typedef {Object} SubSegmentNode
 * @property {number} sub_segment_id
 * @property {string} sub_segment_name
 * @property {ProjectNode[]} projects
 */

/**
 * @typedef {Object} SegmentNode
 * @property {number} segment_id
 * @property {string} segment_name
 * @property {SubSegmentNode[]} sub_segments
 */

/**
 * @typedef {Object} OrgHierarchyResponse
 * @property {SegmentNode[]} segments
 * @property {number} total_segments
 * @property {number} total_sub_segments
 * @property {number} total_projects
 * @property {number} total_teams
 */

/**
 * Fetch the complete organization hierarchy.
 * 
 * @param {Object} options - Options object
 * @param {AbortSignal} [options.signal] - AbortController signal for cancellation
 * @returns {Promise<OrgHierarchyResponse>} Organization hierarchy response
 */
export async function fetchOrgHierarchy({ signal } = {}) {
  return httpClient.get('/org-hierarchy', {}, { signal });
}

/**
 * @typedef {Object} SegmentCreateResponse
 * @property {number} segment_id
 * @property {string} segment_name
 * @property {string|null} created_at
 * @property {string|null} created_by
 * @property {string} message
 */

/**
 * Create a new segment.
 * 
 * @param {string} name - Segment name
 * @returns {Promise<SegmentCreateResponse>} Created segment
 */
export async function createSegment(name) {
  return httpClient.post('/org-hierarchy/segments', { name });
}

/**
 * @typedef {Object} SubSegmentCreateResponse
 * @property {number} sub_segment_id
 * @property {string} sub_segment_name
 * @property {number} segment_id
 * @property {string|null} created_at
 * @property {string|null} created_by
 * @property {string} message
 */

/**
 * Create a new sub-segment under a segment.
 * 
 * @param {number} segmentId - Parent segment ID
 * @param {string} name - Sub-segment name
 * @returns {Promise<SubSegmentCreateResponse>} Created sub-segment
 */
export async function createSubSegment(segmentId, name) {
  return httpClient.post('/org-hierarchy/sub-segments', { segment_id: segmentId, name });
}

/**
 * @typedef {Object} ProjectCreateResponse
 * @property {number} project_id
 * @property {string} project_name
 * @property {number} sub_segment_id
 * @property {string|null} created_at
 * @property {string|null} created_by
 * @property {string} message
 */

/**
 * Create a new project under a sub-segment.
 * 
 * @param {number} subSegmentId - Parent sub-segment ID
 * @param {string} name - Project name
 * @returns {Promise<ProjectCreateResponse>} Created project
 */
export async function createProject(subSegmentId, name) {
  return httpClient.post('/org-hierarchy/projects', { sub_segment_id: subSegmentId, name });
}

/**
 * @typedef {Object} TeamCreateResponse
 * @property {number} team_id
 * @property {string} team_name
 * @property {number} project_id
 * @property {string|null} created_at
 * @property {string|null} created_by
 * @property {string} message
 */

/**
 * Create a new team under a project.
 * 
 * @param {number} projectId - Parent project ID
 * @param {string} name - Team name
 * @returns {Promise<TeamCreateResponse>} Created team
 */
export async function createTeam(projectId, name) {
  return httpClient.post('/org-hierarchy/teams', { project_id: projectId, name });
}

/**
 * @typedef {Object} SegmentUpdateResponse
 * @property {number} segment_id
 * @property {string} segment_name
 * @property {string|null} updated_at
 * @property {string|null} updated_by
 * @property {string} message
 */

/**
 * Update a segment's name.
 * 
 * @param {number} segmentId - Segment ID to update
 * @param {string} name - New segment name
 * @returns {Promise<SegmentUpdateResponse>} Updated segment
 */
export async function updateSegmentName(segmentId, name) {
  return httpClient.put(`/org-hierarchy/segments/${segmentId}`, { name });
}

/**
 * @typedef {Object} SubSegmentUpdateResponse
 * @property {number} sub_segment_id
 * @property {string} sub_segment_name
 * @property {number} segment_id
 * @property {string|null} updated_at
 * @property {string|null} updated_by
 * @property {string} message
 */

/**
 * Update a sub-segment's name.
 * 
 * @param {number} subSegmentId - Sub-segment ID to update
 * @param {string} name - New sub-segment name
 * @returns {Promise<SubSegmentUpdateResponse>} Updated sub-segment
 */
export async function updateSubSegmentName(subSegmentId, name) {
  return httpClient.put(`/org-hierarchy/sub-segments/${subSegmentId}`, { name });
}

/**
 * @typedef {Object} ProjectUpdateResponse
 * @property {number} project_id
 * @property {string} project_name
 * @property {number} sub_segment_id
 * @property {string} message
 */

/**
 * Update a project's name.
 * 
 * @param {number} projectId - Project ID to update
 * @param {string} name - New project name
 * @returns {Promise<ProjectUpdateResponse>} Updated project
 */
export async function updateProjectName(projectId, name) {
  return httpClient.put(`/org-hierarchy/projects/${projectId}`, { name });
}

/**
 * @typedef {Object} TeamUpdateResponse
 * @property {number} team_id
 * @property {string} team_name
 * @property {number} project_id
 * @property {string} message
 */

/**
 * Update a team's name.
 * 
 * @param {number} teamId - Team ID to update
 * @param {string} name - New team name
 * @returns {Promise<TeamUpdateResponse>} Updated team
 */
export async function updateTeamName(teamId, name) {
  return httpClient.put(`/org-hierarchy/teams/${teamId}`, { name });
}

/**
 * @typedef {Object} DependencyConflictResponse
 * @property {string} message - Error message
 * @property {Object} dependencies - Dependency counts
 * @property {number} [dependencies.sub_segments] - Count of sub-segments
 * @property {number} [dependencies.projects] - Count of projects
 * @property {number} [dependencies.teams] - Count of teams
 */

/**
 * @typedef {Object} CheckDeleteResult
 * @property {boolean} canDelete - Whether deletion is allowed (no dependencies)
 * @property {DependencyConflictResponse|null} conflict - Conflict data if has dependencies
 */

// Import API_BASE_URL for direct fetch (to properly handle various status codes)
import { API_BASE_URL } from '../../config/apiConfig';

/**
 * Check if a segment can be deleted (dry run - does NOT delete).
 * 
 * @param {number} segmentId - Segment ID to check
 * @returns {Promise<CheckDeleteResult>} Check result
 * @throws {Error} If segment not found (404) or other server error
 */
export async function checkCanDeleteSegment(segmentId) {
  const response = await fetch(`${API_BASE_URL}/org-hierarchy/segments/${segmentId}?dry_run=true`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // 200 OK = can delete (no dependencies)
  if (response.status === 200) {
    return { canDelete: true, conflict: null };
  }
  
  // 409 Conflict = has dependencies
  if (response.status === 409) {
    const data = await response.json();
    return { canDelete: false, conflict: data };
  }
  
  // 404 Not Found or other errors
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }
  
  return { canDelete: true, conflict: null };
}

/**
 * Delete a segment (soft delete - actually deletes).
 * Should only be called after user confirms deletion (when checkCanDeleteSegment returns canDelete=true).
 * 
 * @param {number} segmentId - Segment ID to delete
 * @throws {Error} If deletion fails
 */
export async function deleteSegment(segmentId) {
  const response = await fetch(`${API_BASE_URL}/org-hierarchy/segments/${segmentId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // 204 No Content = success
  if (response.status === 204) {
    return;
  }
  
  // Any error
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }
}

/**
 * Check if a sub-segment can be deleted (dry run - does NOT delete).
 * 
 * @param {number} subSegmentId - Sub-segment ID to check
 * @returns {Promise<CheckDeleteResult>} Check result
 * @throws {Error} If sub-segment not found (404) or other server error
 */
export async function checkCanDeleteSubSegment(subSegmentId) {
  const response = await fetch(`${API_BASE_URL}/org-hierarchy/sub-segments/${subSegmentId}?dry_run=true`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // 200 OK = can delete (no dependencies)
  if (response.status === 200) {
    return { canDelete: true, conflict: null };
  }
  
  // 409 Conflict = has dependencies
  if (response.status === 409) {
    const data = await response.json();
    return { canDelete: false, conflict: data };
  }
  
  // 404 Not Found or other errors
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }
  
  return { canDelete: true, conflict: null };
}

/**
 * Delete a sub-segment (soft delete - actually deletes).
 * Should only be called after user confirms deletion (when checkCanDeleteSubSegment returns canDelete=true).
 * 
 * @param {number} subSegmentId - Sub-segment ID to delete
 * @throws {Error} If deletion fails
 */
export async function deleteSubSegment(subSegmentId) {
  const response = await fetch(`${API_BASE_URL}/org-hierarchy/sub-segments/${subSegmentId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // 204 No Content = success
  if (response.status === 204) {
    return;
  }
  
  // Any error
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }
}

/**
 * Check if a project can be deleted (dry run - does NOT delete).
 * 
 * @param {number} projectId - Project ID to check
 * @returns {Promise<CheckDeleteResult>} Check result
 * @throws {Error} If project not found (404) or other server error
 */
export async function checkCanDeleteProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/org-hierarchy/projects/${projectId}?dry_run=true`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // 200 OK = can delete (no dependencies)
  if (response.status === 200) {
    return { canDelete: true, conflict: null };
  }
  
  // 409 Conflict = has dependencies
  if (response.status === 409) {
    const data = await response.json();
    return { canDelete: false, conflict: data };
  }
  
  // 404 Not Found or other errors
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }
  
  return { canDelete: true, conflict: null };
}

/**
 * Delete a project (soft delete - actually deletes).
 * Should only be called after user confirms deletion (when checkCanDeleteProject returns canDelete=true).
 * 
 * @param {number} projectId - Project ID to delete
 * @throws {Error} If deletion fails
 */
export async function deleteProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/org-hierarchy/projects/${projectId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // 204 No Content = success
  if (response.status === 204) {
    return;
  }
  
  // Any error
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }
}

/**
 * Delete a team (soft delete).
 * Will return 409 Conflict if team has employees assigned.
 * 
 * @param {number} teamId - Team ID to delete
 * @throws {Error} If deletion fails or team has dependencies
 */
export async function deleteTeam(teamId) {
  const response = await fetch(`${API_BASE_URL}/org-hierarchy/teams/${teamId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // 204 No Content = success
  if (response.status === 204) {
    return;
  }
  
  // 409 Conflict - has dependencies
  if (response.status === 409) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      throw new Error('Team has dependencies and cannot be deleted');
    }
    const error = new Error(errorData.detail?.message || 'Team has dependencies and cannot be deleted');
    error.status = 409;
    error.data = errorData.detail;
    throw error;
  }
  
  // Any other error
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }
}
