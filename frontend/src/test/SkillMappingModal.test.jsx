/**
 * Unit tests for SkillMappingModal component
 * 
 * Tests the Skill Mapping modal including:
 * - API call to fetch suggestions when modal opens
 * - Displaying suggestions from API response
 * - Error handling
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SkillMappingModal from '@/pages/BulkImport/SkillMappingModal.jsx';

// Mock bulkImportApi
vi.mock('@/services/api/bulkImportApi.js', () => ({
  bulkImportApi: {
    getUnresolvedSkills: vi.fn(),
    getSingleSkillSuggestions: vi.fn(),
    resolveSkill: vi.fn()
  }
}));

// Get mocked module
import { bulkImportApi } from '@/services/api/bulkImportApi.js';

describe('SkillMappingModal', () => {
  const mockUnresolvedSkill = {
    raw_skill_id: 42, // Valid ID - enables single-skill endpoint
    raw_text: 'Python Programming',
    normalized_text: 'python programming',
    employee_name: 'John Doe',
    employee_zid: 'Z12345',
    suggestions: [] // Empty - should trigger fetch
  };

  const mockImportRunId = 'test-job-uuid-123';

  // Response format from getSingleSkillSuggestions API (single skill object)
  const mockApiResponse = {
    raw_skill_id: 42,
    raw_text: 'Python Programming',
    normalized_text: 'python programming',
    suggestions: [
      {
        skill_id: 101,
        skill_name: 'Python',
        category: 'Programming',
        subcategory: 'Languages',
        match_type: 'embedding',
        confidence: 0.92
      },
      {
        skill_id: 102,
        skill_name: 'Python 3',
        category: 'Programming',
        subcategory: 'Languages',
        match_type: 'embedding',
        confidence: 0.85
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
    it('should call getSingleSkillSuggestions API when modal opens with empty suggestions', async () => {
      // Arrange
      bulkImportApi.getSingleSkillSuggestions.mockResolvedValueOnce(mockApiResponse);

      // Act
      render(
        <SkillMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert - API should be called with correct args
      await waitFor(() => {
        expect(bulkImportApi.getSingleSkillSuggestions).toHaveBeenCalledTimes(1);
        expect(bulkImportApi.getSingleSkillSuggestions).toHaveBeenCalledWith(
          mockImportRunId,
          42, // raw_skill_id
          { maxSuggestions: 10, includeEmbeddings: true }
        );
      });
    });

    it('should display suggestions from API response', async () => {
      // Arrange
      bulkImportApi.getSingleSkillSuggestions.mockResolvedValueOnce(mockApiResponse);

      // Act
      render(
        <SkillMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert - suggestions should be displayed
      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
        expect(screen.getByText('Python 3')).toBeInTheDocument();
      });
    });

    it('should NOT call API when modal is closed', () => {
      // Arrange
      bulkImportApi.getSingleSkillSuggestions.mockResolvedValueOnce(mockApiResponse);

      // Act
      render(
        <SkillMappingModal
          isOpen={false}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert - API should NOT be called when modal is closed
      expect(bulkImportApi.getSingleSkillSuggestions).not.toHaveBeenCalled();
    });

    it('should NOT call API when suggestions are already provided', async () => {
      // Arrange
      const skillWithSuggestions = {
        ...mockUnresolvedSkill,
        suggestions: [
          {
            skill_id: 101,
            skill_name: 'Python',
            category: 'Programming',
            subcategory: 'Languages',
            match_type: 'embedding',
            confidence: 0.92
          }
        ]
      };

      // Act
      render(
        <SkillMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={skillWithSuggestions}
          onResolved={vi.fn()}
        />
      );

      // Wait a tick to ensure no API call happens
      await new Promise(r => setTimeout(r, 100));

      // Assert - API should NOT be called when suggestions exist
      expect(bulkImportApi.getSingleSkillSuggestions).not.toHaveBeenCalled();
      // But existing suggestions should be displayed
      expect(screen.getByText('Python')).toBeInTheDocument();
    });

    it('should display error message when API call fails', async () => {
      // Arrange
      bulkImportApi.getSingleSkillSuggestions.mockRejectedValueOnce(new Error('Network error'));

      // Act
      render(
        <SkillMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert - error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/Failed to load skill suggestions/)).toBeInTheDocument();
      });
    });

    it('should show loading state while fetching', async () => {
      // Arrange - Use a promise that doesn't resolve immediately
      let resolveApi;
      const apiPromise = new Promise(resolve => { resolveApi = resolve; });
      bulkImportApi.getSingleSkillSuggestions.mockReturnValueOnce(apiPromise);

      // Act
      render(
        <SkillMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert - loading state should be shown
      expect(screen.getByText(/Loading suggestions/)).toBeInTheDocument();

      // Resolve the API call
      resolveApi(mockApiResponse);

      // Wait for suggestions to appear
      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Modal Rendering
  // =========================================================================
  describe('Modal Rendering', () => {
    it('should display unresolved skill text', async () => {
      // Arrange
      bulkImportApi.getUnresolvedSkills.mockResolvedValueOnce(mockApiResponse);

      // Act
      render(
        <SkillMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert
      expect(screen.getByText('Python Programming')).toBeInTheDocument();
    });

    it('should display employee info', async () => {
      // Arrange
      bulkImportApi.getUnresolvedSkills.mockResolvedValueOnce(mockApiResponse);

      // Act
      render(
        <SkillMappingModal
          isOpen={true}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText(/Z12345/)).toBeInTheDocument();
    });

    it('should return null when modal is closed', () => {
      // Act
      const { container } = render(
        <SkillMappingModal
          isOpen={false}
          onClose={vi.fn()}
          importRunId={mockImportRunId}
          unresolvedSkill={mockUnresolvedSkill}
          onResolved={vi.fn()}
        />
      );

      // Assert - should render nothing
      expect(container.firstChild).toBeNull();
    });
  });
});
