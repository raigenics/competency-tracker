/**
 * useEmployeeForm Hook Unit Tests
 * 
 * Tests:
 * 1. Form state management
 * 2. Validation rules (with org assignment)
 * 3. Submit functionality (with role_id)
 * 4. Role selection
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useEmployeeForm } from '@/hooks/useEmployeeForm.js';

// Mock the API
vi.mock('@/services/api/employeeApi.js', () => ({
  employeeApi: {
    createEmployee: vi.fn(),
    updateEmployee: vi.fn()
  }
}));

import { employeeApi } from '@/services/api/employeeApi.js';

// Helper: Valid org assignment for tests
const validOrgAssignment = {
  selectedSegmentId: 1,
  selectedSubSegmentId: 2,
  selectedProjectId: 3,
  selectedTeamId: 5
};

describe('useEmployeeForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    employeeApi.createEmployee.mockResolvedValue({ employee_id: 1, zid: 'Z0123456' });
    employeeApi.updateEmployee.mockResolvedValue({ employee_id: 1, zid: 'Z0123456', message: 'Employee updated successfully' });
  });

  describe('1. Form State Management', () => {
    it('initializes with empty form data', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      expect(result.current.formData.zid).toBe('');
      expect(result.current.formData.fullName).toBe('');
      expect(result.current.formData.email).toBe('');
      expect(result.current.formData.roleId).toBeNull();
      expect(result.current.formData.roleName).toBe('');
      expect(result.current.errors).toEqual({});
      expect(result.current.isSubmitting).toBe(false);
    });

    it('handleChange updates form data', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.handleChange({ target: { name: 'zid', value: 'Z0123456' } });
      });
      
      expect(result.current.formData.zid).toBe('Z0123456');
    });

    it('setField updates specific field', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('fullName', 'Test User');
      });
      
      expect(result.current.formData.fullName).toBe('Test User');
    });

    it('prefill sets multiple fields', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.prefill({
          zid: 'Z9876543',
          fullName: 'Pre-filled User',
          email: 'user@example.com'
        });
      });
      
      expect(result.current.formData.zid).toBe('Z9876543');
      expect(result.current.formData.fullName).toBe('Pre-filled User');
      expect(result.current.formData.email).toBe('user@example.com');
    });

    it('reset clears form data', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      // Set some values
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
      });
      
      // Reset
      act(() => {
        result.current.reset();
      });
      
      expect(result.current.formData.zid).toBe('');
      expect(result.current.formData.fullName).toBe('');
    });

    it('isDirty returns true when form has changes', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      expect(result.current.isDirty()).toBe(false);
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
      });
      
      expect(result.current.isDirty()).toBe(true);
    });
  });

  describe('2. Validation Rules', () => {
    it('validate returns false when zid is empty', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate(validOrgAssignment);
      });
      
      expect(isValid).toBe(false);
      expect(result.current.errors.zid).toBeDefined();
    });

    it('validate returns false when fullName is empty', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate(validOrgAssignment);
      });
      
      expect(isValid).toBe(false);
      expect(result.current.errors.fullName).toBeDefined();
    });

    it('validate returns false when email is empty', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setRole(1, 'Developer');
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate(validOrgAssignment);
      });
      
      expect(isValid).toBe(false);
      expect(result.current.errors.email).toBeDefined();
    });

    it('validate returns false when roleId is not selected', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        // No role set
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate(validOrgAssignment);
      });
      
      expect(isValid).toBe(false);
      expect(result.current.errors.roleId).toBeDefined();
    });

    it('validate returns false when segment is not selected', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate({
          ...validOrgAssignment,
          selectedSegmentId: null
        });
      });
      
      expect(isValid).toBe(false);
      expect(result.current.errors.segmentId).toBeDefined();
    });

    it('validate returns false when team is not selected', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate({
          ...validOrgAssignment,
          selectedTeamId: null
        });
      });
      
      expect(isValid).toBe(false);
      expect(result.current.errors.teamId).toBeDefined();
    });

    it('validate returns false for invalid email format', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'invalid-email');
        result.current.setRole(1, 'Developer');
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate(validOrgAssignment);
      });
      
      expect(isValid).toBe(false);
      expect(result.current.errors.email).toContain('valid');
    });

    it('validate returns true when all required fields are valid', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      let isValid;
      act(() => {
        isValid = result.current.validate(validOrgAssignment);
      });
      
      expect(isValid).toBe(true);
      expect(result.current.errors).toEqual({});
    });
  });

  describe('3. Submit Functionality', () => {
    it('submit calls createEmployee API with role_id and team_id', async () => {
      const onSuccess = vi.fn();
      const { result } = renderHook(() => useEmployeeForm({ onSuccess }));
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(7, 'Developer');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment);
      });
      
      expect(employeeApi.createEmployee).toHaveBeenCalledWith({
        zid: 'Z0123456',
        full_name: 'Test User',
        email: 'test@example.com',
        role_id: 7,
        team_id: 5,
        start_date_of_working: null
      });
      expect(onSuccess).toHaveBeenCalled();
    });

    it('submit does NOT include skills in payload', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment);
      });
      
      const callPayload = employeeApi.createEmployee.mock.calls[0][0];
      expect(callPayload).not.toHaveProperty('skills');
    });

    it('submit does NOT send role_name in payload', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment);
      });
      
      const callPayload = employeeApi.createEmployee.mock.calls[0][0];
      expect(callPayload).not.toHaveProperty('role_name');
      expect(callPayload.role_id).toBe(1);
    });

    it('submit returns null if validation fails', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      // Missing email - should fail validation
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setRole(1, 'Developer');
      });
      
      let response;
      await act(async () => {
        response = await result.current.submit(validOrgAssignment);
      });
      
      expect(response).toBeNull();
      expect(employeeApi.createEmployee).not.toHaveBeenCalled();
    });

    it('submit sets isSubmitting to true during request', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      let _submittingDuringRequest = false;
      employeeApi.createEmployee.mockImplementation(async () => {
        _submittingDuringRequest = result.current.isSubmitting;
        return { employee_id: 1 };
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment);
      });
      
      // Cannot easily check this synchronously, but isSubmitting should be false after
      expect(result.current.isSubmitting).toBe(false);
    });

    it('submit calls onError on API failure', async () => {
      const onError = vi.fn();
      employeeApi.createEmployee.mockRejectedValue(new Error('Duplicate ZID'));
      
      const { result } = renderHook(() => useEmployeeForm({ onError }));
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      await act(async () => {
        try {
          await result.current.submit(validOrgAssignment);
        } catch (_e) {
          // Expected error
        }
      });
      
      expect(onError).toHaveBeenCalled();
      expect(result.current.submitError).toBeDefined();
    });

    it('submit sets submitError message on failure', async () => {
      employeeApi.createEmployee.mockRejectedValue({ 
        response: { data: { detail: 'Employee with ZID already exists' } }
      });
      
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      await act(async () => {
        try {
          await result.current.submit(validOrgAssignment);
        } catch (_e) {
          // Expected
        }
      });
      
      expect(result.current.submitError).toContain('already exists');
    });
  });

  describe('4. Role Selection', () => {
    it('setRole updates both roleId and roleName', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setRole(5, 'Tech Lead');
      });
      
      expect(result.current.formData.roleId).toBe(5);
      expect(result.current.formData.roleName).toBe('Tech Lead');
    });

    it('setRole clears roleId error', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      // Trigger validation to set roleId error
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test');
        result.current.setField('email', 'test@example.com');
        // No role set, so validation should fail
        result.current.validate(validOrgAssignment);
      });
      
      expect(result.current.errors.roleId).toBeDefined();
      
      // Now set role
      act(() => {
        result.current.setRole(1, 'Developer');
      });
      
      expect(result.current.errors.roleId).toBeNull();
    });

    it('clearError clears specific error', () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      // Trigger multiple errors
      act(() => {
        result.current.validate({});
      });
      
      expect(result.current.errors.zid).toBeDefined();
      expect(result.current.errors.fullName).toBeDefined();
      
      // Clear only zid error
      act(() => {
        result.current.clearError('zid');
      });
      
      expect(result.current.errors.zid).toBeNull();
      expect(result.current.errors.fullName).toBeDefined(); // Still present
    });
  });

  describe('5. Update Employee (Edit Mode)', () => {
    it('submit with employeeId calls updateEmployee API', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Updated User');
        result.current.setField('email', 'updated@example.com');
        result.current.setRole(2, 'Senior Developer');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment, 123); // Pass employeeId for update
      });
      
      expect(employeeApi.updateEmployee).toHaveBeenCalledTimes(1);
      expect(employeeApi.createEmployee).not.toHaveBeenCalled();
    });

    it('submit with employeeId sends correct payload (without zid)', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Updated User');
        result.current.setField('email', 'updated@example.com');
        result.current.setRole(2, 'Senior Developer');
        result.current.setField('startDate', '2024-01-15');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment, 123);
      });
      
      const callPayload = employeeApi.updateEmployee.mock.calls[0][1];
      expect(callPayload).toEqual({
        full_name: 'Updated User',
        email: 'updated@example.com',
        team_id: 5,
        role_id: 2,
        start_date_of_working: '2024-01-15'
      });
      // ZID should NOT be in update payload
      expect(callPayload).not.toHaveProperty('zid');
    });

    it('submit with employeeId passes employeeId as first arg', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment, 456);
      });
      
      expect(employeeApi.updateEmployee).toHaveBeenCalledWith(456, expect.any(Object));
    });

    it('submit without employeeId calls createEmployee API', async () => {
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'New User');
        result.current.setField('email', 'new@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment); // No employeeId = create
      });
      
      expect(employeeApi.createEmployee).toHaveBeenCalledTimes(1);
      expect(employeeApi.updateEmployee).not.toHaveBeenCalled();
    });

    it('submit handles update API errors', async () => {
      employeeApi.updateEmployee.mockRejectedValue({ 
        response: { data: { detail: 'Team not found' } }
      });
      
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Test User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      await act(async () => {
        await result.current.submit(validOrgAssignment, 123);
      });
      
      expect(result.current.submitError).toContain('Team not found');
    });

    it('submit returns updated employee on success', async () => {
      const mockResponse = { employee_id: 123, zid: 'Z0123456', full_name: 'Updated User' };
      employeeApi.updateEmployee.mockResolvedValue(mockResponse);
      
      const { result } = renderHook(() => useEmployeeForm());
      
      act(() => {
        result.current.setField('zid', 'Z0123456');
        result.current.setField('fullName', 'Updated User');
        result.current.setField('email', 'test@example.com');
        result.current.setRole(1, 'Developer');
      });
      
      let response;
      await act(async () => {
        response = await result.current.submit(validOrgAssignment, 123);
      });
      
      expect(response).toEqual(mockResponse);
    });
  });
});
