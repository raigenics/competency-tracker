/**
 * SkillsTableRow - Single row in skills table with inline edit support
 * Matches UIUpdates.html styling exactly
 * 
 * Features:
 * - Display mode: Checkbox | Skill Name | Alias | Edit/Delete buttons
 * - Edit mode: Checkbox (disabled) | Input boxes | Save/Cancel buttons
 * - ENTER saves, ESC cancels
 * - Alias: comma-separated string (split/trim on save)
 * - Checkbox for bulk selection
 * 
 * Alias format from backend:
 * - aliases: [{id, text, source, confidenceScore}, ...]
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Pencil, Trash2, Check, X } from 'lucide-react';

const SkillsTableRow = ({
  skill,
  onSave,
  onDelete,
  disabled = false,
  isSelected = false,
  onSelectChange
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(skill.name);
  const [editAlias, setEditAlias] = useState('');
  const nameInputRef = useRef(null);

  // Format aliases for display/edit (extract text from alias objects)
  const formatAliases = useCallback((aliases) => {
    if (!aliases || !Array.isArray(aliases)) return '';
    return aliases.map(a => typeof a === 'object' ? a.text : a).filter(Boolean).join(', ');
  }, []);

  // Initialize edit values from skill
  useEffect(() => {
    setEditName(skill.name);
    setEditAlias(formatAliases(skill.aliases));
  }, [skill, formatAliases]);

  // Focus name input when entering edit mode
  useEffect(() => {
    if (isEditing && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [isEditing]);

  const handleEdit = useCallback(() => {
    if (disabled) return;
    setEditName(skill.name);
    setEditAlias(formatAliases(skill.aliases));
    setIsEditing(true);
  }, [skill, formatAliases, disabled]);

  const handleSave = useCallback(() => {
    const trimmedName = editName.trim();
    if (!trimmedName) {
      // Don't allow empty skill name
      return;
    }

    // Parse new alias texts from comma-separated input
    const newAliasTexts = editAlias
      .split(',')
      .map(a => a.trim())
      .filter(a => a.length > 0);

    // Get existing aliases (with IDs)
    const existingAliases = skill.aliases || [];
    
    // Build updated aliases array:
    // - Keep existing aliases that still have matching text
    // - Add new aliases without ID
    const updatedAliases = [];
    const existingTextsLower = new Set(existingAliases.map(a => a.text.toLowerCase()));
    const newTextsLower = new Set(newAliasTexts.map(t => t.toLowerCase()));
    
    // Keep existing aliases that are still in the new list
    for (const existing of existingAliases) {
      if (newTextsLower.has(existing.text.toLowerCase())) {
        updatedAliases.push(existing);
      }
    }
    
    // Add new aliases (without ID - will be created)
    for (const text of newAliasTexts) {
      if (!existingTextsLower.has(text.toLowerCase())) {
        updatedAliases.push({ text }); // No ID = new alias
      }
    }
    
    // Find removed aliases (had ID, no longer in list)
    const removedAliasIds = existingAliases
      .filter(a => !newTextsLower.has(a.text.toLowerCase()))
      .map(a => a.id);

    onSave({
      ...skill,
      name: trimmedName,
      aliases: updatedAliases,
      _removedAliasIds: removedAliasIds // Hidden field for parent to process
    });
    setIsEditing(false);
  }, [editName, editAlias, skill, onSave]);

  const handleCancel = useCallback(() => {
    setEditName(skill.name);
    setEditAlias(formatAliases(skill.aliases));
    setIsEditing(false);
  }, [skill, formatAliases]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  }, [handleSave, handleCancel]);

  const handleDelete = useCallback(() => {
    onDelete(skill);
  }, [skill, onDelete]);

  const handleCheckboxChange = useCallback((e) => {
    if (onSelectChange) {
      onSelectChange(skill.id, e.target.checked);
    }
  }, [skill.id, onSelectChange]);

  // Display aliases (comma-separated texts)
  const displayAlias = formatAliases(skill.aliases) || '-';

  if (isEditing) {
    return (
      <tr data-skill-id={skill.id}>
        <td style={{ textAlign: 'center' }}>
          <input
            type="checkbox"
            checked={isSelected}
            disabled
            title="Cannot change selection while editing"
          />
        </td>
        <td>
          <input
            ref={nameInputRef}
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Skill name"
          />
        </td>
        <td>
          <input
            type="text"
            value={editAlias}
            onChange={(e) => setEditAlias(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Comma-separated aliases"
          />
        </td>
        <td>
          <div className="skill-actions">
            <button className="btn-save" onClick={handleSave}>
              <Check size={14} />
              Save
            </button>
            <button className="btn-cancel" onClick={handleCancel}>
              <X size={14} />
              Cancel
            </button>
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr data-skill-id={skill.id} className={isSelected ? 'selected' : ''}>
      <td style={{ textAlign: 'center' }}>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={handleCheckboxChange}
          disabled={disabled}
        />
      </td>
      <td>{skill.name}</td>
      <td>{displayAlias}</td>
      <td>
        <div className="skill-actions">
          <button className="btn-edit" onClick={handleEdit} disabled={disabled}>
            <Pencil size={14} />
            Edit
          </button>
          <button className="btn-delete" onClick={handleDelete} disabled={disabled}>
            <Trash2 size={14} />
            Delete
          </button>
        </div>
      </td>
    </tr>
  );
};

export default SkillsTableRow;
