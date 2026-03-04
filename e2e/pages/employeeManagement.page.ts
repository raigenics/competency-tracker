// Module: employeeManagement.page.ts
// Purpose: Page object for Employee Management module
// Part of: CompetencyIQ E2E Automation Suite
//
// Route: /employees → EmployeeManagement component
// Source: frontend/src/pages/Employees/EmployeeManagement.jsx
//
// ⚠️  SELECTOR NOTES — READ BEFORE EDITING:
//
//   1. "employees-page" is the ONLY semantic className in EmployeeManagement.jsx.
//      Everything else uses Tailwind utility classes (px-4, py-2.5, bg-[#667eea], etc.).
//      NEVER use Tailwind strings as selectors.
//
//   2. The employee list is a CSS GRID of <div>s — NOT an HTML <table>.
//      getByRole('table') finds NOTHING. Row count is proxied via Edit button count.
//
//   3. Edit buttons:   title="Edit employee"   → getByTitle('Edit employee')
//      Delete buttons: title="Delete employee" → getByTitle('Delete employee')
//      These title attributes are the ONLY stable per-row action selectors.
//
//   4. Autocomplete dropdown container and items have NO semantic class or testid.
//      SUGGESTED IMPROVEMENT: Add data-testid="autocomplete-dropdown" to the dropdown div
//      and data-testid="suggestion-item" to each item div in EmployeeManagement.jsx.
//      WORKAROUND: Each suggestion item contains <span>—</span> (em dash separator between
//      ZID and name). Table row "—" values are plain text nodes inside <div>s, not <span>s.
//      This makes locating spans containing exactly "—" specific to suggestion items.
//
//   5. Clear search button (X): plain <button> sibling of search input — SVG child,
//      no title or aria-label.
//      SUGGESTED IMPROVEMENT: Add data-testid="clear-search-btn" to that button.
//      WORKAROUND: CSS sibling combinator from search input.
//
//   6. Delete modal: no semantic class or testid. Located by its h3 heading text.
//
//   7. AddEmployeeDrawer has BOTH .add-employee-drawer CSS class AND
//      data-testid="add-employee-drawer" — confirmed from AddEmployeeDrawer.jsx.
//
// SELECTORS USED — CONFIRMED STRATEGIES:
//   pageRoot             → .employees-page  (semantic class — only one on page)
//   pageHeading          → getByRole('heading', { name: 'Employees' })
//   addEmployeeBtn       → getByRole('button', { name: '+ Add Employee' })
//   searchInput          → getByPlaceholder('Search by ZID or Name...')
//   clearSearchBtn       → CSS sibling of search input (see note 5)
//   subSegmentSelect     → locator('select').nth(0)
//   projectSelect        → locator('select').nth(1)
//   teamSelect           → locator('select').nth(2)
//   suggestion items     → span[text-is("—")] parent — see getSuggestionItems()
//   noSuggestionsText    → getByText('No Record Found')
//   editBtns             → getByTitle('Edit employee')   — title attr from JSX
//   deleteBtns           → getByTitle('Delete employee') — title attr from JSX
//   loadingText          → getByText('Loading employees...')
//   emptyStateHeading    → getByRole('heading', { name: 'No Employees Found' })
//   columnHeaders        → getByText('ZID'), getByText('Full Name'), etc.
//   deleteModalHeading   → getByRole('heading', { name: 'Delete Employee' })
//   deleteModalName      → locator('strong')  (only <strong> in DOM when modal open)
//   deleteCancelBtn      → getByRole('button', { name: 'Cancel' })
//   drawer               → locator('.add-employee-drawer')  (semantic class confirmed)
//   drawerTitle          → locator('.drawer-title h3')      (semantic class confirmed)
//   drawerCloseBtn       → locator('.close-btn')            (semantic class confirmed)
//   paginationInfo       → getByText(/Showing/)
//   nextPageBtn          → getByRole('button', { name: 'Next' })
//   prevPageBtn          → getByRole('button', { name: 'Previous' })

import { Page, Locator } from '@playwright/test';

export default class EmployeeManagementPage {
  readonly page: Page;

  // ── Page structure ────────────────────────────────────────────────────────
  readonly pageRoot: Locator;           // .employees-page (only semantic class)
  readonly pageHeading: Locator;        // h1 "Employees" via role

  // ── Add Employee button (RBAC: SUPER_ADMIN → visible) ─────────────────────
  readonly addEmployeeBtn: Locator;

  // ── Search & filter bar ───────────────────────────────────────────────────
  readonly searchInput: Locator;        // placeholder "Search by ZID or Name..."
  readonly clearSearchBtn: Locator;     // X button sibling of search input (see note 5)
  readonly subSegmentSelect: Locator;   // first <select> in filter bar
  readonly projectSelect: Locator;      // second <select> (disabled until subSegment chosen)
  readonly teamSelect: Locator;         // third <select> (disabled until project chosen)

  // ── Autocomplete suggestions ──────────────────────────────────────────────
  readonly noSuggestionsText: Locator;  // "No Record Found" empty state text

  // ── Employee data rows (grid divs — NOT a real <table>) ───────────────────
  readonly editBtns: Locator;           // all [title="Edit employee"] buttons on page
  readonly deleteBtns: Locator;         // all [title="Delete employee"] buttons on page
  readonly loadingText: Locator;        // "Loading employees..." shown while fetching
  readonly emptyStateHeading: Locator;  // h3 "No Employees Found"

  // ── Column headers (div-based header row, NOT <thead>) ────────────────────
  readonly colZID: Locator;
  readonly colFullName: Locator;
  readonly colSubSegment: Locator;
  readonly colProject: Locator;
  readonly colTeam: Locator;
  readonly colRole: Locator;
  readonly colActions: Locator;

  // ── Delete confirmation modal (no semantic class — located by heading) ─────
  readonly deleteModalHeading: Locator;   // h3 "Delete Employee"
  readonly deleteModalName: Locator;      // <strong> containing employee name
  readonly deleteCancelBtn: Locator;      // button "Cancel"
  // NOTE: deleteConfirmBtn intentionally omitted — NEVER click in smoke tests

  // ── Add/Edit drawer (.add-employee-drawer — semantic class confirmed) ──────
  readonly drawer: Locator;              // .add-employee-drawer
  readonly drawerTitle: Locator;         // .drawer-title h3
  readonly drawerCloseBtn: Locator;      // .close-btn
  readonly editLoadingContainer: Locator; // .edit-loading-container (overlay during edit bootstrap)

  // ── Pagination ────────────────────────────────────────────────────────────
  readonly paginationInfo: Locator;     // "Showing X to Y of Z employees"
  readonly nextPageBtn: Locator;        // button "Next"
  readonly prevPageBtn: Locator;        // button "Previous"

  constructor(page: Page) {
    this.page = page;

    this.pageRoot    = page.locator('.employees-page');
    this.pageHeading = page.getByRole('heading', { name: 'Employees' });

    this.addEmployeeBtn = page.getByRole('button', { name: '+ Add Employee' });

    this.searchInput    = page.getByPlaceholder('Search by ZID or Name...');
    // Clear X: appears as a button sibling of the search input when searchTerm !== ''
    // No title or aria-label — SUGGESTED IMPROVEMENT: add data-testid="clear-search-btn"
    this.clearSearchBtn = page.locator('input[placeholder="Search by ZID or Name..."] ~ button');
    this.subSegmentSelect = page.locator('select').nth(0);
    this.projectSelect    = page.locator('select').nth(1);
    this.teamSelect       = page.locator('select').nth(2);

    this.noSuggestionsText = page.getByText('No Record Found');

    // Title attributes are the most stable per-row action selectors (no testid on rows)
    this.editBtns   = page.getByTitle('Edit employee');
    this.deleteBtns = page.getByTitle('Delete employee');

    this.loadingText       = page.getByText('Loading employees...');
    this.emptyStateHeading = page.getByRole('heading', { name: 'No Employees Found' });

    // Column headers — exact text from JSX (div-based grid header, NOT <thead>)
    this.colZID        = page.getByText('ZID',         { exact: true });
    this.colFullName   = page.getByText('Full Name',   { exact: true });
    this.colSubSegment = page.getByText('Sub-segment', { exact: true });
    this.colProject    = page.getByText('Project',     { exact: true });
    this.colTeam       = page.getByText('Team',        { exact: true });
    this.colRole       = page.getByText('Role',        { exact: true });
    this.colActions    = page.getByText('Actions',     { exact: true });

    this.deleteModalHeading = page.getByRole('heading', { name: 'Delete Employee' });
    // <strong> only exists in the delete modal (conditional render — no other <strong> on page)
    this.deleteModalName    = page.locator('strong');
    this.deleteCancelBtn    = page.getByRole('button', { name: 'Cancel' });

    this.drawer                = page.locator('.add-employee-drawer');
    this.drawerTitle           = page.locator('.drawer-title h3');
    this.drawerCloseBtn        = page.locator('.close-btn');
    // .edit-loading-container: semantic class confirmed from AddEmployeeDrawer.jsx
    // Shown while bootstrap data (org dropdowns + role) loads in edit mode
    this.editLoadingContainer  = page.locator('.edit-loading-container');

    this.paginationInfo = page.getByText(/Showing/);
    this.nextPageBtn    = page.getByRole('button', { name: 'Next' });
    this.prevPageBtn    = page.getByRole('button', { name: 'Previous' });
  }

  /**
   * Navigate to /employees and wait for page root to be visible.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/employees');
    await this.pageRoot.waitFor({ state: 'visible', timeout: 15000 });
  }

  /**
   * Wait for the initial table data to finish loading.
   * Uses loading text disappearance + first Edit button visibility as proxy.
   * (SUPER_ADMIN: every data row renders an Edit button → editBtns.count() === row count)
   */
  async waitForTableLoad(): Promise<void> {
    await this.loadingText.waitFor({ state: 'hidden', timeout: 10000 });
    await this.editBtns.first().waitFor({ state: 'visible', timeout: 10000 });
  }

  /**
   * Fill the search input and wait for the 300ms debounce.
   */
  async typeInSearch(text: string): Promise<void> {
    await this.searchInput.fill(text);
    await this.page.waitForTimeout(400); // 300ms debounce + 100ms margin
  }

  /**
   * Wait for autocomplete dropdown to show suggestions OR "No Record Found".
   *
   * LIMITATION: Dropdown container has no semantic class or testid.
   *   SUGGESTED IMPROVEMENT: Add data-testid="autocomplete-dropdown" to the dropdown div
   *   in EmployeeManagement.jsx for a first-class stable selector.
   * WORKAROUND: Races between first suggestion item becoming visible and the empty-state text.
   */
  async waitForSuggestions(): Promise<void> {
    await Promise.race([
      this.getSuggestionItems().first().waitFor({ state: 'visible', timeout: 5000 }),
      this.noSuggestionsText.waitFor({ state: 'visible', timeout: 5000 }),
    ]);
  }

  /**
   * Locator for all autocomplete suggestion item divs.
   *
   * Strategy: Each suggestion item renders <span>—</span> (em dash separator, JSX line ~877).
   * Table row "—" fallback values are plain text nodes inside <div> cells — NOT in <span>s.
   * Targeting <span> elements whose text is exactly "—" is therefore unique to suggestions.
   * Traversing to the parent gives the clickable item div.
   *
   * SUGGESTED IMPROVEMENT: Add data-testid="suggestion-item" to each item div in the
   * suggestions.map() loop in EmployeeManagement.jsx for a simpler selector.
   */
  getSuggestionItems(): Locator {
    return this.page.locator('span').filter({ hasText: /^—$/ }).locator('xpath=..');
  }

  /**
   * Click the autocomplete suggestion at the given index (default: first).
   */
  async clickSuggestion(index = 0): Promise<void> {
    const items = this.getSuggestionItems();
    await items.nth(index).waitFor({ state: 'visible', timeout: 5000 });
    await items.nth(index).click();
  }

  /**
   * Click the X button to clear the search input.
   */
  async clearSearch(): Promise<void> {
    await this.clearSearchBtn.click();
    await this.page.waitForTimeout(400);
  }

  /**
   * Count visible data rows.
   * Proxy: Edit button count equals row count for SUPER_ADMIN (one Edit per row).
   */
  async getRowCount(): Promise<number> {
    return await this.editBtns.count();
  }

  /**
   * Click "+ Add Employee" and wait for the drawer to open.
   */
  async openAddDrawer(): Promise<void> {
    await this.addEmployeeBtn.click();
    await this.drawer.waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * Click the ✕ close button and wait for the drawer to close.
   */
  async closeDrawer(): Promise<void> {
    await this.drawerCloseBtn.click();
    await this.drawer.waitFor({ state: 'hidden', timeout: 5000 });
  }

  /**
   * Click the Delete button on the given row index (0-based) and wait for modal.
   */
  async clickDeleteOnRow(rowIndex = 0): Promise<void> {
    await this.deleteBtns.nth(rowIndex).click();
    await this.deleteModalHeading.waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * Click Cancel in the delete confirmation modal and wait for it to close.
   */
  async cancelDelete(): Promise<void> {
    await this.deleteCancelBtn.click();
    await this.deleteModalHeading.waitFor({ state: 'hidden', timeout: 5000 });
  }

  /**
   * Click the Edit button on the given row index (0-based), wait for the drawer to open,
   * and then wait for the edit bootstrap loading overlay to disappear.
   * The overlay (.edit-loading-container) appears briefly while the drawer fetches
   * org dropdowns and role data for the selected employee.
   */
  async clickEditOnRow(rowIndex = 0): Promise<void> {
    await this.editBtns.nth(rowIndex).click();
    await this.drawer.waitFor({ state: 'visible', timeout: 5000 });
    // Wait for edit bootstrap loading overlay (may be instant if data is cached)
    try {
      await this.editLoadingContainer.waitFor({ state: 'visible', timeout: 2000 });
      await this.editLoadingContainer.waitFor({ state: 'hidden', timeout: 8000 });
    } catch {
      // Loading overlay may not appear if bootstrap data loads faster than 2s — that's OK
    }
  }
}

