// Dropdown API service for dashboard filters
import { API_BASE_URL } from '../../config/apiConfig.js';

export const dropdownApi = {
  // Get all sub-segments
  async getSubSegments() {
    try {
      const response = await fetch(`${API_BASE_URL}/dropdown/sub-segments`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.sub_segments;
    } catch (error) {
      console.error('Failed to fetch sub-segments:', error);
      throw error;
    }
  },

  // Get projects for a specific sub-segment
  async getProjects(subSegmentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/dropdown/projects?sub_segment_id=${subSegmentId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.projects;
    } catch (error) {
      console.error(`Failed to fetch projects for sub-segment ${subSegmentId}:`, error);
      throw error;
    }
  },

  // Get teams for a specific project
  async getTeams(projectId) {
    try {
      const response = await fetch(`${API_BASE_URL}/dropdown/teams?project_id=${projectId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.teams;
    } catch (error) {
      console.error(`Failed to fetch teams for project ${projectId}:`, error);
      throw error;
    }
  }
};
