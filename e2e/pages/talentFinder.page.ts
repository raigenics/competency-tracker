// Module: talentFinder.page.ts
// Purpose: Page object for Talent Finder module (AdvancedQueryPage)
// Route:   /talent-finder → renders AdvancedQueryPage
//          (frontend/src/pages/AdvancedQuery/AdvancedQueryPage.jsx)
// Part of: CompetencyIQ E2E Automation Suite
//
// ⚠️  NAMING NOTE:
//   The sidebar link says "Talent Finder" but the mounted component is
//   AdvancedQueryPage, which renders h1.page-title = "Capability Finder".
//   TalentFinderPage.jsx exists as dead code and is NOT served by any route.
//
// Source files read:
//   frontend/src/pages/AdvancedQuery/AdvancedQueryPage.jsx         (207 lines)
//   frontend/src/pages/AdvancedQuery/components/QueryBuilderPanel.jsx (288 lines)
//   frontend/src/layouts/MainLayout via TwoPaneLayout is NOT used here
//   frontend/src/components/PageHeader.jsx                          (44 lines)
//   frontend/src/components/Sidebar.jsx                             (208 lines)
//
// All selectors verified against JSX source — no guesses.

import { Page, Locator } from '@playwright/test';

export default class TalentFinderPage {
  readonly page: Page;

  // ── PAGE ROOT ──────────────────────────────────────────────────────────────
  /** <div className="capability-finder">  (AdvancedQueryPage.jsx line ~131) */
  readonly pageRoot: Locator;

  // ── PAGE HEADER ────────────────────────────────────────────────────────────
  /**
   * h1.page-title — text: "Capability Finder"  (PageHeader.jsx + AdvancedQueryPage.jsx line ~133)
   * ⚠️ NOT "Talent Finder" — that text only appears in the sidebar link.
   */
  readonly pageTitle: Locator;
  /** p.page-subtitle — "Select skills and optional filters to find matching employees." */
  readonly pageSubtitle: Locator;

  // ── LAYOUT GRID ───────────────────────────────────────────────────────────
  /** div.cf-grid — two-column grid holding both cards */
  readonly cfGrid: Locator;

  // ── LEFT CARD — Filters ────────────────────────────────────────────────────
  /** section.cf-card[aria-label="Filters"]  (line ~138) */
  readonly filtersCard: Locator;
  /** h3 "Find Talent By" inside the filters card  (line ~139) */
  readonly filtersHeading: Locator;

  // ── FILTER PANEL LOADING ────────────────────────────────────────────────────
  /**
   * Shown by QueryBuilderPanel while fetching roles + sub-segments from API.
   * Text: "Loading filters..."  (QueryBuilderPanel.jsx line ~134)
   * Disappears when dropdown data is ready.
   */
  readonly filtersPanelLoading: Locator;

  // ── FILTER FIELDS ──────────────────────────────────────────────────────────
  /**
   * Match mode segmented control — two buttons inside div.cf-segmented
   * (QueryBuilderPanel.jsx lines ~154-165)
   * "All skills" button is .active by default.
   */
  readonly matchModeSegmented: Locator;
  readonly matchModeAllBtn: Locator;
  readonly matchModeAnyBtn: Locator;

  /** label.cf-label "Skills to Match" — first field in the panel */
  readonly skillsLabel: Locator;

  // ── ACTION BUTTONS ─────────────────────────────────────────────────────────
  /**
   * button.cf-btn.primary — "Search" / "Searching..." during load
   * DISABLED when query.skills.length === 0  (line ~205)
   */
  readonly searchBtn: Locator;
  /** button.cf-btn.ghost — "Reset" — calls handleClearFilters()  (line ~211) */
  readonly resetBtn: Locator;

  // ── RIGHT CARD — Results ────────────────────────────────────────────────────
  /** section.cf-card[aria-label="Results"]  (line ~147) */
  readonly resultsCard: Locator;
  /**
   * div.cf-count — "Matching Talent (N)"  (line ~149)
   * Always visible; count is 0 before any search.
   */
  readonly resultsCount: Locator;
  /** div.cf-topbar — contains cf-count + TalentExportMenu */
  readonly resultsTopbar: Locator;

  // ── EMPTY / LOADING STATES ────────────────────────────────────────────────
  /**
   * div.cf-empty — container for both pre-search and no-results states.
   * cf-empty-title text changes based on state:
   *   Pre-search:  "No search performed"
   *   No results:  "No matching employees found"
   */
  readonly emptyState: Locator;
  readonly emptyStateTitle: Locator;
  readonly emptyStateSub: Locator;

  // ── SKILL SELECTOR ──────────────────────────────────────────────────────────
  /**
   * The text input inside EnhancedSkillSelector.
   * placeholder="Type to search skills\u2026"  (U+2026 ellipsis)
   * Clicking the input (or its parent container) opens the suggestion dropdown.
   */
  readonly skillSelectorInput: Locator;
  /**
   * Each <li> option inside the open EnhancedSkillSelector dropdown.
   * Scoped to the "Skills to Match" cf-field to avoid matching other dropdowns.
   * The component uses Tailwind-only classes — no custom BEM class on <li>.
   */
  readonly skillOptionInDropdown: Locator;
  /**
   * Selected skill chip: span with Tailwind bg-blue-100 rounded-full classes.
   * Appears inside the selector container after a skill is chosen via handleSelectSkill().
   * EnhancedSkillSelector.jsx renders: <span className="...bg-blue-100...rounded-full...">.
   */
  readonly selectedSkillChip: Locator;
  /**
   * Result rows — <tr> inside <tbody> in TalentResultsTable.
   * TalentResultsTable renders a plain <table>; rows use Tailwind border classes,
   * no custom BEM class.  Present only after a successful search.
   */
  readonly resultsRow: Locator;

  constructor(page: Page) {
    this.page = page;

    // Page root
    this.pageRoot = page.locator('.capability-finder');

    // Header (PageHeader renders h1.page-title, p.page-subtitle)
    this.pageTitle    = page.locator('h1.page-title');
    this.pageSubtitle = page.locator('p.page-subtitle');

    // Grid
    this.cfGrid = page.locator('.cf-grid');

    // Left card
    this.filtersCard    = page.locator('section.cf-card[aria-label="Filters"]');
    this.filtersHeading = this.filtersCard.locator('h3');

    // Filter panel loading state
    this.filtersPanelLoading = page.getByText('Loading filters...');

    // Match mode
    this.matchModeSegmented = page.locator('.cf-segmented');
    this.matchModeAllBtn    = page.locator('.cf-segmented button', { hasText: 'All skills' });
    this.matchModeAnyBtn    = page.locator('.cf-segmented button', { hasText: 'Any skill' });

    // Skills label (first cf-label rendered in panel)
    this.skillsLabel = page.locator('.cf-label', { hasText: 'Skills to Match' });

    // Action buttons (inside cf-actions div)
    this.searchBtn = page.locator('button.cf-btn.primary');
    this.resetBtn  = page.locator('button.cf-btn.ghost');

    // Right card
    this.resultsCard   = page.locator('section.cf-card[aria-label="Results"]');
    this.resultsCount  = page.locator('.cf-count');
    this.resultsTopbar = page.locator('.cf-topbar');

    // Empty / loading states
    this.emptyState      = page.locator('.cf-empty');
    this.emptyStateTitle = page.locator('.cf-empty-title');
    this.emptyStateSub   = page.locator('.cf-empty-sub');

    // Skill selector — EnhancedSkillSelector uses Tailwind only (no BEM classes)
    // Scope skillOptionInDropdown + selectedSkillChip to the "Skills to Match" field
    const skillsField = page.locator('.cf-field', {
      has: page.locator('.cf-label', { hasText: 'Skills to Match' }),
    });
    this.skillSelectorInput    = page.locator('input[placeholder="Type to search skills\u2026"]');
    this.skillOptionInDropdown = skillsField.locator('li');
    this.selectedSkillChip     = skillsField.locator('span[class*="rounded-full"]');

    // Results table — TalentResultsTable → <tbody> <tr>
    this.resultsRow = page.locator('tbody tr');
  }

  // ── NAVIGATION ─────────────────────────────────────────────────────────────

  /**
   * Navigate to /talent-finder and wait for the page root to be visible.
   * Does NOT wait for filter dropdowns — call waitForFiltersReady() after this.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/talent-finder');
    await this.pageRoot.waitFor({ state: 'visible', timeout: 15_000 });
  }

  // ── LOAD WAITS ─────────────────────────────────────────────────────────────

  /**
   * Wait for the QueryBuilderPanel to finish loading dropdown data.
   * The Search button is only rendered after loading=false in the panel.
   * Waits up to 15 s to cover slow API responses.
   */
  async waitForFiltersReady(): Promise<void> {
    await this.searchBtn.waitFor({ state: 'visible', timeout: 15_000 });
  }

  // ── STATE CHECKS ───────────────────────────────────────────────────────────

  /**
   * True when Search button is disabled (no skills selected).
   * Confirmed from line ~205: disabled={isLoading || !query.skills || query.skills.length === 0}
   */
  async isSearchDisabled(): Promise<boolean> {
    return this.searchBtn.isDisabled();
  }

  /**
   * True when "All skills" button has the active class.
   * Default state on page load.
   */
  async isMatchModeAll(): Promise<boolean> {
    const cls = (await this.matchModeAllBtn.getAttribute('class')) ?? '';
    return cls.includes('active');
  }

  // ── RESULT COUNT HELPER ────────────────────────────────────────────────────

  /**
   * Returns the numeric count from div.cf-count text "Matching Talent (N)".
   * Extracts the number in parentheses.
   */
  async getMatchingTalentCount(): Promise<number> {
    const text = (await this.resultsCount.textContent()) ?? '';
    const match = text.match(/\((\d+)\)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  // ── SKILL SELECTION ────────────────────────────────────────────────────────

  /**
   * Select a skill using EnhancedSkillSelector (Path A — searchable input):
   *   1. Click the input to open the dropdown
   *   2. Fill the skill name to filter suggestions (API-driven)
   *   3. Wait for the matching <li> option to appear (up to 10 s)
   *   4. Click the option
   *   5. Wait for the selection chip to confirm React state update
   *
   * EnhancedSkillSelector fetches via capabilityFinderApi.getSkillSuggestions()
   * on open; a "Loading..." placeholder appears until results arrive.
   */
  async selectSkill(skillName: string): Promise<void> {
    // Open the dropdown by clicking the input
    await this.skillSelectorInput.click();
    // Filter options by typing the skill name
    await this.skillSelectorInput.fill(skillName);
    // Wait for API to return the option (loadSuggestions is async)
    const option = this.skillOptionInDropdown.filter({ hasText: skillName }).first();
    await option.waitFor({ state: 'visible', timeout: 10_000 });
    // Click the option (handleSelectSkill adds to query.skills array)
    await option.click();
    // Confirm chip rendered — proves React state was updated
    const chip = this.selectedSkillChip.filter({ hasText: skillName }).first();
    await chip.waitFor({ state: 'visible', timeout: 5_000 });
  }

  /**
   * Wait for at least one result row to be visible.
   * TalentResultsTable renders <tbody> <tr> rows only after a successful API response.
   */
  async waitForResults(timeout = 10_000): Promise<void> {
    await this.resultsRow.first().waitFor({ state: 'visible', timeout });
  }
}
