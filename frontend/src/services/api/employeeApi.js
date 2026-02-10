import httpClient from './httpClient.js';

// Employee API service
export const employeeApi = {// Get employee suggestions for autocomplete
  async getSuggestions(query, limit = 8) {
    try {
      return await httpClient.get('/employees/suggest', { q: query, limit });
    } catch (error) {
      console.error('Failed to fetch employee suggestions:', error);
      throw error;
    }
  },  // Get paginated list of employees
  async getEmployees(params = {}, options = {}) {
    try {
      // Call real backend API with ID-based filters
      console.log('Fetching employees from API with params:', params);
      
      const response = await httpClient.get('/employees', params, options);
      
      // Backend returns: { items, total, page, size, has_next, has_previous }
      return response;
    } catch (error) {
      // Don't log abort errors as failures (expected during cleanup)
      if (error.name === 'AbortError') {
        throw error;
      }
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
  },  // Get employee competency profile
  async getEmployeeProfile(employeeId) {
    try {
      const response = await httpClient.get(`/competencies/employee/${employeeId}/profile`);
      
      // Transform backend response to match frontend expectations
      return {
        employee_id: response.employee_id,
        employee_name: response.employee_name,
        role: response.role?.role_name || response.role,
        start_date_of_working: response.start_date_of_working,
        organization: response.organization,        skills: (response.skills || []).map(skill => ({
          skillName: skill.skill_name,
          proficiency: skill.proficiency?.level_name || skill.proficiency,
          proficiencyLevelId: skill.proficiency?.proficiency_level_id || null,
          category: skill.category || '–',
          yearsOfExperience: skill.years_experience || 0,
          lastUsed: skill.last_used || null,
          lastUpdated: skill.last_updated || null,
          certification: skill.certification || null,
          emp_skill_id: skill.emp_skill_id
        })),
        competency_summary: response.competency_summary || {},
        total_skills: response.skills?.length || 0,
        last_updated: response.last_updated
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
  },

  // Create new employee (basic details only, no skills)
  async createEmployee(employeeData) {
    try {
      const response = await httpClient.post('/employees/', employeeData);
      return response;
    } catch (error) {
      console.error('Failed to create employee:', error);
      throw error;
    }
  },

  // Save employee skills (bulk replace-all)
  async saveEmployeeSkills(employeeId, skills) {
    try {
      const response = await httpClient.post(`/employees/${employeeId}/skills`, {
        skills: skills
      });
      return response;
    } catch (error) {
      console.error('Failed to save employee skills:', error);
      throw error;
    }
  }
};

export default employeeApi;
