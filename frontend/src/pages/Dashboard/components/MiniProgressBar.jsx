/**
 * MiniProgressBar - Subtle progress indicator for stat blocks
 * 
 * Local component for Dashboard "Skill Update Activity" card only.
 * Do NOT use in other parts of the application.
 * 
 * @param {Object} props
 * @param {number} props.value - Progress value (0-100)
 * @param {string} props.variant - 'success' | 'warn' | 'danger' (determines fill color)
 * @param {boolean} props.showPercent - Whether to show % label on right (default: true)
 */
const MiniProgressBar = ({ value = 0, variant = 'success', showPercent = true }) => {
  // Clamp value between 0 and 100
  const clampedValue = Math.min(100, Math.max(0, value || 0));
  
  // Map variant to CSS class
  const variantClass = {
    success: 'db-progress-success',
    warn: 'db-progress-warn',
    danger: 'db-progress-danger'
  }[variant] || 'db-progress-success';
  
  return (
    <div className="db-progress-row">
      <div className="db-progress-track">
        <div 
          className={`db-progress-fill ${variantClass}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
      {showPercent && (
        <span className="db-progress-pct">{clampedValue}%</span>
      )}
    </div>
  );
};

export default MiniProgressBar;
