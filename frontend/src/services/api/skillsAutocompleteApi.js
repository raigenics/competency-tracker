/**
 * Skills Autocomplete API Service
 * 
 * SRP: Handles fetching skills for autocomplete/autosuggest functionality.
 * Reuses the existing /skills endpoint with search parameter.
 */
import httpClient from './httpClient.js';

/**
 * @typedef {Object} SkillSuggestion
 * @property {number} skill_id - Unique skill ID
 * @property {string} skill_name - Display name of the skill
 * @property {string} category_name - Parent category name
 * @property {string|null} subcategory_name - Subcategory name (may be null)
 * @property {number} employee_count - Number of employees with this skill
 */

export const skillsAutocompleteApi = {
  /**
   * Search skills for autocomplete functionality.
   * 
   * @param {string} query - Search term (matches skill_name)
   * @param {number} limit - Maximum results to return
   * @returns {Promise<SkillSuggestion[]>} Array of skill suggestions
   */
  async searchSkills(query = '', limit = 10) {
    try {
      // Use existing /skills endpoint with search param
      const response = await httpClient.get('/skills/', {
        search: query || undefined,
        page: 1,
        size: limit
      });
      
      // Transform response to suggestion format
      const items = response.items || [];
      return items.map(skill => ({
        skill_id: skill.skill_id,
        skill_name: skill.skill_name,
        category_name: skill.category?.category_name || 'Uncategorized',
        subcategory_name: skill.category?.subcategory_name || null,
        employee_count: skill.employee_count || 0
      }));
    } catch (error) {
      console.error('[skillsAutocompleteApi] Failed to search skills:', error);
      throw error;
    }
  },

  /**
   * Get all skills (limited) for initial dropdown population.
   * 
   * @param {number} limit - Maximum results to return
   * @returns {Promise<SkillSuggestion[]>} Array of skill suggestions
   */
  async getAllSkills(limit = 100) {
    return this.searchSkills('', limit);
  }
};

export default skillsAutocompleteApi;
