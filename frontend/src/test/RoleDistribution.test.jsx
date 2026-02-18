/**
 * RoleDistribution Component Unit Tests
 * 
 * Tests:
 * 1. Expand/collapse toggle behavior
 * 2. Expand icon class toggles "expanded"
 * 3. Expand not rendered when roles <= 3
 * 4. Groups with sum(counts)==0 are not rendered
 * 5. "+ N more" appears only when N>0
 * 6. Helper functions (getTopRoles, getHiddenRoles, hasRoleData, shouldShowExpand)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import RoleDistribution, {
  getTopRoles,
  getHiddenRoles,
  hasRoleData,
  shouldShowExpand
} from '@/pages/Dashboard/components/RoleDistribution/RoleDistribution.jsx';

// Mock the useRoleDistribution hook
vi.mock('@/hooks/useRoleDistribution', () => ({
  useRoleDistribution: vi.fn()
}));

import { useRoleDistribution } from '@/hooks/useRoleDistribution';

// ============================================
// TEST DATA
// ============================================

const mockRolesWithMoreThan3 = [
  { role_name: 'Frontend Dev', employee_count: 12 },
  { role_name: 'Backend Dev', employee_count: 10 },
  { role_name: 'Full Stack', employee_count: 8 },
  { role_name: 'Cloud Eng', employee_count: 7 },
  { role_name: 'DevOps', employee_count: 6 },
  { role_name: 'QA Engineer', employee_count: 4 }
];

const mockRolesExactly3 = [
  { role_name: 'Frontend Dev', employee_count: 12 },
  { role_name: 'Backend Dev', employee_count: 10 },
  { role_name: 'Full Stack', employee_count: 8 }
];

const mockRolesLessThan3 = [
  { role_name: 'Frontend Dev', employee_count: 5 },
  { role_name: 'Backend Dev', employee_count: 3 }
];

const mockRolesAllZero = [
  { role_name: 'Frontend Dev', employee_count: 0 },
  { role_name: 'Backend Dev', employee_count: 0 }
];

const mockRowWithMoreRoles = {
  breakdown_id: 1,
  breakdown_name: 'ADT',
  total_employees: 54,
  all_roles: mockRolesWithMoreThan3
};

const mockRowWithExactly3Roles = {
  breakdown_id: 2,
  breakdown_name: 'BCD',
  total_employees: 30,
  all_roles: mockRolesExactly3
};

const mockRowWithZeroRoles = {
  breakdown_id: 3,
  breakdown_name: 'Empty Sub',
  total_employees: 0,
  all_roles: mockRolesAllZero
};

const mockDataWithExpandableRows = {
  title: 'Role Distribution by Sub-Segment',
  subtitle: 'Showing breakdown across all sub-segments',
  breakdown_label: 'Sub-Segment',
  rows: [mockRowWithMoreRoles, mockRowWithExactly3Roles]
};

const mockDataWithZeroRowsMixed = {
  title: 'Role Distribution by Sub-Segment',
  subtitle: 'Showing breakdown across all sub-segments',
  breakdown_label: 'Sub-Segment',
  rows: [mockRowWithMoreRoles, mockRowWithZeroRoles]
};

// ============================================
// HELPER FUNCTION TESTS
// ============================================

describe('Helper Functions', () => {
  describe('getTopRoles', () => {
    it('returns top 3 roles sorted by count descending', () => {
      const result = getTopRoles(mockRolesWithMoreThan3);
      expect(result).toHaveLength(3);
      expect(result[0].role_name).toBe('Frontend Dev');
      expect(result[1].role_name).toBe('Backend Dev');
      expect(result[2].role_name).toBe('Full Stack');
    });

    it('returns all roles if less than 3', () => {
      const result = getTopRoles(mockRolesLessThan3);
      expect(result).toHaveLength(2);
    });

    it('returns empty array for null/undefined input', () => {
      expect(getTopRoles(null)).toEqual([]);
      expect(getTopRoles(undefined)).toEqual([]);
    });
  });

  describe('getHiddenRoles', () => {
    it('returns roles beyond visible limit', () => {
      const result = getHiddenRoles(mockRolesWithMoreThan3);
      expect(result).toHaveLength(3);
      expect(result[0].role_name).toBe('Cloud Eng');
      expect(result[1].role_name).toBe('DevOps');
      expect(result[2].role_name).toBe('QA Engineer');
    });

    it('returns empty array when exactly 3 roles', () => {
      const result = getHiddenRoles(mockRolesExactly3);
      expect(result).toHaveLength(0);
    });

    it('returns empty array for less than 3 roles', () => {
      const result = getHiddenRoles(mockRolesLessThan3);
      expect(result).toHaveLength(0);
    });
  });

  describe('hasRoleData', () => {
    it('returns true when at least one role has count > 0', () => {
      expect(hasRoleData(mockRolesWithMoreThan3)).toBe(true);
      expect(hasRoleData(mockRolesLessThan3)).toBe(true);
    });

    it('returns false when all roles have count = 0', () => {
      expect(hasRoleData(mockRolesAllZero)).toBe(false);
    });

    it('returns false for empty/null/undefined', () => {
      expect(hasRoleData([])).toBe(false);
      expect(hasRoleData(null)).toBe(false);
      expect(hasRoleData(undefined)).toBe(false);
    });
  });

  describe('shouldShowExpand', () => {
    it('returns true when more than 3 roles', () => {
      expect(shouldShowExpand(mockRolesWithMoreThan3)).toBe(true);
    });

    it('returns false when exactly 3 roles', () => {
      expect(shouldShowExpand(mockRolesExactly3)).toBe(false);
    });

    it('returns false when less than 3 roles', () => {
      expect(shouldShowExpand(mockRolesLessThan3)).toBe(false);
    });
  });
});

// ============================================
// COMPONENT TESTS
// ============================================

describe('RoleDistribution Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Expand/Collapse Behavior', () => {
    it('clicking group row shows expanded content row', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithExpandableRows,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      // Find the expandable row (ADT has more than 3 roles)
      const adtRow = screen.getByText('ADT').closest('tr');
      expect(adtRow).toBeInTheDocument();
      
      // Initially, expanded content should be hidden
      expect(screen.queryByText('Additional Roles')).not.toBeVisible();
      
      // Click to expand
      fireEvent.click(adtRow);
      
      // Now expanded content should be visible
      expect(screen.getByText('Additional Roles')).toBeVisible();
    });

    it('clicking expanded row again hides content', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithExpandableRows,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      const adtRow = screen.getByText('ADT').closest('tr');
      
      // Click to expand
      fireEvent.click(adtRow);
      expect(screen.getByText('Additional Roles')).toBeVisible();
      
      // Click again to collapse
      fireEvent.click(adtRow);
      expect(screen.queryByText('Additional Roles')).not.toBeVisible();
    });

    it('expanded section only contains roles NOT in top section (no duplication)', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithExpandableRows,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      const adtRow = screen.getByText('ADT').closest('tr');
      
      // Click to expand
      fireEvent.click(adtRow);
      
      // Get the expanded section
      const expandedRow = screen.getByText('Additional Roles').closest('tr');
      
      // Top 3 roles should NOT appear in expanded section
      // (Frontend Dev, Backend Dev, Full Stack are top 3)
      const expandedContent = within(expandedRow);
      
      // These should NOT be in expanded section (they are top 3)
      expect(expandedContent.queryByText('Frontend Dev')).not.toBeInTheDocument();
      expect(expandedContent.queryByText('Backend Dev')).not.toBeInTheDocument();
      expect(expandedContent.queryByText('Full Stack')).not.toBeInTheDocument();
      
      // These SHOULD be in expanded section (they are beyond top 3)
      expect(expandedContent.getByText('Cloud Eng')).toBeInTheDocument();
      expect(expandedContent.getByText('DevOps')).toBeInTheDocument();
      expect(expandedContent.getByText('QA Engineer')).toBeInTheDocument();
    });

    it('expand icon has "expanded" class when expanded', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithExpandableRows,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      const adtRow = screen.getByText('ADT').closest('tr');
      const expandIcon = adtRow.querySelector('.expand-icon');
      
      // Initially not expanded
      expect(expandIcon).not.toHaveClass('expanded');
      
      // Click to expand
      fireEvent.click(adtRow);
      
      // Now has expanded class
      expect(expandIcon).toHaveClass('expanded');
    });

    it('sets aria-expanded correctly on toggle', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithExpandableRows,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      const adtRow = screen.getByText('ADT').closest('tr');
      
      // Initially aria-expanded=false
      expect(adtRow).toHaveAttribute('aria-expanded', 'false');
      
      // Click to expand
      fireEvent.click(adtRow);
      
      // Now aria-expanded=true
      expect(adtRow).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Expand Control Visibility', () => {
    it('does NOT show expand icon when roles <= 3', () => {
      const dataWith3Roles = {
        ...mockDataWithExpandableRows,
        rows: [mockRowWithExactly3Roles]
      };
      
      useRoleDistribution.mockReturnValue({
        data: dataWith3Roles,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      const bcdRow = screen.getByText('BCD').closest('tr');
      const expandIcon = bcdRow.querySelector('.expand-icon');
      
      // No expand icon when <= 3 roles
      expect(expandIcon).toBeNull();
    });

    it('does NOT show "+ N more" indicator when roles <= 3', () => {
      const dataWith3Roles = {
        ...mockDataWithExpandableRows,
        rows: [mockRowWithExactly3Roles]
      };
      
      useRoleDistribution.mockReturnValue({
        data: dataWith3Roles,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      // Should not have "+ N more" text
      expect(screen.queryByText(/\+ \d+ more/)).not.toBeInTheDocument();
    });

    it('shows expand icon when roles > 3', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithExpandableRows,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      const adtRow = screen.getByText('ADT').closest('tr');
      const expandIcon = adtRow.querySelector('.expand-icon');
      
      expect(expandIcon).toBeInTheDocument();
    });

    it('shows "+ N more" with correct count when N > 0', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithExpandableRows,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      // ADT has 6 roles, so should show "+ 3 more"
      expect(screen.getByText('+ 3 more')).toBeInTheDocument();
    });
  });

  describe('Zero Data Filtering', () => {
    it('does NOT render groups with sum(counts) == 0', () => {
      useRoleDistribution.mockReturnValue({
        data: mockDataWithZeroRowsMixed,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      // ADT row should be rendered (has role data)
      expect(screen.getByText('ADT')).toBeInTheDocument();
      
      // Empty Sub should NOT be rendered (all roles have count 0)
      expect(screen.queryByText('Empty Sub')).not.toBeInTheDocument();
    });

    it('shows empty state when all groups have zero data', () => {
      const dataAllZero = {
        ...mockDataWithExpandableRows,
        rows: [mockRowWithZeroRoles]
      };
      
      useRoleDistribution.mockReturnValue({
        data: dataAllZero,
        isLoading: false,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      // Should show empty state
      expect(screen.getByText('No role distribution data')).toBeInTheDocument();
    });
  });

  describe('Loading and Error States', () => {
    it('shows loading skeleton when isLoading=true', () => {
      useRoleDistribution.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: vi.fn()
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      // Should have loading animation class
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('shows error state with retry button on error', () => {
      const mockRefetch = vi.fn();
      useRoleDistribution.mockReturnValue({
        data: null,
        isLoading: false,
        error: { message: 'Network error' },
        refetch: mockRefetch
      });

      render(<RoleDistribution dashboardFilters={{}} />);
      
      expect(screen.getByText('Failed to load role distribution')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
      
      // Click retry
      fireEvent.click(screen.getByText('Retry'));
      expect(mockRefetch).toHaveBeenCalled();
    });
  });
});
