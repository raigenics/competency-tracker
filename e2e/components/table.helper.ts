// Module: table.helper.ts
// Purpose: Paginated table interactions used across governance modules
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Table Helper
 * 
 * Provides reusable methods for interacting with data tables:
 * - Employee Management table
 * - Role Catalog table
 * - Any paginated data table
 */
export class TableHelper {
  readonly page: Page;
  readonly table: Locator;
  readonly tbody: Locator;
  readonly thead: Locator;
  readonly pagination: Locator;
  readonly pageSizeSelect: Locator;
  readonly selectAllCheckbox: Locator;
  readonly loadingSpinner: Locator;
  readonly emptyState: Locator;

  /**
   * Create a new TableHelper instance
   * @param page - Playwright Page object
   * @param tableTestId - data-testid of the table element
   */
  constructor(page: Page, tableTestId: string = 'data-table') {
    this.page = page;
    this.table = page.getByTestId(tableTestId);
    this.tbody = this.table.locator('tbody');
    this.thead = this.table.locator('thead');
    this.pagination = page.getByTestId('pagination');
    this.pageSizeSelect = page.getByTestId('page-size-select');
    this.selectAllCheckbox = this.thead.getByRole('checkbox');
    this.loadingSpinner = page.getByTestId('table-loading');
    this.emptyState = page.getByTestId('table-empty');
  }

  /**
   * Get the total number of visible rows in the table
   */
  async getRowCount(): Promise<number> {
    const rows = this.tbody.locator('tr');
    return await rows.count();
  }

  /**
   * Get a specific row by index (0-based)
   * @param index - Row index (0-based)
   */
  getRowByIndex(index: number): Locator {
    return this.tbody.locator('tr').nth(index);
  }

  /**
   * Get a specific row by data-testid
   * @param rowId - The ID in the row's data-testid (e.g., table-row-123)
   */
  getRowById(rowId: number): Locator {
    return this.page.getByTestId(`table-row-${rowId}`);
  }

  /**
   * Navigate to the next page
   */
  async nextPage(): Promise<void> {
    const nextButton = this.pagination.getByRole('button', { name: /next/i });
    await nextButton.click();
    await this.waitForLoad();
  }

  /**
   * Navigate to the previous page
   */
  async prevPage(): Promise<void> {
    const prevButton = this.pagination.getByRole('button', { name: /prev/i });
    await prevButton.click();
    await this.waitForLoad();
  }

  /**
   * Navigate to a specific page number
   * @param pageNumber - Page number to navigate to
   */
  async goToPage(pageNumber: number): Promise<void> {
    const pageButton = this.pagination.getByRole('button', { name: String(pageNumber) });
    await pageButton.click();
    await this.waitForLoad();
  }

  /**
   * Select a row by clicking its checkbox
   * @param index - Row index (0-based)
   */
  async selectRow(index: number): Promise<void> {
    const row = this.getRowByIndex(index);
    const checkbox = row.getByRole('checkbox');
    await checkbox.click();
  }

  /**
   * Select all rows using the header checkbox
   */
  async selectAll(): Promise<void> {
    await this.selectAllCheckbox.click();
  }

  /**
   * Change the page size
   * @param size - Number of rows per page (e.g., 10, 25, 50)
   */
  async setPageSize(size: number): Promise<void> {
    await this.pageSizeSelect.click();
    await this.page.getByRole('option', { name: String(size) }).click();
    await this.waitForLoad();
  }

  /**
   * Get text content of a specific cell
   * @param rowIndex - Row index (0-based)
   * @param columnIndex - Column index (0-based)
   */
  async getCellText(rowIndex: number, columnIndex: number): Promise<string> {
    const row = this.getRowByIndex(rowIndex);
    const cell = row.locator('td').nth(columnIndex);
    return await cell.textContent() || '';
  }

  /**
   * Click action button in a row
   * @param rowIndex - Row index (0-based)
   * @param buttonTestId - data-testid of the action button
   */
  async clickRowAction(rowIndex: number, buttonTestId: string): Promise<void> {
    const row = this.getRowByIndex(rowIndex);
    const button = row.getByTestId(buttonTestId);
    await button.click();
  }

  /**
   * Wait for table to finish loading
   */
  async waitForLoad(): Promise<void> {
    await this.loadingSpinner.waitFor({ state: 'hidden' });
  }

  /**
   * Check if table is empty (shows empty state)
   */
  async isEmpty(): Promise<boolean> {
    return await this.emptyState.isVisible();
  }

  /**
   * Get total items count from pagination
   */
  async getTotalCount(): Promise<number> {
    const countText = await this.pagination.getByTestId('total-count').textContent();
    return parseInt(countText || '0', 10);
  }

  /**
   * Get current page number from pagination
   */
  async getCurrentPage(): Promise<number> {
    const currentPage = await this.pagination.getByTestId('current-page').textContent();
    return parseInt(currentPage || '1', 10);
  }

  /**
   * Sort table by clicking a column header
   * @param columnName - Column header text
   */
  async sortByColumn(columnName: string): Promise<void> {
    const header = this.thead.getByRole('columnheader', { name: columnName });
    await header.click();
    await this.waitForLoad();
  }
}

export default TableHelper;
