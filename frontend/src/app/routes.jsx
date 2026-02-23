import { createBrowserRouter } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout.jsx';
import DashboardPage from '../pages/Dashboard/DashboardPage.jsx';
import AdvancedQueryPage from '../pages/AdvancedQuery/AdvancedQueryPage.jsx';
import SkillTaxonomyPage from '../pages/Taxonomy/SkillTaxonomyPage.jsx';
import MyProfilePage from '../pages/Profile/MyProfilePage.jsx';
import EmployeeProfilePage from '../pages/Profile/EmployeeProfilePage.jsx';
import ComparisonPage from '../pages/Comparison/ComparisonPage.jsx';
import EmployeesPage from '../pages/Employees/EmployeesPage.jsx';
import BulkImportPage from '../pages/BulkImport/BulkImportPage.jsx';
import RbacAdminPage from '../pages/RbacAdmin/RbacAdminPage.jsx';
import { FEATURE_FLAGS } from '../config/featureFlags';

// Settings placeholder page
import SettingsPage from '../pages/Settings/SettingsPage.jsx';

// Master Data pages (used for Governance section)
import { 
  SkillTaxonomyPage as MasterDataSkillTaxonomyPage,
  OrgHierarchyPage,
  RolesPage 
} from '../pages/MasterData';

// Skill Library page (new design)
import { SkillLibraryPage } from '../pages/SkillLibrary';

export const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      // ============================================
      // INSIGHTS Section
      // ============================================
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        // Skill Coverage -> Organizational Skill Map (SkillTaxonomyPage)
        path: "skill-coverage",
        element: <SkillTaxonomyPage />,
      },
      {
        // Talent Finder -> Skill Search (AdvancedQueryPage)
        path: "talent-finder",
        element: <AdvancedQueryPage />,
      },

      // ============================================
      // PEOPLE Section
      // ============================================
      {
        path: "employees",
        element: <EmployeesPage />,
      },

      // ============================================
      // GOVERNANCE Section (admin+)
      // ============================================
      {
        path: "governance/skill-library",
        element: <SkillLibraryPage />,
      },
      {
        path: "governance/org-structure",
        element: <OrgHierarchyPage />,
      },
      {
        path: "governance/role-catalog",
        element: <RolesPage />,
      },

      // ============================================
      // SYSTEM Section (superadmin only)
      // ============================================
      {
        path: "system/import",
        element: <BulkImportPage />,
      },
      {
        path: "system/settings",
        element: <SettingsPage />,
      },

      // ============================================
      // Legacy routes (keep for backwards compatibility)
      // ============================================
      {
        path: "query",
        element: <AdvancedQueryPage />,
      },
      {
        path: "taxonomy",
        element: <SkillTaxonomyPage />,
      },
      {
        path: "profile",
        element: <MyProfilePage />,
      },
      {
        path: "profile/employee/:id",
        element: <EmployeeProfilePage />,
      },
      {
        path: "comparison",
        element: <ComparisonPage />,
      },
      {
        path: "bulk-import",
        element: <BulkImportPage />,
      },
      // RBAC Admin - controlled by feature flag
      ...(FEATURE_FLAGS.SHOW_RBAC_ADMIN ? [
        {
          path: "rbac-admin",
          element: <RbacAdminPage />,
        }
      ] : []),
      // Legacy Master Data routes
      {
        path: "admin/master-data/skill-taxonomy",
        element: <MasterDataSkillTaxonomyPage />,
      },
      {
        path: "admin/master-data/org-hierarchy",
        element: <OrgHierarchyPage />,
      },
      {
        path: "admin/master-data/roles",
        element: <RolesPage />,
      },
    ],
  },
]);

export default router;
