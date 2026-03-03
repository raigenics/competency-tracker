// Module: sidebar.page.ts
// Purpose: Page object for shared sidebar navigation component
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Sidebar Page Object
 * 
 * Represents the main sidebar navigation component shared across all pages.
 * Route: n/a (shared component)
 * 
 * Key data-testid selectors:
 * - sidebar-container: Main sidebar wrapper
 * - sidebar-logo: Application logo
 * - nav-dashboard: Dashboard nav link
 * - nav-skill-coverage: Skill Coverage nav link
 * - nav-talent-finder: Talent Finder nav link
 * - nav-profile: Employee Directory nav link
 * - nav-employees: Employee Management nav link
 * - nav-import: Import Data nav link
 * - nav-skill-library: Skill Library nav link
 * - nav-org-structure: Org Structure nav link
 * - nav-role-catalog: Role Catalog nav link
 * - sidebar-collapse-btn: Collapse/expand button
 */
export default class SidebarPage {
  readonly page: Page;
  readonly container: Locator;
  readonly logo: Locator;
  readonly dashboardLink: Locator;
  readonly skillCoverageLink: Locator;
  readonly talentFinderLink: Locator;
  readonly profileLink: Locator;
  readonly employeesLink: Locator;
  readonly importLink: Locator;
  readonly skillLibraryLink: Locator;
  readonly orgStructureLink: Locator;
  readonly roleCatalogLink: Locator;
  readonly collapseButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.container = page.getByTestId('sidebar-container');
    this.logo = page.getByTestId('sidebar-logo');
    this.dashboardLink = page.getByTestId('nav-dashboard');
    this.skillCoverageLink = page.getByTestId('nav-skill-coverage');
    this.talentFinderLink = page.getByTestId('nav-talent-finder');
    this.profileLink = page.getByTestId('nav-profile');
    this.employeesLink = page.getByTestId('nav-employees');
    this.importLink = page.getByTestId('nav-import');
    this.skillLibraryLink = page.getByTestId('nav-skill-library');
    this.orgStructureLink = page.getByTestId('nav-org-structure');
    this.roleCatalogLink = page.getByTestId('nav-role-catalog');
    this.collapseButton = page.getByTestId('sidebar-collapse-btn');
  }

  /**
   * Navigate to Dashboard via sidebar
   */
  async navigateToDashboard(): Promise<void> {
    await this.dashboardLink.click();
    await this.page.waitForURL('**/dashboard');
  }

  /**
   * Navigate to Skill Coverage via sidebar
   */
  async navigateToSkillCoverage(): Promise<void> {
    await this.skillCoverageLink.click();
    await this.page.waitForURL('**/skill-coverage');
  }

  /**
   * Navigate to Talent Finder via sidebar
   */
  async navigateToTalentFinder(): Promise<void> {
    await this.talentFinderLink.click();
    await this.page.waitForURL('**/talent-finder');
  }

  /**
   * Navigate to Employee Directory via sidebar
   */
  async navigateToProfile(): Promise<void> {
    await this.profileLink.click();
    await this.page.waitForURL('**/profile');
  }

  /**
   * Navigate to Employee Management via sidebar
   */
  async navigateToEmployees(): Promise<void> {
    await this.employeesLink.click();
    await this.page.waitForURL('**/employees');
  }

  /**
   * Navigate to Import Data via sidebar
   */
  async navigateToImport(): Promise<void> {
    await this.importLink.click();
    await this.page.waitForURL('**/system/import');
  }

  /**
   * Navigate to Skill Library via sidebar
   */
  async navigateToSkillLibrary(): Promise<void> {
    await this.skillLibraryLink.click();
    await this.page.waitForURL('**/governance/skill-library');
  }

  /**
   * Navigate to Org Structure via sidebar
   */
  async navigateToOrgStructure(): Promise<void> {
    await this.orgStructureLink.click();
    await this.page.waitForURL('**/governance/org-structure');
  }

  /**
   * Navigate to Role Catalog via sidebar
   */
  async navigateToRoleCatalog(): Promise<void> {
    await this.roleCatalogLink.click();
    await this.page.waitForURL('**/governance/role-catalog');
  }

  /**
   * Collapse or expand the sidebar
   */
  async toggleCollapse(): Promise<void> {
    await this.collapseButton.click();
  }

  /**
   * Check if sidebar is collapsed
   */
  async isCollapsed(): Promise<boolean> {
    // TODO: Implement based on actual collapsed state indicator
    return false;
  }
}
