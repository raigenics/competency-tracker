// Module: cascadingFilters.helper.ts
// Purpose: Cascading dropdown pattern: SubSegment → Project → Team
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Cascading Filters Helper
 * 
 * Provides reusable methods for interacting with the cascading filter pattern
 * used throughout the application: SubSegment → Project → Team
 * 
 * The cascade behavior:
 * - Selecting a SubSegment populates Project dropdown with relevant projects
 * - Selecting a Project populates Team dropdown with relevant teams
 * - Clearing a parent filter clears all child filters
 */
export class CascadingFiltersHelper {
  readonly page: Page;
  readonly container: Locator;
  readonly subSegmentDropdown: Locator;
  readonly projectDropdown: Locator;
  readonly teamDropdown: Locator;
  readonly clearAllButton: Locator;

  /**
   * Create a new CascadingFiltersHelper instance
   * @param page - Playwright Page object
   * @param containerTestId - data-testid of the filters container (optional)
   */
  constructor(page: Page, containerTestId?: string) {
    this.page = page;
    this.container = containerTestId 
      ? page.getByTestId(containerTestId) 
      : page.locator('body');
    this.subSegmentDropdown = this.container.getByTestId('filter-subsegment');
    this.projectDropdown = this.container.getByTestId('filter-project');
    this.teamDropdown = this.container.getByTestId('filter-team');
    this.clearAllButton = this.container.getByTestId('clear-filters-btn');
  }

  /**
   * Select a sub-segment from the dropdown
   * @param name - Sub-segment name to select
   */
  async selectSubSegment(name: string): Promise<void> {
    await this.subSegmentDropdown.click();
    await this.page.getByRole('option', { name }).click();
    // Wait for project dropdown to be populated
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Select a project from the dropdown
   * @param name - Project name to select
   */
  async selectProject(name: string): Promise<void> {
    await this.projectDropdown.click();
    await this.page.getByRole('option', { name }).click();
    // Wait for team dropdown to be populated
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Select a team from the dropdown
   * @param name - Team name to select
   */
  async selectTeam(name: string): Promise<void> {
    await this.teamDropdown.click();
    await this.page.getByRole('option', { name }).click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Clear all filter selections
   */
  async clearAll(): Promise<void> {
    await this.clearAllButton.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get currently selected sub-segment value
   */
  async getSelectedSubSegment(): Promise<string> {
    return await this.subSegmentDropdown.inputValue();
  }

  /**
   * Get currently selected project value
   */
  async getSelectedProject(): Promise<string> {
    return await this.projectDropdown.inputValue();
  }

  /**
   * Get currently selected team value
   */
  async getSelectedTeam(): Promise<string> {
    return await this.teamDropdown.inputValue();
  }

  /**
   * Check if project dropdown is enabled (has options)
   */
  async isProjectDropdownEnabled(): Promise<boolean> {
    return await this.projectDropdown.isEnabled();
  }

  /**
   * Check if team dropdown is enabled (has options)
   */
  async isTeamDropdownEnabled(): Promise<boolean> {
    return await this.teamDropdown.isEnabled();
  }

  /**
   * Select full cascade: SubSegment → Project → Team
   * @param subSegment - Sub-segment name
   * @param project - Project name
   * @param team - Team name
   */
  async selectFullCascade(
    subSegment: string, 
    project: string, 
    team: string
  ): Promise<void> {
    await this.selectSubSegment(subSegment);
    await this.selectProject(project);
    await this.selectTeam(team);
  }

  /**
   * Get count of options in a dropdown
   * @param dropdown - The dropdown locator
   */
  async getOptionCount(dropdown: Locator): Promise<number> {
    await dropdown.click();
    const options = this.page.getByRole('option');
    const count = await options.count();
    await this.page.keyboard.press('Escape'); // Close dropdown
    return count;
  }
}

export default CascadingFiltersHelper;
