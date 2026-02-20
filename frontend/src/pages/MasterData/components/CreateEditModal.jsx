/**
 * CreateEditModal - Modal for creating/editing master data items
 * Matches ContentPage.html modal structure exactly
 */
import React, { useState } from 'react';

const CreateEditModal = ({
  isOpen,
  onClose,
  onSave,
  onSubmit, // Alternative prop name for save handler
  title,
  itemType, // Alternative for title: 'category', 'subcategory', 'skill'
  mode = 'create', // 'create' or 'edit'
  initialName = '',
  initialDescription = '',
  showParentSelect = false,
  parentOptions = [],
  selectedParent = '',
  defaultParentId = '',
  isSaving = false, // Show loading state on save button
  error = null, // Error message to display
}) => {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);
  const [parent, setParent] = useState(selectedParent || defaultParentId);
  // Track previous props for render-time sync
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  const [prevInitialName, setPrevInitialName] = useState(initialName);
  const [prevInitialDescription, setPrevInitialDescription] = useState(initialDescription);
  const [prevSelectedParent, setPrevSelectedParent] = useState(selectedParent);

  // Sync form values when modal opens or initial values change (React recommended pattern)
  if (isOpen && (
    isOpen !== prevIsOpen ||
    initialName !== prevInitialName ||
    initialDescription !== prevInitialDescription ||
    selectedParent !== prevSelectedParent
  )) {
    setPrevIsOpen(isOpen);
    setPrevInitialName(initialName);
    setPrevInitialDescription(initialDescription);
    setPrevSelectedParent(selectedParent);
    setName(initialName);
    setDescription(initialDescription);
    setParent(selectedParent || defaultParentId);
  } else if (isOpen !== prevIsOpen) {
    setPrevIsOpen(isOpen);
  }

  // Resolve the display title
  const displayTitle = title || (itemType ? `${mode === 'edit' ? 'Edit' : 'Add'} ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}` : 'Add Item');
  
  // Use onSubmit or onSave (onSubmit takes precedence)
  const saveHandler = onSubmit || onSave;

  const handleSave = () => {
    if (saveHandler) {
      saveHandler({ name, description, parent });
    }
    // Don't close here - let the handler decide (for async operations)
    if (!onSubmit) {
      onClose();
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  // Determine if we should show parent select
  const shouldShowParentSelect = showParentSelect || (parentOptions && parentOptions.length > 0);

  return (
    <div className="modal-overlay active" onClick={handleOverlayClick}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">{displayTitle}</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">
              Name <span className="required">*</span>
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isSaving}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              placeholder="Enter description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isSaving}
            />
            <div className="form-help">Optional: Provide additional context</div>
          </div>
          {shouldShowParentSelect && (
            <div className="form-group">
              <label className="form-label">Parent</label>
              <select
                className="form-select"
                value={parent}
                onChange={(e) => setParent(e.target.value)}
                disabled={isSaving}
              >
                {parentOptions.map(opt => (
                  <option key={opt.value || opt.id} value={opt.value || opt.id}>{opt.label || opt.name}</option>
                ))}
              </select>
            </div>
          )}
          {error && (
            <div className="form-error" style={{ 
              color: 'var(--danger-color, #dc3545)', 
              fontSize: '13px', 
              marginTop: '8px',
              padding: '8px 12px',
              backgroundColor: 'var(--danger-bg, #f8d7da)',
              borderRadius: '4px'
            }}>
              {error}
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={isSaving}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateEditModal;
