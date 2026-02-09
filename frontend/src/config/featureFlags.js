/**
 * Feature Flags Configuration
 * 
 * Central configuration for toggling features on/off during development.
 * This allows easy control of work-in-progress features.
 * 
 * Usage:
 * - Set flag to `true` to enable the feature
 * - Set flag to `false` to disable the feature
 */

export const FEATURE_FLAGS = {
  /**
   * RBAC Admin Panel
   * Controls visibility of the RBAC (Role-Based Access Control) admin interface
   * - Sidebar menu item
   * - Route accessibility
   * 
   * Set to `true` when ready to release RBAC feature
   */
  SHOW_RBAC_ADMIN: false
};


/* =============================================================================
 * RBAC (Role-Based Access Control) Configuration
 * =============================================================================
 * 
 * IMPORTANT: This is a TEMPORARY implementation using hardcoded roles.
 * Once login/authentication is built, replace this with JWT token-based roles.
 * 
 * SCOPE: RBAC is applied ONLY for Data Management pages for now:
 * - Employees page
 * - (Future: other data management pages)
 * 
 * ROLE-DRIVEN VISIBILITY + PERMISSIONS:
 * ┌─────────────────────┬────────────────────────────────────┬──────────────────────────────┐
 * │ Role                │ Data Visibility                    │ CRUD Permissions             │
 * ├─────────────────────┼────────────────────────────────────┼──────────────────────────────┤
 * │ SUPER_ADMIN         │ Can see ALL data                   │ Full CRUD for ALL data       │
 * │ SEGMENT_HEAD        │ Can see all data in their segment  │ NO CRUD (view only)          │
 * │ SUBSEGMENT_HEAD     │ Can see all data in sub-segment    │ NO CRUD (view only)          │
 * │ PROJECT_MANAGER     │ Can see only their project         │ CRUD for their project only  │
 * │ TEAM_LEAD           │ Can see only their team            │ CRUD for their team only     │
 * │ TEAM_MEMBER         │ Can see their team (view)          │ CRUD for own data ONLY       │
 * └─────────────────────┴────────────────────────────────────┴──────────────────────────────┘
 * 
 * Note for TEAM_MEMBER:
 * - VIEW: Can see all team members' data (team-wide visibility)
 * - CRUD: Can only create/update/delete their OWN employee record
 * 
 * HOW TO REPLACE WITH REAL LOGIN:
 * 1. When JWT authentication is implemented, decode token to get user's role
 * 2. Replace getRbacContext() to read from auth context/token instead of RBAC_CONFIG
 * 3. Populate currentScope from user's profile in the token (segment, project, team, etc.)
 * 4. Remove RBAC_CONFIG.currentRole and RBAC_CONFIG.currentScope hardcoded values
 * 
 * ============================================================================= */

/**
 * Available roles in the system
 */
export const RBAC_ROLES = {
  SUPER_ADMIN: 'SUPER_ADMIN',
  SEGMENT_HEAD: 'SEGMENT_HEAD',
  SUBSEGMENT_HEAD: 'SUBSEGMENT_HEAD',
  PROJECT_MANAGER: 'PROJECT_MANAGER',
  TEAM_LEAD: 'TEAM_LEAD',
  TEAM_MEMBER: 'TEAM_MEMBER'
};

/**
 * Role permissions configuration
 * Defines what each role can do
 */
export const ROLE_PERMISSIONS = {
  [RBAC_ROLES.SUPER_ADMIN]: {
    canView: true,
    canCreate: true,
    canUpdate: true,
    canDelete: true,
    scopeLevel: 'all'
  },
  [RBAC_ROLES.SEGMENT_HEAD]: {
    canView: true,
    canCreate: false,
    canUpdate: false,
    canDelete: false,
    scopeLevel: 'segment'
  },
  [RBAC_ROLES.SUBSEGMENT_HEAD]: {
    canView: true,
    canCreate: false,
    canUpdate: false,
    canDelete: false,
    scopeLevel: 'sub_segment'
  },
  [RBAC_ROLES.PROJECT_MANAGER]: {
    canView: true,
    canCreate: true,
    canUpdate: true,
    canDelete: true,
    scopeLevel: 'project'
  },
  [RBAC_ROLES.TEAM_LEAD]: {
    canView: true,
    canCreate: true,
    canUpdate: true,
    canDelete: true,
    scopeLevel: 'team'
  },
  [RBAC_ROLES.TEAM_MEMBER]: {
    canView: true,
    canCreate: true,  // Only for self
    canUpdate: true,  // Only for self
    canDelete: true,  // Only for self
    scopeLevel: 'team',
    selfOnly: true    // CRUD restricted to own employee record
  }
};

/**
 * RBAC Configuration
 * TEMPORARY: Hardcoded until login is implemented
 * 
 * currentScope: Set these to actual IDs when testing specific role behaviors.
 * Use null for placeholders - backend will handle appropriately.
 */
export const RBAC_CONFIG = {
  // Default role for development/testing
  defaultRole: RBAC_ROLES.SUPER_ADMIN,
  
  // Currently active role (change this to test different roles)
  currentRole: RBAC_ROLES.SUPER_ADMIN,
  
  // Current user's scope context (populated from user profile after login)
  // Set to null for now - will be populated when user logs in
  currentScope: {
    segment_id: null,       // User's segment ID
    sub_segment_id: null,   // User's sub-segment ID  
    project_id: null,       // User's project ID
    team_id: null,          // User's team ID
    employee_id: null       // User's own employee ID (for TEAM_MEMBER self-only CRUD)
  }
};

/**
 * Get the current RBAC context for API calls.
 * This function returns the role and scope to be sent with API requests.
 * 
 * USAGE IN API CALLS:
 * ```javascript
 * const { role, scope, permissions } = getRbacContext();
 * // Pass to httpClient via headers
 * ```
 * 
 * @returns {Object} - { role, scope, permissions }
 */
export function getRbacContext() {
  const role = RBAC_CONFIG.currentRole;
  const scope = RBAC_CONFIG.currentScope;
  const permissions = ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS[RBAC_ROLES.TEAM_MEMBER];
  
  return {
    role,
    scope,
    permissions
  };
}

/**
 * Check if current role has a specific permission
 * 
 * @param {string} action - 'view', 'create', 'update', 'delete'
 * @returns {boolean}
 */
export function hasPermission(action) {
  const { permissions } = getRbacContext();
  
  switch (action) {
    case 'view':
      return permissions.canView;
    case 'create':
      return permissions.canCreate;
    case 'update':
      return permissions.canUpdate;
    case 'delete':
      return permissions.canDelete;
    default:
      return false;
  }
}

/**
 * Check if current role is restricted to self-only CRUD
 * (Used for TEAM_MEMBER role)
 * 
 * @returns {boolean}
 */
export function isSelfOnlyCrud() {
  const { permissions } = getRbacContext();
  return permissions.selfOnly === true;
}
