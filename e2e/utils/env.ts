// Module: env.ts
// Purpose: Environment variable exports for E2E tests
// Part of: CompetencyIQ E2E Automation Suite

import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

/**
 * Base URL for the application under test
 * @default 'http://localhost:5173'
 */
export const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

/**
 * API base URL derived from BASE_URL
 */
export const API_BASE_URL = `${BASE_URL}/api`;

/**
 * Admin user email for authentication
 */
export const ADMIN_EMAIL = process.env.ADMIN_EMAIL || '';

/**
 * Admin user password for authentication
 */
export const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || '';

/**
 * Minimum ID for test data isolation
 * All test-created entities should use IDs >= this value
 * @default 9000
 */
export const SEED_MIN_ID = parseInt(process.env.SEED_MIN_ID || '9000', 10);

/**
 * Database connection string for direct DB operations
 */
export const DB_CONNECTION_STRING = process.env.DB_CONNECTION_STRING || '';

/**
 * Database host for PostgreSQL connection
 */
export const DB_HOST = process.env.DB_HOST || 'localhost';

/**
 * Database port for PostgreSQL connection
 * @default 5432
 */
export const DB_PORT = parseInt(process.env.DB_PORT || '5432', 10);

/**
 * Database name
 */
export const DB_NAME = process.env.DB_NAME || '';

/**
 * Database user
 */
export const DB_USER = process.env.DB_USER || '';

/**
 * Database password
 */
export const DB_PASSWORD = process.env.DB_PASSWORD || '';

/**
 * Validate required environment variables are set
 * Call this in global-setup to fail fast
 */
export function validateEnv(): void {
  const required = ['BASE_URL'];
  const missing = required.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    console.warn(`⚠️  Missing recommended env vars: ${missing.join(', ')}`);
  }
}

/**
 * Check if running in CI environment
 */
export const IS_CI = Boolean(process.env.CI);

/**
 * Check if running in debug mode
 */
export const IS_DEBUG = Boolean(process.env.DEBUG);
