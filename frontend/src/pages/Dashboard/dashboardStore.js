/**
 * Page-scoped state store for Dashboard
 * Preserves dashboard data across navigation to avoid re-fetching on back navigation.
 * Uses TTL (60 seconds) to ensure data freshness while preventing unnecessary API calls.
 */

import { create } from 'zustand';

// Cache TTL in milliseconds (60 seconds)
export const DASHBOARD_CACHE_TTL = 60 * 1000;

const useDashboardStore = create((set, get) => ({
  // Cache metadata
  hasCachedData: false,
  cachedAt: 0,
  
  // Cached dashboard payload
  cachedPayload: null,
  
  // Check if cache is valid (exists and not expired)
  isCacheValid: () => {
    const state = get();
    if (!state.hasCachedData || !state.cachedPayload) {
      return false;
    }
    return (Date.now() - state.cachedAt) < DASHBOARD_CACHE_TTL;
  },
  
  // Set cached payload after successful fetch
  setCachedPayload: (payload) => set({
    cachedPayload: payload,
    hasCachedData: true,
    cachedAt: Date.now()
  }),
  
  // Clear cache (for hard refresh scenarios if needed)
  clearCache: () => set({
    hasCachedData: false,
    cachedAt: 0,
    cachedPayload: null
  })
}));

export default useDashboardStore;
