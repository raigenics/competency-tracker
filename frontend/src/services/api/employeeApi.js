import httpClient from './httpClient.js';
import { mockEmployees } from '../../data/mockEmployees.js';

// TODO: Replace with actual FastAPI calls
export const employeeApi = {
  // Get paginated list of employees
  async getEmployees(params = {}) {
    try {
      // TODO: return await httpClient.get('/employees', params);
      console.log('Mock: Fetching employees with params:', params);
      
      // Simulate API response structure
      return {
        items: mockEmployees,
        total: mockEmployees.length,
        page: params.page || 1,
        size: params.size || 10,
        has_next: false,
        has_previous: false
      };
    } catch (error) {
      console.error('Failed to fetch employees:', error);
      throw error;
    }
  },

  // Get specific employee by ID
  async getEmployee(employeeId) {
    try {
      // TODO: return await httpClient.get(`/employees/${employeeId}`);
      console.log('Mock: Fetching employee:', employeeId);
      
      const employee = mockEmployees.find(emp => emp.id === employeeId);
      if (!employee) {
        throw new Error('Employee not found');
      }
      return employee;
    } catch (error) {
      console.error('Failed to fetch employee:', error);
      throw error;
    }
  },

  // Get employee competency profile
  async getEmployeeProfile(employeeId) {
    try {
      // TODO: return await httpClient.get(`/competencies/employee/${employeeId}/profile`);
      console.log('Mock: Fetching employee profile:', employeeId);
      
      const employee = mockEmployees.find(emp => emp.id === employeeId);
      if (!employee) {
        throw new Error('Employee not found');
      }
      
      // Simulate profile structure
      return {
        employee_id: employee.id,
        employee_name: employee.name,
        role: employee.role,
        organization: {
          sub_segment: employee.subSegment,
          project: employee.project,
          team: employee.team
        },
        skills: employee.skills.map(skill => ({
          ...skill,
          emp_skill_id: Math.floor(Math.random() * 1000) + 1
        })),
        competency_summary: {
          Expert: employee.skills.filter(s => s.proficiency === 'Expert').length,
          Proficient: employee.skills.filter(s => s.proficiency === 'Proficient').length,
          Intermediate: employee.skills.filter(s => s.proficiency === 'Intermediate').length,
          Beginner: employee.skills.filter(s => s.proficiency === 'Beginner').length
        },
        total_skills: employee.skills.length,
        last_updated: employee.lastUpdated
      };
    } catch (error) {
      console.error('Failed to fetch employee profile:', error);
      throw error;
    }
  },

  // Get employees by list of IDs (for "View All with Skill" feature)
  async getEmployeesByIds(employeeIds) {
    try {
      const response = await httpClient.post('/employees/by-ids', {
        employee_ids: employeeIds
      });
      return response.results || [];
    } catch (error) {
      console.error('Failed to fetch employees by IDs:', error);
      throw error;
    }
  },

  // Update employee skill
  async updateEmployeeSkill(empSkillId, skillData) {
    try {
      // TODO: return await httpClient.put(`/competencies/employee-skill/${empSkillId}`, skillData);
      console.log('Mock: Updating employee skill:', empSkillId, skillData);
      
      return {
        message: 'Employee skill updated successfully',
        emp_skill_id: empSkillId,
        history_id: Math.floor(Math.random() * 1000) + 1,
        updated_fields: skillData
      };
    } catch (error) {
      console.error('Failed to update employee skill:', error);
      throw error;
    }
  },

  // Create new employee skill
  async createEmployeeSkill(skillData) {
    try {
      // TODO: return await httpClient.post('/competencies/employee-skill', skillData);
      console.log('Mock: Creating employee skill:', skillData);
      
      return {
        message: 'Employee skill created successfully',
        emp_skill_id: Math.floor(Math.random() * 1000) + 1,
        history_id: Math.floor(Math.random() * 1000) + 1
      };
    } catch (error) {
      console.error('Failed to create employee skill:', error);
      throw error;
    }
  },

  // Get skill history for employee
  async getSkillHistory(employeeId, params = {}) {
    try {
      // TODO: return await httpClient.get(`/competencies/employee/${employeeId}/skill-history`, params);
      console.log('Mock: Fetching skill history for employee:', employeeId);
      
      // Mock history data
      const mockHistory = [
        {
          history_id: 1,
          employee_id: employeeId,
          employee_name: mockEmployees.find(e => e.id === employeeId)?.name,
          skill_name: 'ReactJS',
          action: 'UPDATE',
          old_proficiency_name: 'Proficient',
          new_proficiency_name: 'Expert',
          changed_at: '2024-12-01T10:30:00',
          changed_by: 'manager',
          change_reason: 'Annual review - demonstrated advanced capabilities',
          change_source: 'UI'
        }
      ];
      
      return {
        items: mockHistory,
        total: mockHistory.length,
        page: 1,
        size: 10,
        has_next: false,
        has_previous: false
      };
    } catch (error) {
      console.error('Failed to fetch skill history:', error);
      throw error;
    }
  }
};

export default employeeApi;
