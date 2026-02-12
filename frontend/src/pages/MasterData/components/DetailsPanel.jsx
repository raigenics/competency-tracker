/**
 * DetailsPanel - Right panel showing selected node details
 * Matches ContentPage.html structure exactly
 * 
 * Updated: Now supports custom header content via headerContent prop
 * for inline editable titles, and headerActions for action buttons
 */
import React from 'react';

const DetailsPanel = ({
  title = 'Select an item to view details',
  subtitle,
  children,
  onEdit,
  onDelete,
  onAddChild,
  addChildLabel,
  showActions = false,
  // New: Allow custom header content (for InlineEditableTitle)
  headerContent = null,
  // New: Allow action buttons in header (Download Template, Import, Add)
  headerActions = null
}) => {
  return (
    <div className="details-panel">
      <div className="details-header">
        <div className="content-title-section">
          {headerContent ? (
            headerContent
          ) : (
            <div className="details-title">{title}</div>
          )}
          {subtitle && <div className="details-subtitle">{subtitle}</div>}
        </div>
        {headerActions && (
          <div className="action-buttons">
            {headerActions}
          </div>
        )}
      </div>
      <div className="details-content">
        <div style={{ maxWidth: '1400px', width: '100%' }}>
          {children}
        </div>
      </div>
      {showActions && (
        <div className="details-actions">
          {onEdit && (
            <button className="btn btn-secondary" onClick={onEdit}>
              ✏️ Edit
            </button>
          )}
          {onDelete && (
            <button className="btn btn-danger" onClick={onDelete}>
              🗑️ Delete
            </button>
          )}
          {onAddChild && addChildLabel && (
            <button className="btn btn-primary" onClick={onAddChild}>
              {addChildLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// Sub-components for building details content - matching HTML exactly
export const InfoSection = ({ title, children, action }) => (
  <div className="info-section">
    <div className="info-section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
      <div className="info-section-title" style={{ margin: 0 }}>{title}</div>
      {action && <div className="info-section-action">{action}</div>}
    </div>
    {children}
  </div>
);

export const InfoBox = ({ children, style }) => (
  <div className="info-box" style={style}>
    {children}
  </div>
);

export const InfoGrid = ({ children }) => (
  <div className="info-grid">
    {children}
  </div>
);

export const InfoItem = ({ label, value, style }) => (
  <div className="info-item" style={style}>
    <div className="info-label">{label}</div>
    <div className="info-value">{value}</div>
  </div>
);

export const StatsGrid = ({ children }) => (
  <div className="stats-grid">
    {children}
  </div>
);

export const StatCard = ({ label, value }) => (
  <div className="stat-card">
    <div className="stat-label">{label}</div>
    <div className="stat-value">{value}</div>
  </div>
);

export const Alert = ({ type = 'info', icon, children }) => (
  <div className={`alert alert-${type}`}>
    {icon && <span className="alert-icon">{icon}</span>}
    <div>{children}</div>
  </div>
);

// Empty state component matching HTML
export const EmptyState = ({ onAddRoot, addButtonLabel = '➕ Add New Category' }) => (
  <div className="empty-state">
    <div className="empty-icon">📋</div>
    <h3>No Item Selected</h3>
    <p>Select an item from the tree to view and edit its details</p>
    <div className="empty-actions">
      <p><strong>Quick Actions:</strong></p>
      <button className="btn btn-primary" onClick={onAddRoot}>
        {addButtonLabel}
      </button>
    </div>
  </div>
);

export default DetailsPanel;
