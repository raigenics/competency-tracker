/**
 * Roles API Service
 * 
 * SRP: Handles all role-related API calls.
 * Supports CRUD operations: Create, Read, Update, Delete (soft).
 */
import httpClient from './httpClient.js';

/**
 * @typedef {Object} Role
 * @property {number} role_id - Role ID
 * @property {string} role_name - Role name
 * @property {string|null} role_alias - Role alias (comma-separated)
 * @property {string|null} role_description - Role description
 */

/**
 * @typedef {Object} RoleCreate
 * @property {string} role_name - Role name
 * @property {string} [role_alias] - Optional role alias (comma-separated)
 * @property {string} [role_description] - Optional role description
 */

/**
 * @typedef {Object} BulkDeleteResponse
 * @property {number} deleted_count - Number of roles deleted
 */

/**
 * @typedef {Object} ImportFailure
 * @property {number} row_number - Excel row number
 * @property {string} role_name - Role name from the row
 * @property {string} reason - Reason for failure
 */

/**
 * @typedef {Object} ImportRolesResponse
 * @property {number} total_rows - Total data rows in Excel
 * @property {number} success_count - Number imported successfully
 * @property {number} failure_count - Number that failed
 * @property {ImportFailure[]} failures - Details of failed rows
 */

export const rolesApi = {
  /**
   * Get all roles for dropdown/table
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
  },

  /**
   * Create a new role
   * @param {RoleCreate} roleData - Role name and optional description
   * @returns {Promise<Role>} Created role
   */
  async createRole(roleData) {
    try {
      return await httpClient.post('/roles/', roleData);
    } catch (error) {
      console.error('Failed to create role:', error);
      throw error;
    }
  },

  /**
   * Update an existing role
   * @param {number} roleId - Role ID
   * @param {RoleCreate} roleData - Updated role name and optional description
   * @returns {Promise<Role>} Updated role
   */
  async updateRole(roleId, roleData) {
    try {
      return await httpClient.put(`/roles/${roleId}`, roleData);
    } catch (error) {
      console.error(`Failed to update role ${roleId}:`, error);
      throw error;
    }
  },

  /**
   * Soft delete a role by ID
   * @param {number} roleId - Role ID
   * @returns {Promise<void>}
   */
  async deleteRole(roleId) {
    try {
      return await httpClient.delete(`/roles/${roleId}`);
    } catch (error) {
      console.error(`Failed to delete role ${roleId}:`, error);
      throw error;
    }
  },

  /**
   * Soft delete multiple roles at once
   * @param {number[]} roleIds - List of role IDs to delete
   * @returns {Promise<BulkDeleteResponse>} Number of roles deleted
   */
  async deleteRolesBulk(roleIds) {
    try {
      return await httpClient.delete('/roles/', { role_ids: roleIds });
    } catch (error) {
      console.error('Failed to bulk delete roles:', error);
      throw error;
    }
  },

  /**
   * Import roles from Excel file.
   * 
   * @param {File} file - Excel file (.xlsx or .xls) with columns: Role Name, Alias, Role Description
   * @returns {Promise<ImportRolesResponse>} Import result with counts and failures
   * @throws {Error} 400 if file invalid, 500 on server error
   */
  async importRoles(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      return await httpClient.post('/roles/import', formData);
    } catch (error) {
      console.error('Failed to import roles:', error);
      throw error;
    }
  }
};

export default rolesApi;
