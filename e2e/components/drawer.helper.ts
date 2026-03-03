// Module: drawer.helper.ts
// Purpose: Reusable helper for slide-out drawers (Employee Management, Skill Library, etc.)
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Drawer Helper
 * 
 * Provides reusable methods for interacting with slide-out drawer components
 * used throughout the application for create/edit forms.
 * 
 * Common drawer patterns:
 * - Employee Management: Add/Edit Employee
 * - Skill Library: Add/Edit Category/Subcategory/Skill
 * - Org Structure: Add/Edit Segment/SubSegment/Project/Team
 * - Role Catalog: Add/Edit Role
 */
export class DrawerHelper {
  readonly page: Page;
  readonly drawerSelector: string;
  readonly drawer: Locator;
  readonly closeButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;
  readonly loadingSpinner: Locator;

  /**
   * Create a new DrawerHelper instance
   * @param page - Playwright Page object
   * @param drawerTestId - data-testid of the drawer container
   */
  constructor(page: Page, drawerTestId: string = 'drawer') {
    this.page = page;
    this.drawerSelector = drawerTestId;
    this.drawer = page.getByTestId(drawerTestId);
    this.closeButton = this.drawer.getByTestId('drawer-close-btn');
    this.saveButton = this.drawer.getByTestId('drawer-save-btn');
    this.cancelButton = this.drawer.getByTestId('drawer-cancel-btn');
    this.loadingSpinner = this.drawer.getByTestId('drawer-loading');
  }

  /**
   * Wait for drawer to open and be visible
   */
  async open(): Promise<void> {
    await this.drawer.waitFor({ state: 'visible' });
  }

  /**
   * Fill a form field by label
   * @param label - Field label text
   * @param value - Value to fill
   */
  async fillField(label: string, value: string): Promise<void> {
    const field = this.drawer.getByLabel(label);
    await field.fill(value);
  }

  /**
   * Select an option from a dropdown field by label
   * @param label - Field label text
   * @param optionText - Option text to select
   */
  async selectOption(label: string, optionText: string): Promise<void> {
    const dropdown = this.drawer.getByLabel(label);
    await dropdown.click();
    await this.page.getByRole('option', { name: optionText }).click();
  }

  /**
   * Toggle a checkbox field by label
   * @param label - Checkbox label text
   */
  async toggleCheckbox(label: string): Promise<void> {
    const checkbox = this.drawer.getByLabel(label);
    await checkbox.click();
  }

  /**
   * Click the save button to submit the form
   */
  async save(): Promise<void> {
    await this.saveButton.click();
  }

  /**
   * Click the cancel button to close without saving
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
  }

  /**
   * Click the close (X) button to close the drawer
   */
  async close(): Promise<void> {
    await this.closeButton.click();
  }

  /**
   * Wait for the drawer to close
   */
  async waitForClose(): Promise<void> {
    await this.drawer.waitFor({ state: 'hidden' });
  }

  /**
   * Wait for drawer loading to complete
   */
  async waitForLoad(): Promise<void> {
    await this.loadingSpinner.waitFor({ state: 'hidden' });
  }

  /**
   * Check if drawer is visible
   */
  async isVisible(): Promise<boolean> {
    return await this.drawer.isVisible();
  }

  /**
   * Get validation error message for a field
   * @param fieldName - Field name to check for error
   */
  async getFieldError(fieldName: string): Promise<string> {
    const errorElement = this.drawer.getByTestId(`error-${fieldName}`);
    return await errorElement.textContent() || '';
  }

  /**
   * Check if field has validation error
   * @param fieldName - Field name to check
   */
  async hasFieldError(fieldName: string): Promise<boolean> {
    const errorElement = this.drawer.getByTestId(`error-${fieldName}`);
    return await errorElement.isVisible();
  }
}

export default DrawerHelper;
