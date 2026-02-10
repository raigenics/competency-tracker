import httpClient from './httpClient.js';

/**
 * Employee validation API service
 * Handles uniqueness checks for ZID and Email fields
 */
export const employeeValidationApi = {
  /**
   * Validate that ZID and/or email are unique
   * @param {Object} params
   * @param {string} [params.zid] - ZID to check
   * @param {string} [params.email] - Email to check
   * @param {number} [params.excludeEmployeeId] - Employee ID to exclude (for edit mode)
   * @returns {Promise<{zid_exists: boolean, email_exists: boolean}>}
   */
  async validateUnique({ zid, email, excludeEmployeeId } = {}) {
    try {
      const queryParams = {};
      
      if (zid) {
        queryParams.zid = zid;
      }
      if (email) {
        queryParams.email = email;
      }
      if (excludeEmployeeId) {
        queryParams.exclude_employee_id = excludeEmployeeId;
      }

      return await httpClient.get('/employees/validate-unique', queryParams);
    } catch (error) {
      console.error('Failed to validate employee uniqueness:', error);
      throw error;
    }
  }
};

export default employeeValidationApi;
