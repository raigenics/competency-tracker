/**
 * Cache Utility for Stale-While-Revalidate Pattern
 * 
 * Provides simple in-memory caching with TTL for:
 * - Employee list rows (for instant Edit prefill)
 * - Dropdown data (segments, subsegments, projects, teams, roles)
 * 
 * Design:
 * - Cache reads are synchronous
 * - TTL-based expiry (configurable)
 * - getOrFetch pattern for async data loading
 * - No external dependencies
 */

// === CONFIGURATION ===
const DEFAULT_TTL_MS = 10 * 60 * 1000; // 10 minutes
const DROPDOWN_TTL_MS = 30 * 60 * 1000; // 30 minutes for dropdown data

// === CACHE STORAGE ===
const cacheStorage = new Map();  // key -> { data, expiresAt }

/**
 * Set a value in cache with TTL
 * @param {string} key - Cache key
 * @param {any} data - Data to cache
 * @param {number} ttlMs - Time to live in milliseconds
 */
export function cacheSet(key, data, ttlMs = DEFAULT_TTL_MS) {
  cacheStorage.set(key, {
    data,
    expiresAt: Date.now() + ttlMs
  });
}

/**
 * Get a value from cache (returns null if expired or missing)
 * @param {string} key - Cache key
 * @returns {any|null} - Cached data or null
 */
export function cacheGet(key) {
  const entry = cacheStorage.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) {
    cacheStorage.delete(key);
    return null;
  }
  return entry.data;
}

/**
 * Check if cache has a valid (non-expired) entry
 * @param {string} key - Cache key
 * @returns {boolean}
 */
export function cacheHas(key) {
  return cacheGet(key) !== null;
}

/**
 * Delete a cache entry
 * @param {string} key - Cache key
 */
export function cacheDelete(key) {
  cacheStorage.delete(key);
}

/**
 * Clear all cache entries
 */
export function cacheClear() {
  cacheStorage.clear();
}

/**
 * Get or fetch pattern - returns cached data or fetches fresh
 * @param {string} key - Cache key
 * @param {Function} fetchFn - Async function to fetch data if not cached
 * @param {number} ttlMs - TTL for new cache entry
 * @returns {Promise<any>} - Cached or freshly fetched data
 */
export async function cacheGetOrFetch(key, fetchFn, ttlMs = DEFAULT_TTL_MS) {
  const cached = cacheGet(key);
  if (cached !== null) {
    return cached;
  }
  
  const data = await fetchFn();
  cacheSet(key, data, ttlMs);
  return data;
}

// === EMPLOYEE LIST CACHE ===
// Stores employee list rows by employee_id for instant Edit prefill

const EMPLOYEE_CACHE_PREFIX = 'emp:';

/**
 * Cache an employee from list response
 * @param {Object} employee - Employee object from list API
 */
export function cacheEmployee(employee) {
  if (!employee?.employee_id) return;
  cacheSet(`${EMPLOYEE_CACHE_PREFIX}${employee.employee_id}`, employee, DEFAULT_TTL_MS);
}

/**
 * Cache multiple employees from list response
 * @param {Array} employees - Array of employee objects
 */
export function cacheEmployees(employees) {
  if (!Array.isArray(employees)) return;
  employees.forEach(cacheEmployee);
}

/**
 * Get cached employee by ID
 * @param {number} employeeId - Employee ID
 * @returns {Object|null} - Cached employee or null
 */
export function getCachedEmployee(employeeId) {
  return cacheGet(`${EMPLOYEE_CACHE_PREFIX}${employeeId}`);
}

// === DROPDOWN CACHE ===
// Caches dropdown data with longer TTL

const DROPDOWN_CACHE_KEYS = {
  segments: 'dropdown:segments',
  roles: 'dropdown:roles',
  subSegments: (segmentId) => `dropdown:subsegments:${segmentId}`,
  projects: (subSegmentId) => `dropdown:projects:${subSegmentId}`,
  teams: (projectId) => `dropdown:teams:${projectId}`
};

/**
 * Get cached segments
 * @returns {Array|null}
 */
export function getCachedSegments() {
  return cacheGet(DROPDOWN_CACHE_KEYS.segments);
}

/**
 * Cache segments
 * @param {Array} segments
 */
export function cacheSegments(segments) {
  cacheSet(DROPDOWN_CACHE_KEYS.segments, segments, DROPDOWN_TTL_MS);
}

/**
 * Get cached roles
 * @returns {Array|null}
 */
export function getCachedRoles() {
  return cacheGet(DROPDOWN_CACHE_KEYS.roles);
}

/**
 * Cache roles
 * @param {Array} roles
 */
export function cacheRoles(roles) {
  cacheSet(DROPDOWN_CACHE_KEYS.roles, roles, DROPDOWN_TTL_MS);
}

/**
 * Get cached sub-segments for a segment
 * @param {number} segmentId
 * @returns {Array|null}
 */
export function getCachedSubSegments(segmentId) {
  return cacheGet(DROPDOWN_CACHE_KEYS.subSegments(segmentId));
}

/**
 * Cache sub-segments for a segment
 * @param {number} segmentId
 * @param {Array} subSegments
 */
export function cacheSubSegments(segmentId, subSegments) {
  cacheSet(DROPDOWN_CACHE_KEYS.subSegments(segmentId), subSegments, DROPDOWN_TTL_MS);
}

/**
 * Get cached projects for a sub-segment
 * @param {number} subSegmentId
 * @returns {Array|null}
 */
export function getCachedProjects(subSegmentId) {
  return cacheGet(DROPDOWN_CACHE_KEYS.projects(subSegmentId));
}

/**
 * Cache projects for a sub-segment
 * @param {number} subSegmentId
 * @param {Array} projects
 */
export function cacheProjects(subSegmentId, projects) {
  cacheSet(DROPDOWN_CACHE_KEYS.projects(subSegmentId), projects, DROPDOWN_TTL_MS);
}

/**
 * Get cached teams for a project
 * @param {number} projectId
 * @returns {Array|null}
 */
export function getCachedTeams(projectId) {
  return cacheGet(DROPDOWN_CACHE_KEYS.teams(projectId));
}

/**
 * Cache teams for a project
 * @param {number} projectId
 * @param {Array} teams
 */
export function cacheTeams(projectId, teams) {
  cacheSet(DROPDOWN_CACHE_KEYS.teams(projectId), teams, DROPDOWN_TTL_MS);
}

// === DIAGNOSTIC ===
export function getCacheStats() {
  let validCount = 0;
  let expiredCount = 0;
  const now = Date.now();
  
  cacheStorage.forEach((entry) => {
    if (entry.expiresAt > now) {
      validCount++;
    } else {
      expiredCount++;
    }
  });
  
  return { total: cacheStorage.size, valid: validCount, expired: expiredCount };
}
