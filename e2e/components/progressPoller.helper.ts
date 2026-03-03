// Module: progressPoller.helper.ts
// Purpose: Polls import job progress bar until status = Completed or timeout
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Progress Poller Helper
 * 
 * Provides methods for polling and waiting on async progress operations:
 * - Import job progress tracking
 * - Batch operation progress
 * - Any long-running async task with progress indicator
 */
export class ProgressPollerHelper {
  readonly page: Page;
  readonly container: Locator;
  readonly progressBar: Locator;
  readonly progressPercent: Locator;
  readonly statusText: Locator;
  readonly defaultTimeout: number;
  readonly pollInterval: number;

  /**
   * Create a new ProgressPollerHelper instance
   * @param page - Playwright Page object
   * @param containerTestId - data-testid of the progress container
   * @param defaultTimeout - Default timeout in milliseconds (default: 60000)
   * @param pollInterval - Polling interval in milliseconds (default: 1000)
   */
  constructor(
    page: Page, 
    containerTestId: string = 'progress-container',
    defaultTimeout: number = 60000,
    pollInterval: number = 1000
  ) {
    this.page = page;
    this.container = page.getByTestId(containerTestId);
    this.progressBar = this.container.getByTestId('progress-bar');
    this.progressPercent = this.container.getByTestId('progress-percent');
    this.statusText = this.container.getByTestId('progress-status');
    this.defaultTimeout = defaultTimeout;
    this.pollInterval = pollInterval;
  }

  /**
   * Wait for the operation to complete
   * @param timeoutMs - Timeout in milliseconds (uses default if not specified)
   * @returns Final status string
   */
  async waitForCompletion(timeoutMs?: number): Promise<string> {
    const timeout = timeoutMs ?? this.defaultTimeout;
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const status = await this.getStatus();
      
      if (this.isCompletedStatus(status)) {
        return status;
      }
      
      if (this.isErrorStatus(status)) {
        throw new Error(`Operation failed with status: ${status}`);
      }

      // Wait before polling again
      await this.page.waitForTimeout(this.pollInterval);
    }

    throw new Error(`Operation timed out after ${timeout}ms`);
  }

  /**
   * Get the current status text
   */
  async getStatus(): Promise<string> {
    const text = await this.statusText.textContent();
    return text?.trim() || '';
  }

  /**
   * Get the current progress percentage
   */
  async getProgressPercent(): Promise<number> {
    const text = await this.progressPercent.textContent();
    const match = text?.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Check if the operation is still in progress
   */
  async isInProgress(): Promise<boolean> {
    const status = await this.getStatus();
    return this.isProgressingStatus(status);
  }

  /**
   * Check if the operation has completed (success or failure)
   */
  async isComplete(): Promise<boolean> {
    const status = await this.getStatus();
    return this.isCompletedStatus(status) || this.isErrorStatus(status);
  }

  /**
   * Check if the operation completed successfully
   */
  async isSuccess(): Promise<boolean> {
    const status = await this.getStatus();
    return this.isCompletedStatus(status);
  }

  /**
   * Check if the operation failed
   */
  async isFailed(): Promise<boolean> {
    const status = await this.getStatus();
    return this.isErrorStatus(status);
  }

  /**
   * Get progress updates as the operation runs
   * @param callback - Function called with each progress update
   * @param timeoutMs - Timeout in milliseconds
   */
  async trackProgress(
    callback: (percent: number, status: string) => void,
    timeoutMs?: number
  ): Promise<void> {
    const timeout = timeoutMs ?? this.defaultTimeout;
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const percent = await this.getProgressPercent();
      const status = await this.getStatus();
      
      callback(percent, status);

      if (this.isCompletedStatus(status) || this.isErrorStatus(status)) {
        return;
      }

      await this.page.waitForTimeout(this.pollInterval);
    }

    throw new Error(`Progress tracking timed out after ${timeout}ms`);
  }

  /**
   * Check if status indicates operation is in progress
   */
  private isProgressingStatus(status: string): boolean {
    const progressStatuses = ['pending', 'running', 'processing', 'in progress'];
    return progressStatuses.some(s => status.toLowerCase().includes(s));
  }

  /**
   * Check if status indicates successful completion
   */
  private isCompletedStatus(status: string): boolean {
    const completedStatuses = ['completed', 'success', 'done', 'finished'];
    return completedStatuses.some(s => status.toLowerCase().includes(s));
  }

  /**
   * Check if status indicates an error
   */
  private isErrorStatus(status: string): boolean {
    const errorStatuses = ['failed', 'error', 'aborted', 'cancelled'];
    return errorStatuses.some(s => status.toLowerCase().includes(s));
  }
}

export default ProgressPollerHelper;
