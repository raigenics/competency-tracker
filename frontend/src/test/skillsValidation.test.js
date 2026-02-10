/**
 * Skills Validation Module Tests
 * 
 * Tests for validating employee skills array
 */
import { describe, it, expect } from 'vitest';
import { validateEmployeeSkills, isSkillRowComplete } from '@/utils/skillsValidation.js';

describe('skillsValidation', () => {
  describe('isSkillRowComplete', () => {
    it('should return false for null/undefined skill', () => {
      expect(isSkillRowComplete(null)).toBe(false);
      expect(isSkillRowComplete(undefined)).toBe(false);
    });

    it('should return false for skill without skill_id', () => {
      const skill = {
        skill_id: null,
        proficiency: 'EXPERT',
        yearsExperience: 5
      };
      expect(isSkillRowComplete(skill)).toBe(false);
    });

    it('should return false for skill without proficiency', () => {
      const skill = {
        skill_id: 1,
        proficiency: '',
        yearsExperience: 5
      };
      expect(isSkillRowComplete(skill)).toBe(false);
    });

    it('should return false for skill without experience', () => {
      const skill = {
        skill_id: 1,
        proficiency: 'EXPERT',
        yearsExperience: ''
      };
      expect(isSkillRowComplete(skill)).toBe(false);
    });

    it('should return true for complete skill row', () => {
      const skill = {
        skill_id: 1,
        proficiency: 'EXPERT',
        yearsExperience: 5
      };
      expect(isSkillRowComplete(skill)).toBe(true);
    });

    it('should return true for skill with 0 years experience', () => {
      const skill = {
        skill_id: 1,
        proficiency: 'NOVICE',
        yearsExperience: 0
      };
      expect(isSkillRowComplete(skill)).toBe(true);
    });
  });

  describe('validateEmployeeSkills', () => {
    it('should return error for null skills array', () => {
      const result = validateEmployeeSkills(null);
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Add at least one skill.');
      expect(result.validSkillCount).toBe(0);
    });

    it('should return error for empty array', () => {
      const result = validateEmployeeSkills([]);
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Add at least one skill with proficiency and experience.');
      expect(result.validSkillCount).toBe(0);
    });

    it('should return error when only incomplete skills exist', () => {
      const skills = [
        { skill_id: null, proficiency: '', yearsExperience: '' },
        { skill_id: 1, proficiency: '', yearsExperience: '' }
      ];
      const result = validateEmployeeSkills(skills);
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Add at least one skill with proficiency and experience.');
      expect(result.validSkillCount).toBe(0);
    });

    it('should return valid when at least one complete skill exists', () => {
      const skills = [
        { skill_id: 1, proficiency: 'EXPERT', yearsExperience: 5 },
        { skill_id: null, proficiency: '', yearsExperience: '' } // Empty row, ignored
      ];
      const result = validateEmployeeSkills(skills);
      expect(result.isValid).toBe(true);
      expect(result.error).toBe(null);
      expect(result.validSkillCount).toBe(1);
    });

    it('should count multiple complete skills', () => {
      const skills = [
        { skill_id: 1, proficiency: 'EXPERT', yearsExperience: 5 },
        { skill_id: 2, proficiency: 'COMPETENT', yearsExperience: 3 }
      ];
      const result = validateEmployeeSkills(skills);
      expect(result.isValid).toBe(true);
      expect(result.error).toBe(null);
      expect(result.validSkillCount).toBe(2);
    });
  });
});
