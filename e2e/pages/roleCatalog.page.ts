// Module: roleCatalog.page.ts
// Purpose: Page object for Role Catalog (Governance) module
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Role Catalog Page Object
 *
 * Route: /governance/role-catalog
 *
 * Selectors are based on CSS classes, text content, roles, and attributes
 * present in RolesPage.jsx (no data-testid attributes exist on that component).
 */
export default class RoleCatalogPage {
  readonly page: Page;

  // ── Layout ──────────────────────────────────────────────────────────────
  readonly pageWrapper: Locator;
  readonly tableContainer: Locator;
  readonly table: Locator;
  readonly tableRows: Locator;
  readonly emptyState: Locator;

  // ── Header controls ──────────────────────────────────────────────────────
  readonly addRoleButton: Locator;
  readonly importButton: Locator;
  readonly downloadLink: Locator;
  readonly searchInput: Locator;

  // ── Inline add-row form ──────────────────────────────────────────────────
  readonly addNameInput: Locator;
  readonly addAliasInput: Locator;
  readonly addDescInput: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  // ── Bulk action bar ──────────────────────────────────────────────────────
  readonly bulkActionBar: Locator;
  readonly selectedPill: Locator;

  // ── Delete-confirm modal ─────────────────────────────────────────────────
  readonly modal: Locator;
  readonly modalConfirm: Locator;
  readonly modalCancel: Locator;

  constructor(page: Page) {
    this.page = page;

    this.pageWrapper     = page.locator('[data-page="role-catalog"]');
    this.tableContainer  = page.locator('.skills-table-container');
    this.table           = page.locator('.skills-table');
    this.tableRows       = page.locator('.skills-table tbody tr');
    this.emptyState      = page.locator('.empty-state');

    this.addRoleButton   = page.locator('button:has-text("+ Add Role")');
    this.importButton    = page.locator('button:has-text("Import Roles")');
    this.downloadLink    = page.locator('a:has-text("Download Template")');
    this.searchInput     = page.locator('input[placeholder="Search roles..."]');

    this.addNameInput    = page.locator('input[placeholder="Enter role name"]');
    this.addAliasInput   = page.locator('input[placeholder="Enter comma-separated aliases"]');
    this.addDescInput    = page.locator('input[placeholder="Enter description (optional)"]');
    this.saveButton      = page.locator('button.btn-save');
    this.cancelButton    = page.locator('button.btn-cancel');

    this.bulkActionBar   = page.locator('.bulk-action-bar');
    this.selectedPill    = page.locator('.selected-count-pill');

    this.modal        = page.locator('.modal-overlay.active');
    this.modalConfirm = page.locator('.modal-overlay.active .btn-danger');
    this.modalCancel  = page.locator('.modal-overlay.active .btn-secondary');
  }

  /**
   * Navigate to the role catalog page and wait for it to be ready.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/governance/role-catalog');
    await this.page.waitForSelector('[data-page="role-catalog"]');
    await this.page.waitForSelector('.skills-table-container', {
      state: 'visible',
      timeout: 15000,
    });
  }

  /**
   * Wait for the table to finish loading data.
   * Waits for the container to appear, the loading state to clear,
   * and at least one row to be present.
   */
  async waitForTableLoad(): Promise<void> {
    await this.tableContainer.waitFor({ state: 'visible', timeout: 15000 });
    // If an empty-state div is transiently shown (e.g. "Loading roles..."),
    // wait until it is gone before asserting on rows.
    try {
      await this.page.waitForSelector('.empty-state', {
        state: 'hidden',
        timeout: 10000,
      });
    } catch {
      // empty-state may never appear — that's fine, continue
    }
    await this.page.waitForSelector('.skills-table tbody tr', {
      state: 'visible',
      timeout: 10000,
    });
  }

  /**
   * Return the number of rows currently rendered in the table body.
   */
  async getRowCount(): Promise<number> {
    return this.tableRows.count();
  }

  /**
   * Return a locator scoped to the tbody row that contains the given text.
   */
  findRowByName(name: string): Locator {
    return this.page.locator('.skills-table tbody tr').filter({ hasText: name });
  }

  /**
   * Click "+ Add Role" and wait for the inline form to appear.
   */
  async clickAddRole(): Promise<void> {
    await this.addRoleButton.click();
    await this.addNameInput.waitFor({ state: 'visible', timeout: 10000 });
  }

  /**
   * Fill the inline add-role form fields.
   * Only fills alias and description when values are provided.
   */
  async fillAddForm(name: string, alias?: string, description?: string): Promise<void> {
    await this.addNameInput.fill(name);
    if (alias !== undefined) {
      await this.addAliasInput.fill(alias);
    }
    if (description !== undefined) {
      await this.addDescInput.fill(description);
    }
  }

  /**
   * Click Save and wait for the inline form to close.
   */
  async saveInlineForm(): Promise<void> {
    await this.saveButton.click();
    // Wait for either success (form closes) or failure (error appears).
    // If the role name is a duplicate, the API returns 409 and the
    // form stays open with an inline error — we must handle both cases.
    await Promise.race([
      this.addNameInput.waitFor({ state: 'hidden', timeout: 10000 }),
      this.page.waitForTimeout(10000),
    ]);
    const formStillOpen = await this.addNameInput.isVisible();
    if (formStillOpen) {
      throw new Error(
        'saveInlineForm: form did not close after clicking Save. ' +
        'The role name may already exist (duplicate 409 error). ' +
        'Check the inline error message on the form.'
      );
    }
  }

  /**
   * Click Cancel and wait for the inline form to close.
   */
  async cancelInlineForm(): Promise<void> {
    await this.cancelButton.click();
    await this.addNameInput.waitFor({ state: 'hidden', timeout: 10000 });
  }

  /**
   * Click the Edit action on the row matching roleName.
   * Waits for the inline edit name input to appear.
   */
  async clickEditOnRow(roleName: string): Promise<void> {
  const row = this.findRowByName(roleName);
  // Row actions are hover-only — must hover the row first
  await row.hover();
  await row.locator('.action-link:has-text("Edit")').waitFor({ state: 'visible', timeout: 5000 });
  await row.locator('.action-link:has-text("Edit")').click();
  await this.page.waitForSelector('input[placeholder="Enter role name"]', {
    state: 'visible',
    timeout: 10000,
  });
}

  /**
   * Click the Delete action on the row matching roleName.
   * Waits for the confirmation modal to appear.
   */
  async clickDeleteOnRow(roleName: string): Promise<void> {
  const row = this.findRowByName(roleName);
  // Row actions are hover-only — must hover the row first
  await row.hover();
  await row.locator('.action-link.danger').waitFor({ state: 'visible', timeout: 5000 });
  await row.locator('.action-link.danger').click();
  await this.page.waitForSelector('.modal-overlay.active', {
  state: 'visible',
  timeout: 10000
  });
}

  /**
   * Confirm deletion in the modal and wait for it to close.
   */
  async confirmDelete(): Promise<void> {
  const modalDeleteBtn = this.page.locator('.modal-overlay.active .btn-danger');
  await modalDeleteBtn.waitFor({ state: 'visible', timeout: 10000 });
  await modalDeleteBtn.click();
  await this.page.waitForSelector('.modal-overlay.active', {
    state: 'hidden',
    timeout: 10000
  });
}
  /**
   * Type a search query into the search input and wait for the debounce.
   */
  async searchFor(query: string): Promise<void> {
    await this.searchInput.fill(query);
    // Do NOT wait for .skills-table-container here.
    // When search returns no results, the table disappears
    // and .empty-state renders instead.
    // Wait only for the debounce to settle.
    await this.page.waitForTimeout(800);
  }

  /**
   * Clear the search input.
   */
  async clearSearch(): Promise<void> {
    await this.searchInput.fill('');
  }
}
