/**
 * OrgProjectTeamsPanel - Displays teams table when a Project is selected
 * Same layout as OrgSubSegmentProjectsPanel but for teams
 * 
 * Features:
 * - Table with columns: Checkbox | Team Name | Actions (Edit, Delete)
 * - Bulk selection with select-all checkbox (indeterminate support)
 * - Bulk action bar when selection > 0
 * - Header trash icon when selection > 0
 * - "+ Add Team" button in header
 * - INLINE EDIT: click Edit → input field → Save/Cancel
 * - INLINE ADD: click "+ Add Team" → new row at top with input → Save/Cancel
 */
import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { Trash2, Pencil, Check, X, Search } from 'lucide-react';
import BulkActionBar from './BulkActionBar';
import DeleteConfirmModal from './DeleteConfirmModal';
import DeleteSelectedModal from './DeleteSelectedModal';

const OrgProjectTeamsPanel = ({
  teams = [],
  projectName = '',
  onCreateTeam,
  onEditTeam,
  onDeleteTeam,
  onBulkDeleteTeams,
  disabled = false,
}) => {
  // Selection state
  const [selectedIds, setSelectedIds] = useState(new Set());
  
  // Delete modal states
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  const [bulkDeleteModalOpen, setBulkDeleteModalOpen] = useState(false);
  
  // Inline edit state
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  
  // Inline add state
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [addName, setAddName] = useState('');
  const [isAddingSaving, setIsAddingSaving] = useState(false);
  const [addError, setAddError] = useState(null);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  
  const selectAllRef = useRef(null);
  const nameInputRef = useRef(null);
  const addInputRef = useRef(null);

  // Clean up stale selections when teams list changes
  useEffect(() => {
    const teamIdSet = new Set(teams.map(t => t.id));
    const hasStale = Array.from(selectedIds).some(id => !teamIdSet.has(id));
    if (hasStale) {
      const newSelection = new Set();
      selectedIds.forEach(id => {
        if (teamIdSet.has(id)) {
          newSelection.add(id);
        }
      });
      setSelectedIds(newSelection);
    }
  }, [teams]);
  
  // Focus input when entering edit mode
  useEffect(() => {
    if (editingId !== null && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [editingId]);
  
  // Focus input when entering add mode
  useEffect(() => {
    if (isAddingNew && addInputRef.current) {
      addInputRef.current.focus();
    }
  }, [isAddingNew]);

  // Filter teams by search query
  const filteredTeams = useMemo(() => {
    if (!searchQuery.trim()) return teams;
    const query = searchQuery.toLowerCase();
    return teams.filter(team => 
      team.name.toLowerCase().includes(query)
    );
  }, [teams, searchQuery]);

  // Update select-all checkbox indeterminate state
  useEffect(() => {
    if (selectAllRef.current) {
      const visibleCount = filteredTeams.length;
      const selectedCount = selectedIds.size;
      selectAllRef.current.indeterminate = selectedCount > 0 && selectedCount < visibleCount;
    }
  }, [selectedIds, filteredTeams.length]);

  // Compute selection state for header checkbox
  const selectionState = useMemo(() => {
    const visibleCount = filteredTeams.length;
    const selectedCount = selectedIds.size;
    if (selectedCount === 0) return 'none';
    if (selectedCount === visibleCount && visibleCount > 0) return 'all';
    return 'some';
  }, [selectedIds, filteredTeams.length]);

  // Selection handlers
  const handleSelectAll = useCallback((e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(filteredTeams.map(t => t.id)));
    } else {
      setSelectedIds(new Set());
    }
  }, [filteredTeams]);

  const handleSelectRow = useCallback((id, checked) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);
  
  // Inline edit handlers
  const handleEdit = useCallback((team) => {
    setEditingId(team.id);
    setEditName(team.name);
  }, []);
  
  const handleCancel = useCallback(() => {
    setEditingId(null);
    setEditName('');
  }, []);
  
  const handleSave = useCallback(async () => {
    if (!editingId || isSaving) return;
    
    const trimmedName = editName.trim();
    if (!trimmedName) {
      handleCancel();
      return;
    }
    
    // Find the team being edited
    const team = teams.find(t => t.id === editingId);
    if (!team) {
      handleCancel();
      return;
    }
    
    // Skip save if name unchanged
    if (trimmedName === team.name) {
      handleCancel();
      return;
    }
    
    setIsSaving(true);
    try {
      if (onEditTeam) {
        await onEditTeam({ ...team, newName: trimmedName });
      }
      handleCancel();
    } catch (error) {
      // Keep edit mode open on error so user can retry
      console.error('Failed to save team name:', error);
    } finally {
      setIsSaving(false);
    }
  }, [editingId, editName, isSaving, teams, onEditTeam, handleCancel]);
  
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  }, [handleSave, handleCancel]);
  
  // Inline add handlers
  const handleStartAdd = useCallback(() => {
    // If already adding, just focus the input
    if (isAddingNew) {
      addInputRef.current?.focus();
      return;
    }
    // Cancel any edit in progress
    if (editingId !== null) {
      setEditingId(null);
      setEditName('');
    }
    setIsAddingNew(true);
    setAddName('');
  }, [isAddingNew, editingId]);
  
  const handleAddCancel = useCallback(() => {
    setIsAddingNew(false);
    setAddName('');
    setAddError(null);
  }, []);
  
  const handleAddSave = useCallback(async () => {
    if (isAddingSaving) return;
    
    const trimmedName = addName.trim();
    if (!trimmedName) {
      addInputRef.current?.focus();
      return;
    }
    
    setIsAddingSaving(true);
    setAddError(null);
    try {
      if (onCreateTeam) {
        await onCreateTeam(trimmedName);
      }
      // Success - exit add mode
      setIsAddingNew(false);
      setAddName('');
      setAddError(null);
    } catch (error) {
      // Handle 409 duplicate error with user-friendly message
      if (error.status === 409) {
        const errorMessage = error.message || `'${trimmedName}' team already exists.`;
        setAddError(errorMessage);
      } else {
        // For other errors, show generic message
        setAddError(error.message || 'Failed to create team');
      }
      console.error('Failed to create team:', error);
    } finally {
      setIsAddingSaving(false);
    }
  }, [addName, isAddingSaving, onCreateTeam]);
  
  const handleAddKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleAddCancel();
    }
  }, [handleAddSave, handleAddCancel]);

  // Single delete handlers
  const handleDeleteRequest = useCallback((team) => {
    setItemToDelete(team);
    setDeleteModalOpen(true);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (itemToDelete && onDeleteTeam) {
      await onDeleteTeam(itemToDelete);
    }
    setDeleteModalOpen(false);
    setItemToDelete(null);
  }, [itemToDelete, onDeleteTeam]);

  const handleCancelDelete = useCallback(() => {
    setDeleteModalOpen(false);
    setItemToDelete(null);
  }, []);

  // Bulk delete handlers
  const handleBulkDeleteRequest = useCallback(() => {
    if (selectedIds.size > 0) {
      setBulkDeleteModalOpen(true);
    }
  }, [selectedIds.size]);

  const handleConfirmBulkDelete = useCallback(async () => {
    if (selectedIds.size === 0) return;

    const teamsToDelete = teams.filter(t => selectedIds.has(t.id));
    
    if (onBulkDeleteTeams) {
      await onBulkDeleteTeams(teamsToDelete);
    } else if (onDeleteTeam) {
      // Fall back to deleting one by one
      for (const team of teamsToDelete) {
        await onDeleteTeam(team);
      }
    }
    
    setSelectedIds(new Set());
    setBulkDeleteModalOpen(false);
  }, [selectedIds, teams, onBulkDeleteTeams, onDeleteTeam]);

  const handleCancelBulkDelete = useCallback(() => {
    setBulkDeleteModalOpen(false);
  }, []);

  // Empty state - but show table if adding
  if ((!teams || teams.length === 0) && !isAddingNew) {
    return (
      <div className="info-section">
        <div className="info-section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
          <div className="info-section-title" style={{ margin: 0 }}>TEAMS IN THIS PROJECT</div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {!disabled && onCreateTeam && (
              <button className="btn btn-primary btn-sm" onClick={handleStartAdd}>
                + Add Team
              </button>
            )}
          </div>
        </div>
        <div className="skills-empty-state">
          <div className="empty-icon">👥</div>
          <p>No teams in this project yet</p>
          {!disabled && onCreateTeam && (
            <button 
              className="btn btn-primary btn-sm" 
              onClick={handleStartAdd}
              style={{ marginTop: '16px' }}
            >
              + Add First Team
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="info-section">
      {/* Section Header */}
      <div className="info-section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
        <div className="info-section-title" style={{ margin: 0 }}>TEAMS IN THIS PROJECT</div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {/* Search box - only show if teams exist */}
          {teams.length > 0 && (
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
                placeholder="Search teams..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '180px',
                  padding: '8px 12px 8px 36px',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontFamily: 'inherit'
                }}
              />
            </div>
          )}
          {/* Header trash button - only visible when selection > 0 */}
          {selectedIds.size > 0 && (
            <button 
              className="btn btn-danger btn-sm"
              onClick={handleBulkDeleteRequest}
              title={`Delete ${selectedIds.size} selected team(s)`}
            >
              <Trash2 size={14} />
            </button>
          )}
          {!disabled && onCreateTeam && (
            <button 
              className="btn btn-primary btn-sm" 
              onClick={handleStartAdd}
              disabled={isAddingSaving}
            >
              {isAddingSaving ? 'Adding...' : '+ Add Team'}
            </button>
          )}
        </div>
      </div>

      {/* Bulk Action Bar */}
      <BulkActionBar
        selectedCount={selectedIds.size}
        onDeleteSelected={handleBulkDeleteRequest}
        onClearSelection={handleClearSelection}
        itemLabel="team"
      />

      {/* Teams Table */}
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
                  disabled={filteredTeams.length === 0}
                  title={selectionState === 'all' ? 'Deselect all' : 'Select all'}
                />
              </th>
              <th>TEAM</th>
              <th style={{ width: '140px', textAlign: 'right', paddingRight: '16px' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {/* Inline Add Row - shown at top when adding */}
            {isAddingNew && (
              <tr className="add-row" style={{ backgroundColor: 'var(--background-secondary, #f8f9fa)' }}>
                <td style={{ textAlign: 'center' }}>
                  {/* Empty checkbox cell for alignment */}
                </td>
                <td>
                  <div>
                    <input
                      ref={addInputRef}
                      type="text"
                      className={`inline-edit-input${addError ? ' input-error' : ''}`}
                      value={addName}
                      onChange={(e) => {
                        setAddName(e.target.value);
                        if (addError) setAddError(null);
                      }}
                      onKeyDown={handleAddKeyDown}
                      disabled={isAddingSaving}
                      placeholder="Enter team name"
                      style={{
                        width: '100%',
                        padding: '4px 8px',
                        border: addError ? '1px solid #dc2626' : '1px solid var(--border-color)',
                        borderRadius: '4px',
                        fontSize: 'inherit',
                        backgroundColor: addError ? '#fef2f2' : undefined,
                      }}
                    />
                    {addError && (
                      <div style={{
                        color: '#dc2626',
                        fontSize: '12px',
                        marginTop: '4px',
                        lineHeight: '1.4'
                      }}>
                        {addError}
                      </div>
                    )}
                  </div>
                </td>
                <td style={{ textAlign: 'right', paddingRight: '16px' }}>
                  <div className="row-actions">
                    <button 
                      className="action-link"
                      onClick={handleAddSave}
                      disabled={isAddingSaving}
                      title="Save"
                    >
                      <Check size={14} />
                      <span>Save</span>
                    </button>
                    <button 
                      className="action-link danger"
                      onClick={handleAddCancel}
                      disabled={isAddingSaving}
                      title="Cancel"
                    >
                      <X size={14} />
                      <span>Cancel</span>
                    </button>
                  </div>
                </td>
              </tr>
            )}
            {filteredTeams.map((team) => {
              const isEditing = editingId === team.id;
              
              return (
                <tr key={team.id} className={selectedIds.has(team.id) ? 'selected' : ''}>
                  <td style={{ textAlign: 'center' }}>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(team.id)}
                      onChange={(e) => handleSelectRow(team.id, e.target.checked)}
                      disabled={isEditing}
                    />
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        ref={nameInputRef}
                        type="text"
                        className="inline-edit-input"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isSaving}
                        style={{
                          width: '100%',
                          padding: '4px 8px',
                          border: '1px solid var(--border-color)',
                          borderRadius: '4px',
                          fontSize: 'inherit',
                        }}
                      />
                    ) : (
                      team.name
                    )}
                  </td>
                  <td style={{ textAlign: 'right', paddingRight: '16px' }}>
                    <div className="row-actions">
                      {isEditing ? (
                        <>
                          <button 
                            className="action-link"
                            onClick={handleSave}
                            disabled={isSaving}
                            title="Save"
                          >
                            <Check size={14} />
                            <span>Save</span>
                          </button>
                          <button 
                            className="action-link danger"
                            onClick={handleCancel}
                            disabled={isSaving}
                            title="Cancel"
                          >
                            <X size={14} />
                            <span>Cancel</span>
                          </button>
                        </>
                      ) : (
                        <>
                          {onEditTeam && (
                            <button 
                              className="action-link"
                              onClick={() => handleEdit(team)}
                              title="Edit team"
                            >
                              <Pencil size={14} />
                              <span>Edit</span>
                            </button>
                          )}
                          {onDeleteTeam && (
                            <button 
                              className="action-link danger"
                              onClick={() => handleDeleteRequest(team)}
                              title="Delete team"
                            >
                              <Trash2 size={14} />
                              <span>Delete</span>
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Single Delete Modal */}
      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        itemName={itemToDelete?.name || 'this team'}
      />

      {/* Bulk Delete Modal */}
      <DeleteSelectedModal
        isOpen={bulkDeleteModalOpen}
        onClose={handleCancelBulkDelete}
        onConfirm={handleConfirmBulkDelete}
        selectedCount={selectedIds.size}
        itemLabel="team"
      />
    </div>
  );
};

export default OrgProjectTeamsPanel;
