// Module: bulk-import.spec.ts
// Purpose: Smoke tests for Bulk Import module — Module 9 of 9 (final module)
// Part of: CompetencyIQ E2E Automation Suite
//
// Page under test: /system/import → BulkImportPage (frontend/src/pages/BulkImport/BulkImportPage.jsx)
//
// ⚠️  CRITICAL RULES — DO NOT VIOLATE:
//
//   1. NEVER CLICK START IMPORT.
//      startImportBtn calls bulkImportApi.importExcel() — a real, irreversible API call
//      that creates/updates employees and skills in the database.
//      Smoke tests stop at State 2 (file selected). Start Import is never invoked.
//
//   2. FILE INPUT IS HIDDEN.
//      input[type="file"] has className="hidden". Use setInputFiles() via attachFile().
//      Never: fileInput.click(). Always: attachFile(fixturePath).
//
//   3. PAGE TITLE CONTAINS EN-DASH (–), NOT A HYPHEN (-).
//      "Bulk Import – Employee & Skill Data"
//      The character is U+2013 (en dash), copied directly from JSX line 412.
//
//   4. SMOKE SCOPE = States 1 and 2 ONLY.
//      State 1: Idle — no file, drop zone shows idle text, no Start Import button in DOM.
//      State 2: File selected — ready text visible, Remove/Start Import visible and enabled.
//      States 3-6 (Import, Error, Success, With-Errors) require real API calls — OUT OF SCOPE.
//
// FIXTURE STRATEGY:
//   No .xlsx fixture file exists in e2e/fixtures/ (confirmed at time of writing).
//   The beforeAll generates test-import.xlsx using SheetJS (xlsx package is in devDependencies).
//   The file only needs to pass: file.name.endsWith('.xlsx') AND be a valid Excel binary.
//   SheetJS writes a properly signed XLSX binary with the PK ZIP magic bytes.

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import * as XLSX from 'xlsx';
import BulkImportPage from '../../pages/bulkImport.page';

// Absolute path to the fixture .xlsx file
const FIXTURE_PATH = path.resolve(__dirname, '..', '..', 'fixtures', 'test-import.xlsx');

test.describe('Bulk Import - Smoke Tests @smoke @import', () => {

  // ── Create the .xlsx fixture once before all tests ───────────────────────
  test.beforeAll(async () => {
    // Ensure the fixtures directory exists
    const fixturesDir = path.dirname(FIXTURE_PATH);
    if (!fs.existsSync(fixturesDir)) {
      fs.mkdirSync(fixturesDir, { recursive: true });
    }

    // Only generate if the file does not already exist
    if (!fs.existsSync(FIXTURE_PATH)) {
      // Create a minimal valid XLSX with one "Employee" sheet
      // Columns match the BulkImportPage expected format from the failed rows table:
      // Segment, ZID, Employee Name, Skill, Category
      // This content is not validated by smoke tests — we only verify the UI state change.
      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.aoa_to_sheet([
        ['Segment',    'ZID',          'Employee Name', 'Skill',        'Category'],
        ['Test Seg',   'TEST-EMP-001', 'Alice Chen',    'JavaScript',   'Technical'],
      ]);
      XLSX.utils.book_append_sheet(wb, ws, 'Employee');
      XLSX.writeFile(wb, FIXTURE_PATH);
      console.log(`[bulk-import] Fixture created: ${FIXTURE_PATH}`);
    }
  });

  // ── TEST 1 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: If the upload zone is missing or the heading is broken, no bulk
  // import is possible at all. This test confirms the route is correctly mounted,
  // the page header matches the intended module (including the en-dash), and all
  // three always-visible elements (heading, drop zone, Download Template) are present.
  // If any of these are absent, the entire module is unreachable or unrecognizable.
  test('should load in idle state with heading, subtitle, and upload zone visible', async ({ page }) => {
    const bi = new BulkImportPage(page);
    await bi.navigate();
    await bi.waitForLoad();

    // Page title — EN-DASH (–) copied from JSX, NOT a hyphen (-)
    await expect(bi.pageHeading).toBeVisible();
    await expect(bi.pageHeading).toContainText('Bulk Import – Employee & Skill Data');

    // Subtitle confirms correct component is mounted
    await expect(bi.pageSubtitle).toBeVisible();

    // Step 1 block confirms template guidance section is present
    await expect(bi.step1Block).toBeVisible();
    await expect(bi.downloadTemplateBtn).toBeVisible();

    // Drop zone must show idle-state text (exact string from JSX)
    await expect(bi.dropZoneIdleText).toBeVisible();
    await expect(bi.dropZoneIdleText).toHaveText('Drag & drop your Excel file here, or click to browse');

    // Start Import must NOT be in the DOM before any file is attached
    // (it is wrapped in {selectedFile && (...)} — conditional render, not just hidden)
    expect(await bi.isInIdleState()).toBe(true);
    await expect(bi.startImportBtn).toHaveCount(0);
  });

  // ── TEST 2 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: setInputFiles() triggering React's handleFileSelect is the ONLY
  // way to enter the import flow. If attaching a file does not update the UI —
  // showing the filename, size, Remove button, and Start Import — users have no
  // indication the file was accepted and cannot proceed with the import.
  // This is the critical integration between Playwright's file attachment API
  // and the React state transition from idle → file-selected.
  test('should transition to file-selected state after attaching a valid .xlsx file', async ({ page }) => {
    const bi = new BulkImportPage(page);
    await bi.navigate();
    await bi.waitForLoad();

    // Confirm idle state before attach
    await expect(bi.dropZoneIdleText).toBeVisible();

    // Attach the fixture — uses setInputFiles(), never click()
    await bi.attachFile(FIXTURE_PATH);

    // Drop zone must now show "File uploaded successfully!" (exact string from JSX)
    await expect(bi.dropZoneReadyText).toBeVisible();
    await expect(bi.dropZoneReadyText).toHaveText('File uploaded successfully!');

    // File info panel must appear with fixture filename and size
    // File name: selectedFile.name is rendered as a text/medium div (no testid)
    await expect(page.getByText('test-import.xlsx')).toBeVisible();
    // File size: formatFileSize(selectedFile.size) — value depends on fixture size
    // Assert the size element is visible (any KB/B value is fine — not an exact value assertion)
    await expect(page.getByText(/\d+(\.\d+)? (B|KB|MB)$/)).toBeVisible();

    // Remove button must be visible
    await expect(bi.removeFileBtn).toBeVisible();

    // Start Import button must be visible and enabled
    // ⚠️ DO NOT CLICK. This is the boundary of smoke scope.
    await expect(bi.startImportBtn).toBeVisible();
    await expect(bi.startImportBtn).not.toBeDisabled();
    await expect(bi.startImportBtn).toHaveText('Start Import');

    // Confirm file-selected state via helper
    expect(await bi.isInFileSelectedState()).toBe(true);
    expect(await bi.isStartImportEnabled()).toBe(true);
  });

  // ── TEST 3 ────────────────────────────────────────────────────────────────
  // WHY SMOKE: If the Remove button doesn't work, users who attach the wrong file
  // cannot swap it — they would have to reload the page and lose context.
  // This is the ONLY undo operation available before the import starts.
  // It is also the only state transition that goes backwards: file-selected → idle.
  // A broken Remove button makes incorrect file selection unrecoverable in-page.
  test('should return to idle state after clicking Remove', async ({ page }) => {
    const bi = new BulkImportPage(page);
    await bi.navigate();
    await bi.waitForLoad();

    // Attach file to enter file-selected state
    await bi.attachFile(FIXTURE_PATH);

    // Confirm file-selected state before exercising Remove
    await expect(bi.startImportBtn).toBeVisible();
    await expect(bi.dropZoneReadyText).toBeVisible();

    // Click Remove — triggers removeFile() which clears selectedFile state + resets input.value
    await bi.removeFile();

    // Drop zone must return to idle text
    await expect(bi.dropZoneIdleText).toBeVisible();
    await expect(bi.dropZoneIdleText).toHaveText('Drag & drop your Excel file here, or click to browse');

    // File info panel elements must be GONE from DOM (conditional render)
    await expect(bi.startImportBtn).toHaveCount(0);
    await expect(bi.removeFileBtn).toHaveCount(0);
    await expect(page.getByText('test-import.xlsx')).toHaveCount(0);

    // Download Template and Step 1 must still be visible — Remove doesn't break the layout
    await expect(bi.downloadTemplateBtn).toBeVisible();
    await expect(bi.step1Block).toBeVisible();

    // Confirm idle state via helper
    expect(await bi.isInIdleState()).toBe(true);
  });

  // ── OPTIONAL TEST — Download Template dialog ──────────────────────────────
  // WHY SAFE: downloadTemplate() calls alert() only. Zero API calls. No DB writes.
  // WHY SMOKE: The "Download Template" CTA is the first action instructed by the UI.
  // If clicking it does nothing (no dialog), users assume the page is broken before
  // they even attempt file upload.
  test('should show an alert when Download Template is clicked', async ({ page }) => {
    const bi = new BulkImportPage(page);
    await bi.navigate();
    await bi.waitForLoad();

    // Register a one-time dialog handler before clicking (must register first)
    let dialogMessage = '';
    page.once('dialog', async (dialog) => {
      dialogMessage = dialog.message();
      await dialog.accept();
    });

    await bi.downloadTemplateBtn.click();

    // Wait briefly for dialog to fire and be accepted
    await page.waitForTimeout(300);

    // Dialog must have appeared with template-related message
    expect(dialogMessage).toContain('Template download would start here');

    // Page must still be on the bulk import route after dialog dismissed
    expect(page.url()).toContain('/system/import');

    // Page root must still be visible — dialog didn't navigate away
    await expect(bi.pageRoot).toBeVisible();
  });

});

// ─── REGRESSION TESTS (future) ────────────────────────────────────────────────
//
// These scenarios require clicking Start Import or depend on post-import state.
// They MUST NOT run until a proper import mock/isolation strategy is in place.
//
// 1.  Start Import button is disabled while isImporting === true
//     — Reason: Requires clicking Start Import → real API call triggered.
//
// 2.  Import in Progress card shows spinner and warning text during import
//     — Reason: Requires clicking Start Import.
//
// 3.  Progress bar renders with percentage when progressData.percent_complete is set
//     — Reason: Requires backend polling during active import.
//
// 4.  Import Error card shows error message and "← Try Again" button
//     — Reason: Requires a failed API call (mock setup needed).
//
// 5.  "← Try Again" resets back to idle state
//     — Reason: Depends on Import Error state.
//
// 6.  Success result shows "All Records Imported Successfully!" heading + stats
//     — Reason: Requires completed API call.
//
// 7.  "Completed with Errors" heading and failed rows table visible
//     — Reason: Requires completed API call with errors.
//
// 8.  Failed rows table has correct column headers (Sheet, Excel Row, Segment, ...)
//     — Reason: Table only renders when importResults.failed_rows.length > 0.
//
// 9.  "Map Skill" button appears for SKILL_NOT_RESOLVED rows
//     — Reason: Requires specific failed row data from completed import.
//
// 10. "Map Role" button appears for MISSING_ROLE rows
//     — Reason: Same dependency.
//
// 11. "Map Team" button appears for MISSING_TEAM rows
//     — Reason: Same dependency.
//
// 12. "Go to Employees Page →" navigates to /employees
//     — Reason: Only rendered in importResults state.
//
// 13. "Import Another File" resets to idle state
//     — Reason: Only rendered in importResults state.
//
// 14. Drop zone accepts .xls files as well as .xlsx
//     — Reason: accept=".xlsx" on input, but handleFileSelect also allows .xls.
//               Edge case validation — core smoke path uses .xlsx only.
