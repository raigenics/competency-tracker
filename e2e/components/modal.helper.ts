// Module: modal.helper.ts
// Purpose: Handles confirmation modals and dependency-block modals
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Modal Helper
 * 
 * Provides reusable methods for interacting with modal dialogs:
 * - Confirmation modals (delete confirmations)
 * - Dependency warning modals (can't delete due to relationships)
 * - Alert modals (error/success messages)
 */
export class ModalHelper {
  readonly page: Page;
  readonly modal: Locator;
  readonly title: Locator;
  readonly message: Locator;
  readonly confirmButton: Locator;
  readonly cancelButton: Locator;
  readonly closeButton: Locator;

  /**
   * Create a new ModalHelper instance
   * @param page - Playwright Page object
   * @param modalTestId - data-testid of the modal container (default: 'modal')
   */
  constructor(page: Page, modalTestId: string = 'modal') {
    this.page = page;
    this.modal = page.getByTestId(modalTestId);
    this.title = this.modal.getByTestId('modal-title');
    this.message = this.modal.getByTestId('modal-message');
    this.confirmButton = this.modal.getByTestId('modal-confirm-btn');
    this.cancelButton = this.modal.getByTestId('modal-cancel-btn');
    this.closeButton = this.modal.getByTestId('modal-close-btn');
  }

  /**
   * Click the confirm button (Yes, Delete, OK, etc.)
   */
  async confirm(): Promise<void> {
    await this.confirmButton.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  /**
   * Click the cancel button (No, Cancel, etc.)
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  /**
   * Click the close (X) button
   */
  async close(): Promise<void> {
    await this.closeButton.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  /**
   * Wait for a dependency warning modal to appear
   * Used when trying to delete an entity with child relationships
   */
  async waitForDependencyModal(): Promise<void> {
    await this.page.getByTestId('dependency-modal').waitFor({ state: 'visible' });
  }

  /**
   * Get the dependency warning message
   * @returns The message explaining why deletion is blocked
   */
  async getDependencyMessage(): Promise<string> {
    const dependencyModal = this.page.getByTestId('dependency-modal');
    const message = dependencyModal.getByTestId('dependency-message');
    return await message.textContent() || '';
  }

  /**
   * Get the modal title text
   */
  async getTitle(): Promise<string> {
    return await this.title.textContent() || '';
  }

  /**
   * Get the modal message text
   */
  async getMessage(): Promise<string> {
    return await this.message.textContent() || '';
  }

  /**
   * Check if modal is visible
   */
  async isVisible(): Promise<boolean> {
    return await this.modal.isVisible();
  }

  /**
   * Wait for the modal to close
   */
  async waitForClose(): Promise<void> {
    await this.modal.waitFor({ state: 'hidden' });
  }

  /**
   * Wait for the modal to open
   */
  async waitForOpen(): Promise<void> {
    await this.modal.waitFor({ state: 'visible' });
  }

  /**
   * Check if this is a dependency warning modal
   */
  async isDependencyWarning(): Promise<boolean> {
    const title = await this.getTitle();
    return title.toLowerCase().includes('cannot delete') || 
           title.toLowerCase().includes('dependency');
  }
}

export default ModalHelper;
