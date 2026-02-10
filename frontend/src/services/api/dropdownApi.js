// Dropdown API service for dashboard filters
import { API_BASE_URL } from '../../config/apiConfig.js';

// ========== DIAGNOSTIC LOGGING - START ==========
const API_T0 = performance.now();
const apiLog = (endpoint, msg, extra = {}) => {
  const t = (performance.now() - API_T0).toFixed(1);
  console.log(`[API][${endpoint}] t=${t}ms ${msg}`, extra);
};
let apiCallCounts = { segments: 0, subSegments: 0, subSegmentsBySegment: 0, projects: 0, teams: 0 };
// ========== DIAGNOSTIC LOGGING - END ==========

// ========== SEGMENT CACHE (single-flight pattern) ==========
let segmentsCache = null;
let segmentsInFlight = null;

export const dropdownApi = {
  // Get all segments (cached, single-flight)
  async getSegments() {
    // Return cached result if available
    if (segmentsCache !== null) {
      apiLog('SEGMENTS', 'cache-hit', { count: segmentsCache.length });
      return segmentsCache;
    }
    
    // Return in-flight promise if request already pending (single-flight)
    if (segmentsInFlight !== null) {
      apiLog('SEGMENTS', 'single-flight-reuse');
      return segmentsInFlight;
    }
    
    apiCallCounts.segments++;
    apiLog('SEGMENTS', 'call-start', { callCount: apiCallCounts.segments });
    const startTime = performance.now();
    
    // Create and store the in-flight promise
    segmentsInFlight = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/dropdown/segments`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const duration = (performance.now() - startTime).toFixed(1);
        apiLog('SEGMENTS', 'call-end', { duration: duration + 'ms', count: data?.segments?.length || 0 });
        
        // Cache the result
        segmentsCache = data.segments || [];
        return segmentsCache;
      } catch (error) {
        apiLog('SEGMENTS', 'call-error', { error: error.message });
        console.error('Failed to fetch segments:', error);
        throw error;
      } finally {
        // Clear in-flight after completion (success or error)
        segmentsInFlight = null;
      }
    })();
    
    return segmentsInFlight;
  },
  
  // Clear segments cache (for testing or manual refresh)
  clearSegmentsCache() {
    apiLog('SEGMENTS', 'cache-cleared');
    segmentsCache = null;
    segmentsInFlight = null;
  },

  // Get sub-segments for a specific segment
  async getSubSegmentsBySegment(segmentId) {
    apiCallCounts.subSegmentsBySegment++;
    apiLog('SUBSEGMENTS_BY_SEGMENT', 'call-start', { segmentId, callCount: apiCallCounts.subSegmentsBySegment });
    const startTime = performance.now();
    try {
      const response = await fetch(`${API_BASE_URL}/dropdown/segments/${segmentId}/sub-segments`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const duration = (performance.now() - startTime).toFixed(1);
      apiLog('SUBSEGMENTS_BY_SEGMENT', 'call-end', { duration: duration + 'ms', count: data?.sub_segments?.length || 0 });
      return data.sub_segments;
    } catch (error) {
      apiLog('SUBSEGMENTS_BY_SEGMENT', 'call-error', { error: error.message });
      console.error(`Failed to fetch sub-segments for segment ${segmentId}:`, error);
      throw error;
    }
  },

  // Get all sub-segments (legacy - for backward compatibility)
  async getSubSegments() {
    apiCallCounts.subSegments++;
    apiLog('SUBSEGMENTS_ALL', 'call-start', { callCount: apiCallCounts.subSegments });
    const startTime = performance.now();
    try {
      const response = await fetch(`${API_BASE_URL}/dropdown/sub-segments`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const duration = (performance.now() - startTime).toFixed(1);
      apiLog('SUBSEGMENTS_ALL', 'call-end', { duration: duration + 'ms', count: data?.sub_segments?.length || 0 });
      return data.sub_segments;
    } catch (error) {
      apiLog('SUBSEGMENTS_ALL', 'call-error', { error: error.message });
      console.error('Failed to fetch sub-segments:', error);
      throw error;
    }
  },

  // Get projects for a specific sub-segment
  async getProjects(subSegmentId) {
    apiCallCounts.projects++;
    apiLog('PROJECTS', 'call-start', { subSegmentId, callCount: apiCallCounts.projects });
    const startTime = performance.now();
    try {
      const response = await fetch(`${API_BASE_URL}/dropdown/projects?sub_segment_id=${subSegmentId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const duration = (performance.now() - startTime).toFixed(1);
      apiLog('PROJECTS', 'call-end', { duration: duration + 'ms', count: data?.projects?.length || 0 });
      return data.projects;
    } catch (error) {
      apiLog('PROJECTS', 'call-error', { error: error.message });
      console.error(`Failed to fetch projects for sub-segment ${subSegmentId}:`, error);
      throw error;
    }
  },

  // Get teams for a specific project
  async getTeams(projectId) {
    apiCallCounts.teams++;
    apiLog('TEAMS', 'call-start', { projectId, callCount: apiCallCounts.teams });
    const startTime = performance.now();
    try {
      const response = await fetch(`${API_BASE_URL}/dropdown/teams?project_id=${projectId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const duration = (performance.now() - startTime).toFixed(1);
      apiLog('TEAMS', 'call-end', { duration: duration + 'ms', count: data?.teams?.length || 0 });
      return data.teams;
    } catch (error) {
      apiLog('TEAMS', 'call-error', { error: error.message });
      console.error(`Failed to fetch teams for project ${projectId}:`, error);
      throw error;
    }
  }
};
