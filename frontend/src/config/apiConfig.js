/**
 * API Configuration
 * Centralized configuration for backend API base URL.
 * Driven by VITE_API_BASE_URL environment variable.
 */

const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api`;

export { API_BASE_URL };
