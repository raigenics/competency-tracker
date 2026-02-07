import { useState, useEffect } from 'react';
import { X, Loader2, Plus, Trash2 } from 'lucide-react';
import { rbacAdminApi } from '../../../services/api/rbacAdminApi.js';
import { getRoleScopeType, requiresScopeValue } from '../../../utils/rbacRoleHelpers.js';
import RoleBadge from './RoleBadge.jsx';

/**
 * Manage Access Modal Component
 * 
 * Modal for managing user's role assignments.
 * Shows current assignments and allows adding/revoking roles.
 */
const ManageAccessModal = ({ user, onClose, onAccessUpdated }) => {
  // State
  const [loading, setLoading] = useState(true);
  const [userDetail, setUserDetail] = useState(null);
  const [showNewRoleForm, setShowNewRoleForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Lookup data
  const [roles, setRoles] = useState([]);
  const [scopeTypes, setScopeTypes] = useState([]);
  const [scopeValues, setScopeValues] = useState([]);
  const [loadingScopeValues, setLoadingScopeValues] = useState(false);

  // New role form state
  const [newRoleForm, setNewRoleForm] = useState({
    role_id: '',
    role_code: '',
    scope_type_code: '',
    scope_type_id: '',
    scope_id: ''
  });

  // Load user detail and lookup data on mount
  useEffect(() => {
    loadData();
  }, [user.user_id]);

  /**
   * Load user detail and lookup data
   */
  const loadData = async () => {
    setLoading(true);
    try {
      const [detail, rolesData, scopeTypesData] = await Promise.all([
        rbacAdminApi.getUserDetail(user.user_id),
        rbacAdminApi.getRoles(),
        rbacAdminApi.getScopeTypes()
      ]);

      setUserDetail(detail);
      setRoles(rolesData);
      setScopeTypes(scopeTypesData);
    } catch (error) {
      console.error('Failed to load data:', error);
      alert('Failed to load user details');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle role selection - auto-fill scope type
   */
  const handleRoleChange = async (roleId) => {
    // Reset form state
    setNewRoleForm(prev => ({ 
      ...prev, 
      role_id: roleId, 
      role_code: '',
      scope_type_code: '',
      scope_type_id: '', 
      scope_id: '' 
    }));
    setScopeValues([]);

    if (!roleId) return;

    const selectedRole = roles.find(r => r.role_id === parseInt(roleId));
    if (!selectedRole) return;

    // Use helper to determine scope type from role code
    const scopeTypeCode = getRoleScopeType(selectedRole.role_code);
    if (!scopeTypeCode) {
      console.warn(`No scope type mapping found for role: ${selectedRole.role_code}`);
      return;
    }

    // Find scope type ID from code
    const scopeType = scopeTypes.find(st => st.scope_type_code === scopeTypeCode);
    if (!scopeType) {
      console.warn(`Scope type not found for code: ${scopeTypeCode}`);
      return;
    }

    // Update form with role and scope type
    setNewRoleForm(prev => ({ 
      ...prev, 
      role_code: selectedRole.role_code,
      scope_type_code: scopeTypeCode,
      scope_type_id: scopeType.scope_type_id 
    }));

    // Load scope values if scope requires selection
    if (requiresScopeValue(scopeTypeCode)) {
      await loadScopeValues(scopeTypeCode);
    }
  };

  /**
   * Load scope values for selected scope type
   */
  const loadScopeValues = async (scopeTypeCode) => {
    setLoadingScopeValues(true);
    try {
      const values = await rbacAdminApi.getScopeValues(scopeTypeCode);
      setScopeValues(values);
    } catch (error) {
      console.error('Failed to load scope values:', error);
      alert('Failed to load scope values');
    } finally {
      setLoadingScopeValues(false);
    }
  };

  /**
   * Handle save new role assignment
   */
  const handleSaveNewRole = async () => {
    // Validation
    if (!newRoleForm.role_id) {
      alert('Please select a role');
      return;
    }

    // Scope type is auto-derived from role, should always be set when role is selected
    if (!newRoleForm.scope_type_code || !newRoleForm.scope_type_id) {
      alert('Unable to determine scope type for selected role. Please try again.');
      return;
    }

    // Check if scope value is required (all scopes except GLOBAL)
    if (requiresScopeValue(newRoleForm.scope_type_code) && !newRoleForm.scope_id) {
      alert('Please select a scope value');
      return;
    }

    setSubmitting(true);
    try {
      await rbacAdminApi.createRoleAssignment(user.user_id, {
        role_id: parseInt(newRoleForm.role_id),
        scope_type_id: parseInt(newRoleForm.scope_type_id),
        scope_id: newRoleForm.scope_id ? parseInt(newRoleForm.scope_id) : null
      });

      // Reload user detail
      const updatedDetail = await rbacAdminApi.getUserDetail(user.user_id);
      setUserDetail(updatedDetail);

      // Reset form
      setNewRoleForm({ role_id: '', role_code: '', scope_type_code: '', scope_type_id: '', scope_id: '' });
      setShowNewRoleForm(false);
      setScopeValues([]);

      alert('Role assigned successfully!');
    } catch (error) {
      console.error('Failed to assign role:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      alert(`Failed to assign role: ${errorMessage}`);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Handle revoke role assignment
   */
  const handleRevokeRole = async (assignment) => {
    if (!confirm(`Are you sure you want to revoke this access?\n\nRole: ${assignment.role_name}\nScope: ${assignment.scope_name || 'All Systems'}\n\nNote: This is a soft delete. Historical data is preserved in audit log.`)) {
      return;
    }

    setSubmitting(true);
    try {
      await rbacAdminApi.revokeRoleAssignment(user.user_id, assignment.assignment_id);

      // Reload user detail
      const updatedDetail = await rbacAdminApi.getUserDetail(user.user_id);
      setUserDetail(updatedDetail);

      alert('Access revoked successfully.\n\nAudit log entry created with revoked_at timestamp.');
    } catch (error) {
      console.error('Failed to revoke role:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      alert(`Failed to revoke role: ${errorMessage}`);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Cancel new role form
   */
  const handleCancelNewRole = () => {
    setNewRoleForm({ role_id: '', role_code: '', scope_type_code: '', scope_type_id: '', scope_id: '' });
    setScopeValues([]);
    setShowNewRoleForm(false);
  };

  // Get scope type name from ID
  const getScopeTypeName = (scopeTypeId) => {
    const scopeType = scopeTypes.find(st => st.scope_type_id === scopeTypeId);
    return scopeType?.scope_name || '';
  };

  if (loading) {
    return (
      <div className="rbac-modal-overlay">
        <div className="bg-white rounded-lg p-8">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto" />
        </div>
      </div>
    );
  }

  const activeAssignments = userDetail?.role_assignments.filter(a => a.is_active) || [];
  const revokedAssignments = userDetail?.role_assignments.filter(a => !a.is_active) || [];

  return (
    <div className="rbac-modal-overlay">
      <div className="rbac-modal" style={{ maxWidth: '700px' }}>
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Manage Access: {userDetail?.full_name}
            </h2>
            <p className="text-sm text-gray-500 mt-1">{userDetail?.email}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={submitting}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6">
          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <strong>Assign roles and scopes to this user.</strong> Multiple role assignments are allowed. Each assignment is explicit and independent.
            </p>
          </div>

          {/* Current Role Assignments */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Current Role Assignments</h3>
              <button
                onClick={() => setShowNewRoleForm(true)}
                disabled={submitting || showNewRoleForm}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className="w-4 h-4" />
                Add Role Assignment
              </button>
            </div>

            {activeAssignments.length === 0 ? (
              <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <p className="font-medium">No role assignments yet</p>
                <p className="text-sm mt-1">Click "Add Role Assignment" to grant access</p>
              </div>
            ) : (
              <div className="space-y-3">
                {activeAssignments.map((assignment) => (
                  <div key={assignment.assignment_id} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <RoleBadge assignment={{
                          role_name: assignment.role_name,
                          scope_type: assignment.scope_type,
                          scope_name: assignment.scope_name
                        }} />
                      </div>
                      <button
                        onClick={() => handleRevokeRole(assignment)}
                        disabled={submitting}
                        className="inline-flex items-center gap-1 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded border border-red-300 hover:border-red-400 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Trash2 className="w-4 h-4" />
                        Revoke
                      </button>
                    </div>
                    <p className="text-xs text-gray-500">
                      Granted by: {assignment.granted_by_name} on {new Date(assignment.granted_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Revoked Assignments (collapsed section) */}
            {revokedAssignments.length > 0 && (
              <details className="mt-4">
                <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-900">
                  Show {revokedAssignments.length} revoked assignment{revokedAssignments.length !== 1 ? 's' : ''}
                </summary>
                <div className="mt-2 space-y-2">
                  {revokedAssignments.map((assignment) => (
                    <div key={assignment.assignment_id} className="bg-red-50 border border-red-200 rounded-lg p-3 opacity-60">
                      <div className="flex items-center gap-2 mb-1">
                        <RoleBadge assignment={{
                          role_name: assignment.role_name,
                          scope_type: assignment.scope_type,
                          scope_name: assignment.scope_name
                        }} />
                        <span className="text-xs font-semibold text-red-600">REVOKED</span>
                      </div>
                      <p className="text-xs text-gray-600">
                        Revoked on {assignment.revoked_at ? new Date(assignment.revoked_at).toLocaleDateString() : 'Unknown'}
                      </p>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>

          {/* New Role Assignment Form */}
          {showNewRoleForm && (
            <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4">
              <h4 className="text-md font-semibold text-green-900 mb-4">Add New Role Assignment</h4>

              <div className="space-y-4">
                {/* Select Role */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Role <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={newRoleForm.role_id}
                    onChange={(e) => handleRoleChange(e.target.value)}
                    disabled={submitting}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Choose a role...</option>
                    {roles.map((role) => (
                      <option key={role.role_id} value={role.role_id}>
                        {role.role_name} - {role.description}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Scope Type (auto-filled, read-only) */}
                {newRoleForm.scope_type_code && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Scope Type (auto-determined)
                    </label>
                    <input
                      type="text"
                      value={newRoleForm.scope_type_code.replace(/_/g, ' ')}
                      disabled
                      readOnly
                      className="block w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700 font-medium"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Scope type is automatically determined based on the selected role
                    </p>
                  </div>
                )}

                {/* Scope Value (conditional based on scope type) */}
                {newRoleForm.scope_type_code && requiresScopeValue(newRoleForm.scope_type_code) && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select Specific Scope <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={newRoleForm.scope_id}
                      onChange={(e) => setNewRoleForm(prev => ({ ...prev, scope_id: e.target.value }))}
                      disabled={submitting || loadingScopeValues || (!loadingScopeValues && scopeValues.length === 0)}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="">
                        {loadingScopeValues ? 'Loading...' : scopeValues.length === 0 ? 'No scopes available for this scope type' : 'Choose...'}
                      </option>
                      {scopeValues.map((value) => (
                        <option key={value.scope_id} value={value.scope_id}>
                          {value.scope_name}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Select which {newRoleForm.scope_type_code.toLowerCase().replace(/_/g, ' ')} this user should have access to
                    </p>
                  </div>
                )}

                {/* GLOBAL scope info */}
                {newRoleForm.scope_type_code === 'GLOBAL' && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm text-blue-800">
                      <strong>Global Access:</strong> This role grants system-wide access. No specific scope selection is required.
                    </p>
                  </div>
                )}

                {/* Buttons */}
                <div className="flex gap-3 justify-end pt-2">
                  <button
                    type="button"
                    onClick={handleCancelNewRole}
                    disabled={submitting}
                    className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveNewRole}
                    disabled={submitting}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    Save Role Assignment
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200 bg-gray-50">
          <button
            type="button"
            onClick={() => {
              onAccessUpdated();
              onClose();
            }}
            disabled={submitting}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManageAccessModal;
