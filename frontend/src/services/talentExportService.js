import capabilityFinderApi from './api/capabilityFinderApi';

/**
 * Service for handling talent export operations
 * Provides utilities for downloading Excel files from blob responses
 */

/**
 * Downloads an Excel blob as a file
 * @param {Blob} blob - The Excel file blob
 * @param {string} filename - The filename for the download
 */
export const downloadExcelFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Generates a timestamp for filenames
 * @returns {string} Formatted timestamp (YYYY-MM-DDTHH-MM-SS)
 */
export const generateTimestamp = () => {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
};

/**
 * Exports all matching talent based on filters
 * @param {Object} filters - The search filters
 * @param {string} baseFilename - Base filename without timestamp (default: 'capability_finder_all')
 * @returns {Promise<void>}
 */
export const exportAllTalent = async (filters, baseFilename = 'capability_finder_all') => {
  const payload = {
    mode: 'all',
    filters: {
      skills: filters.skills || [],
      sub_segment_id: filters.subSegment === 'all' ? null : parseInt(filters.subSegment),
      team_id: filters.team ? parseInt(filters.team) : null,
      role: filters.role || null,
      min_proficiency: filters.proficiency?.min || 0,
      min_experience_years: filters.experience?.min || 0
    },
    selected_employee_ids: []
  };
  
  const blob = await capabilityFinderApi.exportMatchingTalent(payload);
  const timestamp = generateTimestamp();
  downloadExcelFile(blob, `${baseFilename}_${timestamp}.xlsx`);
};

/**
 * Exports selected talent based on filters and selection
 * @param {Object} filters - The search filters
 * @param {Array<number>} selectedEmployeeIds - Array of selected employee IDs
 * @param {string} baseFilename - Base filename without timestamp (default: 'capability_finder_selected')
 * @returns {Promise<void>}
 */
export const exportSelectedTalent = async (filters, selectedEmployeeIds, baseFilename = 'capability_finder_selected') => {
  const payload = {
    mode: 'selected',
    filters: {
      skills: filters.skills || [],
      sub_segment_id: filters.subSegment === 'all' ? null : parseInt(filters.subSegment),
      team_id: filters.team ? parseInt(filters.team) : null,
      role: filters.role || null,
      min_proficiency: filters.proficiency?.min || 0,
      min_experience_years: filters.experience?.min || 0
    },
    selected_employee_ids: selectedEmployeeIds
  };
  
  const blob = await capabilityFinderApi.exportMatchingTalent(payload);
  const timestamp = generateTimestamp();
  downloadExcelFile(blob, `${baseFilename}_${timestamp}.xlsx`);
};

const talentExportService = {
  downloadExcelFile,
  generateTimestamp,
  exportAllTalent,
  exportSelectedTalent
};

export default talentExportService;
