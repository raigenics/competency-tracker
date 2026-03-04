// Module:  skill-coverage.spec.ts
// Purpose: Smoke tests for Skill Coverage / Capability Overview module
// Part of: CompetencyIQ E2E Automation Suite
//
// Page under test: /skill-coverage → SkillCoveragePage (Taxonomy/SkillCoveragePage.jsx)
//
// ⚠️  IMPORTANT — COMMON MISTAKES AVOIDED:
//   1. Title is "Capability Overview" NOT "Skill Coverage" (the h1 in SkillCoveragePage.jsx)
//   2. Metric values are NOT asserted — they change with live data
//   3. Level 2 expand (sub-cat → skills) is NOT a dedicated smoke test
//   4. waitForTreeLoad() is ALWAYS called before any tree assertion

import { test, expect } from '@playwright/test';
import SkillCoveragePage from '../../pages/skillCoverage.page';

test.describe('Skill Coverage - Smoke Tests @smoke @insights', () => {

  // ── TEST 1 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: If the two-pane layout shell is broken the entire page is unusable.
  // This test confirms the route maps to the correct component and the layout
  // structure renders. A broken rendering here means every other test would fail.
  test('loads two-pane layout with left and right panes', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    // Page root must exist
    await expect(sc.pageRoot).toBeVisible();

    // Left and right panes from TwoPaneLayout (data-testid set unconditionally)
    await expect(sc.leftPane).toBeVisible();
    await expect(sc.rightPane).toBeVisible();

    // URL confirms routing
    await expect(page).toHaveURL(/\/skill-coverage/);
  });

  // ── TEST 2 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The correct h1 text confirms the right component mounted.
  // The title is "Capability Overview" (from h1.co-page-title in JSX line 676).
  // If the wrong component is mounted the sidebar link is broken — unusable.
  test('renders page title "Capability Overview"', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    // h1.co-page-title — confirmed in SkillCoveragePage.jsx line 676
    await expect(sc.pageTitle).toContainText('Capability Overview');
  });

  // ── TEST 3 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The metrics strip is part of the page header and shows 4 key stats.
  // If the strip renders nothing, the header is broken. We do NOT assert numeric
  // values because those change with live data.
  test('metrics strip is visible with exactly 4 items', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    await expect(sc.metricsStrip).toBeVisible();

    // Exactly 4 div.co-metrics-item: skills, employees, aver. proficiency, certifications
    await expect(sc.metricsItems).toHaveCount(4);

    // Each item has a visible label (text never empty even while loading)
    const labels = ['skills', 'employees', 'aver. proficiency', 'certifications'];
    for (const label of labels) {
      await expect(
        sc.metricsStrip.locator('.co-metrics-label', { hasText: label })
      ).toBeVisible();
    }
  });

  // ── TEST 4 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The three controls (search, Expand All, Collapse All) are the
  // only way to interact with the tree. If any is absent, tree navigation
  // is partially broken and the page cannot be fully used.
  test('tree toolbar has search input, Expand All, and Collapse All buttons', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    // Search box wrapper and its input
    await expect(sc.searchWrapper).toBeVisible();
    await expect(sc.searchInput).toBeVisible();

    // Expand All and Collapse All buttons (button.co-tree-action-btn)
    await expect(sc.expandAllBtn).toBeVisible();
    await expect(sc.collapseAllBtn).toBeVisible();

    // Path legend confirms structure hint is shown
    await expect(sc.pathLegend).toContainText('Category');
  });

  // ── TEST 5 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The Organisation Summary button is the first visible item in
  // the tree body and its "active" class drives the default right-panel state.
  // If it is missing or not active on load, the right panel shows the wrong
  // default state — users immediately see a broken page.
  test('Organisation Summary button is visible and active by default', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    await expect(sc.orgSummaryBtn).toBeVisible();
    await expect(sc.orgSummaryBtn).toContainText('Organisation Summary');

    // Active class is present when !selectedSkill (default: no skill selected)
    expect(await sc.isOrgSummaryActive()).toBe(true);
  });

  // ── TEST 6 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: If no categories appear after load the tree is empty and the
  // page is useless. This verifies the lazy-load API call (skillApi.getCategories)
  // succeeded and the results were rendered.
  test('at least one category is visible in the tree after load', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    const count = await sc.getCategoryCount();
    expect(count).toBeGreaterThanOrEqual(1);

    // Each category row has the type badge "Category"
    await expect(sc.categoryRows.first().locator('.co-tree-type')).toContainText('Category');
  });

  // ── TEST 7 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: Expanding a category is the primary Level-1 tree interaction.
  // If this fails, users cannot reach any sub-categories or skills — the tree
  // provides zero value. It also validates the lazy-load for sub-categories.
  test('expanding a category reveals sub-category rows', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    // Expand the first available category
    await sc.expandFirstCategory();

    // At least one sub-category row must now be visible
    await expect(sc.subCategoryRows.first()).toBeVisible();
    await expect(sc.subCategoryRows.first().locator('.co-tree-type')).toContainText('Sub');
  });

  // ── TEST 8 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The right panel showing "Organisation Capability Summary" is the
  // default state every user sees on arrival. If this content is missing, the
  // right side of the page is blank on load — a visually broken first impression.
  test('right panel shows Organisation Capability Summary by default', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    // co-detail-title rendered by SkillDetailsPanel when skill prop === null
    await expect(sc.rightPanelDefault).toBeVisible();
    await expect(sc.rightPanelDefault).toContainText('Organisation Capability Summary');

    // dp-top-bar (skill-selected state) must NOT be visible yet
    await expect(sc.rightPanelSkillDetail).not.toBeVisible();
  });

  // ── TEST 9 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: Clicking a skill and seeing the detail panel is the core use-case
  // of this page. If skill selection is broken the page has no primary function.
  // Setup uses expand category + expand subcategory to reach a skill row —
  // this is necessary scaffolding, not the assertion target.
  test('clicking a skill populates the right panel with skill details', async ({ page }) => {
    const sc = new SkillCoveragePage(page);
    await sc.navigate();
    await sc.waitForTreeLoad();

    // Setup: drill down to skill rows
    await sc.expandFirstCategory();
    await sc.expandFirstSubcategory();

    // Verify at least one skill row appeared before clicking
    await expect(sc.skillRows.first()).toBeVisible();
    await expect(sc.skillRows.first().locator('.co-tree-type')).toContainText('Skill');

    // Click the first skill
    await sc.clickFirstSkill();

    // Right panel must switch to skill-detail mode (dp-top-bar renders)
    await expect(sc.rightPanelSkillDetail).toBeVisible();

    // Back button must be present in the detail panel
    await expect(sc.backBtn).toBeVisible();
    await expect(sc.backBtn).toContainText('Back');

    // Default org summary title must no longer be visible
    await expect(sc.rightPanelDefault).not.toBeVisible();
  });

  // ── TEST 10 ───────────────────────────────────────────────────────────────
  // SMOKE: Search is the primary navigation mechanism on this page.
  // Silent API failure or missed debounce = page looks fine but returns nothing.
  // Uses seeded skill "JavaScript" (skill_id 9070, 3 employees) - guaranteed results.
  test('should return results when searching for a seeded skill term', async ({ page }) => {
    const sc = new SkillCoveragePage(page);

    // Step 1+2: Fresh load, wait for tree
    await sc.navigate();
    await sc.waitForTreeLoad();

    // Step 3: Confirm search input is ready (enabled after tree load)
    await expect(sc.searchInput).toBeVisible();
    await expect(sc.searchInput).not.toBeDisabled();

    // Step 4: Type search term — searchFor fills input and waits 400ms (debounce 300ms + buffer)
    await sc.searchFor('JavaScript');

    // Step 5: Wait for search hint — confirms API round-trip completed
    await sc.searchHint.waitFor({ state: 'visible', timeout: 5_000 });
    await expect(sc.searchHint).toContainText('Showing results for "JavaScript"');

    // Step 6: Assert "JavaScript" text appears in a filtered tree node
    await expect(
      page.locator('.co-tree-name', { hasText: 'JavaScript' }).first()
    ).toBeVisible();

    // Step 7: Still in search mode
    await expect(sc.searchHint).toBeVisible();

    // Step 8: Clear search
    await sc.clearSearch();

    // Step 9: Full tree restored — hint gone, input empty, category rows back
    await expect(sc.searchHint).not.toBeVisible();
    await expect(sc.searchInput).toHaveValue('');
    await expect(sc.categoryRows.first()).toBeVisible();
  });

});

// ─── REGRESSION TESTS (future) ────────────────────────────────────────────────
//
// These scenarios are notable failures but the page remains partially usable.
// Implement as a separate describe block or spec file.
//
// 1.  Specific metric values are numerically correct
//     — Reason: values change with live data; correct structure is smoke (Test 3).
//
// 2.  Expanding a sub-category loads skill rows
//     — Reason: level-2 expand; test 9 covers this as setup, not as assertion target.
//
// 3.  Search input accepts text (type → input.value updates)
//     — Reason: basic browser input works; debounce/filter logic tested separately.
//
// 4.  Clear search button (×) appears only after text is entered
//     — Reason: conditional render UX detail; absence of clear btn is not blocking.
//
// 5.  Typing 1 character does NOT trigger a search API call
//     — Reason: 2-char minimum debounce; minor UX, tree still usable.
//
// 6.  Typing 2+ characters triggers search after 300 ms
//     — Reason: debounce timing test; search may still respond without strict timing.
//
// 7.  p.co-tree-search-hint appears while search term is active
//     — Reason: cosmetic hint; its absence does not impair search functionality.
//
// 8.  Clearing search restores full category tree
//     — Reason: QoL; user can reload page as workaround.
//
// 9.  Back button returns to "Organisation Capability Summary" default state
//     — Reason: back nav; user can click another skill as workaround if broken.
//
// 10. Scroll position in left pane preserved when navigating away and back
//     — Reason: Zustand scroll restoration; pure UX, zero functional impact.
//
// 11. Zustand cache prevents a second API call on return navigation
//     — Reason: performance/architecture concern; page still loads correctly without.
//
// 12. div.co-tree-empty appears when DB has no skills
//     — Reason: edge case requiring specific DB state; not reproducible in normal runs.
