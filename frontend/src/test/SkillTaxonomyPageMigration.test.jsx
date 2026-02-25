/**
 * Regression tests for SkillTaxonomyPage TwoPaneLayout Migration
 * 
 * These tests verify at the SOURCE CODE level that:
 * 1. The hardcoded calc(100vh - 340px) magic height is removed
 * 2. The page imports and uses TwoPaneLayout
 * 3. The co-grid class is no longer used
 * 
 * We check source code directly rather than rendering, because:
 * - No complex API/store mocking required
 * - Faster and more reliable
 * - Direct verification of the actual migration goal
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
const __dirname = dirname(fileURLToPath(import.meta.url));

// Read the source file
const sourceFile = resolve(__dirname, '../pages/Taxonomy/SkillTaxonomyPage.jsx');
const sourceCode = readFileSync(sourceFile, 'utf-8');

describe('SkillTaxonomyPage - TwoPaneLayout Migration Regression', () => {
  
  // =========================================================================
  // 1) Magic Height Removal Verification
  // =========================================================================
  describe('Magic Height Removal (Regression)', () => {
    it('should NOT contain calc(100vh - 340px) magic height hack', () => {
      // The old hardcoded value should not be present
      expect(sourceCode).not.toContain('calc(100vh - 340px)');
      expect(sourceCode).not.toContain('calc(100vh-340px)'); // Also check without spaces
    });

    it('should NOT use inline maxHeight style with calc', () => {
      // Check that we're not using the old inline style pattern
      // Old pattern was: style={{ maxHeight: 'calc(100vh - 340px)', overflowY: 'auto' }}
      expect(sourceCode).not.toMatch(/style=\{\{.*maxHeight:\s*['"]calc\(100vh/);
    });
  });

  // =========================================================================
  // 2) TwoPaneLayout Import Verification
  // =========================================================================
  describe('TwoPaneLayout Integration', () => {
    it('should import TwoPaneLayout component', () => {
      expect(sourceCode).toContain("import TwoPaneLayout from '../../layouts/TwoPaneLayout");
    });

    it('should use TwoPaneLayout component in JSX', () => {
      expect(sourceCode).toContain('<TwoPaneLayout');
    });

    it('should pass leftPane prop to TwoPaneLayout', () => {
      expect(sourceCode).toMatch(/leftPane\s*=\s*\{/);
    });

    it('should pass rightPane prop to TwoPaneLayout', () => {
      expect(sourceCode).toMatch(/rightPane\s*=\s*\{/);
    });
  });

  // =========================================================================
  // 3) Old Pattern Removal Verification
  // =========================================================================
  describe('Old co-grid Pattern Removal', () => {
    it('should NOT use co-grid class (old two-column layout)', () => {
      // The old pattern was: <div className="co-grid">
      // This should be replaced by TwoPaneLayout
      expect(sourceCode).not.toMatch(/className=["'][^"']*co-grid[^"']*["']/);
    });
  });

  // =========================================================================
  // 4) Layout Props Configuration
  // =========================================================================
  describe('TwoPaneLayout Configuration', () => {
    it('should configure left pane width (~520px)', () => {
      // SkillTaxonomyPage should configure the left pane width
      expect(sourceCode).toMatch(/leftWidth\s*=\s*["']520px["']/);
    });

    it('should enable left pane scrolling', () => {
      expect(sourceCode).toMatch(/leftScrollable\s*=?\s*\{?\s*true\s*\}?/);
    });

    it('should include left header slot', () => {
      expect(sourceCode).toMatch(/leftHeader\s*=\s*\{/);
    });
  });
});
