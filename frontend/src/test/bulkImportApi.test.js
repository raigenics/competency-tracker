/**
 * Unit tests for bulkImportApi service
 * 
 * Tests API calls for the Bulk Import feature.
 * Covers success and error scenarios for all endpoints.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { bulkImportApi } from '@/services/api/bulkImportApi.js';
import httpClient from '@/services/api/httpClient.js';

// Mock the httpClient
vi.mock('@/services/api/httpClient.js', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

describe('bulkImportApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // importExcel
  // =========================================================================
  describe('importExcel', () => {
    it('should upload Excel file and return job response', async () => {
      // Arrange
      const mockFile = new File(['test content'], 'employees.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const mockResponse = {
        job_id: 'test-job-123',
        status: 'pending',
        message: 'Import job created. Poll /import/status/test-job-123 for progress.'
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await bulkImportApi.importExcel(mockFile);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith('/import/excel', expect.any(FormData));
    });

    it('should create FormData with file', async () => {
      // Arrange
      const mockFile = new File(['excel data'], 'data.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      httpClient.post.mockResolvedValueOnce({ job_id: 'job-1' });

      // Act
      await bulkImportApi.importExcel(mockFile);

      // Assert
      const formDataArg = httpClient.post.mock.calls[0][1];
      expect(formDataArg instanceof FormData).toBe(true);
      expect(formDataArg.get('file')).toBeInstanceOf(File);
    });

    it('should log upload start with filename', async () => {
      // Arrange
      const mockFile = new File(['content'], 'employees_2024.xlsx');
      httpClient.post.mockResolvedValueOnce({ job_id: 'job-1' });

      // Act
      await bulkImportApi.importExcel(mockFile);

      // Assert
      expect(console.log).toHaveBeenCalledWith(
        'Uploading Excel file for import:',
        'employees_2024.xlsx'
      );
    });

    it('should log import completion', async () => {
      // Arrange
      const mockFile = new File(['content'], 'test.xlsx');
      const mockResponse = { job_id: 'job-123', status: 'pending' };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      await bulkImportApi.importExcel(mockFile);

      // Assert
      expect(console.log).toHaveBeenCalledWith('Import completed:', mockResponse);
    });

    it('should throw error on API failure', async () => {
      // Arrange
      const mockFile = new File(['content'], 'test.xlsx');
      const error = new Error('Network error');
      httpClient.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(bulkImportApi.importExcel(mockFile)).rejects.toThrow('Network error');
    });

    it('should log error on failure', async () => {
      // Arrange
      const mockFile = new File(['content'], 'test.xlsx');
      httpClient.post.mockRejectedValueOnce(new Error('Upload failed'));

      // Act
      try {
        await bulkImportApi.importExcel(mockFile);
      } catch {
        // Expected
      }

      // Assert
      expect(console.error).toHaveBeenCalledWith(
        'Failed to import Excel file:',
        expect.any(Error)
      );
    });

    it('should call correct endpoint', async () => {
      // Arrange
      const mockFile = new File(['content'], 'test.xlsx');
      httpClient.post.mockResolvedValueOnce({ job_id: 'job-1' });

      // Act
      await bulkImportApi.importExcel(mockFile);

      // Assert
      expect(httpClient.post).toHaveBeenCalledWith(
        '/import/excel',
        expect.any(FormData)
      );
    });

    it('should handle large file upload', async () => {
      // Arrange - 10MB mock file
      const largeContent = new Array(10 * 1024 * 1024).fill('a').join('');
      const mockFile = new File([largeContent], 'large_import.xlsx');
      httpClient.post.mockResolvedValueOnce({ job_id: 'large-job' });

      // Act
      const result = await bulkImportApi.importExcel(mockFile);

      // Assert
      expect(result.job_id).toBe('large-job');
    });
  });

  // =========================================================================
  // getJobStatus
  // =========================================================================
  describe('getJobStatus', () => {
    it('should return job status for valid job_id', async () => {
      // Arrange
      const mockStatus = {
        job_id: 'test-123',
        status: 'processing',
        percent_complete: 50,
        message: 'Processing skills...',
        employees_processed: 100,
        skills_processed: 250
      };
      httpClient.get.mockResolvedValueOnce(mockStatus);

      // Act
      const result = await bulkImportApi.getJobStatus('test-123');

      // Assert
      expect(result).toEqual(mockStatus);
      expect(httpClient.get).toHaveBeenCalledWith('/import/status/test-123');
    });

    it('should return pending status for new job', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({
        job_id: 'new-job',
        status: 'pending',
        percent_complete: 0,
        message: 'Initializing...'
      });

      // Act
      const result = await bulkImportApi.getJobStatus('new-job');

      // Assert
      expect(result.status).toBe('pending');
      expect(result.percent_complete).toBe(0);
    });

    it('should return completed status with result', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({
        job_id: 'done-job',
        status: 'completed',
        percent_complete: 100,
        message: 'Import completed successfully',
        result: {
          employees_imported: 50,
          skills_imported: 200,
          failed_rows: []
        }
      });

      // Act
      const result = await bulkImportApi.getJobStatus('done-job');

      // Assert
      expect(result.status).toBe('completed');
      expect(result.percent_complete).toBe(100);
      expect(result.result.employees_imported).toBe(50);
    });

    it('should return failed status with error', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({
        job_id: 'failed-job',
        status: 'failed',
        percent_complete: 30,
        error: 'Invalid data in row 15'
      });

      // Act
      const result = await bulkImportApi.getJobStatus('failed-job');

      // Assert
      expect(result.status).toBe('failed');
      expect(result.error).toBe('Invalid data in row 15');
    });

    it('should throw error on API failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Not found'));

      // Act & Assert
      await expect(bulkImportApi.getJobStatus('unknown')).rejects.toThrow('Not found');
    });

    it('should log error on failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Status check failed'));

      // Act
      try {
        await bulkImportApi.getJobStatus('test-job');
      } catch {
        // Expected
      }

      // Assert
      expect(console.error).toHaveBeenCalledWith(
        'Failed to get job status:',
        expect.any(Error)
      );
    });

    it('should handle UUID format job_id', async () => {
      // Arrange
      const uuidJobId = '550e8400-e29b-41d4-a716-446655440000';
      httpClient.get.mockResolvedValueOnce({
        job_id: uuidJobId,
        status: 'processing'
      });

      // Act
      await bulkImportApi.getJobStatus(uuidJobId);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith(`/import/status/${uuidJobId}`);
    });

    it('should return processing status with counts', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({
        job_id: 'job-1',
        status: 'processing',
        percent_complete: 75,
        employees_processed: 200,
        skills_processed: 800
      });

      // Act
      const result = await bulkImportApi.getJobStatus('job-1');

      // Assert
      expect(result.employees_processed).toBe(200);
      expect(result.skills_processed).toBe(800);
    });
  });

  // =========================================================================
  // validateExcel
  // =========================================================================
  describe('validateExcel', () => {
    it('should return null (validation not implemented)', async () => {
      // Arrange
      const mockFile = new File(['content'], 'test.xlsx');

      // Act
      const result = await bulkImportApi.validateExcel(mockFile);

      // Assert
      expect(result).toBeNull();
    });

    it('should log that validation is skipped', async () => {
      // Arrange
      const mockFile = new File(['content'], 'data.xlsx');

      // Act
      await bulkImportApi.validateExcel(mockFile);

      // Assert
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Validation endpoint not available'),
        'data.xlsx'
      );
    });

    it('should not call httpClient', async () => {
      // Arrange
      const mockFile = new File(['content'], 'test.xlsx');

      // Act
      await bulkImportApi.validateExcel(mockFile);

      // Assert
      expect(httpClient.post).not.toHaveBeenCalled();
      expect(httpClient.get).not.toHaveBeenCalled();
    });
  });

  // =========================================================================
  // Integration Scenarios
  // =========================================================================
  describe('Integration Scenarios', () => {
    it('should support full import workflow', async () => {
      // Arrange
      const mockFile = new File(['excel data'], 'employees.xlsx');
      
      // Step 1: Start import
      httpClient.post.mockResolvedValueOnce({
        job_id: 'workflow-job-123',
        status: 'pending'
      });
      
      // Step 2: Poll status (processing)
      httpClient.get.mockResolvedValueOnce({
        job_id: 'workflow-job-123',
        status: 'processing',
        percent_complete: 50
      });
      
      // Step 3: Poll status (completed)
      httpClient.get.mockResolvedValueOnce({
        job_id: 'workflow-job-123',
        status: 'completed',
        percent_complete: 100,
        result: { employees_imported: 100 }
      });

      // Act
      const startResult = await bulkImportApi.importExcel(mockFile);
      const midStatus = await bulkImportApi.getJobStatus(startResult.job_id);
      const finalStatus = await bulkImportApi.getJobStatus(startResult.job_id);

      // Assert
      expect(startResult.status).toBe('pending');
      expect(midStatus.status).toBe('processing');
      expect(finalStatus.status).toBe('completed');
      expect(finalStatus.result.employees_imported).toBe(100);
    });

    it('should handle import failure workflow', async () => {
      // Arrange
      const mockFile = new File(['bad data'], 'invalid.xlsx');
      
      // Start import
      httpClient.post.mockResolvedValueOnce({
        job_id: 'fail-job-456',
        status: 'pending'
      });
      
      // Poll returns failure
      httpClient.get.mockResolvedValueOnce({
        job_id: 'fail-job-456',
        status: 'failed',
        error: 'Missing required column: employee_id'
      });

      // Act
      const startResult = await bulkImportApi.importExcel(mockFile);
      const failStatus = await bulkImportApi.getJobStatus(startResult.job_id);

      // Assert
      expect(startResult.status).toBe('pending');
      expect(failStatus.status).toBe('failed');
      expect(failStatus.error).toContain('Missing required column');
    });
  });

  // =========================================================================
  // Edge Cases
  // =========================================================================
  describe('Edge Cases', () => {
    it('should handle empty file', async () => {
      // Arrange
      const emptyFile = new File([], 'empty.xlsx');
      httpClient.post.mockResolvedValueOnce({ job_id: 'empty-job' });

      // Act
      const result = await bulkImportApi.importExcel(emptyFile);

      // Assert
      expect(result.job_id).toBe('empty-job');
    });

    it('should handle special characters in filename', async () => {
      // Arrange
      const mockFile = new File(['data'], 'données_employés_2024.xlsx');
      httpClient.post.mockResolvedValueOnce({ job_id: 'special-job' });

      // Act
      await bulkImportApi.importExcel(mockFile);

      // Assert
      expect(console.log).toHaveBeenCalledWith(
        'Uploading Excel file for import:',
        'données_employés_2024.xlsx'
      );
    });

    it('should handle network timeout', async () => {
      // Arrange
      const mockFile = new File(['data'], 'test.xlsx');
      const timeoutError = new Error('Network timeout');
      timeoutError.code = 'TIMEOUT';
      httpClient.post.mockRejectedValueOnce(timeoutError);

      // Act & Assert
      await expect(bulkImportApi.importExcel(mockFile)).rejects.toThrow('Network timeout');
    });
  });

  // =========================================================================
  // getUnresolvedSkills
  // =========================================================================
  describe('getUnresolvedSkills', () => {
    it('should fetch unresolved skills with default options', async () => {
      // Arrange
      const mockResponse = {
        import_run_id: 'job-123',
        total_count: 2,
        unresolved_skills: [
          { raw_skill_id: 1, raw_text: 'Python Dev', suggestions: [] },
          { raw_skill_id: 2, raw_text: 'JS', suggestions: [] }
        ]
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await bulkImportApi.getUnresolvedSkills('job-123');

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith(
        '/import/job-123/unresolved-skills?include_suggestions=true&max_suggestions=5'
      );
      expect(result.total_count).toBe(2);
      expect(result.unresolved_skills).toHaveLength(2);
    });

    it('should pass custom options to API', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ import_run_id: 'job-456', total_count: 0, unresolved_skills: [] });

      // Act
      await bulkImportApi.getUnresolvedSkills('job-456', { includeSuggestions: false, maxSuggestions: 3 });

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith(
        '/import/job-456/unresolved-skills?include_suggestions=false&max_suggestions=3'
      );
    });

    it('should throw on API error', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Job not found'));

      // Act & Assert
      await expect(bulkImportApi.getUnresolvedSkills('bad-job')).rejects.toThrow('Job not found');
    });
  });

  // =========================================================================
  // resolveSkill
  // =========================================================================
  describe('resolveSkill', () => {
    it('should resolve skill and create alias', async () => {
      // Arrange
      const mockResponse = {
        raw_skill_id: 1,
        resolved_skill_id: 100,
        alias_created: true,
        alias_text: 'python dev',
        message: "Skill 'Python Dev' mapped to 'Python'"
      };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await bulkImportApi.resolveSkill('job-123', 1, 100);

      // Assert
      expect(httpClient.post).toHaveBeenCalledWith(
        '/import/job-123/unresolved-skills/resolve',
        { raw_skill_id: 1, target_skill_id: 100 }
      );
      expect(result.alias_created).toBe(true);
      expect(result.resolved_skill_id).toBe(100);
    });

    it('should handle conflict error (alias exists for different skill)', async () => {
      // Arrange
      const conflictError = new Error('Conflict');
      conflictError.response = {
        status: 409,
        data: {
          detail: {
            message: "Alias 'python dev' already exists for skill 'Python Development'",
            existing_skill_id: 200,
            existing_skill_name: 'Python Development'
          }
        }
      };
      httpClient.post.mockRejectedValueOnce(conflictError);

      // Act & Assert
      await expect(bulkImportApi.resolveSkill('job-123', 1, 100)).rejects.toThrow('Conflict');
    });

    it('should handle already resolved error', async () => {
      // Arrange
      const alreadyResolvedError = new Error('Already resolved');
      alreadyResolvedError.response = {
        status: 400,
        data: { detail: 'Raw skill input 1 is already resolved' }
      };
      httpClient.post.mockRejectedValueOnce(alreadyResolvedError);

      // Act & Assert
      await expect(bulkImportApi.resolveSkill('job-123', 1, 100)).rejects.toThrow('Already resolved');
    });
  });
});
