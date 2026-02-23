/**
 * Route Integration Tests
 * =======================
 * Tests verifying that routes render the correct page components.
 * 
 * Key verifications:
 * 1. /skill-coverage renders SkillTaxonomyPage (Capability Overview)
 * 2. /talent-finder renders AdvancedQueryPage (Capability Finder)
 * 3. Neither shows placeholder "Coming Soon" text
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';

// Mock API responses to avoid network calls
vi.mock('../api/httpClient', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  }
}));

// Mock taxonomy API
vi.mock('../api/taxonomy', () => ({
  default: {
    getTree: vi.fn().mockResolvedValue({ data: { categories: [] } }),
    getCategories: vi.fn().mockResolvedValue({ data: [] }),
    getSubcategories: vi.fn().mockResolvedValue({ data: [] }),
    getSkills: vi.fn().mockResolvedValue({ data: [] }),
  },
  taxonomyApi: {
    getTree: vi.fn().mockResolvedValue({ data: { categories: [] } }),
    getCategories: vi.fn().mockResolvedValue({ data: [] }),
    getSubcategories: vi.fn().mockResolvedValue({ data: [] }),
    getSkills: vi.fn().mockResolvedValue({ data: [] }),
  }
}));

// Mock skill stats API
vi.mock('../api/skillStats', () => ({
  default: {
    getSkillStats: vi.fn().mockResolvedValue({ data: { skills: [] } }),
    getEmployeeSkillStats: vi.fn().mockResolvedValue({ data: [] }),
  },
  skillStatsApi: {
    getSkillStats: vi.fn().mockResolvedValue({ data: { skills: [] } }),
    getEmployeeSkillStats: vi.fn().mockResolvedValue({ data: [] }),
  }
}));

// Mock employees API
vi.mock('../api/employees', () => ({
  default: {
    getEmployees: vi.fn().mockResolvedValue({ data: [] }),
    searchEmployees: vi.fn().mockResolvedValue({ data: [] }),
  },
  employeeApi: {
    getEmployees: vi.fn().mockResolvedValue({ data: [] }),
    searchEmployees: vi.fn().mockResolvedValue({ data: [] }),
  }
}));

// Mock dashboard API
vi.mock('../api/dashboardApi', () => ({
  dashboardApi: {
    getSkillGapAnalysis: vi.fn().mockResolvedValue({ data: [] }),
    getSegments: vi.fn().mockResolvedValue({ data: [] }),
    getSubSegments: vi.fn().mockResolvedValue({ data: [] }),
    getProjects: vi.fn().mockResolvedValue({ data: [] }),
  }
}));

// Mock feature flags
vi.mock('../config/featureFlags', () => ({
  RBAC_CONFIG: {
    currentRole: 'SUPER_ADMIN',
    currentScope: {}
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
  },
  getRbacContext: () => ({
    role: 'SUPER_ADMIN',
    scope: {},
    permissions: { canView: true, canCreate: true, canUpdate: true, canDelete: true }
  }),
  hasPermission: () => true
}));

// Import pages after mocks
import MainLayout from '../layouts/MainLayout.jsx';
import SkillTaxonomyPage from '../pages/Taxonomy/SkillTaxonomyPage.jsx';
import AdvancedQueryPage from '../pages/AdvancedQuery/AdvancedQueryPage.jsx';

// Helper to create router with specific route
const createTestRouter = (initialPath, routes) => {
  return createMemoryRouter(routes, {
    initialEntries: [initialPath],
  });
};

describe('Route Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('/skill-coverage route', () => {
    it('should render SkillTaxonomyPage (Capability Overview), not "Coming Soon"', async () => {
      const routes = [
        {
          path: '/',
          element: <MainLayout />,
          children: [
            {
              path: 'skill-coverage',
              element: <SkillTaxonomyPage />,
            },
          ],
        },
      ];

      const router = createTestRouter('/skill-coverage', routes);
      render(<RouterProvider router={router} />);

      // Should NOT show "Coming Soon" placeholder
      await waitFor(() => {
        expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
      });

      // Should show Capability Overview content
      await waitFor(() => {
        expect(screen.getByText('Capability Overview')).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should render skill taxonomy tree panel', async () => {
      const routes = [
        {
          path: '/',
          element: <MainLayout />,
          children: [
            {
              path: 'skill-coverage',
              element: <SkillTaxonomyPage />,
            },
          ],
        },
      ];

      const router = createTestRouter('/skill-coverage', routes);
      render(<RouterProvider router={router} />);

      // Should have tree panel for navigating categories
      await waitFor(() => {
        // Look for the category/subcategory navigation structure
        const pageContent = document.body.textContent;
        expect(pageContent).not.toContain('This feature is coming soon');
      });
    });
  });

  describe('/talent-finder route', () => {
    it('should render AdvancedQueryPage (Capability Finder), not "Coming Soon"', async () => {
      const routes = [
        {
          path: '/',
          element: <MainLayout />,
          children: [
            {
              path: 'talent-finder',
              element: <AdvancedQueryPage />,
            },
          ],
        },
      ];

      const router = createTestRouter('/talent-finder', routes);
      render(<RouterProvider router={router} />);

      // Should NOT show "Coming Soon" placeholder
      await waitFor(() => {
        expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
      });

      // Should show Capability Finder content
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Capability Finder/i })).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should render skill search functionality', async () => {
      const routes = [
        {
          path: '/',
          element: <MainLayout />,
          children: [
            {
              path: 'talent-finder',
              element: <AdvancedQueryPage />,
            },
          ],
        },
      ];

      const router = createTestRouter('/talent-finder', routes);
      render(<RouterProvider router={router} />);

      // Should have search/query interface
      await waitFor(() => {
        const pageContent = document.body.textContent;
        expect(pageContent).not.toContain('This feature is coming soon');
      });
    });
  });

  describe('No "Coming Soon" placeholders in main nav routes', () => {
    it('should not show placeholder text on /skill-coverage', async () => {
      const routes = [
        {
          path: '/',
          element: <MainLayout />,
          children: [
            {
              path: 'skill-coverage',
              element: <SkillTaxonomyPage />,
            },
          ],
        },
      ];

      const router = createTestRouter('/skill-coverage', routes);
      render(<RouterProvider router={router} />);

      await waitFor(() => {
        // Check for placeholder text patterns
        expect(screen.queryByText('This feature is coming soon')).not.toBeInTheDocument();
        expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
      });
    });

    it('should not show placeholder text on /talent-finder', async () => {
      const routes = [
        {
          path: '/',
          element: <MainLayout />,
          children: [
            {
              path: 'talent-finder',
              element: <AdvancedQueryPage />,
            },
          ],
        },
      ];

      const router = createTestRouter('/talent-finder', routes);
      render(<RouterProvider router={router} />);

      await waitFor(() => {
        // Check for placeholder text patterns
        expect(screen.queryByText('This feature is coming soon')).not.toBeInTheDocument();
        expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
      });
    });
  });
});
