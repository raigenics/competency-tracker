// Module: skillCoverage.page.ts
// Purpose: Page object for Skill Coverage / Capability Overview module
// Route:   /skill-coverage  → renders SkillCoveragePage (Taxonomy/SkillCoveragePage.jsx)
// Part of: CompetencyIQ E2E Automation Suite
//
// Source files read before writing selectors:
//   frontend/src/pages/Taxonomy/SkillCoveragePage.jsx         (831 lines)
//   frontend/src/pages/Taxonomy/components/TaxonomyTree.jsx   (310 lines)
//   frontend/src/pages/Taxonomy/components/SkillDetailsPanel.jsx (610 lines)
//   frontend/src/layouts/TwoPaneLayout.jsx                    (155 lines)
//
// All selectors verified against JSX source — no guesses.

import { Page, Locator } from '@playwright/test';

export default class SkillCoveragePage {
  readonly page: Page;

  // ── Page root ────────────────────────────────────────────────────────────
  /** Outermost div: <div className="capability-overview">  (SkillCoveragePage.jsx line 672) */
  readonly pageRoot: Locator;

  // ── Header section ───────────────────────────────────────────────────────
  /** h1.co-page-title → "Capability Overview"  (NOT "Skill Coverage") */
  readonly pageTitle: Locator;
  /** p.co-page-description below the h1 */
  readonly pageDescription: Locator;

  // ── Metrics strip ────────────────────────────────────────────────────────
  /** div.co-metrics-strip — the entire metrics bar  (line 683) */
  readonly metricsStrip: Locator;
  /**
   * div.co-metrics-item — exactly 4 items in source order:
   *   [0] skills  [1] employees  [2] aver. proficiency  [3] certifications
   */
  readonly metricsItems: Locator;

  // ── TwoPaneLayout panes ──────────────────────────────────────────────────
  /**
   * Left pane wrapper rendered by TwoPaneLayout:
   *   className="two-pane-left co-tree-panel"
   *   data-testid="two-pane-left"  (TwoPaneLayout.jsx line 105)
   */
  readonly leftPane: Locator;
  /**
   * Right pane wrapper:
   *   className="two-pane-right co-detail-pane"
   *   data-testid="two-pane-right"  (TwoPaneLayout.jsx line 130)
   */
  readonly rightPane: Locator;

  // ── Tree toolbar (inside TwoPaneLayout leftHeader slot) ──────────────────
  /** div.co-tree-search-box — wrapper around search icon + input + clear btn */
  readonly searchWrapper: Locator;
  /** The <input type="text"> inside co-tree-search-box — no own class on the element */
  readonly searchInput: Locator;
  /**
   * button.co-tree-search-clear — the × clear button.
   * Only present when searchTerm is truthy  (line 745: conditional render).
   */
  readonly clearSearchBtn: Locator;
  /** button.co-tree-action-btn with text "Expand All" */
  readonly expandAllBtn: Locator;
  /** button.co-tree-action-btn with text "Collapse All" */
  readonly collapseAllBtn: Locator;
  /** span.co-tree-path-legend → "Category → Sub-Category → Skills" */
  readonly pathLegend: Locator;
  /**
   * p.co-tree-search-hint — "Showing results for ..." text.
   * Only present when searchTerm is non-empty  (line 757: conditional render).
   */
  readonly searchHint: Locator;

  // ── Organisation Summary button ───────────────────────────────────────────
  /**
   * button.co-org-summary-btn
   * Gets class `active` appended when !selectedSkill  (line 778).
   */
  readonly orgSummaryBtn: Locator;

  // ── Tree body ────────────────────────────────────────────────────────────
  /** div.co-tree-body — scrollable container for org-summary-btn + TaxonomyTree */
  readonly treeBody: Locator;
  /**
   * Category row buttons — button.co-tree-row that contain
   * a span.co-tree-type with text "Category"  (TaxonomyTree.jsx line 173).
   * These rows are only visible after tree load (not during skeleton).
   */
  readonly categoryRows: Locator;
  /**
   * Sub-category row buttons — button.co-tree-row with type badge "Sub"
   * (TaxonomyTree.jsx line 225).
   * Visible only after a parent category is expanded.
   */
  readonly subCategoryRows: Locator;
  /**
   * Skill row buttons — button.co-tree-row.skill
   * (TaxonomyTree.jsx line 262: className="co-tree-row skill").
   * Visible only after a subcategory is expanded.
   */
  readonly skillRows: Locator;

  // ── Right panel states ────────────────────────────────────────────────────
  /**
   * h2.co-detail-title inside the default (no-skill) right panel.
   * Text: "Organisation Capability Summary"
   * Present when skill prop === null  (SkillDetailsPanel.jsx line ~225).
   */
  readonly rightPanelDefault: Locator;
  /**
   * div.dp-top-bar — rendered only when a skill is selected (showViewAll=true).
   * Contains dp-back-btn + dp-breadcrumb + dp-export-btn  (SkillDetailsPanel.jsx line ~417).
   */
  readonly rightPanelSkillDetail: Locator;
  /**
   * button.dp-back-btn — "Back" button inside skill-detail panel.
   * Clicking calls handleBackToSummary() → sets selectedSkill=null.
   */
  readonly backBtn: Locator;

  constructor(page: Page) {
    this.page = page;

    // Page root — use :not(.co-card) to exclude SkillDetailsPanel's
    // <div class="co-card capability-overview co-details-panel"> which shares the class
    this.pageRoot = page.locator('.capability-overview:not(.co-card)');

    // Header
    this.pageTitle       = page.locator('.co-page-title');
    this.pageDescription = page.locator('.co-page-description');

    // Metrics
    this.metricsStrip = page.locator('.co-metrics-strip');
    this.metricsItems = page.locator('.co-metrics-item');

    // Panes — use data-testid set directly by TwoPaneLayout.jsx
    this.leftPane  = page.locator('[data-testid="two-pane-left"]');
    this.rightPane = page.locator('[data-testid="two-pane-right"]');

    // Toolbar
    this.searchWrapper  = page.locator('.co-tree-search-box');
    this.searchInput    = page.locator('.co-tree-search-box input');
    this.clearSearchBtn = page.locator('.co-tree-search-clear');
    this.expandAllBtn   = page.locator('.co-tree-action-btn', { hasText: 'Expand All' });
    this.collapseAllBtn = page.locator('.co-tree-action-btn', { hasText: 'Collapse All' });
    this.pathLegend     = page.locator('.co-tree-path-legend');
    this.searchHint     = page.locator('.co-tree-search-hint');

    // Org summary
    this.orgSummaryBtn = page.locator('.co-org-summary-btn');

    // Tree body and rows
    this.treeBody = page.locator('.co-tree-body');
    this.categoryRows = page.locator('.co-tree-row', {
      has: page.locator('.co-tree-type', { hasText: 'Category' }),
    });
    this.subCategoryRows = page.locator('.co-tree-row', {
      has: page.locator('.co-tree-type', { hasText: 'Sub' }),
    });
    this.skillRows = page.locator('.co-tree-row.skill');

    // Right panel
    this.rightPanelDefault     = page.locator('.co-detail-title');
    this.rightPanelSkillDetail = page.locator('.dp-top-bar');
    this.backBtn               = page.locator('.dp-back-btn');
  }

  // ── Navigation ────────────────────────────────────────────────────────────

  /**
   * Navigate to /skill-coverage and wait for the page root div to be visible.
   * Does NOT wait for the tree to load — call waitForTreeLoad() after this.
   */
  async navigate(): Promise<void> {
    await this.page.goto('/skill-coverage');
    await this.pageRoot.waitFor({ state: 'visible', timeout: 15_000 });
  }

  // ── Load waits ────────────────────────────────────────────────────────────

  /**
   * Wait for at least one category row to appear in the tree.
   *
   * Design notes:
   *   - On mount, isLoading=true; skeleton may or may not appear (200ms timer guard).
   *   - After API responds, isLoading=false → co-tree-row nodes render.
   *   - 15 s timeout covers slow CI API responses.
   */
  async waitForTreeLoad(): Promise<void> {
    await this.categoryRows.first().waitFor({ state: 'visible', timeout: 15_000 });
  }

  // ── Tree interactions ─────────────────────────────────────────────────────

  /**
   * Type a search term and wait 400 ms (debounce is 300 ms; +100 ms buffer).
   * The search fires only when term.length >= 2  (SkillCoveragePage.jsx line 274).
   */
  async searchFor(term: string): Promise<void> {
    await this.searchInput.fill(term);
    await this.page.waitForTimeout(400);
  }

  /** Click the × clear btn and wait 400 ms for the tree to fully restore. */
  async clearSearch(): Promise<void> {
    await this.clearSearchBtn.click();
    await this.page.waitForTimeout(400);
  }

  /**
   * Click "Expand All" and wait 1000 ms.
   * expandAll() expands the in-memory node set; uncached nodes fire lazy-load calls.
   */
  async clickExpandAll(): Promise<void> {
    await this.expandAllBtn.click();
    await this.page.waitForTimeout(1_000);
  }

  /** Click "Collapse All" and wait 500 ms. */
  async clickCollapseAll(): Promise<void> {
    await this.collapseAllBtn.click();
    await this.page.waitForTimeout(500);
  }

  /** Click Organisation Summary button and wait 500 ms. */
  async clickOrgSummaryBtn(): Promise<void> {
    await this.orgSummaryBtn.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Expand a category by name.
   * Restricts to rows with type "Category" to avoid false-matching subcategory names.
   * Waits 1000 ms for lazy-load API call to return subcategories.
   */
  async expandCategory(name: string): Promise<void> {
    const row = this.page.locator('.co-tree-row', {
      has: this.page.locator('.co-tree-type', { hasText: 'Category' }),
    }).filter({
      has: this.page.locator('.co-tree-name', { hasText: name }),
    }).first();
    await row.click();
    await this.page.waitForTimeout(1_000);
  }

  /**
   * Expand the first visible category row (any name).
   * Useful in smoke tests that need sub-categories but don't care which category.
   * Waits 1000 ms for subcategory lazy-load.
   */
  async expandFirstCategory(): Promise<void> {
    await this.categoryRows.first().click();
    await this.page.waitForTimeout(1_000);
  }

  /**
   * Expand the first visible sub-category row (any name).
   * Requires the parent category to already be expanded.
   * Waits 1000 ms for skill lazy-load.
   */
  async expandFirstSubcategory(): Promise<void> {
    await this.subCategoryRows.first().click();
    await this.page.waitForTimeout(1_000);
  }

  /**
   * Click a skill row by name.
   * Waits 800 ms for right-panel API calls (getSkill, getSkillSummary etc.)
   * to resolve and dp-top-bar to render.
   */
  async clickSkill(name: string): Promise<void> {
    const row = this.skillRows.filter({
      has: this.page.locator('.co-tree-name', { hasText: name }),
    }).first();
    await row.click();
    await this.page.waitForTimeout(800);
  }

  /**
   * Click the first visible skill row (any name).
   * Waits 800 ms.
   */
  async clickFirstSkill(): Promise<void> {
    await this.skillRows.first().click();
    await this.page.waitForTimeout(800);
  }

  // ── Data reads ────────────────────────────────────────────────────────────

  /**
   * Returns {label, value} for all 4 metrics items in source order:
   *   skills | employees | aver. proficiency | certifications
   * Values may be '...' (kpiLoading) or '—' (kpiError).
   */
  async getMetricValues(): Promise<Array<{ label: string; value: string }>> {
    const count = await this.metricsItems.count();
    const result: Array<{ label: string; value: string }> = [];
    for (let i = 0; i < count; i++) {
      const item = this.metricsItems.nth(i);
      const value = (await item.locator('.co-metrics-value').textContent()) ?? '';
      const label = (await item.locator('.co-metrics-label').textContent()) ?? '';
      result.push({ label: label.trim(), value: value.trim() });
    }
    return result;
  }

  /** Count of currently visible category rows. Call after waitForTreeLoad(). */
  async getCategoryCount(): Promise<number> {
    return this.categoryRows.count();
  }

  // ── State checks ──────────────────────────────────────────────────────────

  /**
   * True when the default right panel (no skill selected) is visible.
   * Looks for .co-detail-title "Organisation Capability Summary".
   */
  async isDefaultRightPanel(): Promise<boolean> {
    return this.rightPanelDefault.isVisible();
  }

  /**
   * True when a skill is selected (showViewAll=true in SkillDetailsPanel).
   * Looks for .dp-top-bar which contains Back btn + skill breadcrumb.
   */
  async isSkillDetailRightPanel(): Promise<boolean> {
    return this.rightPanelSkillDetail.isVisible();
  }

  /**
   * True when the Organisation Summary button has class `active`.
   * active is present when !selectedSkill  (SkillCoveragePage.jsx line 778).
   */
  async isOrgSummaryActive(): Promise<boolean> {
    const classes = (await this.orgSummaryBtn.getAttribute('class')) ?? '';
    return classes.includes('active');
  }
}
