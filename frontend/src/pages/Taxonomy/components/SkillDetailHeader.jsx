import React from 'react';
import { ArrowRight } from 'lucide-react';
import '../CapabilityOverview.css';

/**
 * SkillDetailHeader - Presentational component for skill detail panel header
 * 
 * Renders:
 * - Breadcrumb navigation (Category → Sub-Category → Skill)
 * - Skill title
 * - View Employees CTA button
 * 
 * Props:
 * - categoryName: string - Parent category name
 * - subCategoryName: string - Parent subcategory name
 * - skillName: string - Selected skill name
 * - employeeCount: number - Number of employees with this skill
 * - onViewEmployees: function - Callback when View Employees button is clicked
 * - isDisabled: boolean - Whether the button is disabled
 */
const SkillDetailHeader = ({
  _categoryName,
  _subCategoryName,
  skillName,
  employeeCount,
  onViewEmployees,
  isDisabled = false
}) => {
  return (
    <div className="co-skill-header">
      <div className="co-skill-header-left">
        {/* <div className="co-skill-header-crumbs">
          Capability Structure → {categoryName}
          {subCategoryName && ` → ${subCategoryName}`}
          {' → '}<b>{skillName}</b>
        </div> */}
        <h1 className="co-skill-header-title">{skillName}</h1>
      </div>
      <div className="co-skill-header-right">
        <button
          className="co-skill-header-btn"
          onClick={onViewEmployees}
          disabled={isDisabled || employeeCount === 0}
          type="button"
          aria-label="View employees"
        >
          <ArrowRight className="co-skill-header-btn-icon" aria-hidden="true" />
          View Employees ({employeeCount})
        </button>
      </div>
    </div>
  );
};

export default SkillDetailHeader;
