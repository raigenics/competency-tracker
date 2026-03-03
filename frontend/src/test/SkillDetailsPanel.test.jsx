/**
 * Unit tests for SkillDetailsPanel component (Capability Overview page)
 * 
 * Tests:
 * 1. Initial empty state - "Select a skill" message when no skill is selected
 * 2. Skill summary view when a skill is selected
 * 3. View Profile click opens drawer (matches Skill Search behavior)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SkillDetailsPanel from '@/pages/Taxonomy/components/SkillDetailsPanel';

// Mock the APIs
vi.mock('@/services/api/skillApi', () => ({
  skillApi: {
    getSkillSummary: vi.fn(),
    getSkill: vi.fn(),
    getCapabilitySnapshot: vi.fn(),
    getProficiencyBreakdown: vi.fn(),
    getLeadingSubSegment: vi.fn(),
    getEmployeesSummary: vi.fn(),
    getEmployeesList: vi.fn()
  }
}));

vi.mock('@/services/api/employeeApi', () => ({
  employeeApi: {
    getEmployeesByIds: vi.fn(),
    getEmployeeProfile: vi.fn()
  }
}));

// Mock talentExportService
vi.mock('@/services/talentExportService', () => ({
  default: {
    exportToExcel: vi.fn()
  }
}));

// Mock EmployeeProfileDrawer to track its props
vi.mock('@/components/EmployeeProfileDrawer', () => ({
  default: vi.fn(({ isOpen, employeeId, onClose }) => (
    isOpen ? (
      <div data-testid="employee-profile-drawer" data-employee-id={employeeId}>
        <button onClick={onClose}>Close Drawer</button>
        Mock Drawer for Employee {employeeId}
      </div>
    ) : null
  ))
}));

// Helper to render with router
const renderWithRouter = (component) => {
  return render(
    <MemoryRouter>
      {component}
    </MemoryRouter>
  );
};

describe('SkillDetailsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Empty State', () => {
    it('shows Sub-Segments Capability Summary when skill is null', () => {
      renderWithRouter(
        <SkillDetailsPanel 
          skill={null}
          showViewAll={false}
          onViewAll={() => {}}
          onBackToSummary={() => {}}
        />
      );

      // Check for summary heading
      expect(screen.getByRole('heading', { name: /sub-segments capability summary/i })).toBeInTheDocument();
      
      // Check for category coverage cards
      expect(screen.getByText(/most populated category/i)).toBeInTheDocument();
      expect(screen.getByText(/least populated category/i)).toBeInTheDocument();
    });

    it('shows Sub-Segments Capability Summary when skill is undefined', () => {
      renderWithRouter(
        <SkillDetailsPanel 
          skill={undefined}
          showViewAll={false}
          onViewAll={() => {}}
          onBackToSummary={() => {}}
        />
      );

      expect(screen.getByRole('heading', { name: /sub-segments capability summary/i })).toBeInTheDocument();
    });

    it('shows hint list in empty state', () => {
      renderWithRouter(
        <SkillDetailsPanel 
          skill={null}
          showViewAll={false}
          onViewAll={() => {}}
          onBackToSummary={() => {}}
        />
      );

      // Check for hint items
      expect(screen.getByText(/use search to jump to technologies/i)).toBeInTheDocument();
      expect(screen.getByText(/expand categories to compare skill density/i)).toBeInTheDocument();
    });

    it('shows "No employees in scope" when categoryCoverage returns null categories', () => {
      // When API returns null for both most_populated_category and least_populated_category
      renderWithRouter(
        <SkillDetailsPanel 
          skill={null}
          showViewAll={false}
          onViewAll={() => {}}
          onBackToSummary={() => {}}
          categoryCoverage={{
            most_populated_category: null,
            least_populated_category: null
          }}
          categoryCoverageLoading={false}
          categoryCoverageError={null}
        />
      );

      // Hardcoded fallbacks should NOT be rendered
      expect(screen.queryByText('Programming')).not.toBeInTheDocument();
      expect(screen.queryByText('Mobile Development')).not.toBeInTheDocument();
      expect(screen.queryByText(/14 skills/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/4 skills/i)).not.toBeInTheDocument();

      // "No employees in scope" should be rendered for both cards
      const noEmployeesMessages = screen.getAllByText('No employees in scope');
      expect(noEmployeesMessages).toHaveLength(2);
    });
  });

  describe('Skill Selected State', () => {
    it('does not show empty state when skill is provided', async () => {
      const mockSkill = {
        skill_id: 1,
        name: 'React',
        category_name: 'Frontend',
        subcategory_name: 'JavaScript Frameworks'
      };

      const { skillApi } = await import('@/services/api/skillApi');
      skillApi.getSkillSummary.mockResolvedValue({
        skill_id: 1,
        skill_name: 'React',
        employee_count: 10,
        certified_count: 5,
        employee_ids: [1, 2, 3]
      });

      renderWithRouter(
        <SkillDetailsPanel 
          skill={mockSkill}
          showViewAll={false}
          onViewAll={() => {}}
          onBackToSummary={() => {}}
        />
      );

      // Should NOT show the empty state message
      expect(screen.queryByText(/select a skill from the tree/i)).not.toBeInTheDocument();
    });
  });

  describe('Employee List View - View Profile Drawer', () => {
    it('renders View Profile buttons that open the drawer (not links)', async () => {
      const mockSkill = {
        skill_id: 1,
        name: 'React',
        category_name: 'Frontend',
        subcategory_name: 'JavaScript Frameworks'
      };

      const mockEmployees = [
        {
          id: 42,
          name: 'John Doe',
          subSegment: 'Engineering',
          project: 'Project Alpha',
          role: 'Developer',
          team: 'Team A',
          skills: [{ name: 'React', proficiency: 4 }]
        },
        {
          id: 99,
          name: 'Jane Smith',
          subSegment: 'Design',
          project: 'Project Beta',
          role: 'Designer',
          team: 'Team B',
          skills: [{ name: 'React', proficiency: 3 }]
        }
      ];

      const { skillApi } = await import('@/services/api/skillApi');

      skillApi.getSkillSummary.mockResolvedValue({
        skill_id: 1,
        skill_name: 'React',
        employee_count: 2,
        certified_count: 1,
        employee_ids: [42, 99]
      });

      // Mock the new getEmployeesList API
      skillApi.getEmployeesList.mockResolvedValue({
        skill_id: 1,
        skill_name: 'React',
        employees: mockEmployees.map(emp => ({
          employee_id: emp.id,
          employee_name: emp.name,
          sub_segment: emp.subSegment,
          team_name: emp.team,
          proficiency_level: 4,
          proficiency_label: 'Proficient',
          certified: false,
          skill_last_updated_days: 10
        })),
        total_count: mockEmployees.length
      });

      // Mock getEmployeesSummary for header KPIs
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 2,
        avg_proficiency: 3.5,
        certified_count: 1,
        team_count: 2
      });

      renderWithRouter(
        <SkillDetailsPanel 
          skill={mockSkill}
          showViewAll={true}
          onViewAll={() => {}}
          onBackToSummary={() => {}}
        />
      );

      // Wait for employees to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // View Profile should be buttons, NOT links (drawer behavior)
      const viewProfileButtons = screen.getAllByRole('button', { name: /view profile/i });
      expect(viewProfileButtons).toHaveLength(2);

      // Should NOT be links (no href attribute)
      expect(screen.queryAllByRole('link', { name: /view profile/i })).toHaveLength(0);
    });

    it('clicking View Profile opens the drawer with correct employee', async () => {
      const mockSkill = {
        skill_id: 1,
        name: 'React',
        category_name: 'Frontend',
        subcategory_name: 'JavaScript Frameworks'
      };

      const mockEmployees = [
        {
          id: 42,
          name: 'John Doe',
          subSegment: 'Engineering',
          project: 'Project Alpha',
          role: 'Developer',
          team: 'Team A',
          skills: [{ name: 'React', proficiency: 4 }]
        }
      ];

      const { skillApi } = await import('@/services/api/skillApi');

      skillApi.getSkillSummary.mockResolvedValue({
        skill_id: 1,
        skill_name: 'React',
        employee_count: 1,
        certified_count: 0,
        employee_ids: [42]
      });

      // Mock the new getEmployeesList API
      skillApi.getEmployeesList.mockResolvedValue({
        skill_id: 1,
        skill_name: 'React',
        employees: mockEmployees.map(emp => ({
          employee_id: emp.id,
          employee_name: emp.name,
          sub_segment: emp.subSegment,
          team_name: emp.team,
          proficiency_level: 4,
          proficiency_label: 'Proficient',
          certified: false,
          skill_last_updated_days: 10
        })),
        total_count: mockEmployees.length
      });

      // Mock getEmployeesSummary for header KPIs
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 1,
        avg_proficiency: 4.0,
        certified_count: 0,
        team_count: 1
      });

      renderWithRouter(
        <SkillDetailsPanel 
          skill={mockSkill}
          showViewAll={true}
          onViewAll={() => {}}
          onBackToSummary={() => {}}
        />
      );

      // Wait for employees to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Drawer should not be visible initially
      expect(screen.queryByTestId('employee-profile-drawer')).not.toBeInTheDocument();

      // Click View Profile button
      const viewProfileButton = screen.getByRole('button', { name: /view profile/i });
      fireEvent.click(viewProfileButton);

      // Drawer should now be visible with correct employee ID
      await waitFor(() => {
        const drawer = screen.getByTestId('employee-profile-drawer');
        expect(drawer).toBeInTheDocument();
        expect(drawer).toHaveAttribute('data-employee-id', '42');
      });
    });
  });
});
