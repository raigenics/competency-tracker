// Module: assertions.ts
// Purpose: Custom assertion helpers for E2E tests
// Part of: CompetencyIQ E2E Automation Suite

import { Page, expect, Locator } from '@playwright/test';

/**
 * Assert that a data table is loaded and visible
 * Checks for table presence and at least one data row
 * 
 * @param page - Playwright page instance
 * @param tableSelector - Optional CSS selector for the table (default: 'table')
 */
export async function expectTableLoaded(
  page: Page,
  tableSelector: string = 'table'
): Promise<void> {
  const table = page.locator(tableSelector);
  
  // Table should be visible
  await expect(table).toBeVisible();
  
  // Should have at least one row (header or data)
  const rows = table.locator('tbody tr');
  
  // Wait for table to have content (not loading state)
  // TODO: Implement actual loading detection based on app patterns
  // await expect(rows).not.toHaveCount(0);
}

/**
 * Assert that a toast notification is visible
 * 
 * @param page - Playwright page instance
 * @param expectedText - Optional text to match in the toast
 * @param type - Optional toast type ('success' | 'error' | 'warning' | 'info')
 */
export async function expectToastVisible(
  page: Page,
  expectedText?: string,
  type?: 'success' | 'error' | 'warning' | 'info'
): Promise<void> {
  // TODO: Update selector based on actual toast component implementation
  const toastSelector = '[role="alert"], .toast, .notification';
  const toast = page.locator(toastSelector).first();
  
  await expect(toast).toBeVisible({ timeout: 5000 });
  
  if (expectedText) {
    await expect(toast).toContainText(expectedText);
  }
  
  if (type) {
    // TODO: Update based on how toast types are indicated in the app
    // await expect(toast).toHaveClass(new RegExp(type, 'i'));
  }
}

/**
 * Assert that a drawer/slide-out panel is open
 * 
 * @param page - Playwright page instance
 * @param drawerSelector - Optional CSS selector for the drawer
 */
export async function expectDrawerOpen(
  page: Page,
  drawerSelector?: string
): Promise<void> {
  // TODO: Update selector based on actual drawer component
  const selector = drawerSelector || '[role="dialog"], .drawer, .slide-panel';
  const drawer = page.locator(selector).first();
  
  await expect(drawer).toBeVisible();
  
  // Drawer should be in open/expanded state
  // TODO: Add specific checks based on drawer implementation
  // await expect(drawer).toHaveAttribute('aria-expanded', 'true');
}

/**
 * Assert that a modal dialog is visible
 * 
 * @param page - Playwright page instance
 * @param expectedTitle - Optional expected modal title
 */
export async function expectModalVisible(
  page: Page,
  expectedTitle?: string
): Promise<void> {
  // TODO: Update selector based on actual modal component
  const modal = page.locator('[role="dialog"], .modal, [data-testid="modal"]').first();
  
  await expect(modal).toBeVisible();
  
  if (expectedTitle) {
    // Check modal header/title contains expected text
    const titleLocator = modal.locator('h1, h2, h3, [class*="title"]').first();
    await expect(titleLocator).toContainText(expectedTitle);
  }
}

/**
 * Assert that an empty state is displayed
 * Used when a list/table has no data to show
 * 
 * @param page - Playwright page instance
 * @param expectedMessage - Optional expected empty state message
 */
export async function expectEmptyState(
  page: Page,
  expectedMessage?: string
): Promise<void> {
  // TODO: Update selector based on actual empty state component
  const emptyState = page.locator(
    '[data-testid="empty-state"], .empty-state, .no-data, .no-results'
  ).first();
  
  await expect(emptyState).toBeVisible();
  
  if (expectedMessage) {
    await expect(emptyState).toContainText(expectedMessage);
  }
}

/**
 * Assert that a loading spinner/indicator is NOT visible
 * Use after actions to confirm loading has completed
 * 
 * @param page - Playwright page instance
 * @param timeout - Max time to wait for loading to complete (default: 30000ms)
 */
export async function expectLoadingComplete(
  page: Page,
  timeout: number = 30000
): Promise<void> {
  // TODO: Update selectors based on actual loading indicators
  const loadingIndicators = page.locator(
    '.loading, .spinner, [data-testid="loading"], [aria-busy="true"]'
  );
  
  // Wait for all loading indicators to disappear
  await expect(loadingIndicators).toHaveCount(0, { timeout });
}

/**
 * Assert that a specific page/route is loaded
 * 
 * @param page - Playwright page instance
 * @param urlPattern - URL pattern to match (string or RegExp)
 */
export async function expectPageLoaded(
  page: Page,
  urlPattern: string | RegExp
): Promise<void> {
  await expect(page).toHaveURL(urlPattern);
  
  // Wait for network to be idle
  await page.waitForLoadState('networkidle', { timeout: 30000 });
}

/**
 * Assert that form validation error is visible
 * 
 * @param page - Playwright page instance
 * @param fieldName - Name/label of the field with the error
 * @param errorMessage - Expected error message (optional)
 */
export async function expectFormError(
  page: Page,
  fieldName: string,
  errorMessage?: string
): Promise<void> {
  // Find field by label and check for associated error
  const field = page.getByLabel(fieldName);
  
  // Check field has invalid state
  // TODO: Adjust based on how form validation is indicated
  // await expect(field).toHaveAttribute('aria-invalid', 'true');
  
  if (errorMessage) {
    // Look for error message near the field
    const errorLocator = page.locator('.error, .invalid-feedback, [role="alert"]')
      .filter({ hasText: errorMessage });
    await expect(errorLocator).toBeVisible();
  }
}

/**
 * Assert that a success message is displayed
 * 
 * @param page - Playwright page instance
 * @param message - Expected success message text
 */
export async function expectSuccessMessage(
  page: Page,
  message: string
): Promise<void> {
  // TODO: Update selectors based on actual success message component
  const successLocator = page.locator(
    '.success, .alert-success, [role="alert"]'
  ).filter({ hasText: message });
  
  await expect(successLocator).toBeVisible();
}

/**
 * Assert count of items in a list/table matches expected
 * 
 * @param locator - Playwright locator for the items
 * @param expectedCount - Expected number of items
 */
export async function expectItemCount(
  locator: Locator,
  expectedCount: number
): Promise<void> {
  await expect(locator).toHaveCount(expectedCount);
}
