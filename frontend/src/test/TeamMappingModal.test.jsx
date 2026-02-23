/**
 * Unit tests for TeamMappingModal component
 * 
 * Tests the Team Mapping modal including:
 * - API call to fetch teams when modal opens
 * - Displaying teams from API response
 * - Search filtering
 * - Error handling
 * - Map button calls API and triggers callback
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TeamMappingModal from '@/pages/BulkImport/TeamMappingModal.jsx';

// Mock bulkImportApi
vi.mock('@/services/api/bulkImportApi.js', () => ({
  bulkImportApi: {
    getTeamsForMapping: vi.fn(),
    mapTeam: vi.fn()
  }
}));

// Get mocked module
import { bulkImportApi } from '@/services/api/bulkImportApi.js';

describe('TeamMappingModal', () => {
  const mockFailedRow = {
    error_code: 'MISSING_TEAM',
    team_name: 'eCOM Ops (DevOps)',
    project_name: 'IT Project',
    project_id: 10,
    employee_name: 'John Doe',
    zid: 'Z12345',
    resolved: false
  };

  const mockImportRunId = 'test-job-uuid-123';
  const mockFailedRowIndex = 0;

  const mockTeamsResponse = {
    total_count: 3,
    project_id: 10,
    project_name: 'IT Project',
    teams: [
      {
        team_id: 1,
        team_name: 'DevOps Team',
        project_id: 10
      },
      {
        team_id: 2,
        team_name: 'Backend Team',
        project_id: 10
      },
      {
        team_id: 3,
        team_name: 'Frontend Team',
        project_id: 10
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // API Call on Modal Open
  // =========================================================================
  describe('API Call on Modal Open', () => {
    it('should call getTeamsForMapping API when modal opens', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Assert - API should be called with correct args
      await waitFor(() => {
        expect(bulkImportApi.getTeamsForMapping).toHaveBeenCalledTimes(1);
        expect(bulkImportApi.getTeamsForMapping).toHaveBeenCalledWith(
          mockImportRunId,
          10 // project_id
        );
      });
    });

    it('should display teams from API response', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Assert - teams should be displayed
      await waitFor(() => {
        expect(screen.getByText('DevOps Team')).toBeInTheDocument();
        expect(screen.getByText('Backend Team')).toBeInTheDocument();
        expect(screen.getByText('Frontend Team')).toBeInTheDocument();
      });
    });

    it('should display project name from failed row', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Assert - project name should be displayed
      await waitFor(() => {
        expect(screen.getByText('IT Project')).toBeInTheDocument();
      });
    });

    it('should display error when project_id is missing and NOT call API', async () => {
      // Arrange
      const failedRowNoProject = {
        ...mockFailedRow,
        project_id: undefined
      };

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={failedRowNoProject}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Assert - should show the exact support message
      await waitFor(() => {
        expect(screen.getByText('Cannot load teams: missing project information. Please contact support.')).toBeInTheDocument();
      });
      
      // API should NOT have been called
      expect(bulkImportApi.getTeamsForMapping).not.toHaveBeenCalled();
    });
  });

  // =========================================================================
  // Search Filtering
  // =========================================================================
  describe('Search Filtering', () => {
    it('should filter teams as user types', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Wait for teams to load
      await waitFor(() => {
        expect(screen.getByText('DevOps Team')).toBeInTheDocument();
      });

      // Type in search
      const searchInput = screen.getByPlaceholderText('Search teams...');
      fireEvent.change(searchInput, { target: { value: 'backend' } });

      // Assert - only Backend Team should be visible
      await waitFor(() => {
        expect(screen.getByText('Backend Team')).toBeInTheDocument();
        expect(screen.queryByText('DevOps Team')).not.toBeInTheDocument();
        expect(screen.queryByText('Frontend Team')).not.toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Team Mapping
  // =========================================================================
  describe('Team Mapping', () => {
    it('should disable Map button when no team is selected', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Wait for teams to load
      await waitFor(() => {
        expect(screen.getByText('DevOps Team')).toBeInTheDocument();
      });

      // Assert - Map button should be disabled
      const mapButton = screen.getByRole('button', { name: /map to selected team/i });
      expect(mapButton).toBeDisabled();
    });

    it('should enable Map button when team is selected', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Wait for teams to load
      await waitFor(() => {
        expect(screen.getByText('DevOps Team')).toBeInTheDocument();
      });

      // Select a team
      const teamRadio = screen.getAllByRole('radio')[0];
      fireEvent.click(teamRadio);

      // Assert - Map button should be enabled
      const mapButton = screen.getByRole('button', { name: /map to selected team/i });
      expect(mapButton).not.toBeDisabled();
    });

    it('should call mapTeam API and trigger callback on success', async () => {
      // Arrange
      const onMapped = vi.fn();
      const onClose = vi.fn();
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);
      bulkImportApi.mapTeam.mockResolvedValueOnce({
        failed_row_index: 0,
        mapped_team_id: 1,
        mapped_team_name: 'DevOps Team',
        project_id: 10,
        project_name: 'IT Project',
        message: 'Successfully mapped',
        alias_persisted: true
      });

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={onClose}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={onMapped}
        />
      );

      // Wait for teams to load
      await waitFor(() => {
        expect(screen.getByText('DevOps Team')).toBeInTheDocument();
      });

      // Select a team
      const teamRadio = screen.getAllByRole('radio')[0];
      fireEvent.click(teamRadio);

      // Click Map button
      const mapButton = screen.getByRole('button', { name: /map to selected team/i });
      fireEvent.click(mapButton);

      // Assert - API should be called and callbacks triggered
      await waitFor(() => {
        expect(bulkImportApi.mapTeam).toHaveBeenCalledWith(
          mockImportRunId,
          0, // failedRowIndex
          1  // team_id
        );
        expect(onMapped).toHaveBeenCalledWith({
          failed_row_index: 0,
          mapped_team_id: 1,
          mapped_team_name: 'DevOps Team',
          project_id: 10,
          project_name: 'IT Project',
          message: 'Successfully mapped',
          alias_persisted: true
        });
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  // =========================================================================
  // Error Handling
  // =========================================================================
  describe('Error Handling', () => {
    it('should display error message when API fails to load teams', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockRejectedValueOnce(new Error('Network error'));

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/unable to load teams/i)).toBeInTheDocument();
      });
    });

    it('should display 409 conflict error correctly', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);
      bulkImportApi.mapTeam.mockRejectedValueOnce({
        response: {
          status: 409,
          data: { detail: "Alias 'eCOM Ops' already mapped to 'Other Team'" }
        }
      });

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Wait for teams and select one
      await waitFor(() => {
        expect(screen.getByText('DevOps Team')).toBeInTheDocument();
      });

      const teamRadio = screen.getAllByRole('radio')[0];
      fireEvent.click(teamRadio);

      const mapButton = screen.getByRole('button', { name: /map to selected team/i });
      fireEvent.click(mapButton);

      // Assert - error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/already mapped/i)).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Admin Contact Info
  // =========================================================================
  describe('Admin Contact Info', () => {
    it('should display message about contacting admin for team creation', async () => {
      // Arrange
      bulkImportApi.getTeamsForMapping.mockResolvedValueOnce(mockTeamsResponse);

      // Act
      render(
        <TeamMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          failedRow={mockFailedRow}
          failedRowIndex={mockFailedRowIndex}
          onMapped={vi.fn()}
        />
      );

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/contact your administrator/i)).toBeInTheDocument();
      });
    });
  });
});
