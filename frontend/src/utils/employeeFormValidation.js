/**
 * Employee Form Validation Module
 * 
 * SRP: Responsible solely for validating employee form fields.
 * Does NOT handle state management, API calls, or UI rendering.
 * 
 * All employee fields in Add Employee form are REQUIRED.
 */

/**
 * Validates email format
 * @param {string} email 
 * @returns {boolean}
 */
const isValidEmail = (email) => {
  if (!email) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
};

/**
 * Checks if a value is non-empty after trimming
 * @param {any} value 
 * @returns {boolean}
 */
const isNotEmpty = (value) => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  if (typeof value === 'number') return true; // 0 is valid for numbers
  return Boolean(value);
};

/**
 * Field validation rules
 * Each rule returns an error message string or null if valid
 */
const fieldValidators = {
  zid: (value) => {
    if (!isNotEmpty(value)) return 'Employee ID (ZID) is required';
    if (value.length > 50) return 'ZID must be 50 characters or less';
    return null;
  },
  
  fullName: (value) => {
    if (!isNotEmpty(value)) return 'Full Name is required';
    if (value.length > 255) return 'Name must be 255 characters or less';
    return null;
  },
  
  email: (value) => {
    if (!isNotEmpty(value)) return 'Email is required';
    if (!isValidEmail(value)) return 'Please enter a valid email address';
    return null;
  },
  
  roleId: (value) => {
    if (!isNotEmpty(value)) return 'Role/Designation is required';
    return null;
  },
  
  segmentId: (value) => {
    if (!isNotEmpty(value)) return 'Segment is required';
    return null;
  },
  
  subSegmentId: (value) => {
    if (!isNotEmpty(value)) return 'Sub-Segment is required';
    return null;
  },
  
  projectId: (value) => {
    if (!isNotEmpty(value)) return 'Project is required';
    return null;
  },
  
  teamId: (value) => {
    if (!isNotEmpty(value)) return 'Team is required';
    return null;
  }
};

/**
 * Validates the complete employee form
 * 
 * @param {Object} formValues - Form field values
 * @param {string} formValues.zid - Employee ZID
 * @param {string} formValues.fullName - Full name
 * @param {string} formValues.email - Email address
 * @param {number|string} formValues.roleId - Selected role ID
 * @param {number|string} formValues.segmentId - Selected segment ID
 * @param {number|string} formValues.subSegmentId - Selected sub-segment ID
 * @param {number|string} formValues.projectId - Selected project ID
 * @param {number|string} formValues.teamId - Selected team ID
 * 
 * @returns {{ isValid: boolean, errors: Object.<string, string> }}
 */
export function validateEmployeeForm(formValues) {
  const errors = {};
  
  // Validate each required field
  const fieldsToValidate = [
    'zid',
    'fullName', 
    'email',
    'roleId',
    'segmentId',
    'subSegmentId',
    'projectId',
    'teamId'
  ];
  
  for (const field of fieldsToValidate) {
    const validator = fieldValidators[field];
    if (validator) {
      const error = validator(formValues[field]);
      if (error) {
        errors[field] = error;
      }
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

/**
 * Validates a single field
 * Useful for real-time validation on blur
 * 
 * @param {string} fieldName - Name of the field to validate
 * @param {any} value - Field value
 * @returns {string|null} - Error message or null if valid
 */
export function validateField(fieldName, value) {
  const validator = fieldValidators[fieldName];
  if (!validator) return null;
  return validator(value);
}

export default { validateEmployeeForm, validateField };
