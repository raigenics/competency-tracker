import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { bulkImportApi } from '../../services/api/bulkImportApi.js';

/**
 * Modal for mapping MISSING_ROLE errors from import failures.
 * 
 * Displays a searchable list of available roles and allows mapping
 * the failed row to an existing master role.
 */
const RoleMappingModal = ({ 
  isOpen, 
  onClose, 
  importRunId, 
  failedRow,
  failedRowIndex,
  onMapped 
}) => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mapping, setMapping] = useState(false);
  const [selectedRoleId, setSelectedRoleId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch roles when modal opens
  useEffect(() => {
    if (!isOpen) {
      // Reset state when modal closes
      setRoles([]);
      setSelectedRoleId(null);
      setSearchQuery('');
      setError(null);
      return;
    }
    
    if (!importRunId) {
      console.error('[RoleMappingModal] Cannot fetch roles: missing importRunId');
      return;
    }
    
    const fetchRoles = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await bulkImportApi.getRolesForMapping(importRunId);
        
        if (response.roles?.length > 0) {
          setRoles(response.roles);
        } else {
          setRoles([]);
          console.warn('[RoleMappingModal] No roles found');
        }
      } catch (err) {
        console.error('[RoleMappingModal] Failed to fetch roles:', err);
        setError('Failed to load roles. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchRoles();
  }, [isOpen, importRunId]);

  // Handle role mapping
  const handleMap = useCallback(async () => {
    if (!selectedRoleId || failedRowIndex === undefined || failedRowIndex === null) {
      console.error('[RoleMappingModal] Cannot map: missing selectedRoleId or failedRowIndex');
      setError('Cannot map role: missing required data');
      return;
    }

    setMapping(true);
    setError(null);

    try {
      const result = await bulkImportApi.mapRole(
        importRunId,
        failedRowIndex,
        selectedRoleId
      );
      
      onMapped?.(result);
      onClose();
    } catch (err) {
      console.error('Failed to map role:', err);
      
      if (err.response?.status === 409) {
        // Alias conflict - already mapped to different role
        setError(err.response.data?.detail || 'This role name is already mapped to a different role. Contact admin to resolve this conflict.');
      } else if (err.response?.status === 400) {
        setError(err.response.data?.detail || 'This row has already been mapped or is not a MISSING_ROLE error.');
      } else if (err.response?.status === 404) {
        setError(err.response.data?.detail || 'Role or import job not found.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to map role');
      }
    } finally {
      setMapping(false);
    }
  }, [selectedRoleId, failedRowIndex, importRunId, onMapped, onClose]);

  // Filter roles by search query (client-side) - memoized for performance
  const filteredRoles = useMemo(() => {
    return roles.filter(role => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase().trim();
      if (!query) return true;
      return (
        role.role_name.toLowerCase().includes(query) ||
        (role.role_alias && role.role_alias.toLowerCase().includes(query)) ||
        (role.role_description && role.role_description.toLowerCase().includes(query))
      );
    });
  }, [roles, searchQuery]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-xl shadow-2xl w-[600px] max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#e2e8f0]">
          <h2 className="text-lg font-semibold text-[#1e293b]">
            Map Missing Role
          </h2>
          <p className="text-sm text-[#64748b] mt-1">
            Map "<span className="font-medium text-[#334155]">{failedRow?.role_name || 'Unknown Role'}</span>" to an existing role
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Employee info */}
          {failedRow?.employee_name && (
            <div className="mb-4 p-3 bg-[#f8fafc] rounded-lg">
              <span className="text-xs text-[#64748b]">Employee: </span>
              <span className="text-sm text-[#334155] font-medium">
                {failedRow.employee_name || failedRow.full_name}
                {failedRow.zid && (
                  <span className="text-[#64748b] ml-1">({failedRow.zid})</span>
                )}
              </span>
            </div>
          )}

          {/* Search filter */}
          <div className="mb-4">
            <input
              type="text"
              placeholder="Search roles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-[#e2e8f0] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#667eea]/20 focus:border-[#667eea]"
            />
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-[#fef2f2] border border-[#fecaca] rounded-lg text-sm text-[#dc2626]">
              {error}
            </div>
          )}

          {/* Admin contact info */}
          <div className="mb-4 p-3 bg-[#fffbeb] border border-[#fef3c7] rounded-lg text-sm text-[#92400e]">
            Can&apos;t find the right role? Please contact your administrator to create a new role in master data.
          </div>

          {/* Roles list */}
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {loading ? (
              <div className="text-center py-8 text-[#64748b]">
                Loading roles...
              </div>
            ) : filteredRoles.length === 0 ? (
              <div className="text-center py-8 text-[#64748b]">
                {searchQuery ? 'No roles match your search.' : 'No roles available.'}
              </div>
            ) : (
              filteredRoles.map((role) => (
                <label
                  key={role.role_id}
                  className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedRoleId === role.role_id
                      ? 'border-[#667eea] bg-[#667eea]/5'
                      : 'border-[#e2e8f0] hover:border-[#cbd5e1] hover:bg-[#f8fafc]'
                  }`}
                >
                  <input
                    type="radio"
                    name="role-selection"
                    value={role.role_id}
                    checked={selectedRoleId === role.role_id}
                    onChange={() => setSelectedRoleId(role.role_id)}
                    className="w-4 h-4 text-[#667eea] focus:ring-[#667eea]"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-[#1e293b]">
                      {role.role_name}
                    </div>
                    {role.role_alias && (
                      <div className="text-xs text-[#64748b]">
                        Aliases: {role.role_alias}
                      </div>
                    )}
                    {role.role_description && (
                      <div className="text-xs text-[#94a3b8] mt-0.5">
                        {role.role_description}
                      </div>
                    )}
                  </div>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#e2e8f0] flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={mapping}
            className="px-4 py-2 text-sm font-medium text-[#475569] bg-white border border-[#e2e8f0] rounded-lg hover:bg-[#f8fafc] disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleMap}
            disabled={!selectedRoleId || mapping}
            className="px-4 py-2 text-sm font-medium text-white bg-[#667eea] rounded-lg hover:bg-[#5568d3] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {mapping ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Mapping...
              </>
            ) : (
              'Map to Selected Role'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RoleMappingModal;
