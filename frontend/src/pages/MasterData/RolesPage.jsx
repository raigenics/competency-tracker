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
  DependencyModal
} from './components';
import '../MasterData/contentPage.css';
import rolesApi from '../../services/api/rolesApi';

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
  const [newRoleDescription, setNewRoleDescription] = useState('');
  const addInputRef = useRef(null);
  
  // Inline edit state
  const [editingId, setEditingId] = useState(null);
  const [editDraftName, setEditDraftName] = useState('');
  const [editDraftDescription, setEditDraftDescription] = useState('');
  const editInputRef = useRef(null);
  
  // Modal states (only for delete)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [dependencyModalOpen, setDependencyModalOpen] = useState(false);
  const [bulkDeleteModalOpen, setBulkDeleteModalOpen] = useState(false);
  const [roleToDelete, setRoleToDelete] = useState(null);
  const [dependencyInfo, setDependencyInfo] = useState({ itemName: '', dependencies: [] });

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
      setEditDraftDescription('');
    }
    setIsAdding(true);
    setNewRoleName('');
    setNewRoleDescription('');
  }, [isAdding, editingId]);

  const handleAddSave = useCallback(async () => {
    const trimmedName = newRoleName.trim();
    if (!trimmedName) {
      addInputRef.current?.focus();
      return;
    }
    
    try {
      const createdRole = await rolesApi.createRole({
        role_name: trimmedName,
        role_description: newRoleDescription.trim() || null
      });
      
      // Add to local state
      setRolesData(prev => [{
        id: createdRole.role_id,
        name: createdRole.role_name,
        description: createdRole.role_description || ''
      }, ...prev]);
      
      setIsAdding(false);
      setNewRoleName('');
      setNewRoleDescription('');
      console.log('Created role:', createdRole);
    } catch (err) {
      console.error('Failed to create role:', err);
      // Could show toast notification here
    }
  }, [newRoleName, newRoleDescription]);

  const handleAddCancel = useCallback(() => {
    setIsAdding(false);
    setNewRoleName('');
    setNewRoleDescription('');
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
      setNewRoleDescription('');
    }
    if (editingId === role.id) {
      // Already editing this row, focus input
      editInputRef.current?.focus();
      return;
    }
    setEditingId(role.id);
    setEditDraftName(role.name);
    setEditDraftDescription(role.description || '');
  }, [isAdding, editingId]);

  const handleEditSave = useCallback(async () => {
    const trimmedName = editDraftName.trim();
    if (!trimmedName) {
      editInputRef.current?.focus();
      return;
    }
    
    try {
      const updatedRole = await rolesApi.updateRole(editingId, {
        role_name: trimmedName,
        role_description: editDraftDescription.trim() || null
      });
      
      // Update local state
      setRolesData(prev => prev.map(r => 
        r.id === editingId ? {
          id: updatedRole.role_id,
          name: updatedRole.role_name,
          description: updatedRole.role_description || ''
        } : r
      ));
      
      console.log('Updated role:', updatedRole);
      setEditingId(null);
      setEditDraftName('');
      setEditDraftDescription('');
    } catch (err) {
      console.error('Failed to update role:', err);
      // Could show toast notification here
    }
  }, [editingId, editDraftName, editDraftDescription]);

  const handleEditCancel = useCallback(() => {
    setEditingId(null);
    setEditDraftName('');
    setEditDraftDescription('');
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

  return (
    <div className="master-data-page" style={{ height: '100%' }}>
      <div className="details-panel" style={{ flex: 1 }}>
        {/* Header - uses existing .details-header class with border-bottom */}
        <div className="details-header">
          <h1 className="details-title" style={{ marginBottom: 0 }}>Roles</h1>
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
                    <th>Description</th>
                    <th style={{ width: '160px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Inline Add Row - appears at top when adding */}
                  {isAdding && (
                    <tr style={{ backgroundColor: '#fff9e6' }}>
                      <td style={{ textAlign: 'center' }}>
                        {/* Empty checkbox cell - disabled for new row */}
                      </td>
                      <td>
                        <input
                          ref={addInputRef}
                          type="text"
                          value={newRoleName}
                          onChange={(e) => setNewRoleName(e.target.value)}
                          onKeyDown={handleAddKeyDown}
                          placeholder="Enter role name"
                          style={{
                            width: '100%',
                            padding: '8px 12px',
                            border: '2px solid var(--primary)',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontFamily: 'inherit'
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
                            padding: '8px 12px',
                            border: '2px solid var(--primary)',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontFamily: 'inherit'
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
                  )}
                  
                  {/* Role Rows */}
                  {filteredRoles.map((role) => (
                    editingId === role.id ? (
                      // Inline Edit Row
                      <tr key={role.id} style={{ backgroundColor: '#fff9e6' }}>
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
                            onChange={(e) => setEditDraftName(e.target.value)}
                            onKeyDown={handleEditKeyDown}
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              border: '2px solid var(--primary)',
                              borderRadius: '4px',
                              fontSize: '14px',
                              fontFamily: 'inherit'
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
                              padding: '8px 12px',
                              border: '2px solid var(--primary)',
                              borderRadius: '4px',
                              fontSize: '14px',
                              fontFamily: 'inherit'
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
    </div>
  );
};

export default RolesPage;
