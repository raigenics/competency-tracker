// HTTP client wrapper for API calls
import { API_BASE_URL } from '../../config/apiConfig.js';
import { getRbacContext } from '../../config/featureFlags.js';

/**
 * Build RBAC headers from current context.
 * 
 * Headers sent:
 * - X-RBAC-Role: Current role name
 * - X-RBAC-Scope-Segment: Segment ID (if set)
 * - X-RBAC-Scope-SubSegment: Sub-segment ID (if set)
 * - X-RBAC-Scope-Project: Project ID (if set)
 * - X-RBAC-Scope-Team: Team ID (if set)
 * - X-RBAC-Scope-Employee: Employee ID (if set, for self-only CRUD)
 * 
 * TEMPORARY: Reads from featureFlags.js RBAC_CONFIG
 * REPLACE: Once JWT auth is implemented, these headers can be removed
 * as the backend will read role/scope from the token.
 */
function buildRbacHeaders() {
  const { role, scope } = getRbacContext();
  
  const headers = {
    'X-RBAC-Role': role
  };
  
  // Only add scope headers if values are not null
  if (scope.segment_id != null) {
    headers['X-RBAC-Scope-Segment'] = String(scope.segment_id);
  }
  if (scope.sub_segment_id != null) {
    headers['X-RBAC-Scope-SubSegment'] = String(scope.sub_segment_id);
  }
  if (scope.project_id != null) {
    headers['X-RBAC-Scope-Project'] = String(scope.project_id);
  }
  if (scope.team_id != null) {
    headers['X-RBAC-Scope-Team'] = String(scope.team_id);
  }
  if (scope.employee_id != null) {
    headers['X-RBAC-Scope-Employee'] = String(scope.employee_id);
  }
  
  return headers;
}

class HttpClient {
  async get(endpoint, params = {}) {
    try {
      const url = new URL(`${API_BASE_URL}${endpoint}`);
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
          url.searchParams.append(key, params[key]);
        }
      });
      
      const response = await fetch(url, {
        headers: buildRbacHeaders()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('GET request failed:', error);
      throw error;
    }
  }
  
  async post(endpoint, data = {}, options = {}) {
    try {
      // Detect if data is FormData
      const isFormData = data instanceof FormData;
      
      // Build fetch options with RBAC headers
      const rbacHeaders = buildRbacHeaders();
      const fetchOptions = {
        method: 'POST',
        ...options,
      };
      
      if (isFormData) {
        // For FormData: Do NOT set Content-Type (browser sets it with boundary)
        // Do NOT stringify - send FormData directly
        fetchOptions.headers = {
          ...rbacHeaders,
          ...(options.headers || {}),
        };
        fetchOptions.body = data;
      } else {
        // For regular objects: Use JSON
        fetchOptions.headers = {
          'Content-Type': 'application/json',
          ...rbacHeaders,
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
          ...buildRbacHeaders(),
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
  
  async delete(endpoint, data = null) {
    try {
      const options = {
        method: 'DELETE',
        headers: buildRbacHeaders(),
      };
      
      // Add body if data is provided
      if (data) {
        options.headers = {
          'Content-Type': 'application/json',
          ...buildRbacHeaders(),
        };
        options.body = JSON.stringify(data);
      }
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // 204 No Content - return null immediately
      if (response.status === 204) {
        return null;
      }
      
      // Check if response has content (for other 2xx responses)
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return null;
    } catch (error) {
      console.error('DELETE request failed:', error);
      throw error;
    }
  }
}

export const httpClient = new HttpClient();
export default httpClient;
