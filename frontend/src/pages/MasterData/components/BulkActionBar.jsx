/**
 * BulkActionBar - Contextual action bar for bulk operations
 * Appears when 1+ rows are selected in a table
 * 
 * Features:
 * - Shows selected count pill
 * - Delete Selected button (danger)
 * - Clear selection button
 */
import React from 'react';
import { Trash2, X } from 'lucide-react';

const BulkActionBar = ({
  selectedCount,
  onDeleteSelected,
  onClearSelection
}) => {
  if (selectedCount === 0) return null;

  return (
    <div className="bulk-action-bar">
      <span className="selected-count-pill">
        {selectedCount} selected
      </span>
      <button 
        className="btn btn-danger btn-sm"
        onClick={onDeleteSelected}
      >
        <Trash2 size={14} />
        Delete Selected
      </button>
      <button 
        className="btn btn-secondary btn-sm"
        onClick={onClearSelection}
      >
        <X size={14} />
        Clear
      </button>
    </div>
  );
};

export default BulkActionBar;
