import { useState, useEffect } from 'react';
import { Search, Plus, Settings, Loader2 } from 'lucide-react';
import { rbacAdminApi } from '../../../services/api/rbacAdminApi.js';
import AddUserModal from './AddUserModal.jsx';
import ManageAccessModal from './ManageAccessModal.jsx';
import RoleBadge from './RoleBadge.jsx';

/**
 * User Management Tab Component
 * 
 * Displays filterable table of users with their role assignments.
 * Allows creating new users and managing their access.
 */
const UserManagementTab = () => {
  // State
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [scopeTypeFilter, setScopeTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Modal state
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [manageAccessUser, setManageAccessUser] = useState(null);
  
  // Lookup data for filters
  const [roles, setRoles] = useState([]);
  const [scopeTypes, setScopeTypes] = useState([]);

  // Load users on mount and when filters change
  useEffect(() => {
    loadUsers();
  }, [searchTerm, roleFilter, scopeTypeFilter, statusFilter]);

  // Load lookup data on mount
  useEffect(() => {
    loadLookupData();
  }, []);

  /**
   * Load users from API with current filters
   */
  const loadUsers = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (roleFilter) params.role_id = roleFilter;
      if (scopeTypeFilter) params.scope_type_id = scopeTypeFilter;
      if (statusFilter) params.status = statusFilter;

      const data = await rbacAdminApi.listUsers(params);
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
      alert('Failed to load users. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load roles and scope types for filter dropdowns
   */
  const loadLookupData = async () => {
    try {
      const [rolesData, scopeTypesData] = await Promise.all([
        rbacAdminApi.getRoles(),
        rbacAdminApi.getScopeTypes()
      ]);
      setRoles(rolesData);
      setScopeTypes(scopeTypesData);
    } catch (error) {
      console.error('Failed to load lookup data:', error);
    }
  };

  /**
   * Handle user created successfully
   */
  const handleUserCreated = (newUser) => {
    setShowAddUserModal(false);
    
    // Show success message and open manage access modal
    alert(`User "${newUser.full_name}" created successfully!\n\nNow assign roles and scopes to this user.`);
    
    // Open manage access modal for the new user
    setManageAccessUser({
      user_id: newUser.user_id,
      full_name: newUser.full_name,
      email: newUser.email
    });
    
    // Reload user list
    loadUsers();
  };

  /**
   * Handle access updated successfully
   */
  const handleAccessUpdated = () => {
    setManageAccessUser(null);
    loadUsers(); // Reload to show updated role assignments
  };

  /**
   * Clear all filters
   */
  const clearFilters = () => {
    setSearchTerm('');
    setRoleFilter('');
    setScopeTypeFilter('');
    setStatusFilter('');
  };

  const hasActiveFilters = searchTerm || roleFilter || scopeTypeFilter || statusFilter;

  return (
    <div>
      {/* Controls: Search, Filters, Add User Button */}
      <div className="mb-6 space-y-4">
        {/* Search and Add User Button Row */}
        <div className="flex gap-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Add User Button */}
          <button
            onClick={() => setShowAddUserModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
          >
            <Plus className="w-5 h-5" />
            Add User
          </button>
        </div>

        {/* Filters Row */}
        <div className="flex gap-4 items-end">
          {/* Role Filter */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Role
            </label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Roles</option>
              {roles.map((role) => (
                <option key={role.role_id} value={role.role_id}>
                  {role.role_name}
                </option>
              ))}
            </select>
          </div>

          {/* Scope Type Filter */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Scope Type
            </label>
            <select
              value={scopeTypeFilter}
              onChange={(e) => setScopeTypeFilter(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Scope Types</option>
              {scopeTypes.map((scopeType) => (
                <option key={scopeType.scope_type_id} value={scopeType.scope_type_id}>
                  {scopeType.scope_name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {/* Clear Filters Button */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg font-medium mb-2">No users found</p>
          <p className="text-sm">
            {hasActiveFilters
              ? 'Try adjusting your filters'
              : 'Click "Add User" to create your first user'}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="rbac-table">
            <thead>
              <tr>
                <th>User ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role Assignments</th>
                <th>Linked Employee</th>
                <th>Status</th>
                <th style={{textAlign: 'right'}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.user_id}>
                  <td>{user.user_id}</td>
                  <td><strong>{user.full_name}</strong></td>
                  <td>{user.email}</td>
                  <td>
                    {user.role_assignments.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {user.role_assignments.map((assignment, idx) => (
                          <RoleBadge key={idx} assignment={assignment} />
                        ))}
                      </div>
                    ) : (
                      <span style={{color: '#9ca3af', fontStyle: 'italic'}}>No roles assigned</span>
                    )}
                  </td>
                  <td>
                    {user.linked_employee_zid ? (
                      <div>
                        <div style={{fontWeight: '500'}}>{user.linked_employee_name}</div>
                        <div style={{fontSize: '0.75rem', color: '#6b7280'}}>{user.linked_employee_zid}</div>
                      </div>
                    ) : (
                      <span style={{color: '#9ca3af', fontStyle: 'italic'}}>None</span>
                    )}
                  </td>
                  <td>
                    <span
                      className={`rbac-badge-status ${
                        user.status === 'active' ? 'active' : 'inactive'
                      }`}
                    >
                      {user.status}
                    </span>
                  </td>
                  <td style={{textAlign: 'right'}}>
                    <button
                      onClick={() => setManageAccessUser(user)}
                      className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-900"
                    >
                      <Settings className="w-4 h-4" />
                      Manage Access
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Result Count */}
      {!loading && users.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          Showing {users.length} user{users.length !== 1 ? 's' : ''}
          {hasActiveFilters && ' (filtered)'}
        </div>
      )}

      {/* Modals */}
      {showAddUserModal && (
        <AddUserModal
          onClose={() => setShowAddUserModal(false)}
          onUserCreated={handleUserCreated}
        />
      )}

      {manageAccessUser && (
        <ManageAccessModal
          user={manageAccessUser}
          onClose={() => setManageAccessUser(null)}
          onAccessUpdated={handleAccessUpdated}
        />
      )}
    </div>
  );
};

export default UserManagementTab;
