import httpClient from './httpClient.js';
import { DEFAULT_DASHBOARD_CONTEXT } from '../../config/featureFlags.js';

/**
 * Dashboard API service for fetching dashboard metrics and analytics.
 * 
 * IMPORTANT: 
 * - Employee scope, top skills, and skill momentum respond to filter changes
 * - Org skill coverage is organization-wide and ignores all filters
 */
export const dashboardApi = {
  /**
   * Get employee scope count based on filters.
   * This endpoint responds to filter changes.
   */
  async getDashboardMetrics(filters = {}) {
    try {
      const params = {};
      if (filters.subSegment) params.sub_segment_id = filters.subSegment;
      if (filters.project) params.project_id = filters.project;
      if (filters.team) params.team_id = filters.team;
      
      return await httpClient.get('/dashboard/employee-scope', params);
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      throw error;
    }
  },

  /**
   * Get top skills by employee count based on filters.
   * This endpoint responds to filter changes.
   * 
   * CHANGE #2: Limit to 8 skills max (was 10) for non-team scopes.
   * API already supports 'limit' param - no backend change required.
   */
  async getSkillDistribution(filters = {}) {
    try {
      // Top Skills limited to 8 via API 'limit' param (API already supports this)
      const params = { limit: filters.team ? 5 : 8 };
      if (filters.subSegment) params.sub_segment_id = filters.subSegment;
      if (filters.project) params.project_id = filters.project;
      if (filters.team) params.team_id = filters.team;
      
      return await httpClient.get('/dashboard/top-skills', params);
    } catch (error) {
      console.error('Failed to fetch skill distribution:', error);
      throw error;
    }
  },

  /**
   * Get organizational skill coverage data.
   * This endpoint is organization-wide and ignores all filters.
   * Should only be fetched ONCE on dashboard mount.
   */
  async getOrgCoverage() {
    try {
      return await httpClient.get('/dashboard/org-skill-coverage');
    } catch (error) {
      console.error('Failed to fetch org coverage:', error);
      throw error;
    }
  },

  /**
   * Get skill progress momentum data based on filters.
   * This endpoint responds to filter changes.
   */
  async getSkillProgressMomentum(filters = {}) {
    try {
      const params = {};
      if (filters.subSegment) params.sub_segment_id = filters.subSegment;
      if (filters.project) params.project_id = filters.project;
      if (filters.team) params.team_id = filters.team;
      
      return await httpClient.get('/dashboard/skill-momentum', params);
    } catch (error) {
      console.error('Failed to fetch skill momentum:', error);
      throw error;
    }
  },

  /**
   * Get skill update activity metrics based on filters.
   * This endpoint responds to filter changes.
   */
  async getSkillUpdateActivity(filters = {}, days = 90) {
    try {
      const params = { days };
      if (filters.subSegment) params.sub_segment_id = filters.subSegment;
      if (filters.project) params.project_id = filters.project;
      if (filters.team) params.team_id = filters.team;
      
      return await httpClient.get('/dashboard/skill-update-activity', params);
    } catch (error) {
      console.error('Failed to fetch skill update activity:', error);
      throw error;
    }
  },

  /**
   * Get data freshness percentage based on filters.
   * This endpoint responds to filter changes.
   * 
   * Data Freshness = % of employees with at least one skill update in the time window.
   * 
   * @param {Object} filters - Dashboard filters { subSegment, project, team }
   * @param {number} days - Time window in days (default: 90)
   * @returns {Promise<{window_days: number, employees_in_scope: number, employees_with_update: number, freshness_percent: number}>}
   */
  async getDataFreshness(filters = {}, days = 90) {
    try {
      const params = { days };
      if (filters.subSegment) params.sub_segment_id = filters.subSegment;
      if (filters.project) params.project_id = filters.project;
      if (filters.team) params.team_id = filters.team;
      
      return await httpClient.get('/dashboard/data-freshness', params);
    } catch (error) {
      console.error('Failed to fetch data freshness:', error);
      throw error;
    }
  },

  /**
   * Get role distribution data for the dashboard section.
   * This endpoint responds to filter changes.
   * 
   * Context resolution:
   * - No sub_segment_id => SEGMENT context (breakdown = sub-segments)
   * - sub_segment_id only => SUB_SEGMENT context (breakdown = projects)
   * - sub_segment_id + project_id => PROJECT context (breakdown = teams)
   * - All provided => TEAM context (single team row)
   * 
   * @param {Object} filters - Dashboard filters { subSegment, project, team }
   * @param {Object} options - Optional settings { segmentId, topN, maxRoles, includeEmpty }
   * @returns {Promise<RoleDistributionResponse>}
   */
  async getRoleDistribution(filters = {}, options = {}) {
    try {
      const {
        segmentId = DEFAULT_DASHBOARD_CONTEXT.SEGMENT_ID,
        topN = 3,
        maxRoles = 10,
        includeEmpty = true
      } = options;

      // Build params based on context level
      const params = {
        segment_id: segmentId,
        top_n: topN,
        max_roles: maxRoles,
        include_empty: includeEmpty
      };

      // Only add filter params if they have values (handles "All ..." selections)
      if (filters.subSegment) {
        params.sub_segment_id = filters.subSegment;
        
        if (filters.project) {
          params.project_id = filters.project;
          
          if (filters.team) {
            params.team_id = filters.team;
          }
        }
      }

      return await httpClient.get('/dashboard/role-distribution', params);
    } catch (error) {
      console.error('Failed to fetch role distribution:', error);
      throw error;
    }
  }
};

export default dashboardApi;
