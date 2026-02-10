/**
 * useUniqueEmployeeValidation Hook Unit Tests
 * 
 * Tests:
 * 1. ZID validation (debounced)
 * 2. Email validation (debounced)
 * 3. Error state management
 * 4. Loading state management
 * 5. excludeEmployeeId for edit mode
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useUniqueEmployeeValidation } from '@/hooks/useUniqueEmployeeValidation.js';

// Mock the validation API
vi.mock('@/services/api/employeeValidationApi.js', () => ({
  employeeValidationApi: {
    validateUnique: vi.fn()
  }
}));

import { employeeValidationApi } from '@/services/api/employeeValidationApi.js';

describe('useUniqueEmployeeValidation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('1. Initial State', () => {
    it('initializes with no errors', () => {
      const { result } = renderHook(() => useUniqueEmployeeValidation());
      
      expect(result.current.uniqueErrors.zid).toBeNull();
      expect(result.current.uniqueErrors.email).toBeNull();
    });

    it('initializes with no loading states', () => {
      const { result } = renderHook(() => useUniqueEmployeeValidation());
      
      expect(result.current.isValidating.zid).toBe(false);
      expect(result.current.isValidating.email).toBe(false);
    });

    it('hasUniqueErrors returns false initially', () => {
      const { result } = renderHook(() => useUniqueEmployeeValidation());
      
      expect(result.current.hasUniqueErrors()).toBe(false);
    });
  });

  describe('2. ZID Validation', () => {
    it('sets loading state when validating', async () => {
      let resolvePromise;
      employeeValidationApi.validateUnique.mockImplementation(() => 
        new Promise(resolve => { resolvePromise = resolve; })
      );

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateZid('Z0123456');
      });

      // Should be validating after debounce with 0 delay
      await waitFor(() => {
        expect(result.current.isValidating.zid).toBe(true);
      });

      // Cleanup: resolve the promise
      await act(async () => {
        resolvePromise({ zid_exists: false, email_exists: false });
      });
    });

    it('shows error when ZID already exists', async () => {
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: true, 
        email_exists: false 
      });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateZid('Z0123456');
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.zid).toBe('This ZID is already in use');
      });
    });

    it('clears error when ZID is unique', async () => {
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: false, 
        email_exists: false 
      });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateZid('Z9999999');
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.zid).toBeNull();
        expect(result.current.isValidating.zid).toBe(false);
      });
    });

    it('clears error when ZID is empty', () => {
      const { result } = renderHook(() => useUniqueEmployeeValidation());
      
      act(() => {
        result.current.validateZid('');
      });

      expect(result.current.uniqueErrors.zid).toBeNull();
      expect(result.current.isValidating.zid).toBe(false);
    });

    it('debounces rapid ZID changes', async () => {
      vi.useFakeTimers();
      
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: false, 
        email_exists: false 
      });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 300 }));
      
      // Rapid typing simulation
      act(() => {
        result.current.validateZid('Z');
        result.current.validateZid('Z0');
        result.current.validateZid('Z01');
        result.current.validateZid('Z012');
      });

      // Advance partially - should not have called API yet
      await act(async () => {
        vi.advanceTimersByTime(200);
      });

      expect(employeeValidationApi.validateUnique).not.toHaveBeenCalled();

      // Advance past debounce
      await act(async () => {
        vi.advanceTimersByTime(300);
        // Need to flush promises too
        await Promise.resolve();
      });

      // Should only call once with final value
      expect(employeeValidationApi.validateUnique).toHaveBeenCalledTimes(1);
      expect(employeeValidationApi.validateUnique).toHaveBeenCalledWith({
        zid: 'Z012',
        excludeEmployeeId: null
      });

      vi.useRealTimers();
    });
  });

  describe('3. Email Validation', () => {
    it('shows error when email already exists', async () => {
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: false, 
        email_exists: true 
      });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateEmail('existing@example.com');
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.email).toBe('This email is already in use');
      });
    });

    it('clears error when email is unique', async () => {
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: false, 
        email_exists: false 
      });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateEmail('new@example.com');
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.email).toBeNull();
      });
    });
  });

  describe('4. Edit Mode - excludeEmployeeId', () => {
    it('passes excludeEmployeeId to API call', async () => {
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: false, 
        email_exists: false 
      });

      const { result } = renderHook(() => 
        useUniqueEmployeeValidation({ 
          excludeEmployeeId: 42,
          debounceDelay: 0 
        })
      );
      
      act(() => {
        result.current.validateZid('Z0123456');
      });

      await waitFor(() => {
        expect(employeeValidationApi.validateUnique).toHaveBeenCalledWith({
          zid: 'Z0123456',
          excludeEmployeeId: 42
        });
      });
    });

    it('excludes own ZID in edit mode', async () => {
      // Simulate edit mode where the current employee's ZID won't trigger error
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: false,  // Backend excludes current employee
        email_exists: false 
      });

      const { result } = renderHook(() => 
        useUniqueEmployeeValidation({ 
          excludeEmployeeId: 42,
          debounceDelay: 0 
        })
      );
      
      act(() => {
        result.current.validateZid('Z0123456'); // Current employee's ZID
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.zid).toBeNull();
      });
    });
  });

  describe('5. Clear Methods', () => {
    it('clearUniqueError clears specific field error', async () => {
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: true, 
        email_exists: false 
      });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      // Trigger ZID error
      act(() => {
        result.current.validateZid('Z0123456');
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.zid).toBe('This ZID is already in use');
      });

      // Clear ZID error
      act(() => {
        result.current.clearUniqueError('zid');
      });

      expect(result.current.uniqueErrors.zid).toBeNull();
    });

    it('clearAllUniqueErrors clears all errors', async () => {
      // Set up mock to return both errors
      employeeValidationApi.validateUnique
        .mockResolvedValueOnce({ zid_exists: true, email_exists: false })
        .mockResolvedValueOnce({ zid_exists: false, email_exists: true });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      // Trigger ZID error
      act(() => {
        result.current.validateZid('Z0123456');
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.zid).toBe('This ZID is already in use');
      });

      // Trigger email error
      act(() => {
        result.current.validateEmail('existing@example.com');
      });

      await waitFor(() => {
        expect(result.current.uniqueErrors.email).toBe('This email is already in use');
      });

      // Clear all
      act(() => {
        result.current.clearAllUniqueErrors();
      });

      expect(result.current.uniqueErrors.zid).toBeNull();
      expect(result.current.uniqueErrors.email).toBeNull();
    });
  });

  describe('6. Utility Methods', () => {
    it('hasUniqueErrors returns true when ZID has error', async () => {
      employeeValidationApi.validateUnique.mockResolvedValue({ 
        zid_exists: true, 
        email_exists: false 
      });

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateZid('Z0123456');
      });

      await waitFor(() => {
        expect(result.current.hasUniqueErrors()).toBe(true);
      });
    });

    it('isAnyValidating returns true during validation', async () => {
      let resolvePromise;
      employeeValidationApi.validateUnique.mockImplementation(() => 
        new Promise(resolve => { resolvePromise = resolve; })
      );

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateZid('Z0123456');
      });

      // During validation, isValidating should be true
      await waitFor(() => {
        expect(result.current.isAnyValidating()).toBe(true);
      });

      // Cleanup: resolve the promise
      await act(async () => {
        resolvePromise({ zid_exists: false, email_exists: false });
      });
    });
  });

  describe('7. API Error Handling', () => {
    it('does not show error on API failure', async () => {
      employeeValidationApi.validateUnique.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useUniqueEmployeeValidation({ debounceDelay: 0 }));
      
      act(() => {
        result.current.validateZid('Z0123456');
      });

      // Should not show error - let server-side validation catch it on save
      await waitFor(() => {
        expect(result.current.uniqueErrors.zid).toBeNull();
        expect(result.current.isValidating.zid).toBe(false);
      });
    });
  });
});
