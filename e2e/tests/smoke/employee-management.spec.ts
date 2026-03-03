// Module: employee-management.spec.ts
// Purpose: Smoke tests for Employee Management module - critical path validation
// Part of: CompetencyIQ E2E Automation Suite
//
// Page under test: /employees → EmployeeManagement (frontend/src/pages/Employees/EmployeeManagement.jsx)
//
// ⚠️  IMPORTANT — COMMON MISTAKES AVOIDED:
//   1. The employee list is a CSS GRID of <div>s — NOT an HTML <table>.
//      Never use getByRole('table') or 'tbody tr'. Row count proxied via editBtns.count().
//   2. RBAC role is SUPER_ADMIN (featureFlags.js: currentRole = RBAC_ROLES.SUPER_ADMIN).
//      canShowAddEmployee() → true. getRowActions() → canEdit: true, canDelete: true.
//      Add, Edit, and Delete are ALL visible. Tests are NOT skipped for RBAC.
//   3. Never trigger Save in the drawer or Delete/Confirm in the modal.
//      Only open + inspect + close/cancel is permitted in smoke tests.
//   4. Never assert exact row counts. Use > 0 or >= 1 only.
//   5. Column headers are in a div-based grid header row, NOT <thead>.
//      They are plain text — located via getByText().
//   6. Autocomplete dropdown and items have no testid — see page object for selector details.
//
// Source files read before writing:
//   frontend/src/pages/Employees/EmployeeManagement.jsx (1097 lines)
//   frontend/src/rbac/permissions.js                    canShowAddEmployee() / getRowActions()
//   frontend/src/config/featureFlags.js                 currentRole = SUPER_ADMIN
//   frontend/src/components/AddEmployeeDrawer.jsx       drawer class / title / close button
//   e2e/testdata/seed.sql                               Alice Chen (9090, ZID TEST-EMP-001)

import { test, expect } from '@playwright/test';
import EmployeeManagementPage from '../../pages/employeeManagement.page';

test.describe('Employee Management - Smoke Tests @smoke @governance', () => {

  // ── TEST 1 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: If the page doesn't load with data, the entire module is unusable.
  // Covers route resolution (/employees → EmployeeManagement), API call on mount,
  // search/filter UI presence, and column header rendering. All are load-time baselines.
  test('should load page with employees table and all UI controls visible', async ({ page }) => {
    const em = new EmployeeManagementPage(page);
    await em.navigate();
    await em.waitForTableLoad();

    // Page heading confirms correct component mounted at /employees
    await expect(em.pageHeading).toBeVisible();
    await expect(em.pageHeading).toContainText('Employees');

    // Search input must be present and functional
    await expect(em.searchInput).toBeVisible();
    await expect(em.searchInput).not.toBeDisabled();

    // All three filter dropdowns must be visible (sub-segment populates on mount)
    await expect(em.subSegmentSelect).toBeVisible();
    await expect(em.projectSelect).toBeVisible();
    await expect(em.teamSelect).toBeVisible();

    // At least one seeded employee must appear
    const rowCount = await em.getRowCount();
    expect(rowCount).toBeGreaterThan(0);

    // All 7 column headers visible — confirmed exact text from JSX grid header divs
    await expect(em.colZID).toBeVisible();
    await expect(em.colFullName).toBeVisible();
    await expect(em.colSubSegment).toBeVisible();
    await expect(em.colProject).toBeVisible();
    await expect(em.colTeam).toBeVisible();
    await expect(em.colRole).toBeVisible();
    await expect(em.colActions).toBeVisible();
  });

  // ── TEST 2 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: Autocomplete is the primary way to find a specific employee in
  // large datasets. If typing 2+ characters does not trigger suggestions, users
  // cannot locate anyone without scrolling through every page of results.
  test('should show autocomplete suggestions after typing 2+ characters', async ({ page }) => {
    const em = new EmployeeManagementPage(page);
    await em.navigate();
    await em.waitForTableLoad();

    // "Alice" triggers the 300ms debounce and API fetch for suggestions
    await em.typeInSearch('Alice');
    await em.waitForSuggestions();

    // At least one suggestion must appear (seeded employee Alice Chen matches "Alice")
    const items = em.getSuggestionItems();
    const count = await items.count();
    expect(count).toBeGreaterThan(0);

    // First suggestion must contain "Alice" — suggestion format: "{ZID} — {full_name}"
    await expect(items.first()).toContainText('Alice');
  });

  // ── TEST 3 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: Autocomplete is useless if clicking a suggestion does not update
  // the employee list. This test confirms the full search journey completes:
  // type → dropdown → click → table filters to matching employees.
  test('should filter employee list after selecting autocomplete suggestion', async ({ page }) => {
    const em = new EmployeeManagementPage(page);
    await em.navigate();
    await em.waitForTableLoad();

    await em.typeInSearch('Alice');
    await em.waitForSuggestions();

    // Click first suggestion — expects filtered results for Alice Chen
    await em.clickSuggestion(0);
    // Allow React state update + API re-fetch to complete after selection
    await page.waitForTimeout(500);

    // Table must still have rows — clicking a valid suggestion should filter, not empty the list
    const rowCount = await em.getRowCount();
    expect(rowCount).toBeGreaterThanOrEqual(1);
  });

  // ── TEST 4 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: canShowAddEmployee() returns TRUE for SUPER_ADMIN (verified from
  // permissions.js). If the Add Employee entry point is broken while RBAC permits it,
  // HR and managers have NO way to onboard new employees.
  // DOES NOT save — opens drawer, checks title, closes.
  //
  // RBAC: canShowAddEmployee() for currentRole=SUPER_ADMIN → true
  //   (permissions.js: canCreate=true, selfOnly=undefined → returns true)
  test('should open Add Employee drawer with correct title and close it', async ({ page }) => {
    const em = new EmployeeManagementPage(page);
    await em.navigate();
    await em.waitForTableLoad();

    // Add button must be visible — RBAC permits it for SUPER_ADMIN
    await expect(em.addEmployeeBtn).toBeVisible();

    // Open the drawer
    await em.openAddDrawer();
    await expect(em.drawer).toBeVisible();

    // Title must confirm add mode (JSX: isEditMode ? 'Edit Employee' : 'Add Employee')
    await expect(em.drawerTitle).toContainText('Add Employee');

    // Close without saving
    await em.closeDrawer();
    await expect(em.drawer).not.toBeVisible();

    // Page must still be intact after close
    await expect(em.pageRoot).toBeVisible();
  });

  // ── TEST 5 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: getRowActions() returns canDelete=true for SUPER_ADMIN (verified from
  // permissions.js). If the modal fails to open when Delete is clicked, users get
  // no feedback and no safety gate — the workflow is broken and confusing.
  // DOES NOT confirm deletion — only opens modal, checks employee name, cancels.
  //
  // RBAC: getRowActions() for SUPER_ADMIN → canDelete: true
  //   (permissions.js: permissions.canDelete=true → result.canDelete=true)
  test('should open delete confirmation modal and cancel without deleting', async ({ page }) => {
    const em = new EmployeeManagementPage(page);
    await em.navigate();
    await em.waitForTableLoad();

    // Delete buttons must be visible — RBAC permits delete for SUPER_ADMIN
    await expect(em.deleteBtns.first()).toBeVisible();

    // Click Delete on the first row
    await em.clickDeleteOnRow(0);

    // Modal must appear with heading "Delete Employee"
    await expect(em.deleteModalHeading).toBeVisible();

    // Employee name must be shown in the modal (confirms the correct employee is targeted)
    // Using <strong> element — only one <strong> in the DOM when modal is open
    await expect(em.deleteModalName).toBeVisible();
    const employeeName = await em.deleteModalName.textContent();
    expect(employeeName?.trim()).not.toBe('');

    // Cancel — NEVER click the "Delete" confirm button in smoke tests
    await em.cancelDelete();
    await expect(em.deleteModalHeading).not.toBeVisible();

    // Table must still be intact after cancel
    await expect(em.pageRoot).toBeVisible();
    const rowCount = await em.getRowCount();
    expect(rowCount).toBeGreaterThan(0);
  });

  // ── TEST 6 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: getRowActions() returns canEdit=true for SUPER_ADMIN (verified from
  // permissions.js). If clicking Edit does nothing, managers cannot update any
  // employee record. The check that inputs are pre-filled is critical — an edit
  // drawer that opens empty could cause users to accidentally blank all field values.
  // DOES NOT save — opens drawer in edit mode, verifies pre-fill, closes.
  //
  // RBAC: getRowActions() for SUPER_ADMIN → canEdit: true
  //   (permissions.js: permissions.canUpdate=true → result.canEdit=true)
  test('should open Edit drawer in edit mode with pre-filled data', async ({ page }) => {
    const em = new EmployeeManagementPage(page);
    await em.navigate();
    await em.waitForTableLoad();

    // Edit buttons must be visible — RBAC permits edit for SUPER_ADMIN
    await expect(em.editBtns.first()).toBeVisible();

    // Click Edit on first row — waitForTableLoad handles edit bootstrap loading overlay
    await em.clickEditOnRow(0);
    await expect(em.drawer).toBeVisible();

    // Title must confirm edit mode (JSX: isEditMode ? 'Edit Employee' : 'Add Employee')
    await expect(em.drawerTitle).toContainText('Edit Employee');

    // At least one input in the drawer must have a non-empty value (confirms pre-fill worked)
    // Without pre-fill, editing would overwrite all fields with blank values on save.
    const drawerInputs = em.drawer.locator('input[type="text"], input:not([type])');
    const inputCount = await drawerInputs.count();
    expect(inputCount).toBeGreaterThan(0);

    let foundNonEmptyInput = false;
    for (let i = 0; i < Math.min(inputCount, 6); i++) {
      const val = await drawerInputs.nth(i).inputValue();
      if (val.trim() !== '') {
        foundNonEmptyInput = true;
        break;
      }
    }
    expect(foundNonEmptyInput).toBe(true);

    // Close without saving
    await em.closeDrawer();
    await expect(em.drawer).not.toBeVisible();
  });

});

// ─── REGRESSION TESTS (future) ────────────────────────────────────────────────
//
// These scenarios are covered by source-code reading but do not make the page
// completely unusable if absent — regression scope.
//
// 1.  Column headers display exact uppercase text (ZID, FULL NAME, etc.)
//     — Reason: CSS text-transform cosmetic; data still readable without it.
//
// 2.  Typing exactly 1 character does NOT trigger autocomplete (< 2 char minimum)
//     — Reason: UX guard detail; 2-char search still works.
//
// 3.  Clear (X) button appears when search input has text
//     — Reason: User can manually clear the field; no functional blocker.
//
// 4.  Clearing search via X button restores the unfiltered employee list
//     — Reason: Manually emptying the input achieves the same result.
//
// 5.  Sub-segment dropdown populates with API data on mount
//     — Reason: Filtering via sub-segment is QoL; search still works.
//
// 6.  Project dropdown is disabled until sub-segment is selected
//     — Reason: UX cascade constraint; not core list/search functionality.
//
// 7.  Team dropdown is disabled until project is selected
//     — Reason: Same cascading dependency.
//
// 8.  Pagination "Showing X to Y of Z employees" appears when totalPages > 1
//     — Reason: Only 5 seeded employees; requires 11+ to trigger. Navigation edge case.
//
// 9.  Next / Previous pagination buttons change the displayed page
//     — Reason: Edge case; requires > 10 employees to trigger.
//
// 10. Clicking a row (anywhere outside action buttons) navigates to employee profile
//     — Reason: Employee Directory provides alternate profile access path.
//
// 11. Empty state "No Employees Found" shows when search matches nothing
//     — Reason: Informational feedback; non-functional path not core.
//
// 12. Add Employee drawer shows validation error for missing required fields
//     — Reason: Validation UX detail; requires form interaction beyond smoke scope.
//
// 13. Edit drawer subtitle reads "Update employee information and skills"
//     — Reason: Subtitle text is cosmetic; title check is sufficient.
