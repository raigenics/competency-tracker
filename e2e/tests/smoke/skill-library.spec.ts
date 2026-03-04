// Module: skill-library.spec.ts
// Purpose: Smoke tests for Skill Taxonomy (Governance) module - critical path validation
// Part of: CompetencyIQ E2E Automation Suite

import { test, expect } from '@playwright/test';
import SkillLibraryPage from '../../pages/skillLibrary.page';

/**
 * Skill Taxonomy Smoke Tests
 *
 * @tags @smoke @governance
 *
 * Two-panel layout:
 *   LEFT  — .tree-panel  : Category → Sub-Category tree
 *   RIGHT — .details-panel : Context-sensitive detail view
 *
 * Seeded data (ids 9050-9062):
 *   Categories : Programming, Testing
 *   Sub-cats   : Frontend Dev, Backend Dev (under Programming)
 *                Automation QA (under Testing)
 *   Skills     : JavaScript, TypeScript, React, TailwindCSS (Frontend Dev)
 *                Python, FastAPI, PostgreSQL, SQLAlchemy (Backend Dev)
 *                Playwright, Test Design (Automation QA)
 */
test.describe('Skill Taxonomy - Smoke Tests @smoke @governance', () => {

  // ── TEST 1 ────────────────────────────────────────────────────────────────
  test('should load skill taxonomy page successfully', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    await expect(skillLibrary.treePanel).toBeVisible();
    await expect(skillLibrary.detailsPanel).toBeVisible();
    await expect(skillLibrary.treeSearchInput).toBeVisible();
    await expect(skillLibrary.addCategoryBtn).toBeVisible();
  });

  // ── TEST 2 ────────────────────────────────────────────────────────────────
  test('should display seeded categories in tree', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    // Category nodes render as <div className="sl-node"> (SkillLibraryPage.jsx renderTree)
    await expect(page.locator('.sl-node').filter({ hasText: 'Programming' })).toBeVisible();
    await expect(page.locator('.sl-node').filter({ hasText: 'Testing' })).toBeVisible();
  });

  // ── TEST 3 ────────────────────────────────────────────────────────────────
  test('should expand category to show sub-categories', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    // Caret renders as <span className="sl-caret"> inside <div className="sl-node">
    await page.locator('.sl-node').filter({ hasText: 'Programming' })
      .locator('.sl-caret').click();
    await page.waitForTimeout(500);

    // Sub-category nodes render as <div className="sl-subnode">
    await expect(page.locator('.sl-subnode').filter({ hasText: 'Frontend Dev' })).toBeVisible();
    await expect(page.locator('.sl-subnode').filter({ hasText: 'Backend Dev' })).toBeVisible();
  });

  // ── TEST 4 ────────────────────────────────────────────────────────────────
  test('should show skills table when sub-category is selected', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    // Expand Programming
    await page.locator('.sl-node').filter({ hasText: 'Programming' })
      .locator('.sl-caret').click();
    await page.waitForTimeout(500);

    // Select Frontend Dev sub-category
    await page.locator('.sl-subnode').filter({ hasText: 'Frontend Dev' }).click();
    await page.waitForTimeout(1000);

    await expect(skillLibrary.skillsTable).toBeVisible();
    await expect(skillLibrary.addSkillBtn).toBeVisible();
    await expect(skillLibrary.findSkillByName('JavaScript')).toBeVisible();
    await expect(skillLibrary.findSkillByName('TypeScript')).toBeVisible();
    await expect(skillLibrary.findSkillByName('React')).toBeVisible();
  });

  // ── TEST 5 ────────────────────────────────────────────────────────────────
  test('should show category details when category is selected', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    await skillLibrary.clickTreeNode('Programming');
    await page.waitForTimeout(1000);

    await expect(skillLibrary.categoryBadge).toBeVisible();
    // sl-pill text is UPPERCASE: 'CATEGORY' (SkillLibraryPage.jsx renderCategoryPanel)
    await expect(skillLibrary.categoryBadge).toContainText('CATEGORY');
    await expect(skillLibrary.detailsPanel).toContainText('Programming');
  });

  // ── TEST 6 ────────────────────────────────────────────────────────────────
  test('should filter skills within sub-category', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    // Expand Programming
    await page.locator('.sl-node').filter({ hasText: 'Programming' })
      .locator('.sl-caret').click();
    await page.waitForTimeout(500);

    // Select Frontend Dev sub-category
    await page.locator('.sl-subnode').filter({ hasText: 'Frontend Dev' }).click();
    await page.waitForTimeout(1000);

    // Filter — only "JavaScript" should remain, "React" should disappear
    await skillLibrary.skillSearchInput.fill('Java');
    await page.waitForTimeout(500);

    await expect(skillLibrary.findSkillByName('JavaScript')).toBeVisible();
    await expect(skillLibrary.findSkillByName('React')).not.toBeVisible();

    // Clear filter — "React" must come back
    await skillLibrary.skillSearchInput.fill('');
    await page.waitForTimeout(500);

    await expect(skillLibrary.findSkillByName('React')).toBeVisible();
  });

  // ── TEST 7 ────────────────────────────────────────────────────────────────
  test('should add a new skill inline and delete it', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    // Expand Testing → select Automation QA
    await page.locator('.sl-node').filter({ hasText: 'Testing' })
      .locator('.sl-caret').click();
    await page.waitForTimeout(500);

    await page.locator('.sl-subnode').filter({ hasText: 'Automation QA' }).click();
    await page.waitForTimeout(1000);

    const countBefore = await skillLibrary.getSkillRowCount();

    // Open inline add-skill form
    await skillLibrary.clickAddSkill();
    await expect(skillLibrary.addSkillNameInput).toBeVisible();

    // Fill and save
    const uniqueSkillName = `PW-Skill-${Date.now()}`;
    const ts = Date.now();
    // Aliases must also be unique — hardcoded 'pw' can persist if a prior run
    // crashed before cleanup, causing a 409 Conflict on the next run.
    await skillLibrary.fillAddSkillForm(uniqueSkillName, `pw-${ts},pw-test-${ts}`);
    await skillLibrary.saveSkillForm();

    // Verify row was added
    await expect(skillLibrary.findSkillByName(uniqueSkillName)).toBeVisible();
    expect(await skillLibrary.getSkillRowCount()).toBe(countBefore + 1);

    // ── CLEANUP: delete the skill ─────────────────────────────────────────
    const skillRow = skillLibrary.findSkillByName(uniqueSkillName);
    await skillRow.hover();
    await skillRow.locator('button.btn-delete').click();

    await expect(page.locator('.modal-overlay.active')).toBeVisible();
    await page.locator('.modal-overlay.active .btn-danger').click();
    await expect(page.locator('.modal-overlay.active')).toBeHidden();

    await expect(skillLibrary.findSkillByName(uniqueSkillName)).not.toBeVisible();
  });

  // ── TEST 8 ────────────────────────────────────────────────────────────────
  test('should add a new category via modal and delete it', async ({ page }) => {
    const skillLibrary = new SkillLibraryPage(page);
    await skillLibrary.navigate();
    await skillLibrary.waitForTreeLoad();

    // Open creation modal
    await skillLibrary.openCreateModal();
    await expect(skillLibrary.modal).toBeVisible();

    // Fill and save
    const uniqueCatName = `PW-Category-${Date.now()}`;
    await skillLibrary.fillModalName(uniqueCatName);
    await skillLibrary.saveModal();
    await page.waitForTimeout(1000);

    // Verify it appears in the tree — new category renders as .sl-node
    await expect(page.locator('.sl-node').filter({ hasText: uniqueCatName })).toBeVisible();

    // ── CLEANUP: delete the category ─────────────────────────────────────
    await skillLibrary.clickTreeNode(uniqueCatName);
    await page.waitForTimeout(1000);

    // SkillLibraryPage.jsx renderCategoryPanel: <button ... title="Delete category">🗑️</button>
    await skillLibrary.detailsPanel.locator('button[title="Delete category"]').click();

    await expect(skillLibrary.modal).toBeVisible();
    await skillLibrary.modalDeleteBtn.click();
    await expect(skillLibrary.modal).toBeHidden();
    await page.waitForTimeout(1000);

    await expect(page.locator('.sl-node').filter({ hasText: uniqueCatName })).not.toBeVisible();
  });

});