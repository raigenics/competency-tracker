/**
 * Unit tests for capabilityFinderApi service
 * 
 * Tests API calls for the Capability Finder feature.
 * Covers success and error scenarios for all endpoints.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import capabilityFinderApi from '@/services/api/capabilityFinderApi.js';
import httpClient from '@/services/api/httpClient.js';

// Mock the httpClient
vi.mock('@/services/api/httpClient.js', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

// Mock fetch for export endpoint (uses raw fetch)
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('capabilityFinderApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // getAllSkills
  // =========================================================================
  describe('getAllSkills', () => {
    it('should return array of skill names on success', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ skills: ['AWS', 'Docker', 'Python'] });

      // Act
      const result = await capabilityFinderApi.getAllSkills();

      // Assert
      expect(result).toEqual(['AWS', 'Docker', 'Python']);
      expect(httpClient.get).toHaveBeenCalledWith('/capability-finder/skills');
    });

    it('should return empty array when response has no skills', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({});

      // Act
      const result = await capabilityFinderApi.getAllSkills();

      // Assert
      expect(result).toEqual([]);
    });

    it('should throw error on API failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Network error'));

      // Act & Assert
      await expect(capabilityFinderApi.getAllSkills()).rejects.toThrow('Network error');
    });

    it('should log error on failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('API error'));

      // Act
      try {
        await capabilityFinderApi.getAllSkills();
      } catch {
        // ignore
      }

      // Assert
      expect(console.error).toHaveBeenCalledWith('Failed to fetch skills:', expect.any(Error));
    });
  });

  // =========================================================================
  // getSkillSuggestions
  // =========================================================================
  describe('getSkillSuggestions', () => {
    it('should return suggestions without query parameter', async () => {
      // Arrange
      const suggestions = [
        { skill_id: 1, skill_name: 'Python', is_employee_available: true, is_selectable: true }
      ];
      httpClient.get.mockResolvedValueOnce({ suggestions });

      // Act
      const result = await capabilityFinderApi.getSkillSuggestions();

      // Assert
      expect(result).toEqual(suggestions);
      expect(httpClient.get).toHaveBeenCalledWith('/capability-finder/skills/suggestions');
    });

    it('should pass query parameter when provided', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ suggestions: [] });

      // Act
      await capabilityFinderApi.getSkillSuggestions('python');

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/capability-finder/skills/suggestions?query=python');
    });

    it('should encode query parameter with special characters', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ suggestions: [] });

      // Act
      await capabilityFinderApi.getSkillSuggestions('C++ & C#');

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/capability-finder/skills/suggestions?query=C%2B%2B%20%26%20C%23');
    });

    it('should return empty array when no suggestions', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({});

      // Act
      const result = await capabilityFinderApi.getSkillSuggestions();

      // Assert
      expect(result).toEqual([]);
    });

    it('should throw error on API failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Network error'));

      // Act & Assert
      await expect(capabilityFinderApi.getSkillSuggestions()).rejects.toThrow();
    });
  });

  // =========================================================================
  // getAllRoles
  // =========================================================================
  describe('getAllRoles', () => {
    it('should return array of role names on success', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ roles: ['Developer', 'Manager', 'QA'] });

      // Act
      const result = await capabilityFinderApi.getAllRoles();

      // Assert
      expect(result).toEqual(['Developer', 'Manager', 'QA']);
      expect(httpClient.get).toHaveBeenCalledWith('/capability-finder/roles');
    });

    it('should return empty array when no roles', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({});

      // Act
      const result = await capabilityFinderApi.getAllRoles();

      // Assert
      expect(result).toEqual([]);
    });

    it('should throw error on API failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Server error'));

      // Act & Assert
      await expect(capabilityFinderApi.getAllRoles()).rejects.toThrow('Server error');
    });
  });

  // =========================================================================
  // searchMatchingTalent
  // =========================================================================
  describe('searchMatchingTalent', () => {
    it('should return search results on success', async () => {
      // Arrange
      const response = {
        results: [
          { employee_id: 1, employee_name: 'John Doe', role: 'Developer', team: 'TeamA', sub_segment: 'SS1', top_skills: [] }
        ],
        count: 1
      };
      httpClient.post.mockResolvedValueOnce(response);

      // Act
      const result = await capabilityFinderApi.searchMatchingTalent({ skills: ['Python'] });

      // Assert
      expect(result).toEqual(response);
      expect(httpClient.post).toHaveBeenCalledWith('/capability-finder/search', { skills: ['Python'] });
    });

    it('should pass all filter parameters', async () => {
      // Arrange
      const payload = {
        skills: ['Python', 'AWS'],
        sub_segment_id: 1,
        team_id: 5,
        role: 'Developer',
        min_proficiency: 3,
        min_experience_years: 2
      };
      httpClient.post.mockResolvedValueOnce({ results: [], count: 0 });

      // Act
      await capabilityFinderApi.searchMatchingTalent(payload);

      // Assert
      expect(httpClient.post).toHaveBeenCalledWith('/capability-finder/search', payload);
    });

    it('should return empty results when no matches', async () => {
      // Arrange
      httpClient.post.mockResolvedValueOnce({ results: [], count: 0 });

      // Act
      const result = await capabilityFinderApi.searchMatchingTalent({ skills: ['NonExistent'] });

      // Assert
      expect(result.results).toEqual([]);
      expect(result.count).toBe(0);
    });

    it('should throw error on API failure', async () => {
      // Arrange
      httpClient.post.mockRejectedValueOnce(new Error('Search failed'));

      // Act & Assert
      await expect(capabilityFinderApi.searchMatchingTalent({ skills: ['Python'] })).rejects.toThrow('Search failed');
    });

    it('should log error on failure', async () => {
      // Arrange
      httpClient.post.mockRejectedValueOnce(new Error('API error'));

      // Act
      try {
        await capabilityFinderApi.searchMatchingTalent({ skills: [] });
      } catch {
        // ignore
      }

      // Assert
      expect(console.error).toHaveBeenCalledWith('Failed to search matching talent:', expect.any(Error));
    });
  });

  // =========================================================================
  // exportMatchingTalent
  // =========================================================================
  describe('exportMatchingTalent', () => {
    it('should return blob on successful export', async () => {
      // Arrange
      const mockBlob = new Blob(['test content'], { type: 'application/xlsx' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      });

      // Act
      const result = await capabilityFinderApi.exportMatchingTalent({
        mode: 'all',
        filters: { skills: [] },
        selected_employee_ids: []
      });

      // Assert
      expect(result).toBe(mockBlob);
    });

    it('should send correct payload for "all" mode', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob()
      });

      const payload = {
        mode: 'all',
        filters: { skills: ['Python'], min_proficiency: 0, min_experience_years: 0 },
        selected_employee_ids: []
      };

      // Act
      await capabilityFinderApi.exportMatchingTalent(payload);

      // Assert
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/capability-finder/export'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(payload)
        })
      );
    });

    it('should send correct payload for "selected" mode', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob()
      });

      const payload = {
        mode: 'selected',
        filters: { skills: ['Python'] },
        selected_employee_ids: [1, 2, 3]
      };

      // Act
      await capabilityFinderApi.exportMatchingTalent(payload);

      // Assert
      const [url, options] = mockFetch.mock.calls[0];
      const body = JSON.parse(options.body);
      expect(body.mode).toBe('selected');
      expect(body.selected_employee_ids).toEqual([1, 2, 3]);
    });

    it('should throw error on non-ok response', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Export failed' })
      });

      // Act & Assert
      await expect(capabilityFinderApi.exportMatchingTalent({
        mode: 'all',
        filters: { skills: [] },
        selected_employee_ids: []
      })).rejects.toThrow('Export failed');
    });

    it('should throw error on network failure', async () => {
      // Arrange
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // Act & Assert
      await expect(capabilityFinderApi.exportMatchingTalent({
        mode: 'all',
        filters: { skills: [] },
        selected_employee_ids: []
      })).rejects.toThrow('Network error');
    });

    it('should handle response without JSON on error', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('No JSON'); }
      });

      // Act & Assert
      await expect(capabilityFinderApi.exportMatchingTalent({
        mode: 'all',
        filters: { skills: [] },
        selected_employee_ids: []
      })).rejects.toThrow('Export failed');
    });

    it('should include Content-Type header', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob()
      });

      // Act
      await capabilityFinderApi.exportMatchingTalent({
        mode: 'all',
        filters: { skills: [] },
        selected_employee_ids: []
      });

      // Assert
      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers['Content-Type']).toBe('application/json');
    });
  });
});
