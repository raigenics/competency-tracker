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
