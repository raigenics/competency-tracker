/**
 * TwoPaneLayout - Reusable two-column layout primitive
 * 
 * Provides a container with two panes (left/right) that:
 * - Fills available vertical space within the parent container
 * - Supports independent scrolling per pane
 * - Supports optional sticky headers per pane
 * - Uses flexbox for proper height distribution
 * 
 * Usage:
 * ```jsx
 * <TwoPaneLayout
 *   leftWidth="520px"
 *   leftScrollable={true}
 *   rightScrollable={true}
 *   leftHeader={<div>Tree Header</div>}
 *   leftPane={<TreeContent />}
 *   rightPane={<DetailsContent />}
 *   gap="14px"
 * />
 * ```
 * 
 * @module layouts/TwoPaneLayout
 */
import React from 'react';

/**
 * TwoPaneLayout Component
 * 
 * @param {Object} props
 * @param {string} [props.leftWidth='520px'] - Width of the left pane (CSS value)
 * @param {boolean} [props.leftScrollable=true] - Enable scrolling in left pane body
 * @param {boolean} [props.rightScrollable=false] - Enable scrolling in right pane body
 * @param {React.ReactNode} [props.leftHeader] - Optional sticky header for left pane
 * @param {React.ReactNode} [props.rightHeader] - Optional sticky header for right pane
 * @param {React.ReactNode} props.leftPane - Content for left pane body
 * @param {React.ReactNode} props.rightPane - Content for right pane body
 * @param {string} [props.gap='14px'] - Gap between panes (CSS value)
 * @param {string} [props.className] - Additional CSS classes for container
 * @param {string} [props.minHeight='400px'] - Minimum height of the layout
 * @param {string} [props.maxHeight] - Optional max height (defaults to fill available space)
 * @param {string} [props.leftPaneClassName] - Additional CSS classes for left pane
 * @param {string} [props.rightPaneClassName] - Additional CSS classes for right pane
 */
const TwoPaneLayout = ({
  leftWidth = '520px',
  leftScrollable = true,
  rightScrollable = false,
  leftHeader = null,
  rightHeader = null,
  leftPane,
  rightPane,
  gap = '14px',
  className = '',
  minHeight = '400px',
  maxHeight,
  leftPaneClassName = '',
  rightPaneClassName = '',
}) => {
  // Container style - uses flex to distribute height
  const containerStyle = {
    display: 'grid',
    gridTemplateColumns: `${leftWidth} 1fr`,
    gap,
    alignItems: 'stretch',
    minHeight,
    width: '100%',
    minWidth: 0,
    // Use flex-1 approach: fill available space up to a reasonable max
    // The parent (page content area) determines the actual available height
    ...(maxHeight && { maxHeight }),
  };

  // Pane wrapper style - flex column to separate header from body
  const paneWrapperStyle = {
    display: 'flex',
    flexDirection: 'column',
    minHeight: 0, // Critical: allows flex children to shrink below content size
    maxHeight: 'inherit',
  };

  // Scrollable body style
  const scrollableBodyStyle = {
    flex: '1 1 auto',
    minHeight: 0, // Critical for flex scroll containers
    overflowY: 'auto',
    overflowX: 'hidden',
  };

  // Non-scrollable body style
  const staticBodyStyle = {
    flex: '1 1 auto',
    minHeight: 0,
    overflow: 'visible',
  };

  return (
    <div 
      className={`two-pane-layout ${className}`.trim()}
      style={containerStyle}
      data-testid="two-pane-layout"
    >
      {/* Left Pane */}
      <div 
        className={`two-pane-left ${leftPaneClassName}`.trim()}
        style={paneWrapperStyle}
        data-testid="two-pane-left"
      >
        {leftHeader && (
          <div 
            className="two-pane-left-header"
            style={{ flexShrink: 0 }}
            data-testid="two-pane-left-header"
          >
            {leftHeader}
          </div>
        )}
        <div 
          className="two-pane-left-body"
          style={leftScrollable ? scrollableBodyStyle : staticBodyStyle}
          data-testid="two-pane-left-body"
        >
          {leftPane}
        </div>
      </div>

      {/* Right Pane */}
      <div 
        className={`two-pane-right ${rightPaneClassName}`.trim()}
        style={paneWrapperStyle}
        data-testid="two-pane-right"
      >
        {rightHeader && (
          <div 
            className="two-pane-right-header"
            style={{ flexShrink: 0 }}
            data-testid="two-pane-right-header"
          >
            {rightHeader}
          </div>
        )}
        <div 
          className="two-pane-right-body"
          style={rightScrollable ? scrollableBodyStyle : staticBodyStyle}
          data-testid="two-pane-right-body"
        >
          {rightPane}
        </div>
      </div>
    </div>
  );
};

export default TwoPaneLayout;
