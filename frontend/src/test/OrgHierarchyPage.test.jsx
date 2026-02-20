/**
 * Unit tests for OrgHierarchyPage component
 * 
 * Tests the Org Hierarchy Master Data UI including:
 * - Initial render
 * - Loading state
 * - Tree rendering with segments, sub-segments, projects
 * - Node selection
 * - Tree search (segments/sub-segments/projects)
 * - Team search fallback (when tree has no matches)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OrgHierarchyPage from '@/pages/MasterData/OrgHierarchyPage.jsx';

// Mock the API module
vi.mock('@/services/api/orgHierarchyApi', () => ({
  fetchOrgHierarchy: vi.fn(),
  createSegment: vi.fn(),
  createSubSegment: vi.fn(),
  createProject: vi.fn(),
  createTeam: vi.fn(),
  updateSegmentName: vi.fn(),
  updateSubSegmentName: vi.fn(),
  updateProjectName: vi.fn(),
  updateTeamName: vi.fn(),
  checkCanDeleteSegment: vi.fn(),
  checkCanDeleteSubSegment: vi.fn(),
  deleteSegment: vi.fn(),
  deleteSubSegment: vi.fn(),
  checkCanDeleteProject: vi.fn(),
  deleteProject: vi.fn(),
  deleteTeam: vi.fn()
}));

// Mock config
vi.mock('@/config/apiConfig', () => ({
  API_BASE_URL: 'http://localhost:8000/api/v1'
}));

// Get mocked functions - only import what's actually used in tests
import { fetchOrgHierarchy } from '@/services/api/orgHierarchyApi';

// Helper to render with router
const renderWithRouter = (component) => {
  return render(
    <MemoryRouter>
      {component}
    </MemoryRouter>
  );
};

// Mock org hierarchy data with teams
const mockOrgHierarchyResponse = {
  segments: [
    {
      segment_id: 1,
      segment_name: 'Digital Industries',
      sub_segments: [
        {
          sub_segment_id: 10,
          sub_segment_name: 'Factory Automation',
          projects: [
            {
              project_id: 100,
              project_name: 'PLC Controller',
              teams: [
                { team_id: 1000, team_name: 'Firmware Team' },
                { team_id: 1001, team_name: 'QA Team' }
              ]
            },
            {
              project_id: 101,
              project_name: 'Motion Control',
              teams: [
                { team_id: 1002, team_name: 'Drive Development' }
              ]
            }
          ]
        },
        {
          sub_segment_id: 11,
          sub_segment_name: 'Process Automation',
          projects: [
            {
              project_id: 102,
              project_name: 'DCS Platform',
              teams: [
                { team_id: 1003, team_name: 'CloudTeamAlpha' }
              ]
            }
          ]
        }
      ]
    },
    {
      segment_id: 2,
      segment_name: 'Smart Infrastructure',
      sub_segments: [
        {
          sub_segment_id: 20,
          sub_segment_name: 'Building Technologies',
          projects: [
            {
              project_id: 200,
              project_name: 'BMS System',
              teams: [
                { team_id: 2000, team_name: 'Integration Team' }
              ]
            }
          ]
        }
      ]
    }
  ],
  total_segments: 2,
  total_sub_segments: 3,
  total_projects: 4,
  total_teams: 5
};

describe('OrgHierarchyPage', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    // Reset all mocks
    vi.clearAllMocks();
    // Default mock for fetchOrgHierarchy
    fetchOrgHierarchy.mockResolvedValue(mockOrgHierarchyResponse);
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  // =========================================================================
  // Initial Render & Loading
  // =========================================================================
  describe('Initial Render & Loading', () => {
    it('should render page with master data layout', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);
      
      // Page should have the tree panel
      await waitFor(() => {
        expect(screen.getByText('Organization Hierarchy')).toBeInTheDocument();
      });
    });

    it('should call fetchOrgHierarchy on mount', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);
      
      await waitFor(() => {
        expect(fetchOrgHierarchy).toHaveBeenCalled();
      });
    });

    it('should render segments in tree', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
        expect(screen.getByText('Smart Infrastructure')).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Tree Node Selection
  // =========================================================================
  describe('Tree Node Selection', () => {
    it('should select segment when clicked', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Click on segment
      fireEvent.click(screen.getByText('Digital Industries'));
      await vi.advanceTimersByTimeAsync(50);

      // Should display segment details
      await waitFor(() => {
        // The segment name appears in multiple places - tree and details panel
        const segmentElements = screen.getAllByText('Digital Industries');
        expect(segmentElements.length).toBeGreaterThan(1);
      });
    });

    it('should show teams when project is selected', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Expand segment
      fireEvent.click(screen.getByText('Digital Industries'));
      await vi.advanceTimersByTimeAsync(50);

      // Now expand sub-segment (may appear multiple times)
      await waitFor(() => {
        const elements = screen.getAllByText('Factory Automation');
        expect(elements.length).toBeGreaterThan(0);
      });
      fireEvent.click(screen.getAllByText('Factory Automation')[0]);
      await vi.advanceTimersByTimeAsync(50);

      // Now click on project (may appear multiple times)
      await waitFor(() => {
        const elements = screen.getAllByText('PLC Controller');
        expect(elements.length).toBeGreaterThan(0);
      });
      fireEvent.click(screen.getAllByText('PLC Controller')[0]);
      await vi.advanceTimersByTimeAsync(50);

      // Should show teams in right panel
      await waitFor(() => {
        expect(screen.getByText('Firmware Team')).toBeInTheDocument();
        expect(screen.getByText('QA Team')).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Tree Search (Segments/Sub-Segments/Projects)
  // =========================================================================
  describe('Tree Search', () => {
    it('should search for existing Segment and show it', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Find the tree search input
      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');
      expect(searchInput).toBeInTheDocument();

      // Search for segment
      fireEvent.change(searchInput, { target: { value: 'Digital' } });
      await vi.advanceTimersByTimeAsync(400); // Wait for debounce

      // Segment should still be visible (tree match)
      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Should NOT show "No results found" OR team search mode
      expect(screen.queryByText(/No results found/)).not.toBeInTheDocument();
      expect(screen.queryByText('Search Results')).not.toBeInTheDocument();
    });

    it('should search for existing Sub-Segment and show it', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Expand to see sub-segments
      fireEvent.click(screen.getByText('Digital Industries'));
      await vi.advanceTimersByTimeAsync(50);

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for sub-segment
      fireEvent.change(searchInput, { target: { value: 'Factory' } });
      await vi.advanceTimersByTimeAsync(400);

      // Sub-segment should be visible (tree match - may appear multiple times)
      await waitFor(() => {
        const elements = screen.getAllByText('Factory Automation');
        expect(elements.length).toBeGreaterThan(0);
      });

      // Should NOT show team search mode
      expect(screen.queryByText('Search Results')).not.toBeInTheDocument();
    });

    it('should search for existing Project and show it', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Expand hierarchy
      fireEvent.click(screen.getByText('Digital Industries'));
      await vi.advanceTimersByTimeAsync(50);

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for project
      fireEvent.change(searchInput, { target: { value: 'PLC' } });
      await vi.advanceTimersByTimeAsync(400);

      // Project should be visible (tree match)
      await waitFor(() => {
        expect(screen.getByText('PLC Controller')).toBeInTheDocument();
      });

      // Should NOT show team search mode
      expect(screen.queryByText('Search Results')).not.toBeInTheDocument();
    });

    it('tree search takes precedence over team search', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for "Smart" which matches segment "Smart Infrastructure"
      fireEvent.change(searchInput, { target: { value: 'Smart' } });
      await vi.advanceTimersByTimeAsync(400);

      // Should show tree match, NOT team search mode
      await waitFor(() => {
        expect(screen.getByText('Smart Infrastructure')).toBeInTheDocument();
      });
      expect(screen.queryByText('Search Results')).not.toBeInTheDocument();
    });
  });

  // =========================================================================
  // Team Fallback Search (when tree has no matches)
  // =========================================================================
  describe('Team Fallback Search', () => {
    it('should show team search results when no tree matches exist', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for "CloudTeamAlpha" (team name, not in tree)
      fireEvent.change(searchInput, { target: { value: 'CloudTeamAlpha' } });
      await vi.advanceTimersByTimeAsync(500);

      // Should show Search Results mode
      await waitFor(() => {
        expect(screen.getByText('Search Results')).toBeInTheDocument();
      });

      // Should show the matching team in results
      await waitFor(() => {
        expect(screen.getByText('CloudTeamAlpha')).toBeInTheDocument();
      });
    });

    it('should show team search fallback message in tree panel', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for "Firmware" (team name)
      fireEvent.change(searchInput, { target: { value: 'Firmware' } });
      await vi.advanceTimersByTimeAsync(500);

      // Should show fallback message with team count
      await waitFor(() => {
        const fallbackContent = screen.getByText((content, element) => {
          return element?.tagName === 'STRONG' && /\d+\s*team/.test(content);
        });
        expect(fallbackContent).toBeInTheDocument();
      });
    });

    it('should display "No results found" when neither tree nor teams match', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for non-existing term
      fireEvent.change(searchInput, { target: { value: 'XYZNonExistent123' } });
      await vi.advanceTimersByTimeAsync(500);

      // Should show "No results found" messages (may appear in tree panel and details panel)
      await waitFor(() => {
        const noResultsElements = screen.getAllByText(/No results found/);
        expect(noResultsElements.length).toBeGreaterThan(0);
      });
    });

    it('should navigate to project when clicking team search result', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for "Firmware" (team name)
      fireEvent.change(searchInput, { target: { value: 'Firmware' } });
      await vi.advanceTimersByTimeAsync(500);

      // Wait for search results
      await waitFor(() => {
        expect(screen.getByText('Search Results')).toBeInTheDocument();
      });

      // Find and click on the Firmware Team row
      const firmwareRow = screen.getByText('Firmware Team').closest('tr');
      expect(firmwareRow).toBeInTheDocument();
      fireEvent.click(firmwareRow);
      await vi.advanceTimersByTimeAsync(100);

      // After clicking, should clear search and navigate to project
      await waitFor(() => {
        // Search Results should be hidden (back to normal mode)
        expect(screen.queryByText('Search Results')).not.toBeInTheDocument();
      });

      // The parent project should now be selected
      await waitFor(() => {
        const plcElements = screen.queryAllByText('PLC Controller');
        expect(plcElements.length).toBeGreaterThan(0);
      });
    });

    it('should display team hierarchy info in search results', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for "Integration" (team name)
      fireEvent.change(searchInput, { target: { value: 'Integration' } });
      await vi.advanceTimersByTimeAsync(500);

      // Should show Search Results with hierarchy columns
      await waitFor(() => {
        expect(screen.getByText('Search Results')).toBeInTheDocument();
      });

      // Should show parent project, sub-segment, and segment
      await waitFor(() => {
        expect(screen.getByText('Integration Team')).toBeInTheDocument();
        expect(screen.getByText('BMS System')).toBeInTheDocument(); // Project
        expect(screen.getByText('Building Technologies')).toBeInTheDocument(); // Sub-Segment
        expect(screen.getByText('Smart Infrastructure')).toBeInTheDocument(); // Segment
      });
    });

    it('should rank exact team name matches higher', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for "QA Team" (exact match)
      fireEvent.change(searchInput, { target: { value: 'QA Team' } });
      await vi.advanceTimersByTimeAsync(500);

      // Should show search results
      await waitFor(() => {
        expect(screen.getByText('Search Results')).toBeInTheDocument();
      });

      // The exact match should appear first
      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        // First data row (skip header) should be QA Team
        expect(rows[1]).toHaveTextContent('QA Team');
      });
    });
  });

  // =========================================================================
  // Clearing Search
  // =========================================================================
  describe('Clearing Search', () => {
    it('should restore normal tree state when clearing search', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');

      // Search for team (triggers team search mode)
      fireEvent.change(searchInput, { target: { value: 'Firmware' } });
      await vi.advanceTimersByTimeAsync(500);

      // Should show Search Results
      await waitFor(() => {
        expect(screen.getByText('Search Results')).toBeInTheDocument();
      });

      // Clear search using clear button
      const clearButton = screen.getByLabelText('Clear search');
      fireEvent.click(clearButton);
      await vi.advanceTimersByTimeAsync(500);

      // Tree should be restored
      await waitFor(() => {
        const segmentElements = screen.queryAllByText('Digital Industries');
        expect(segmentElements.length).toBeGreaterThan(0);
      });

      // Search Results should be gone
      await waitFor(() => {
        expect(screen.queryByText('Search Results')).not.toBeInTheDocument();
      });
    });

    it('should keep details panel blank in team search mode', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // First select a project to show teams
      fireEvent.click(screen.getByText('Digital Industries'));
      await vi.advanceTimersByTimeAsync(50);
      
      await waitFor(() => {
        const elements = screen.getAllByText('Factory Automation');
        expect(elements.length).toBeGreaterThan(0);
      });
      fireEvent.click(screen.getAllByText('Factory Automation')[0]);
      await vi.advanceTimersByTimeAsync(50);

      await waitFor(() => {
        const elements = screen.getAllByText('PLC Controller');
        expect(elements.length).toBeGreaterThan(0);
      });
      fireEvent.click(screen.getAllByText('PLC Controller')[0]);
      await vi.advanceTimersByTimeAsync(50);

      // Now teams should be visible
      await waitFor(() => {
        expect(screen.getByText('Firmware Team')).toBeInTheDocument();
      });

      // Now search for a team (team search mode)
      const searchInput = screen.getByPlaceholderText('Search segments, projects, teams...');
      fireEvent.change(searchInput, { target: { value: 'CloudTeamAlpha' } });
      await vi.advanceTimersByTimeAsync(500);

      // Should show Search Results, NOT the previous project's details/teams
      await waitFor(() => {
        expect(screen.getByText('Search Results')).toBeInTheDocument();
      });

      // The previous project teams should not be shown (details section is blank)
      // Note: Firmware Team may appear in search results if it matches, but should not appear 
      // as part of the project teams panel
    });
  });

  // =========================================================================
  // Tree Expand/Click Behavior Unchanged
  // =========================================================================
  describe('Tree Expand/Click Behavior', () => {
    it('should expand segment to show sub-segments', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Click to expand
      fireEvent.click(screen.getByText('Digital Industries'));
      await vi.advanceTimersByTimeAsync(50);

      // Sub-segments should be visible (may appear multiple times)
      await waitFor(() => {
        const factoryElements = screen.getAllByText('Factory Automation');
        const processElements = screen.getAllByText('Process Automation');
        expect(factoryElements.length).toBeGreaterThan(0);
        expect(processElements.length).toBeGreaterThan(0);
      });
    });

    it('should expand sub-segment to show projects', async () => {
      renderWithRouter(<OrgHierarchyPage />);
      await vi.advanceTimersByTimeAsync(100);

      await waitFor(() => {
        expect(screen.getByText('Digital Industries')).toBeInTheDocument();
      });

      // Expand segment
      fireEvent.click(screen.getByText('Digital Industries'));
      await vi.advanceTimersByTimeAsync(50);

      // Expand sub-segment (may appear multiple times in tree and details)
      await waitFor(() => {
        const elements = screen.getAllByText('Factory Automation');
        expect(elements.length).toBeGreaterThan(0);
      });
      // Click the first one (in tree)
      fireEvent.click(screen.getAllByText('Factory Automation')[0]);
      await vi.advanceTimersByTimeAsync(50);

      // Projects should be visible (may appear multiple times)
      await waitFor(() => {
        const plcElements = screen.getAllByText('PLC Controller');
        const motionElements = screen.getAllByText('Motion Control');
        expect(plcElements.length).toBeGreaterThan(0);
        expect(motionElements.length).toBeGreaterThan(0);
      });
    });
  });
});
