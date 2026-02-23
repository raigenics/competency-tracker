/**
 * Sidebar Unit Tests
 * ==================
 * Tests for the Sidebar navigation component.
 * 
 * Test coverage:
 * 1. Renders correct sections for each role (viewer/manager/admin/superadmin)
 * 2. Correct active state when route changes
 * 3. Clicking each nav item navigates to the correct route
 * 4. Collapsible sections work correctly
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Use vi.hoisted to create mock state that's available during mock hoisting
const { mockRbacState } = vi.hoisted(() => ({
  mockRbacState: {
    currentRole: 'SUPER_ADMIN'
  }
}));

// Mock featureFlags module
vi.mock('../config/featureFlags', () => ({
  RBAC_CONFIG: {
    get currentRole() {
      return mockRbacState.currentRole;
    }
  },
  RBAC_ROLES: {
    SUPER_ADMIN: 'SUPER_ADMIN',
    SEGMENT_HEAD: 'SEGMENT_HEAD',
    SUBSEGMENT_HEAD: 'SUBSEGMENT_HEAD',
    PROJECT_MANAGER: 'PROJECT_MANAGER',
    TEAM_LEAD: 'TEAM_LEAD',
    TEAM_MEMBER: 'TEAM_MEMBER'
  },
  FEATURE_FLAGS: {
    SHOW_RBAC_ADMIN: false
  }
}));

// Import after mocks are set up
import Sidebar from '../components/Sidebar.jsx';

// Helper to render Sidebar with a specific initial route
const renderSidebar = (initialRoute = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Sidebar />
    </MemoryRouter>
  );
};

describe('Sidebar Component', () => {
  beforeEach(() => {
    // Reset to superadmin by default
    mockRbacState.currentRole = 'SUPER_ADMIN';
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // =========================================
  // Section Visibility Tests (RBAC)
  // =========================================
  describe('Section visibility based on role', () => {
    it('should show Insights, People, and Governance for superadmin (no System section)', () => {
      mockRbacState.currentRole = 'SUPER_ADMIN';
      renderSidebar();

      // Check all sections are visible
      expect(screen.getByText('Insights')).toBeInTheDocument();
      expect(screen.getByText('People')).toBeInTheDocument();
      expect(screen.getByText('Governance')).toBeInTheDocument();
      // System section should NOT exist
      expect(screen.queryByText('System')).not.toBeInTheDocument();
    });

    it('should show Insights, People, Governance for admin (no System)', () => {
      mockRbacState.currentRole = 'SEGMENT_HEAD'; // Maps to 'admin'
      renderSidebar();

      expect(screen.getByText('Insights')).toBeInTheDocument();
      expect(screen.getByText('People')).toBeInTheDocument();
      expect(screen.getByText('Governance')).toBeInTheDocument();
      expect(screen.queryByText('System')).not.toBeInTheDocument();
    });

    it('should show Insights and People but hide Governance for manager', () => {
      mockRbacState.currentRole = 'PROJECT_MANAGER'; // Maps to 'manager'
      renderSidebar();

      expect(screen.getByText('Insights')).toBeInTheDocument();
      expect(screen.getByText('People')).toBeInTheDocument();
      expect(screen.queryByText('Governance')).not.toBeInTheDocument();
      expect(screen.queryByText('System')).not.toBeInTheDocument();
    });

    it('should show only Insights for viewer (TEAM_MEMBER)', () => {
      mockRbacState.currentRole = 'TEAM_MEMBER'; // Maps to 'viewer'
      renderSidebar();

      expect(screen.getByText('Insights')).toBeInTheDocument();
      expect(screen.queryByText('People')).not.toBeInTheDocument();
      expect(screen.queryByText('Governance')).not.toBeInTheDocument();
      expect(screen.queryByText('System')).not.toBeInTheDocument();
    });
  });

  // =========================================
  // Navigation Items Tests
  // =========================================
  describe('Navigation items', () => {
    it('should render all Insights navigation items', () => {
      renderSidebar();

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Skill Coverage')).toBeInTheDocument();
      expect(screen.getByText('Talent Finder')).toBeInTheDocument();
    });

    it('should render People section with Employee Directory link', () => {
      renderSidebar();

      expect(screen.getByText('Employee Directory')).toBeInTheDocument();
    });

    it('should render Governance section items for admin role', () => {
      mockRbacState.currentRole = 'SUPER_ADMIN';
      renderSidebar();

      expect(screen.getByText('Employee Management')).toBeInTheDocument();
      expect(screen.getByText('Import Data')).toBeInTheDocument();
      expect(screen.getByText('Skill Library')).toBeInTheDocument();
      expect(screen.getByText('Organization Structure')).toBeInTheDocument();
      expect(screen.getByText('Role Catalog')).toBeInTheDocument();
    });

    it('should NOT render Settings in any section', () => {
      mockRbacState.currentRole = 'SUPER_ADMIN';
      renderSidebar();

      expect(screen.queryByText('Settings')).not.toBeInTheDocument();
    });
  });

  // =========================================
  // Active State Tests
  // =========================================
  describe('Active state based on route', () => {
    it('should mark Dashboard as active when on /dashboard', () => {
      renderSidebar('/dashboard');

      const dashboardLink = screen.getByText('Dashboard').closest('a');
      expect(dashboardLink).toHaveClass('is-active');
      expect(dashboardLink).toHaveAttribute('aria-current', 'page');
    });

    it('should mark Dashboard as active when on root /', () => {
      renderSidebar('/');

      const dashboardLink = screen.getByText('Dashboard').closest('a');
      expect(dashboardLink).toHaveClass('is-active');
    });

    it('should mark Employee Directory as active when on /profile', () => {
      renderSidebar('/profile');

      const employeeDirectoryLink = screen.getByText('Employee Directory').closest('a');
      expect(employeeDirectoryLink).toHaveClass('is-active');
      expect(employeeDirectoryLink).toHaveAttribute('aria-current', 'page');
    });

    it('should mark Employee Management as active when on /employees', () => {
      renderSidebar('/employees');

      const employeeManagementLink = screen.getByText('Employee Management').closest('a');
      expect(employeeManagementLink).toHaveClass('is-active');
      expect(employeeManagementLink).toHaveAttribute('aria-current', 'page');
    });

    it('should mark Skill Library as active for nested route /governance/skill-library/xyz', () => {
      renderSidebar('/governance/skill-library/category/123');

      const skillLibraryLink = screen.getByText('Skill Library').closest('a');
      expect(skillLibraryLink).toHaveClass('is-active');
    });

    it('should mark Import Data as active when on /system/import', () => {
      renderSidebar('/system/import');

      const importLink = screen.getByText('Import Data').closest('a');
      expect(importLink).toHaveClass('is-active');
      expect(importLink).toHaveAttribute('aria-current', 'page');
    });
  });

  // =========================================
  // Link Navigation Tests
  // =========================================
  describe('Link navigation', () => {
    it('should have correct href for Dashboard link', () => {
      renderSidebar();

      const dashboardLink = screen.getByText('Dashboard').closest('a');
      expect(dashboardLink).toHaveAttribute('href', '/dashboard');
    });

    it('should have correct href for Skill Coverage link', () => {
      renderSidebar();

      const skillCoverageLink = screen.getByText('Skill Coverage').closest('a');
      expect(skillCoverageLink).toHaveAttribute('href', '/skill-coverage');
    });

    it('should have correct href for Talent Finder link', () => {
      renderSidebar();

      const talentFinderLink = screen.getByText('Talent Finder').closest('a');
      expect(talentFinderLink).toHaveAttribute('href', '/talent-finder');
    });

    it('should have correct href for Employee Directory link (route /profile)', () => {
      renderSidebar();

      const employeeDirectoryLink = screen.getByText('Employee Directory').closest('a');
      expect(employeeDirectoryLink).toHaveAttribute('href', '/profile');
    });

    it('should have correct href for Employee Management link (route /employees)', () => {
      renderSidebar();

      const employeeManagementLink = screen.getByText('Employee Management').closest('a');
      expect(employeeManagementLink).toHaveAttribute('href', '/employees');
    });

    it('should have correct hrefs for Governance links', () => {
      renderSidebar();

      expect(screen.getByText('Employee Management').closest('a')).toHaveAttribute('href', '/employees');
      expect(screen.getByText('Import Data').closest('a')).toHaveAttribute('href', '/system/import');
      expect(screen.getByText('Skill Library').closest('a')).toHaveAttribute('href', '/governance/skill-library');
      expect(screen.getByText('Organization Structure').closest('a')).toHaveAttribute('href', '/governance/org-structure');
      expect(screen.getByText('Role Catalog').closest('a')).toHaveAttribute('href', '/governance/role-catalog');
    });
  });

  // =========================================
  // Collapsible Sections Tests
  // =========================================
  describe('Collapsible sections', () => {
    it('should render Governance as a details element', () => {
      renderSidebar();

      const governanceSection = screen.getByText('Governance').closest('details');
      expect(governanceSection).toBeInTheDocument();
      expect(governanceSection.tagName).toBe('DETAILS');
    });

    it('should have Governance section open by default', () => {
      renderSidebar();

      const governanceSection = screen.getByText('Governance').closest('details');
      expect(governanceSection).toHaveAttribute('open');
    });

    it('should toggle Governance section when summary is clicked', () => {
      renderSidebar();

      const governanceSummary = screen.getByText('Governance').closest('summary');
      const governanceDetails = governanceSummary.closest('details');

      // Initially open
      expect(governanceDetails).toHaveAttribute('open');

      // Click to close
      fireEvent.click(governanceSummary);
      expect(governanceDetails).not.toHaveAttribute('open');

      // Click to open again
      fireEvent.click(governanceSummary);
      expect(governanceDetails).toHaveAttribute('open');
    });
  });

  // =========================================
  // Semantic Structure Tests
  // =========================================
  describe('Semantic HTML structure', () => {
    it('should render as an aside element', () => {
      renderSidebar();

      const sidebar = screen.getByRole('complementary', { name: /primary navigation/i });
      expect(sidebar).toBeInTheDocument();
      expect(sidebar.tagName).toBe('ASIDE');
    });

    it('should have a nav element inside', () => {
      renderSidebar();

      const nav = document.querySelector('.sidebar .nav');
      expect(nav).toBeInTheDocument();
      expect(nav.tagName).toBe('NAV');
    });

    it('should render brand section with title and subtitle', () => {
      renderSidebar();

      expect(screen.getByText('CompetencyIQ')).toBeInTheDocument();
      expect(screen.getByText('Skill Intelligence Platform')).toBeInTheDocument();
    });

    it('should render divider when Governance section is visible', () => {
      renderSidebar();

      const divider = document.querySelector('.divider');
      expect(divider).toBeInTheDocument();
      expect(divider).toHaveAttribute('role', 'separator');
    });

    it('should not render divider when no admin sections are visible', () => {
      mockRbacState.currentRole = 'TEAM_MEMBER';
      renderSidebar();

      const divider = document.querySelector('.divider');
      expect(divider).not.toBeInTheDocument();
    });
  });

  // =========================================
  // Icon Tests
  // =========================================
  describe('Navigation icons', () => {
    it('should render emoji icons for each nav item', () => {
      renderSidebar();

      // Check that icons are present (emoji placeholders)
      expect(screen.getByText('📊')).toBeInTheDocument(); // Dashboard
      expect(screen.getByText('🗺️')).toBeInTheDocument(); // Skill Coverage
      expect(screen.getByText('🔎')).toBeInTheDocument(); // Talent Finder
      expect(screen.getByText('👥')).toBeInTheDocument(); // Employee Directory
      expect(screen.getByText('✏️')).toBeInTheDocument(); // Employee Management
      expect(screen.getByText('⬆️')).toBeInTheDocument(); // Import Data
      expect(screen.getByText('📚')).toBeInTheDocument(); // Skill Library
      expect(screen.getByText('🏢')).toBeInTheDocument(); // Organization Structure
      expect(screen.getByText('🧩')).toBeInTheDocument(); // Role Catalog
    });

    it('should NOT render Settings icon', () => {
      renderSidebar();

      expect(screen.queryByText('⚙️')).not.toBeInTheDocument();
    });
  });
});
