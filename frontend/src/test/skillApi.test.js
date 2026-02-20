/**
 * Unit tests for skillApi.js - Organizational Skill Map API service
 * 
 * Tests all API methods used by the Organizational Skill Map (Taxonomy) feature:
 * - getSkillSummary
 * - getTaxonomyTree
 * - getCategories
 * - getSubcategories
 * - getSkills
 * - searchSkillsInTaxonomy
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { skillApi } from '@/services/api/skillApi.js';
import httpClient from '@/services/api/httpClient.js';

// Mock the httpClient
vi.mock('@/services/api/httpClient.js', () => ({
  default: {
    get: vi.fn()
  }
}));

describe('skillApi - Organizational Skill Map', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // getSkillSummary
  // =========================================================================
  describe('getSkillSummary', () => {
    it('should fetch skill summary for given skill ID', async () => {
      // Arrange
      const mockResponse = {
        skill_id: 1,
        skill_name: 'Python',
        employee_count: 10,
        employee_ids: [1, 2, 3],
        avg_experience_years: 3.5
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getSkillSummary(1);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/1/summary');
      expect(result).toEqual(mockResponse);
    });

    it('should handle error when fetching skill summary fails', async () => {
      // Arrange
      const error = new Error('Network error');
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(skillApi.getSkillSummary(1)).rejects.toThrow('Network error');
    });

    it('should pass correct skill ID in URL', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({});

      // Act
      await skillApi.getSkillSummary(42);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/42/summary');
    });
  });

  // =========================================================================
  // getTaxonomyTree
  // =========================================================================
  describe('getTaxonomyTree', () => {
    it('should fetch complete taxonomy tree', async () => {
      // Arrange
      const mockResponse = {
        categories: [
          {
            category_id: 1,
            category_name: 'Programming',
            subcategories: [
              {
                subcategory_id: 1,
                subcategory_name: 'Backend',
                skills: [{ skill_id: 1, skill_name: 'Python' }]
              }
            ]
          }
        ]
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getTaxonomyTree();

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/taxonomy/tree');
      expect(result).toEqual(mockResponse);
    });

    it('should handle error when fetching taxonomy tree fails', async () => {
      // Arrange
      const error = new Error('Server error');
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(skillApi.getTaxonomyTree()).rejects.toThrow('Server error');
    });

    it('should return empty categories array when no data', async () => {
      // Arrange
      const mockResponse = { categories: [] };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getTaxonomyTree();

      // Assert
      expect(result.categories).toEqual([]);
    });
  });

  // =========================================================================
  // getCategories (lazy-loading)
  // =========================================================================
  describe('getCategories', () => {
    it('should fetch categories with counts', async () => {
      // Arrange
      const mockResponse = {
        categories: [
          { category_id: 1, category_name: 'Programming', subcategory_count: 5, skill_count: 20 },
          { category_id: 2, category_name: 'Design', subcategory_count: 3, skill_count: 15 }
        ]
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getCategories();

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/capability/categories');
      expect(result).toEqual(mockResponse);
    });

    it('should handle error when fetching categories fails', async () => {
      // Arrange
      const error = new Error('Failed to fetch categories');
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(skillApi.getCategories()).rejects.toThrow('Failed to fetch categories');
    });

    it('should return empty categories when none exist', async () => {
      // Arrange
      const mockResponse = { categories: [] };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getCategories();

      // Assert
      expect(result.categories).toEqual([]);
    });
  });

  // =========================================================================
  // getSubcategories
  // =========================================================================
  describe('getSubcategories', () => {
    it('should fetch subcategories for a category', async () => {
      // Arrange
      const mockResponse = {
        category_id: 1,
        category_name: 'Programming',
        subcategories: [
          { subcategory_id: 1, subcategory_name: 'Backend', skill_count: 10 },
          { subcategory_id: 2, subcategory_name: 'Frontend', skill_count: 8 }
        ]
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getSubcategories(1);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/capability/categories/1/subcategories');
      expect(result).toEqual(mockResponse);
    });

    it('should handle error when fetching subcategories fails', async () => {
      // Arrange
      const error = new Error('Category not found');
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(skillApi.getSubcategories(999)).rejects.toThrow('Category not found');
    });

    it('should pass correct category ID in URL', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ subcategories: [] });

      // Act
      await skillApi.getSubcategories(42);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/capability/categories/42/subcategories');
    });
  });

  // =========================================================================
  // getSkills (for subcategory)
  // =========================================================================
  describe('getSkills', () => {
    it('should fetch skills for a subcategory', async () => {
      // Arrange
      const mockResponse = {
        subcategory_id: 1,
        subcategory_name: 'Backend',
        skills: [
          { skill_id: 1, skill_name: 'Python' },
          { skill_id: 2, skill_name: 'Django' }
        ]
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getSkills(1);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/capability/subcategories/1/skills');
      expect(result).toEqual(mockResponse);
    });

    it('should handle error when fetching skills fails', async () => {
      // Arrange
      const error = new Error('Subcategory not found');
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(skillApi.getSkills(999)).rejects.toThrow('Subcategory not found');
    });

    it('should return empty skills array when subcategory has no skills', async () => {
      // Arrange
      const mockResponse = { subcategory_id: 1, skills: [] };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.getSkills(1);

      // Assert
      expect(result.skills).toEqual([]);
    });
  });

  // =========================================================================
  // searchSkillsInTaxonomy
  // =========================================================================
  describe('searchSkillsInTaxonomy', () => {
    it('should search skills with query parameter', async () => {
      // Arrange
      const mockResponse = {
        results: [
          {
            skill_id: 1,
            skill_name: 'Python',
            category_id: 1,
            category_name: 'Programming',
            subcategory_id: 1,
            subcategory_name: 'Backend'
          }
        ],
        count: 1
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.searchSkillsInTaxonomy('python');

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/capability/search', { q: 'python' });
      expect(result).toEqual(mockResponse);
    });

    it('should handle error when search fails', async () => {
      // Arrange
      const error = new Error('Search failed');
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(skillApi.searchSkillsInTaxonomy('test')).rejects.toThrow('Search failed');
    });

    it('should return empty results when no matches', async () => {
      // Arrange
      const mockResponse = { results: [], count: 0 };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await skillApi.searchSkillsInTaxonomy('nonexistent');

      // Assert
      expect(result.results).toEqual([]);
      expect(result.count).toBe(0);
    });

    it('should pass query correctly for partial matches', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ results: [], count: 0 });

      // Act
      await skillApi.searchSkillsInTaxonomy('react');

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/capability/search', { q: 'react' });
    });

    it('should handle special characters in query', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ results: [], count: 0 });

      // Act
      await skillApi.searchSkillsInTaxonomy('C++');

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/skills/capability/search', { q: 'C++' });
    });
  });

  // =========================================================================
  // API Error Handling
  // =========================================================================
  describe('API error handling', () => {
    it('should propagate network errors', async () => {
      // Arrange
      const networkError = new Error('Network error');
      httpClient.get.mockRejectedValueOnce(networkError);

      // Act & Assert
      await expect(skillApi.getTaxonomyTree()).rejects.toThrow('Network error');
    });

    it('should propagate 401 errors', async () => {
      // Arrange
      const authError = new Error('Unauthorized');
      httpClient.get.mockRejectedValueOnce(authError);

      // Act & Assert
      await expect(skillApi.getCategories()).rejects.toThrow('Unauthorized');
    });

    it('should propagate 500 errors', async () => {
      // Arrange
      const serverError = new Error('Internal server error');
      httpClient.get.mockRejectedValueOnce(serverError);

      // Act & Assert
      await expect(skillApi.getSkillSummary(1)).rejects.toThrow('Internal server error');
    });
  });
});
