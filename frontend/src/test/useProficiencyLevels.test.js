/**
 * useProficiencyLevels Hook Unit Tests
 * 
 * Tests for the proficiency levels hook.
 * Covers:
 * - Successful fetch returns levels and options
 * - Error handling
 * - Loading state
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useProficiencyLevels } from '@/hooks/useProficiencyLevels.js';

// Mock fetch globally
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

// Mock API response data
const mockApiResponse = {
  proficiency_levels: [
    { proficiency_level_id: 1, level_name: 'Novice', level_description: 'New to the skill', value: 'NOVICE' },
    { proficiency_level_id: 2, level_name: 'Advanced Beginner', level_description: 'Some experience', value: 'ADVANCED_BEGINNER' },
    { proficiency_level_id: 3, level_name: 'Competent', level_description: 'Can work independently', value: 'COMPETENT' },
    { proficiency_level_id: 4, level_name: 'Proficient', level_description: 'Expert level', value: 'PROFICIENT' },
    { proficiency_level_id: 5, level_name: 'Expert', level_description: 'Master level', value: 'EXPERT' }
  ]
};

describe('useProficiencyLevels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Suppress console errors during tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should return loading true initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    const { result } = renderHook(() => useProficiencyLevels());
    
    expect(result.current.loading).toBe(true);
    expect(result.current.levels).toEqual([]);
    expect(result.current.options).toEqual([]);
    expect(result.current.error).toBe(null);
  });

  it('should fetch and return proficiency levels successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponse
    });

    const { result } = renderHook(() => useProficiencyLevels());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Check levels (for tooltip)
    expect(result.current.levels).toHaveLength(5);
    expect(result.current.levels[0]).toEqual({
      level_name: 'Novice',
      level_description: 'New to the skill'
    });
    expect(result.current.levels[4]).toEqual({
      level_name: 'Expert',
      level_description: 'Master level'
    });

    // Check options (for dropdown)
    expect(result.current.options).toHaveLength(5);
    expect(result.current.options[0]).toEqual({
      value: 'NOVICE',
      label: 'Novice'
    });
    expect(result.current.options[4]).toEqual({
      value: 'EXPERT',
      label: 'Expert'
    });

    expect(result.current.error).toBe(null);
  });

  it('should handle API error gracefully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500
    });

    const { result } = renderHook(() => useProficiencyLevels());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch proficiency levels: 500');
    expect(result.current.levels).toEqual([]);
    expect(result.current.options).toEqual([]);
  });

  it('should handle network error gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useProficiencyLevels());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.levels).toEqual([]);
    expect(result.current.options).toEqual([]);
  });

  it('should handle empty response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ proficiency_levels: [] })
    });

    const { result } = renderHook(() => useProficiencyLevels());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.levels).toEqual([]);
    expect(result.current.options).toEqual([]);
    expect(result.current.error).toBe(null);
  });

  it('should handle null level_description', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        proficiency_levels: [
          { proficiency_level_id: 1, level_name: 'Novice', level_description: null, value: 'NOVICE' }
        ]
      })
    });

    const { result } = renderHook(() => useProficiencyLevels());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.levels[0]).toEqual({
      level_name: 'Novice',
      level_description: ''
    });
  });

  it('should call correct API endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponse
    });

    renderHook(() => useProficiencyLevels());

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('/dropdown/proficiency-levels');
  });
});
