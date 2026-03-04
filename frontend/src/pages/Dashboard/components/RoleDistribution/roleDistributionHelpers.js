/**
 * Helper functions for RoleDistribution component.
 * Extracted for react-refresh compatibility (SRP-friendly).
 */

/** Maximum roles to show before needing expand */
export const VISIBLE_LIMIT = 3;

/**
 * Get top N roles sorted by count descending.
 * @param {Array} roleBreakdown - Array of {role_name, employee_count}
 * @param {number} limit - Max roles to return (default: VISIBLE_LIMIT)
 * @returns {Array} Top roles
 */
export const getTopRoles = (roleBreakdown, limit = VISIBLE_LIMIT) => {
  if (!roleBreakdown || !Array.isArray(roleBreakdown)) return [];
  return [...roleBreakdown]
    .sort((a, b) => (b.employee_count || 0) - (a.employee_count || 0))
    .slice(0, limit);
};

/**
 * Get roles beyond the visible limit.
 * @param {Array} roleBreakdown - Array of {role_name, employee_count}
 * @param {number} limit - Visible limit (default: VISIBLE_LIMIT)
 * @returns {Array} Hidden roles
 */
export const getHiddenRoles = (roleBreakdown, limit = VISIBLE_LIMIT) => {
  if (!roleBreakdown || !Array.isArray(roleBreakdown)) return [];
  return [...roleBreakdown]
    .sort((a, b) => (b.employee_count || 0) - (a.employee_count || 0))
    .slice(limit);
};

/**
 * Check if the role breakdown has any data (at least one role with count > 0).
 * @param {Array} roleBreakdown - Array of {role_name, employee_count}
 * @returns {boolean} True if has role data
 */
export const hasRoleData = (roleBreakdown) => {
  if (!roleBreakdown || !Array.isArray(roleBreakdown)) return false;
  return roleBreakdown.some((role) => (role.employee_count || 0) > 0);
};

/**
 * Determine if expand control should be shown.
 * Only show expand when there are more than VISIBLE_LIMIT distinct roles.
 * @param {Array} roleBreakdown - Array of {role_name, employee_count}
 * @returns {boolean} True if expand should be shown
 */
export const shouldShowExpand = (roleBreakdown) => {
  if (!roleBreakdown || !Array.isArray(roleBreakdown)) return false;
  return roleBreakdown.length > VISIBLE_LIMIT;
};
