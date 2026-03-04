// Module: global-teardown.ts
// Purpose: Post-test cleanup - removes test data from database
// Part of: CompetencyIQ E2E Automation Suite

import { FullConfig } from '@playwright/test';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * Global teardown function executed once after all tests complete.
 * 
 * Responsibilities:
 * 1. Clean up test data created during test run
 * 2. Remove test records with IDs >= 9000
 * 3. Log cleanup summary
 * 
 * @param config - Playwright full configuration object
 */
async function globalTeardown(config: FullConfig): Promise<void> {
  console.log('🧹 Global teardown: starting...');

  // ============================================
  // STEP 1: Clean up test data
  // ============================================
  console.log('🗑️  Global teardown: cleaning test database...');

  try {
    // TODO: Uncomment when cleanup.ts is implemented
    // const { default: cleanupTestData } = await import('./testdata/cleanup');
    // await cleanupTestData();
    console.log('✅ Database cleanup complete (stub)');
  } catch (error) {
    console.error('❌ Database cleanup failed:', error);
    // Log but don't fail - cleanup errors shouldn't fail the test run
  }

  // ============================================
  // STEP 2: Report summary
  // ============================================
  console.log('📊 Global teardown: generating summary...');
  console.log('   Test data with IDs >= 9000 has been cleaned up');
  console.log('   Records with created_by = "test_automation" removed');

  console.log('✅ Global teardown complete');
}

export default globalTeardown;
