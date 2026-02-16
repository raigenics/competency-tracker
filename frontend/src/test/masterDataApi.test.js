/**
 * Unit tests for masterDataApi service
 * 
 * Tests API calls for the Master Data / Skill Taxonomy feature.
 * Covers success and error scenarios for all endpoints.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import masterDataApi, {
  fetchSkillTaxonomy,
  updateCategoryName,
  updateSubcategoryName,
  updateSkillName,
  updateAliasText,
  createAlias,
  createCategory,
  createSubcategory,
  createSkill,
  deleteAlias,
  deleteCategory,
  deleteSubcategory,
  deleteSkill,
  importSkills,
  getImportJobStatus,
} from '@/services/api/masterDataApi.js';
import httpClient from '@/services/api/httpClient.js';

// Mock the httpClient
vi.mock('@/services/api/httpClient.js', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  }
}));

describe('masterDataApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // fetchSkillTaxonomy
  // =========================================================================
  describe('fetchSkillTaxonomy', () => {
    it('should fetch taxonomy without search param', async () => {
      // Arrange
      const mockResponse = {
        categories: [
          { id: 1, name: 'Programming', subcategories: [] }
        ],
        total_categories: 1,
        total_subcategories: 0,
        total_skills: 0
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await fetchSkillTaxonomy();

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.get).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy',
        {},
        { signal: undefined }
      );
    });

    it('should fetch taxonomy with search param', async () => {
      // Arrange
      const mockResponse = {
        categories: [
          { id: 1, name: 'Programming', subcategories: [
            { id: 10, name: 'Languages', skills: [
              { id: 100, name: 'Python', employee_count: 5 }
            ]}
          ]}
        ],
        total_categories: 1,
        total_subcategories: 1,
        total_skills: 1
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await fetchSkillTaxonomy({ search: 'python' });

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.get).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy',
        { q: 'python' },
        { signal: undefined }
      );
    });

    it('should pass abort signal when provided', async () => {
      // Arrange
      const controller = new AbortController();
      const mockResponse = { categories: [], total_categories: 0 };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      await fetchSkillTaxonomy({ signal: controller.signal });

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy',
        {},
        { signal: controller.signal }
      );
    });

    it('should pass both search and signal when provided', async () => {
      // Arrange
      const controller = new AbortController();
      const mockResponse = { categories: [], total_categories: 0 };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      await fetchSkillTaxonomy({ search: 'java', signal: controller.signal });

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy',
        { q: 'java' },
        { signal: controller.signal }
      );
    });

    it('should propagate API errors', async () => {
      // Arrange
      const error = new Error('Network error');
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(fetchSkillTaxonomy()).rejects.toThrow('Network error');
    });
  });

  // =========================================================================
  // updateCategoryName
  // =========================================================================
  describe('updateCategoryName', () => {
    it('should update category name successfully', async () => {
      // Arrange
      const mockResponse = {
        category_id: 1,
        category_name: 'Updated Category',
        message: 'Category updated successfully'
      };
      httpClient.patch.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await updateCategoryName(1, 'Updated Category');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.patch).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/categories/1',
        { category_name: 'Updated Category' }
      );
    });

    it('should propagate 404 error for non-existent category', async () => {
      // Arrange
      const error = new Error('Category not found');
      error.status = 404;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateCategoryName(999, 'Name')).rejects.toThrow('Category not found');
    });

    it('should propagate 409 conflict error for duplicate name', async () => {
      // Arrange
      const error = new Error('Category name already exists');
      error.status = 409;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateCategoryName(1, 'Existing')).rejects.toThrow('Category name already exists');
    });
  });

  // =========================================================================
  // updateSubcategoryName
  // =========================================================================
  describe('updateSubcategoryName', () => {
    it('should update subcategory name successfully', async () => {
      // Arrange
      const mockResponse = {
        subcategory_id: 10,
        subcategory_name: 'Updated Subcategory',
        category_id: 1,
        message: 'Subcategory updated successfully'
      };
      httpClient.patch.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await updateSubcategoryName(10, 'Updated Subcategory');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.patch).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/subcategories/10',
        { subcategory_name: 'Updated Subcategory' }
      );
    });

    it('should propagate 404 error for non-existent subcategory', async () => {
      // Arrange
      const error = new Error('Subcategory not found');
      error.status = 404;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateSubcategoryName(999, 'Name')).rejects.toThrow('Subcategory not found');
    });

    it('should propagate 409 conflict error for duplicate name', async () => {
      // Arrange
      const error = new Error('Subcategory name already exists');
      error.status = 409;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateSubcategoryName(1, 'Existing')).rejects.toThrow('Subcategory name already exists');
    });
  });

  // =========================================================================
  // updateSkillName
  // =========================================================================
  describe('updateSkillName', () => {
    it('should update skill name successfully', async () => {
      // Arrange
      const mockResponse = {
        skill_id: 100,
        skill_name: 'Updated Skill',
        subcategory_id: 10,
        message: 'Skill updated successfully'
      };
      httpClient.patch.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await updateSkillName(100, 'Updated Skill');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.patch).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/skills/100',
        { skill_name: 'Updated Skill' }
      );
    });

    it('should propagate 404 error for non-existent skill', async () => {
      // Arrange
      const error = new Error('Skill not found');
      error.status = 404;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateSkillName(999, 'Name')).rejects.toThrow('Skill not found');
    });

    it('should propagate 409 conflict error for duplicate name', async () => {
      // Arrange
      const error = new Error('Skill name already exists');
      error.status = 409;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateSkillName(1, 'Existing')).rejects.toThrow('Skill name already exists');
    });
  });

  // =========================================================================
  // updateAliasText
  // =========================================================================
  describe('updateAliasText', () => {
    it('should update alias text successfully', async () => {
      // Arrange
      const mockResponse = {
        alias_id: 500,
        alias_text: 'Updated Alias',
        skill_id: 100,
        message: 'Alias updated successfully'
      };
      httpClient.patch.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await updateAliasText(500, 'Updated Alias');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.patch).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/aliases/500',
        { alias_text: 'Updated Alias' }
      );
    });

    it('should propagate 404 error for non-existent alias', async () => {
      // Arrange
      const error = new Error('Alias not found');
      error.status = 404;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateAliasText(999, 'Text')).rejects.toThrow('Alias not found');
    });

    it('should propagate 409 conflict error for duplicate alias', async () => {
      // Arrange
      const error = new Error('Alias already exists');
      error.status = 409;
      httpClient.patch.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(updateAliasText(1, 'Existing')).rejects.toThrow('Alias already exists');
    });
  });

  // =========================================================================
  // createAlias
  // =========================================================================
  describe('createAlias', () => {
    it('should create alias with default source and confidence', async () => {
      // Arrange
      const mockResponse = {
        id: 600,
        alias_text: 'New Alias',
        skill_id: 100,
        source: 'manual',
        confidence_score: 1.0,
        message: 'Alias created successfully'
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await createAlias(100, 'New Alias');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/skills/100/aliases',
        { alias_text: 'New Alias', source: 'manual', confidence_score: 1.0 }
      );
    });

    it('should create alias with custom source and confidence', async () => {
      // Arrange
      const mockResponse = {
        id: 601,
        alias_text: 'Imported Alias',
        skill_id: 100,
        source: 'excel_import',
        confidence_score: 0.9
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await createAlias(100, 'Imported Alias', 'excel_import', 0.9);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/skills/100/aliases',
        { alias_text: 'Imported Alias', source: 'excel_import', confidence_score: 0.9 }
      );
    });

    it('should propagate 404 error for non-existent skill', async () => {
      // Arrange
      const error = new Error('Skill not found');
      error.status = 404;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createAlias(999, 'Alias')).rejects.toThrow('Skill not found');
    });

    it('should propagate 409 conflict error for duplicate alias', async () => {
      // Arrange
      const error = new Error('Alias already exists for this skill');
      error.status = 409;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createAlias(100, 'Existing')).rejects.toThrow('Alias already exists');
    });
  });

  // =========================================================================
  // createCategory
  // =========================================================================
  describe('createCategory', () => {
    it('should create category successfully', async () => {
      // Arrange
      const mockResponse = {
        id: 5,
        name: 'New Category',
        created_at: '2024-01-15T10:00:00Z',
        created_by: 'admin',
        message: 'Category created successfully'
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await createCategory('New Category');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/categories',
        { category_name: 'New Category' }
      );
    });

    it('should propagate 409 conflict error for duplicate category name', async () => {
      // Arrange
      const error = new Error('Category with this name already exists');
      error.status = 409;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createCategory('Existing')).rejects.toThrow('Category with this name already exists');
    });

    it('should propagate validation error', async () => {
      // Arrange
      const error = new Error('Category name is required');
      error.status = 422;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createCategory('')).rejects.toThrow('Category name is required');
    });
  });

  // =========================================================================
  // createSubcategory
  // =========================================================================
  describe('createSubcategory', () => {
    it('should create subcategory successfully', async () => {
      // Arrange
      const mockResponse = {
        id: 15,
        name: 'New Subcategory',
        category_id: 1,
        created_at: '2024-01-15T10:00:00Z',
        created_by: 'admin',
        message: 'Subcategory created successfully'
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await createSubcategory(1, 'New Subcategory');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/categories/1/subcategories',
        { subcategory_name: 'New Subcategory' }
      );
    });

    it('should propagate 404 error for non-existent category', async () => {
      // Arrange
      const error = new Error('Category not found');
      error.status = 404;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createSubcategory(999, 'Name')).rejects.toThrow('Category not found');
    });

    it('should propagate 409 conflict error for duplicate subcategory name', async () => {
      // Arrange
      const error = new Error('Subcategory with this name already exists in category');
      error.status = 409;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createSubcategory(1, 'Existing')).rejects.toThrow('Subcategory with this name already exists');
    });
  });

  // =========================================================================
  // createSkill
  // =========================================================================
  describe('createSkill', () => {
    it('should create skill without aliases', async () => {
      // Arrange
      const mockResponse = {
        id: 200,
        name: 'New Skill',
        subcategory_id: 10,
        created_at: '2024-01-15T10:00:00Z',
        created_by: 'admin',
        aliases: [],
        message: 'Skill created successfully'
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await createSkill(10, 'New Skill');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/subcategories/10/skills',
        { skill_name: 'New Skill' }
      );
    });

    it('should create skill with aliases', async () => {
      // Arrange
      const mockResponse = {
        id: 201,
        name: 'Python Programming',
        subcategory_id: 10,
        aliases: [
          { id: 700, alias_text: 'python', skill_id: 201 },
          { id: 701, alias_text: 'py', skill_id: 201 }
        ],
        message: 'Skill created successfully'
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await createSkill(10, 'Python Programming', 'python, py');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/subcategories/10/skills',
        { skill_name: 'Python Programming', alias_text: 'python, py' }
      );
    });

    it('should not include alias_text when aliasText is null', async () => {
      // Arrange
      const mockResponse = { id: 202, name: 'Skill', aliases: [] };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      await createSkill(10, 'Skill', null);

      // Assert
      const callBody = httpClient.post.mock.calls[0][1];
      expect(callBody).not.toHaveProperty('alias_text');
    });

    it('should propagate 404 error for non-existent subcategory', async () => {
      // Arrange
      const error = new Error('Subcategory not found');
      error.status = 404;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createSkill(999, 'Skill')).rejects.toThrow('Subcategory not found');
    });

    it('should propagate 409 conflict error for duplicate skill name', async () => {
      // Arrange
      const error = new Error('Skill with this name already exists');
      error.status = 409;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(createSkill(10, 'Existing')).rejects.toThrow('Skill with this name already exists');
    });
  });

  // =========================================================================
  // deleteAlias
  // =========================================================================
  describe('deleteAlias', () => {
    it('should delete alias successfully', async () => {
      // Arrange
      const mockResponse = {
        id: 500,
        alias_text: 'Deleted Alias',
        skill_id: 100,
        message: 'Alias deleted successfully'
      };
      httpClient.delete.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await deleteAlias(500);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.delete).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/aliases/500'
      );
    });

    it('should propagate 404 error for non-existent alias', async () => {
      // Arrange
      const error = new Error('Alias not found');
      error.status = 404;
      httpClient.delete.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(deleteAlias(999)).rejects.toThrow('Alias not found');
    });
  });

  // =========================================================================
  // deleteCategory
  // =========================================================================
  describe('deleteCategory', () => {
    it('should delete category successfully', async () => {
      // Arrange
      const mockResponse = {
        category_id: 1,
        category_name: 'Deleted Category',
        deleted_at: '2024-01-15T12:00:00Z',
        message: 'Category soft deleted successfully'
      };
      httpClient.delete.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await deleteCategory(1);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.delete).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/categories/1'
      );
    });

    it('should propagate 404 error for non-existent category', async () => {
      // Arrange
      const error = new Error('Category not found');
      error.status = 404;
      httpClient.delete.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(deleteCategory(999)).rejects.toThrow('Category not found');
    });

    it('should propagate 409 conflict error when category has subcategories', async () => {
      // Arrange
      const error = new Error('Cannot delete category with subcategories');
      error.status = 409;
      httpClient.delete.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(deleteCategory(1)).rejects.toThrow('Cannot delete category with subcategories');
    });
  });

  // =========================================================================
  // deleteSubcategory
  // =========================================================================
  describe('deleteSubcategory', () => {
    it('should delete subcategory successfully', async () => {
      // Arrange
      const mockResponse = {
        subcategory_id: 10,
        subcategory_name: 'Deleted Subcategory',
        category_id: 1,
        deleted_at: '2024-01-15T12:00:00Z',
        message: 'Subcategory soft deleted successfully'
      };
      httpClient.delete.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await deleteSubcategory(10);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.delete).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/subcategories/10'
      );
    });

    it('should propagate 404 error for non-existent subcategory', async () => {
      // Arrange
      const error = new Error('Subcategory not found');
      error.status = 404;
      httpClient.delete.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(deleteSubcategory(999)).rejects.toThrow('Subcategory not found');
    });

    it('should propagate 409 conflict error when subcategory has skills', async () => {
      // Arrange
      const error = new Error('Cannot delete subcategory with skills');
      error.status = 409;
      httpClient.delete.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(deleteSubcategory(10)).rejects.toThrow('Cannot delete subcategory with skills');
    });
  });

  // =========================================================================
  // deleteSkill
  // =========================================================================
  describe('deleteSkill', () => {
    it('should delete skill successfully', async () => {
      // Arrange
      const mockResponse = {
        id: 100,
        name: 'Deleted Skill',
        subcategory_id: 10,
        deleted_at: '2024-01-15T12:00:00Z',
        message: 'Skill soft deleted successfully'
      };
      httpClient.delete.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await deleteSkill(100);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.delete).toHaveBeenCalledWith(
        '/master-data/skill-taxonomy/skills/100'
      );
    });

    it('should propagate 404 error for non-existent skill', async () => {
      // Arrange
      const error = new Error('Skill not found');
      error.status = 404;
      httpClient.delete.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(deleteSkill(999)).rejects.toThrow('Skill not found');
    });

    it('should propagate 409 conflict error when skill has dependencies', async () => {
      // Arrange
      const error = new Error('Cannot delete skill with assigned employees');
      error.status = 409;
      httpClient.delete.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(deleteSkill(100)).rejects.toThrow('Cannot delete skill with assigned employees');
    });
  });

  // =========================================================================
  // importSkills
  // =========================================================================
  describe('importSkills', () => {
    it('should upload Excel file and return job response', async () => {
      // Arrange
      const mockFile = new File(['test content'], 'skills.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const mockResponse = {
        job_id: 'import-job-123',
        status: 'pending',
        message: 'Import job created successfully'
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await importSkills(mockFile);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith(
        '/admin/skills/master-import',
        expect.any(FormData)
      );
    });

    it('should create FormData with file', async () => {
      // Arrange
      const mockFile = new File(['excel data'], 'skills_master.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      httpClient.post.mockResolvedValueOnce({ job_id: 'job-1' });

      // Act
      await importSkills(mockFile);

      // Assert
      const formDataArg = httpClient.post.mock.calls[0][1];
      expect(formDataArg instanceof FormData).toBe(true);
      expect(formDataArg.get('file')).toBeInstanceOf(File);
    });

    it('should propagate error on invalid file', async () => {
      // Arrange
      const mockFile = new File(['text'], 'invalid.txt', { type: 'text/plain' });
      const error = new Error('Invalid file type');
      error.status = 400;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(importSkills(mockFile)).rejects.toThrow('Invalid file type');
    });

    it('should propagate server error', async () => {
      // Arrange
      const mockFile = new File(['content'], 'test.xlsx');
      const error = new Error('Internal server error');
      error.status = 500;
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(importSkills(mockFile)).rejects.toThrow('Internal server error');
    });
  });

  // =========================================================================
  // getImportJobStatus
  // =========================================================================
  describe('getImportJobStatus', () => {
    it('should get job status for pending job', async () => {
      // Arrange
      const mockResponse = {
        job_id: 'import-job-123',
        status: 'pending',
        percent_complete: 0,
        message: 'Job is queued'
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await getImportJobStatus('import-job-123');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.get).toHaveBeenCalledWith('/import/status/import-job-123');
    });

    it('should get job status for in-progress job', async () => {
      // Arrange
      const mockResponse = {
        job_id: 'import-job-123',
        status: 'processing',
        percent_complete: 50,
        message: 'Processing rows 50/100'
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await getImportJobStatus('import-job-123');

      // Assert
      expect(result).toEqual(mockResponse);
    });

    it('should get job status for completed job', async () => {
      // Arrange
      const mockResponse = {
        job_id: 'import-job-123',
        status: 'completed',
        percent_complete: 100,
        message: 'Import completed successfully',
        result: {
          imported_skills: 25,
          imported_categories: 5,
          imported_subcategories: 10
        }
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await getImportJobStatus('import-job-123');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(result.result).toBeDefined();
    });

    it('should get job status for failed job', async () => {
      // Arrange
      const mockResponse = {
        job_id: 'import-job-123',
        status: 'failed',
        percent_complete: 25,
        message: 'Import failed',
        error: 'Invalid data format in row 26'
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await getImportJobStatus('import-job-123');

      // Assert
      expect(result).toEqual(mockResponse);
      expect(result.error).toBeDefined();
    });

    it('should propagate 404 error for non-existent job', async () => {
      // Arrange
      const error = new Error('Job not found');
      error.status = 404;
      httpClient.get.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(getImportJobStatus('invalid-job')).rejects.toThrow('Job not found');
    });
  });

  // =========================================================================
  // Default export
  // =========================================================================
  describe('default export', () => {
    it('should export all API functions', () => {
      expect(masterDataApi.fetchSkillTaxonomy).toBe(fetchSkillTaxonomy);
      expect(masterDataApi.updateCategoryName).toBe(updateCategoryName);
      expect(masterDataApi.updateSubcategoryName).toBe(updateSubcategoryName);
      expect(masterDataApi.updateSkillName).toBe(updateSkillName);
      expect(masterDataApi.updateAliasText).toBe(updateAliasText);
      expect(masterDataApi.createAlias).toBe(createAlias);
      expect(masterDataApi.createCategory).toBe(createCategory);
      expect(masterDataApi.createSubcategory).toBe(createSubcategory);
      expect(masterDataApi.createSkill).toBe(createSkill);
      expect(masterDataApi.deleteAlias).toBe(deleteAlias);
      expect(masterDataApi.deleteCategory).toBe(deleteCategory);
      expect(masterDataApi.deleteSubcategory).toBe(deleteSubcategory);
      expect(masterDataApi.deleteSkill).toBe(deleteSkill);
      expect(masterDataApi.importSkills).toBe(importSkills);
      expect(masterDataApi.getImportJobStatus).toBe(getImportJobStatus);
    });
  });
});
