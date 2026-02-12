/**
 * SkillsTable - Table component for displaying/editing skills in a sub-category
 * Matches UIUpdates.html styling exactly
 * 
 * Features:
 * - Table with columns: Checkbox | Skill Name | Alias | Actions
 * - Inline editing via SkillsTableRow
 * - Inline adding via AddSkillRow at top
 * - Empty state when no skills
 * - Delete confirmation modal (single)
 * - Bulk selection with select-all checkbox (indeterminate support)
 * - Bulk action bar when selection > 0
 * - Bulk delete confirmation modal
 * 
 * Selection state is managed by parent via selectedSkillIds/onSelectedSkillIdsChange
 */
import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import SkillsTableRow from './SkillsTableRow';
import AddSkillRow from './AddSkillRow';
import DeleteConfirmModal from './DeleteConfirmModal';
import BulkActionBar from './BulkActionBar';
import DeleteSelectedModal from './DeleteSelectedModal';

const SkillsTable = ({
  skills = [],
  onSkillSave,
  onSkillDelete,
  onBulkDelete,
  onAddSkill,
  onAddSkillComplete,
  onAddSkillCancel,
  isAddingSkill = false,
  disabled = false,
  // Bulk selection - managed by parent
  selectedSkillIds = new Set(),
  onSelectedSkillIdsChange,
  // Allow parent to open bulk delete modal
  showBulkDeleteModal = false,
  onCloseBulkDeleteModal
}) => {
  // Single delete state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [skillToDelete, setSkillToDelete] = useState(null);
  
  // Internal bulk delete modal state (when triggered from BulkActionBar)
  const [internalBulkDeleteModalOpen, setInternalBulkDeleteModalOpen] = useState(false);
  
  const tableContainerRef = useRef(null);
  const selectAllRef = useRef(null);

  // Scroll to top when adding starts
  useEffect(() => {
    if (isAddingSkill && tableContainerRef.current) {
      tableContainerRef.current.scrollTop = 0;
    }
  }, [isAddingSkill]);

  // Clean up stale selections when skills list changes
  useEffect(() => {
    if (!onSelectedSkillIdsChange) return;
    const skillIdSet = new Set(skills.map(s => s.id));
    const hasStale = Array.from(selectedSkillIds).some(id => !skillIdSet.has(id));
    if (hasStale) {
      const newSelection = new Set();
      selectedSkillIds.forEach(id => {
        if (skillIdSet.has(id)) {
          newSelection.add(id);
        }
      });
      onSelectedSkillIdsChange(newSelection);
    }
  }, [skills, selectedSkillIds, onSelectedSkillIdsChange]);

  // Update select-all checkbox indeterminate state
  useEffect(() => {
    if (selectAllRef.current) {
      const visibleCount = skills.length;
      const selectedCount = selectedSkillIds.size;
      selectAllRef.current.indeterminate = selectedCount > 0 && selectedCount < visibleCount;
    }
  }, [selectedSkillIds, skills.length]);

  // Compute selection state for header checkbox
  const selectionState = useMemo(() => {
    const visibleCount = skills.length;
    const selectedCount = selectedSkillIds.size;
    if (selectedCount === 0) return 'none';
    if (selectedCount === visibleCount && visibleCount > 0) return 'all';
    return 'some';
  }, [selectedSkillIds, skills.length]);

  // Single delete handlers
  const handleDeleteRequest = useCallback((skill) => {
    setSkillToDelete(skill);
    setDeleteModalOpen(true);
  }, []);

  const handleConfirmDelete = useCallback(() => {
    if (skillToDelete) {
      onSkillDelete(skillToDelete);
    }
    setDeleteModalOpen(false);
    setSkillToDelete(null);
  }, [skillToDelete, onSkillDelete]);

  const handleCancelDelete = useCallback(() => {
    setDeleteModalOpen(false);
    setSkillToDelete(null);
  }, []);

  // Add skill handlers
  const handleAddSkillSave = useCallback((newSkill) => {
    if (onAddSkillComplete) {
      onAddSkillComplete(newSkill);
    }
  }, [onAddSkillComplete]);

  const handleAddSkillCancel = useCallback(() => {
    if (onAddSkillCancel) {
      onAddSkillCancel();
    }
  }, [onAddSkillCancel]);

  // Bulk selection handlers
  const handleSelectAll = useCallback((e) => {
    if (!onSelectedSkillIdsChange) return;
    if (e.target.checked) {
      // Select all visible skills
      onSelectedSkillIdsChange(new Set(skills.map(s => s.id)));
    } else {
      // Deselect all
      onSelectedSkillIdsChange(new Set());
    }
  }, [skills, onSelectedSkillIdsChange]);

  const handleSelectRow = useCallback((skillId, checked) => {
    if (!onSelectedSkillIdsChange) return;
    const newSet = new Set(selectedSkillIds);
    if (checked) {
      newSet.add(skillId);
    } else {
      newSet.delete(skillId);
    }
    onSelectedSkillIdsChange(newSet);
  }, [selectedSkillIds, onSelectedSkillIdsChange]);

  const handleClearSelection = useCallback(() => {
    if (onSelectedSkillIdsChange) {
      onSelectedSkillIdsChange(new Set());
    }
  }, [onSelectedSkillIdsChange]);

  const handleBulkDeleteRequest = useCallback(() => {
    if (selectedSkillIds.size > 0) {
      setInternalBulkDeleteModalOpen(true);
    }
  }, [selectedSkillIds.size]);

  const handleConfirmBulkDelete = useCallback(async () => {
    if (selectedSkillIds.size === 0) return;

    // Get the selected skills
    const skillsToDelete = skills.filter(s => selectedSkillIds.has(s.id));
    
    // Call the bulk delete handler if provided
    if (onBulkDelete) {
      await onBulkDelete(skillsToDelete);
    } else {
      // Fall back to deleting one by one
      for (const skill of skillsToDelete) {
        await onSkillDelete(skill);
      }
    }
    
    // Clear selection and close modal
    if (onSelectedSkillIdsChange) {
      onSelectedSkillIdsChange(new Set());
    }
    setInternalBulkDeleteModalOpen(false);
    if (onCloseBulkDeleteModal) {
      onCloseBulkDeleteModal();
    }
  }, [selectedSkillIds, skills, onBulkDelete, onSkillDelete, onSelectedSkillIdsChange, onCloseBulkDeleteModal]);

  const handleCancelBulkDelete = useCallback(() => {
    setInternalBulkDeleteModalOpen(false);
    if (onCloseBulkDeleteModal) {
      onCloseBulkDeleteModal();
    }
  }, [onCloseBulkDeleteModal]);

  // Determine if bulk delete modal should be shown
  const bulkDeleteModalOpen = internalBulkDeleteModalOpen || showBulkDeleteModal;

  // Empty state (but show table if adding)
  if ((!skills || skills.length === 0) && !isAddingSkill) {
    return (
      <>
        <div className="skills-empty-state">
          <div className="empty-icon">🏷️</div>
          <p>No skills in this sub-category yet</p>
          {!disabled && onAddSkill && (
            <button 
              className="btn btn-primary btn-sm" 
              onClick={onAddSkill}
              style={{ marginTop: '16px' }}
            >
              + Add First Skill
            </button>
          )}
        </div>
      </>
    );
  }

  return (
    <>
      {/* Bulk Action Bar - only visible when selection > 0 */}
      <BulkActionBar
        selectedCount={selectedSkillIds.size}
        onDeleteSelected={handleBulkDeleteRequest}
        onClearSelection={handleClearSelection}
        itemLabel="skill"
      />

      <div className="skills-table-container" ref={tableContainerRef}>
        <table className="skills-table">
          <thead>
            <tr>
              <th style={{ width: '40px', textAlign: 'center' }}>
                <input
                  ref={selectAllRef}
                  type="checkbox"
                  checked={selectionState === 'all'}
                  onChange={handleSelectAll}
                  disabled={skills.length === 0}
                  title={selectionState === 'all' ? 'Deselect all' : 'Select all'}
                />
              </th>
              <th>Skill Name</th>
              <th>Alias</th>
              <th style={{ width: '140px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isAddingSkill && (
              <AddSkillRow
                onSave={handleAddSkillSave}
                onCancel={handleAddSkillCancel}
              />
            )}
            {skills.map((skill) => (
              <SkillsTableRow
                key={skill.id}
                skill={skill}
                onSave={onSkillSave}
                onDelete={handleDeleteRequest}
                disabled={disabled}
                isSelected={selectedSkillIds.has(skill.id)}
                onSelectChange={handleSelectRow}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Single delete modal */}
      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        itemName={skillToDelete?.name || 'this skill'}
      />

      {/* Bulk delete modal */}
      <DeleteSelectedModal
        isOpen={bulkDeleteModalOpen}
        onClose={handleCancelBulkDelete}
        onConfirm={handleConfirmBulkDelete}
        selectedCount={selectedSkillIds.size}
        itemLabel="skill"
      />
    </>
  );
};

export default SkillsTable;
