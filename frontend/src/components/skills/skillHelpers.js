/**
 * Helper functions for skill-related operations.
 * Extracted from EmployeeSkillsTab for react-refresh compatibility.
 */

/**
 * Create a new empty skill row with default values.
 * NOTE: lastUsed is now split into lastUsedMonth and lastUsedYear per designer spec.
 */
export const createEmptySkill = () => ({
  id: Date.now() + Math.random(),
  skill_id: null,
  skillName: '',
  proficiency: '',
  yearsExperience: '',
  lastUsedMonth: '',      // Month dropdown (01-12) per designer spec
  lastUsedYear: '',       // Year input (YYYY) per designer spec  
  startedFrom: '',        // Date field - restored (was accidentally removed)
  certification: ''
});

/**
 * Validate a single skill row
 * @param {Object} skill 
 * @returns {Object} Errors object (empty if valid)
 */
export const validateSkillRow = (skill) => {
  const errors = {};
  
  // Skill must be selected from suggestions (has skill_id)
  if (!skill.skill_id) {
    errors.skillName = 'Please select a skill from the list';
  }
  
  // Proficiency is required
  if (!skill.proficiency) {
    errors.proficiency = 'Proficiency is required';
  }
  
  // Experience is required
  if (!skill.yearsExperience && skill.yearsExperience !== 0) {
    errors.yearsExperience = 'Experience is required';
  } else if (skill.yearsExperience < 0) {
    errors.yearsExperience = 'Invalid experience';
  }
  
  // Certification is optional - no validation needed
  
  return errors;
};
