// HTTP client wrapper for API calls
import { API_BASE_URL } from '../../config/apiConfig.js';

class HttpClient {  async get(endpoint, params = {}) {
    try {
      const url = new URL(`${API_BASE_URL}${endpoint}`);
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
          url.searchParams.append(key, params[key]);
        }
      });
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('GET request failed:', error);
      throw error;
    }
  }  async post(endpoint, data = {}, options = {}) {
    try {
      // Detect if data is FormData
      const isFormData = data instanceof FormData;
      
      // Build fetch options
      const fetchOptions = {
        method: 'POST',
        ...options,
      };
      
      if (isFormData) {
        // For FormData: Do NOT set Content-Type (browser sets it with boundary)
        // Do NOT stringify - send FormData directly
        fetchOptions.body = data;
      } else {
        // For regular objects: Use JSON
        fetchOptions.headers = {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        };
        fetchOptions.body = JSON.stringify(data);
      }
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('POST request failed:', error);
      throw error;
    }
  }
  async put(endpoint, data = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('PUT request failed:', error);
      throw error;
    }
  }
  async delete(endpoint) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('DELETE request failed:', error);
      throw error;
    }
  }
}

export const httpClient = new HttpClient();
export default httpClient;
