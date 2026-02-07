import httpClient from './httpClient.js';

// Bulk Import API service
export const bulkImportApi = {  /**
   * Import Excel file with employees and skills data
   * @param {File} file - The Excel file to import
   * @returns {Promise} Import result with statistics
   */
  async importExcel(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log('Uploading Excel file for import:', file.name);
      
      // httpClient.post will auto-detect FormData and handle it correctly
      // Do NOT set Content-Type manually - browser sets it with boundary
      const response = await httpClient.post('/import/excel', formData);

      console.log('Import completed:', response);
      return response;
    } catch (error) {
      console.error('Failed to import Excel file:', error);
      throw error;
    }
  },
  /**
   * Get import job status by job ID
   * @param {string} jobId - The job ID to check status for
   * @returns {Promise} Job status with progress information
   */
  async getJobStatus(jobId) {
    try {
      const response = await httpClient.get(`/import/status/${jobId}`);
      return response;
    } catch (error) {
      console.error('Failed to get job status:', error);
      throw error;
    }
  },

  /**
   * Optional: Validate Excel file without importing (future enhancement)
   * This is a placeholder for when validation endpoint is implemented
   * @param {File} file - The Excel file to validate
   * @returns {Promise} Validation results
   */  async validateExcel(file) {
    // TODO: Validation endpoint not yet implemented on backend
    // For now, skip validation and proceed directly to import
    console.log('Validation endpoint not available, skipping pre-import validation for:', file.name);    return null;
    
    /* Uncomment when backend validation endpoint is ready:
    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log('Validating Excel file:', file.name);
      
      // httpClient.post will auto-detect FormData
      // Do NOT set Content-Type manually
      const response = await httpClient.post('/import/validate', formData);

      return response;
    } catch (error) {
      // If validation endpoint doesn't exist, return null to skip validation
      if (error.response && error.response.status === 404) {
        console.log('Validation endpoint not available, skipping validation');
        return null;
      }
      console.error('Failed to validate Excel file:', error);
      throw error;
    }
    */
  },
};

export default bulkImportApi;
