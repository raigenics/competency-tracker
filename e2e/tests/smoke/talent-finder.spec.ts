// Module:  talent-finder.spec.ts
// Purpose: Smoke tests for Talent Finder module (AdvancedQueryPage)
// Part of: CompetencyIQ E2E Automation Suite
//
// ⚠️  NOTE: TalentFinderPage.jsx (/talent-finder placeholder) is DEAD CODE.
//     The real /talent-finder route renders AdvancedQueryPage (fully implemented).
//     These tests run against the implemented AdvancedQueryPage at /talent-finder.
//
// ⚠️  TITLE NOTE:
//     The sidebar link says "Talent Finder".
//     The mounted component renders h1.page-title = "Capability Finder".
//     Test 2 asserts the actual rendered text, not the sidebar label.
//
// Source files read before writing selectors:
//   frontend/src/pages/AdvancedQuery/AdvancedQueryPage.jsx         (207 lines)
//   frontend/src/pages/AdvancedQuery/components/QueryBuilderPanel.jsx (288 lines)
//   frontend/src/components/PageHeader.jsx                          (44 lines)
//   frontend/src/components/Sidebar.jsx                             (208 lines)

import { test, expect } from '@playwright/test';
import TalentFinderPage from '../../pages/talentFinder.page';

test.describe('Talent Finder - Smoke Tests @smoke @insights', () => {

  // ── TEST 1 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: If the page root or grid doesn't render the entire page is broken.
  // This confirms the /talent-finder route resolves to AdvancedQueryPage (not a
  // 404 or the dead TalentFinderPage placeholder) and that both layout cards are
  // present on arrival.
  test('loads capability finder at /talent-finder with both layout cards', async ({ page }) => {
    const tf = new TalentFinderPage(page);
    await tf.navigate();
    await tf.waitForFiltersReady();

    // Page root
    await expect(tf.pageRoot).toBeVisible();

    // Two-column grid
    await expect(tf.cfGrid).toBeVisible();

    // Both pane cards present (aria-label set in AdvancedQueryPage.jsx)
    await expect(tf.filtersCard).toBeVisible();
    await expect(tf.resultsCard).toBeVisible();

    // URL confirmed
    await expect(page).toHaveURL(/\/talent-finder/);
  });

  // ── TEST 2 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The h1 text confirms the correct component mounted.
  // The actual title is "Capability Finder" (PageHeader prop in AdvancedQueryPage.jsx
  // line ~133). If a different component mounts, this assertion fails and signals
  // a routing regression. The sidebar label ("Talent Finder") is DIFFERENT — see note.
  test('renders page title "Capability Finder" (not "Talent Finder")', async ({ page }) => {
    const tf = new TalentFinderPage(page);
    await tf.navigate();
    await tf.waitForFiltersReady();

    // h1.page-title rendered by PageHeader with title="Capability Finder"
    await expect(tf.pageTitle).toContainText('Capability Finder');

    // Subtitle confirms it's the Capability Finder, not any other page
    await expect(tf.pageSubtitle).toContainText('Select skills and optional filters');
  });

  // ── TEST 3 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The sidebar link is the primary navigation entry point.
  // A broken <a href="/talent-finder"> means users can never reach the page organically.
  // Sidebar.jsx line 113-120: NavLink to="/talent-finder" with span "Talent Finder".
  test('Talent Finder sidebar link navigates to the capability finder page', async ({ page }) => {
    // Start on dashboard (confirmed working in earlier smoke runs)
    await page.goto('/dashboard');
    await page.waitForSelector('.dashboard-page', { state: 'visible', timeout: 15_000 });

    // NavLink renders as <a href="/talent-finder"> (Sidebar.jsx line 113-120)
    const sidebarLink = page.locator('a[href="/talent-finder"]');
    await expect(sidebarLink).toBeVisible();
    await sidebarLink.click();

    await expect(page).toHaveURL(/\/talent-finder/);

    // Confirm AdvancedQueryPage mounted (not the dead TalentFinderPage stub)
    await expect(page.locator('h1.page-title')).toContainText('Capability Finder');
  });

  // ── TEST 4 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The "Find Talent By" heading and filter fields are the core UI
  // for all search operations. If the filters card fails to render (API load
  // fails, component crash), users have no way to initiate a search.
  test('filters card shows "Find Talent By" heading and key filter fields', async ({ page }) => {
    const tf = new TalentFinderPage(page);
    await tf.navigate();
    await tf.waitForFiltersReady();

    // Section heading
    await expect(tf.filtersHeading).toContainText('Find Talent By');

    // "Skills to Match" label — first and most important filter field
    await expect(tf.skillsLabel).toBeVisible();

    // Sub-Segment, Team, Role labels (cf-label in QueryBuilderPanel.jsx lines ~168-190)
    await expect(page.locator('.cf-label', { hasText: 'Sub-Segment' })).toBeVisible();
    await expect(page.locator('.cf-label', { hasText: 'Team' })).toBeVisible();
    await expect(page.locator('.cf-label', { hasText: 'Role' })).toBeVisible();
  });

  // ── TEST 5 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The match mode toggle is required for all searches — it governs
  // whether employees must have ALL or ANY of the selected skills. Both buttons
  // must render and "All skills" must be active by default.
  test('match mode segmented control renders with "All skills" active by default', async ({ page }) => {
    const tf = new TalentFinderPage(page);
    await tf.navigate();
    await tf.waitForFiltersReady();

    // Both match mode buttons visible (cf-segmented in QueryBuilderPanel.jsx)
    await expect(tf.matchModeAllBtn).toBeVisible();
    await expect(tf.matchModeAnyBtn).toBeVisible();

    // "All skills" is the default active state (matchMode initial = 'all')
    expect(await tf.isMatchModeAll()).toBe(true);
  });

  // ── TEST 6 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The Search button being disabled when no skills are selected is
  // the primary UX guard: prevents empty API calls and guides users to the
  // required input. If this is absent or always-enabled the page misleads users.
  test('Search button is visible and disabled before any skill is selected', async ({ page }) => {
    const tf = new TalentFinderPage(page);
    await tf.navigate();
    await tf.waitForFiltersReady();

    // Search button rendered (button.cf-btn.primary from QueryBuilderPanel.jsx line ~200)
    await expect(tf.searchBtn).toBeVisible();
    await expect(tf.searchBtn).toContainText('Search');

    // Disabled — line ~205: disabled={isLoading || !query.skills || query.skills.length === 0}
    expect(await tf.isSearchDisabled()).toBe(true);

    // Reset button present alongside
    await expect(tf.resetBtn).toBeVisible();
    await expect(tf.resetBtn).toContainText('Reset');
  });

  // ── TEST 7 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The results card must always be visible on page load with the
  // count showing "Matching Talent (0)". If it is absent or the count element
  // is missing, the right half of the two-column layout is broken.
  test('results card shows "Matching Talent (0)" count on load', async ({ page }) => {
    const tf = new TalentFinderPage(page);
    await tf.navigate();
    await tf.waitForFiltersReady();

    // Results card present
    await expect(tf.resultsCard).toBeVisible();

    // Topbar with count visible (cf-topbar + cf-count from AdvancedQueryPage.jsx line ~149)
    await expect(tf.resultsTopbar).toBeVisible();
    await expect(tf.resultsCount).toContainText('Matching Talent');

    // No search performed yet — count must be 0
    const count = await tf.getMatchingTalentCount();
    expect(count).toBe(0);
  });

  // ── TEST 8 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: "No search performed" is the default right-panel state every
  // user sees on arrival. If this element is absent, the right card is blank on
  // load — a broken first impression that signals a component render failure.
  // Source: AdvancedQueryPage.jsx ~line 162: !hasSearched && queryResults.length===0
  test('initial empty state shows "No search performed" message', async ({ page }) => {
    const tf = new TalentFinderPage(page);
    await tf.navigate();
    await tf.waitForFiltersReady();

    // cf-empty div present in right card
    await expect(tf.emptyState).toBeVisible();

    // Title: "No search performed"
    await expect(tf.emptyStateTitle).toContainText('No search performed');

    // Subtext guides user to next action
    await expect(tf.emptyStateSub).toContainText('Select skills and click Search');
  });

  // ── TEST 9 ───────────────────────────────────────────────────────────────────────────────
  // SMOKE: The full search journey is the core purpose of this page.
  // If selecting a skill, clicking Search, and receiving results is broken,
  // the page is non-functional for all users regardless of layout rendering.
  // Promoted from regression items 1+2. Seeded skill: "JavaScript"
  // (skill_id 9070, mapped to Alice, Carol, Emma — 3 guaranteed results).
  test('should return results when searching for a seeded skill', async ({ page }) => {
    const tf = new TalentFinderPage(page);

    // Step 1: Fresh page load
    await tf.navigate();
    await tf.waitForFiltersReady();

    // Step 2: Assert baseline empty state before anything
    expect(await tf.isSearchDisabled()).toBe(true);
    expect(await tf.getMatchingTalentCount()).toBe(0);
    await expect(tf.emptyState).toBeVisible();
    await expect(tf.emptyStateTitle).toContainText('No search performed');

    // Step 3: Select skill "JavaScript" via EnhancedSkillSelector
    // Pattern A: click input → type to filter → wait for API option → click it → wait for chip
    await tf.selectSkill('JavaScript');

    // Step 4: Confirm chip is visible — proves React query.skills array was updated
    await expect(tf.selectedSkillChip.filter({ hasText: 'JavaScript' }).first()).toBeVisible();

    // Step 5: Search button must now be enabled (skills.length === 1)
    expect(await tf.isSearchDisabled()).toBe(false);

    // Step 6: Click Search
    await tf.searchBtn.click();

    // Step 7: Wait for result rows to appear (API round-trip complete)
    await tf.waitForResults(10_000);

    // Step 8: Count must be greater than zero
    const count = await tf.getMatchingTalentCount();
    expect(count).toBeGreaterThan(0);

    // Step 9: At least one result row is visible
    await expect(tf.resultsRow.first()).toBeVisible();

    // Step 10: Empty state is gone
    await expect(tf.emptyState).not.toBeVisible();
  });

});

// ─── REGRESSION TESTS (future) ────────────────────────────────────────────────
//
// This page is fully implemented. The following scenarios are notable failures
// but the page remains at least partially usable without them.
//
// Note: Items 1+2 promoted to smoke (Test 9) — seeded data confirmed.
//
// 3.  "No matching employees found" after zero-result search
//     — Reason: requires specific query that returns no matches.
//
// 4.  Match mode toggle: clicking "Any skill" adds class active to that button
//     — Reason: UI state; doesn't break search functionality.
//
// 5.  Reset clears all filter selections and empties results
//     — Reason: QoL; can reload page as workaround.
//
// 6.  Sub-segment dropdown populates with API data
//     — Reason: dropdown content; page still usable with empty dropdown.
//
// 7.  Team dropdown disabled when Sub-Segment = "All Sub-Segments"
//     — Reason: UX guard detail; TeamComboBox disabled prop verified separately.
//
// 8.  Proficiency select has correct options (Any, 1+, 2+, 3+, 4+, 5 Expert)
//     — Reason: select options are static in JSX; no API dependency.
//
// 9.  Export button disabled when queryResults.length === 0
//     — Reason: export UX detail; disabled prop on TalentExportMenu.
//
// 10. Results table shows employee name, role, team, sub-segment columns
//     — Reason: requires successful search; QueryResultsTable regression scope.
//
// 11. Multi-skill search with match mode "All skills" narrows results
//     — Reason: API behaviour test; requires DB state with multi-skilled employees.
//
// 12. "Searching employees..." loading text visible during API call
//     — Reason: timing-sensitive; LoadingState renders briefly then replaces.
