// Module: dashboard.page.ts
// Purpose: Page object for Dashboard module
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Dashboard Page Object
 *
 * Route: /dashboard
 *
 * DashboardPage.jsx layout (715 lines):
 *
 * ALWAYS PRESENT:
 *   <div className="dashboard-page">
 *     <main>
 *       <PageHeader title="Dashboard" .../>
 *
 * EMPTY STATE  (showEmptyState = !loading && (isEmptyState || totalEmployees === 0))
 * Condition: segment_id=1 has NO sub-segments, OR employees=0 in scope
 *
 *   <div className="scope-banner">            ← sibling of empty-content, NOT inside it
 *   <div className="empty-content">
 *     <div className="empty-heading">Your dashboard is ready</div>
 *     <div className="action-row">
 *       <button className="btn-primary">Go to Import Data</button>
 *       <button className="btn-secondary">Go to Employee Management</button>
 *     <div className="checklist">
 *
 * DATA STATE  (condition: !showEmptyState)
 *   <div className="db-grid">
 *     <section className="db-card db-filters-card">
 *       <button className="db-btn ghost">Reset</button>
 *       <div className="db-filters">
 *         <select> Sub-Segment  nth(0) — always enabled
 *         <select> Project      nth(1) — disabled when !dashboardFilters.subSegment
 *         <select> Team         nth(2) — disabled when !dashboardFilters.project
 *       <div className="db-scope"><div className="tag">...
 *       <div className="db-inline-loading">  ← only when isFetching=true
 *     <section className="db-kpis">
 *       <div className="db-kpi"><div className="value">
 */
export default class DashboardPage {
  readonly page: Page;

  // ── Always present ──────────────────────────────────────────────────────────
  /** Root wrapper: <div className="dashboard-page"> */
  readonly pageRoot: Locator;

  // ── Data state ──────────────────────────────────────────────────────────────
  /** Main analytics grid — only rendered when !showEmptyState */
  readonly mainGrid: Locator;
  /** Dashboard Context Filters card */
  readonly filtersCard: Locator;
  /** KPI row: <section className="db-kpis"> */
  readonly kpiSection: Locator;
  /** Each individual KPI card: <div className="db-kpi"> */
  readonly kpiCards: Locator;
  /** Reset button: <button className="db-btn ghost"> */
  readonly resetBtn: Locator;
  /** Current scope text: <div className="db-scope"> <div className="tag"> */
  readonly scopeTag: Locator;
  /** Sub-Segment select — nth(0) in .db-filters */
  readonly subSegmentSelect: Locator;
  /** Project select — nth(1) in .db-filters; disabled until sub-segment chosen */
  readonly projectSelect: Locator;
  /** Team select — nth(2) in .db-filters; disabled until project chosen */
  readonly teamSelect: Locator;
  /** Inline loading indicator during filter-triggered data refresh */
  readonly inlineLoading: Locator;

  // ── Empty state ─────────────────────────────────────────────────────────────
  /** Scope banner — sibling of emptyContent, rendered in same {showEmptyState && ...} block */
  readonly scopeBanner: Locator;
  /** Empty state container */
  readonly emptyContent: Locator;
  /** "Your dashboard is ready" heading */
  readonly emptyHeading: Locator;
  /** Navigation action buttons row */
  readonly actionRow: Locator;
  /** Setup progress checklist */
  readonly checklist: Locator;

  constructor(page: Page) {
    this.page = page;

    this.pageRoot = page.locator('.dashboard-page');

    this.mainGrid    = page.locator('.db-grid');
    this.filtersCard = page.locator('.db-filters-card');
    this.kpiSection  = page.locator('.db-kpis');
    this.kpiCards    = page.locator('.db-kpi');
    // Reset: <button className="db-btn ghost"> — two separate classes
    this.resetBtn    = page.locator('button.db-btn.ghost');
    this.scopeTag    = page.locator('.db-scope .tag');

    // .db-filters contains exactly 3 <select> elements:
    //   index 0 = Sub-Segment, 1 = Project, 2 = Team
    this.subSegmentSelect = page.locator('.db-filters select').nth(0);
    this.projectSelect    = page.locator('.db-filters select').nth(1);
    this.teamSelect       = page.locator('.db-filters select').nth(2);
    this.inlineLoading    = page.locator('.db-inline-loading');

    this.scopeBanner  = page.locator('.scope-banner');
    this.emptyContent = page.locator('.empty-content');
    this.emptyHeading = page.locator('.empty-heading');
    this.actionRow    = page.locator('.action-row');
    this.checklist    = page.locator('.checklist');
  }

  /** Navigate to /dashboard and wait for the page root to be visible */
  async navigate(): Promise<void> {
    await this.page.goto('/dashboard');
    await this.page.waitForSelector('.dashboard-page', { state: 'visible', timeout: 20000 });
  }

  /**
   * Wait for the page to leave the loading state.
   * Resolves when either .db-grid (data state) or .empty-content (empty state)
   * becomes visible. Allows up to 20s for the 200ms skeleton-flicker guard.
   */
  async waitForLoad(): Promise<void> {
    await this.page.waitForSelector('.db-grid, .empty-content', {
      state: 'visible',
      timeout: 20000,
    });
  }

  /** Returns true when the data state (.db-grid) is visible */
  async isDataState(): Promise<boolean> {
    return await this.mainGrid.isVisible();
  }

  /** Returns true when the empty state (.empty-content) is visible */
  async isEmptyState(): Promise<boolean> {
    return await this.emptyContent.isVisible();
  }

  /**
   * Wait until the sub-segment select is visible and the inline loader has cleared.
   * Also waits for sub-segment options to be populated from the API —
   * .db-grid renders immediately on first load (before fetch completes), so
   * options are initially empty until initializeDashboard() resolves.
   * Call before interacting with filters.
   */
  async waitForFiltersReady(): Promise<void> {
    await this.subSegmentSelect.waitFor({ state: 'visible' });
    try {
      await this.page.waitForSelector('.db-inline-loading', { state: 'hidden', timeout: 8000 });
    } catch {
      // spinner may not appear at all if the refresh is instant
    }
    // Wait for at least one sub-segment option to be loaded from the API
    await this.page.waitForSelector(
      '.db-filters select option[value]:not([value=""])',
      { state: 'attached', timeout: 15000 },
    );
  }

  /** Select a sub-segment by option value; waits 1000ms for cascade to settle */
  async selectSubSegment(value: string): Promise<void> {
    await this.subSegmentSelect.selectOption(value);
    await this.page.waitForTimeout(1000);
  }

  /** Select a project by option value; waits 1000ms for cascade to settle */
  async selectProject(value: string): Promise<void> {
    await this.projectSelect.selectOption(value);
    await this.page.waitForTimeout(1000);
  }

  /** Click the Reset button and wait 500ms for filters to clear */
  async clickReset(): Promise<void> {
    await this.resetBtn.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Returns all sub-segment option values (excludes the "All Sub-Segments" placeholder).
   * Values are the numeric segment IDs rendered as option value="{id}".
   */
  async getSubSegmentOptions(): Promise<string[]> {
    const opts = await this.subSegmentSelect.locator('option').all();
    const values: string[] = [];
    for (const opt of opts) {
      const val = await opt.getAttribute('value');
      if (val && val !== '') values.push(val);
    }
    return values;
  }

  /**
   * Returns all project option values (excludes the "All Projects" placeholder).
   */
  async getProjectOptions(): Promise<string[]> {
    const opts = await this.projectSelect.locator('option').all();
    const values: string[] = [];
    for (const opt of opts) {
      const val = await opt.getAttribute('value');
      if (val && val !== '') values.push(val);
    }
    return values;
  }
}
