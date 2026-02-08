/**
 * Capability Finder API service for fetching typeahead/autocomplete data.
 * Provides skills and roles data for the Advanced Query page.
 */
import httpClient from './httpClient.js';
import { API_BASE_URL } from '../../config/apiConfig.js';

export const capabilityFinderApi = {
  /**
   * Get all distinct skill names for typeahead.
   * @returns {Promise<string[]>} Array of skill names sorted A-Z
   */
  async getAllSkills() {
    try {
      const response = await httpClient.get('/capability-finder/skills');
      return response.skills || [];
    } catch (error) {
      console.error('Failed to fetch skills:', error);
      throw error;
    }
  },

  /**
   * Get enhanced skill suggestions with employee availability metadata.
   * @param {string} query - Optional search query to filter skills
   * @returns {Promise<Array>} Array of skill suggestions with metadata
   */
  async getSkillSuggestions(query = '') {
    try {
      const params = query ? `?query=${encodeURIComponent(query)}` : '';
      const response = await httpClient.get(`/capability-finder/skills/suggestions${params}`);
      return response.suggestions || [];
    } catch (error) {
      console.error('Failed to fetch skill suggestions:', error);
      throw error;
    }
  },

  /**
   * Get all distinct role names for typeahead.
   * @returns {Promise<string[]>} Array of role names sorted A-Z
   */
  async getAllRoles() {
    try {
      const response = await httpClient.get('/capability-finder/roles');
      return response.roles || [];
    } catch (error) {
      console.error('Failed to fetch roles:', error);
      throw error;
    }
  },

  /**
   * Search for employees matching specified criteria.
   * @param {Object} payload - Search parameters
   * @param {string[]} payload.skills - Required skill names (AND logic)
   * @param {number|null} payload.sub_segment_id - Sub-segment ID filter
   * @param {number|null} payload.team_id - Team ID filter
   * @param {string} payload.role - Role name filter
   * @param {number} payload.min_proficiency - Minimum proficiency level (0-5)
   * @param {number} payload.min_experience_years - Minimum years of experience
   * @returns {Promise<Object>} Search results with count and employee list
   */
  async searchMatchingTalent(payload) {
    try {
      const response = await httpClient.post('/capability-finder/search', payload);
      return response;
    } catch (error) {
      console.error('Failed to search matching talent:', error);
      throw error;
    }
  },
  /**
   * Export matching talent to Excel file.
   * @param {Object} payload - Export parameters
   * @param {string} payload.mode - "all" or "selected"
   * @param {Object} payload.filters - Search filters (same as searchMatchingTalent)
   * @param {number[]} payload.selected_employee_ids - Array of employee IDs (required if mode="selected")
   * @returns {Promise<Blob>} Excel file as blob
   */
  async exportMatchingTalent(payload) {
    try {
      const response = await fetch(`${API_BASE_URL}/capability-finder/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Export failed' }));
        throw new Error(errorData.detail || `Export failed with status ${response.status}`);
      }

      const blob = await response.blob();
      return blob;
    } catch (error) {
      console.error('Failed to export matching talent:', error);
      throw error;
    }
  }
};

export default capabilityFinderApi;
