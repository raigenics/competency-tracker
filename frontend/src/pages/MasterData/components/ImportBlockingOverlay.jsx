/**
 * ImportBlockingOverlay - Full-page blocking overlay during import operations
 * 
 * Features:
 * - Blocks ALL user interaction (clicks, scrolling, keyboard)
 * - Shows spinner animation
 * - Shows status message from backend
 * - Cannot be closed by user (no ESC, no click-outside)
 * - High z-index to cover everything
 */
import React, { useEffect } from 'react';

const ImportBlockingOverlay = ({
  isVisible,
  message = 'Processing...',
  title = 'Import in progress'
}) => {
  // Block keyboard events (especially ESC)
  useEffect(() => {
    if (!isVisible) return;
    
    const handleKeyDown = (e) => {
      // Block ESC and other keys while overlay is visible
      e.preventDefault();
      e.stopPropagation();
    };
    
    // Prevent scrolling on body
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', handleKeyDown, true);
    
    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        // Block all pointer events on children except our modal
        pointerEvents: 'all',
      }}
      // Prevent click-through
      onClick={(e) => e.stopPropagation()}
    >
      <div
        style={{
          backgroundColor: 'var(--surface, #ffffff)',
          borderRadius: '12px',
          padding: '32px 48px',
          maxWidth: '450px',
          width: '90%',
          textAlign: 'center',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        }}
      >
        {/* Spinner */}
        <div
          style={{
            width: '48px',
            height: '48px',
            margin: '0 auto 24px',
            border: '4px solid var(--border, #e0e0e0)',
            borderTopColor: 'var(--primary, #6366f1)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
        
        {/* Title */}
        <h2
          style={{
            margin: '0 0 8px',
            fontSize: '20px',
            fontWeight: 600,
            color: 'var(--text-primary, #1a1a2e)',
          }}
        >
          {title}
        </h2>
        
        {/* Subtitle */}
        <p
          style={{
            margin: '0 0 24px',
            fontSize: '14px',
            color: 'var(--text-secondary, #6b7280)',
            lineHeight: 1.5,
          }}
        >
          This may take a few minutes.<br />
          Please don't refresh or close this tab.
        </p>
        
        {/* Status message */}
        <p
          style={{
            margin: 0,
            fontSize: '14px',
            fontWeight: 500,
            color: 'var(--primary, #6366f1)',
            minHeight: '20px',
          }}
        >
          {message}
        </p>
      </div>
      
      {/* CSS animation for spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default ImportBlockingOverlay;
