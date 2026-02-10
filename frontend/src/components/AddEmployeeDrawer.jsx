import React, { useState, useEffect, useCallback } from 'react';
import { useOrgAssignment } from '../hooks/useOrgAssignment.js';
import { useEmployeeForm } from '../hooks/useEmployeeForm.js';
import { useRoles } from '../hooks/useRoles.js';
import { useUniqueEmployeeValidation } from '../hooks/useUniqueEmployeeValidation.js';
import { RoleAutoSuggestSelect } from './RoleAutoSuggestSelect.jsx';
import { EmployeeSkillsTab, createEmptySkill } from './skills/EmployeeSkillsTab.jsx';
import { employeeApi } from '../services/api/employeeApi.js';
import { dropdownApi } from '../services/api/dropdownApi.js';
import { validateEmployeeSkills } from '../utils/skillsValidation.js';

// ========== DIAGNOSTIC LOGGING - START ==========
const DIAG_T0 = performance.now();
const diagLog = (tag, msg, extra = {}) => {
  const t = (performance.now() - DIAG_T0).toFixed(1);
  console.log(`[${tag}] t=${t}ms ${msg}`, extra);
};
let editDrawerOpenCount = 0;
// ========== DIAGNOSTIC LOGGING - END ==========

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
  
  // Edit mode loading state - shows loading UI while preparing form
  const [isEditLoading, setIsEditLoading] = useState(false);
  
  // Skills loading state - for lazy loading skills on tab click
  const [isSkillsLoading, setIsSkillsLoading] = useState(false);
  const [skillsLoaded, setSkillsLoaded] = useState(false);
  
  // Use organizational assignment hook for cascading dropdowns
  // Pass isEditMode to skip initial API calls (bootstrap will provide data)
  const orgAssignment = useOrgAssignment({ isEditMode: mode === 'edit' });
  
  // Use employee form hook for form state and validation
  // NOTE: Don't pass onSuccess here - we handle success after skills save in handleSave
  const employeeForm = useEmployeeForm({
    onError: (err) => {
      console.error('Save error:', err);
    }
  });
  
  // Use roles hook for role dropdown (only fetches in add mode or if bootstrap doesn't have roles)
  const rolesHook = useRoles();
  
  // In edit mode with bootstrap data, use bootstrap roles instead of separate API call
  const bootstrapRoles = employee?._bootstrapOptions?.roles;
  const roles = bootstrapRoles || rolesHook.roles;
  const rolesLoading = bootstrapRoles ? false : rolesHook.loading;
  
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

  /**
   * Load employee data for Edit mode with sequential dropdown loading.
   * Ensures dropdowns are properly populated before setting values.
   * 
   * Backend now returns org IDs directly (segment_id, sub_segment_id, project_id, team_id),
   * so we no longer need to fetch hierarchy separately.
   * 
   * OPTIMIZATION: If _bootstrapLoaded flag is set, skip API calls and use setFromBootstrap.
   */
  const loadEmployeeForEdit = useCallback(async (employeeData) => {
    if (!employeeData) return;
    
    // ===== DIAGNOSTIC LOGGING =====
    const loadStart = performance.now();
    diagLog('EDIT', 'loadEmployeeForEdit-start', { 
      employee_id: employeeData.employee_id,
      _bootstrapLoaded: !!employeeData._bootstrapLoaded,
      _awaitingBootstrap: !!employeeData._awaitingBootstrap
    });
    // ===== END DIAGNOSTIC =====
    
    // OPTIMIZATION: If awaiting bootstrap, skip entirely - do nothing until bootstrap arrives
    if (employeeData._awaitingBootstrap) {
      diagLog('EDIT', 'skipping-loadEmployeeForEdit (awaiting bootstrap)');
      // Suppress cascade effects while waiting for bootstrap
      orgAssignment.suppressCascades();
      // Just prefill basic form fields, dropdowns will be set when bootstrap arrives
      employeeForm.prefill(employeeData);
      return;
    }
    
    // OPTIMIZATION: Bootstrap path - SINGLE-SHOT, NO loading state, NO cascade API calls
    if (employeeData._bootstrapLoaded && employeeData._bootstrapOptions) {
      diagLog('EDIT', 'using-bootstrap-options (single-shot)', {
        segments: employeeData._bootstrapOptions.segments?.length,
        subSegments: employeeData._bootstrapOptions.sub_segments?.length,
        projects: employeeData._bootstrapOptions.projects?.length,
        teams: employeeData._bootstrapOptions.teams?.length
      });
      
      // Step 1: Pre-fill basic form fields
      employeeForm.prefill(employeeData);
      
      // Step 2: Use setFromBootstrap to populate dropdowns WITHOUT API calls
      orgAssignment.setFromBootstrap(
        employeeData._bootstrapOptions,
        {
          segmentId: employeeData.segment_id,
          subSegmentId: employeeData.sub_segment_id,
          projectId: employeeData.project_id,
          teamId: employeeData.team_id
        }
      );
      
      diagLog('EDIT', 'setFromBootstrap-complete', { duration: (performance.now() - loadStart).toFixed(1) + 'ms' });
      
      // Step 3: Pre-load skills if available from bootstrap
      if (employeeData.skills && employeeData.skills.length > 0) {
        setSkills(employeeData.skills.map(s => ({ ...createEmptySkill(), ...s })));
        setSkillsLoaded(true);
        diagLog('EDIT', 'skills-loaded-from-bootstrap', { count: employeeData.skills.length });
      } else {
        setSkills([createEmptySkill()]);
      }
      
      // Step 4: Clear validation errors
      uniqueValidation.clearAllUniqueErrors();
      
      // NO loading state for bootstrap path - it's synchronous
      setIsEditLoading(false);
      return;
    }
    
    // FALLBACK: Sequential API calls (only when bootstrap is NOT available)
    console.warn('[EDIT] FALLBACK path triggered - this should NOT happen if bootstrap succeeded!', {
      _bootstrapLoaded: employeeData._bootstrapLoaded,
      _bootstrapOptions: !!employeeData._bootstrapOptions,
      segment_id: employeeData.segment_id,
      sub_segment_id: employeeData.sub_segment_id,
      project_id: employeeData.project_id,
      team_id: employeeData.team_id,
      employeeData_keys: Object.keys(employeeData)
    });
    diagLog('EDIT', 'fallback-path (no bootstrap)', {
      segment_id: employeeData.segment_id,
      sub_segment_id: employeeData.sub_segment_id,
      project_id: employeeData.project_id,
      team_id: employeeData.team_id
    });
    
    setIsEditLoading(true);
    setSkillsLoaded(false);
    
    try {
      // Step 1: Pre-fill basic form fields
      employeeForm.prefill(employeeData);
      
      // Step 2: Load org dropdowns via sequential API calls
      const hasAnyOrgId = employeeData.segment_id || employeeData.sub_segment_id || 
                          employeeData.project_id || employeeData.team_id;
      if (hasAnyOrgId) {
        diagLog('EDIT', 'calling-loadForEditMode', {
          segmentId: employeeData.segment_id,
          subSegmentId: employeeData.sub_segment_id,
          projectId: employeeData.project_id,
          teamId: employeeData.team_id
        });
        
        await orgAssignment.loadForEditMode({
          segmentId: employeeData.segment_id,
          subSegmentId: employeeData.sub_segment_id,
          projectId: employeeData.project_id,
          teamId: employeeData.team_id
        });
        diagLog('EDIT', 'loadForEditMode-complete', { duration: (performance.now() - loadStart).toFixed(1) + 'ms' });
      }
      
      // Reset skills for lazy loading
      setSkills([createEmptySkill()]);
      
      // Step 3: Clear validation errors
      uniqueValidation.clearAllUniqueErrors();
      
    } catch (err) {
      console.error('Failed to load employee for edit:', err);
      diagLog('EDIT', 'loadEmployeeForEdit-ERROR', { error: err.message });
    } finally {
      diagLog('EDIT', 'loadEmployeeForEdit-end', { totalDuration: (performance.now() - loadStart).toFixed(1) + 'ms' });
      setIsEditLoading(false);
    }
  }, [employeeForm, orgAssignment, uniqueValidation]);

  /**
   * @deprecated No longer needed - backend returns org IDs directly
   * Fetch org hierarchy from team_id to get all parent IDs.
   * Uses dropdownApi to traverse the hierarchy.
   */
  const fetchOrgHierarchy = async (teamId) => {
    diagLog('EDIT', 'fetchOrgHierarchy-start', { teamId });
    const hierarchyStart = performance.now();
    
    diagLog('EDIT', 'fetchOrgHierarchy-getTeams-start');
    const allTeams = await dropdownApi.getTeams(null);
    diagLog('EDIT', 'fetchOrgHierarchy-getTeams-end', { count: allTeams?.length, duration: (performance.now() - hierarchyStart).toFixed(1) + 'ms' });
    const team = allTeams.find(t => t.team_id === teamId);
    if (!team) throw new Error('Team not found');
    
    diagLog('EDIT', 'fetchOrgHierarchy-getProjects-start');
    const projStart = performance.now();
    const allProjects = await dropdownApi.getProjects(null);
    diagLog('EDIT', 'fetchOrgHierarchy-getProjects-end', { count: allProjects?.length, duration: (performance.now() - projStart).toFixed(1) + 'ms' });
    const project = allProjects.find(p => p.project_id === team.project_id);
    if (!project) throw new Error('Project not found');
    
    diagLog('EDIT', 'fetchOrgHierarchy-getSubSegments-start');
    const subSegStart = performance.now();
    const allSubSegments = await dropdownApi.getSubSegments(null);
    diagLog('EDIT', 'fetchOrgHierarchy-getSubSegments-end', { count: allSubSegments?.length, duration: (performance.now() - subSegStart).toFixed(1) + 'ms' });
    const subSegment = allSubSegments.find(s => s.sub_segment_id === project.sub_segment_id);
    if (!subSegment) throw new Error('Sub-segment not found');
    
    diagLog('EDIT', 'fetchOrgHierarchy-complete', { totalDuration: (performance.now() - hierarchyStart).toFixed(1) + 'ms' });
    return {
      segmentId: subSegment.segment_id,
      subSegmentId: subSegment.sub_segment_id,
      projectId: project.project_id,
      teamId: teamId
    };
  };

  /**
   * Load skills when Skills tab is clicked (lazy loading).
   */
  const loadSkillsForEdit = useCallback(async () => {
    if (skillsLoaded || !employee?.skills) return;
    
    setIsSkillsLoading(true);
    try {
      // Simulate slight delay for UX (skills may already be in memory)
      await new Promise(resolve => setTimeout(resolve, 100));
      
      if (employee.skills && employee.skills.length > 0) {
        setSkills(employee.skills.map(s => ({ ...createEmptySkill(), ...s })));
      }
      setSkillsLoaded(true);
    } finally {
      setIsSkillsLoading(false);
    }
  }, [employee, skillsLoaded]);

  /**
   * Handle tab change - load skills lazily when Skills tab is clicked
   */
  const handleTabChange = useCallback((tab) => {
    setActiveTab(tab);
    if (tab === 'skills' && mode === 'edit' && !skillsLoaded) {
      loadSkillsForEdit();
    }
  }, [mode, skillsLoaded, loadSkillsForEdit]);

  // Reset form when drawer opens/closes or mode changes
  useEffect(() => {
    // ===== DIAGNOSTIC LOGGING =====
    diagLog('EDIT', 'drawer-useEffect-fired', { 
      isOpen, 
      mode, 
      hasEmployee: !!employee,
      employee_id: employee?.employee_id,
      _bootstrapLoaded: employee?._bootstrapLoaded,
      _awaitingBootstrap: employee?._awaitingBootstrap,
      hasBootstrapOptions: !!employee?._bootstrapOptions
    });
    // ===== END DIAGNOSTIC =====
    
    if (isOpen) {
      if (mode === 'edit' && employee) {
        // ===== DIAGNOSTIC LOGGING =====
        editDrawerOpenCount++;
        diagLog('EDIT', 'drawer-open (edit mode)', { 
          openCount: editDrawerOpenCount, 
          employee_id: employee?.employee_id,
          _bootstrapLoaded: employee?._bootstrapLoaded,
          _awaitingBootstrap: employee?._awaitingBootstrap,
          segment_id: employee?.segment_id,
          sub_segment_id: employee?.sub_segment_id,
          project_id: employee?.project_id,
          team_id: employee?.team_id
        });
        // ===== END DIAGNOSTIC =====
        // Edit mode: use sequential loading for dropdowns
        loadEmployeeForEdit(employee);
      } else {
        // Add mode: reset everything
        setIsEditLoading(false);
        setSkillsLoaded(false);
        employeeForm.reset();
        orgAssignment.reset();
        setSkills([createEmptySkill()]);
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
    // Pass employee ID for updates, null for creates
    const employeeIdForUpdate = mode === 'edit' ? employee?.employee_id : null;
    const employeeResult = await employeeForm.submit(orgAssignment, employeeIdForUpdate);
    
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
    const successMessage = mode === 'edit' ? 'Employee updated successfully!' : 'Employee saved successfully!';
    alert(successMessage);
    if (onSave) onSave(employeeResult);
    
    if (mode === 'edit') {
      // In edit mode, close the drawer after successful update
      onClose();
    } else {
      // In add mode, reset form for next entry (instead of closing drawer)
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
    }
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
        {/* Full-page loading overlay while awaiting bootstrap data */}
        {mode === 'edit' && employee?._awaitingBootstrap && (
          <div className="absolute inset-0 bg-gray-900/20 backdrop-blur-[2px] z-50 flex flex-col items-center justify-center cursor-not-allowed">
            <div className="flex flex-col items-center gap-4 bg-white/95 px-8 py-6 rounded-xl shadow-lg">
              <div className="relative">
                <div className="w-10 h-10 border-4 border-blue-200 rounded-full"></div>
                <div className="absolute top-0 left-0 w-10 h-10 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
              </div>
              <div className="text-center">
                <p className="text-base font-medium text-gray-700">
                  Loading {employee?.full_name || 'employee'} data
                </p>
                <p className="text-sm text-gray-500 mt-1">Please wait...</p>
              </div>
            </div>
          </div>
        )}

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
            onClick={() => handleTabChange('details')}
            disabled={isEditLoading}
          >
            Employee Details
            {Object.keys(errors).length > 0 && (
              <span className="error-indicator" />
            )}
          </button>
          <button 
            className={`tab-btn ${activeTab === 'skills' ? 'active' : ''}`}
            onClick={() => handleTabChange('skills')}
            disabled={isEditLoading}
          >
            Skills
            {(skillsError || Object.keys(skillErrors).length > 0) && (
              <span className="error-indicator" />
            )}
          </button>
        </div>

        {/* Body */}
        <div className="drawer-body">
          {/* Edit Loading State */}
          {isEditLoading && (
            <div className="edit-loading-container" data-testid="edit-loading">
              <div className="edit-loading-spinner" />
              <p className="edit-loading-text">Loading employee information…</p>
            </div>
          )}
          
          {/* Tab 1: Employee Details */}
          <div className={`tab-content ${activeTab === 'details' && !isEditLoading ? 'active' : ''}`}>
            {/* Import Info Callout (only in edit mode) */}
            {isEditMode && !isEditLoading && (
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
          <div className={`tab-content ${activeTab === 'skills' && !isEditLoading ? 'active' : ''}`}>
            {/* Skills Loading State (for lazy loading in edit mode) */}
            {isSkillsLoading && (
              <div className="skills-loading-container" data-testid="skills-loading">
                <div className="edit-loading-spinner" />
                <p className="edit-loading-text">Loading skills…</p>
              </div>
            )}
            
            {/* Skills content (only show when not loading) */}
            {!isSkillsLoading && (
              <>
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
              </>
            )}
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
              {isSubmitting ? 'Saving...' : (isEditMode ? 'Update Employee' : 'Save Employee')}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default AddEmployeeDrawer;
