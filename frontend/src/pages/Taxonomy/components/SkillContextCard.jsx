import React from 'react';
import '../CapabilityOverview.css';

/**
 * SkillContextCard - Presentational component for skill context information.
 * Displays Category, Sub-Category, and Leading Sub-Segment in a card layout.
 * 
 * Props:
 *   @param {string} categoryName - The skill's category name
 *   @param {string} subCategoryName - The skill's sub-category name
 *   @param {string} leadingSubSegmentName - The leading sub-segment (highest employee count for this skill)
 *   @param {boolean} isLoading - Loading state for skeleton display
 */
const SkillContextCard = ({
  categoryName = '—',
  subCategoryName = '—',
  leadingSubSegmentName = '—',
  isLoading = false
}) => {
  // 3 rows: Category, Sub-Category, Leading Sub-Segment
  const rows = [
    { label: 'Category', value: categoryName || '—' },
    { label: 'Sub-Category', value: subCategoryName || '—' },
    { label: 'Leading Sub-Segment', value: leadingSubSegmentName || '—' }
  ];

  return (
    <div className="co-ctx-card">
      <p className="co-ctx-title">Skill Context</p>

      <div className="co-ctx-list">
        {rows.map(({ label, value }) => (
          <div key={label} className={`co-ctx-row ${isLoading ? 'co-ctx-row--loading' : ''}`}>
            <div className="co-ctx-label">{label}</div>
            <div className="co-ctx-value" title={value}>
              {isLoading ? (
                <span className="co-ctx-skeleton" />
              ) : (
                value
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SkillContextCard;
