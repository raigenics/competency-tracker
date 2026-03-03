// Module: orgStructure.page.ts
// Purpose: Page object for Org Structure (Governance) module
// Part of: CompetencyIQ E2E Automation Suite

import { Page, Locator } from '@playwright/test';

/**
 * Org Structure Page Object
 *
 * Route: /governance/org-structure  (routes.jsx line 69)
 *
 * OrgHierarchyPage.jsx layout:
 *   <div className="org-hierarchy">
 *     <section className="oh-content">
 *       <div className="oh-grid">
 *         <section className="oh-card">          ← LEFT  tree panel
 *           <input className="oh-input">         ← search
 *           <div className="oh-tree">            ← tree container
 *             <div className="oh-node [selected]">  ← each tree row
 *               <span className="oh-caret">      ← expand/collapse
 *               <span className="oh-label">     ← text label
 *         <section className="oh-card oh-panel"> ← RIGHT details panel
 *           <div className="oh-panel-header">
 *             <span className="oh-pill">        ← type badge (SEGMENT etc.)
 *             <h2 className="oh-panel-title">   ← item name
 *           <div className="oh-panel-body">
 *             <div className="oh-empty">        ← empty state
 *
 * Add Segment button (PageHeader actions):
 *   <button className="oh-btn">+ Add Segment</button>
 *
 * Loading (in renderPanel when isLoading=true):
 *   <div className="oh-loading"><div className="oh-spinner"></div>
 *
 * Delete button (visible when item selected & not editing):
 *   <button class="oh-iconbtn oh-iconbtn-sm oh-iconbtn-danger"
 *           title="Delete segment">  (or "Delete subsegment" etc.)
 *
 * Modals (CreateEditModal / DeleteConfirmModal):
 *   render <div class="modal-overlay active"> when isOpen=true
 *   return null when closed
 *   Save   → .btn.btn-primary
 *   Cancel → .btn.btn-secondary
 *   Delete → .btn.btn-danger
 */
export default class OrgStructurePage {
  readonly page: Page;

  // ── Layout ─────────────────────────────────────────────────────────────────
  /** Left tree panel: <section className="oh-card"> */
  readonly treePanel: Locator;
  /** Right details panel: <section className="oh-card oh-panel"> */
  readonly detailsPanel: Locator;
  /** Scrollable tree list: <div className="oh-tree"> */
  readonly treeArea: Locator;

  // ── Tree controls ───────────────────────────────────────────────────────────
  /** "+ Add Segment" button in PageHeader: <button className="oh-btn"> */
  readonly addSegmentBtn: Locator;
  /** Tree search box: <input className="oh-input"> */
  readonly treeSearchInput: Locator;

  // ── State indicators ────────────────────────────────────────────────────────
  /** Loading state: <div className="oh-loading"> */
  readonly loadingSpinner: Locator;
  /** Empty state (nothing selected): <div className="oh-empty"> */
  readonly emptyState: Locator;

  // ── Modal (CreateEditModal / DeleteConfirmModal) ─────────────────────────────
  readonly modal: Locator;
  readonly modalNameInput: Locator;
  readonly modalSaveBtn: Locator;
  readonly modalCancelBtn: Locator;
  readonly modalDeleteBtn: Locator;

  constructor(page: Page) {
    this.page = page;

    this.treePanel    = page.locator('.oh-card:not(.oh-panel)');
    this.detailsPanel = page.locator('.oh-card.oh-panel');
    this.treeArea     = page.locator('.oh-tree');

    // "+ Add Segment" in PageHeader actions (global, not inside tree panel)
    this.addSegmentBtn   = page.locator('button.oh-btn:has-text("+ Add Segment")');
    // placeholder confirmed: OrgHierarchyPage.jsx ~line 1604
    this.treeSearchInput = page.locator('input.oh-input');

    this.loadingSpinner = page.locator('.oh-loading');
    this.emptyState     = page.locator('.oh-empty');

    // Modals use same CreateEditModal / DeleteConfirmModal components
    this.modal          = page.locator('.modal-overlay.active');
    this.modalNameInput = page.locator('.modal-overlay.active .form-input');
    this.modalSaveBtn   = page.locator('.modal-overlay.active .btn.btn-primary');
    this.modalCancelBtn = page.locator('.modal-overlay.active .btn.btn-secondary');
    this.modalDeleteBtn = page.locator('.modal-overlay.active .btn.btn-danger');
  }

  /**
   * Navigate to the Org Structure page.
   * Waits for the .oh-grid wrapper (always rendered regardless of loading state).
   * routes.jsx line 69: path: "governance/org-structure"
   */
  async navigate(): Promise<void> {
    await this.page.goto('/governance/org-structure');
    await this.page.waitForSelector('.oh-grid', { state: 'visible', timeout: 20000 });
  }

  /**
   * Wait for the hierarchy data to finish loading.
   * .oh-loading appears in renderPanel() while isLoading=true,
   * then disappears when data arrives and .oh-node rows render.
   */
  async waitForTreeLoad(): Promise<void> {
    try {
      await this.page.waitForSelector('.oh-loading', { state: 'hidden', timeout: 20000 });
    } catch {
      // loader may not appear if data loads fast
    }
    await this.page.waitForSelector('.oh-node', { state: 'visible', timeout: 20000 });
  }

  /** Click a tree node by visible text label, then wait 800 ms for panel to update */
  async clickTreeNode(name: string): Promise<void> {
    await this.page.locator('.oh-node').filter({ hasText: name }).click();
    await this.page.waitForTimeout(800);
  }

  /** Click the expand caret on a tree node to show its children */
  async expandTreeNode(name: string): Promise<void> {
    await this.page.locator('.oh-node').filter({ hasText: name })
      .locator('.oh-caret').click();
  }

  /** Return a locator for a tree node containing the given name */
  findNodeByName(name: string): Locator {
    return this.page.locator('.oh-node').filter({ hasText: name });
  }

  /** Count all currently visible tree nodes */
  async getNodeCount(): Promise<number> {
    return await this.page.locator('.oh-node').count();
  }

  /** Click "+ Add Segment" button and wait for modal to open */
  async openCreateSegmentModal(): Promise<void> {
    await this.addSegmentBtn.click();
    await this.modal.waitFor({ state: 'visible' });
  }

  /** Fill the name input in the active modal */
  async fillModalName(name: string): Promise<void> {
    await this.modalNameInput.fill(name);
  }

  /** Click Save in active modal and wait for it to close */
  async saveModal(): Promise<void> {
    await this.modalSaveBtn.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  /** Click Cancel in active modal and wait for it to close */
  async cancelModal(): Promise<void> {
    await this.modalCancelBtn.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  /** Fill the tree search box and wait for the 300 ms debounce + render */
  async searchTree(query: string): Promise<void> {
    await this.treeSearchInput.fill(query);
    await this.page.waitForTimeout(400);
  }

  /** Clear the tree search box and wait for results to reset */
  async clearSearch(): Promise<void> {
    await this.treeSearchInput.fill('');
    await this.page.waitForTimeout(400);
  }
}
