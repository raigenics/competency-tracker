// HTTP client wrapper for API calls
import { API_BASE_URL } from '../../config/apiConfig.js';
import { getRbacContext } from '../../config/featureFlags.js';

/**
 * ============================================================================
 * DIAGNOSTIC LOGGING - HTTP Request Timing
 * ============================================================================
 * 
 * To enable HTTP timing logs, run in browser console:
 *   localStorage.setItem("DEBUG_HTTP", "1");
 *   location.reload();
 * 
 * To disable:
 *   localStorage.removeItem("DEBUG_HTTP");
 *   location.reload();
 * 
 * To view recent request timings:
 *   window.__httpTimings.list()     // Show all recent requests
 *   window.__httpTimings.clear()    // Clear history
 *   window.__httpTimings.summary()  // Show stats summary
 * 
 * Log format:
 *   [HTTP START] id=12 method=GET url=http://...?page=1 t=1234.56
 *   [HTTP END]   id=12 status=200 ms=483 bytes=12345
 *   [HTTP FAIL]  id=12 ms=802 error="..." aborted=false
 *   [HTTP ABORT] id=12 ms=120
 * ============================================================================
 */

// Only enable in dev mode AND when localStorage flag is set
const DEBUG_HTTP = typeof window !== 'undefined' 
  && import.meta.env.DEV 
  && localStorage.getItem("DEBUG_HTTP") === "1";

// Global request counter for unique IDs
let _httpRequestId = 0;

// In-memory storage for recent request timings (keep last 100)
const _httpTimings = [];
const MAX_TIMINGS = 100;

function recordTiming(record) {
  _httpTimings.push(record);
  if (_httpTimings.length > MAX_TIMINGS) {
    _httpTimings.shift();
  }
}

// Expose timing utilities on window for console access
if (typeof window !== 'undefined') {
  window.__httpTimings = {
    list: () => {
      console.table(_httpTimings.map(r => ({
        id: r.id,
        method: r.method,
        url: r.url.replace(API_BASE_URL, ''),
        status: r.status || '-',
        ms: r.durationMs?.toFixed(1) || '-',
        bytes: r.bytes || '-',
        aborted: r.aborted ? 'YES' : '',
        error: r.error || ''
      })));
      return _httpTimings;
    },
    clear: () => {
      _httpTimings.length = 0;
      console.log('[HTTP] Timings cleared');
    },
    summary: () => {
      if (_httpTimings.length === 0) {
        console.log('[HTTP] No timings recorded');
        return;
      }
      const completed = _httpTimings.filter(r => r.durationMs && !r.aborted && !r.error);
      const durations = completed.map(r => r.durationMs);
      const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
      const max = Math.max(...durations);
      const min = Math.min(...durations);
      console.log(`[HTTP] Summary: ${_httpTimings.length} requests, ${completed.length} completed`);
      console.log(`[HTTP] Duration: avg=${avg.toFixed(1)}ms, min=${min.toFixed(1)}ms, max=${max.toFixed(1)}ms`);
      const aborted = _httpTimings.filter(r => r.aborted).length;
      const failed = _httpTimings.filter(r => r.error && !r.aborted).length;
      if (aborted) console.log(`[HTTP] Aborted: ${aborted}`);
      if (failed) console.log(`[HTTP] Failed: ${failed}`);
    },
    raw: () => _httpTimings
  };
}

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
  async get(endpoint, params = {}, options = {}) {
    const reqId = ++_httpRequestId;
    const startTime = performance.now();
    const url = new URL(`${API_BASE_URL}${endpoint}`);
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null) {
        url.searchParams.append(key, params[key]);
      }
    });
    const fullUrl = url.toString();
    
    // Timing record
    const record = { id: reqId, method: 'GET', url: fullUrl, startTime: Date.now() };
    
    if (DEBUG_HTTP) {
      console.log(`[HTTP START] id=${reqId} method=GET url=${fullUrl} t=${startTime.toFixed(2)}`);
    }
    
    try {
      const response = await fetch(url, {
        headers: buildRbacHeaders(),
        signal: options.signal
      });
      
      const durationMs = performance.now() - startTime;
      const text = await response.text();
      const bytes = text.length;
      
      record.status = response.status;
      record.durationMs = durationMs;
      record.bytes = bytes;
      recordTiming(record);
      
      if (DEBUG_HTTP) {
        console.log(`[HTTP END]   id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)} bytes=${bytes}`);
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return JSON.parse(text);
    } catch (error) {
      const durationMs = performance.now() - startTime;
      record.durationMs = durationMs;
      
      if (error.name === 'AbortError') {
        record.aborted = true;
        recordTiming(record);
        if (DEBUG_HTTP) {
          console.log(`[HTTP ABORT] id=${reqId} ms=${durationMs.toFixed(1)}`);
        }
        throw error;
      }
      
      record.error = error.message;
      recordTiming(record);
      if (DEBUG_HTTP) {
        console.log(`[HTTP FAIL]  id=${reqId} ms=${durationMs.toFixed(1)} error="${error.message}" aborted=false`);
      }
      console.error('GET request failed:', error);
      throw error;
    }
  }
  
  async post(endpoint, data = {}, options = {}) {
    const reqId = ++_httpRequestId;
    const startTime = performance.now();
    const fullUrl = `${API_BASE_URL}${endpoint}`;
    const record = { id: reqId, method: 'POST', url: fullUrl, startTime: Date.now() };
    
    if (DEBUG_HTTP) {
      console.log(`[HTTP START] id=${reqId} method=POST url=${fullUrl} t=${startTime.toFixed(2)}`);
    }
    
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
      
      const response = await fetch(fullUrl, fetchOptions);
      const durationMs = performance.now() - startTime;
      const text = await response.text();
      const bytes = text.length;
      
      record.status = response.status;
      record.durationMs = durationMs;
      record.bytes = bytes;
      recordTiming(record);
      
      if (DEBUG_HTTP) {
        console.log(`[HTTP END]   id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)} bytes=${bytes}`);
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return JSON.parse(text);
    } catch (error) {
      const durationMs = performance.now() - startTime;
      if (!record.durationMs) {
        record.durationMs = durationMs;
        record.error = error.message;
        recordTiming(record);
      }
      if (DEBUG_HTTP && !record.status) {
        console.log(`[HTTP FAIL]  id=${reqId} ms=${durationMs.toFixed(1)} error="${error.message}" aborted=false`);
      }
      console.error('POST request failed:', error);
      throw error;
    }
  }
  
  async put(endpoint, data = {}) {
    const reqId = ++_httpRequestId;
    const startTime = performance.now();
    const fullUrl = `${API_BASE_URL}${endpoint}`;
    const record = { id: reqId, method: 'PUT', url: fullUrl, startTime: Date.now() };
    
    if (DEBUG_HTTP) {
      console.log(`[HTTP START] id=${reqId} method=PUT url=${fullUrl} t=${startTime.toFixed(2)}`);
    }
    
    try {
      const response = await fetch(fullUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...buildRbacHeaders(),
        },
        body: JSON.stringify(data),
      });
      
      const durationMs = performance.now() - startTime;
      const text = await response.text();
      const bytes = text.length;
      
      record.status = response.status;
      record.durationMs = durationMs;
      record.bytes = bytes;
      recordTiming(record);
      
      if (DEBUG_HTTP) {
        console.log(`[HTTP END]   id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)} bytes=${bytes}`);
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return JSON.parse(text);
    } catch (error) {
      const durationMs = performance.now() - startTime;
      if (!record.durationMs) {
        record.durationMs = durationMs;
        record.error = error.message;
        recordTiming(record);
      }
      if (DEBUG_HTTP && !record.status) {
        console.log(`[HTTP FAIL]  id=${reqId} ms=${durationMs.toFixed(1)} error="${error.message}" aborted=false`);
      }
      console.error('PUT request failed:', error);
      throw error;
    }
  }

  async patch(endpoint, data = {}) {
    const reqId = ++_httpRequestId;
    const startTime = performance.now();
    const fullUrl = `${API_BASE_URL}${endpoint}`;
    const record = { id: reqId, method: 'PATCH', url: fullUrl, startTime: Date.now() };
    
    if (DEBUG_HTTP) {
      console.log(`[HTTP START] id=${reqId} method=PATCH url=${fullUrl} t=${startTime.toFixed(2)}`);
    }
    
    try {
      const response = await fetch(fullUrl, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...buildRbacHeaders(),
        },
        body: JSON.stringify(data),
      });
      
      const durationMs = performance.now() - startTime;
      const text = await response.text();
      const bytes = text.length;
      
      record.status = response.status;
      record.durationMs = durationMs;
      record.bytes = bytes;
      recordTiming(record);
      
      if (DEBUG_HTTP) {
        console.log(`[HTTP END]   id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)} bytes=${bytes}`);
      }
      
      if (!response.ok) {
        // Parse error response for structured error messages
        let errorData;
        try {
          errorData = JSON.parse(text);
        } catch {
          errorData = { detail: text || `HTTP error! status: ${response.status}` };
        }
        const error = new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        error.status = response.status;
        error.data = errorData;
        throw error;
      }
      return JSON.parse(text);
    } catch (error) {
      const durationMs = performance.now() - startTime;
      if (!record.durationMs) {
        record.durationMs = durationMs;
        record.error = error.message;
        recordTiming(record);
      }
      if (DEBUG_HTTP && !record.status) {
        console.log(`[HTTP FAIL]  id=${reqId} ms=${durationMs.toFixed(1)} error="${error.message}" aborted=false`);
      }
      console.error('PATCH request failed:', error);
      throw error;
    }
  }
  
  async delete(endpoint, data = null) {
    const reqId = ++_httpRequestId;
    const startTime = performance.now();
    const fullUrl = `${API_BASE_URL}${endpoint}`;
    const record = { id: reqId, method: 'DELETE', url: fullUrl, startTime: Date.now() };
    
    if (DEBUG_HTTP) {
      console.log(`[HTTP START] id=${reqId} method=DELETE url=${fullUrl} t=${startTime.toFixed(2)}`);
    }
    
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
      
      const response = await fetch(fullUrl, options);
      const durationMs = performance.now() - startTime;
      
      record.status = response.status;
      record.durationMs = durationMs;
      
      if (!response.ok) {
        // Parse error response for structured error messages (409 conflicts, etc.)
        let errorData;
        try {
          const text = await response.text();
          record.bytes = text.length;
          errorData = text ? JSON.parse(text) : { detail: `HTTP error! status: ${response.status}` };
        } catch {
          errorData = { detail: `HTTP error! status: ${response.status}` };
        }
        
        recordTiming(record);
        if (DEBUG_HTTP) {
          console.log(`[HTTP FAIL]  id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)}`);
        }
        
        const error = new Error(
          typeof errorData.detail === 'string' 
            ? errorData.detail 
            : errorData.detail?.message || `HTTP error! status: ${response.status}`
        );
        error.status = response.status;
        error.data = errorData.detail || errorData;
        throw error;
      }
      
      // 204 No Content - return null immediately
      if (response.status === 204) {
        record.bytes = 0;
        recordTiming(record);
        if (DEBUG_HTTP) {
          console.log(`[HTTP END]   id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)} bytes=0`);
        }
        return null;
      }
      
      // Check if response has content (for other 2xx responses)
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const text = await response.text();
        record.bytes = text.length;
        recordTiming(record);
        if (DEBUG_HTTP) {
          console.log(`[HTTP END]   id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)} bytes=${text.length}`);
        }
        return JSON.parse(text);
      }
      
      record.bytes = 0;
      recordTiming(record);
      if (DEBUG_HTTP) {
        console.log(`[HTTP END]   id=${reqId} status=${response.status} ms=${durationMs.toFixed(1)} bytes=0`);
      }
      return null;
    } catch (error) {
      const durationMs = performance.now() - startTime;
      if (!record.durationMs) {
        record.durationMs = durationMs;
        record.error = error.message;
        recordTiming(record);
      }
      if (DEBUG_HTTP && !record.status) {
        console.log(`[HTTP FAIL]  id=${reqId} ms=${durationMs.toFixed(1)} error="${error.message}" aborted=false`);
      }
      console.error('DELETE request failed:', error);
      throw error;
    }
  }
}

export const httpClient = new HttpClient();
export default httpClient;
