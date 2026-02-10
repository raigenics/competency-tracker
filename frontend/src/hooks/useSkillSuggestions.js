/**
 * useSkillSuggestions Hook
 * 
 * SRP: Manages skill suggestions state for autocomplete.
 * Loads skills from API and provides filtering/suggestion logic.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { skillsAutocompleteApi } from '../services/api/skillsAutocompleteApi.js';
import { MAX_SKILL_SUGGESTIONS } from '../config/constants.js';

/**
 * @typedef {Object} SkillSuggestion
 * @property {number} skill_id
 * @property {string} skill_name
 * @property {string} category_name
 * @property {string|null} subcategory_name
 */

/**
 * Hook for skill autocomplete suggestions.
 * 
 * @returns {Object} Skill suggestions state and methods
 */
export function useSkillSuggestions() {
  // All loaded skills (cached)
  const [allSkills, setAllSkills] = useState([]);
  // Filtered suggestions based on query
  const [suggestions, setSuggestions] = useState([]);
  // Loading state
  const [loading, setLoading] = useState(true);
  // Error state
  const [error, setError] = useState(null);
  // Current search query (for debouncing)
  const searchTimeoutRef = useRef(null);

  /**
   * Load all skills on mount
   */
  useEffect(() => {
    let mounted = true;

    const loadSkills = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const skills = await skillsAutocompleteApi.getAllSkills(200);
        if (mounted) {
          setAllSkills(skills);
          console.log('[useSkillSuggestions] Loaded skills:', skills.length);
        }
      } catch (err) {
        console.error('[useSkillSuggestions] Failed to load skills:', err);
        if (mounted) {
          setError('Failed to load skills');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadSkills();

    return () => {
      mounted = false;
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  /**
   * Filter skills based on search query.
   * Matches against skill_name (case-insensitive contains).
   * 
   * @param {string} query - Search query
   * @returns {SkillSuggestion[]} Filtered suggestions (max MAX_SKILL_SUGGESTIONS)
   */
  const filterSkills = useCallback((query) => {
    if (!query || query.trim().length === 0) {
      // Return top skills when no query
      return allSkills.slice(0, MAX_SKILL_SUGGESTIONS);
    }

    const normalizedQuery = query.toLowerCase().trim();
    
    const filtered = allSkills.filter(skill => {
      // Match skill name
      if (skill.skill_name.toLowerCase().includes(normalizedQuery)) {
        return true;
      }
      // Could also match aliases here if available in the future
      return false;
    });

    return filtered.slice(0, MAX_SKILL_SUGGESTIONS);
  }, [allSkills]);

  /**
   * Update suggestions based on query (debounced).
   * 
   * @param {string} query - Search query
   */
  const search = useCallback((query) => {
    // Clear any pending search
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Debounce the search
    searchTimeoutRef.current = setTimeout(() => {
      const filtered = filterSkills(query);
      setSuggestions(filtered);
    }, 150);
  }, [filterSkills]);

  /**
   * Get immediate suggestions (no debounce).
   * Used for initial focus or programmatic access.
   * 
   * @param {string} query - Search query
   * @returns {SkillSuggestion[]}
   */
  const getSuggestions = useCallback((query) => {
    return filterSkills(query);
  }, [filterSkills]);

  /**
   * Find a skill by ID
   * 
   * @param {number} skillId
   * @returns {SkillSuggestion|undefined}
   */
  const getSkillById = useCallback((skillId) => {
    return allSkills.find(s => s.skill_id === skillId);
  }, [allSkills]);

  /**
   * Clear suggestions
   */
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
  }, []);

  return {
    // State
    allSkills,
    suggestions,
    loading,
    error,
    
    // Methods
    search,
    getSuggestions,
    getSkillById,
    clearSuggestions
  };
}

export default useSkillSuggestions;
