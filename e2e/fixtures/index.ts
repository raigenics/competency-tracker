// Module: index.ts
// Purpose: Extended Playwright fixtures with page objects and authenticated context
// Part of: CompetencyIQ E2E Automation Suite

import { test as base, expect, Page } from '@playwright/test';

// Page Objects
import DashboardPage from '../pages/dashboard.page';
import SkillCoveragePage from '../pages/skillCoverage.page';
import TalentFinderPage from '../pages/talentFinder.page';
import EmployeeDirectoryPage from '../pages/employeeDirectory.page';
import EmployeeManagementPage from '../pages/employeeManagement.page';
import ImportDataPage from '../pages/importData.page';
import SkillLibraryPage from '../pages/skillLibrary.page';
import OrgStructurePage from '../pages/orgStructure.page';
import RoleCatalogPage from '../pages/roleCatalog.page';
import SidebarPage from '../pages/sidebar.page';

/**
 * Type definitions for custom fixtures
 */
type CustomFixtures = {
  /** Pre-authenticated page fixture */
  authenticatedPage: Page;
  
  /** Dashboard page object */
  dashboardPage: DashboardPage;
  
  /** Skill Coverage page object */
  skillCoveragePage: SkillCoveragePage;
  
  /** Talent Finder page object */
  talentFinderPage: TalentFinderPage;
  
  /** Employee Directory (Profile) page object */
  employeeDirectoryPage: EmployeeDirectoryPage;
  
  /** Employee Management page object */
  employeeManagementPage: EmployeeManagementPage;
  
  /** Import Data page object */
  importDataPage: ImportDataPage;
  
  /** Skill Library page object */
  skillLibraryPage: SkillLibraryPage;
  
  /** Org Structure page object */
  orgStructurePage: OrgStructurePage;
  
  /** Role Catalog page object */
  roleCatalogPage: RoleCatalogPage;
  
  /** Sidebar navigation page object */
  sidebarPage: SidebarPage;
};

/**
 * Extended Playwright test with custom fixtures
 * 
 * Usage:
 * ```typescript
 * import { test, expect } from '../fixtures';
 * 
 * test('example test', async ({ dashboardPage }) => {
 *   await dashboardPage.navigate();
 *   await expect(dashboardPage.container).toBeVisible();
 * });
 * ```
 */
export const test = base.extend<CustomFixtures>({
  /**
   * Pre-authenticated page fixture
   * Uses stored auth state from global-setup
   */
  authenticatedPage: async ({ page }, use) => {
    // Auth state is automatically loaded from storageState in playwright.config.ts
    // This fixture ensures we have a page with auth context
    await use(page);
  },

  /**
   * Dashboard page object fixture
   */
  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },

  /**
   * Skill Coverage page object fixture
   */
  skillCoveragePage: async ({ page }, use) => {
    const skillCoveragePage = new SkillCoveragePage(page);
    await use(skillCoveragePage);
  },

  /**
   * Talent Finder page object fixture
   */
  talentFinderPage: async ({ page }, use) => {
    const talentFinderPage = new TalentFinderPage(page);
    await use(talentFinderPage);
  },

  /**
   * Employee Directory page object fixture
   */
  employeeDirectoryPage: async ({ page }, use) => {
    const employeeDirectoryPage = new EmployeeDirectoryPage(page);
    await use(employeeDirectoryPage);
  },

  /**
   * Employee Management page object fixture
   */
  employeeManagementPage: async ({ page }, use) => {
    const employeeManagementPage = new EmployeeManagementPage(page);
    await use(employeeManagementPage);
  },

  /**
   * Import Data page object fixture
   */
  importDataPage: async ({ page }, use) => {
    const importDataPage = new ImportDataPage(page);
    await use(importDataPage);
  },

  /**
   * Skill Library page object fixture
   */
  skillLibraryPage: async ({ page }, use) => {
    const skillLibraryPage = new SkillLibraryPage(page);
    await use(skillLibraryPage);
  },

  /**
   * Org Structure page object fixture
   */
  orgStructurePage: async ({ page }, use) => {
    const orgStructurePage = new OrgStructurePage(page);
    await use(orgStructurePage);
  },

  /**
   * Role Catalog page object fixture
   */
  roleCatalogPage: async ({ page }, use) => {
    const roleCatalogPage = new RoleCatalogPage(page);
    await use(roleCatalogPage);
  },

  /**
   * Sidebar navigation page object fixture
   */
  sidebarPage: async ({ page }, use) => {
    const sidebarPage = new SidebarPage(page);
    await use(sidebarPage);
  },
});
Object.assign(test, base);

// Re-export expect from Playwright for convenience
export { expect };
export default test;
