import httpClient from './httpClient.js';

// TODO: Replace with actual FastAPI calls
export const skillApi = {
  // Get paginated list of skills (general/mock)
  async getSkillsPaginated(params = {}) {
    try {
      // TODO: return await httpClient.get('/skills', params);
      console.log('Mock: Fetching skills with params:', params);
      
      const mockSkills = [
        { skill_id: 1, skill_name: 'ReactJS', category: { category_name: 'Frontend Frameworks' }, employee_count: 47 },
        { skill_id: 2, skill_name: 'Python', category: { category_name: 'Programming Languages' }, employee_count: 52 },
        { skill_id: 3, skill_name: 'AWS', category: { category_name: 'Cloud Platforms' }, employee_count: 36 },
        { skill_id: 4, skill_name: 'Node.js', category: { category_name: 'Backend Frameworks' }, employee_count: 34 },
        { skill_id: 5, skill_name: 'TypeScript', category: { category_name: 'Programming Languages' }, employee_count: 28 }
      ];
      
      return {
        items: mockSkills,
        total: mockSkills.length,
        page: params.page || 1,
        size: params.size || 10,
        has_next: false,
        has_previous: false
      };
    } catch (error) {
      console.error('Failed to fetch skills:', error);
      throw error;
    }
  },

  // Get skill details by ID
  async getSkill(skillId) {
    try {
      // TODO: return await httpClient.get(`/skills/${skillId}`);
      console.log('Mock: Fetching skill:', skillId);
      
      return {
        skill_id: skillId,
        skill_name: 'ReactJS',
        category: { category_name: 'Frontend Frameworks' },
        employee_count: 47,
        avg_proficiency: 3.2,
        certification_rate: 0.65
      };
    } catch (error) {
      console.error('Failed to fetch skill:', error);
      throw error;
    }
  },

  // Get skill progression data
  async getSkillProgression(skillId, _params = {}) {
    try {
      // TODO: return await httpClient.get(`/competencies/skill/${skillId}/progression`, params);
      console.log('Mock: Fetching skill progression:', skillId);
      
      const mockProgression = [
        {
          employee_id: 1,
          employee_name: 'Sarah Johnson',
          skill_id: skillId,
          skill_name: 'ReactJS',
          progression: [
            {
              from_proficiency_name: 'Proficient',
              to_proficiency_name: 'Expert',
              changed_at: '2024-06-15T09:00:00',
              change_reason: 'Completed advanced React course'
            }
          ],
          current_proficiency: 'Expert',
          progression_trend: 'improving'
        }
      ];
      
      return mockProgression;
    } catch (error) {
      console.error('Failed to fetch skill progression:', error);
      throw error;
    }
  },

  // Search skills by query
  async searchSkills(query) {
    try {
      // TODO: return await httpClient.get('/skills', { search: query });
      console.log('Mock: Searching skills:', query);
      
      // Mock search results
      return {
        items: [
          { skill_id: 1, skill_name: 'ReactJS', category: 'Frontend' },
          { skill_id: 2, skill_name: 'React Native', category: 'Mobile' }
        ],
        total: 2
      };
    } catch (error) {
      console.error('Failed to search skills:', error);
      throw error;
    }
  },

  // Get skill summary statistics
  async getSkillSummary(skillId) {
    try {
      const response = await httpClient.get(`/skills/${skillId}/summary`);
      return response;
    } catch (error) {
      console.error('Failed to fetch skill summary:', error);
      throw error;
    }
  },

  // Get complete taxonomy tree (all categories, subcategories, skills)
  async getTaxonomyTree() {
    try {
      const response = await httpClient.get('/skills/taxonomy/tree');
      return response;
    } catch (error) {
      console.error('Failed to fetch taxonomy tree:', error);
      throw error;
    }
  },

  // === Lazy-loading Taxonomy Methods ===

  // Get categories with counts only (for initial load)
  async getCategories() {
    try {
      const response = await httpClient.get('/skills/capability/categories');
      return response;
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      throw error;
    }
  },

  // Get subcategories for a specific category
  async getSubcategories(categoryId) {
    try {
      const response = await httpClient.get(`/skills/capability/categories/${categoryId}/subcategories`);
      return response;
    } catch (error) {
      console.error(`Failed to fetch subcategories for category ${categoryId}:`, error);
      throw error;
    }
  },

  // Get skills for a specific subcategory
  async getSkills(subcategoryId) {
    try {
      const response = await httpClient.get(`/skills/capability/subcategories/${subcategoryId}/skills`);
      return response;
    } catch (error) {
      console.error(`Failed to fetch skills for subcategory ${subcategoryId}:`, error);
      throw error;
    }
  },

  // Search skills across entire taxonomy with hierarchy path
  async searchSkillsInTaxonomy(query) {
    try {
      const response = await httpClient.get('/skills/capability/search', { q: query });
      return response;
    } catch (error) {
      console.error(`Failed to search skills with query '${query}':`, error);
      throw error;
    }
  }
};

export default skillApi;
