/**
 * Unit tests for employeeApi service
 * 
 * Tests API calls for Employee Profile feature and related employee operations.
 * Covers success and error scenarios for all endpoints.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { employeeApi } from '@/services/api/employeeApi.js';
import httpClient from '@/services/api/httpClient.js';

// Mock the httpClient
vi.mock('@/services/api/httpClient.js', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}));

describe('employeeApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'groupCollapsed').mockImplementation(() => {});
    vi.spyOn(console, 'groupEnd').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // getSuggestions
  // =========================================================================
  describe('getSuggestions', () => {
    it('should return suggestions for valid query', async () => {
      // Arrange
      const mockSuggestions = [
        { id: 1, name: 'John Doe' },
        { id: 2, name: 'Jane Doe' }
      ];
      httpClient.get.mockResolvedValueOnce(mockSuggestions);

      // Act
      const result = await employeeApi.getSuggestions('Doe');

      // Assert
      expect(result).toEqual(mockSuggestions);
      expect(httpClient.get).toHaveBeenCalledWith('/employees/suggest', { q: 'Doe', limit: 8 });
    });

    it('should use custom limit when provided', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce([]);

      // Act
      await employeeApi.getSuggestions('test', 5);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/employees/suggest', { q: 'test', limit: 5 });
    });

    it('should throw error on API failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Network error'));

      // Act & Assert
      await expect(employeeApi.getSuggestions('test')).rejects.toThrow('Network error');
      expect(console.error).toHaveBeenCalledWith('Failed to fetch employee suggestions:', expect.any(Error));
    });
  });

  // =========================================================================
  // getEmployees
  // =========================================================================
  describe('getEmployees', () => {
    it('should return paginated employees list', async () => {
      // Arrange
      const mockResponse = {
        items: [{ id: 1, name: 'John' }, { id: 2, name: 'Jane' }],
        total: 2,
        page: 1,
        size: 10,
        has_next: false,
        has_previous: false
      };
      httpClient.get.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await employeeApi.getEmployees({ page: 1, size: 10 });

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.get).toHaveBeenCalledWith('/employees', { page: 1, size: 10 }, {});
    });

    it('should pass options to httpClient', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce({ items: [] });
      const mockSignal = new AbortController().signal;

      // Act
      await employeeApi.getEmployees({}, { signal: mockSignal });

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/employees', {}, { signal: mockSignal });
    });

    it('should re-throw AbortError without logging', async () => {
      // Arrange
      const abortError = new Error('Aborted');
      abortError.name = 'AbortError';
      httpClient.get.mockRejectedValueOnce(abortError);

      // Act & Assert
      await expect(employeeApi.getEmployees({})).rejects.toThrow('Aborted');
      expect(console.error).not.toHaveBeenCalled();
    });

    it('should log and throw non-abort errors', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Server error'));

      // Act & Assert
      await expect(employeeApi.getEmployees({})).rejects.toThrow('Server error');
      expect(console.error).toHaveBeenCalledWith('Failed to fetch employees:', expect.any(Error));
    });
  });

  // =========================================================================
  // getEmployee
  // =========================================================================
  describe('getEmployee', () => {
    it('should return employee by ID', async () => {
      // Arrange
      const mockEmployee = { id: 123, name: 'John Doe', role: 'Developer' };
      httpClient.get.mockResolvedValueOnce(mockEmployee);

      // Act
      const result = await employeeApi.getEmployee(123);

      // Assert
      expect(result).toEqual(mockEmployee);
      expect(httpClient.get).toHaveBeenCalledWith('/employees/123');
    });

    it('should throw error for invalid employee ID', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Employee not found'));

      // Act & Assert
      await expect(employeeApi.getEmployee(999)).rejects.toThrow('Employee not found');
      expect(console.error).toHaveBeenCalledWith('Failed to fetch employee:', expect.any(Error));
    });
  });

  // =========================================================================
  // getEmployeeProfile (Core Employee Profile API)
  // =========================================================================
  describe('getEmployeeProfile', () => {
    const mockProfileResponse = {
      employee_id: 1,
      employee_name: 'John Doe',
      role: { role_id: 10, role_name: 'Software Engineer' },
      start_date_of_working: '2020-01-15',
      organization: { segment: 'Engineering', sub_segment: 'Backend' },
      skills: [
        {
          emp_skill_id: 100,
          skill_name: 'Python',
          proficiency: { proficiency_level_id: 3, level_name: 'Expert' },
          category: 'Programming',
          years_experience: 5,
          last_used: '2024-12-01',
          last_updated: '2024-12-15',
          certification: 'AWS Certified'
        },
        {
          emp_skill_id: 101,
          skill_name: 'JavaScript',
          proficiency: { proficiency_level_id: 2, level_name: 'Proficient' },
          category: 'Programming',
          years_experience: 3,
          last_used: null,
          last_updated: null,
          certification: null
        }
      ],
      competency_summary: { total_skills: 2, expert_count: 1 },
      last_updated: '2024-12-15T10:30:00'
    };

    it('should fetch and transform employee profile', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce(mockProfileResponse);

      // Act
      const result = await employeeApi.getEmployeeProfile(1);

      // Assert
      expect(httpClient.get).toHaveBeenCalledWith('/competencies/employee/1/profile');
      expect(result.employee_id).toBe(1);
      expect(result.employee_name).toBe('John Doe');
      expect(result.role).toBe('Software Engineer');
      expect(result.total_skills).toBe(2);
    });

    it('should transform skills array correctly', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce(mockProfileResponse);

      // Act
      const result = await employeeApi.getEmployeeProfile(1);

      // Assert
      expect(result.skills).toHaveLength(2);
      expect(result.skills[0]).toEqual({
        skillName: 'Python',
        proficiency: 'Expert',
        proficiencyLevelId: 3,
        category: 'Programming',
        yearsOfExperience: 5,
        lastUsed: '2024-12-01',
        lastUpdated: '2024-12-15',
        certification: 'AWS Certified',
        emp_skill_id: 100
      });
    });

    it('should handle missing optional fields with defaults', async () => {
      // Arrange
      const minimalProfile = {
        employee_id: 2,
        employee_name: 'Jane Doe',
        role: null,
        skills: [{
          emp_skill_id: 200,
          skill_name: 'React'
          // No proficiency, category, years_experience, etc.
        }]
      };
      httpClient.get.mockResolvedValueOnce(minimalProfile);

      // Act
      const result = await employeeApi.getEmployeeProfile(2);

      // Assert
      expect(result.role).toBeNull();
      expect(result.competency_summary).toEqual({});
      expect(result.total_skills).toBe(1);
      expect(result.skills[0]).toEqual({
        skillName: 'React',
        proficiency: undefined,
        proficiencyLevelId: null,
        category: '–',
        yearsOfExperience: 0,
        lastUsed: null,
        lastUpdated: null,
        certification: null,
        emp_skill_id: 200
      });
    });

    it('should handle empty skills array', async () => {
      // Arrange
      const profileWithNoSkills = {
        employee_id: 3,
        employee_name: 'New Employee',
        skills: []
      };
      httpClient.get.mockResolvedValueOnce(profileWithNoSkills);

      // Act
      const result = await employeeApi.getEmployeeProfile(3);

      // Assert
      expect(result.skills).toEqual([]);
      expect(result.total_skills).toBe(0);
    });

    it('should handle null skills array', async () => {
      // Arrange
      const profileWithNullSkills = {
        employee_id: 4,
        employee_name: 'Another Employee',
        skills: null
      };
      httpClient.get.mockResolvedValueOnce(profileWithNullSkills);

      // Act
      const result = await employeeApi.getEmployeeProfile(4);

      // Assert
      expect(result.skills).toEqual([]);
      expect(result.total_skills).toBe(0);
    });

    it('should handle role as string (legacy format)', async () => {
      // Arrange
      const legacyProfile = {
        employee_id: 5,
        employee_name: 'Legacy User',
        role: 'Manager',
        skills: []
      };
      httpClient.get.mockResolvedValueOnce(legacyProfile);

      // Act
      const result = await employeeApi.getEmployeeProfile(5);

      // Assert
      expect(result.role).toBe('Manager');
    });

    it('should throw error when profile fetch fails', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Employee not found'));

      // Act & Assert
      await expect(employeeApi.getEmployeeProfile(999)).rejects.toThrow('Employee not found');
      expect(console.error).toHaveBeenCalledWith('Failed to fetch employee profile:', expect.any(Error));
    });

    it('should include organization structure', async () => {
      // Arrange
      httpClient.get.mockResolvedValueOnce(mockProfileResponse);

      // Act
      const result = await employeeApi.getEmployeeProfile(1);

      // Assert
      expect(result.organization).toEqual({ segment: 'Engineering', sub_segment: 'Backend' });
      expect(result.start_date_of_working).toBe('2020-01-15');
      expect(result.last_updated).toBe('2024-12-15T10:30:00');
    });

    it('should handle proficiency as string (legacy format)', async () => {
      // Arrange
      const legacySkillProfile = {
        employee_id: 6,
        skills: [{
          emp_skill_id: 300,
          skill_name: 'Java',
          proficiency: 'Expert'  // String instead of object
        }]
      };
      httpClient.get.mockResolvedValueOnce(legacySkillProfile);

      // Act
      const result = await employeeApi.getEmployeeProfile(6);

      // Assert
      expect(result.skills[0].proficiency).toBe('Expert');
      expect(result.skills[0].proficiencyLevelId).toBeNull();
    });
  });

  // =========================================================================
  // getEmployeesByIds
  // =========================================================================
  describe('getEmployeesByIds', () => {
    it('should fetch employees by IDs', async () => {
      // Arrange
      const mockResults = [
        { id: 1, name: 'John' },
        { id: 2, name: 'Jane' }
      ];
      httpClient.post.mockResolvedValueOnce({ results: mockResults });

      // Act
      const result = await employeeApi.getEmployeesByIds([1, 2]);

      // Assert
      expect(result).toEqual(mockResults);
      expect(httpClient.post).toHaveBeenCalledWith('/employees/by-ids', { employee_ids: [1, 2] });
    });

    it('should return empty array when no results', async () => {
      // Arrange
      httpClient.post.mockResolvedValueOnce({});

      // Act
      const result = await employeeApi.getEmployeesByIds([999]);

      // Assert
      expect(result).toEqual([]);
    });

    it('should throw error on API failure', async () => {
      // Arrange
      httpClient.post.mockRejectedValueOnce(new Error('Invalid IDs'));

      // Act & Assert
      await expect(employeeApi.getEmployeesByIds([1, 2])).rejects.toThrow('Invalid IDs');
      expect(console.error).toHaveBeenCalledWith('Failed to fetch employees by IDs:', expect.any(Error));
    });
  });

  // =========================================================================
  // updateEmployeeSkill (Mock implementation)
  // =========================================================================
  describe('updateEmployeeSkill', () => {
    it('should return mock success response', async () => {
      // Act
      const result = await employeeApi.updateEmployeeSkill(100, { proficiency_level_id: 3 });

      // Assert
      expect(result.message).toBe('Employee skill updated successfully');
      expect(result.emp_skill_id).toBe(100);
      expect(result.updated_fields).toEqual({ proficiency_level_id: 3 });
      expect(typeof result.history_id).toBe('number');
    });

    it('should log mock update details', async () => {
      // Act
      await employeeApi.updateEmployeeSkill(100, { proficiency_level_id: 2 });

      // Assert
      expect(console.log).toHaveBeenCalledWith('Mock: Updating employee skill:', 100, { proficiency_level_id: 2 });
    });
  });

  // =========================================================================
  // createEmployeeSkill (Mock implementation)
  // =========================================================================
  describe('createEmployeeSkill', () => {
    it('should return mock success response', async () => {
      // Act
      const result = await employeeApi.createEmployeeSkill({ 
        employee_id: 1, 
        skill_id: 50, 
        proficiency_level_id: 2 
      });

      // Assert
      expect(result.message).toBe('Employee skill created successfully');
      expect(typeof result.emp_skill_id).toBe('number');
      expect(typeof result.history_id).toBe('number');
    });

    it('should log mock creation details', async () => {
      // Arrange
      const skillData = { employee_id: 1, skill_id: 50 };

      // Act
      await employeeApi.createEmployeeSkill(skillData);

      // Assert
      expect(console.log).toHaveBeenCalledWith('Mock: Creating employee skill:', skillData);
    });
  });

  // =========================================================================
  // getSkillHistory (Mock implementation - currently has bug with undefined mockEmployees)
  // =========================================================================
  describe('getSkillHistory', () => {
    // Note: The current implementation references 'mockEmployees' which is undefined,
    // causing an error. These tests verify the error handling behavior.
    // When the API is properly implemented, these tests should be updated.
    
    it('should throw ReferenceError due to undefined mockEmployees in mock implementation', async () => {
      // Act & Assert
      await expect(employeeApi.getSkillHistory(1)).rejects.toThrow(ReferenceError);
    });

    it('should log error message when mock fails', async () => {
      // Act
      try {
        await employeeApi.getSkillHistory(1);
      } catch {
        // Expected to throw
      }

      // Assert - verify the error was logged before re-throwing
      expect(console.error).toHaveBeenCalledWith('Failed to fetch skill history:', expect.any(ReferenceError));
    });

    it('should log mock operation before error occurs', async () => {
      // Act
      try {
        await employeeApi.getSkillHistory(123, { page: 2 });
      } catch {
        // Expected to throw
      }

      // Assert - the console.log should have been called before the error
      expect(console.log).toHaveBeenCalledWith('Mock: Fetching skill history for employee:', 123);
    });
  });

  // =========================================================================
  // createEmployee
  // =========================================================================
  describe('createEmployee', () => {
    it('should create new employee', async () => {
      // Arrange
      const newEmployee = { name: 'New Person', role_id: 1 };
      const mockResponse = { id: 100, ...newEmployee };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await employeeApi.createEmployee(newEmployee);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith('/employees/', newEmployee);
    });

    it('should throw error on creation failure', async () => {
      // Arrange
      httpClient.post.mockRejectedValueOnce(new Error('Validation error'));

      // Act & Assert
      await expect(employeeApi.createEmployee({})).rejects.toThrow('Validation error');
      expect(console.error).toHaveBeenCalledWith('Failed to create employee:', expect.any(Error));
    });
  });

  // =========================================================================
  // updateEmployee
  // =========================================================================
  describe('updateEmployee', () => {
    it('should update existing employee', async () => {
      // Arrange
      const updateData = { name: 'Updated Name' };
      const mockResponse = { id: 1, name: 'Updated Name' };
      httpClient.put.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await employeeApi.updateEmployee(1, updateData);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.put).toHaveBeenCalledWith('/employees/1', updateData);
    });

    it('should throw error on update failure', async () => {
      // Arrange
      httpClient.put.mockRejectedValueOnce(new Error('Employee not found'));

      // Act & Assert
      await expect(employeeApi.updateEmployee(999, {})).rejects.toThrow('Employee not found');
      expect(console.error).toHaveBeenCalledWith('Failed to update employee:', expect.any(Error));
    });
  });

  // =========================================================================
  // saveEmployeeSkills
  // =========================================================================
  describe('saveEmployeeSkills', () => {
    it('should save employee skills bulk', async () => {
      // Arrange
      const skills = [
        { skill_id: 1, proficiency_level_id: 2 },
        { skill_id: 2, proficiency_level_id: 3 }
      ];
      const mockResponse = { message: 'Skills saved', updated: 2 };
      httpClient.post.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await employeeApi.saveEmployeeSkills(1, skills);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.post).toHaveBeenCalledWith('/employees/1/skills', { skills });
    });

    it('should handle empty skills array', async () => {
      // Arrange
      httpClient.post.mockResolvedValueOnce({ message: 'Skills cleared' });

      // Act
      const result = await employeeApi.saveEmployeeSkills(1, []);

      // Assert
      expect(result.message).toBe('Skills cleared');
      expect(httpClient.post).toHaveBeenCalledWith('/employees/1/skills', { skills: [] });
    });

    it('should throw error on save failure', async () => {
      // Arrange
      httpClient.post.mockRejectedValueOnce(new Error('Invalid skill data'));

      // Act & Assert
      await expect(employeeApi.saveEmployeeSkills(1, [])).rejects.toThrow('Invalid skill data');
      expect(console.error).toHaveBeenCalledWith('Failed to save employee skills:', expect.any(Error));
    });
  });

  // =========================================================================
  // getEmployeeEditBootstrap
  // =========================================================================
  describe('getEmployeeEditBootstrap', () => {
    it('should fetch bootstrap data for editing', async () => {
      // Arrange
      const mockBootstrap = {
        employee: { id: 1, name: 'John', segment_id: 10 },
        options: {
          segments: [{ id: 10, name: 'Segment A' }],
          sub_segments: [],
          projects: [],
          teams: []
        },
        skills: [],
        meta: {}
      };
      httpClient.get.mockResolvedValueOnce(mockBootstrap);

      // Act
      const result = await employeeApi.getEmployeeEditBootstrap(1);

      // Assert
      expect(result).toEqual(mockBootstrap);
      expect(httpClient.get).toHaveBeenCalledWith('/employees/1/edit-bootstrap');
    });

    it('should log bootstrap data summary', async () => {
      // Arrange
      const mockBootstrap = {
        employee: { segment_id: 1, sub_segment_id: 2, project_id: 3, team_id: 4 },
        options: {
          segments: [1, 2],
          sub_segments: [1],
          projects: [1, 2, 3],
          teams: []
        }
      };
      httpClient.get.mockResolvedValueOnce(mockBootstrap);

      // Act
      await employeeApi.getEmployeeEditBootstrap(1);

      // Assert
      expect(console.groupCollapsed).toHaveBeenCalledWith('[BOOTSTRAP][API]');
      expect(console.log).toHaveBeenCalledWith('employee ids', expect.any(Object));
      expect(console.log).toHaveBeenCalledWith('options count', expect.any(Object));
      expect(console.groupEnd).toHaveBeenCalled();
    });

    it('should throw error on fetch failure', async () => {
      // Arrange
      httpClient.get.mockRejectedValueOnce(new Error('Not found'));

      // Act & Assert
      await expect(employeeApi.getEmployeeEditBootstrap(999)).rejects.toThrow('Not found');
      expect(console.error).toHaveBeenCalledWith('Failed to fetch edit bootstrap:', expect.any(Error));
    });
  });

  // =========================================================================
  // deleteEmployee
  // =========================================================================
  describe('deleteEmployee', () => {
    it('should soft-delete employee', async () => {
      // Arrange
      const mockResponse = { message: 'Employee deleted', employee_id: 1 };
      httpClient.delete.mockResolvedValueOnce(mockResponse);

      // Act
      const result = await employeeApi.deleteEmployee(1);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(httpClient.delete).toHaveBeenCalledWith('/employees/1');
    });

    it('should throw error on deletion failure', async () => {
      // Arrange
      httpClient.delete.mockRejectedValueOnce(new Error('Cannot delete'));

      // Act & Assert
      await expect(employeeApi.deleteEmployee(1)).rejects.toThrow('Cannot delete');
      expect(console.error).toHaveBeenCalledWith('Failed to delete employee:', expect.any(Error));
    });
  });
});
