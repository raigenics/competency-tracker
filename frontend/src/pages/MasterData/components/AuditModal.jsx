/**
 * AuditModal - Display audit trail/history
 * Matches ContentPage.html modal structure exactly
 */
import React from 'react';

const AuditModal = ({
  isOpen,
  onClose,
  itemName = 'Item',
  auditLogs = []
}) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  // Default dummy audit logs if none provided
  const displayLogs = auditLogs.length > 0 ? auditLogs : [
    {
      action: 'Created',
      user: 'John Smith',
      timestamp: '2024-01-15 09:30:00',
      details: 'Item was created'
    },
    {
      action: 'Updated',
      user: 'Jane Doe',
      timestamp: '2024-01-20 14:15:00',
      details: 'Description was modified'
    },
    {
      action: 'Updated',
      user: 'Mike Johnson',
      timestamp: '2024-02-01 11:45:00',
      details: 'Status changed to Active'
    }
  ];

  const getActionIcon = (action) => {
    switch (action.toLowerCase()) {
      case 'created':
        return '🆕';
      case 'updated':
        return '✏️';
      case 'deleted':
        return '🗑️';
      case 'restored':
        return '♻️';
      default:
        return '📝';
    }
  };

  const getActionColor = (action) => {
    switch (action.toLowerCase()) {
      case 'created':
        return 'var(--success)';
      case 'updated':
        return 'var(--primary)';
      case 'deleted':
        return 'var(--danger)';
      case 'restored':
        return 'var(--info)';
      default:
        return 'var(--text-secondary)';
    }
  };

  return (
    <div className="modal-overlay active" onClick={handleOverlayClick}>
      <div className="modal modal-large">
        <div className="modal-header">
          <div className="modal-title">📋 Audit History - {itemName}</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="audit-timeline">
            {displayLogs.map((log, index) => (
              <div key={index} className="audit-item">
                <div className="audit-icon" style={{ background: getActionColor(log.action) }}>
                  {getActionIcon(log.action)}
                </div>
                <div className="audit-content">
                  <div className="audit-header">
                    <span className="audit-action" style={{ color: getActionColor(log.action) }}>
                      {log.action}
                    </span>
                    <span className="audit-timestamp">{log.timestamp}</span>
                  </div>
                  <div className="audit-user">by {log.user}</div>
                  {log.details && (
                    <div className="audit-details">{log.details}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
          {displayLogs.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <div className="empty-text">No audit history available</div>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default AuditModal;
