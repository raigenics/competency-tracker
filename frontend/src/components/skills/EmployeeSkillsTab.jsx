/**
 * EmployeeSkillsTab Component
 * 
 * SRP: Renders the Skills tab content for Add Employee drawer.
 * Manages skill rows, validation, and user guidance.
 * 
 * NOTE: This is UI only - does NOT save to backend.
 */
import React, { useState, useCallback } from 'react';
import { SkillRowEditor } from './SkillRowEditor.jsx';
import { ProficiencyInfoTooltip } from './ProficiencyInfoTooltip.jsx';
import { useSkillSuggestions } from '../../hooks/useSkillSuggestions.js';
import { useProficiencyLevels } from '../../hooks/useProficiencyLevels.js';
import { SUPER_ADMIN_EMAIL } from '../../config/constants.js';
import { createEmptySkill } from './skillHelpers.js';

/**
 * @param {Object} props
 * @param {Array} props.skills - Current skills state
 * @param {Function} props.onSkillsChange - Callback when skills change
 * @param {Object} props.errors - Validation errors by skill id
 */
export function EmployeeSkillsTab({
  skills = [],
  onSkillsChange,
  errors = {}
}) {
  // Use skill suggestions hook
  const {
    suggestions,
    loading: skillsLoading,
    error: skillsError,
    search: searchSkills
  } = useSkillSuggestions();

  // Use proficiency levels hook (fetches from DB)
  const {
    levels: proficiencyLevels,
    options: proficiencyOptions
  } = useProficiencyLevels();

  // Current search query per row (for managing separate autocomplete states)
  const [currentSearchRowId, setCurrentSearchRowId] = useState(null);

  /**
   * Handle skill field change
   */
  const handleSkillChange = useCallback((skillId, field, value) => {
    const updatedSkills = skills.map(skill => {
      if (skill.id === skillId) {
        return { ...skill, [field]: value };
      }
      return skill;
    });
    onSkillsChange(updatedSkills);
  }, [skills, onSkillsChange]);

  /**
   * Handle skill selection from autocomplete
   */
  const handleSelectSkill = useCallback((rowId, suggestionData) => {
    const updatedSkills = skills.map(skill => {
      if (skill.id === rowId) {
        return {
          ...skill,
          skill_id: suggestionData.skill_id,
          skillName: suggestionData.skill_name,
          category_name: suggestionData.category_name,
          subcategory_name: suggestionData.subcategory_name
        };
      }
      return skill;
    });
    onSkillsChange(updatedSkills);
  }, [skills, onSkillsChange]);

  /**
   * Handle search for a specific row
   */
  const handleSearch = useCallback((rowId, query) => {
    setCurrentSearchRowId(rowId);
    searchSkills(query);
  }, [searchSkills]);

  /**
   * Add a new skill row
   */
  const handleAddSkill = useCallback(() => {
    const newSkill = createEmptySkill();
    onSkillsChange([...skills, newSkill]);
  }, [skills, onSkillsChange]);

  /**
   * Delete a skill row
   */
  const handleDeleteSkill = useCallback((skillId) => {
    if (skills.length <= 1) {
      // Keep at least one row - just clear it
      onSkillsChange([createEmptySkill()]);
      return;
    }
    const updatedSkills = skills.filter(s => s.id !== skillId);
    onSkillsChange(updatedSkills);
  }, [skills, onSkillsChange]);

  // Check if skill row can be deleted
  const canDeleteRow = skills.length > 1;

  return (
    <div className="form-section" data-testid="employee-skills-tab">
      <div className="section-header">
        <div className="section-title">Employee Skills</div>
        <div className="section-description">
          Add skills from the approved list below.
        </div>
      </div>

      {/* Info callout with admin contact */}
      <div className="info-callout" data-testid="skills-info-callout">
        <div className="info-callout-title">💡 Skill Selection</div>
        <div className="info-callout-text" data-testid="skills-info-message">
          Select skills from the approved list. If you don't find a skill, 
          email the admin at{' '}
          <a href={`mailto:${SUPER_ADMIN_EMAIL}`} data-testid="admin-email-link">
            {SUPER_ADMIN_EMAIL}
          </a>{' '}
          to request it be added.
        </div>
      </div>

      {/* Error loading skills */}
      {skillsError && (
        <div className="info-callout" style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
          <div className="info-callout-title" style={{ color: '#dc2626' }}>❌ Error</div>
          <div className="info-callout-text" style={{ color: '#dc2626' }}>{skillsError}</div>
        </div>
      )}

      {/* Skills table */}
      <div className="skills-table-container">
        <table className="skills-table" data-testid="skills-table">
          <thead>
            <tr>
              <th style={{ width: '36%' }}>Skill Name *</th>
              <th style={{ width: '11%' }}>
                Proficiency *{' '}
                <ProficiencyInfoTooltip levels={proficiencyLevels} />
              </th>
              <th style={{ width: '8%' }}>Exp (Yrs) *</th>
              <th style={{ width: '13%' }}>Last Used</th>
              <th style={{ width: '11%' }}>Started From</th>
              <th style={{ width: '15%' }}>Certification</th>
              <th style={{ width: '6%', textAlign: 'right' }}></th>
            </tr>
          </thead>
          <tbody>
            {skills.map((skill) => (
              <SkillRowEditor
                key={skill.id}
                skill={skill}
                onChange={handleSkillChange}
                onSelectSkill={handleSelectSkill}
                onDelete={handleDeleteSkill}
                suggestions={currentSearchRowId === skill.id ? suggestions : []}
                onSearch={(query) => handleSearch(skill.id, query)}
                loading={currentSearchRowId === skill.id && skillsLoading}
                proficiencies={proficiencyOptions}
                errors={errors[skill.id] || {}}
                canDelete={canDeleteRow}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Add skill button */}
      <button 
        className="add-skill-btn" 
        onClick={handleAddSkill}
        data-testid="add-skill-btn"
      >
        + Add Skill
      </button>
    </div>
  );
}

export default EmployeeSkillsTab;
