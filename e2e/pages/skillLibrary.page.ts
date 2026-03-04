// Module: skillLibrary.page.ts
// Purpose: Page object for Skill Library (Governance) module
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Skill Library Page Object
 *
 * Route: /governance/skill-library   (routes.jsx line 66)
 *
 * Two-panel layout — SkillLibraryPage.jsx renders:
 *   <div className="skill-library">
 *     <section className="sl-card">          ← LEFT  tree panel
 *       <div className="sl-tree"> ... </div> ← tree container
 *     </section>
 *     <section className="sl-card sl-panel"> ← RIGHT details panel
 *       ...
 *     </section>
 *   </div>
 *
 * Tree nodes (renderTree):
 *   <div className="sl-node [selected]">   ← category row
 *     <span className="sl-caret">          ← expand/collapse toggle
 *     <span className="sl-label">          ← text label
 *   <div className="sl-subnode [selected]"> ← sub-category row
 *     <span className="sl-label">
 *
 * Category/Sub-category badge in details header:
 *   <span className="sl-pill">CATEGORY</span>
 *   <span className="sl-pill">SUB-CATEGORY</span>
 *
 * Modals (CreateEditModal / DeleteConfirmModal):
 *   render <div className="modal-overlay active"> when isOpen=true
 *   return null when isOpen=false
 *   Save   → <button className="btn btn-primary">
 *   Cancel → <button className="btn btn-secondary">
 *   Delete → <button className="btn btn-danger">
 */
export default class SkillLibraryPage {
  readonly page: Page;

  // ── Layout ─────────────────────────────────────────────────────────────────
  /** Left tree panel: <section className="sl-card"> (first, no sl-panel modifier) */
  readonly treePanel: Locator;
  /** Scrollable tree list container: <div className="sl-tree"> */
  readonly treeContent: Locator;
  /** Right details panel: <section className="sl-card sl-panel"> */
  readonly detailsPanel: Locator;

  // ── Tree controls ───────────────────────────────────────────────────────────
  /** "+ Add Category" button in PageHeader actions: <button className="sl-btn"> */
  readonly addCategoryBtn: Locator;
  /** Tree search: placeholder="Search categories or sub-categories..." */
  readonly treeSearchInput: Locator;

  // ── Details — category / sub-category badge ─────────────────────────────────
  /** <span className="sl-pill"> — shows "CATEGORY" or "SUB-CATEGORY" */
  readonly categoryBadge: Locator;

  // ── Details — sub-category / skills table ───────────────────────────────────
  /** SkillsTable renders <table className="skills-table"> */
  readonly skillsTable: Locator;
  readonly skillRows: Locator;
  /** "+ Add Skill" button: <button className="sl-btn subtle"> */
  readonly addSkillBtn: Locator;
  /** skill search: placeholder="Search skills..." */
  readonly skillSearchInput: Locator;

  // ── AddSkillRow inline (AddSkillRow.jsx) ────────────────────────────────────
  readonly addSkillNameInput: Locator;
  readonly addSkillAliasInput: Locator;
  readonly skillSaveBtn: Locator;
  readonly skillCancelBtn: Locator;

  // ── Modal (CreateEditModal / DeleteConfirmModal) ─────────────────────────────
  readonly modal: Locator;
  readonly modalNameInput: Locator;
  readonly modalSaveBtn: Locator;
  readonly modalCancelBtn: Locator;
  readonly modalDeleteBtn: Locator;

  // ── Misc ────────────────────────────────────────────────────────────────────
  /** Root page wrapper used as an existence sentinel: <div className="skill-library"> */
  readonly loadingContainer: Locator;

  constructor(page: Page) {
    this.page = page;

    // LEFT panel is the only .sl-card without the extra .sl-panel modifier
    this.treePanel    = page.locator('.sl-card:not(.sl-panel)');
    this.treeContent  = page.locator('.sl-tree');
    // RIGHT panel always has both classes
    this.detailsPanel = page.locator('.sl-card.sl-panel');

    // "+ Add Category" button lives in PageHeader actions outside either panel
    this.addCategoryBtn  = page.locator('button.sl-btn:has-text("+ Add Category")');
    // placeholder confirmed: SkillLibraryPage.jsx line ~1893
    this.treeSearchInput = page.locator('input[placeholder="Search categories or sub-categories..."]');

    // .sl-pill renders "CATEGORY" or "SUB-CATEGORY" depending on selection
    this.categoryBadge = page.locator('.sl-pill');

    // MasterData SkillsTable.jsx line 227: <table className="skills-table">
    this.skillsTable      = page.locator('.skills-table');
    this.skillRows        = page.locator('.skills-table tbody tr');
    // SkillLibraryPage.jsx renderSubcategoryPanel: <button className="sl-btn subtle">
    this.addSkillBtn      = page.locator('button.sl-btn:has-text("+ Add Skill")');
    this.skillSearchInput = page.locator('input[placeholder="Search skills..."]');

    // AddSkillRow.jsx placeholders (lines 91, 100) and button classes (lines 105, 109)
    this.addSkillNameInput  = page.locator('input[placeholder="Enter skill name"]');
    this.addSkillAliasInput = page.locator('input[placeholder="Comma-separated aliases"]');
    this.skillSaveBtn       = page.locator('button.btn-save');
    this.skillCancelBtn     = page.locator('button.btn-cancel');

    // Modals always rendered with class "modal-overlay active"; removed from DOM when closed
    this.modal          = page.locator('.modal-overlay.active');
    this.modalNameInput = page.locator('.modal-overlay.active .form-input');
    // CreateEditModal line 177: <button className="btn btn-primary">
    this.modalSaveBtn   = page.locator('.modal-overlay.active .btn.btn-primary');
    // CreateEditModal line 176: <button className="btn btn-secondary">
    this.modalCancelBtn = page.locator('.modal-overlay.active .btn.btn-secondary');
    // DeleteConfirmModal line 36: <button className="btn btn-danger">
    this.modalDeleteBtn = page.locator('.modal-overlay.active .btn.btn-danger');

    // Root wrapper always present once React mounts the page
    this.loadingContainer = page.locator('.skill-library');
  }

  /**
   * Navigate to the Skill Library page.
   * Waits for the tree container (.sl-tree) which is always rendered
   * regardless of loading/error state.
   * routes.jsx line 66: path: "governance/skill-library"
   */
  async navigate(): Promise<void> {
    await this.page.goto('/governance/skill-library');
    await this.page.waitForSelector('.sl-tree', {
      state: 'visible',
      timeout: 20000,
    });
  }

  /**
   * Wait for at least one category node (.sl-node) to appear in the tree.
   * The loading state is inline text with no CSS class, so we cannot wait
   * for a loader to hide — we simply wait for data to arrive.
   */
  async waitForTreeLoad(): Promise<void> {
    await this.page.waitForSelector('.sl-node', {
      state: 'visible',
      timeout: 20000,
    });
  }

  /** Click a tree item by visible text label, then pause 500 ms.
   *  Categories render as .sl-node, sub-categories as .sl-subnode. */
  async clickTreeNode(name: string): Promise<void> {
    await this.page.locator('.sl-node, .sl-subnode').filter({ hasText: name }).click();
    await this.page.waitForTimeout(500);
  }

  /** Click the "+ Category" button and wait for the modal to become active */
  async openCreateModal(): Promise<void> {
    await this.addCategoryBtn.click();
    await this.modal.waitFor({ state: 'visible' });
  }

  /** Type a name into the active modal's name input */
  async fillModalName(name: string): Promise<void> {
    await this.modalNameInput.fill(name);
  }

  /** Click Save in the active modal and wait for it to close */
  async saveModal(): Promise<void> {
    await this.modalSaveBtn.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  /** Click "+ Add Skill" button and wait for the inline name input to appear */
  async clickAddSkill(): Promise<void> {
    await this.addSkillBtn.click();
    await this.addSkillNameInput.waitFor({ state: 'visible' });
  }

  /** Fill the inline add-skill form (alias is optional) */
  async fillAddSkillForm(name: string, alias?: string): Promise<void> {
    await this.addSkillNameInput.fill(name);
    if (alias) {
      await this.addSkillAliasInput.fill(alias);
    }
  }

  /** Click the Save button in the inline add-skill row and wait for that row to disappear */
  async saveSkillForm(): Promise<void> {
    await this.skillSaveBtn.click();
    await this.page.locator('tr.add-skill-row').waitFor({ state: 'hidden' });
  }

  /** Click the Cancel button in the inline add-skill row */
  async cancelSkillForm(): Promise<void> {
    await this.skillCancelBtn.click();
  }

  /** Count visible skill rows in the skills table */
  async getSkillRowCount(): Promise<number> {
    return await this.skillRows.count();
  }

  /** Return a locator for the skills-table row whose text contains `name` */
  findSkillByName(name: string): Locator {
    return this.page.locator('.skills-table tbody tr').filter({ hasText: name });
  }

  /** Fill the tree search box and wait for the 300 ms debounce + render */
  async searchTree(query: string): Promise<void> {
    await this.treeSearchInput.fill(query);
    await this.page.waitForTimeout(500);
  }

  /** Clear the tree search box and wait for results to reset */
  async clearTreeSearch(): Promise<void> {
    await this.treeSearchInput.fill('');
    await this.page.waitForTimeout(500);
  }
}
