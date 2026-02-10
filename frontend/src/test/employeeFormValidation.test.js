/**
 * employeeFormValidation Module Unit Tests
 * 
 * Tests the validation logic for employee form fields.
 * All fields are required per requirements.
 */
import { describe, it, expect } from 'vitest';
import { validateEmployeeForm, validateField } from '@/utils/employeeFormValidation.js';

describe('employeeFormValidation', () => {
  
  describe('validateEmployeeForm', () => {
    const validFormData = {
      zid: 'Z0123456',
      fullName: 'John Doe',
      email: 'john.doe@example.com',
      roleId: 1,
      segmentId: 1,
      subSegmentId: 1,
      projectId: 1,
      teamId: 1
    };
    
    it('returns isValid=true when all fields are valid', () => {
      const result = validateEmployeeForm(validFormData);
      
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    it('returns isValid=false when ZID is empty', () => {
      const formData = { ...validFormData, zid: '' };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.zid).toBeDefined();
    });

    it('returns isValid=false when ZID is whitespace only', () => {
      const formData = { ...validFormData, zid: '   ' };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.zid).toBeDefined();
    });

    it('returns isValid=false when fullName is empty', () => {
      const formData = { ...validFormData, fullName: '' };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.fullName).toBeDefined();
    });

    it('returns isValid=false when email is empty', () => {
      const formData = { ...validFormData, email: '' };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toBeDefined();
    });

    it('returns isValid=false when email format is invalid', () => {
      const formData = { ...validFormData, email: 'not-an-email' };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toContain('valid');
    });

    it('returns isValid=false when roleId is null', () => {
      const formData = { ...validFormData, roleId: null };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.roleId).toBeDefined();
    });

    it('returns isValid=false when segmentId is null', () => {
      const formData = { ...validFormData, segmentId: null };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.segmentId).toBeDefined();
    });

    it('returns isValid=false when subSegmentId is null', () => {
      const formData = { ...validFormData, subSegmentId: null };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.subSegmentId).toBeDefined();
    });

    it('returns isValid=false when projectId is null', () => {
      const formData = { ...validFormData, projectId: null };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.projectId).toBeDefined();
    });

    it('returns isValid=false when teamId is null', () => {
      const formData = { ...validFormData, teamId: null };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.teamId).toBeDefined();
    });

    it('returns multiple errors when multiple fields are invalid', () => {
      const formData = { 
        zid: '', 
        fullName: '', 
        email: '', 
        roleId: null,
        segmentId: null,
        subSegmentId: null,
        projectId: null,
        teamId: null
      };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(Object.keys(result.errors).length).toBe(8);
    });

    it('validates ZID max length', () => {
      const formData = { ...validFormData, zid: 'Z'.repeat(51) };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.zid).toContain('50');
    });

    it('validates fullName max length', () => {
      const formData = { ...validFormData, fullName: 'A'.repeat(256) };
      const result = validateEmployeeForm(formData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.fullName).toContain('255');
    });
  });

  describe('validateField', () => {
    it('returns null for unknown field names', () => {
      const result = validateField('unknownField', 'value');
      expect(result).toBeNull();
    });

    it('validates email field correctly', () => {
      expect(validateField('email', '')).toBeDefined();
      expect(validateField('email', 'invalid')).toBeDefined();
      expect(validateField('email', 'valid@email.com')).toBeNull();
    });

    it('validates zid field correctly', () => {
      expect(validateField('zid', '')).toBeDefined();
      expect(validateField('zid', 'Z123')).toBeNull();
    });
  });
});
