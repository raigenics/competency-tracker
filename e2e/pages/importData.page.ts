// Module: importData.page.ts
// Purpose: Page object for Import Data (System) module
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Import Data Page Object
 * 
 * Route: /system/import
 * 
 * Key data-testid selectors:
 * - import-data-container: Main page wrapper
 * - import-data-header: Page header
 * - file-upload-zone: Drag-drop upload zone
 * - file-input: Hidden file input
 * - supported-formats: Supported formats text
 * - preview-container: Data preview container
 * - preview-table: Preview data table
 * - column-mapping: Column mapping section
 * - validation-errors: Validation errors list
 * - start-import-btn: Start import button
 * - cancel-btn: Cancel button
 * - progress-container: Import progress container
 * - progress-bar: Progress bar
 * - progress-percent: Progress percentage text
 * - progress-status: Status text
 * - results-container: Results summary container
 * - created-count: Created records count
 * - updated-count: Updated records count
 * - skipped-count: Skipped records count
 * - error-count: Error records count
 * - error-details: Error details section
 * - download-errors-btn: Download error report button
 * - unresolved-skills: Unresolved skills section
 * - loading-spinner: Loading indicator
 */
export default class ImportDataPage {
  readonly page: Page;
  readonly container: Locator;
  readonly header: Locator;
  readonly fileUploadZone: Locator;
  readonly fileInput: Locator;
  readonly supportedFormats: Locator;
  readonly previewContainer: Locator;
  readonly previewTable: Locator;
  readonly columnMapping: Locator;
  readonly validationErrors: Locator;
  readonly startImportButton: Locator;
  readonly cancelButton: Locator;
  readonly progressContainer: Locator;
  readonly progressBar: Locator;
  readonly progressPercent: Locator;
  readonly progressStatus: Locator;
  readonly resultsContainer: Locator;
  readonly createdCount: Locator;
  readonly updatedCount: Locator;
  readonly skippedCount: Locator;
  readonly errorCount: Locator;
  readonly errorDetails: Locator;
  readonly downloadErrorsButton: Locator;
  readonly unresolvedSkills: Locator;
  readonly loadingSpinner: Locator;

  constructor(page: Page) {
    this.page = page;
    this.container = page.getByTestId('import-data-container');
    this.header = page.getByTestId('import-data-header');
    this.fileUploadZone = page.getByTestId('file-upload-zone');
    this.fileInput = page.getByTestId('file-input');
    this.supportedFormats = page.getByTestId('supported-formats');
    this.previewContainer = page.getByTestId('preview-container');
    this.previewTable = page.getByTestId('preview-table');
    this.columnMapping = page.getByTestId('column-mapping');
    this.validationErrors = page.getByTestId('validation-errors');
    this.startImportButton = page.getByTestId('start-import-btn');
    this.cancelButton = page.getByTestId('cancel-btn');
    this.progressContainer = page.getByTestId('progress-container');
    this.progressBar = page.getByTestId('progress-bar');
    this.progressPercent = page.getByTestId('progress-percent');
    this.progressStatus = page.getByTestId('progress-status');
    this.resultsContainer = page.getByTestId('results-container');
    this.createdCount = page.getByTestId('created-count');
    this.updatedCount = page.getByTestId('updated-count');
    this.skippedCount = page.getByTestId('skipped-count');
    this.errorCount = page.getByTestId('error-count');
    this.errorDetails = page.getByTestId('error-details');
    this.downloadErrorsButton = page.getByTestId('download-errors-btn');
    this.unresolvedSkills = page.getByTestId('unresolved-skills');
    this.loadingSpinner = page.getByTestId('loading-spinner');
  }

  /**
   * Navigate directly to the import data page
   */
  async navigate(): Promise<void> {
    await this.page.goto('/system/import');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for page to finish loading
   */
  async waitForLoad(): Promise<void> {
    await this.loadingSpinner.waitFor({ state: 'hidden' });
    await this.container.waitFor({ state: 'visible' });
  }

  /**
   * Upload a file for import
   */
  async uploadFile(filePath: string): Promise<void> {
    await this.fileInput.setInputFiles(filePath);
    await this.previewContainer.waitFor({ state: 'visible' });
  }

  /**
   * Start the import process
   */
  async startImport(): Promise<void> {
    await this.startImportButton.click();
    await this.progressContainer.waitFor({ state: 'visible' });
  }

  /**
   * Get current progress percentage
   */
  async getProgressPercent(): Promise<string> {
    return await this.progressPercent.textContent() || '0%';
  }

  /**
   * Get current import status
   */
  async getStatus(): Promise<string> {
    return await this.progressStatus.textContent() || '';
  }

  /**
   * Wait for import to complete
   */
  async waitForCompletion(timeoutMs: number = 60000): Promise<void> {
    await this.resultsContainer.waitFor({ state: 'visible', timeout: timeoutMs });
  }

  /**
   * Get created records count
   */
  async getCreatedCount(): Promise<number> {
    const text = await this.createdCount.textContent() || '0';
    return parseInt(text, 10);
  }

  /**
   * Get error records count
   */
  async getErrorCount(): Promise<number> {
    const text = await this.errorCount.textContent() || '0';
    return parseInt(text, 10);
  }

  /**
   * Click cancel button
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
  }

  /**
   * Download error report
   */
  async downloadErrorReport(): Promise<void> {
    await this.downloadErrorsButton.click();
  }
}
