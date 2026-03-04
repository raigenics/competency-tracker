// Module:  employee-directory.spec.ts
// Purpose: Smoke tests for Employee Directory module
// Part of: CompetencyIQ E2E Automation Suite
//
// Page under test: /profile → EmployeeDirectory (frontend/src/pages/Profile/EmployeeDirectory.jsx)
//
// ⚠️  IMPORTANT — COMMON MISTAKES AVOIDED:
//   1. Search button (btn-primary) has NO disabled prop — ALWAYS ENABLED.
//      Never assert searchBtn is disabled. Opposite of Talent Finder.
//   2. Two states share .empty-state class. Distinguish by h2 text only.
//   3. Export button has BOTH disabled attr AND "disabled" CSS class on load.
//   4. Min 2 chars + 300ms debounce before autocomplete fires.
//   5. Profile name uses toContainText (partial) — not toHaveText.
//
// Source files read before writing selectors:
//   frontend/src/pages/Profile/EmployeeDirectory.jsx  (817 lines)
//   frontend/src/app/routes.jsx                        confirmed route: /profile
//   e2e/testdata/seed.sql                              Alice's full_name: 'Alice Chen'

import { test, expect } from '@playwright/test';
import EmployeeDirectoryPage from '../../pages/employeeDirectory.page';

test.describe('Employee Directory - Smoke Tests @smoke @people', () => {

  // ── TEST 1 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: Layout shell broken = nothing usable. Confirms route /profile
  // maps to EmployeeDirectory, the topbar renders, the search input is present
  // and enabled, the export button is visibly disabled, and the default empty
  // state appears — the complete correct first-render baseline.
  test('should show topbar with title, search, and default empty state on load', async ({ page }) => {
    const ed = new EmployeeDirectoryPage(page);
    await ed.navigate();
    await ed.waitForLoad();

    // Page title confirms correct component mounted
    await expect(ed.pageTitle).toContainText('Employee Profile');

    // Search input must be present and enabled (no load gate on this input)
    await expect(ed.searchInput).toBeVisible();
    await expect(ed.searchInput).not.toBeDisabled();

    // Search button ALWAYS enabled — no disabled prop in JSX
    await expect(ed.searchBtn).toBeVisible();
    await expect(ed.searchBtn).not.toBeDisabled();

    // Export button DISABLED on load — both CSS class and attribute
    await expect(ed.exportBtn).toBeVisible();
    await expect(ed.exportBtn).toBeDisabled();
    await expect(ed.exportBtn).toHaveClass(/disabled/);

    // Default empty state: "No employee selected"
    expect(await ed.isDefaultEmptyState()).toBe(true);
    await expect(ed.emptyState).toBeVisible();
    await expect(ed.emptyStateHeading).toContainText('No employee selected');
  });

  // ── TEST 2 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: The autocomplete is the only way to navigate to an employee.
  // If typing 2+ characters does not generate a dropdown, the page is
  // completely unusable — no employee can ever be loaded.
  test('should show autocomplete dropdown after typing 2+ characters', async ({ page }) => {
    const ed = new EmployeeDirectoryPage(page);
    await ed.navigate();
    await ed.waitForLoad();

    // Type 2 characters — minimum required to trigger API fetch + debounce
    await ed.typeInSearch('Al');
    await ed.waitForDropdown();

    // At least one item must appear (seeded employees include Alice Chen)
    await expect(ed.dropdownItems.first()).toBeVisible();
    const count = await ed.dropdownItems.count();
    expect(count).toBeGreaterThan(0);
  });

  // ── TEST 3 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: Searching for an employee and loading their profile is the
  // entire function of this page. If autocomplete, selection, or profile
  // load is broken, the page has zero value for any user.
  // Uses seeded employee Alice Chen (employee_id 9090, 2 skills seeded).
  test('should load employee profile after searching and selecting from autocomplete', async ({ page }) => {
    const ed = new EmployeeDirectoryPage(page);

    // Step 1: Fresh page load
    await ed.navigate();
    await ed.waitForLoad();

    // Step 2: Confirm baseline — no profile loaded yet
    expect(await ed.isDefaultEmptyState()).toBe(true);

    // Step 3: Type "Alice" — triggers 300ms debounce, API fetches suggestions
    await ed.typeInSearch('Alice');

    // Step 4: Dropdown appears with Alice's name
    await ed.waitForDropdown();
    await expect(ed.dropdownItems.first()).toBeVisible();
    const count = await ed.dropdownItems.count();
    expect(count).toBeGreaterThan(0);
    await expect(ed.empNameInDropdown.first()).toContainText('Alice');

    // Step 5: Click the first suggestion (Alice Chen)
    await ed.selectSuggestion(0);

    // Step 6: Wait for profile to load (profileHeader visible = data rendered)
    await ed.waitForProfileLoad();

    // Step 7: Profile header visible; name contains "Alice"
    await expect(ed.profileHeader).toBeVisible();
    await expect(ed.profileName).toContainText('Alice');

    // Step 8: ZID badge must be visible with "ZID:" prefix
    await expect(ed.zidBadge).toBeVisible();
    await expect(ed.zidBadge).toContainText('ZID:');

    // Step 9: Exactly 4 org meta chips (Sub-Seg, Project, Team, Role)
    await expect(ed.metaChips).toHaveCount(4);

    // Step 10: Total Skills count > 0 (Alice has 2 seeded skills)
    const skillCount = await ed.getTotalSkillsCount();
    expect(skillCount).toBeGreaterThan(0);

    // Step 11: Core Expertise section renders with at least one card
    await expect(ed.expertiseGrid).toBeVisible();
    const cardCount = await ed.expertiseCards.count();
    expect(cardCount).toBeGreaterThan(0);

    // Step 12: All Skills table visible with at least one row
    await expect(ed.skillsTable).toBeVisible();
    const rowCount = await ed.getSkillsTableRowCount();
    expect(rowCount).toBeGreaterThan(0);

    // Step 13: Export button is NOW ENABLED (hasSelectedEmployee === true)
    await expect(ed.exportBtn).not.toBeDisabled();
    await expect(ed.exportBtn).not.toHaveClass(/disabled/);
  });

  // ── TEST 4 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: "No matching employee found" is the state users see when their
  // search returns nothing. If this silently disappears and the page stays on
  // the default empty state, users have no feedback that their query failed.
  // They will believe the page is hanging or broken.
  test('should show no-match state when search returns no employee', async ({ page }) => {
    const ed = new EmployeeDirectoryPage(page);
    await ed.navigate();
    await ed.waitForLoad();

    // Type an unknown term — guaranteed no match in seeded data
    await ed.typeInSearch('ZZZUnknownEmployee999');
    // Wait for debounce + any API call to settle
    await page.waitForTimeout(400);

    // Click Search — handleSearchSubmit sets showNoMatchState = true
    // when no match is found and no suggestion is available
    await ed.searchBtn.click();

    // No-match state must appear
    expect(await ed.isNoMatchState()).toBe(true);
    await expect(ed.emptyState).toBeVisible();
    await expect(ed.emptyStateHeading).toContainText('No matching employee found');
  });

});

// ─── REGRESSION TESTS (future) ────────────────────────────────────────────────
//
// These scenarios are notable but the page remains partially usable without them.
//
// 1.  Typing 1 character does NOT trigger autocomplete (< 2 char minimum)
//     — Reason: UX guard detail; page still works with mouse clicks.
//
// 2.  Pressing Enter auto-selects the first suggestion
//     — Reason: keyboard shortcut; mouse click is an equivalent workaround.
//
// 3.  Skills table has exactly 6 proficiency filter buttons
//     — Reason: filter count is cosmetic; full table still accessible without it.
//
// 4.  Clicking a filter button narrows the skills table rows
//     — Reason: QoL filtering; full unfiltered list is still visible.
//
// 5.  Skills inline search input filters rows by term
//     — Reason: search-within-results is QoL; full table visible without it.
//
// 6.  Error state "Failed to load profile" appears on API failure
//     — Reason: requires mocked API failure; not reproducible in normal runs.
//
// 7.  Stale row class applied to skills not used in 12+ months
//     — Reason: visual signal; does not affect data accuracy.
//
// 8.  Highlighted class applied to keyboard-navigated dropdown item
//     — Reason: UX detail for accessibility; click interaction unaffected.
//
// 9.  Export button triggers dropdown with Excel + PDF options
//     — Reason: export UX; unrelated to profile read functionality.
//
// 10. Legend row visible below skills table
//     — Reason: informational; absence does not break data display.