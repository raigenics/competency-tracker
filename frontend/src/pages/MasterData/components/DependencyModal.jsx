/**
 * DependencyModal - Warning modal shown when item has dependencies
 * Matches ContentPage.html modal structure exactly
 */
import React from 'react';

const DependencyModal = ({
  isOpen,
  onClose,
  itemName: _itemName = 'this item',
  dependencies = []
}) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  // Default dummy dependencies if none provided
  const displayDependencies = dependencies.length > 0 ? dependencies : [
    { icon: '📂', label: '12 Sub-Categories' },
    { icon: '🏷️', label: '156 Skills' },
    { icon: '👥', label: '45 Employees' }
  ];

  return (
    <div className="modal-overlay active" onClick={handleOverlayClick}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">⚠️ Cannot Delete</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="alert alert-error">
            <span className="alert-icon">⚠️</span>
            <div>
              <strong>This item has dependencies and cannot be deleted.</strong>
            </div>
          </div>
          <div className="info-section" style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '12px' }}>Dependencies found:</h3>
            <ul className="dependency-list">
              {displayDependencies.map((dep, index) => (
                <li key={index} className="dependency-item">
                  {dep.icon} {dep.label}
                </li>
              ))}
            </ul>
          </div>
          <p style={{ marginTop: '16px', color: 'var(--text-secondary)', fontSize: '13px' }}>
            To delete this item, you must first remove all sub-items and employee associations.
          </p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default DependencyModal;
