/**
 * Skills Validation Module
 * 
 * SRP: Responsible solely for validating employee skills.
 * Does NOT handle state management, API calls, or UI rendering.
 */

/**
 * Checks if a skill row is complete (has all required fields)
 * @param {Object} skill - Skill row object
 * @returns {boolean}
 */
export function isSkillRowComplete(skill) {
  if (!skill) return false;
  
  // Required fields: skill_id, proficiency, yearsExperience
  const hasSkillId = skill.skill_id != null;
  const hasProficiency = Boolean(skill.proficiency && skill.proficiency.trim() !== '');
  const hasExperience = skill.yearsExperience !== '' && skill.yearsExperience !== null && skill.yearsExperience !== undefined;
  
  return hasSkillId && hasProficiency && hasExperience;
}

/**
 * Validates that employee has at least one complete skill row
 * 
 * @param {Array} skills - Array of skill row objects
 * @returns {{ isValid: boolean, error: string|null, validSkillCount: number }}
 */
export function validateEmployeeSkills(skills) {
  if (!skills || !Array.isArray(skills)) {
    return {
      isValid: false,
      error: 'Add at least one skill.',
      validSkillCount: 0
    };
  }
  
  // Count complete skill rows
  const completeSkills = skills.filter(isSkillRowComplete);
  
  if (completeSkills.length === 0) {
    return {
      isValid: false,
      error: 'Add at least one skill with proficiency and experience.',
      validSkillCount: 0
    };
  }
  
  return {
    isValid: true,
    error: null,
    validSkillCount: completeSkills.length
  };
}

export default { validateEmployeeSkills, isSkillRowComplete };
