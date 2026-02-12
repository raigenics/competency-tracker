/**
 * AddSkillRow - Inline add row for creating new skills in SkillsTable
 * Matches the edit row styling from SkillsTableRow
 * 
 * Features:
 * - Empty row at top of table for adding new skill
 * - Skill Name (required) and Alias (optional, comma-separated) inputs
 * - Save/Cancel actions
 * - ENTER saves, ESC cancels
 * - Auto-focus on name input
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Check, X } from 'lucide-react';

const AddSkillRow = ({
  onSave,
  onCancel
}) => {
  const [name, setName] = useState('');
  const [alias, setAlias] = useState('');
  const nameInputRef = useRef(null);

  // Auto-focus name input on mount
  useEffect(() => {
    if (nameInputRef.current) {
      nameInputRef.current.focus();
    }
  }, []);

  const handleSave = useCallback(() => {
    const trimmedName = name.trim();
    if (!trimmedName) {
      // Don't allow empty skill name
      nameInputRef.current?.focus();
      return;
    }

    // Parse aliases from comma-separated input
    const aliases = alias
      .split(',')
      .map(a => a.trim())
      .filter(a => a.length > 0)
      .map(text => ({ text })); // New aliases without ID

    // Create new skill with temporary ID
    const newSkill = {
      id: `temp-${Date.now()}`,
      rawId: null, // No backend ID yet
      type: 'skill',
      name: trimmedName,
      aliases,
      createdAt: new Date().toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      }),
      createdBy: 'system',
      employeeCount: 0,
      _isNew: true // Flag for parent to know this is a new skill
    };

    onSave(newSkill);
  }, [name, alias, onSave]);

  const handleCancel = useCallback(() => {
    onCancel();
  }, [onCancel]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  }, [handleSave, handleCancel]);

  return (
    <tr className="add-skill-row" style={{ backgroundColor: 'var(--background-secondary, #f8f9fa)' }}>
      <td style={{ textAlign: 'center' }}>
        {/* Empty checkbox cell for alignment */}
      </td>
      <td>
        <input
          ref={nameInputRef}
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter skill name"
        />
      </td>
      <td>
        <input
          type="text"
          value={alias}
          onChange={(e) => setAlias(e.target.value)}
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
};

export default AddSkillRow;
