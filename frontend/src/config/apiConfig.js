/**
 * API Configuration
 * Centralized configuration for backend API base URL.
 * Driven by VITE_API_BASE_URL environment variable.
 */

const base = import.meta.env.VITE_API_BASE_URL;

if (!base) {
  throw new Error(
    "VITE_API_BASE_URL is not set. Set it in Azure Static Web Apps > Environment variables."
  );
}

export const API_BASE_URL = `${base}/api`;
