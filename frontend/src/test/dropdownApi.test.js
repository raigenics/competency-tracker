/**
 * dropdownApi Unit Tests
 * 
 * Tests:
 * 1. Segments cache - returns cached data on subsequent calls
 * 2. Single-flight pattern - concurrent calls share same promise
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dropdownApi } from '@/services/api/dropdownApi.js';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('dropdownApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Clear any cached data between tests
    dropdownApi.clearSegmentsCache();
  });

  describe('getSegments cache', () => {
    it('should call API on first request', async () => {
      const mockSegments = [{ segment_id: 1, segment_name: 'DTS' }];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ segments: mockSegments })
      });

      const result = await dropdownApi.getSegments();

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockSegments);
    });

    it('should return cached data on second request without calling API', async () => {
      const mockSegments = [{ segment_id: 1, segment_name: 'DTS' }];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ segments: mockSegments })
      });

      // First call - should hit API
      const result1 = await dropdownApi.getSegments();
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Second call - should use cache
      const result2 = await dropdownApi.getSegments();
      expect(mockFetch).toHaveBeenCalledTimes(1); // Still only 1 call
      expect(result2).toEqual(mockSegments);
      expect(result1).toBe(result2); // Same reference
    });

    it('should clear cache when clearSegmentsCache is called', async () => {
      const mockSegments1 = [{ segment_id: 1, segment_name: 'DTS' }];
      const mockSegments2 = [{ segment_id: 2, segment_name: 'PA' }];
      
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ segments: mockSegments1 })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ segments: mockSegments2 })
        });

      // First call
      await dropdownApi.getSegments();
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Clear cache
      dropdownApi.clearSegmentsCache();

      // Second call should hit API again
      const result = await dropdownApi.getSegments();
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual(mockSegments2);
    });
  });

  describe('getSegments single-flight pattern', () => {
    it('should reuse in-flight promise for concurrent requests', async () => {
      const mockSegments = [{ segment_id: 1, segment_name: 'DTS' }];
      let resolvePromise;
      
      // Create a slow-resolving fetch that we control
      mockFetch.mockReturnValueOnce(
        new Promise(resolve => {
          resolvePromise = () => resolve({
            ok: true,
            json: () => Promise.resolve({ segments: mockSegments })
          });
        })
      );

      // Start two concurrent requests
      const promise1 = dropdownApi.getSegments();
      const promise2 = dropdownApi.getSegments();

      // Should only have made 1 fetch call
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Resolve the pending fetch
      resolvePromise();

      // Both promises should resolve to same data
      const [result1, result2] = await Promise.all([promise1, promise2]);
      expect(result1).toEqual(mockSegments);
      expect(result2).toEqual(mockSegments);
      expect(result1).toBe(result2); // Same reference
    });

    it('should allow new request after in-flight completes with error', async () => {
      const mockSegments = [{ segment_id: 1, segment_name: 'DTS' }];
      
      // First call fails
      mockFetch.mockRejectedValueOnce(new Error('Network error'));
      
      // Second call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ segments: mockSegments })
      });

      // First call should fail
      await expect(dropdownApi.getSegments()).rejects.toThrow('Network error');
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Second call should work (in-flight cleared after error)
      const result = await dropdownApi.getSegments();
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual(mockSegments);
    });
  });
});
