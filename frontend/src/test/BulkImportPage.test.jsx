/**
 * Unit tests for BulkImportPage component
 * 
 * Tests the Bulk Import UI including:
 * - Initial render
 * - File selection and drag/drop
 * - Upload/import flow
 * - Progress display
 * - Success/error result display
 * - Reset flow
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BulkImportPage from '@/pages/BulkImport/BulkImportPage.jsx';

// Mock dependencies
vi.mock('@/services/api/bulkImportApi.js', () => ({
  bulkImportApi: {
    importExcel: vi.fn(),
    getJobStatus: vi.fn(),
    validateExcel: vi.fn()
  }
}));

vi.mock('@/components/PageHeader.jsx', () => ({
  default: ({ title, subtitle }) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  )
}));

// Get mocked module
import { bulkImportApi } from '@/services/api/bulkImportApi.js';

// Helper to render with router
const renderWithRouter = (component) => {
  return render(
    <MemoryRouter>
      {component}
    </MemoryRouter>
  );
};

// Create mock file
const createMockFile = (name = 'employees.xlsx', size = 1024) => {
  const file = new File(['test content'], name, {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

describe('BulkImportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // Initial Render
  // =========================================================================
  describe('Initial Render', () => {
    it('should render page with header', () => {
      // Act
      renderWithRouter(<BulkImportPage />);

      // Assert
      expect(screen.getByTestId('page-header')).toBeInTheDocument();
      expect(screen.getByText(/Bulk Import/)).toBeInTheDocument();
    });

    it('should render upload section', () => {
      // Act
      renderWithRouter(<BulkImportPage />);

      // Assert
      expect(screen.getByText('Upload Excel File')).toBeInTheDocument();
    });

    it('should render drag and drop zone', () => {
      // Act
      renderWithRouter(<BulkImportPage />);

      // Assert
      expect(screen.getByText(/Drag & drop your Excel file here/)).toBeInTheDocument();
    });

    it('should render download template button', () => {
      // Act
      renderWithRouter(<BulkImportPage />);

      // Assert
      expect(screen.getByText('Download Template')).toBeInTheDocument();
    });

    it('should render file format hint', () => {
      // Act
      renderWithRouter(<BulkImportPage />);

      // Assert
      expect(screen.getByText(/Accepts .xlsx files only/)).toBeInTheDocument();
    });

    it('should render step instructions', () => {
      // Act
      renderWithRouter(<BulkImportPage />);

      // Assert
      expect(screen.getByText(/Step 1: Download Excel Template/)).toBeInTheDocument();
      expect(screen.getByText(/Step 2: Upload Your File/)).toBeInTheDocument();
    });
  });

  // =========================================================================
  // File Selection
  // =========================================================================
  describe('File Selection', () => {
    it('should accept xlsx file', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('data.xlsx');
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [file] } });

      // Assert
      await waitFor(() => {
        expect(screen.getByText('data.xlsx')).toBeInTheDocument();
      });
    });

    it('should show file size after selection', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx', 2048);
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [file] } });

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/KB/)).toBeInTheDocument();
      });
    });

    it('should show Start Import button after file selection', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [file] } });

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });
    });

    it('should show Remove button after file selection', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [file] } });

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Remove')).toBeInTheDocument();
      });
    });

    it('should remove file on Remove click', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });
      
      await waitFor(() => {
        expect(screen.getByText('test.xlsx')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Remove'));

      // Assert
      await waitFor(() => {
        expect(screen.queryByText('test.xlsx')).not.toBeInTheDocument();
      });
    });

    it('should reject non-Excel files', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const csvFile = new File(['data'], 'data.csv', { type: 'text/csv' });
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [csvFile] } });

      // Assert - should not show the file
      await waitFor(() => {
        expect(screen.queryByText('data.csv')).not.toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Import Flow
  // =========================================================================
  describe('Import Flow', () => {
    it('should start import when Start Import is clicked', async () => {
      // Arrange
      bulkImportApi.importExcel.mockResolvedValueOnce({
        job_id: 'test-job-123',
        status: 'pending'
      });
      bulkImportApi.getJobStatus.mockResolvedValue({
        job_id: 'test-job-123',
        status: 'completed',
        percent_complete: 100
      });

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert
      await waitFor(() => {
        expect(bulkImportApi.importExcel).toHaveBeenCalledWith(file);
      });
    });

    it('should show progress section during import', async () => {
      // Arrange
      bulkImportApi.importExcel.mockResolvedValueOnce({
        job_id: 'test-job',
        status: 'pending'
      });
      bulkImportApi.getJobStatus.mockResolvedValue({
        job_id: 'test-job',
        status: 'processing',
        percent_complete: 50,
        message: 'Processing...'
      });

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Import in Progress')).toBeInTheDocument();
      });
    });

    it('should disable buttons during import', async () => {
      // Arrange
      bulkImportApi.importExcel.mockResolvedValueOnce({
        job_id: 'test-job',
        status: 'pending'
      });
      bulkImportApi.getJobStatus.mockResolvedValue({
        job_id: 'test-job',
        status: 'processing',
        percent_complete: 25
      });

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Importing...')).toBeDisabled();
      });
    });
  });

  // =========================================================================
  // Progress Display
  // =========================================================================
  describe('Progress Display', () => {
    it('should show progress bar during import', async () => {
      // Arrange
      bulkImportApi.importExcel.mockResolvedValueOnce({
        job_id: 'job-1',
        status: 'pending'
      });
      bulkImportApi.getJobStatus.mockResolvedValue({
        status: 'processing',
        percent_complete: 45,
        message: 'Processing skills...'
      });

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Progress')).toBeInTheDocument();
      });
    });

    it('should show warning not to close page', async () => {
      // Arrange
      bulkImportApi.importExcel.mockResolvedValueOnce({
        job_id: 'job-1',
        status: 'pending'
      });
      bulkImportApi.getJobStatus.mockResolvedValue({
        status: 'processing',
        percent_complete: 30
      });

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/Do not close this page/)).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Error Display
  // =========================================================================
  describe('Error Display', () => {
    it('should show error when import fails to start', async () => {
      // Arrange
      bulkImportApi.importExcel.mockRejectedValueOnce(new Error('Upload failed'));

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert - multiple "Import Failed" elements exist (h2 header and h4 in error box)
      await waitFor(() => {
        const importFailedElements = screen.getAllByText('Import Failed');
        expect(importFailedElements.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should show Try Again button on error', async () => {
      // Arrange
      bulkImportApi.importExcel.mockRejectedValueOnce(new Error('Network error'));

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert
      await waitFor(() => {
        expect(screen.getByText('← Try Again')).toBeInTheDocument();
      });
    });

    it('should reset state on Try Again click', async () => {
      // Arrange
      bulkImportApi.importExcel.mockRejectedValueOnce(new Error('Failed'));

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Start Import'));

      await waitFor(() => {
        expect(screen.getByText('← Try Again')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('← Try Again'));

      // Assert
      await waitFor(() => {
        expect(screen.queryByText('Import Failed')).not.toBeInTheDocument();
      });
    });

    it('should show error detail from API', async () => {
      // Arrange
      const error = new Error('Validation error');
      error.response = { data: { detail: 'Missing employee_id column' } };
      bulkImportApi.importExcel.mockRejectedValueOnce(error);

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/Missing employee_id column/)).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Download Template
  // =========================================================================
  describe('Download Template', () => {
    it('should trigger download on button click', async () => {
      // Arrange
      const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
      renderWithRouter(<BulkImportPage />);

      // Act
      fireEvent.click(screen.getByText('Download Template'));

      // Assert
      expect(alertMock).toHaveBeenCalled();
    });
  });

  // =========================================================================
  // Drag and Drop
  // =========================================================================
  describe('Drag and Drop', () => {
    it('should accept dropped xlsx file', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const dropZone = screen.getByText(/Drag & drop/).closest('div');
      const file = createMockFile('dropped.xlsx');

      // Act
      fireEvent.dragOver(dropZone);
      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file] }
      });

      // Assert
      await waitFor(() => {
        expect(screen.getByText('dropped.xlsx')).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // File Size Formatting
  // =========================================================================
  describe('File Size Formatting', () => {
    it('should format small files in bytes', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('small.xlsx', 500);
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [file] } });

      // Assert
      await waitFor(() => {
        expect(screen.getByText('500 B')).toBeInTheDocument();
      });
    });

    it('should format medium files in KB', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('medium.xlsx', 5000);
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [file] } });

      // Assert
      await waitFor(() => {
        expect(screen.getByText('4.9 KB')).toBeInTheDocument();
      });
    });

    it('should format large files in MB', async () => {
      // Arrange
      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('large.xlsx', 5 * 1024 * 1024);
      const input = document.querySelector('input[type="file"]');

      // Act
      fireEvent.change(input, { target: { files: [file] } });

      // Assert
      await waitFor(() => {
        expect(screen.getByText('5.0 MB')).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // Legacy/Sync Response
  // =========================================================================
  describe('Legacy Sync Response', () => {
    it('should handle synchronous import response (no job_id)', async () => {
      // Arrange - old sync response without job_id
      bulkImportApi.importExcel.mockResolvedValueOnce({
        employees_imported: 50,
        skills_imported: 200,
        failed_rows: []
      });

      renderWithRouter(<BulkImportPage />);
      const file = createMockFile('test.xlsx');
      const input = document.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Start Import')).toBeInTheDocument();
      });

      // Act
      fireEvent.click(screen.getByText('Start Import'));

      // Assert - should show results directly
      await waitFor(() => {
        expect(bulkImportApi.getJobStatus).not.toHaveBeenCalled();
      });
    });
  });
});
