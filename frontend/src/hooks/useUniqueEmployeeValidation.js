/**
 * useUniqueEmployeeValidation Hook
 * 
 * SRP: Handles async validation of ZID and Email uniqueness.
 * Uses debouncing to prevent excessive API calls during typing.
 * 
 * Integrates with the backend /employees/validate-unique endpoint.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { employeeValidationApi } from '../services/api/employeeValidationApi.js';

/**
 * Debounce delay in milliseconds
 */
const DEBOUNCE_DELAY = 500;

/**
 * Hook for validating ZID and Email uniqueness with debounce.
 * 
 * @param {Object} options
 * @param {number} [options.excludeEmployeeId] - Employee ID to exclude (for edit mode)
 * @param {number} [options.debounceDelay] - Debounce delay in ms (default: 500)
 * @returns {Object} Validation state and methods
 */
export function useUniqueEmployeeValidation({ 
  excludeEmployeeId = null,
  debounceDelay = DEBOUNCE_DELAY 
} = {}) {
  // Validation errors for uniqueness
  const [uniqueErrors, setUniqueErrors] = useState({
    zid: null,
    email: null
  });

  // Loading states
  const [isValidating, setIsValidating] = useState({
    zid: false,
    email: false
  });

  // Refs for debounce timers
  const zidTimeoutRef = useRef(null);
  const emailTimeoutRef = useRef(null);

  // Track mounted state for async operations
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (zidTimeoutRef.current) clearTimeout(zidTimeoutRef.current);
      if (emailTimeoutRef.current) clearTimeout(emailTimeoutRef.current);
    };
  }, []);

  /**
   * Validate ZID uniqueness (debounced)
   * @param {string} zid - ZID value to validate
   */
  const validateZid = useCallback((zid) => {
    // Clear existing timeout
    if (zidTimeoutRef.current) {
      clearTimeout(zidTimeoutRef.current);
    }

    // Clear error immediately if empty
    if (!zid || zid.trim().length === 0) {
      setUniqueErrors(prev => ({ ...prev, zid: null }));
      setIsValidating(prev => ({ ...prev, zid: false }));
      return;
    }

    // Set validating state
    setIsValidating(prev => ({ ...prev, zid: true }));

    // Debounce the API call
    zidTimeoutRef.current = setTimeout(async () => {
      try {
        const result = await employeeValidationApi.validateUnique({
          zid: zid.trim(),
          excludeEmployeeId
        });

        if (mountedRef.current) {
          setUniqueErrors(prev => ({
            ...prev,
            zid: result.zid_exists ? 'This ZID is already in use' : null
          }));
        }
      } catch (error) {
        console.error('[useUniqueEmployeeValidation] ZID validation failed:', error);
        // Don't set error on network failure - let server validation catch it
        if (mountedRef.current) {
          setUniqueErrors(prev => ({ ...prev, zid: null }));
        }
      } finally {
        if (mountedRef.current) {
          setIsValidating(prev => ({ ...prev, zid: false }));
        }
      }
    }, debounceDelay);
  }, [excludeEmployeeId, debounceDelay]);

  /**
   * Validate email uniqueness (debounced)
   * @param {string} email - Email value to validate
   */
  const validateEmail = useCallback((email) => {
    // Clear existing timeout
    if (emailTimeoutRef.current) {
      clearTimeout(emailTimeoutRef.current);
    }

    // Clear error immediately if empty
    if (!email || email.trim().length === 0) {
      setUniqueErrors(prev => ({ ...prev, email: null }));
      setIsValidating(prev => ({ ...prev, email: false }));
      return;
    }

    // Set validating state
    setIsValidating(prev => ({ ...prev, email: true }));

    // Debounce the API call
    emailTimeoutRef.current = setTimeout(async () => {
      try {
        const result = await employeeValidationApi.validateUnique({
          email: email.trim(),
          excludeEmployeeId
        });

        if (mountedRef.current) {
          setUniqueErrors(prev => ({
            ...prev,
            email: result.email_exists ? 'This email is already in use' : null
          }));
        }
      } catch (error) {
        console.error('[useUniqueEmployeeValidation] Email validation failed:', error);
        // Don't set error on network failure - let server validation catch it
        if (mountedRef.current) {
          setUniqueErrors(prev => ({ ...prev, email: null }));
        }
      } finally {
        if (mountedRef.current) {
          setIsValidating(prev => ({ ...prev, email: false }));
        }
      }
    }, debounceDelay);
  }, [excludeEmployeeId, debounceDelay]);

  /**
   * Clear a specific uniqueness error
   * @param {string} field - 'zid' or 'email'
   */
  const clearUniqueError = useCallback((field) => {
    setUniqueErrors(prev => ({ ...prev, [field]: null }));
  }, []);

  /**
   * Clear all uniqueness errors
   */
  const clearAllUniqueErrors = useCallback(() => {
    setUniqueErrors({ zid: null, email: null });
  }, []);

  /**
   * Check if there are any uniqueness errors
   * @returns {boolean}
   */
  const hasUniqueErrors = useCallback(() => {
    return Boolean(uniqueErrors.zid || uniqueErrors.email);
  }, [uniqueErrors]);

  /**
   * Check if any validation is in progress
   * @returns {boolean}
   */
  const isAnyValidating = useCallback(() => {
    return isValidating.zid || isValidating.email;
  }, [isValidating]);

  return {
    // Validation errors
    uniqueErrors,
    
    // Loading states
    isValidating,
    
    // Validation methods
    validateZid,
    validateEmail,
    
    // Clear methods
    clearUniqueError,
    clearAllUniqueErrors,
    
    // Utility methods
    hasUniqueErrors,
    isAnyValidating
  };
}

export default useUniqueEmployeeValidation;
