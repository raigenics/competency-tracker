import httpClient from './httpClient.js';

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
   */
  async getSkillDistribution(filters = {}) {
    try {
      const params = { limit: filters.team ? 5 : 10 };
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
  }
};

export default dashboardApi;
