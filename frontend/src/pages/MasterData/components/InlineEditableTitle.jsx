/**
 * InlineEditableTitle - Reusable inline edit component for Category/Sub-Category names
 * Matches UIUpdates.html styling exactly
 * 
 * Features:
 * - Click edit icon to enter edit mode
 * - Save icon (checkmark) to save changes
 * - Cancel icon (X) to revert changes
 * - ESC key cancels edit
 * - ENTER key saves
 * - Validates non-empty name
 * - Optional delete icon beside edit
 * - Optional add child button
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Pencil, Check, X, Trash2 } from 'lucide-react';

const InlineEditableTitle = ({ 
  value, 
  onSave,
  onDelete,
  onAddChild,
  addChildLabel,
  disabled = false,
  placeholder = 'Enter name...'
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const inputRef = useRef(null);

  // Sync internal state when value prop changes
  useEffect(() => {
    setEditValue(value);
  }, [value]);

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleEditClick = useCallback(() => {
    if (disabled) return;
    setEditValue(value);
    setIsEditing(true);
  }, [value, disabled]);

  const handleSave = useCallback(() => {
    const trimmed = editValue.trim();
    if (!trimmed) {
      // Don't allow empty names - could show error or just revert
      setEditValue(value);
      setIsEditing(false);
      return;
    }
    
    if (trimmed !== value) {
      onSave(trimmed);
    }
    setIsEditing(false);
  }, [editValue, value, onSave]);

  const handleCancel = useCallback(() => {
    setEditValue(value);
    setIsEditing(false);
  }, [value]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  }, [handleSave, handleCancel]);

  if (isEditing) {
    return (
      <div className="details-title-row">
        <input
          ref={inputRef}
          type="text"
          className="details-title-input"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleCancel}
          placeholder={placeholder}
        />
        <Check 
          className="icon-save"
          size={20}
          onMouseDown={(e) => {
            e.preventDefault(); // Prevent blur before save
            handleSave();
          }}
          aria-label="Save"
        />
        <X 
          className="icon-cancel"
          size={20}
          onMouseDown={(e) => {
            e.preventDefault(); // Prevent blur before cancel
            handleCancel();
          }}
          aria-label="Cancel"
        />
      </div>
    );
  }

  return (
    <div className="details-title-row">
      <div className="details-title-left">
        <div className="details-title" id="titleText">{value}</div>
        {!disabled && (
          <>
            <Pencil 
              className="icon-edit"
              size={20}
              onClick={handleEditClick}
              aria-label="Edit"
            />
            {onDelete && (
              <Trash2 
                className="icon-delete"
                size={20}
                onClick={onDelete}
                aria-label="Delete"
              />
            )}
          </>
        )}
      </div>
      {onAddChild && addChildLabel && (
        <button className="btn btn-primary btn-sm" onClick={onAddChild}>
          {addChildLabel}
        </button>
      )}
    </div>
  );
};

export default InlineEditableTitle;
