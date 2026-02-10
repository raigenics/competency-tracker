/**
 * Roles API Service
 * 
 * SRP: Handles all role-related API calls.
 * Read-only operations for fetching roles.
 */
import httpClient from './httpClient.js';

/**
 * @typedef {Object} Role
 * @property {number} role_id - Role ID
 * @property {string} role_name - Role name
 */

export const rolesApi = {
  /**
   * Get all roles for dropdown/autosuggest
   * @returns {Promise<Role[]>} List of roles
   */
  async getRoles() {
    try {
      return await httpClient.get('/roles/');
    } catch (error) {
      console.error('Failed to fetch roles:', error);
      throw error;
    }
  },

  /**
   * Get a single role by ID
   * @param {number} roleId - Role ID
   * @returns {Promise<Role>} Role data
   */
  async getRole(roleId) {
    try {
      return await httpClient.get(`/roles/${roleId}`);
    } catch (error) {
      console.error(`Failed to fetch role ${roleId}:`, error);
      throw error;
    }
  }
};

export default rolesApi;
