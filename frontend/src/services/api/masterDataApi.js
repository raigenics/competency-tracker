/**
 * Master Data API client
 * Handles API calls for Master Data management (Skill Taxonomy, etc.)
 */
import httpClient from './httpClient';

/**
 * @typedef {Object} TaxonomySkill
 * @property {number} id - Skill ID
 * @property {string} name - Skill name
 * @property {string|null} description - Skill description
 * @property {number} employee_count - Number of employees with this skill
 * @property {string|null} created_at - Creation timestamp (ISO format)
 * @property {string|null} created_by - Creator username
 */

/**
 * @typedef {Object} TaxonomySubCategory
 * @property {number} id - SubCategory ID
 * @property {string} name - SubCategory name
 * @property {string|null} description - SubCategory description
 * @property {string|null} created_at - Creation timestamp (ISO format)
 * @property {string|null} created_by - Creator username
 * @property {TaxonomySkill[]} skills - Skills in this subcategory
 */

/**
 * @typedef {Object} TaxonomyCategory
 * @property {number} id - Category ID
 * @property {string} name - Category name
 * @property {string|null} description - Category description
 * @property {string|null} created_at - Creation timestamp (ISO format)
 * @property {string|null} created_by - Creator username
 * @property {TaxonomySubCategory[]} subcategories - Subcategories in this category
 */

/**
 * @typedef {Object} SkillTaxonomyResponse
 * @property {TaxonomyCategory[]} categories - List of categories with nested hierarchy
 * @property {number} total_categories - Total number of categories
 * @property {number} total_subcategories - Total number of subcategories
 * @property {number} total_skills - Total number of skills
 */

/**
 * Fetch the complete skill taxonomy hierarchy.
 * 
 * @param {Object} options - Options object
 * @param {AbortSignal} [options.signal] - AbortController signal for cancellation
 * @param {string} [options.search] - Optional search term to filter skills
 * @returns {Promise<SkillTaxonomyResponse>} Skill taxonomy response
 */
export async function fetchSkillTaxonomy({ signal, search } = {}) {
  const params = {};
  if (search) {
    params.q = search;
  }
  return httpClient.get('/master-data/skill-taxonomy', params, { signal });
}

// ============================================================================
// PATCH Endpoints - Update taxonomy entities
// ============================================================================

/**
 * @typedef {Object} CategoryUpdateResponse
 * @property {number} category_id - Category ID
 * @property {string} category_name - Updated category name
 * @property {string} message - Success message
 */

/**
 * @typedef {Object} SubcategoryUpdateResponse
 * @property {number} subcategory_id - Subcategory ID  
 * @property {string} subcategory_name - Updated subcategory name
 * @property {number} category_id - Parent category ID
 * @property {string} message - Success message
 */

/**
 * @typedef {Object} SkillUpdateResponse
 * @property {number} skill_id - Skill ID
 * @property {string} skill_name - Updated skill name
 * @property {number} subcategory_id - Parent subcategory ID
 * @property {string} message - Success message
 */

/**
 * @typedef {Object} AliasUpdateResponse
 * @property {number} alias_id - Alias ID
 * @property {string} alias_text - Updated alias text
 * @property {number} skill_id - Parent skill ID
 * @property {string} message - Success message
 */

/**
 * Update a category name.
 * 
 * @param {number} categoryId - Category ID to update
 * @param {string} categoryName - New category name
 * @returns {Promise<CategoryUpdateResponse>} Update response
 * @throws {Error} 404 if not found, 409 if duplicate name, 422 if validation error
 */
export async function updateCategoryName(categoryId, categoryName) {
  return httpClient.patch(
    `/master-data/skill-taxonomy/categories/${categoryId}`,
    { category_name: categoryName }
  );
}

/**
 * Update a subcategory name.
 * 
 * @param {number} subcategoryId - Subcategory ID to update
 * @param {string} subcategoryName - New subcategory name
 * @returns {Promise<SubcategoryUpdateResponse>} Update response
 * @throws {Error} 404 if not found, 409 if duplicate name within category, 422 if validation error
 */
export async function updateSubcategoryName(subcategoryId, subcategoryName) {
  return httpClient.patch(
    `/master-data/skill-taxonomy/subcategories/${subcategoryId}`,
    { subcategory_name: subcategoryName }
  );
}

/**
 * Update a skill name.
 * 
 * @param {number} skillId - Skill ID to update
 * @param {string} skillName - New skill name
 * @returns {Promise<SkillUpdateResponse>} Update response
 * @throws {Error} 404 if not found, 409 if duplicate name within subcategory, 422 if validation error
 */
export async function updateSkillName(skillId, skillName) {
  return httpClient.patch(
    `/master-data/skill-taxonomy/skills/${skillId}`,
    { skill_name: skillName }
  );
}

/**
 * Update an alias text.
 * 
 * @param {number} aliasId - Alias ID to update
 * @param {string} aliasText - New alias text
 * @returns {Promise<AliasUpdateResponse>} Update response
 * @throws {Error} 404 if not found, 409 if duplicate alias within skill, 422 if validation error
 */
export async function updateAliasText(aliasId, aliasText) {
  return httpClient.patch(
    `/master-data/skill-taxonomy/aliases/${aliasId}`,
    { alias_text: aliasText }
  );
}

/**
 * Create a new alias for a skill.
 * 
 * @param {number} skillId - Skill ID to add alias to
 * @param {string} aliasText - Alias text
 * @param {string} [source='manual'] - Source of the alias
 * @param {number} [confidenceScore=1.0] - Confidence score
 * @returns {Promise<AliasCreateResponse>} Create response with new alias ID
 * @throws {Error} 404 if skill not found, 409 if duplicate alias, 422 if validation error
 */
export async function createAlias(skillId, aliasText, source = 'manual', confidenceScore = 1.0) {
  return httpClient.post(
    `/master-data/skill-taxonomy/skills/${skillId}/aliases`,
    { alias_text: aliasText, source, confidence_score: confidenceScore }
  );
}

// ============================================================================
// POST Endpoints - Create Category/Subcategory
// ============================================================================

/**
 * @typedef {Object} CategoryCreateResponse
 * @property {number} id - Category ID
 * @property {string} name - Category name
 * @property {string|null} created_at - Creation timestamp (ISO format)
 * @property {string|null} created_by - Creator username
 * @property {string} message - Success message
 */

/**
 * Create a new category.
 * 
 * @param {string} categoryName - Category name
 * @returns {Promise<CategoryCreateResponse>} Create response with new category
 * @throws {Error} 409 if duplicate name, 422 if validation error
 */
export async function createCategory(categoryName) {
  return httpClient.post(
    '/master-data/skill-taxonomy/categories',
    { category_name: categoryName }
  );
}

/**
 * @typedef {Object} SubcategoryCreateResponse
 * @property {number} id - Subcategory ID
 * @property {string} name - Subcategory name
 * @property {number} category_id - Parent category ID
 * @property {string|null} created_at - Creation timestamp (ISO format)
 * @property {string|null} created_by - Creator username
 * @property {string} message - Success message
 */

/**
 * Create a new subcategory under a category.
 * 
 * @param {number} categoryId - Parent category ID
 * @param {string} subcategoryName - Subcategory name
 * @returns {Promise<SubcategoryCreateResponse>} Create response with new subcategory
 * @throws {Error} 404 if category not found, 409 if duplicate name, 422 if validation error
 */
export async function createSubcategory(categoryId, subcategoryName) {
  return httpClient.post(
    `/master-data/skill-taxonomy/categories/${categoryId}/subcategories`,
    { subcategory_name: subcategoryName }
  );
}

/**
 * @typedef {Object} SkillCreateResponse
 * @property {number} id - Skill ID
 * @property {string} name - Skill name
 * @property {number} subcategory_id - Parent subcategory ID
 * @property {string|null} created_at - Creation timestamp (ISO format)
 * @property {string|null} created_by - Creator username
 * @property {Array<Object>} aliases - Created aliases (each with id, alias_text, skill_id, source)
 * @property {string} message - Success message
 */

/**
 * Create a new skill under a subcategory, optionally with aliases.
 * 
 * @param {number} subcategoryId - Parent subcategory ID
 * @param {string} skillName - Skill name
 * @param {string|null} [aliasText] - Optional comma-separated alias texts (e.g., "alias1, alias2")
 * @returns {Promise<SkillCreateResponse>} Create response with new skill and aliases
 * @throws {Error} 404 if subcategory not found, 409 if duplicate name/alias, 422 if validation error
 */
export async function createSkill(subcategoryId, skillName, aliasText = null) {
  const body = { skill_name: skillName };
  if (aliasText) {
    body.alias_text = aliasText;
  }
  return httpClient.post(
    `/master-data/skill-taxonomy/subcategories/${subcategoryId}/skills`,
    body
  );
}

/**
 * Delete an alias.
 * 
 * @param {number} aliasId - Alias ID to delete
 * @returns {Promise<{id: number, alias_text: string, skill_id: number, message: string}>} Delete response
 * @throws {Error} 404 if not found
 */
export async function deleteAlias(aliasId) {
  return httpClient.delete(`/master-data/skill-taxonomy/aliases/${aliasId}`);
}

// ============================================================================
// DELETE Endpoints - Soft Delete Category/Subcategory
// ============================================================================

/**
 * Soft delete a category.
 * Category must not have any subcategories - delete them first.
 * 
 * @param {number} categoryId - Category ID to delete
 * @returns {Promise<{category_id: number, category_name: string, deleted_at: string, message: string}>} Delete response
 * @throws {Error} 404 if not found, 409 if category has subcategories
 */
export async function deleteCategory(categoryId) {
  return httpClient.delete(`/master-data/skill-taxonomy/categories/${categoryId}`);
}

/**
 * Soft delete a subcategory.
 * Subcategory must not have any skills - delete them first.
 * 
 * @param {number} subcategoryId - Subcategory ID to delete
 * @returns {Promise<{subcategory_id: number, subcategory_name: string, category_id: number, deleted_at: string, message: string}>} Delete response
 * @throws {Error} 404 if not found, 409 if subcategory has skills
 */
export async function deleteSubcategory(subcategoryId) {
  return httpClient.delete(`/master-data/skill-taxonomy/subcategories/${subcategoryId}`);
}

/**
 * Soft delete a skill.
 * 
 * @param {number} skillId - Skill ID to delete
 * @returns {Promise<{id: number, name: string, subcategory_id: number, deleted_at: string, message: string}>} Delete response
 * @throws {Error} 404 if not found
 */
export async function deleteSkill(skillId) {
  return httpClient.delete(`/master-data/skill-taxonomy/skills/${skillId}`);
}

/**
 * Import skills from Excel file.
 * Returns immediately with job_id - poll getImportJobStatus for progress.
 * 
 * @param {File} file - Excel file (.xlsx or .xls)
 * @returns {Promise<{job_id: string, status: string, message: string}>} Job info
 * @throws {Error} 400 if file invalid, 500 on server error
 */
export async function importSkills(file) {
  const formData = new FormData();
  formData.append('file', file);
  return httpClient.post('/admin/skills/master-import', formData);
}

/**
 * Get import job status (for polling progress).
 * 
 * @param {string} jobId - Job ID returned from importSkills
 * @returns {Promise<{job_id: string, status: string, percent_complete: number, message: string, error: string|null, result: Object|null}>}
 * @throws {Error} 404 if job not found
 */
export async function getImportJobStatus(jobId) {
  return httpClient.get(`/import/status/${jobId}`);
}

export default {
  fetchSkillTaxonomy,
  updateCategoryName,
  updateSubcategoryName,
  updateSkillName,
  updateAliasText,
  createAlias,
  createCategory,
  createSubcategory,
  createSkill,
  deleteAlias,
  deleteCategory,
  deleteSubcategory,
  deleteSkill,
  importSkills,
  getImportJobStatus,
};
