/**
 * SkillProficiencyBreakdown - Presentational component for proficiency distribution
 * 
 * Displays:
 * - Section title "Proficiency Breakdown" with Avg/Median meta on right
 * - Stacked horizontal bar with 5 segments (one per level)
 * - Legend items for all 5 levels with color swatch, label, and count
 * - Footnote text
 * 
 * Props:
 * - counts: { Novice: number, "Adv. Beginner": number, Competent: number, Proficient: number, Expert: number }
 * - avg: number (1-5) rounded to 1 decimal
 * - median: number (1-5)
 * - total: number - total employees
 * - isLoading: boolean
 * 
 * This is a stateless presentational component with no business logic or API calls.
 */
import React from 'react';
import '../CapabilityOverview.css';

// Proficiency levels in display order
const PROFICIENCY_LEVELS = [
  { key: 'Novice', label: 'Novice', cssClass: 'co-pb-s1' },
  { key: 'Adv. Beginner', label: 'Adv. Beginner', cssClass: 'co-pb-s2' },
  { key: 'Competent', label: 'Competent', cssClass: 'co-pb-s3' },
  { key: 'Proficient', label: 'Proficient', cssClass: 'co-pb-s4' },
  { key: 'Expert', label: 'Expert', cssClass: 'co-pb-s5' }
];

// Default counts object with all levels set to 0
const DEFAULT_COUNTS = {
  'Novice': 0,
  'Adv. Beginner': 0,
  'Competent': 0,
  'Proficient': 0,
  'Expert': 0
};

const SkillProficiencyBreakdown = ({
  counts = null,
  avg = null,
  median = null,
  total = 0,
  isLoading = false
}) => {
  // Build safe counts object - merge defaults with provided counts (if any)
  const safeCounts = { ...DEFAULT_COUNTS, ...(counts ?? {}) };

  // Calculate percentage widths for stacked bar (guard division by zero)
  const getPercentage = (count) => {
    if (!total || total === 0) return 0;
    return (count / total) * 100;
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="co-pb-wrap">
        <div className="co-pb-header">
          <div>
            <p className="co-pb-title">Proficiency Breakdown</p>
            <div className="co-pb-meta">
              <span className="co-skeleton" style={{ width: '120px' }}></span>
            </div>
          </div>
          <div className="co-pb-meta co-pb-meta-right">
            <span className="co-skeleton" style={{ width: '60px' }}></span>
            <span className="co-skeleton" style={{ width: '60px' }}></span>
          </div>
        </div>
        <div className="co-pb-stacked co-pb-stacked--loading">
          <span className="co-skeleton" style={{ width: '100%', height: '12px' }}></span>
        </div>
        <div className="co-pb-legend">
          {PROFICIENCY_LEVELS.map((level) => (
            <div key={level.key} className="co-pb-leg-item co-pb-leg-item--loading">
              <span className="co-skeleton" style={{ width: '10px', height: '10px' }}></span>
              <span className="co-skeleton" style={{ width: '60px' }}></span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="co-pb-wrap">
      {/* Header with title and Avg/Median */}
      <div className="co-pb-header">
        <div>
          <p className="co-pb-title">Proficiency Breakdown</p>
          <div className="co-pb-meta">
            Distribution across proficiency levels.
          </div>
        </div>
        <div className="co-pb-meta co-pb-meta-right">
          <div><b className="co-pb-meta-bold">Avg:</b> {avg !== null ? avg.toFixed(1) : '—'}</div>
          <div>Median: {median !== null ? median : '—'}</div>
        </div>
      </div>

      {/* Stacked bar */}
      <div 
        className="co-pb-stacked" 
        role="img" 
        aria-label="Proficiency distribution stacked bar"
      >
        {PROFICIENCY_LEVELS.map((level) => {
          const count = safeCounts[level.key];
          const percentage = getPercentage(count);
          if (percentage === 0) return null;
          return (
            <div
              key={level.key}
              className={`co-pb-seg ${level.cssClass}`}
              style={{ width: `${percentage}%` }}
              title={`${level.label}: ${count}`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="co-pb-legend">
        {PROFICIENCY_LEVELS.map((level) => (
          <div key={level.key} className="co-pb-leg-item">
            <span className={`co-pb-swatch ${level.cssClass}`}></span>
            <div className="co-pb-leg-text">
              {level.label}<br />
              <b>{safeCounts[level.key]}</b>
            </div>
          </div>
        ))}
      </div>

      {/* Footnote */}
      <div className="co-pb-foot">
        Keep this screen insight-first. The employee list belongs to the next screen (on clicking "View Employees").
      </div>
    </div>
  );
};

export default SkillProficiencyBreakdown;
