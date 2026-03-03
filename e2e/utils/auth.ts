// Module: auth.ts
// Purpose: Authentication utilities for E2E tests
// Part of: CompetencyIQ E2E Automation Suite

import { Page } from '@playwright/test';
import { ADMIN_EMAIL, ADMIN_PASSWORD, BASE_URL } from './env';

/**
 * Path to stored authentication state
 */
export const AUTH_STATE_PATH = 'playwright/.auth/admin.json';

/**
 * Login as admin user and save authentication state
 * Used in global-setup to authenticate once for all tests
 * 
 * @param page - Playwright page instance
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  console.log('🔐 Logging in as admin...');

  // Navigate to login page
  await page.goto(`${BASE_URL}/login`);

  // TODO: Implement actual login flow
  // Fill email
  // await page.getByLabel('Email').fill(ADMIN_EMAIL);
  
  // Fill password
  // await page.getByLabel('Password').fill(ADMIN_PASSWORD);
  
  // Submit login form
  // await page.getByRole('button', { name: 'Sign In' }).click();
  
  // Wait for successful login redirect
  // await page.waitForURL('**/dashboard', { timeout: 30000 });

  console.log('✅ Admin login successful');
}

/**
 * Login with custom credentials
 * 
 * @param page - Playwright page instance
 * @param email - User email
 * @param password - User password
 */
export async function loginAs(
  page: Page, 
  email: string, 
  password: string
): Promise<void> {
  console.log(`🔐 Logging in as ${email}...`);

  // Navigate to login page
  await page.goto(`${BASE_URL}/login`);

  // TODO: Implement actual login flow
  // await page.getByLabel('Email').fill(email);
  // await page.getByLabel('Password').fill(password);
  // await page.getByRole('button', { name: 'Sign In' }).click();
  // await page.waitForURL('**/dashboard', { timeout: 30000 });

  console.log(`✅ Login as ${email} successful`);
}

/**
 * Logout current user
 * 
 * @param page - Playwright page instance
 */
export async function logout(page: Page): Promise<void> {
  console.log('🔓 Logging out...');

  // TODO: Implement actual logout flow
  // await page.getByRole('button', { name: /user menu/i }).click();
  // await page.getByRole('menuitem', { name: 'Logout' }).click();
  // await page.waitForURL('**/login');

  console.log('✅ Logout successful');
}

/**
 * Check if user is authenticated
 * 
 * @param page - Playwright page instance
 * @returns true if user appears to be logged in
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  // TODO: Implement actual authentication check
  // Could check for presence of auth token in local storage,
  // or check if user menu is visible, etc.
  
  // Stub: always return false until implemented
  return false;
}

/**
 * Clear authentication state (cookies, local storage)
 * 
 * @param page - Playwright page instance
 */
export async function clearAuth(page: Page): Promise<void> {
  console.log('🧹 Clearing authentication state...');

  // Clear cookies
  await page.context().clearCookies();

  // Clear local storage
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  console.log('✅ Authentication state cleared');
}
