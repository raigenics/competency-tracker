/**
 * DeleteSelectedModal - Confirmation modal for bulk delete operations
 * Extends the pattern from DeleteConfirmModal for multiple items
 */
import React from 'react';

const DeleteSelectedModal = ({
  isOpen,
  onClose,
  onConfirm,
  selectedCount,
  itemLabel = 'skill'
}) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  const pluralLabel = selectedCount === 1 ? itemLabel : `${itemLabel}s`;

  return (
    <div className="modal-overlay active" onClick={handleOverlayClick}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">Delete Selected {pluralLabel}?</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <p>
            Are you sure you want to delete <strong>{selectedCount} {pluralLabel}</strong>?
          </p>
          <p style={{ marginTop: '8px', color: 'var(--text-secondary)', fontSize: '13px' }}>
            This action cannot be undone.
          </p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-danger" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  );
};

export default DeleteSelectedModal;
