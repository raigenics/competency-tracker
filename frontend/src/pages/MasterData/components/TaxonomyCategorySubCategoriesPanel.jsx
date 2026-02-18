/**
 * TaxonomyCategorySubCategoriesPanel - Displays sub-categories table when a Category is selected
 * Mirrors OrgSegmentSubSegmentsPanel but for managing sub-categories under a taxonomy category
 * 
 * Features:
 * - Table with columns: Checkbox | Sub-Category Name | Actions (Edit, Delete)
 * - Bulk selection with select-all checkbox (indeterminate support)
 * - Bulk action bar when selection > 0
 * - Header trash icon when selection > 0
 * - "+ Add Sub-category" button in header
 * - INLINE EDIT: click Edit → input field → Save/Cancel
 * - INLINE ADD: click "+ Add Sub-category" → new row at top with input → Save/Cancel
 */
import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { Trash2, Pencil, Check, X, Search } from 'lucide-react';
import BulkActionBar from './BulkActionBar';
import DeleteConfirmModal from './DeleteConfirmModal';
import DeleteSelectedModal from './DeleteSelectedModal';

const TaxonomyCategorySubCategoriesPanel = ({
  subCategories = [],
  categoryName = '',
  onCreateSubCategory,
  onEditSubCategory,
  onDeleteSubCategory,
  onBulkDeleteSubCategories,
  onSubCategoryClick,
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

  // Clean up stale selections when subCategories list changes
  useEffect(() => {
    const subCategoryIdSet = new Set(subCategories.map(s => s.id));
    const hasStale = Array.from(selectedIds).some(id => !subCategoryIdSet.has(id));
    if (hasStale) {
      const newSelection = new Set();
      selectedIds.forEach(id => {
        if (subCategoryIdSet.has(id)) {
          newSelection.add(id);
        }
      });
      setSelectedIds(newSelection);
    }
  }, [subCategories]);
  
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

  // Filter sub-categories by search query
  const filteredSubCategories = useMemo(() => {
    if (!searchQuery.trim()) return subCategories;
    const query = searchQuery.toLowerCase();
    return subCategories.filter(subCategory => 
      subCategory.name.toLowerCase().includes(query)
    );
  }, [subCategories, searchQuery]);

  // Update select-all checkbox indeterminate state
  useEffect(() => {
    if (selectAllRef.current) {
      const visibleCount = filteredSubCategories.length;
      const selectedCount = selectedIds.size;
      selectAllRef.current.indeterminate = selectedCount > 0 && selectedCount < visibleCount;
    }
  }, [selectedIds, filteredSubCategories.length]);

  // Compute selection state for header checkbox
  const selectionState = useMemo(() => {
    const visibleCount = filteredSubCategories.length;
    const selectedCount = selectedIds.size;
    if (selectedCount === 0) return 'none';
    if (selectedCount === visibleCount && visibleCount > 0) return 'all';
    return 'some';
  }, [selectedIds, filteredSubCategories.length]);

  // Selection handlers
  const handleSelectAll = useCallback((e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(filteredSubCategories.map(s => s.id)));
    } else {
      setSelectedIds(new Set());
    }
  }, [filteredSubCategories]);

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
  const handleEdit = useCallback((subCategory) => {
    setEditingId(subCategory.id);
    setEditName(subCategory.name);
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
    
    // Find the sub-category being edited
    const subCategory = subCategories.find(s => s.id === editingId);
    if (!subCategory) {
      handleCancel();
      return;
    }
    
    // Skip save if name unchanged
    if (trimmedName === subCategory.name) {
      handleCancel();
      return;
    }
    
    setIsSaving(true);
    try {
      if (onEditSubCategory) {
        await onEditSubCategory({ ...subCategory, newName: trimmedName });
      }
      handleCancel();
    } catch (error) {
      // Keep edit mode open on error so user can retry
      console.error('Failed to save sub-category name:', error);
    } finally {
      setIsSaving(false);
    }
  }, [editingId, editName, isSaving, subCategories, onEditSubCategory, handleCancel]);
  
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
      if (onCreateSubCategory) {
        await onCreateSubCategory(trimmedName);
      }
      // Success - exit add mode
      setIsAddingNew(false);
      setAddName('');
      setAddError(null);
    } catch (error) {
      // Handle 409 duplicate error with user-friendly message
      if (error.status === 409) {
        const errorMessage = error.message || `'${trimmedName}' sub-category already exists.`;
        setAddError(errorMessage);
      } else {
        // For other errors, show generic message
        setAddError(error.message || 'Failed to create sub-category');
      }
      console.error('Failed to create sub-category:', error);
    } finally {
      setIsAddingSaving(false);
    }
  }, [addName, isAddingSaving, onCreateSubCategory]);
  
  const handleAddKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleAddCancel();
    }
  }, [handleAddSave, handleAddCancel]);
  
  // Delete handlers
  const handleDeleteRequest = useCallback((subCategory) => {
    setItemToDelete(subCategory);
    setDeleteModalOpen(true);
  }, []);
  
  const handleCancelDelete = useCallback(() => {
    setDeleteModalOpen(false);
    setItemToDelete(null);
  }, []);
  
  const handleConfirmDelete = useCallback(async () => {
    if (!itemToDelete) return;
    
    try {
      if (onDeleteSubCategory) {
        await onDeleteSubCategory(itemToDelete);
      }
    } catch (error) {
      console.error('Failed to delete sub-category:', error);
    } finally {
      setDeleteModalOpen(false);
      setItemToDelete(null);
    }
  }, [itemToDelete, onDeleteSubCategory]);
  
  // Bulk delete handlers
  const handleBulkDeleteRequest = useCallback(() => {
    if (selectedIds.size > 0) {
      setBulkDeleteModalOpen(true);
    }
  }, [selectedIds]);
  
  const handleCancelBulkDelete = useCallback(() => {
    setBulkDeleteModalOpen(false);
  }, []);
  
  const handleConfirmBulkDelete = useCallback(async () => {
    if (selectedIds.size === 0) return;
    
    const itemsToDelete = subCategories.filter(s => selectedIds.has(s.id));
    
    try {
      if (onBulkDeleteSubCategories) {
        await onBulkDeleteSubCategories(itemsToDelete);
      }
      setSelectedIds(new Set());
    } catch (error) {
      console.error('Failed to bulk delete sub-categories:', error);
    } finally {
      setBulkDeleteModalOpen(false);
    }
  }, [selectedIds, subCategories, onBulkDeleteSubCategories]);

  // Row click handler for navigation
  const handleRowClick = useCallback((subCategory, e) => {
    // Only navigate if not clicking on checkbox, actions, or in edit mode
    if (e.target.closest('input[type="checkbox"]') || 
        e.target.closest('.row-actions') || 
        editingId === subCategory.id) {
      return;
    }
    if (onSubCategoryClick) {
      onSubCategoryClick(subCategory);
    }
  }, [onSubCategoryClick, editingId]);

  // Empty state
  if (subCategories.length === 0 && !isAddingNew) {
    return (
      <div className="info-section">
        <div className="info-section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <div className="info-section-title" style={{ margin: 0 }}>SUB-CATEGORIES IN THIS CATEGORY</div>
          {!disabled && onCreateSubCategory && (
            <button 
              className="btn btn-primary btn-sm" 
              onClick={handleStartAdd}
            >
              + Add Sub-category
            </button>
          )}
        </div>
        <div className="empty-state" style={{ 
          textAlign: 'center', 
          padding: '40px 20px', 
          color: 'var(--text-muted)',
          backgroundColor: 'var(--background-secondary, #f8f9fa)',
          borderRadius: '8px'
        }}>
          <div style={{ marginBottom: '12px' }}>No sub-categories in this category</div>
          {!disabled && onCreateSubCategory && (
            <button 
              className="btn btn-primary btn-sm" 
              onClick={handleStartAdd}
            >
              + Add First Sub-category
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
        <div className="info-section-title" style={{ margin: 0 }}>SUB-CATEGORIES IN THIS CATEGORY</div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {/* Search box - only show if sub-categories exist */}
          {subCategories.length > 0 && (
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
                placeholder="Search sub-categories..."
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
              title={`Delete ${selectedIds.size} selected sub-category(ies)`}
            >
              <Trash2 size={14} />
            </button>
          )}
          {!disabled && onCreateSubCategory && (
            <button 
              className="btn btn-primary btn-sm" 
              onClick={handleStartAdd}
              disabled={isAddingSaving}
            >
              {isAddingSaving ? 'Adding...' : '+ Add Sub-category'}
            </button>
          )}
        </div>
      </div>

      {/* Bulk Action Bar */}
      <BulkActionBar
        selectedCount={selectedIds.size}
        onDeleteSelected={handleBulkDeleteRequest}
        onClearSelection={handleClearSelection}
        itemLabel="sub-category"
      />

      {/* Sub-Categories Table */}
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
                  disabled={filteredSubCategories.length === 0}
                  title={selectionState === 'all' ? 'Deselect all' : 'Select all'}
                />
              </th>
              <th>SUB-CATEGORY</th>
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
                      placeholder="Enter sub-category name"
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
            {filteredSubCategories.map((subCategory) => {
              const isEditing = editingId === subCategory.id;
              
              return (
                <tr 
                  key={subCategory.id} 
                  className={selectedIds.has(subCategory.id) ? 'selected' : ''}
                  onClick={(e) => handleRowClick(subCategory, e)}
                  style={{ cursor: onSubCategoryClick && !isEditing ? 'pointer' : 'default' }}
                >
                  <td style={{ textAlign: 'center' }}>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(subCategory.id)}
                      onChange={(e) => handleSelectRow(subCategory.id, e.target.checked)}
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
                      subCategory.name
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
                          {onEditSubCategory && (
                            <button 
                              className="action-link"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEdit(subCategory);
                              }}
                              title="Edit sub-category"
                            >
                              <Pencil size={14} />
                              <span>Edit</span>
                            </button>
                          )}
                          {onDeleteSubCategory && (
                            <button 
                              className="action-link danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteRequest(subCategory);
                              }}
                              title="Delete sub-category"
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
        itemName={itemToDelete?.name || 'this sub-category'}
      />

      {/* Bulk Delete Modal */}
      <DeleteSelectedModal
        isOpen={bulkDeleteModalOpen}
        onClose={handleCancelBulkDelete}
        onConfirm={handleConfirmBulkDelete}
        selectedCount={selectedIds.size}
        itemLabel="sub-category"
      />
    </div>
  );
};

export default TaxonomyCategorySubCategoriesPanel;
