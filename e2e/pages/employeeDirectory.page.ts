// Module: employeeDirectory.page.ts
// Purpose: Page object for Employee Directory module
// Route:   /profile  → renders EmployeeDirectory (frontend/src/pages/Profile/EmployeeDirectory.jsx)
// Part of: CompetencyIQ E2E Automation Suite
//
// Source files read before writing selectors:
//   frontend/src/pages/Profile/EmployeeDirectory.jsx  (817 lines)
//   frontend/src/app/routes.jsx  — confirmed route "profile"
//   e2e/testdata/seed.sql        — Alice Chen (employee_id 9090, ZID TEST-EMP-001)
//
// All selectors verified against JSX source — no guesses.
// NOTE: The old stub used data-testid attributes that do NOT exist in the JSX.
// This file replaces it entirely with verified CSS class selectors.

import { Page, Locator } from '@playwright/test';

export default class EmployeeDirectoryPage {
  readonly page: Page;

  // ── PAGE ROOT ──────────────────────────────────────────────────────────────
  /** <div className="employee-profile">  (line ~424) — always present */
  readonly pageRoot: Locator;

  // ── TOPBAR ─────────────────────────────────────────────────────────────────
  /** <div className="topbar">  (line ~426) — always visible */
  readonly topbar: Locator;
  /** <h1> inside .topbar-title — text: "Employee Profile" */
  readonly pageTitle: Locator;
  /** <div className="search-wrap">  — wraps icon + input + dropdown */
  readonly searchWrap: Locator;
  /**
   * <input type="text" placeholder="Search by name or ZID…">
   * No className — uniquely selected as child input of .search-wrap.
   */
  readonly searchInput: Locator;
  /**
   * <button className="btn-primary">Search</button>
   * ⚠️ NO disabled prop — ALWAYS ENABLED. Never assert it is disabled.
   */
  readonly searchBtn: Locator;
  /**
   * <button className="btn-outline [disabled]">↑ Export ▾</button>
   * Has BOTH disabled attribute AND "disabled" CSS class when !hasSelectedEmployee.
   * Both removed once profile is loaded.
   */
  readonly exportBtn: Locator;

  // ── AUTOCOMPLETE DROPDOWN ──────────────────────────────────────────────────
  /** <div className="dropdown"> — renders inside .search-wrap when open */
  readonly dropdown: Locator;
  /** <div className="dropdown-item [highlighted]"> — each suggestion row */
  readonly dropdownItems: Locator;
  /** <div className="emp-name"> — employee full_name inside each dropdown-item */
  readonly empNameInDropdown: Locator;

  // ── EMPTY / STATE ELEMENTS ─────────────────────────────────────────────────
  /**
   * <div className="empty-state"> — shared by default state, no-match, and error.
   * Distinguish each state by the h2 text content ONLY.
   */
  readonly emptyState: Locator;
  /**
   * <h2> inside .empty-state — text varies:
   *   "No employee selected"        → default (no search yet)
   *   "No matching employee found"  → after search returns no match
   *   "Failed to load profile"      → profile API error
   */
  readonly emptyStateHeading: Locator;

  // ── LOADING STATE ──────────────────────────────────────────────────────────
  /**
   * <div className="loading-state"> — renders while isLoadingProfile === true.
   * May not be visible on fast connections.
   */
  readonly loadingState: Locator;

  // ── PROFILE HEADER ─────────────────────────────────────────────────────────
  /** <div className="profile-header"> — present only when employeeProfile !== null */
  readonly profileHeader: Locator;
  /**
   * <h2> inside .profile-name-block — employee_name from API.
   * Bare h2, no own CSS class.
   */
  readonly profileName: Locator;
  /** <span className="zid-badge"> — text: "ZID: TEST-EMP-001" */
  readonly zidBadge: Locator;
  /** <div className="meta-chip"> — exactly 4: Sub-Seg, Project, Team, Role */
  readonly metaChips: Locator;
  /** <div className="stat-pills"> — container for Total Skills + Certified */
  readonly statPills: Locator;
  /**
   * <div className="val"> inside the FIRST .stat-pill
   * Contains the Total Skills count as text.
   */
  readonly totalSkillsVal: Locator;

  // ── CORE EXPERTISE ─────────────────────────────────────────────────────────
  /** <div className="expertise-grid"> — up to 3 top skills */
  readonly expertiseGrid: Locator;
  /** <div className="expertise-card [stale]"> — each expertise card */
  readonly expertiseCards: Locator;

  // ── ALL SKILLS TABLE ───────────────────────────────────────────────────────
  /** <table> — skills data table, present only after profile loads */
  readonly skillsTable: Locator;
  /** <tbody> <tr> — each skills row; stale rows have class "stale-row" */
  readonly skillsTableRows: Locator;
  /**
   * button.filter-btn — 6 buttons (in JSX order):
   * All Levels | Expert | Proficient | Competent | Adv. Beginner | Novice
   */
  readonly filterBtns: Locator;
  /** <input placeholder="Search within skills…"> inside .table-search */
  readonly tableSearchInput: Locator;
  /** <div className="legend-row"> — footer legend below skills table */
  readonly legendRow: Locator;

  constructor(page: Page) {
    this.page = page;

    this.pageRoot    = page.locator('.employee-profile');
    this.topbar      = page.locator('.topbar');
    this.pageTitle   = page.locator('.topbar h1');
    this.searchWrap  = page.locator('.search-wrap');
    this.searchInput = page.locator('.search-wrap input');
    this.searchBtn   = page.locator('button.btn-primary');
    this.exportBtn   = page.locator('button.btn-outline');

    this.dropdown          = page.locator('.dropdown');
    this.dropdownItems     = page.locator('.dropdown-item');
    this.empNameInDropdown = page.locator('.emp-name');

    this.emptyState       = page.locator('.empty-state');
    this.emptyStateHeading = page.locator('.empty-state h2');

    this.loadingState = page.locator('.loading-state');

    this.profileHeader  = page.locator('.profile-header');
    this.profileName    = page.locator('.profile-name-block h2');
    this.zidBadge       = page.locator('.zid-badge');
    this.metaChips      = page.locator('.meta-chip');
    this.statPills      = page.locator('.stat-pills');
    this.totalSkillsVal = page.locator('.stat-pill .val').first();

    this.expertiseGrid  = page.locator('.expertise-grid');
    this.expertiseCards = page.locator('.expertise-card');

    this.skillsTable      = page.locator('table');
    this.skillsTableRows  = page.locator('table tbody tr');
    this.filterBtns       = page.locator('.filter-btn');
    this.tableSearchInput = page.locator('.table-search input');
    this.legendRow        = page.locator('.legend-row');
  }

  // ── NAVIGATION ──────────────────────────────────────────────────────────────

  /** Navigate to /profile and wait for the page root to appear. */
  async navigate(): Promise<void> {
    await this.page.goto('/profile');
    await this.pageRoot.waitFor({ state: 'visible', timeout: 15_000 });
  }

  // ── LOAD WAITS ──────────────────────────────────────────────────────────────

  /**
   * Wait for topbar and search input to be visible.
   * The search input has no loading gate — ready immediately on mount.
   */
  async waitForLoad(): Promise<void> {
    await this.topbar.waitFor({ state: 'visible', timeout: 15_000 });
    await this.searchInput.waitFor({ state: 'visible', timeout: 10_000 });
  }

  // ── SEARCH INTERACTIONS ─────────────────────────────────────────────────────

  /**
   * Fill the search input and wait 400 ms (300 ms debounce + 100 ms buffer).
   * Min 2 characters required to trigger autocomplete.
   */
  async typeInSearch(text: string): Promise<void> {
    await this.searchInput.fill(text);
    await this.page.waitForTimeout(400);
  }

  /**
   * Wait for the autocomplete dropdown to appear.
   * Call after typeInSearch() with 2+ characters.
   */
  async waitForDropdown(): Promise<void> {
    await this.dropdown.waitFor({ state: 'visible', timeout: 5_000 });
  }

  /**
   * Click a suggestion by index (default: first item, index 0).
   * Waits for at least one item to be visible before clicking.
   */
  async selectSuggestion(index = 0): Promise<void> {
    await this.dropdownItems.first().waitFor({ state: 'visible', timeout: 5_000 });
    await this.dropdownItems.nth(index).click();
  }

  // ── PROFILE LOAD WAIT ───────────────────────────────────────────────────────

  /**
   * Wait for the employee profile to finish loading.
   * Uses profileHeader visibility — reliable even on fast connections where
   * loading-state flashes too briefly to catch.
   */
  async waitForProfileLoad(): Promise<void> {
    await this.profileHeader.waitFor({ state: 'visible', timeout: 10_000 });
  }

  // ── STATE CHECKS ────────────────────────────────────────────────────────────

  /** True when "No employee selected" is displayed (default empty state). */
  async isDefaultEmptyState(): Promise<boolean> {
    const text = (await this.emptyStateHeading.textContent()) ?? '';
    return text.includes('No employee selected');
  }

  /** True when "No matching employee found" is displayed. */
  async isNoMatchState(): Promise<boolean> {
    const text = (await this.emptyStateHeading.textContent()) ?? '';
    return text.includes('No matching employee found');
  }

  /** True when profileHeader is visible (profile data fully rendered). */
  async isProfileLoaded(): Promise<boolean> {
    return this.profileHeader.isVisible();
  }

  // ── DATA READS ──────────────────────────────────────────────────────────────

  /** Returns the employee name text from the profile header h2. */
  async getEmployeeNameFromProfile(): Promise<string> {
    return (await this.profileName.textContent()) ?? '';
  }

  /**
   * Returns the numeric Total Skills count from the first stat-pill.
   * Returns 0 if the text cannot be parsed.
   */
  async getTotalSkillsCount(): Promise<number> {
    const text = (await this.totalSkillsVal.textContent()) ?? '0';
    const parsed = parseInt(text.trim(), 10);
    return isNaN(parsed) ? 0 : parsed;
  }

  /** Returns the count of visible tbody tr rows in the skills table. */
  async getSkillsTableRowCount(): Promise<number> {
    return this.skillsTableRows.count();
  }

  // ── FILTER INTERACTION ──────────────────────────────────────────────────────

  /**
   * Click a filter button by its label text and wait 300 ms.
   * Label must be one of: 'All Levels' | 'Expert' | 'Proficient' |
   *                        'Competent' | 'Adv. Beginner' | 'Novice'
   */
  async clickFilterBtn(label: string): Promise<void> {
    await this.filterBtns.filter({ hasText: label }).click();
    await this.page.waitForTimeout(300);
  }
}
