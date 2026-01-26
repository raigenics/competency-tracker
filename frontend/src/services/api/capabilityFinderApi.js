/**
 * Capability Finder API service for fetching typeahead/autocomplete data.
 * Provides skills and roles data for the Advanced Query page.
 */
import httpClient from './httpClient.js';

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
  }
};

export default capabilityFinderApi;
