import React, { useState, useEffect, useCallback } from 'react';
import { useOrgAssignment } from '../hooks/useOrgAssignment.js';
import { useEmployeeForm } from '../hooks/useEmployeeForm.js';
import { useRoles } from '../hooks/useRoles.js';
import { useUniqueEmployeeValidation } from '../hooks/useUniqueEmployeeValidation.js';
import { RoleAutoSuggestSelect } from './RoleAutoSuggestSelect.jsx';
import { EmployeeSkillsTab, createEmptySkill } from './skills/EmployeeSkillsTab.jsx';
import { employeeApi } from '../services/api/employeeApi.js';
import { validateEmployeeSkills } from '../utils/skillsValidation.js';

/**
 * Add Employee Drawer Component
 * 
 * Right-side sliding drawer for adding/editing employees.
 * UI matches designer's HTML mockup (AddEmployeeDrawDown.html).
 * 
 * Features:
 * - Smooth slide-in/out animation with backdrop fade
 * - Role-based cascading dropdowns for organizational assignment
 * - Form validation and API integration for employee creation
 * 
 * @param {boolean} isOpen - Whether drawer is open
 * @param {Function} onClose - Close handler
 * @param {Function} onSave - Callback after successful save
 * @param {string} mode - 'add' or 'edit'
 * @param {object} employee - Employee data (for edit mode)
 */
const AddEmployeeDrawer = ({ isOpen, onClose, onSave, mode = 'add', employee = null }) => {
  // Active tab: 'details' or 'skills'
  const [activeTab, setActiveTab] = useState('details');
  
  // Use organizational assignment hook for cascading dropdowns
  const orgAssignment = useOrgAssignment();
  
  // Use employee form hook for form state and validation
  // NOTE: Don't pass onSuccess here - we handle success after skills save in handleSave
  const employeeForm = useEmployeeForm({
    onError: (err) => {
      console.error('Save error:', err);
    }
  });
  
  // Use roles hook for role dropdown
  const { roles, loading: rolesLoading } = useRoles();
  
  // Use uniqueness validation hook for ZID/email
  // Pass excludeEmployeeId in edit mode so current employee doesn't trigger duplicate error
  const uniqueValidation = useUniqueEmployeeValidation({
    excludeEmployeeId: mode === 'edit' ? employee?.employee_id : null
  });
  
  // Skills state
  const [skills, setSkills] = useState([createEmptySkill()]);
  // Skills validation errors
  const [skillErrors, setSkillErrors] = useState({});
  // Skills-level error (e.g., "at least one skill required")
  const [skillsError, setSkillsError] = useState(null);
  // Skills saving state
  const [skillsSaveError, setSkillsSaveError] = useState(null);

  /**
   * Wrapper handlers for org assignment that clear validation errors on change
   * Fix #1: Clear error when valid value is selected
   */
  const handleSegmentChangeWithClear = useCallback((value) => {
    orgAssignment.handleSegmentChange(value);
    if (value) {
      employeeForm.clearError('segmentId');
    }
  }, [orgAssignment, employeeForm]);

  const handleSubSegmentChangeWithClear = useCallback((value) => {
    orgAssignment.handleSubSegmentChange(value);
    if (value) {
      employeeForm.clearError('subSegmentId');
    }
  }, [orgAssignment, employeeForm]);

  const handleProjectChangeWithClear = useCallback((value) => {
    orgAssignment.handleProjectChange(value);
    if (value) {
      employeeForm.clearError('projectId');
    }
  }, [orgAssignment, employeeForm]);

  const handleTeamChangeWithClear = useCallback((value) => {
    orgAssignment.handleTeamChange(value);
    if (value) {
      employeeForm.clearError('teamId');
    }
  }, [orgAssignment, employeeForm]);

  /**
   * Wrapper handler for ZID input that triggers uniqueness validation
   */
  const handleZidChange = useCallback((e) => {
    employeeForm.handleChange(e);
    // Trigger debounced uniqueness validation
    uniqueValidation.validateZid(e.target.value);
  }, [employeeForm, uniqueValidation]);

  /**
   * Wrapper handler for Email input that triggers uniqueness validation
   */
  const handleEmailChange = useCallback((e) => {
    employeeForm.handleChange(e);
    // Trigger debounced uniqueness validation
    uniqueValidation.validateEmail(e.target.value);
  }, [employeeForm, uniqueValidation]);

  /**
   * Wrapper for setSkills that clears skills-level error when skills change
   */
  const handleSkillsChange = useCallback((newSkills) => {
    setSkills(newSkills);
    // Clear skills-level error when user adds/modifies skills
    if (skillsError) {
      setSkillsError(null);
    }
  }, [skillsError]);
  
  // Static dropdown options for fields not in cascading logic
  const staticOptions = {
    employmentTypes: [
      { value: 'FULL_TIME', label: 'Full Time' },
      { value: 'CONTRACT', label: 'Contract' },
      { value: 'INTERN', label: 'Intern' }
    ],
    statuses: [
      { value: 'ACTIVE', label: 'Active' },
      { value: 'INACTIVE', label: 'Inactive' },
      { value: 'ON_LEAVE', label: 'On Leave' }
    ],
    proficiencies: [
      { value: 'NOVICE', label: 'Novice' },
      { value: 'ADVANCED_BEGINNER', label: 'Advanced Beginner' },
      { value: 'COMPETENT', label: 'Competent' },
      { value: 'PROFICIENT', label: 'Proficient' },
      { value: 'EXPERT', label: 'Expert' }
    ],
    months: [
      { value: '01', label: 'Jan' },
      { value: '02', label: 'Feb' },
      { value: '03', label: 'Mar' },
      { value: '04', label: 'Apr' },
      { value: '05', label: 'May' },
      { value: '06', label: 'Jun' },
      { value: '07', label: 'Jul' },
      { value: '08', label: 'Aug' },
      { value: '09', label: 'Sep' },
      { value: '10', label: 'Oct' },
      { value: '11', label: 'Nov' },
      { value: '12', label: 'Dec' }
    ]
  };

  // Note: createEmptySkill is now imported from EmployeeSkillsTab

  // Reset form when drawer opens/closes or mode changes
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && employee) {
        // Pre-fill form with employee data
        employeeForm.prefill(employee);
        // Pre-fill skills if available
        if (employee.skills && employee.skills.length > 0) {
          setSkills(employee.skills.map(s => ({ ...createEmptySkill(), ...s })));
        }
        // Clear uniqueness errors in edit mode (user can re-validate as needed)
        uniqueValidation.clearAllUniqueErrors();
      } else {
        // Reset for add mode
        employeeForm.reset();
        orgAssignment.reset();
        setSkills([createEmptySkill()]);
        // Clear uniqueness errors
        uniqueValidation.clearAllUniqueErrors();
      }
      setActiveTab('details');
    }
  }, [isOpen, mode, employee]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent background scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  /**
   * Map frontend skill row to backend API payload format
   */
  const mapSkillToPayload = (skill) => ({
    skill_id: skill.skill_id,
    proficiency: skill.proficiency,
    years_experience: skill.yearsExperience ? parseInt(skill.yearsExperience, 10) : null,
    last_used_month: skill.lastUsedMonth || null,
    last_used_year: skill.lastUsedYear || null,
    started_from: skill.startedFrom || null,
    certification: skill.certification || null
  });

  // Handle save - saves employee details then skills atomically
  const handleSave = async () => {
    // Clear previous errors
    setSkillsSaveError(null);
    setSkillsError(null);
    
    // Block save if uniqueness validation is still in progress
    if (uniqueValidation.isAnyValidating()) {
      // Wait a moment and try again, or show message
      setActiveTab('details');
      return;
    }
    
    // Block save if there are uniqueness errors (ZID or email already exists)
    if (uniqueValidation.hasUniqueErrors()) {
      setActiveTab('details');
      return;
    }
    
    // Validate form with org assignment data (validation now includes all fields)
    const formIsValid = employeeForm.validate(orgAssignment);
    
    // Fix #2: Validate that at least one skill is complete
    const skillsValidation = validateEmployeeSkills(skills);
    
    // If form validation failed, switch to details tab
    if (!formIsValid) {
      setActiveTab('details');
      // Also check skills and set error if invalid (but don't switch tabs)
      if (!skillsValidation.isValid) {
        setSkillsError(skillsValidation.error);
      }
      return;
    }
    
    // If skills validation failed, switch to skills tab and show error
    if (!skillsValidation.isValid) {
      setSkillsError(skillsValidation.error);
      setActiveTab('skills');
      return;
    }
    
    // Step 1: Submit employee details via hook
    const employeeResult = await employeeForm.submit(orgAssignment);
    
    // If employee save failed, stop (error already handled by hook)
    if (!employeeResult || !employeeResult.employee_id) {
      return;
    }
    
    // Step 2: Save skills (only rows with a valid skill_id)
    const validSkills = skills.filter(s => s.skill_id);
    
    if (validSkills.length > 0) {
      try {
        const skillsPayload = validSkills.map(mapSkillToPayload);
        await employeeApi.saveEmployeeSkills(employeeResult.employee_id, skillsPayload);
      } catch (err) {
        console.error('Failed to save skills:', err);
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to save skills';
        setSkillsSaveError(errorMsg);
        // Don't close drawer - show error and let user retry
        alert(`Employee created, but skills save failed: ${errorMsg}`);
        return;
      }
    }
    
    // Step 3: Both succeeded - show success and notify parent
    alert('Employee saved successfully!');
    if (onSave) onSave(employeeResult);
    
    // Reset form for next entry (instead of closing drawer)
    // This allows user to quickly add another employee
    employeeForm.reset();
    orgAssignment.reset();
    setSkills([createEmptySkill()]);
    setSkillErrors({});
    setSkillsError(null);
    setSkillsSaveError(null);
    uniqueValidation.clearAllUniqueErrors();
    setActiveTab('details');
    // Note: Drawer stays open - user can close manually via X or Cancel
  };

  // Handle skills validation callback
  const handleSkillsValidate = useCallback((errors, isValid) => {
    setSkillErrors(errors);
  }, []);

  const isEditMode = mode === 'edit';
  const { formData, errors, handleChange, setRole, isSubmitting, submitError } = employeeForm;

  // Always render for smooth animation, control visibility via CSS classes
  return (
    <>
      {/* Overlay */}
      <div 
        className={`add-employee-drawer-overlay ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        data-testid="add-employee-overlay"
      />

      {/* Drawer */}
      <div className={`add-employee-drawer ${isOpen ? 'open' : ''}`} data-testid="add-employee-drawer">
        {/* Header */}
        <div className="drawer-header">
          <div className="drawer-title">
            <h3>{isEditMode ? 'Edit Employee' : 'Add Employee'}</h3>
            <div className="drawer-subtitle">
              {isEditMode ? 'Update employee information and skills' : 'Complete employee information and skills'}
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Tab navigation */}
        <div className="tab-nav">
          <button 
            className={`tab-btn ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => setActiveTab('details')}
          >
            Employee Details
            {Object.keys(errors).length > 0 && (
              <span className="error-indicator" />
            )}
          </button>
          <button 
            className={`tab-btn ${activeTab === 'skills' ? 'active' : ''}`}
            onClick={() => setActiveTab('skills')}
          >
            Skills
            {(skillsError || Object.keys(skillErrors).length > 0) && (
              <span className="error-indicator" />
            )}
          </button>
        </div>

        {/* Body */}
        <div className="drawer-body">
          {/* Tab 1: Employee Details */}
          <div className={`tab-content ${activeTab === 'details' ? 'active' : ''}`}>
            {/* Import Info Callout (only in edit mode) */}
            {isEditMode && (
              <div className="info-callout">
                <div className="info-callout-title">📥 Imported from Excel</div>
                <div className="info-callout-text">
                  This employee was imported on Jan 15, 2026 via import job #1234. Original data is preserved.
                </div>
              </div>
            )}

            {/* Submit Error Message */}
            {submitError && (
              <div className="info-callout" style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
                <div className="info-callout-title" style={{ color: '#dc2626' }}>❌ Error</div>
                <div className="info-callout-text" style={{ color: '#dc2626' }}>{submitError}</div>
              </div>
            )}

            {/* Personal Information */}
            <div className="form-section">
              <div className="section-header">
                <div className="section-title">Personal Information</div>
                <div className="section-description">Basic employee identification details</div>
              </div>
              <div className="form-grid">
                <div className={`form-field ${errors.zid || uniqueValidation.uniqueErrors.zid ? 'error' : ''}`}>
                  <label>
                    Employee ID (ZID) <span className="required">*</span>
                    {uniqueValidation.isValidating.zid && (
                      <span className="validating-indicator" title="Checking availability...">⏳</span>
                    )}
                  </label>
                  <input 
                    type="text" 
                    name="zid"
                    value={formData.zid}
                    onChange={handleZidChange}
                    placeholder="e.g., Z0123456"
                    disabled={isEditMode}
                  />
                  <div className="input-hint">Unique identifier, auto-generated or manual</div>
                  <div className="error-message">{errors.zid || uniqueValidation.uniqueErrors.zid}</div>
                </div>
                <div className={`form-field ${errors.fullName ? 'error' : ''}`}>
                  <label>
                    Full Name <span className="required">*</span>
                    {isEditMode && <span className="badge imported">Imported</span>}
                  </label>
                  <input 
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    placeholder="e.g., Alex Johnson"
                  />
                  <div className="error-message">{errors.fullName}</div>
                </div>
                <div className={`form-field full-width ${errors.email || uniqueValidation.uniqueErrors.email ? 'error' : ''}`}>
                  <label>
                    Email <span className="required">*</span>
                    {uniqueValidation.isValidating.email && (
                      <span className="validating-indicator" title="Checking availability...">⏳</span>
                    )}
                  </label>
                  <input 
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleEmailChange}
                    placeholder="e.g., alex.johnson@example.com"
                  />
                  <div className="error-message">{errors.email || uniqueValidation.uniqueErrors.email}</div>
                </div>
              </div>
            </div>

            {/* Organizational Assignment - Cascading Dropdowns */}
            <div className="form-section">
              <div className="section-header">
                <div className="section-title">Organizational Assignment</div>
                <div className="section-description">Cascading hierarchy: Segment → Sub-segment → Project → Team (all required)</div>
              </div>
              <div className="form-grid">
                <div className={`form-field ${errors.segmentId ? 'error' : ''}`}>
                  <label>
                    Segment <span className="required">*</span>
                    {orgAssignment.isLocked.segment && <span className="badge">Locked</span>}
                  </label>
                  <select 
                    value={orgAssignment.selectedSegmentId || ''} 
                    onChange={(e) => handleSegmentChangeWithClear(e.target.value)}
                    disabled={orgAssignment.isDisabled.segment || orgAssignment.loading.segments}
                    data-testid="segment-select"
                  >
                    <option value="">
                      {orgAssignment.loading.segments ? 'Loading...' : 'Select Segment'}
                    </option>
                    {orgAssignment.segments.map(opt => (
                      <option key={opt.id} value={opt.id}>{opt.name}</option>
                    ))}
                  </select>
                  <div className="input-hint">Top-level organizational unit</div>
                  <div className="error-message">{errors.segmentId}</div>
                </div>
                <div className={`form-field ${errors.subSegmentId ? 'error' : ''}`}>
                  <label>
                    Sub-Segment <span className="required">*</span>
                    {orgAssignment.isLocked.subSegment && <span className="badge">Locked</span>}
                  </label>
                  <select 
                    value={orgAssignment.selectedSubSegmentId || ''} 
                    onChange={(e) => handleSubSegmentChangeWithClear(e.target.value)}
                    disabled={orgAssignment.isDisabled.subSegment || orgAssignment.loading.subSegments}
                    data-testid="subsegment-select"
                  >
                    <option value="">
                      {orgAssignment.loading.subSegments ? 'Loading...' : 'Select Sub-Segment'}
                    </option>
                    {orgAssignment.subSegments.map(opt => (
                      <option key={opt.id} value={opt.id}>{opt.name}</option>
                    ))}
                  </select>
                  <div className="input-hint">Available after selecting Segment</div>
                  <div className="error-message">{errors.subSegmentId}</div>
                </div>
                <div className={`form-field ${errors.projectId ? 'error' : ''}`}>
                  <label>
                    Project <span className="required">*</span>
                    {orgAssignment.isLocked.project && <span className="badge">Locked</span>}
                  </label>
                  <select 
                    value={orgAssignment.selectedProjectId || ''} 
                    onChange={(e) => handleProjectChangeWithClear(e.target.value)}
                    disabled={orgAssignment.isDisabled.project || orgAssignment.loading.projects}
                    data-testid="project-select"
                  >
                    <option value="">
                      {orgAssignment.loading.projects ? 'Loading...' : 'Select Project'}
                    </option>
                    {orgAssignment.projects.map(opt => (
                      <option key={opt.id} value={opt.id}>{opt.name}</option>
                    ))}
                  </select>
                  <div className="input-hint">Available after selecting Sub-Segment</div>
                  <div className="error-message">{errors.projectId}</div>
                </div>
                <div className={`form-field ${errors.teamId ? 'error' : ''}`}>
                  <label>
                    Team <span className="required">*</span>
                    {orgAssignment.isLocked.team && <span className="badge">Locked</span>}
                  </label>
                  <select 
                    value={orgAssignment.selectedTeamId || ''} 
                    onChange={(e) => handleTeamChangeWithClear(e.target.value)}
                    disabled={orgAssignment.isDisabled.team || orgAssignment.loading.teams}
                    data-testid="team-select"
                  >
                    <option value="">
                      {orgAssignment.loading.teams ? 'Loading...' : 'Select Team'}
                    </option>
                    {orgAssignment.teams.map(opt => (
                      <option key={opt.id} value={opt.id}>{opt.name}</option>
                    ))}
                  </select>
                  <div className="input-hint">Required - Available after selecting Project</div>
                  <div className="error-message">{errors.teamId}</div>
                </div>
              </div>
            </div>

            {/* Role & Employment Details */}
            <div className="form-section">
              <div className="section-header">
                <div className="section-title">Role & Employment Details</div>
              </div>
              <div className="form-grid">
                <div className={`form-field ${errors.roleId ? 'error' : ''}`}>
                  <label>
                    Role / Designation <span className="required">*</span>
                  </label>
                  <RoleAutoSuggestSelect
                    value={formData.roleId}
                    onChange={(roleId, roleName) => setRole(roleId, roleName)}
                    roles={roles}
                    loading={rolesLoading}
                    error={errors.roleId}
                  />
                  <div className="input-hint">Select from roles list</div>
                  <div className="error-message">{errors.roleId}</div>
                </div>
                <div className="form-field">
                  <label>Start Date of Working</label>
                  <input 
                    type="date"
                    name="startDate"
                    value={formData.startDate}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-field">
                  <label>Project Allocation %</label>
                  <input 
                    type="number"
                    name="allocation"
                    value={formData.allocation}
                    onChange={handleChange}
                    placeholder="100"
                    min="0"
                    max="100"
                  />
                  <div className="input-hint">0-100%</div>
                </div>
              </div>
            </div>
          </div>

          {/* Tab 2: Skills */}
          <div className={`tab-content ${activeTab === 'skills' ? 'active' : ''}`}>
            {/* Skills validation error message */}
            {skillsError && (
              <div className="info-callout" style={{ background: '#fef2f2', borderColor: '#fecaca', marginBottom: '1rem' }}>
                <div className="info-callout-title" style={{ color: '#dc2626' }}>❌ Validation Error</div>
                <div className="info-callout-text" style={{ color: '#dc2626' }}>{skillsError}</div>
              </div>
            )}
            <EmployeeSkillsTab
              skills={skills}
              onSkillsChange={handleSkillsChange}
              errors={skillErrors}
              onValidate={handleSkillsValidate}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="drawer-footer">
          <div className="footer-info">
            {isEditMode && (
              <span>Last updated: Jan 15, 2026 by System Import</span>
            )}
          </div>
          <div className="footer-actions">
            <button className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSave} disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Employee'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default AddEmployeeDrawer;
