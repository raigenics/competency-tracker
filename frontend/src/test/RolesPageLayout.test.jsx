/**
 * RolesPage Layout Regression Tests
 * 
 * Verifies that Role Catalog page does NOT create nested scrolling:
 * 1. Page container should NOT have height: 100% that constrains layout
 * 2. details-panel should have overflow: visible (not hidden)
 * 3. details-content should have overflow-y: visible (not auto)
 * 
 * The fix ensures only browser/page scroll is used, not a nested inner scroll.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Read source file for static analysis
const rolesPageSource = readFileSync(
  resolve(__dirname, '../pages/MasterData/RolesPage.jsx'),
  'utf-8'
);

describe('RolesPage Layout - No Nested Scrollbar', () => {
  
  describe('Page Container Styling', () => {
    it('should have data-page="role-catalog" attribute for identification', () => {
      expect(rolesPageSource).toContain('data-page="role-catalog"');
    });

    it('should NOT constrain height to 100% (allows natural content expansion)', () => {
      // The master-data-page container should have height: auto, not height: 100%
      expect(rolesPageSource).toContain("height: 'auto'");
      expect(rolesPageSource).toContain("minHeight: '100%'");
    });

    it('should override details-panel overflow to visible', () => {
      // details-panel CSS has overflow: hidden, but we override inline
      expect(rolesPageSource).toContain("overflow: 'visible'");
    });

    it('should override details-content overflow-y to visible', () => {
      // details-content CSS has overflow-y: auto, but we override inline
      expect(rolesPageSource).toContain("overflowY: 'visible'");
    });
  });

  describe('Scrolling Behavior', () => {
    it('should NOT have nested overflow-y: auto on details-content (inline override present)', () => {
      // Verify the inline style overrides the CSS overflow-y: auto
      // The presence of overflowY: 'visible' confirms no nested scroll
      const detailsContentMatch = rolesPageSource.match(
        /className="details-content"[^>]*style=\{[^}]*overflowY:\s*['"]visible['"]/
      );
      expect(detailsContentMatch).not.toBeNull();
    });
  });
});
