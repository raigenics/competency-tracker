/**
 * Sidebar Navigation Component
 * ============================
 * Exact replication of HTML wireframe structure.
 * Uses semantic tags: <aside>, <nav>, <details>, <summary>, <a>
 * 
 * RBAC Visibility:
 * - INSIGHTS: viewer, manager, admin, superadmin
 * - PEOPLE: manager, admin, superadmin
 * - GOVERNANCE: admin, superadmin (collapsible)
 */

import { NavLink, useLocation } from 'react-router-dom';
import { RBAC_CONFIG, RBAC_ROLES } from '../config/featureFlags';
import '../styles/sidebar.css';

/**
 * Map internal RBAC_ROLES to sidebar role strings
 * @returns {string} - 'viewer' | 'manager' | 'admin' | 'superadmin'
 */
function getSidebarRole() {
  const role = RBAC_CONFIG.currentRole;
  switch (role) {
    case RBAC_ROLES.SUPER_ADMIN:
      return 'superadmin';
    case RBAC_ROLES.SEGMENT_HEAD:
    case RBAC_ROLES.SUBSEGMENT_HEAD:
      return 'admin';
    case RBAC_ROLES.PROJECT_MANAGER:
    case RBAC_ROLES.TEAM_LEAD:
      return 'manager';
    case RBAC_ROLES.TEAM_MEMBER:
    default:
      return 'viewer';
  }
}

/**
 * Check if current role is allowed for a section
 * @param {string} allowedRoles - Comma-separated role list from data-roles
 * @returns {boolean}
 */
function isRoleAllowed(allowedRoles) {
  const currentRole = getSidebarRole();
  const allowed = allowedRoles.split(',').map(r => r.trim());
  return allowed.includes(currentRole);
}

const Sidebar = () => {
  const location = useLocation();

  /**
   * Check if a path is currently active
   * Supports nested routes (e.g., /governance/skill-library/xyz)
   */
  const isActive = (path) => {
    if (path === '/dashboard') {
      // Dashboard is also active for root path
      return location.pathname === '/dashboard' || location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  /**
   * Get className for nav-item based on active state
   */
  const getNavItemClass = (path) => {
    return `nav-item${isActive(path) ? ' is-active' : ''}`;
  };

  /**
   * Get aria-current attribute for accessibility
   */
  const getAriaCurrent = (path) => {
    return isActive(path) ? 'page' : undefined;
  };

  // Check section visibility based on current role
  const showInsights = isRoleAllowed('viewer,manager,admin,superadmin');
  const showPeople = isRoleAllowed('manager,admin,superadmin');
  const showGovernance = isRoleAllowed('admin,superadmin');

  return (
    <aside className="sidebar" aria-label="Primary navigation">
      {/* Brand */}
      <div className="brand">
        <div className="brand__title">CompetencyIQ</div>
        <div className="brand__subtitle">Skill Intelligence Platform</div>
      </div>

      <nav className="nav">
        {/* INSIGHTS (visible to all authenticated users) */}
        {showInsights && (
          <div className="section" data-roles="viewer,manager,admin,superadmin">
            <div className="section__label">Insights</div>
            <div className="nav-list">
              <NavLink 
                className={getNavItemClass('/dashboard')} 
                to="/dashboard"
                aria-current={getAriaCurrent('/dashboard')}
              >
                <span className="nav-item__icon">📊</span>
                <span className="nav-item__text">Dashboard</span>
              </NavLink>
              <NavLink 
                className={getNavItemClass('/skill-coverage')} 
                to="/skill-coverage"
                aria-current={getAriaCurrent('/skill-coverage')}
              >
                <span className="nav-item__icon">🗺️</span>
                <span className="nav-item__text">Skill Coverage</span>
              </NavLink>
              <NavLink 
                className={getNavItemClass('/talent-finder')} 
                to="/talent-finder"
                aria-current={getAriaCurrent('/talent-finder')}
              >
                <span className="nav-item__icon">🔎</span>
                <span className="nav-item__text">Talent Finder</span>
              </NavLink>
            </div>
          </div>
        )}

        {/* PEOPLE (manager+) */}
        {showPeople && (
          <div className="section" data-roles="manager,admin,superadmin">
            <div className="section__label">People</div>
            <div className="nav-list">
              <NavLink 
                className={getNavItemClass('/profile')} 
                to="/profile"
                aria-current={getAriaCurrent('/profile')}
              >
                <span className="nav-item__icon">👥</span>
                <span className="nav-item__text">Employee Directory</span>
              </NavLink>
            </div>
          </div>
        )}

        {/* Divider */}
        {showGovernance && (
          <div className="divider" role="separator" aria-hidden="true"></div>
        )}

        {/* GOVERNANCE (admin only) */}
        {showGovernance && (
          <details 
            className="section__collapsible" 
            open 
            data-roles="admin,superadmin"
          >
            <summary>
              <span>Governance</span>
              <span className="chev">⌄</span>
            </summary>
            <div className="nav-list">
              <NavLink 
                className={getNavItemClass('/employees')} 
                to="/employees"
                aria-current={getAriaCurrent('/employees')}
              >
                <span className="nav-item__icon">✏️</span>
                <span className="nav-item__text">Employee Management</span>
              </NavLink>
              <NavLink 
                className={getNavItemClass('/system/import')} 
                to="/system/import"
                aria-current={getAriaCurrent('/system/import')}
              >
                <span className="nav-item__icon">⬆️</span>
                <span className="nav-item__text">Import Data</span>
              </NavLink>
              <NavLink 
                className={getNavItemClass('/governance/skill-library')} 
                to="/governance/skill-library"
                aria-current={getAriaCurrent('/governance/skill-library')}
              >
                <span className="nav-item__icon">📚</span>
                <span className="nav-item__text">Skill Library</span>
              </NavLink>
              <NavLink 
                className={getNavItemClass('/governance/org-structure')} 
                to="/governance/org-structure"
                aria-current={getAriaCurrent('/governance/org-structure')}
              >
                <span className="nav-item__icon">🏢</span>
                <span className="nav-item__text">Organization Structure</span>
              </NavLink>
              <NavLink 
                className={getNavItemClass('/governance/role-catalog')} 
                to="/governance/role-catalog"
                aria-current={getAriaCurrent('/governance/role-catalog')}
              >
                <span className="nav-item__icon">🧩</span>
                <span className="nav-item__text">Role Catalog</span>
              </NavLink>
            </div>
          </details>
        )}
      </nav>
    </aside>
  );
};

export default Sidebar;
