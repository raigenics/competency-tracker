/**
 * RBAC Role Helper Functions
 * 
 * Pure utility functions for RBAC role and scope type mapping.
 */

/**
 * Maps role codes to their corresponding scope types.
 * This determines what level of access each role operates at.
 */
const ROLE_TO_SCOPE_TYPE_MAP = {
  SUPER_ADMIN: 'GLOBAL',
  SEGMENT_HEAD: 'SEGMENT',
  SUBSEGMENT_HEAD: 'SUB_SEGMENT',
  PROJECT_MANAGER: 'PROJECT',
  TEAM_LEAD: 'TEAM',
  TEAM_MEMBER: 'EMPLOYEE'
};

/**
 * Get the scope type code for a given role code.
 * 
 * @param {string} roleCode - The role code (e.g., 'SUPER_ADMIN', 'PROJECT_MANAGER')
 * @returns {string|null} The corresponding scope type code, or null if not found
 * 
 * @example
 * getRoleScopeType('SUPER_ADMIN') // returns 'GLOBAL'
 * getRoleScopeType('PROJECT_MANAGER') // returns 'PROJECT'
 * getRoleScopeType('UNKNOWN_ROLE') // returns null
 */
export const getRoleScopeType = (roleCode) => {
  if (!roleCode) return null;
  return ROLE_TO_SCOPE_TYPE_MAP[roleCode] || null;
};

/**
 * Check if a scope type requires a specific scope value selection.
 * GLOBAL scope does not require a scope value.
 * 
 * @param {string} scopeTypeCode - The scope type code (e.g., 'GLOBAL', 'PROJECT')
 * @returns {boolean} True if scope value is required, false otherwise
 * 
 * @example
 * requiresScopeValue('GLOBAL') // returns false
 * requiresScopeValue('PROJECT') // returns true
 */
export const requiresScopeValue = (scopeTypeCode) => {
  return scopeTypeCode !== 'GLOBAL';
};

export default {
  getRoleScopeType,
  requiresScopeValue
};
