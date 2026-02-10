/**
 * useRoles Hook
 * 
 * SRP: Handles loading and caching of roles data.
 * Used by Role/Designation autosuggest dropdown.
 */
import { useState, useEffect, useCallback } from 'react';
import { rolesApi } from '../services/api/rolesApi.js';

/**
 * Hook for loading roles for dropdown/autosuggest
 * 
 * @returns {Object} Roles state and methods
 * @returns {Array} return.roles - List of roles with role_id and role_name
 * @returns {boolean} return.loading - Whether roles are being loaded
 * @returns {string|null} return.error - Error message if loading failed
 * @returns {Function} return.refresh - Function to reload roles
 */
export function useRoles() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);  // Start as true to show loading state
  const [error, setError] = useState(null);

  /**
   * Load roles from API
   */
  const loadRoles = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await rolesApi.getRoles();
      console.log('[useRoles] Loaded roles:', data);
      setRoles(data);
    } catch (err) {
      console.error('[useRoles] Failed to load roles:', err);
      setError('Failed to load roles');
      setRoles([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load roles on mount
  useEffect(() => {
    loadRoles();
  }, [loadRoles]);

  /**
   * Refresh roles (can be called manually)
   */
  const refresh = useCallback(() => {
    loadRoles();
  }, [loadRoles]);

  /**
   * Find a role by ID
   * @param {number} roleId 
   * @returns {Object|undefined}
   */
  const getRoleById = useCallback((roleId) => {
    return roles.find(r => r.role_id === roleId);
  }, [roles]);

  /**
   * Find a role by name (case-insensitive exact match)
   * @param {string} roleName 
   * @returns {Object|undefined}
   */
  const getRoleByName = useCallback((roleName) => {
    if (!roleName) return undefined;
    const normalized = roleName.trim().toLowerCase();
    return roles.find(r => r.role_name.toLowerCase() === normalized);
  }, [roles]);

  return {
    roles,
    loading,
    error,
    refresh,
    getRoleById,
    getRoleByName
  };
}

export default useRoles;
