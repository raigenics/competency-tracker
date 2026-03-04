/**
 * MainLayout and AppShell Regression Tests
 * 
 * Phase 2 tests to verify:
 * 1. MainLayout root uses h-screen (not min-h-screen)
 * 2. MainLayout <main> retains overflow-y-auto for scroll containment
 * 3. Sidebar no longer uses height: 100vh (uses 100% instead)
 * 4. Routes render correctly inside MainLayout
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
const __dirname = dirname(fileURLToPath(import.meta.url));
import MainLayout from '@/layouts/MainLayout.jsx';

// Read source files for static analysis
const mainLayoutSource = readFileSync(
  resolve(__dirname, '../layouts/MainLayout.jsx'),
  'utf-8'
);

const sidebarCssSource = readFileSync(
  resolve(__dirname, '../styles/sidebar.css'),
  'utf-8'
);

describe('AppShell Height Model - Phase 2 Regression', () => {
  
  // =========================================================================
  // 1) MainLayout Root Height Model
  // =========================================================================
  describe('MainLayout Root Element', () => {
    it('should use h-screen (not min-h-screen) for fixed viewport height', () => {
      // MainLayout root should use h-screen for fixed viewport framing
      expect(mainLayoutSource).toContain('className="flex h-screen');
      expect(mainLayoutSource).not.toContain('min-h-screen');
    });

    it('should have overflow-y-auto on main content area', () => {
      expect(mainLayoutSource).toContain('overflow-y-auto');
    });

    it('should render main element with flex-1', () => {
      expect(mainLayoutSource).toContain('flex-1');
    });
  });

  // =========================================================================
  // 2) Sidebar Height Model
  // =========================================================================
  describe('Sidebar CSS', () => {
    it('should use height: 100% (not 100vh) to follow parent', () => {
      // Sidebar should inherit height from parent, not set its own 100vh
      expect(sidebarCssSource).toContain('height: 100%');
      expect(sidebarCssSource).not.toMatch(/height:\s*100vh/);
    });

    it('should have overflow: auto on nav element', () => {
      // Sidebar nav should scroll internally if needed
      expect(sidebarCssSource).toMatch(/\.nav\s*\{[^}]*overflow:\s*auto/);
    });
  });

  // =========================================================================
  // 3) MainLayout Renders Correctly
  // =========================================================================
  describe('MainLayout Component Rendering', () => {
    it('should render Sidebar and Outlet', () => {
      const TestPage = () => <div data-testid="test-page">Test Page Content</div>;
      
      render(
        <MemoryRouter initialEntries={['/test']}>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/test" element={<TestPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Test page should render inside MainLayout
      expect(screen.getByTestId('test-page')).toBeInTheDocument();
      
      // Sidebar brand should be present (proves Sidebar rendered)
      expect(screen.getByText('CompetencyIQ')).toBeInTheDocument();
    });

    it('should render main element with correct scroll classes', () => {
      const TestPage = () => <div>Test</div>;
      
      const { container } = render(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/" element={<TestPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      const mainElement = container.querySelector('main');
      expect(mainElement).toBeInTheDocument();
      expect(mainElement).toHaveClass('flex-1');
      expect(mainElement).toHaveClass('overflow-y-auto');
    });
  });

  // =========================================================================
  // 4) No Redundant Page Heights
  // =========================================================================
  describe('Page Height Declarations (Regression)', () => {
    const pageSources = {
      'EmployeeManagement': readFileSync(
        resolve(__dirname, '../pages/Employees/EmployeeManagement.jsx'),
        'utf-8'
      ),
      'BulkImportPage': readFileSync(
        resolve(__dirname, '../pages/BulkImport/BulkImportPage.jsx'),
        'utf-8'
      ),
      'RbacAdminPage': readFileSync(
        resolve(__dirname, '../pages/RbacAdmin/RbacAdminPage.jsx'),
        'utf-8'
      ),
      'ComparisonPage': readFileSync(
        resolve(__dirname, '../pages/Comparison/ComparisonPage.jsx'),
        'utf-8'
      ),
    };

    Object.entries(pageSources).forEach(([pageName, source]) => {
      it(`${pageName} should NOT use min-h-screen in root wrapper`, () => {
        // Pages should not declare min-h-screen as MainLayout owns height
        expect(source).not.toMatch(/className="[^"]*min-h-screen[^"]*"/);
      });
    });

    const cssSources = {
      'Dashboard.css': readFileSync(
        resolve(__dirname, '../pages/Dashboard/Dashboard.css'),
        'utf-8'
      ),
      'CapabilityOverview.css': readFileSync(
        resolve(__dirname, '../pages/Taxonomy/CapabilityOverview.css'),
        'utf-8'
      ),
      'CapabilityFinder.css': readFileSync(
        resolve(__dirname, '../pages/AdvancedQuery/CapabilityFinder.css'),
        'utf-8'
      ),
      'EmployeeProfile.css': readFileSync(
        resolve(__dirname, '../pages/Profile/EmployeeProfile.css'),
        'utf-8'
      ),
    };

    Object.entries(cssSources).forEach(([cssFile, source]) => {
      it(`${cssFile} should NOT use min-height: 100vh`, () => {
        // CSS files should not declare min-height: 100vh
        expect(source).not.toMatch(/^\s*min-height:\s*100vh/m);
      });
    });
  });
});
