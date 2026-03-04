/**
 * useProficiencyLevels Hook
 * 
 * SRP: Fetches proficiency levels from backend API.
 * Returns levels for tooltip and options for dropdown.
 */
import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config/apiConfig.js';

/**
 * @typedef {Object} ProficiencyLevel
 * @property {number} proficiency_level_id
 * @property {string} level_name
 * @property {string|null} level_description
 * @property {string} value - Frontend ENUM value (e.g., 'NOVICE', 'EXPERT')
 */

/**
 * @typedef {Object} ProficiencyOption
 * @property {string} value - Frontend ENUM value
 * @property {string} label - Display label
 */

/**
 * Hook to fetch proficiency levels from backend.
 * 
 * @returns {Object} { levels, options, loading, error }
 * - levels: Array of { level_name, level_description } for tooltip
 * - options: Array of { value, label } for dropdown
 * - loading: boolean loading state
 * - error: string error message or null
 */
export function useProficiencyLevels() {
  const [levels, setLevels] = useState([]);
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    const fetchProficiencyLevels = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/dropdown/proficiency-levels`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch proficiency levels: ${response.status}`);
        }

        const data = await response.json();
        const proficiencyLevels = data.proficiency_levels || [];

        if (mounted) {
          // Levels for tooltip (with descriptions)
          setLevels(proficiencyLevels.map(p => ({
            level_name: p.level_name,
            level_description: p.level_description || ''
          })));

          // Options for dropdown ({ value, label })
          setOptions(proficiencyLevels.map(p => ({
            value: p.value,
            label: p.level_name
          })));

          console.log('[useProficiencyLevels] Loaded levels:', proficiencyLevels.length);
        }
      } catch (err) {
        console.error('[useProficiencyLevels] Failed to load proficiency levels:', err);
        if (mounted) {
          setError(err.message || 'Failed to load proficiency levels');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchProficiencyLevels();

    return () => {
      mounted = false;
    };
  }, []);

  return { levels, options, loading, error };
}

export default useProficiencyLevels;
