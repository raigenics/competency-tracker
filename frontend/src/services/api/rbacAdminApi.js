import httpClient from './httpClient.js';

/**
 * RBAC Admin API service for Super Admin Panel.
 * Handles user management, role assignments, and access control operations.
 */
export const rbacAdminApi = {
  // ========================================================================
  // USER MANAGEMENT
  // ========================================================================

  /**
   * List all users with optional filters and pagination.
   * @param {Object} params - Query parameters
   * @param {string} params.search - Search in name or email
   * @param {number} params.role_id - Filter by role ID
   * @param {number} params.scope_type_id - Filter by scope type ID
   * @param {string} params.status - Filter by status ('active' or 'inactive')
   * @param {number} params.skip - Number of records to skip (default: 0)
   * @param {number} params.limit - Maximum records to return (default: 100)
   * @returns {Promise<Array>} Array of user objects with role assignments
   */
  async listUsers(params = {}) {
    try {
      return await httpClient.get('/rbac-admin/users', params);
    } catch (error) {
      console.error('Failed to list users:', error);
      throw error;
    }
  },

  /**
   * Create a new user account.
   * @param {Object} userData - User creation data
   * @param {string} userData.full_name - User's full name
   * @param {string} userData.email - User's email (must be unique)
   * @param {string} userData.password - Initial password (min 8 characters)
   * @param {string} userData.status - Account status ('active' or 'inactive')
   * @param {number} userData.link_to_employee_id - Optional employee ID to link
   * @returns {Promise<Object>} Created user object
   */
  async createUser(userData) {
    try {
      return await httpClient.post('/rbac-admin/users', userData);
    } catch (error) {
      console.error('Failed to create user:', error);
      throw error;
    }
  },

  /**
   * Get detailed information about a specific user.
   * @param {number} userId - User ID  
   * @returns {Promise<Object>} User details with all role assignments
   */
  async getUserDetail(userId) {
    try {
      return await httpClient.get(`/rbac-admin/users/${userId}`);
    } catch (error) {
      console.error('Failed to get user detail:', error);
      throw error;
    }
  },

  // ========================================================================
  // ROLE ASSIGNMENT MANAGEMENT
  // ========================================================================

  /**
   * Create a new role assignment for a user.
   * @param {number} userId - User ID
   * @param {Object} assignmentData - Assignment data
   * @param {number} assignmentData.role_id - Role ID to assign
   * @param {number} assignmentData.scope_type_id - Scope type ID
   * @param {number} assignmentData.scope_id - Scope entity ID (null for GLOBAL)
   * @returns {Promise<Object>} Created assignment object
   */
  async createRoleAssignment(userId, assignmentData) {
    try {
      return await httpClient.post(`/rbac-admin/users/${userId}/assignments`, {
        user_id: userId,
        ...assignmentData
      });
    } catch (error) {
      console.error('Failed to create role assignment:', error);
      throw error;
    }
  },

  /**
   * Get all role assignments for a user.
   * @param {number} userId - User ID
   * @returns {Promise<Array>} Array of assignment objects
   */
  async getUserAssignments(userId) {
    try {
      return await httpClient.get(`/rbac-admin/users/${userId}/assignments`);
    } catch (error) {
      console.error('Failed to get user assignments:', error);
      throw error;
    }
  },

  /**
   * Revoke (soft delete) a role assignment.
   * @param {number} userId - User ID
   * @param {number} assignmentId - Assignment ID to revoke
   * @param {string} reason - Optional reason for revocation
   * @returns {Promise<void>}
   */
  async revokeRoleAssignment(userId, assignmentId, reason = null) {
    try {
      const body = reason ? { reason } : {};
      return await httpClient.delete(`/rbac-admin/users/${userId}/assignments/${assignmentId}`, body);
    } catch (error) {
      console.error('Failed to revoke role assignment:', error);
      throw error;
    }
  },

  // ========================================================================
  // LOOKUP OPERATIONS
  // ========================================================================

  /**
   * Get all available roles for dropdown selection.
   * @returns {Promise<Array>} Array of role objects
   */
  async getRoles() {
    try {
      return await httpClient.get('/rbac-admin/lookups/roles');
    } catch (error) {
      console.error('Failed to get roles:', error);
      throw error;
    }
  },

  /**
   * Get all available scope types for dropdown selection.
   * @returns {Promise<Array>} Array of scope type objects
   */
  async getScopeTypes() {
    try {
      return await httpClient.get('/rbac-admin/lookups/scope-types');
    } catch (error) {
      console.error('Failed to get scope types:', error);
      throw error;
    }
  },

  /**
   * Get all available values for a specific scope type.
   * @param {string} scopeTypeCode - Scope type code (e.g., 'SUB_SEGMENT', 'PROJECT', 'TEAM', 'EMPLOYEE', 'GLOBAL')
   * @returns {Promise<Array>} Array of scope value objects (empty array for GLOBAL/SEGMENT)
   */
  async getScopeValues(scopeTypeCode) {
    try {
      return await httpClient.get(`/rbac-admin/lookups/scope-values/${scopeTypeCode}`);
    } catch (error) {
      console.error('Failed to get scope values:', error);
      throw error;
    }
  },

  /**
   * Search for employees (for linking to users).
   * @param {string} search - Search term for employee name or ZID
   * @returns {Promise<Array>} Array of employee objects
   */
  async searchEmployees(search = '') {
    try {
      return await httpClient.get('/rbac-admin/lookups/employees', { search });
    } catch (error) {
      console.error('Failed to search employees:', error);
      throw error;
    }
  }
};

export default rbacAdminApi;
