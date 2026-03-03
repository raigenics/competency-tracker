// Module: bulkImport.page.ts
// Purpose: Page object for Bulk Import module
// Part of: CompetencyIQ E2E Automation Suite
//
// Route: /system/import → BulkImportPage component
// Source: frontend/src/pages/BulkImport/BulkImportPage.jsx
//
// ⚠️  SELECTOR NOTES — READ BEFORE EDITING:
//
//   1. "bulk-import-page" is the ONLY semantic className in BulkImportPage.jsx.
//      Everything else uses Tailwind utility classes (px-6, bg-[#667eea], etc.).
//      NEVER use Tailwind strings as selectors.
//
//   2. FILE INPUT IS HIDDEN:
//      The <input type="file"> has className="hidden".
//      Playwright's click() refuses to target hidden elements.
//      ALWAYS use: fileInput.setInputFiles('path/to/file.xlsx')
//      NEVER use:  fileInput.click()
//
//   3. PAGE TITLE CONTAINS AN EN-DASH (–), NOT A HYPHEN (-):
//      Exact string: "Bulk Import – Employee & Skill Data"
//      The character at position 12 is U+2013 EN DASH.
//      A wrong character makes the heading assertion silently fail.
//
//   4. DROP ZONE TEXTS:
//      Idle:          "Drag & drop your Excel file here, or click to browse"
//      File selected: "File uploaded successfully!"
//      These are distinct text nodes — use for state detection.
//
//   5. STATES 3-6 (Import, Error, Success, With-Errors):
//      All require clicking Start Import → real API mutation.
//      locators for these states are included for completeness
//      but MUST NOT be used in smoke tests.
//
//   6. SMOKE SCOPE = States 1-2 ONLY:
//      State 1: Idle (no file)
//      State 2: File selected (setInputFiles called, Remove/Start Import visible)
//      NEVER click startImportBtn in smoke tests.
//
// SELECTORS USED — CONFIRMED STRATEGIES:
//   pageRoot            → .bulk-import-page  (only semantic class)
//   pageHeading         → getByRole('heading', { name: 'Bulk Import – Employee & Skill Data' })
//   pageSubtitle        → getByText('Upload an Excel file to bulk add...')
//   step1Block          → getByText('Step 1: Download Excel Template')
//   downloadTemplateBtn → getByRole('button', { name: 'Download Template' })
//   dropZone            → text-based existence check via idle/selected text
//   dropZoneIdleText    → getByText('Drag & drop your Excel file here, or click to browse')
//   dropZoneReadyText   → getByText('File uploaded successfully!')
//   fileInput           → locator('input[type="file"]')  — setInputFiles() ONLY
//   removeFileBtn       → getByRole('button', { name: 'Remove' })
//   startImportBtn      → getByRole('button', { name: /Start Import|Importing/i })
//   fileNameDisplay     → stable: unique text node (selectedFile.name) inside the file info panel
//   fileSizeDisplay     → div.text-xs sibling below file name in info panel
//   importProgressH2    → getByRole('heading', { name: 'Import in Progress' })
//   doNotCloseWarning   → getByText(/Do not close this page/i)
//   importErrorH2       → getByRole('heading', { name: 'Import Failed' })
//   tryAgainBtn         → getByRole('button', { name: '← Try Again' })
//   importSuccessH2     → getByText('All Records Imported Successfully!')
//   goToEmployeesBtn    → getByRole('button', { name: /Go to Employees Page/i })
//   importAnotherBtn    → getByRole('button', { name: 'Import Another File' })

import { Page, Locator } from '@playwright/test';
import * as path from 'path';

export default class BulkImportPage {
  readonly page: Page;

  // ── Page structure ─────────────────────────────────────────────────────
  readonly pageRoot: Locator;      // .bulk-import-page

  // PageHeader — title contains EN-DASH (U+2013), not a hyphen
  readonly pageHeading: Locator;   // h1 "Bulk Import – Employee & Skill Data"
  readonly pageSubtitle: Locator;  // subtitle paragraph

  // ── Step 1 / Download Template ─────────────────────────────────────────
  readonly step1Block: Locator;          // h4 "Step 1: Download Excel Template"
  readonly downloadTemplateBtn: Locator; // button "Download Template" — alert() only, no API

  // ── Drop zone ──────────────────────────────────────────────────────────
  // No semantic class on the drop zone div — use text content for state detection
  readonly dropZoneIdleText: Locator;  // "Drag & drop your Excel file here, or click to browse"
  readonly dropZoneReadyText: Locator; // "File uploaded successfully!"

  // ── File input — HIDDEN. NEVER click(). ALWAYS setInputFiles(). ─────────
  readonly fileInput: Locator;          // input[type="file"]

  // ── File info panel (only when selectedFile is set) ────────────────────
  // File name: rendered as {selectedFile.name} in a text/medium div
  // Stable approach: the filename appears uniquely in the panel — use toContainText in tests
  readonly removeFileBtn: Locator;     // button "Remove"
  readonly startImportBtn: Locator;    // button "Start Import" / "Importing..." text

  // ── Import in Progress card (State 3 — OUT OF SCOPE for smoke) ──────────
  readonly importProgressH2: Locator;   // h2 "Import in Progress"
  readonly doNotCloseWarning: Locator;  // warning text about not closing page

  // ── Import Error card (State 4 — OUT OF SCOPE for smoke) ────────────────
  readonly importErrorH2: Locator;      // h2 "Import Failed"
  readonly tryAgainBtn: Locator;        // button "← Try Again"

  // ── Import Results (States 5-6 — OUT OF SCOPE for smoke) ────────────────
  readonly importSuccessH2: Locator;    // large h2 "All Records Imported Successfully!"
  readonly goToEmployeesBtn: Locator;   // button "Go to Employees Page →"
  readonly importAnotherBtn: Locator;   // button "Import Another File"

  constructor(page: Page) {
    this.page = page;

    this.pageRoot     = page.locator('.bulk-import-page');

    // ⚠️ EN-DASH in title — U+2013, not hyphen U+002D
    this.pageHeading  = page.getByRole('heading', { name: 'Bulk Import – Employee & Skill Data' });
    this.pageSubtitle = page.getByText('Upload an Excel file to bulk add or update employee and skill records.');

    this.step1Block          = page.getByText('Step 1: Download Excel Template');
    this.downloadTemplateBtn = page.getByRole('button', { name: 'Download Template' });

    this.dropZoneIdleText  = page.getByText('Drag & drop your Excel file here, or click to browse');
    this.dropZoneReadyText = page.getByText('File uploaded successfully!');

    // Hidden input — setInputFiles() only. click() will throw because className="hidden".
    this.fileInput = page.locator('input[type="file"]');

    this.removeFileBtn   = page.getByRole('button', { name: 'Remove' });
    // Matches both "Start Import" and "Importing..." — covers the disabled state too
    this.startImportBtn  = page.getByRole('button', { name: /Start Import|Importing/i });

    this.importProgressH2  = page.getByRole('heading', { name: 'Import in Progress' });
    this.doNotCloseWarning = page.getByText(/Do not close this page/i);

    this.importErrorH2 = page.getByRole('heading', { name: 'Import Failed' });
    this.tryAgainBtn   = page.getByRole('button', { name: '← Try Again' });

    this.importSuccessH2   = page.getByText('All Records Imported Successfully!');
    this.goToEmployeesBtn  = page.getByRole('button', { name: /Go to Employees Page/i });
    this.importAnotherBtn  = page.getByRole('button', { name: 'Import Another File' });
  }

  /**
   * Navigate to /system/import (sidebar nav route) and wait for page root.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/system/import');
    await this.pageRoot.waitFor({ state: 'visible', timeout: 15000 });
  }

  /**
   * Wait for all three always-visible elements to be ready.
   */
  async waitForLoad(): Promise<void> {
    await this.pageHeading.waitFor({ state: 'visible', timeout: 10000 });
    await this.dropZoneIdleText.waitFor({ state: 'visible', timeout: 10000 });
    await this.downloadTemplateBtn.waitFor({ state: 'visible', timeout: 10000 });
  }

  /**
   * Attach a file to the hidden file input using setInputFiles().
   *
   * CRITICAL: The input has className="hidden". This method uses setInputFiles()
   * which bypasses visibility checks. Do NOT replace with fileInput.click().
   *
   * @param filePath Absolute path to the .xlsx file to attach.
   */
  async attachFile(filePath: string): Promise<void> {
    await this.fileInput.setInputFiles(filePath);
    // Brief wait for React state update (handleFileSelect sets selectedFile)
    await this.page.waitForTimeout(300);
  }

  /**
   * Click the Remove button to clear the selected file.
   * After this call the page returns to idle state.
   */
  async removeFile(): Promise<void> {
    await this.removeFileBtn.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Returns true if page is in idle state:
   *   - idle text is visible
   *   - Start Import button is NOT in the DOM (only rendered when selectedFile set)
   */
  async isInIdleState(): Promise<boolean> {
    const idleVisible = await this.dropZoneIdleText.isVisible();
    const startImportPresent = await this.startImportBtn.count();
    return idleVisible && startImportPresent === 0;
  }

  /**
   * Returns true if page is in file-selected state:
   *   - ready text is visible
   *   - Start Import button is visible and enabled
   */
  async isInFileSelectedState(): Promise<boolean> {
    const readyVisible = await this.dropZoneReadyText.isVisible();
    const startImportVisible = await this.startImportBtn.isVisible();
    return readyVisible && startImportVisible;
  }

  /**
   * Returns true if Start Import button is present and NOT disabled.
   */
  async isStartImportEnabled(): Promise<boolean> {
    if (await this.startImportBtn.count() === 0) return false;
    return !(await this.startImportBtn.isDisabled());
  }

  /**
   * Helper: resolve an e2e-relative path to an absolute path.
   * Usage: attachFile(bi.resolveFixture('test-import.xlsx'))
   */
  resolveFixture(filename: string): string {
    return path.resolve(__dirname, '..', 'fixtures', filename);
  }
}
