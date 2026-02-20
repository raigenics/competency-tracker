/**
 * RolesPage - Master Data page for managing Roles
 * Clean table view layout (no tree/detail panels)
 * Integrated with backend API for full CRUD operations.
 * 
 * Layout matches attached HTML wireframe structure:
 * - Header with title
 * - Controls row with search + add button (grouped)
 * - Bulk action bar (visible when items selected)
 * - Table with checkboxes, role name, description, and actions
 * - Inline add/edit (no modals for create/edit)
 * 
 * Styling reuses existing patterns from Skill Taxonomy page:
 * - .skills-table-container / .skills-table for table
 * - .bulk-action-bar / .selected-count-pill for bulk actions
 * - .btn / .btn-primary / .btn-danger / .btn-sm for buttons
 * - .row-actions / .action-link for row actions
 * - .empty-state for empty state
 */
import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { Search, Trash2, X, Check, Loader2 } from 'lucide-react';
import {
  DeleteConfirmModal,
  DependencyModal,
  ImportModal
} from './components';
import '../MasterData/contentPage.css';
import rolesApi from '../../services/api/rolesApi';
import { API_BASE_URL } from '../../config/apiConfig';

const RolesPage = () => {
  // Data state
  const [rolesData, setRolesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  
  // Inline add state
  const [isAdding, setIsAdding] = useState(false);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleAlias, setNewRoleAlias] = useState('');
  const [newRoleDescription, setNewRoleDescription] = useState('');
  const [addError, setAddError] = useState(null);
  const addInputRef = useRef(null);
  
  // Inline edit state
  const [editingId, setEditingId] = useState(null);
  const [editDraftName, setEditDraftName] = useState('');
  const [editDraftAlias, setEditDraftAlias] = useState('');
  const [editDraftDescription, setEditDraftDescription] = useState('');
  const [editError, setEditError] = useState(null);
  const editInputRef = useRef(null);
  
  // Modal states (only for delete)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [dependencyModalOpen, setDependencyModalOpen] = useState(false);
  const [bulkDeleteModalOpen, setBulkDeleteModalOpen] = useState(false);
  const [roleToDelete, setRoleToDelete] = useState(null);
  const [dependencyInfo, setDependencyInfo] = useState({ itemName: '', dependencies: [] });

  // Import modal state
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);

  const selectAllRef = useRef(null);

  // Fetch roles from API
  const fetchRoles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await rolesApi.getRoles();
      // Transform API response to component format
      setRolesData(data.map(role => ({
        id: role.role_id,
        name: role.role_name,
        alias: role.role_alias || '',
        description: role.role_description || ''
      })));
    } catch (err) {
      console.error('Failed to fetch roles:', err);
      setError('Failed to load roles. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load roles on mount
  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  // Filter roles by search query
  const filteredRoles = useMemo(() => {
    if (!searchQuery.trim()) return rolesData;
    const query = searchQuery.toLowerCase();
    return rolesData.filter(role => 
      role.name.toLowerCase().includes(query) ||
      (role.alias && role.alias.toLowerCase().includes(query)) ||
      (role.description && role.description.toLowerCase().includes(query))
    );
  }, [rolesData, searchQuery]);

  // Update select-all checkbox indeterminate state
  useEffect(() => {
    if (selectAllRef.current) {
      const visibleCount = filteredRoles.length;
      const selectedCount = selectedIds.size;
      selectAllRef.current.indeterminate = selectedCount > 0 && selectedCount < visibleCount;
    }
  }, [selectedIds, filteredRoles.length]);

  // Auto-focus add input when entering add mode
  useEffect(() => {
    if (isAdding && addInputRef.current) {
      addInputRef.current.focus();
    }
  }, [isAdding]);

  // Auto-focus edit input when entering edit mode
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  // Selection state for header checkbox
  const selectionState = useMemo(() => {
    const visibleCount = filteredRoles.length;
    const selectedCount = selectedIds.size;
    if (selectedCount === 0) return 'none';
    if (selectedCount === visibleCount && visibleCount > 0) return 'all';
    return 'some';
  }, [selectedIds, filteredRoles.length]);

  // Handlers
  const handleSelectAll = useCallback((e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(filteredRoles.map(r => r.id)));
    } else {
      setSelectedIds(new Set());
    }
  }, [filteredRoles]);

  const handleSelectRow = useCallback((roleId, checked) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(roleId);
      } else {
        newSet.delete(roleId);
      }
      return newSet;
    });
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  // Inline Add handlers
  const handleAddClick = useCallback(() => {
    if (isAdding) {
      // Already adding, just focus the input
      addInputRef.current?.focus();
      return;
    }
    if (editingId) {
      // Cancel any active edit first
      setEditingId(null);
      setEditDraftName('');
      setEditDraftAlias('');
      setEditDraftDescription('');
    }
    setIsAdding(true);
    setNewRoleName('');
    setNewRoleAlias('');
    setNewRoleDescription('');
  }, [isAdding, editingId]);

  const handleAddSave = useCallback(async () => {
    const trimmedName = newRoleName.trim();
    if (!trimmedName) {
      addInputRef.current?.focus();
      return;
    }
    
    setAddError(null);
    
    try {
      const createdRole = await rolesApi.createRole({
        role_name: trimmedName,
        role_alias: newRoleAlias.trim() || null,
        role_description: newRoleDescription.trim() || null
      });
      
      // Add to local state
      setRolesData(prev => [{
        id: createdRole.role_id,
        name: createdRole.role_name,
        alias: createdRole.role_alias || '',
        description: createdRole.role_description || ''
      }, ...prev]);
      
      setIsAdding(false);
      setNewRoleName('');
      setNewRoleAlias('');
      setNewRoleDescription('');
      setAddError(null);
      console.log('Created role:', createdRole);
    } catch (err) {
      console.error('Failed to create role:', err);
      // Handle 409 duplicate error with inline message
      if (err.status === 409) {
        const errorMessage = err.data?.detail || err.message || `Role '${trimmedName}' already exists`;
        setAddError(errorMessage);
        addInputRef.current?.focus();
      } else {
        // For other errors, show generic inline message
        setAddError(err.message || 'Failed to create role');
      }
    }
  }, [newRoleName, newRoleAlias, newRoleDescription]);

  const handleAddCancel = useCallback(() => {
    setIsAdding(false);
    setNewRoleName('');
    setNewRoleAlias('');
    setNewRoleDescription('');
    setAddError(null);
  }, []);

  const handleAddKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleAddCancel();
    }
  }, [handleAddSave, handleAddCancel]);

  // Inline Edit handlers
  const handleEditClick = useCallback((role) => {
    if (isAdding) {
      // Cancel add mode first
      setIsAdding(false);
      setNewRoleName('');
      setNewRoleAlias('');
      setNewRoleDescription('');
    }
    if (editingId === role.id) {
      // Already editing this row, focus input
      editInputRef.current?.focus();
      return;
    }
    setEditingId(role.id);
    setEditDraftName(role.name);
    setEditDraftAlias(role.alias || '');
    setEditDraftDescription(role.description || '');
  }, [isAdding, editingId]);

  const handleEditSave = useCallback(async () => {
    const trimmedName = editDraftName.trim();
    if (!trimmedName) {
      editInputRef.current?.focus();
      return;
    }
    
    setEditError(null);
    
    try {
      const updatedRole = await rolesApi.updateRole(editingId, {
        role_name: trimmedName,
        role_alias: editDraftAlias.trim() || null,
        role_description: editDraftDescription.trim() || null
      });
      
      // Update local state
      setRolesData(prev => prev.map(r => 
        r.id === editingId ? {
          id: updatedRole.role_id,
          name: updatedRole.role_name,
          alias: updatedRole.role_alias || '',
          description: updatedRole.role_description || ''
        } : r
      ));
      
      console.log('Updated role:', updatedRole);
      setEditingId(null);
      setEditDraftName('');
      setEditDraftAlias('');
      setEditDraftDescription('');
      setEditError(null);
    } catch (err) {
      console.error('Failed to update role:', err);
      // Handle 409 duplicate error with inline message
      if (err.status === 409) {
        const errorMessage = err.data?.detail || err.message || `Role '${trimmedName}' already exists`;
        setEditError(errorMessage);
        editInputRef.current?.focus();
      } else {
        // For other errors, show generic inline message
        setEditError(err.message || 'Failed to update role');
      }
    }
  }, [editingId, editDraftName, editDraftAlias, editDraftDescription]);

  const handleEditCancel = useCallback(() => {
    setEditingId(null);
    setEditDraftName('');
    setEditDraftAlias('');
    setEditDraftDescription('');
    setEditError(null);
  }, []);

  const handleEditKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleEditSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleEditCancel();
    }
  }, [handleEditSave, handleEditCancel]);

  const handleDeleteClick = useCallback((role) => {
    setRoleToDelete(role);
    // TODO: Check for dependencies (employees assigned to this role)
    // For now, always show delete confirmation
    setDeleteModalOpen(true);
  }, []);

  const handleConfirmDelete = async () => {
    if (roleToDelete) {
      try {
        await rolesApi.deleteRole(roleToDelete.id);
        console.log('Deleted role:', roleToDelete.id);
        
        // Remove from local state
        setRolesData(prev => prev.filter(r => r.id !== roleToDelete.id));
        setSelectedIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(roleToDelete.id);
          return newSet;
        });
        setDeleteModalOpen(false);
        setRoleToDelete(null);
      } catch (err) {
        console.error('Failed to delete role:', err);
        setDeleteModalOpen(false);
        
        // Handle 409 Conflict - role has dependencies
        if (err.status === 409 && err.data) {
          const deps = err.data.dependencies || {};
          const dependencyList = [];
          if (deps.employees) {
            dependencyList.push({ icon: '👥', label: `${deps.employees} Employee${deps.employees > 1 ? 's' : ''} assigned` });
          }
          setDependencyInfo({
            itemName: roleToDelete.name,
            dependencies: dependencyList
          });
          setDependencyModalOpen(true);
        }
        setRoleToDelete(null);
      }
    } else {
      setDeleteModalOpen(false);
      setRoleToDelete(null);
    }
  };

  const handleBulkDeleteClick = useCallback(() => {
    if (selectedIds.size > 0) {
      setBulkDeleteModalOpen(true);
    }
  }, [selectedIds.size]);

  const handleConfirmBulkDelete = useCallback(async () => {
    try {
      const roleIds = Array.from(selectedIds);
      const result = await rolesApi.deleteRolesBulk(roleIds);
      console.log('Bulk deleted roles:', result.deleted_count);
      
      // Remove from local state and clear selection
      setRolesData(prev => prev.filter(r => !selectedIds.has(r.id)));
      setSelectedIds(new Set());
      setBulkDeleteModalOpen(false);
    } catch (err) {
      console.error('Failed to bulk delete roles:', err);
      setBulkDeleteModalOpen(false);
      
      // Handle 409 Conflict - some roles have dependencies
      if (err.status === 409 && err.data) {
        const blocked = err.data.blocked || [];
        const totalEmployees = err.data.total_employees || 0;
        
        // Build dependency list for display
        const dependencyList = [];
        if (totalEmployees > 0) {
          dependencyList.push({ 
            icon: '👥', 
            label: `${totalEmployees} Employee${totalEmployees > 1 ? 's' : ''} assigned (across ${blocked.length} role${blocked.length > 1 ? 's' : ''})` 
          });
        }
        
        // Show which specific roles are blocked
        blocked.forEach(item => {
          const roleName = rolesData.find(r => r.id === item.role_id)?.name || `Role #${item.role_id}`;
          dependencyList.push({
            icon: '🔗',
            label: `${roleName}: ${item.employees} employee${item.employees > 1 ? 's' : ''}`
          });
        });
        
        setDependencyInfo({
          itemName: `${blocked.length} selected role${blocked.length > 1 ? 's' : ''}`,
          dependencies: dependencyList
        });
        setDependencyModalOpen(true);
        // Keep selection so user can adjust
      }
    }
  }, [selectedIds, rolesData]);

  // Get backend base URL (without /api suffix) for static file access
  const backendBaseUrl = API_BASE_URL.replace(/\/api$/, '');
  const templateUrl = `${backendBaseUrl}/static/templates/RoleMasterData_Template.xlsx`;

  return (
    <div className="master-data-page" style={{ height: '100%' }}>
      <div className="details-panel" style={{ flex: 1 }}>
        {/* Header - uses existing .details-header class with border-bottom */}
        <div className="details-header">
          <div className="content-title-section">
            <h1 className="details-title" style={{ marginBottom: 0 }}>Roles</h1>
          </div>
          <div className="action-buttons">
            <a 
              className="btn btn-secondary" 
              href={templateUrl}
              download="RoleMasterData_Template.xlsx"
              title="Download Excel template to add roles in bulk"
              style={{ textDecoration: 'none' }}
            >
              📥 Download Template
            </a>
            <button 
              className="btn btn-outline" 
              onClick={() => setImportModalOpen(true)}
              title="Upload completed template to import roles"
            >
              📤 Import Roles
            </button>
          </div>
        </div>

        {/* Content wrapper with max-width for better readability */}
        <div className="details-content" style={{ maxWidth: '1400px', width: '100%', margin: '0 auto', padding: 'var(--spacing-lg)' }}>
          
          {/* Loading State */}
          {loading && (
            <div className="empty-state">
              <Loader2 className="animate-spin" size={32} />
              <p style={{ marginTop: '12px' }}>Loading roles...</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="empty-state">
              <div className="empty-icon">⚠️</div>
              <h3>Error Loading Roles</h3>
              <p>{error}</p>
              <button 
                className="btn btn-primary"
                onClick={fetchRoles}
              >
                Retry
              </button>
            </div>
          )}

          {/* Main Content - only show when not loading and no error */}
          {!loading && !error && (
            <>
              {/* Controls Row - Search (left) + Add (right) */}
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: 'var(--spacing-lg)'
              }}>
                {/* Search Input */}
                <div className="search-box" style={{ position: 'relative' }}>
                  <Search 
                    size={16} 
                    style={{ 
                      position: 'absolute', 
                      left: '12px', 
                      top: '50%', 
                      transform: 'translateY(-50%)', 
                      color: 'var(--text-muted)' 
                    }} 
                  />
                  <input
                    type="text"
                    placeholder="Search roles..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{
                      width: '280px',
                      padding: '10px 12px 10px 36px',
                      border: '1px solid var(--border)',
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontFamily: 'inherit'
                    }}
                  />
                </div>
                {/* Add Role Button */}
                <button 
                  className="btn btn-primary"
                  onClick={handleAddClick}
                >
                  + Add Role
                </button>
              </div>

              {/* Bulk Action Bar - visible when items selected */}
              {selectedIds.size > 0 && (
                <div className="bulk-action-bar">
                  <span className="selected-count-pill">
                    {selectedIds.size} selected
                  </span>
                  <button 
                    className="btn btn-danger btn-sm"
                    onClick={handleBulkDeleteClick}
                  >
                <Trash2 size={14} />
                Delete Selected
              </button>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={handleClearSelection}
              >
                <X size={14} />
                Clear
              </button>
            </div>
          )}

          {/* Roles Table or Empty State */}
          {filteredRoles.length === 0 && !isAdding ? (
            <div className="empty-state">
              <div className="empty-icon">👤</div>
              <h3>No roles found</h3>
              <p>
                {searchQuery 
                  ? 'Try adjusting your search query' 
                  : 'Get started by adding your first role'}
              </p>
              {!searchQuery && (
                <button 
                  className="btn btn-primary"
                  onClick={handleAddClick}
                >
                  + Add Role
                </button>
              )}
            </div>
          ) : (
            <div className="skills-table-container">
              <table className="skills-table">
                <thead>
                  <tr>
                    <th style={{ width: '40px', textAlign: 'center' }}>
                      <input
                        ref={selectAllRef}
                        type="checkbox"
                        checked={selectionState === 'all'}
                        onChange={handleSelectAll}
                        disabled={filteredRoles.length === 0}
                        title={selectionState === 'all' ? 'Deselect all' : 'Select all'}
                      />
                    </th>
                    <th style={{ width: '200px' }}>Role Name</th>
                    <th style={{ width: '200px' }}>Role Alias</th>
                    <th>Description</th>
                    <th style={{ width: '160px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Inline Add Row - appears at top when adding */}
                  {isAdding && (
                    <>
                      <tr style={{ backgroundColor: 'var(--background-secondary, #f8f9fa)' }}>
                        <td style={{ textAlign: 'center' }}>
                          {/* Empty checkbox cell - disabled for new row */}
                        </td>
                        <td>
                          <input
                            ref={addInputRef}
                            type="text"
                            value={newRoleName}
                            onChange={(e) => {
                              setNewRoleName(e.target.value);
                              if (addError) setAddError(null);
                            }}
                            onKeyDown={handleAddKeyDown}
                            placeholder="Enter role name"
                            style={{
                              width: '100%',
                              padding: '4px 8px',
                              border: addError ? '1px solid #dc2626' : '1px solid var(--border-color)',
                              borderRadius: '4px',
                              fontSize: 'inherit',
                              backgroundColor: addError ? '#fef2f2' : undefined
                            }}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={newRoleAlias}
                            onChange={(e) => setNewRoleAlias(e.target.value)}
                            onKeyDown={handleAddKeyDown}
                            placeholder="Enter comma-separated aliases"
                            style={{
                              width: '100%',
                              padding: '4px 8px',
                              border: '1px solid var(--border-color)',
                              borderRadius: '4px',
                              fontSize: 'inherit'
                            }}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={newRoleDescription}
                            onChange={(e) => setNewRoleDescription(e.target.value)}
                            onKeyDown={handleAddKeyDown}
                            placeholder="Enter description (optional)"
                            style={{
                              width: '100%',
                              padding: '4px 8px',
                              border: '1px solid var(--border-color)',
                              borderRadius: '4px',
                              fontSize: 'inherit'
                            }}
                          />
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div className="skill-actions" style={{ justifyContent: 'flex-end' }}>
                            <button className="btn-save" onClick={handleAddSave}>
                              <Check size={14} />
                              Save
                            </button>
                            <button className="btn-cancel" onClick={handleAddCancel}>
                              <X size={14} />
                              Cancel
                            </button>
                          </div>
                        </td>
                      </tr>
                      {/* Error row - separate row for validation message */}
                      {addError && (
                        <tr style={{ backgroundColor: 'var(--background-secondary, #f8f9fa)' }}>
                          <td></td>
                          <td colSpan={3} style={{ paddingTop: 0 }}>
                            <div style={{
                              color: '#dc2626',
                              fontSize: '12px',
                              lineHeight: '1.4'
                            }}>
                              {addError}
                            </div>
                          </td>
                          <td></td>
                        </tr>
                      )}
                    </>
                  )}
                  
                  {/* Role Rows */}
                  {filteredRoles.map((role) => (
                    editingId === role.id ? (
                      // Inline Edit Row
                      <React.Fragment key={role.id}>
                        <tr style={{ backgroundColor: 'var(--background-secondary, #f8f9fa)' }}>
                          <td style={{ textAlign: 'center' }}>
                            <input
                              type="checkbox"
                              checked={selectedIds.has(role.id)}
                              onChange={(e) => handleSelectRow(role.id, e.target.checked)}
                            />
                          </td>
                          <td>
                            <input
                              ref={editInputRef}
                              type="text"
                              value={editDraftName}
                              onChange={(e) => {
                                setEditDraftName(e.target.value);
                                if (editError) setEditError(null);
                              }}
                              onKeyDown={handleEditKeyDown}
                              style={{
                                width: '100%',
                                padding: '4px 8px',
                                border: editError ? '1px solid #dc2626' : '1px solid var(--border-color)',
                                borderRadius: '4px',
                                fontSize: 'inherit',
                                backgroundColor: editError ? '#fef2f2' : undefined
                              }}
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              value={editDraftAlias}
                              onChange={(e) => setEditDraftAlias(e.target.value)}
                              onKeyDown={handleEditKeyDown}
                              placeholder="Enter comma-separated aliases"
                              style={{
                                width: '100%',
                                padding: '4px 8px',
                                border: '1px solid var(--border-color)',
                                borderRadius: '4px',
                                fontSize: 'inherit'
                              }}
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              value={editDraftDescription}
                              onChange={(e) => setEditDraftDescription(e.target.value)}
                              onKeyDown={handleEditKeyDown}
                              placeholder="Enter description (optional)"
                              style={{
                                width: '100%',
                                padding: '4px 8px',
                                border: '1px solid var(--border-color)',
                                borderRadius: '4px',
                                fontSize: 'inherit'
                              }}
                            />
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <div className="skill-actions" style={{ justifyContent: 'flex-end' }}>
                              <button className="btn-save" onClick={handleEditSave}>
                                <Check size={14} />
                                Save
                              </button>
                              <button className="btn-cancel" onClick={handleEditCancel}>
                                <X size={14} />
                                Cancel
                              </button>
                            </div>
                          </td>
                        </tr>
                        {/* Error row - separate row for validation message */}
                        {editError && (
                          <tr style={{ backgroundColor: 'var(--background-secondary, #f8f9fa)' }}>
                            <td></td>
                            <td colSpan={3} style={{ paddingTop: 0 }}>
                              <div style={{
                                color: '#dc2626',
                                fontSize: '12px',
                                lineHeight: '1.4'
                              }}>
                                {editError}
                              </div>
                            </td>
                            <td></td>
                          </tr>
                        )}
                      </React.Fragment>
                    ) : (
                      // Normal Row
                      <tr 
                        key={role.id}
                        className={selectedIds.has(role.id) ? 'selected' : ''}
                      >
                        <td style={{ textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={selectedIds.has(role.id)}
                            onChange={(e) => handleSelectRow(role.id, e.target.checked)}
                          />
                        </td>
                        <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{role.name}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{role.alias || '—'}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{role.description || '—'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <div className="row-actions">
                            <button 
                              className="action-link"
                              onClick={() => handleEditClick(role)}
                            >
                              Edit
                            </button>
                            <button 
                              className="action-link danger"
                              onClick={() => handleDeleteClick(role)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  ))}
                </tbody>
              </table>
            </div>
          )}
            </>
          )}
        </div>
      </div>

      {/* Delete Modals */}
      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setRoleToDelete(null);
        }}
        itemName={roleToDelete?.name}
        onConfirm={handleConfirmDelete}
      />

      <DependencyModal
        isOpen={dependencyModalOpen}
        onClose={() => {
          setDependencyModalOpen(false);
          setDependencyInfo({ itemName: '', dependencies: [] });
        }}
        itemName={dependencyInfo.itemName}
        dependencies={dependencyInfo.dependencies}
      />

      {/* Bulk Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={bulkDeleteModalOpen}
        onClose={() => setBulkDeleteModalOpen(false)}
        itemName={`${selectedIds.size} role${selectedIds.size > 1 ? 's' : ''}`}
        onConfirm={handleConfirmBulkDelete}
      />

      {/* Import Modal */}
      <ImportModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        itemType="Roles"
        onImport={async (data) => {
          if (data.type !== 'file' || !data.file) {
            window.alert('Please select an Excel file to import.');
            return;
          }
          
          setImportModalOpen(false);
          setIsImporting(true);
          
          try {
            const result = await rolesApi.importRoles(data.file);
            setImportResult(result);
            // Refresh table
            fetchRoles();
          } catch (err) {
            console.error('Import failed:', err);
            window.alert(`Import failed: ${err.message || 'Unknown error'}`);
          } finally {
            setIsImporting(false);
          }
        }}
      />

      {/* Import Loading Overlay */}
      {isImporting && (
        <div 
          className="modal-backdrop"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100
          }}
        >
          <div 
            style={{
              background: 'var(--card-bg, #fff)',
              borderRadius: '8px',
              padding: '32px 48px',
              textAlign: 'center',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
            }}
          >
            <Loader2 
              size={48} 
              style={{ 
                animation: 'spin 1s linear infinite',
                color: 'var(--primary-color, #0066cc)',
                marginBottom: '16px'
              }} 
            />
            <p style={{ margin: 0, fontSize: '1.1rem' }}>Importing roles...</p>
          </div>
        </div>
      )}

      {/* Import Results Modal */}
      {importResult && (
        <div 
          className="modal-backdrop"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100
          }}
          onClick={() => setImportResult(null)}
        >
          <div 
            style={{
              background: 'var(--card-bg, #fff)',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '600px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginTop: 0, marginBottom: '16px' }}>
              📤 Import Results
            </h3>
            
            {/* Summary */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(3, 1fr)', 
              gap: '16px', 
              marginBottom: '20px' 
            }}>
              <div style={{ 
                padding: '12px', 
                background: 'var(--bg-muted, #f5f5f5)', 
                borderRadius: '6px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                  {importResult.total_rows}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Total Rows
                </div>
              </div>
              <div style={{ 
                padding: '12px', 
                background: 'rgba(34, 197, 94, 0.1)', 
                borderRadius: '6px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#22c55e' }}>
                  {importResult.success_count}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Imported
                </div>
              </div>
              <div style={{ 
                padding: '12px', 
                background: importResult.failure_count > 0 ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-muted, #f5f5f5)', 
                borderRadius: '6px',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: 'bold', 
                  color: importResult.failure_count > 0 ? '#ef4444' : 'inherit' 
                }}>
                  {importResult.failure_count}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Failed
                </div>
              </div>
            </div>
            
            {/* Failures List */}
            {importResult.failures && importResult.failures.length > 0 && (
              <div>
                <h4 style={{ marginBottom: '12px', color: '#ef4444' }}>
                  ⚠️ Failed Rows
                </h4>
                <div style={{ 
                  maxHeight: '200px', 
                  overflowY: 'auto',
                  border: '1px solid var(--border-color, #e5e7eb)',
                  borderRadius: '6px'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ background: 'var(--bg-muted, #f5f5f5)' }}>
                        <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                          Row
                        </th>
                        <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                          Role Name
                        </th>
                        <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                          Reason
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {importResult.failures.map((failure, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-color, #e5e7eb)' }}>
                          <td style={{ padding: '8px' }}>{failure.row_number}</td>
                          <td style={{ padding: '8px' }}>{failure.role_name}</td>
                          <td style={{ padding: '8px', color: '#ef4444' }}>{failure.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Close Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button 
                className="btn btn-primary" 
                onClick={() => setImportResult(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RolesPage;
