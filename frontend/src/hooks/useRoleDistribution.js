import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardApi } from '../services/api/dashboardApi.js';

/**
 * Hook for fetching role distribution data from the backend API.
 * 
 * Handles:
 * - API calls with proper params based on filter context
 * - Loading/error states  
 * - Refetch on filter changes (not on every render)
 * - AbortController for cleanup
 * 
 * @param {Object} filters - Dashboard filters { subSegment, project, team }
 * @param {Object} options - Optional settings { segmentId, topN, maxRoles, includeEmpty }
 * @returns {{ data: RoleDistributionResponse | null, isLoading: boolean, error: Error | null, refetch: () => void }}
 */
export function useRoleDistribution(filters, options = {}) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Use ref to track abort controller
  const abortControllerRef = useRef(null);
  
  // Create stable filter key to detect changes
  const filterKey = `${filters.subSegment || ''}-${filters.project || ''}-${filters.team || ''}`;
  
  const fetchData = useCallback(async () => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController();
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await dashboardApi.getRoleDistribution(filters, options);
      
      // Only update state if this request wasn't aborted
      if (!abortControllerRef.current?.signal.aborted) {
        setData(response);
        setError(null);
      }
    } catch (err) {
      // Ignore abort errors
      if (err.name === 'AbortError') {
        return;
      }
      
      if (!abortControllerRef.current?.signal.aborted) {
        console.error('Failed to fetch role distribution:', err);
        setError(err);
        setData(null);
      }
    } finally {
      if (!abortControllerRef.current?.signal.aborted) {
        setIsLoading(false);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey, options.segmentId, options.topN, options.maxRoles, options.includeEmpty]);
  
  // Fetch on mount and when filters change
  useEffect(() => {
    fetchData();
    
    // Cleanup: abort any pending request on unmount or filter change
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchData]);
  
  // Refetch function for retry button
  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);
  
  return {
    data,
    isLoading,
    error,
    refetch
  };
}

export default useRoleDistribution;
