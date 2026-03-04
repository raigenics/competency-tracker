// Module: org-structure.spec.ts
// Purpose: Smoke tests for Org Structure (Governance) module - critical path validation
// Part of: CompetencyIQ E2E Automation Suite

import { test, expect, APIRequestContext } from '@playwright/test';
import OrgStructurePage from '../../pages/orgStructure.page';

/**
 * Org Structure Smoke Tests
 *
 * @tags @smoke @governance
 *
 * Hierarchy: Segment -> Sub-Segment -> Project -> Team
 * OrgHierarchyPage.jsx: .oh-node (tree rows), .oh-caret (expand), .oh-pill (type badge)
 *
 * Test data lifecycle:
 *   beforeAll -> create hierarchy via API (POST /api/org-hierarchy/...)
 *   afterAll  -> delete hierarchy in reverse order (project -> sub-seg -> segments)
 *
 * API base: http://localhost:8000
 *   POST   /api/org-hierarchy/segments          body: { name }        -> { segment_id }
 *   POST   /api/org-hierarchy/sub-segments      body: { name, segment_id } -> { sub_segment_id }
 *   POST   /api/org-hierarchy/projects          body: { name, sub_segment_id } -> { project_id }
 *   DELETE /api/org-hierarchy/segments/{id}     -> 204 (409 if has deps)
 *   DELETE /api/org-hierarchy/sub-segments/{id} -> 204 (409 if has deps)
 *   DELETE /api/org-hierarchy/projects/{id}     -> 204
 */

const API_BASE = 'http://localhost:8000';

// Timestamped names so parallel/repeated runs never conflict
const ts = Date.now();
const SEG1_NAME = `PW-Seg1-${ts}`;   // has a sub-segment + project underneath
const SEG2_NAME = `PW-Seg2-${ts}`;   // standalone, used for search filter test
const SUB_NAME  = `PW-Sub-${ts}`;    // under SEG1
const PROJ_NAME = `PW-Proj-${ts}`;   // under SUB

// IDs stored after creation so afterAll can clean up
let seg1Id  = 0;
let seg2Id  = 0;
let subId   = 0;
let projId  = 0;

test.describe('Org Structure - Smoke Tests @smoke @governance', () => {

  // Setup: create hierarchy via API before any test runs ----------------------
  test.beforeAll(async ({ playwright }) => {
    const api: APIRequestContext = await playwright.request.newContext({
      baseURL: API_BASE,
    });

    try {
      // 1. Create SEG1
      const seg1Res = await api.post('/api/org-hierarchy/segments', {
        data: { name: SEG1_NAME },
      });
      expect(seg1Res.status()).toBe(201);
      seg1Id = (await seg1Res.json()).segment_id;

      // 2. Create SEG2 (standalone)
      const seg2Res = await api.post('/api/org-hierarchy/segments', {
        data: { name: SEG2_NAME },
      });
      expect(seg2Res.status()).toBe(201);
      seg2Id = (await seg2Res.json()).segment_id;

      // 3. Create SUB under SEG1
      const subRes = await api.post('/api/org-hierarchy/sub-segments', {
        data: { name: SUB_NAME, segment_id: seg1Id },
      });
      expect(subRes.status()).toBe(201);
      subId = (await subRes.json()).sub_segment_id;

      // 4. Create PROJ under SUB
      const projRes = await api.post('/api/org-hierarchy/projects', {
        data: { name: PROJ_NAME, sub_segment_id: subId },
      });
      expect(projRes.status()).toBe(201);
      projId = (await projRes.json()).project_id;
    } finally {
      await api.dispose();
    }
  });

  // Teardown: delete in reverse order (deps first) ----------------------------
  test.afterAll(async ({ playwright }) => {
    const api: APIRequestContext = await playwright.request.newContext({
      baseURL: API_BASE,
    });

    try {
      if (projId) await api.delete(`/api/org-hierarchy/projects/${projId}`);
      if (subId)  await api.delete(`/api/org-hierarchy/sub-segments/${subId}`);
      if (seg1Id) await api.delete(`/api/org-hierarchy/segments/${seg1Id}`);
      if (seg2Id) await api.delete(`/api/org-hierarchy/segments/${seg2Id}`);
    } finally {
      await api.dispose();
    }
  });

  // TEST 1 -------------------------------------------------------------------
  test('should load org structure page successfully', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    await expect(org.treePanel).toBeVisible();
    await expect(org.detailsPanel).toBeVisible();
    await expect(org.addSegmentBtn).toBeVisible();
    await expect(org.treeSearchInput).toBeVisible();
  });

  // TEST 2 -------------------------------------------------------------------
  test('should display test segments in tree', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    await expect(page.locator('.oh-node').filter({ hasText: SEG1_NAME })).toBeVisible();
    await expect(page.locator('.oh-node').filter({ hasText: SEG2_NAME })).toBeVisible();
  });

  // TEST 3 -------------------------------------------------------------------
  test('should expand segment to show sub-segments', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    await org.expandTreeNode(SEG1_NAME);
    await page.waitForTimeout(500);

    await expect(page.locator('.oh-node').filter({ hasText: SUB_NAME })).toBeVisible();
  });

  // TEST 4 -------------------------------------------------------------------
  test('should show segment details when segment is selected', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    await org.clickTreeNode(SEG1_NAME);
    await page.waitForTimeout(1000);

    // Empty state must NOT appear when an item is selected
    await expect(org.detailsPanel.locator('.oh-empty')).not.toBeVisible();
    // Details panel shows the selected item name
    await expect(org.detailsPanel).toContainText(SEG1_NAME);
  });

  // TEST 5 -------------------------------------------------------------------
  test('should show sub-segment details when sub-segment is selected', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    await org.expandTreeNode(SEG1_NAME);
    await page.waitForTimeout(500);

    await org.clickTreeNode(SUB_NAME);
    await page.waitForTimeout(1000);

    await expect(org.detailsPanel).toContainText(SUB_NAME);
    await expect(org.detailsPanel.locator('.oh-panel-body')).toBeVisible();
  });

  // TEST 6 -------------------------------------------------------------------
  test('should show project in tree under sub-segment', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    // Expand SEG1 -> expand SUB -> PROJ should appear
    await org.expandTreeNode(SEG1_NAME);
    await page.waitForTimeout(500);
    await org.expandTreeNode(SUB_NAME);
    await page.waitForTimeout(500);

    await expect(page.locator('.oh-node').filter({ hasText: PROJ_NAME })).toBeVisible();
  });

  // TEST 7 -------------------------------------------------------------------
  test('should filter tree using search', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    // searchTree() fills the input and waits 400ms for the debounce
    await org.searchTree(SEG1_NAME);

    await expect(page.locator('.oh-node').filter({ hasText: SEG1_NAME })).toBeVisible();
    // SEG2_NAME is different enough that it shouldn't match SEG1_NAME
    await expect(page.locator('.oh-node').filter({ hasText: SEG2_NAME })).not.toBeVisible();

    // Clear search: SEG2 must reappear
    await org.clearSearch();
    await expect(page.locator('.oh-node').filter({ hasText: SEG2_NAME })).toBeVisible();
  });

  // TEST 8 -------------------------------------------------------------------
  test('should add a new segment via modal and delete it', async ({ page }) => {
    const org = new OrgStructurePage(page);
    await org.navigate();
    await org.waitForTreeLoad();

    await org.openCreateSegmentModal();
    await expect(org.modal).toBeVisible();

    const uniqueName = `PW-Segment-${Date.now()}`;
    await org.fillModalName(uniqueName);
    await org.saveModal();

    // Full hierarchy reload after create: wait generously
    await page.waitForTimeout(1500);

    // New segment must appear in the tree
    await expect(page.locator('.oh-node').filter({ hasText: uniqueName })).toBeVisible();

    // CLEANUP: select the segment and delete it
    await org.clickTreeNode(uniqueName);
    await page.waitForTimeout(1000);

    // OrgHierarchyPage.jsx renderPanel:
    //   title={`Delete ${getTypeLabel(selectedItem.type).toLowerCase()}`}
    // getTypeLabel('segment') = 'Segment' -> .toLowerCase() = 'segment'
    // -> title="Delete segment"
    await org.detailsPanel.locator('button[title="Delete segment"]').click();

    await expect(org.modal).toBeVisible();
    await org.modalDeleteBtn.click();
    await expect(org.modal).toBeHidden();
    await page.waitForTimeout(1500);

    await expect(page.locator('.oh-node').filter({ hasText: uniqueName })).not.toBeVisible();
  });

});
