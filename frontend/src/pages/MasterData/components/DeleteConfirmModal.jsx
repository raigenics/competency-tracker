/**
 * DeleteConfirmModal - Confirmation modal for deleting items
 * Matches ContentPage.html modal structure exactly
 */
import React from 'react';

const DeleteConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  itemName = 'this item'
}) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay active" onClick={handleOverlayClick}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">Confirm Deletion</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <p>Are you sure you want to delete <strong>{itemName}</strong>?</p>
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

export default DeleteConfirmModal;
