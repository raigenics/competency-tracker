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

// Master Data pages
import { 
  SkillTaxonomyPage as MasterDataSkillTaxonomyPage,
  OrgHierarchyPage,
  RolesPage 
} from '../pages/MasterData';

export const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
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
      },      {
        path: "comparison",
        element: <ComparisonPage />,
      },      {
        path: "employees",
        element: <EmployeesPage />,
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
      // Master Data routes
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
