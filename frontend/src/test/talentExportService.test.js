/**
 * Unit tests for talentExportService
 * 
 * Tests export utilities and download functionality.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import talentExportService, {
  downloadExcelFile,
  generateTimestamp,
  exportAllTalent,
  exportSelectedTalent
} from '@/services/talentExportService.js';
import capabilityFinderApi from '@/services/api/capabilityFinderApi.js';

// Mock capabilityFinderApi
vi.mock('@/services/api/capabilityFinderApi.js', () => ({
  default: {
    exportMatchingTalent: vi.fn()
  }
}));

describe('talentExportService', () => {
  let mockCreateObjectURL;
  let mockRevokeObjectURL;
  let mockAppendChild;
  let mockClick;
  let mockLink;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock URL methods
    mockCreateObjectURL = vi.fn().mockReturnValue('blob:test-url');
    mockRevokeObjectURL = vi.fn();
    globalThis.URL.createObjectURL = mockCreateObjectURL;
    globalThis.URL.revokeObjectURL = mockRevokeObjectURL;

    // Mock document methods and link element
    mockClick = vi.fn();
    mockLink = {
      href: '',
      setAttribute: vi.fn(),
      click: mockClick,
      remove: vi.fn()
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink);
    mockAppendChild = vi.spyOn(document.body, 'appendChild').mockImplementation(() => {});
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // downloadExcelFile
  // =========================================================================
  describe('downloadExcelFile', () => {
    it('should create object URL from blob', () => {
      // Arrange
      const blob = new Blob(['test'], { type: 'application/xlsx' });

      // Act
      downloadExcelFile(blob, 'test.xlsx');

      // Assert
      expect(mockCreateObjectURL).toHaveBeenCalledWith(blob);
    });

    it('should create download link with correct attributes', () => {
      // Arrange
      const blob = new Blob(['test']);

      // Act
      downloadExcelFile(blob, 'export.xlsx');

      // Assert
      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(mockLink.href).toBe('blob:test-url');
      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'export.xlsx');
    });

    it('should append link to body and click it', () => {
      // Arrange
      const blob = new Blob(['test']);

      // Act
      downloadExcelFile(blob, 'test.xlsx');

      // Assert
      expect(mockAppendChild).toHaveBeenCalledWith(mockLink);
      expect(mockClick).toHaveBeenCalled();
    });

    it('should clean up after download', () => {
      // Arrange
      const blob = new Blob(['test']);

      // Act
      downloadExcelFile(blob, 'test.xlsx');

      // Assert
      expect(mockLink.remove).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:test-url');
    });
  });

  // =========================================================================
  // generateTimestamp
  // =========================================================================
  describe('generateTimestamp', () => {
    it('should return formatted timestamp string', () => {
      // Arrange
      const mockDate = new Date('2024-06-15T10:30:45.123Z');
      vi.setSystemTime(mockDate);

      // Act
      const result = generateTimestamp();

      // Assert
      expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$/);

      vi.useRealTimers();
    });

    it('should not contain colons or periods', () => {
      // Act
      const result = generateTimestamp();

      // Assert
      expect(result).not.toContain(':');
      expect(result).not.toContain('.');
    });

    it('should be consistent format each time', () => {
      // Act
      const result1 = generateTimestamp();
      const result2 = generateTimestamp();

      // Assert - both should match same format
      const formatRegex = /^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$/;
      expect(result1).toMatch(formatRegex);
      expect(result2).toMatch(formatRegex);
    });
  });

  // =========================================================================
  // exportAllTalent
  // =========================================================================
  describe('exportAllTalent', () => {
    it('should call API with mode "all"', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      const filters = { skills: ['Python'], subSegment: 'all' };

      // Act
      await exportAllTalent(filters);

      // Assert
      expect(capabilityFinderApi.exportMatchingTalent).toHaveBeenCalledWith(
        expect.objectContaining({ mode: 'all' })
      );
    });

    it('should transform filters correctly', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      const filters = {
        skills: ['Python', 'AWS'],
        subSegment: '5',
        team: '10',
        role: 'Developer',
        proficiency: { min: 3 },
        experience: { min: 2 }
      };

      // Act
      await exportAllTalent(filters);

      // Assert
      expect(capabilityFinderApi.exportMatchingTalent).toHaveBeenCalledWith({
        mode: 'all',
        filters: {
          skills: ['Python', 'AWS'],
          sub_segment_id: 5,
          team_id: 10,
          role: 'Developer',
          min_proficiency: 3,
          min_experience_years: 2
        },
        selected_employee_ids: []
      });
    });

    it('should handle "all" subSegment as null', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      const filters = { skills: [], subSegment: 'all' };

      // Act
      await exportAllTalent(filters);

      // Assert
      const payload = capabilityFinderApi.exportMatchingTalent.mock.calls[0][0];
      expect(payload.filters.sub_segment_id).toBeNull();
    });

    it('should use default filename when not provided', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      // Act
      await exportAllTalent({ skills: [] });

      // Assert - should not throw, filename defaults to 'capability_finder_all'
      expect(mockLink.setAttribute).toHaveBeenCalledWith(
        'download',
        expect.stringContaining('capability_finder_all')
      );
    });

    it('should allow custom filename', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      // Act
      await exportAllTalent({ skills: [] }, 'custom_export');

      // Assert
      expect(mockLink.setAttribute).toHaveBeenCalledWith(
        'download',
        expect.stringContaining('custom_export')
      );
    });

    it('should propagate API errors', async () => {
      // Arrange
      capabilityFinderApi.exportMatchingTalent.mockRejectedValueOnce(new Error('Export failed'));

      // Act & Assert
      await expect(exportAllTalent({ skills: [] })).rejects.toThrow('Export failed');
    });

    it('should handle missing filter properties gracefully', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      const filters = {}; // No properties

      // Act
      await exportAllTalent(filters);

      // Assert - should use defaults
      const payload = capabilityFinderApi.exportMatchingTalent.mock.calls[0][0];
      expect(payload.filters.skills).toEqual([]);
      expect(payload.filters.min_proficiency).toBe(0);
      expect(payload.filters.min_experience_years).toBe(0);
    });
  });

  // =========================================================================
  // exportSelectedTalent
  // =========================================================================
  describe('exportSelectedTalent', () => {
    it('should call API with mode "selected"', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      // Act
      await exportSelectedTalent({ skills: [] }, [1, 2, 3]);

      // Assert
      expect(capabilityFinderApi.exportMatchingTalent).toHaveBeenCalledWith(
        expect.objectContaining({ mode: 'selected' })
      );
    });

    it('should include selected_employee_ids', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      const selectedIds = [10, 20, 30];

      // Act
      await exportSelectedTalent({ skills: [] }, selectedIds);

      // Assert
      expect(capabilityFinderApi.exportMatchingTalent).toHaveBeenCalledWith(
        expect.objectContaining({ selected_employee_ids: selectedIds })
      );
    });

    it('should transform filters correctly', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      const filters = {
        skills: ['Java'],
        subSegment: '3',
        team: '7',
        role: 'QA',
        proficiency: { min: 2 },
        experience: { min: 1 }
      };

      // Act
      await exportSelectedTalent(filters, [1, 2]);

      // Assert
      const payload = capabilityFinderApi.exportMatchingTalent.mock.calls[0][0];
      expect(payload.filters).toEqual({
        skills: ['Java'],
        sub_segment_id: 3,
        team_id: 7,
        role: 'QA',
        min_proficiency: 2,
        min_experience_years: 1
      });
    });

    it('should use default filename when not provided', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      // Act
      await exportSelectedTalent({ skills: [] }, [1]);

      // Assert
      expect(mockLink.setAttribute).toHaveBeenCalledWith(
        'download',
        expect.stringContaining('capability_finder_selected')
      );
    });

    it('should allow custom filename', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      // Act
      await exportSelectedTalent({ skills: [] }, [1], 'my_selection');

      // Assert
      expect(mockLink.setAttribute).toHaveBeenCalledWith(
        'download',
        expect.stringContaining('my_selection')
      );
    });

    it('should propagate API errors', async () => {
      // Arrange
      capabilityFinderApi.exportMatchingTalent.mockRejectedValueOnce(new Error('Export error'));

      // Act & Assert
      await expect(exportSelectedTalent({ skills: [] }, [1])).rejects.toThrow('Export error');
    });

    it('should handle empty selected IDs array', async () => {
      // Arrange
      const mockBlob = new Blob(['test']);
      capabilityFinderApi.exportMatchingTalent.mockResolvedValueOnce(mockBlob);

      // Act
      await exportSelectedTalent({ skills: [] }, []);

      // Assert
      const payload = capabilityFinderApi.exportMatchingTalent.mock.calls[0][0];
      expect(payload.selected_employee_ids).toEqual([]);
    });
  });

  // =========================================================================
  // Default export
  // =========================================================================
  describe('default export', () => {
    it('should export all methods', () => {
      expect(talentExportService.downloadExcelFile).toBeDefined();
      expect(talentExportService.generateTimestamp).toBeDefined();
      expect(talentExportService.exportAllTalent).toBeDefined();
      expect(talentExportService.exportSelectedTalent).toBeDefined();
    });
  });
});
