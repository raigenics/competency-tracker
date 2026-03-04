/**
 * Unit tests for ViewEmployeesHeader component
 * 
 * Tests:
 * 1. KPI cards render dynamic values when API returns data
 * 2. KPI cards render fallback values when data is null
 * 3. Loading state shows proper indicators
 * 4. API is called with correct skillId
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ViewEmployeesHeader from '@/pages/Taxonomy/components/ViewEmployeesHeader';
import { skillApi } from '@/services/api/skillApi';

// Mock the skillApi
vi.mock('@/services/api/skillApi', () => ({
  skillApi: {
    getEmployeesSummary: vi.fn()
  }
}));

describe('ViewEmployeesHeader', () => {
  const defaultProps = {
    skillId: 42,
    skillName: 'Python',
    onBack: vi.fn(),
    onExport: vi.fn(),
    employeeResults: [],
    onSearchChange: vi.fn(),
    searchValue: '',
    onClear: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('KPI Cards Dynamic Data Binding', () => {
    it('renders KPI values from API response', async () => {
      // Arrange
      const mockSummary = {
        employee_count: 128,
        avg_proficiency: 3.5,
        certified_count: 36,
        team_count: 14
      };
      skillApi.getEmployeesSummary.mockResolvedValue(mockSummary);

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert - wait for API data to load
      await waitFor(() => {
        expect(screen.getByText('3.5')).toBeInTheDocument(); // Avg proficiency
      });
      expect(screen.getByText('36')).toBeInTheDocument(); // Certified
      expect(screen.getByText('14')).toBeInTheDocument(); // Teams
    });

    it('calls getEmployeesSummary with correct skillId', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 2.5,
        certified_count: 5,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} skillId={123} />);

      // Assert
      await waitFor(() => {
        expect(skillApi.getEmployeesSummary).toHaveBeenCalledWith(123);
      });
    });

    it('refetches data when skillId changes', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 2.5,
        certified_count: 5,
        team_count: 3
      });

      // Act - initial render
      const { rerender } = render(<ViewEmployeesHeader {...defaultProps} skillId={42} />);
      await waitFor(() => {
        expect(skillApi.getEmployeesSummary).toHaveBeenCalledWith(42);
      });

      // Act - change skillId
      rerender(<ViewEmployeesHeader {...defaultProps} skillId={99} />);
      
      // Assert
      await waitFor(() => {
        expect(skillApi.getEmployeesSummary).toHaveBeenCalledWith(99);
      });
      expect(skillApi.getEmployeesSummary).toHaveBeenCalledTimes(2);
    });
  });

  describe('KPI Cards Fallback Values', () => {
    it('renders "—" for avg_proficiency when null', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: null,
        certified_count: 5,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert
      await waitFor(() => {
        // Find the avg proficiency value - should show dash
        const avgValue = screen.getAllByText('—')[0]; // May be multiple dashes
        expect(avgValue).toBeInTheDocument();
      });
    });

    it('renders "0" for certified_count when zero', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 3.0,
        certified_count: 0,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText('3.0')).toBeInTheDocument(); // avg loads
      });
      // Certified KPI card should show 0 - use the KPI value container
      const certifiedKPI = screen.getByText('Certified').closest('.ve-kpi');
      expect(certifiedKPI.querySelector('.ve-kpi-value').textContent).toBe('0');
    });

    it('renders "0" for team_count when zero', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 3.0,
        certified_count: 5,
        team_count: 0
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText('3.0')).toBeInTheDocument();
      });
      // Teams should show 0
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBeGreaterThan(0);
    });

    it('renders fallback values when API fails', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockRejectedValue(new Error('API Error'));

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert - after loading completes, fallbacks should show
      await waitFor(() => {
        // Avg proficiency shows dash
        const dashElements = screen.getAllByText('—');
        expect(dashElements.length).toBeGreaterThan(0);
      });
    });

    it('does not fetch when skillId is null', async () => {
      // Act
      render(<ViewEmployeesHeader {...defaultProps} skillId={null} />);

      // Wait a bit to ensure no call is made
      await new Promise(resolve => setTimeout(resolve, 100));

      // Assert
      expect(skillApi.getEmployeesSummary).not.toHaveBeenCalled();
    });

    it('does not fetch when skillId is undefined', async () => {
      // Act
      render(<ViewEmployeesHeader {...defaultProps} skillId={undefined} />);

      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 100));

      // Assert
      expect(skillApi.getEmployeesSummary).not.toHaveBeenCalled();
    });

    it('fetches when skillId is 0 (valid ID)', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 0,
        avg_proficiency: 0,
        certified_count: 0,
        team_count: 0
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} skillId={0} />);

      // Assert
      await waitFor(() => {
        expect(skillApi.getEmployeesSummary).toHaveBeenCalledWith(0);
      });
    });
  });

  describe('Loading State', () => {
    it('shows loading indicator while fetching', async () => {
      // Arrange - make API slow
      let resolvePromise;
      skillApi.getEmployeesSummary.mockImplementation(() => 
        new Promise(resolve => { resolvePromise = resolve; })
      );

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert - loading should show "..."
      expect(screen.getAllByText('...').length).toBeGreaterThan(0);

      // Cleanup - resolve the promise
      resolvePromise({ employee_count: 10, avg_proficiency: 3.0, certified_count: 5, team_count: 3 });
    });
  });

  describe('KPI Tags', () => {
    it('shows "Strong" tag for avg_proficiency >= 4.0', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 4.2,
        certified_count: 5,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert - find the avg proficiency KPI specifically
      await waitFor(() => {
        const avgKPI = screen.getByText('Avg proficiency').closest('.ve-kpi');
        expect(avgKPI.querySelector('.ve-tag').textContent).toBe('Strong');
      });
    });

    it('shows "Distributed" tag for team_count >= 3', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 3.0,
        certified_count: 5,
        team_count: 5
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Distributed')).toBeInTheDocument();
      });
    });
  });

  describe('Regression: Header Structure Unchanged', () => {
    it('renders back button', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 3.0,
        certified_count: 5,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert
      expect(screen.getByText('← Back')).toBeInTheDocument();
    });

    it('renders skill name pill', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 3.0,
        certified_count: 5,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} skillName="Python" />);

      // Assert
      expect(screen.getByText('Python')).toBeInTheDocument();
    });

    it('renders "Employees with" title', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 3.0,
        certified_count: 5,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert
      expect(screen.getByText('Employees with')).toBeInTheDocument();
    });

    it('renders all 3 KPI labels', async () => {
      // Arrange
      skillApi.getEmployeesSummary.mockResolvedValue({
        employee_count: 10,
        avg_proficiency: 3.0,
        certified_count: 5,
        team_count: 3
      });

      // Act
      render(<ViewEmployeesHeader {...defaultProps} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Avg proficiency')).toBeInTheDocument();
        expect(screen.getByText('Certified')).toBeInTheDocument();
        expect(screen.getByText('Teams')).toBeInTheDocument();
      });
    });
  });
});
