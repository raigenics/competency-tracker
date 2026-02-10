/**
 * RBAC UI Permissions Helper
 * 
 * Provides utility functions to determine UI visibility based on role permissions.
 * This is UI gating only - backend enforcement is handled separately.
 * 
 * NOTE: currentRole is read from featureFlags.js as a static value until login is implemented.
 */

import { RBAC_CONFIG, RBAC_ROLES, ROLE_PERMISSIONS } from '../config/featureFlags.js';

/**
 * Get permissions for a specific role
 * @param {string} role - Role from RBAC_ROLES
 * @returns {Object} Permission object with canView, canCreate, canUpdate, canDelete, scopeLevel, selfOnly
 */
export function getPermissionsForRole(role) {
  return ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS[RBAC_ROLES.TEAM_MEMBER];
}

/**
 * Get the current role from config
 * @returns {string} Current role
 */
export function getCurrentRole() {
  return RBAC_CONFIG.currentRole;
}

/**
 * Get the current user's scope context
 * @returns {Object} Scope context with segment_id, sub_segment_id, project_id, team_id, employee_id
 */
export function getCurrentScope() {
  return RBAC_CONFIG.currentScope;
}

/**
 * Check if the current role can create employees
 * 
 * For TEAM_MEMBER with selfOnly=true:
 * - Only allowed to create own record
 * - Since we can't determine "self" without login, hide Add button for TEAM_MEMBER
 * 
 * @param {string} [role] - Role to check (defaults to current role)
 * @returns {boolean} Whether the Add Employee button should be visible
 */
export function canShowAddEmployee(role = getCurrentRole()) {
  const permissions = getPermissionsForRole(role);
  
  if (!permissions.canCreate) {
    return false;
  }
  
  // For TEAM_MEMBER, selfOnly applies
  // Without login, we can't determine if they already have an employee record
  // TODO: When login is implemented, check if currentScope.employee_id exists
  //       If employee_id exists, they already have a record - hide Add
  //       If employee_id is null, they can create their own record - show Add
  if (permissions.selfOnly) {
    const scope = getCurrentScope();
    // If we don't have employee_id info, hide Add button for safety
    // This prevents TEAM_MEMBER from creating multiple records
    if (!scope.employee_id) {
      return false;
    }
    // If employee_id exists, they already have a record - can't create another
    return false;
  }
  
  return true;
}

/**
 * Determine which actions should be shown for an employee row
 * 
 * @param {Object} options
 * @param {string} [options.role] - Role to check (defaults to current role)
 * @param {Object} [options.employee] - Employee row data (for future row-level checks)
 * @param {number|null} [options.currentUserEmployeeId] - Current user's employee ID (for selfOnly checks)
 * @returns {Object} { canView, canEdit, canDelete }
 */
export function getRowActions({
  role = getCurrentRole(),
  employee = null,
  currentUserEmployeeId = null
} = {}) {
  const permissions = getPermissionsForRole(role);
  const scope = getCurrentScope();
  
  // If no employee_id passed, try to get from scope
  const userEmployeeId = currentUserEmployeeId ?? scope.employee_id;
  
  const result = {
    canView: permissions.canView,
    canEdit: false,
    canDelete: false
  };
  
  // For view-only roles (SEGMENT_HEAD, SUBSEGMENT_HEAD), only View is allowed
  if (!permissions.canUpdate && !permissions.canDelete) {
    return result;
  }
  
  // For roles with selfOnly (TEAM_MEMBER), check if this is their own row
  if (permissions.selfOnly) {
    if (employee && userEmployeeId) {
      const isSelf = employee.employee_id === userEmployeeId || employee.id === userEmployeeId;
      result.canEdit = isSelf && permissions.canUpdate;
      result.canDelete = isSelf && permissions.canDelete;
    }
    // TODO: When login is implemented and userEmployeeId is available,
    //       row-level selfOnly check will work automatically
    return result;
  }
  
  // For roles with full scope-level permissions (SUPER_ADMIN, PROJECT_MANAGER, TEAM_LEAD)
  // Row-level scope checking would require employee.team_id, project_id, etc.
  // Currently the list API doesn't return these IDs, only display strings.
  // TODO: Add scope-level row filtering when API returns IDs
  //       For now, use role-level gating only
  result.canEdit = permissions.canUpdate;
  result.canDelete = permissions.canDelete;
  
  return result;
}

/**
 * Check if current role is a view-only role
 * @param {string} [role] - Role to check (defaults to current role)
 * @returns {boolean}
 */
export function isViewOnlyRole(role = getCurrentRole()) {
  const permissions = getPermissionsForRole(role);
  return permissions.canView && !permissions.canCreate && !permissions.canUpdate && !permissions.canDelete;
}

/**
 * Export all RBAC constants for convenience
 */
export { RBAC_ROLES, ROLE_PERMISSIONS, RBAC_CONFIG };
