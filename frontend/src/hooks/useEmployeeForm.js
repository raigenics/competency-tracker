/**
 * useEmployeeForm Hook
 * 
 * Handles form state, validation, and submission for Add Employee drawer.
 * Only handles basic employee details - skills are handled separately.
 * 
 * SRP: This hook focuses solely on form management, not UI or API details.
 * Validation logic delegated to employeeFormValidation module.
 */
import { useState, useCallback } from 'react';
import { employeeApi } from '../services/api/employeeApi.js';
import { validateEmployeeForm } from '../utils/employeeFormValidation.js';

/**
 * Initial form state
 */
const initialFormData = {
  zid: '',
  fullName: '',
  email: '',
  roleId: null,   // Changed from roleName to roleId
  roleName: '',   // Keep for display purposes
  startDate: '',
  allocation: ''
};

/**
 * @param {Object} options
 * @param {Function} options.onSuccess - Callback on successful save
 * @param {Function} options.onError - Callback on error
 * @returns {Object} Form state and handlers
 */
export function useEmployeeForm({ onSuccess, onError } = {}) {
  // Form data state
  const [formData, setFormData] = useState(initialFormData);
  
  // Validation errors (includes org assignment errors)
  const [errors, setErrors] = useState({});
  
  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  /**
   * Update a single form field
   */
  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  }, [errors]);

  /**
   * Set a form field programmatically
   */
  const setField = useCallback((name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  }, [errors]);

  /**
   * Set role (both id and name)
   */
  const setRole = useCallback((roleId, roleName) => {
    setFormData(prev => ({ ...prev, roleId, roleName }));
    if (errors.roleId) {
      setErrors(prev => ({ ...prev, roleId: null }));
    }
  }, [errors]);

  /**
   * Clear a specific error
   */
  const clearError = useCallback((fieldName) => {
    setErrors(prev => ({ ...prev, [fieldName]: null }));
  }, []);

  /**
   * Validate all required fields including org assignment
   * @param {Object} orgAssignment - Org assignment data from useOrgAssignment
   * @returns {boolean} True if valid
   */
  const validate = useCallback((orgAssignment = {}) => {
    // Build values object for validation
    const valuesToValidate = {
      zid: formData.zid,
      fullName: formData.fullName,
      email: formData.email,
      roleId: formData.roleId,
      segmentId: orgAssignment.selectedSegmentId,
      subSegmentId: orgAssignment.selectedSubSegmentId,
      projectId: orgAssignment.selectedProjectId,
      teamId: orgAssignment.selectedTeamId
    };
    
    const { isValid, errors: validationErrors } = validateEmployeeForm(valuesToValidate);
    setErrors(validationErrors);
    return isValid;
  }, [formData]);

  /**
   * Submit the form (create employee)
   * @param {Object} orgAssignment - Contains org IDs from useOrgAssignment hook
   * @returns {Promise<Object>} Created employee or null on error
   */
  const submit = useCallback(async (orgAssignment) => {
    // Validate form with org assignment data
    if (!validate(orgAssignment)) {
      return null;
    }
    
    setIsSubmitting(true);
    setSubmitError(null);
    
    try {
      const payload = {
        zid: formData.zid.trim(),
        full_name: formData.fullName.trim(),
        email: formData.email.trim() || null,
        team_id: orgAssignment.selectedTeamId,
        role_id: formData.roleId,  // Use role_id instead of role_name
        start_date_of_working: formData.startDate || null
      };
      
      console.log('[useEmployeeForm] Submitting payload:', payload);
      
      const response = await employeeApi.createEmployee(payload);
      
      if (onSuccess) {
        onSuccess(response);
      }
      
      return response;
    } catch (err) {
      console.error('Failed to create employee:', err);
      
      // Extract error message
      let errorMessage = 'Failed to create employee';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setSubmitError(errorMessage);
      
      if (onError) {
        onError(err);
      }
      
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validate, onSuccess, onError]);

  /**
   * Reset form to initial state
   */
  const reset = useCallback(() => {
    setFormData(initialFormData);
    setErrors({});
    setSubmitError(null);
    setIsSubmitting(false);
  }, []);

  /**
   * Pre-fill form with employee data (for edit mode)
   */
  const prefill = useCallback((employee) => {
    if (!employee) return;
    
    setFormData({
      zid: employee.zid || '',
      fullName: employee.fullName || employee.full_name || '',
      email: employee.email || '',
      roleId: employee.roleId || employee.role_id || null,
      roleName: employee.roleName || employee.role_name || '',
      startDate: employee.startDate || employee.start_date_of_working || '',
      allocation: employee.allocation || ''
    });
    setErrors({});
  }, []);

  /**
   * Check if form has been modified
   */
  const isDirty = useCallback(() => {
    return Object.keys(initialFormData).some(
      key => formData[key] !== initialFormData[key]
    );
  }, [formData]);

  return {
    // Form data
    formData,
    
    // Validation errors
    errors,
    
    // Submission state
    isSubmitting,
    submitError,
    
    // Handlers
    handleChange,
    setField,
    setRole,      // New: set role id + name
    clearError,   // New: clear specific error
    
    // Actions
    validate,
    submit,
    reset,
    prefill,
    
    // Utility
    isDirty
  };
}

export default useEmployeeForm;
