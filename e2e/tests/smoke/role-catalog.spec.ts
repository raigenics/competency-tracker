// Module: role-catalog.spec.ts
// Purpose: Smoke tests for Role Catalog (Governance) module - critical path validation
// Part of: CompetencyIQ E2E Automation Suite

import { test, expect } from '@playwright/test';
import RoleCatalogPage from '../../pages/roleCatalog.page';

test.describe('Role Catalog - Smoke Tests @smoke @governance', () => {

  /**
   * TEST 1
   * Verifies that the Role Catalog page loads correctly:
   * the page wrapper, table container, Add Role button, and
   * search input are all visible and the page title is set.
   */
  test('should load role catalog page successfully', async ({ page }) => {
    const catalog = new RoleCatalogPage(page);
    await catalog.navigate();

    await expect(catalog.pageWrapper).toBeVisible({ timeout: 10000 });
    await expect(page).toHaveTitle(/Roles|CompetencyIQ/i);
    await expect(catalog.tableContainer).toBeVisible({ timeout: 10000 });
    await expect(catalog.addRoleButton).toBeVisible({ timeout: 10000 });
    await expect(catalog.searchInput).toBeVisible({ timeout: 10000 });
  });

  /**
   * TEST 2
   * Verifies that the 12 pre-seeded roles are present in the table:
   * total row count is at least 12, and spot-checks three specific roles
   * by name.
   */
  test('should display seeded roles in table', async ({ page }) => {
    const catalog = new RoleCatalogPage(page);
    await catalog.navigate();
    await catalog.waitForTableLoad();

    const count = await catalog.getRowCount();
    expect(count).toBeGreaterThanOrEqual(12);

    await expect(catalog.findRowByName('Backend Engineer')).toBeVisible({ timeout: 10000 });
    await expect(catalog.findRowByName('QA Engineer')).toBeVisible({ timeout: 10000 });
    await expect(catalog.findRowByName('Scrum Master')).toBeVisible({ timeout: 10000 });
  });

  /**
   * TEST 3
   * Verifies that the table renders the four expected column headers:
   * Role Name, Role Alias, Description, and Actions.
   */
  test('should show correct table columns', async ({ page }) => {
    const catalog = new RoleCatalogPage(page);
    await catalog.navigate();
    await catalog.waitForTableLoad();

    await expect(page.locator('th:has-text("Role Name")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("Role Alias")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("Description")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('th:has-text("Actions")')).toBeVisible({ timeout: 10000 });
  });

  /**
   * TEST 4
   * Verifies that the search input filters table rows correctly:
   * typing "Backend" shows the matching role and hides unrelated ones,
   * and clearing the search restores the full list.
   */
  test('should filter roles using search', async ({ page }) => {
    const catalog = new RoleCatalogPage(page);
    await catalog.navigate();
    await catalog.waitForTableLoad();

    await catalog.searchFor('Backend');

    await expect(catalog.findRowByName('Backend Engineer')).toBeVisible({ timeout: 10000 });
    await expect(catalog.findRowByName('Frontend Engineer')).not.toBeVisible({ timeout: 10000 });

    await catalog.clearSearch();
    await catalog.waitForTableLoad();

    const count = await catalog.getRowCount();
    expect(count).toBeGreaterThanOrEqual(12);
  });

  /**
   * TEST 5
   * Verifies the inline add-role workflow end-to-end:
   * opens the form, fills name/alias/description, saves, confirms the new
   * row appears and the total count increases by 1.
   * Cleans up by deleting the created role before the test ends.
   */
  test('should add a new role inline', async ({ page }) => {
    const uniqueRoleName = `PW-Role-${Date.now()}`;
    const catalog = new RoleCatalogPage(page);
    await catalog.navigate();
    await catalog.waitForTableLoad();

    const countBefore = await catalog.getRowCount();

    await catalog.clickAddRole();
    await expect(catalog.addNameInput).toBeVisible({ timeout: 10000 });

    await catalog.fillAddForm(uniqueRoleName, 'PTR', 'Created by automation');
    await catalog.saveInlineForm();

    await expect(catalog.findRowByName(uniqueRoleName)).toBeVisible({ timeout: 10000 });

    const countAfter = await catalog.getRowCount();
    expect(countAfter).toBe(countBefore + 1);

    // CLEANUP — delete the role we just created
    await catalog.clickDeleteOnRow(uniqueRoleName);
    await catalog.confirmDelete();
    await expect(catalog.findRowByName(uniqueRoleName)).not.toBeVisible({ timeout: 10000 });
  });

  /**
   * TEST 6
   * Verifies that cancelling the add-role form does not persist any data:
   * the form closes and the row count remains unchanged.
   */
  test('should cancel add role without saving', async ({ page }) => {
    const catalog = new RoleCatalogPage(page);
    await catalog.navigate();
    await catalog.waitForTableLoad();

    const countBefore = await catalog.getRowCount();

    await catalog.clickAddRole();
    await catalog.fillAddForm('Should Not Be Saved');
    await catalog.cancelInlineForm();

    await expect(catalog.addNameInput).not.toBeVisible({ timeout: 10000 });

    const countAfter = await catalog.getRowCount();
    expect(countAfter).toBe(countBefore);
  });

  /**
   * TEST 7
   * Verifies the empty-state behaviour when a search yields no results:
   * the empty state element and "No roles found" text appear, and
   * clearing the search restores the table.
   */
  test('should show empty state when search has no results', async ({ page }) => {
    const catalog = new RoleCatalogPage(page);
    await catalog.navigate();
    await catalog.waitForTableLoad();

    await catalog.searchFor('zzznotarealrole999xyz');

    await expect(catalog.emptyState).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.empty-state h3:has-text("No roles found")')).toBeVisible({ timeout: 10000 });

    await catalog.clearSearch();

    await expect(catalog.emptyState).not.toBeVisible({ timeout: 10000 });
    await expect(catalog.tableContainer).toBeVisible({ timeout: 10000 });
  });

});