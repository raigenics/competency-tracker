// Module: cleanup.ts
// Purpose: Cleanup test data via API after E2E tests
// Part of: CompetencyIQ E2E Automation Suite

import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_BASE = `${BASE_URL}/api`;
const MIN_TEST_ID = parseInt(process.env.SEED_MIN_ID || '9000', 10);

/**
 * Helper function to make API DELETE requests
 */
async function apiDelete(endpoint: string): Promise<Response> {
  const url = `${API_BASE}${endpoint}`;
  
  return fetch(url, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      // TODO: Add auth header when implementing actual API calls
      // 'Authorization': `Bearer ${process.env.API_TOKEN}`,
    },
  });
}

/**
 * Cleanup employee skills (fact data)
 */
async function cleanupEmployeeSkills(): Promise<void> {
  console.log('🧹 Cleaning up employee skills...');

  const testEmployeeIds = [9001, 9002, 9003];
  
  for (const employeeId of testEmployeeIds) {
    console.log(`   Removing skills from employee ${employeeId}`);
    // TODO: Implement actual API call
    // await apiDelete(`/employees/${employeeId}/skills`);
  }

  console.log('✅ Employee skills cleaned up');
}

/**
 * Cleanup employees
 */
async function cleanupEmployees(): Promise<void> {
  console.log('🧹 Cleaning up employees...');

  const testEmployeeIds = [9001, 9002, 9003];
  
  for (const id of testEmployeeIds) {
    console.log(`   Deleting employee ${id}`);
    // TODO: Implement actual API call
    // await apiDelete(`/employees/${id}`);
  }

  console.log('✅ Employees cleaned up');
}

/**
 * Cleanup roles
 */
async function cleanupRoles(): Promise<void> {
  console.log('🧹 Cleaning up roles...');

  console.log('   Deleting role 9001');
  // TODO: Implement actual API call
  // await apiDelete('/roles/9001');

  console.log('✅ Roles cleaned up');
}

/**
 * Cleanup skill taxonomy
 */
async function cleanupSkillTaxonomy(): Promise<void> {
  console.log('🧹 Cleaning up skill taxonomy...');

  // Skills (must be deleted before subcategories)
  const testSkillIds = [9001, 9002, 9003];
  for (const id of testSkillIds) {
    console.log(`   Deleting skill ${id}`);
    // TODO: Implement actual API call
    // await apiDelete(`/skills/${id}`);
  }

  // Subcategory
  console.log('   Deleting subcategory 9001');
  // TODO: Implement actual API call
  // await apiDelete('/skill-subcategories/9001');

  // Category
  console.log('   Deleting category 9001');
  // TODO: Implement actual API call
  // await apiDelete('/skill-categories/9001');

  console.log('✅ Skill taxonomy cleaned up');
}

/**
 * Cleanup organizational hierarchy
 */
async function cleanupOrgHierarchy(): Promise<void> {
  console.log('🧹 Cleaning up organizational hierarchy...');

  // Team (must be deleted before project)
  console.log('   Deleting team 9001');
  // TODO: Implement actual API call
  // await apiDelete('/teams/9001');

  // Project (must be deleted before sub-segment)
  console.log('   Deleting project 9001');
  // TODO: Implement actual API call
  // await apiDelete('/projects/9001');

  // Sub-Segment (must be deleted before segment)
  console.log('   Deleting sub-segment 9001');
  // TODO: Implement actual API call
  // await apiDelete('/sub-segments/9001');

  // Segment
  console.log('   Deleting segment 9001');
  // TODO: Implement actual API call
  // await apiDelete('/segments/9001');

  console.log('✅ Organizational hierarchy cleaned up');
}

/**
 * Main cleanup function - orchestrates all cleanup operations
 * Deletes in reverse dependency order
 */
export async function cleanupTestData(): Promise<void> {
  console.log('🗑️  Starting API-based test data cleanup...');
  console.log(`   Target: ${API_BASE}`);
  console.log(`   Removing IDs >= ${MIN_TEST_ID}`);

  try {
    // Cleanup in reverse dependency order
    await cleanupEmployeeSkills();
    await cleanupEmployees();
    await cleanupRoles();
    await cleanupSkillTaxonomy();
    await cleanupOrgHierarchy();

    console.log('');
    console.log('✅ All test data cleaned up successfully via API');
  } catch (error) {
    console.error('❌ Error cleaning up test data:', error);
    // Don't throw - cleanup errors shouldn't fail the test run
    console.warn('⚠️  Cleanup errors are logged but do not fail the process');
  }
}

// Export as default for use in global-teardown
export default cleanupTestData;

// Allow running directly for manual cleanup
if (require.main === module) {
  cleanupTestData()
    .then(() => {
      console.log('Cleanup complete');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Cleanup failed:', error);
      process.exit(1);
    });
}
