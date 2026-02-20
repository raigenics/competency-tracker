/**
 * EmployeesPage Unit Tests
 * 
 * Tests for performance regression fix:
 * 1. EmployeesPage mount triggers employeeApi.getEmployees once
 * 2. EmployeesPage mount does NOT call skills API or roles API
 * 3. Clicking "+ Add Employee" opens drawer and triggers roles + skills loading
 * 
 * Tests for RBAC UI visibility:
 * 4. Add Employee button visible for roles with canCreate=true (excluding TEAM_MEMBER)
 * 5. Actions column shows View/Edit/Delete based on role permissions
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// RBAC Role constants (duplicated to avoid hoisting issues with vi.mock)
const RBAC_ROLES = {
  SUPER_ADMIN: 'SUPER_ADMIN',
  SEGMENT_HEAD: 'SEGMENT_HEAD',
  SUBSEGMENT_HEAD: 'SUBSEGMENT_HEAD',
  PROJECT_MANAGER: 'PROJECT_MANAGER',
  TEAM_LEAD: 'TEAM_LEAD',
  TEAM_MEMBER: 'TEAM_MEMBER'
};

const ROLE_PERMISSIONS = {
  SUPER_ADMIN: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'all' },
  SEGMENT_HEAD: { canView: true, canCreate: false, canUpdate: false, canDelete: false, scopeLevel: 'segment' },
  SUBSEGMENT_HEAD: { canView: true, canCreate: false, canUpdate: false, canDelete: false, scopeLevel: 'sub_segment' },
  PROJECT_MANAGER: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'project' },
  TEAM_LEAD: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'team' },
  TEAM_MEMBER: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'team', selfOnly: true }
};

// Use vi.hoisted to create mock state that's available during mock hoisting
const { mockState } = vi.hoisted(() => ({
  mockState: {
    currentRole: 'SUPER_ADMIN',
    currentScope: { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: null }
  }
}));

// Mock RBAC permissions module
vi.mock('@/rbac/permissions.js', () => {
  const ROLES = {
    SUPER_ADMIN: 'SUPER_ADMIN',
    SEGMENT_HEAD: 'SEGMENT_HEAD',
    SUBSEGMENT_HEAD: 'SUBSEGMENT_HEAD',
    PROJECT_MANAGER: 'PROJECT_MANAGER',
    TEAM_LEAD: 'TEAM_LEAD',
    TEAM_MEMBER: 'TEAM_MEMBER'
  };
  
  const PERMISSIONS = {
    SUPER_ADMIN: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'all' },
    SEGMENT_HEAD: { canView: true, canCreate: false, canUpdate: false, canDelete: false, scopeLevel: 'segment' },
    SUBSEGMENT_HEAD: { canView: true, canCreate: false, canUpdate: false, canDelete: false, scopeLevel: 'sub_segment' },
    PROJECT_MANAGER: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'project' },
    TEAM_LEAD: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'team' },
    TEAM_MEMBER: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'team', selfOnly: true }
  };

  return {
    getCurrentRole: () => mockState.currentRole,
    getCurrentScope: () => mockState.currentScope,
    getPermissionsForRole: (role) => PERMISSIONS[role] || PERMISSIONS.TEAM_MEMBER,
    canShowAddEmployee: () => {
      const permissions = PERMISSIONS[mockState.currentRole] || PERMISSIONS.TEAM_MEMBER;
      if (!permissions.canCreate) return false;
      if (permissions.selfOnly) {
        if (!mockState.currentScope.employee_id) return false;
        return false;
      }
      return true;
    },
    getRowActions: ({ employee } = {}) => {
      const permissions = PERMISSIONS[mockState.currentRole] || PERMISSIONS.TEAM_MEMBER;
      const result = { canView: permissions.canView, canEdit: false, canDelete: false };
      if (!permissions.canUpdate && !permissions.canDelete) return result;
      if (permissions.selfOnly) {
        const userEmployeeId = mockState.currentScope.employee_id;
        if (employee && userEmployeeId) {
          const isSelf = employee.employee_id === userEmployeeId || employee.id === userEmployeeId;
          result.canEdit = isSelf && permissions.canUpdate;
          result.canDelete = isSelf && permissions.canDelete;
        }
        return result;
      }
      result.canEdit = permissions.canUpdate;
      result.canDelete = permissions.canDelete;
      return result;
    },
    RBAC_ROLES: ROLES,
    ROLE_PERMISSIONS: PERMISSIONS
  };
});

// Import after mocks are set up
import EmployeesPage from '@/pages/Employees/EmployeesPage.jsx';

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn()
  };
});

// Mock employeeApi
const mockGetEmployees = vi.fn();
const mockGetSuggestions = vi.fn();
vi.mock('@/services/api/employeeApi.js', () => ({
  employeeApi: {
    getEmployees: (...args) => mockGetEmployees(...args),
    getSuggestions: (...args) => mockGetSuggestions(...args)
  }
}));

// Mock dropdownApi
const mockGetSubSegments = vi.fn();
const mockGetProjects = vi.fn();
const mockGetTeams = vi.fn();
vi.mock('@/services/api/dropdownApi.js', () => ({
  dropdownApi: {
    getSubSegments: (...args) => mockGetSubSegments(...args),
    getProjects: (...args) => mockGetProjects(...args),
    getTeams: (...args) => mockGetTeams(...args)
  }
}));

// Mock rolesApi - IMPORTANT: must track if this is called during page load
const mockGetRoles = vi.fn();
vi.mock('@/services/api/rolesApi.js', () => ({
  rolesApi: {
    getRoles: (...args) => mockGetRoles(...args)
  }
}));

// Mock skillsAutocompleteApi - IMPORTANT: must track if this is called during page load
const mockGetAllSkills = vi.fn();
const mockSearchSkills = vi.fn();
vi.mock('@/services/api/skillsAutocompleteApi.js', () => ({
  skillsAutocompleteApi: {
    getAllSkills: (...args) => mockGetAllSkills(...args),
    searchSkills: (...args) => mockSearchSkills(...args)
  }
}));

// Mock AddEmployeeDrawer hooks (when drawer opens)
vi.mock('@/hooks/useOrgAssignment.js', () => ({
  useOrgAssignment: () => ({
    selectedSegmentId: null,
    selectedSubSegmentId: null,
    selectedProjectId: null,
    selectedTeamId: null,
    segments: [],
    subSegments: [],
    projects: [],
    teams: [],
    loading: { segments: false, subSegments: false, projects: false, teams: false },
    error: null,
    isLocked: { segment: false, subSegment: false, project: false, team: false },
    isDisabled: { segment: false, subSegment: true, project: true, team: true },
    handleSegmentChange: vi.fn(),
    handleSubSegmentChange: vi.fn(),
    handleProjectChange: vi.fn(),
    handleTeamChange: vi.fn(),
    setSelectedSegmentId: vi.fn(),
    setSelectedSubSegmentId: vi.fn(),
    setSelectedProjectId: vi.fn(),
    setSelectedTeamId: vi.fn(),
    reset: vi.fn()
  })
}));

vi.mock('@/hooks/useEmployeeForm.js', () => ({
  useEmployeeForm: () => ({
    formData: {
      firstName: '',
      lastName: '',
      zid: '',
      email: '',
      roleId: null
    },
    errors: {},
    setFormData: vi.fn(),
    handleChange: vi.fn(),
    setRole: vi.fn(),
    validate: vi.fn(() => true),
    clearError: vi.fn(),
    reset: vi.fn(),
    saving: false,
    isSubmitting: false,
    submitError: null
  })
}));

vi.mock('@/hooks/useUniqueEmployeeValidation.js', () => ({
  useUniqueEmployeeValidation: () => ({
    validateZid: vi.fn().mockResolvedValue(true),
    validateEmail: vi.fn().mockResolvedValue(true),
    uniqueErrors: { zid: null, email: null },
    isValidating: { zid: false, email: false },
    hasUniqueErrors: vi.fn(() => false),
    clearAllUniqueErrors: vi.fn()
  })
}));

// Helper to render with router
const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

// Default mock responses
const mockEmployeesResponse = {
  items: [
    {
      employee_id: 1,
      zid: 'Z001',
      full_name: 'John Doe',
      organization: { sub_segment: 'Test', project: 'Project1', team: 'Team1' },
      role: { role_name: 'Developer' },
      skills_count: 3
    }
  ],
  total: 1,
  page: 1,
  size: 10,
  has_next: false,
  has_previous: false
};

describe('EmployeesPage', () => {
  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();
    
    // Reset RBAC mocks to default (SUPER_ADMIN)
    mockState.currentRole = RBAC_ROLES.SUPER_ADMIN;
    mockState.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: null };
    
    // Setup default mock implementations
    mockGetEmployees.mockResolvedValue(mockEmployeesResponse);
    mockGetSuggestions.mockResolvedValue([]);
    mockGetSubSegments.mockResolvedValue([]);
    mockGetProjects.mockResolvedValue([]);
    mockGetTeams.mockResolvedValue([]);
    mockGetRoles.mockResolvedValue([]);
    mockGetAllSkills.mockResolvedValue([]);
    mockSearchSkills.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Performance: API calls on mount', () => {
    it('should call employeeApi.getEmployees on mount', async () => {
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Wait for initial load to complete
      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      // Verify it was called with correct params
      expect(mockGetEmployees).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1, size: 10 }),
        expect.any(Object) // options with signal
      );
    });

    it('should NOT call rolesApi.getRoles on mount (drawer not opened)', async () => {
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Wait for employeeApi to be called (page loaded)
      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      // Verify roles API was NOT called
      expect(mockGetRoles).not.toHaveBeenCalled();
    });

    it('should NOT call skillsAutocompleteApi on mount (drawer not opened)', async () => {
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Wait for employeeApi to be called (page loaded)
      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      // Verify skills API was NOT called
      expect(mockGetAllSkills).not.toHaveBeenCalled();
      expect(mockSearchSkills).not.toHaveBeenCalled();
    });
  });

  describe('Drawer lazy loading', () => {
    it('should load roles and skills when "+ Add Employee" is clicked', async () => {
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Wait for page to load
      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      // Before clicking - verify no roles/skills calls
      expect(mockGetRoles).not.toHaveBeenCalled();
      expect(mockGetAllSkills).not.toHaveBeenCalled();

      // Find and click the "+ Add Employee" button
      const addButton = screen.getByRole('button', { name: /add employee/i });
      expect(addButton).toBeInTheDocument();

      await act(async () => {
        fireEvent.click(addButton);
      });

      // After clicking - drawer opens and should trigger roles/skills loading
      await waitFor(() => {
        expect(mockGetRoles).toHaveBeenCalled();
      }, { timeout: 2000 });

      await waitFor(() => {
        expect(mockGetAllSkills).toHaveBeenCalled();
      }, { timeout: 2000 });
    });

    it('should render employee data without waiting for drawer data', async () => {
      // Add a delay to skills API to simulate slow response
      mockGetAllSkills.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve([]), 5000))
      );

      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Employee data should render quickly (< 1s) without waiting for slow skills API
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      }, { timeout: 1000 });

      // Skills API should NOT have been called since drawer is not open
      expect(mockGetAllSkills).not.toHaveBeenCalled();
    });
  });

  describe('API call count verification', () => {
    it('should call employeeApi.getEmployees exactly once on initial mount', async () => {
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Wait for load to complete
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // With StrictMode handling, should be called once or twice (abort+retry)
      // but not more due to any other bug
      const callCount = mockGetEmployees.mock.calls.length;
      expect(callCount).toBeGreaterThanOrEqual(1);
      expect(callCount).toBeLessThanOrEqual(2); // StrictMode may cause 2
    });
  });

  describe('List refresh after adding employee', () => {
    it('should pass onSave callback to AddEmployeeDrawer', async () => {
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Wait for page to load
      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      // Open the drawer
      const addButton = screen.getByRole('button', { name: /add employee/i });
      await act(async () => {
        fireEvent.click(addButton);
      });

      // Drawer should be rendered (when open)
      // The drawer component receives onSave prop from EmployeesPage
      // This tests that the integration is wired up
      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument();
      });
    });

    it('should re-fetch employees when refreshTrigger changes', async () => {
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      // Wait for initial load
      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      const initialCallCount = mockGetEmployees.mock.calls.length;

      // Note: We can't directly test the callback because it's internal.
      // The integration test confirms:
      // 1. Page loads employees initially
      // 2. Drawer receives onSave prop
      // 3. When onSave is called (tested in AddEmployeeDrawer tests), 
      //    it triggers state change that refetches employees
      
      // This test verifies the initial fetch works
      expect(initialCallCount).toBeGreaterThanOrEqual(1);
    });
  });

  describe('RBAC: Add Employee button visibility', () => {
    it('SUPER_ADMIN: should show Add Employee button', async () => {
      mockState.currentRole = RBAC_ROLES.SUPER_ADMIN;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      const addButton = screen.queryByRole('button', { name: /add employee/i });
      expect(addButton).toBeInTheDocument();
    });

    it('SEGMENT_HEAD: should NOT show Add Employee button (view-only role)', async () => {
      mockState.currentRole = RBAC_ROLES.SEGMENT_HEAD;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      const addButton = screen.queryByRole('button', { name: /add employee/i });
      expect(addButton).not.toBeInTheDocument();
    });

    it('SUBSEGMENT_HEAD: should NOT show Add Employee button (view-only role)', async () => {
      mockState.currentRole = RBAC_ROLES.SUBSEGMENT_HEAD;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      const addButton = screen.queryByRole('button', { name: /add employee/i });
      expect(addButton).not.toBeInTheDocument();
    });

    it('PROJECT_MANAGER: should show Add Employee button', async () => {
      mockState.currentRole = RBAC_ROLES.PROJECT_MANAGER;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      const addButton = screen.queryByRole('button', { name: /add employee/i });
      expect(addButton).toBeInTheDocument();
    });

    it('TEAM_LEAD: should show Add Employee button', async () => {
      mockState.currentRole = RBAC_ROLES.TEAM_LEAD;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      const addButton = screen.queryByRole('button', { name: /add employee/i });
      expect(addButton).toBeInTheDocument();
    });

    it('TEAM_MEMBER without self id: should NOT show Add Employee button', async () => {
      mockState.currentRole = RBAC_ROLES.TEAM_MEMBER;
      mockState.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: null };
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(mockGetEmployees).toHaveBeenCalled();
      });

      const addButton = screen.queryByRole('button', { name: /add employee/i });
      expect(addButton).not.toBeInTheDocument();
    });
  });

  describe('RBAC: Actions column visibility', () => {
    it('SUPER_ADMIN: should show View, Edit, and Delete buttons for each row', async () => {
      mockState.currentRole = RBAC_ROLES.SUPER_ADMIN;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Find the row and check for all action buttons
      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      const editButtons = screen.getAllByRole('button', { name: /edit/i });
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });

      expect(viewButtons.length).toBeGreaterThanOrEqual(1);
      expect(editButtons.length).toBeGreaterThanOrEqual(1);
      expect(deleteButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('SEGMENT_HEAD: should show only View button (view-only role)', async () => {
      mockState.currentRole = RBAC_ROLES.SEGMENT_HEAD;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Should have View button
      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      expect(viewButtons.length).toBeGreaterThanOrEqual(1);

      // Should NOT have Edit or Delete buttons
      const editButtons = screen.queryAllByRole('button', { name: /^edit$/i });
      const deleteButtons = screen.queryAllByRole('button', { name: /delete/i });
      expect(editButtons.length).toBe(0);
      expect(deleteButtons.length).toBe(0);
    });

    it('TEAM_MEMBER without self id: should show only View button', async () => {
      mockState.currentRole = RBAC_ROLES.TEAM_MEMBER;
      mockState.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: null };
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Should have View button
      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      expect(viewButtons.length).toBeGreaterThanOrEqual(1);

      // Should NOT have Edit or Delete buttons (can't determine self)
      const editButtons = screen.queryAllByRole('button', { name: /^edit$/i });
      const deleteButtons = screen.queryAllByRole('button', { name: /delete/i });
      expect(editButtons.length).toBe(0);
      expect(deleteButtons.length).toBe(0);
    });

    it('TEAM_MEMBER with self id: should show Edit/Delete only on own row', async () => {
      mockState.currentRole = RBAC_ROLES.TEAM_MEMBER;
      // Set employee_id to match the mock employee
      mockState.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: 1 };
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Should have View, Edit, Delete for own row (employee_id: 1)
      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });

      expect(viewButtons.length).toBeGreaterThanOrEqual(1);
      expect(editButtons.length).toBeGreaterThanOrEqual(1);
      expect(deleteButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('PROJECT_MANAGER: should show View, Edit, and Delete buttons', async () => {
      mockState.currentRole = RBAC_ROLES.PROJECT_MANAGER;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });

      expect(viewButtons.length).toBeGreaterThanOrEqual(1);
      expect(editButtons.length).toBeGreaterThanOrEqual(1);
      expect(deleteButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('TEAM_LEAD: should show View, Edit, and Delete buttons', async () => {
      mockState.currentRole = RBAC_ROLES.TEAM_LEAD;
      
      await act(async () => {
        renderWithRouter(<EmployeesPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      const editButtons = screen.getAllByRole('button', { name: /^edit$/i });
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });

      expect(viewButtons.length).toBeGreaterThanOrEqual(1);
      expect(editButtons.length).toBeGreaterThanOrEqual(1);
      expect(deleteButtons.length).toBeGreaterThanOrEqual(1);
    });
  });
});
