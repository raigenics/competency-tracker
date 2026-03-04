// Module: dashboard.spec.ts
// Purpose: Smoke tests for Dashboard module - critical path validation
// Part of: CompetencyIQ E2E Automation Suite

import { test, expect } from '@playwright/test';
import DashboardPage from '../../pages/dashboard.page';

/**
 * Dashboard Smoke Tests
 *
 * @tags @smoke @insights
 *
 * Read-only page — zero CRUD, no modals, no test data lifecycle needed.
 *
 * The dashboard renders one of two mutually exclusive states:
 *
 *   DATA STATE  (.db-grid visible)
 *     Shown when segment_id=1 has sub-segments AND employees in scope.
 *     Contains: Dashboard Context Filters (.db-filters-card), KPI row (.db-kpis),
 *     SkillDistributionTable, SkillUpdateActivity, RoleDistribution.
 *
 *   EMPTY STATE (.empty-content visible)
 *     Shown when segment_id=1 has no sub-segments OR totalEmployees===0.
 *     Contains: setup checklist, action buttons, scope banner.
 *
 * DESIGN PRINCIPLE:
 *   Every test handles BOTH states. Tests 2-6 gracefully skip when in empty
 *   state (filters/KPIs simply don't exist). Test 7 covers the empty state
 *   explicitly but also passes in data state.
 */
test.describe('Dashboard - Smoke Tests @smoke @insights', () => {

  // ── TEST 1 ────────────────────────────────────────────────────────────────
  test('should load dashboard page successfully', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.navigate();
    await dashboard.waitForLoad();

    await expect(dashboard.pageRoot).toBeVisible();
    await expect(page).toHaveURL(/\/dashboard/);
    // PageHeader renders <h1 className="page-title">Dashboard</h1>
    await expect(page.locator('h1.page-title')).toContainText('Dashboard');

    const dataVisible  = await dashboard.isDataState();
    const emptyVisible = await dashboard.isEmptyState();
    expect(dataVisible || emptyVisible).toBe(true);

    console.log('Dashboard state:', dataVisible ? 'DATA' : 'EMPTY');
  });

  // ── TEST 2 ────────────────────────────────────────────────────────────────
  test('should render context filters when data is present', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.navigate();
    await dashboard.waitForLoad();

    if (await dashboard.isEmptyState()) {
      test.skip();
      return;
    }

    await expect(dashboard.filtersCard).toBeVisible();
    await expect(page.locator('.db-filters-card')).toContainText('Dashboard Context Filters');
    await expect(dashboard.subSegmentSelect).toBeVisible();
    await expect(dashboard.projectSelect).toBeVisible();
    await expect(dashboard.teamSelect).toBeVisible();
    await expect(dashboard.resetBtn).toBeVisible();
    await expect(dashboard.scopeTag).toBeVisible();
  });

  // ── TEST 3 ────────────────────────────────────────────────────────────────
  test('should show KPI cards when data is present', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.navigate();
    await dashboard.waitForLoad();

    if (await dashboard.isEmptyState()) {
      test.skip();
      return;
    }

    await expect(dashboard.kpiSection).toBeVisible();
    expect(await dashboard.kpiCards.count()).toBeGreaterThanOrEqual(1);
    // KPI labels from DashboardPage.jsx lines 649, 659
    await expect(page.locator('.db-kpis')).toContainText('Employees in Scope');
    await expect(page.locator('.db-kpis')).toContainText('Data Freshness');
  });

  // ── TEST 4 ────────────────────────────────────────────────────────────────
  test('should populate sub-segment dropdown with options', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.navigate();
    await dashboard.waitForLoad();

    if (await dashboard.isEmptyState()) {
      test.skip();
      return;
    }

    await dashboard.waitForFiltersReady();

    const options = await dashboard.getSubSegmentOptions();
    expect(options.length).toBeGreaterThan(0);

    console.log('Sub-segment options:', options);
  });

  // ── TEST 5 ────────────────────────────────────────────────────────────────
  test('should cascade project dropdown when sub-segment selected', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.navigate();
    await dashboard.waitForLoad();

    if (await dashboard.isEmptyState()) {
      test.skip();
      return;
    }

    await dashboard.waitForFiltersReady();

    // Project select is disabled when no sub-segment is chosen
    // DashboardPage.jsx: disabled={loading || !dashboardFilters.subSegment || ...}
    await expect(dashboard.projectSelect).toBeDisabled();

    const subSegOptions = await dashboard.getSubSegmentOptions();
    if (subSegOptions.length === 0) {
      test.skip();
      return;
    }

    await dashboard.selectSubSegment(subSegOptions[0]);

    // After selection, project select becomes enabled
    await expect(dashboard.projectSelect).not.toBeDisabled();
    await expect(dashboard.scopeTag).toBeVisible();
  });

  // ── TEST 6 ────────────────────────────────────────────────────────────────
  test('should reset filters when Reset button clicked', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.navigate();
    await dashboard.waitForLoad();

    if (await dashboard.isEmptyState()) {
      test.skip();
      return;
    }

    await dashboard.waitForFiltersReady();

    const subSegOptions = await dashboard.getSubSegmentOptions();
    if (subSegOptions.length === 0) {
      test.skip();
      return;
    }

    // Select a sub-segment to enable project dropdown
    await dashboard.selectSubSegment(subSegOptions[0]);
    await page.waitForTimeout(1000);
    await expect(dashboard.projectSelect).not.toBeDisabled();

    // Click Reset — clearFilters() sets subSegment:'', project:'', team:''
    await dashboard.clickReset();
    await page.waitForTimeout(500);

    // After reset: project is disabled again and sub-segment value is ''
    await expect(dashboard.projectSelect).toBeDisabled();
    await expect(dashboard.subSegmentSelect).toHaveValue('');
  });

  // ── TEST 7 ────────────────────────────────────────────────────────────────
  test('should render empty state with setup guidance when no data', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.navigate();
    await dashboard.waitForLoad();

    if (await dashboard.isDataState()) {
      // Data state is healthy — verify grid is present and pass
      await expect(dashboard.mainGrid).toBeVisible();
      await expect(dashboard.filtersCard).toBeVisible();
      console.log('Data state healthy — empty state not applicable in this environment');
      return;
    }

    // Empty state assertions
    await expect(dashboard.emptyContent).toBeVisible();
    await expect(dashboard.emptyHeading).toContainText('Your dashboard is ready');
    await expect(dashboard.actionRow).toBeVisible();
    await expect(page.locator('.action-row .btn-primary')).toContainText('Go to Import Data');
    await expect(page.locator('.action-row .btn-secondary')).toContainText('Go to Employee Management');
    await expect(dashboard.checklist).toBeVisible();
  });

});