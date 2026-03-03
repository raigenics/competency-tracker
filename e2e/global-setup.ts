// Module: global-setup.ts
// Purpose: Pre-test setup - seeds database and saves authentication state
// Part of: CompetencyIQ E2E Automation Suite

import { chromium, FullConfig } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';

// Load environment variables
dotenv.config();

/**
 * Global setup function executed once before all tests.
 * 
 * Responsibilities:
 * 1. Load environment configuration
 * 2. Seed test database with known test data
 * 3. Perform admin login and save authentication state
 * 
 * @param config - Playwright full configuration object
 */
async function globalSetup(config: FullConfig): Promise<void> {
  console.log('🚀 Global setup: starting...');
  
  // Ensure auth directory exists
  const authDir = path.join(__dirname, 'playwright', '.auth');
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  // ============================================
  // STEP 1: Seed test database
  // ============================================
  console.log('📦 Global setup: seeding test database...');
  
  try {
    // TODO: Uncomment when api-seed.ts is implemented
    // const { default: seedViaApi } = await import('./testdata/api-seed');
    // await seedViaApi();
    console.log('✅ Database seeding complete (stub)');
  } catch (error) {
    console.error('❌ Database seeding failed:', error);
    // Don't fail setup - tests may still work with existing data
  }

  // ============================================
  // STEP 2: Authenticate and save state
  // ============================================
  console.log('🔐 Global setup: authenticating admin user...');
  
  const baseURL = process.env.BASE_URL || 'http://localhost:5173';
  // const adminEmail = process.env.ADMIN_EMAIL;
  // const adminPassword = process.env.ADMIN_PASSWORD;

  // if (!adminEmail || !adminPassword) {
  //   console.warn('⚠️  ADMIN_EMAIL or ADMIN_PASSWORD not set in .env');
  //   console.warn('⚠️  Skipping authentication setup - tests requiring auth will fail');
    
  //   // Create empty auth state file to prevent file-not-found errors
  //   const emptyState = { cookies: [], origins: [] };
  //   fs.writeFileSync(
  //     path.join(authDir, 'admin.json'),
  //     JSON.stringify(emptyState, null, 2)
  //   );
    
  //   console.log('✅ Global setup complete (without auth)');
  //   return;
  // }

  // Launch browser for authentication
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // No login page exists — app loads as Super Admin by default
    // Just visit the root and save browser state for reuse in tests
    console.log(`🌐 Loading app at ${baseURL} ...`);
    await page.goto(baseURL, { waitUntil: 'networkidle', timeout: 30000 });
    console.log('✅ App loaded — Super Admin by default (no login required)');

    await context.storageState({ path: path.join(authDir, 'admin.json') });
    console.log('💾 Browser state saved to playwright/.auth/admin.json');

  } catch (error) {
    console.warn('⚠️  Could not reach the app.');
    console.warn(`   Expected: ${baseURL}`);
    console.warn('   Fix: start your frontend with npm run dev first');

    fs.writeFileSync(
      path.join(authDir, 'admin.json'),
      JSON.stringify({ cookies: [], origins: [] }, null, 2)
    );
  } finally {
    await browser.close();
  }

  console.log('✅ Global setup complete');
}

export default globalSetup;
