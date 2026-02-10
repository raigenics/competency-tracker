import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/PageHeader.jsx';
import AddEmployeeDrawer from '../../components/AddEmployeeDrawer.jsx';
import { employeeApi } from '../../services/api/employeeApi.js';
import { dropdownApi } from '../../services/api/dropdownApi.js';

/**
 * ============================================================================
 * DIAGNOSTIC LOGGING - Employees Page Timing
 * ============================================================================
 * 
 * To enable timing logs, run in browser console:
 *   localStorage.setItem("DEBUG_EMPLOYEES", "1");
 *   location.reload();
 * 
 * To disable:
 *   localStorage.removeItem("DEBUG_EMPLOYEES");
 *   location.reload();
 * 
 * Log format:
 *   [EMP] page-mount
 *   [EMP] fetch-start page=1 size=10
 *   [EMP] fetch-end ms=483 rows=10 total=150
 *   [EMP] render-data rows=10 msSinceMount=520
 *   [EMP] cache-hit page=1
 * ============================================================================
 */
const DEBUG_EMPLOYEES = typeof window !== 'undefined' 
  && import.meta.env.DEV 
  && localStorage.getItem("DEBUG_EMPLOYEES") === "1";

const EmployeesPage = () => {
  const navigate = useNavigate();
  
  // Diagnostic timing refs
  const mountStartRef = useRef(null);
  const firstRenderDoneRef = useRef(false);
  const fetchStartRef = useRef(null);
  
  /**
   * PERFORMANCE FIX (2026-02-10):
   * Root cause: React StrictMode runs effects twice in dev mode.
   * This caused duplicate API calls to /employees (2x fetch = 2x network latency).
   * 
   * Fix: Use AbortController to cancel inflight request when effect re-runs.
   * - First effect run starts fetch with controller A
   * - StrictMode re-runs effect, aborting controller A and starting controller B
   * - Only controller B's response is used
   * - Also prevents state updates after unmount (no memory leak warnings)
   */
  const abortControllerRef = useRef(null);
  
    // State for search
  const [searchTerm, setSearchTerm] = useState('');
  const [searchQuery, setSearchQuery] = useState(''); // Actual search query to send to API
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const [isSearching, setIsSearching] = useState(false);
  
  // State for filters
  const [filters, setFilters] = useState({
    subSegment: '',
    project: '',
    team: ''
  });
  
  // State for dropdowns
  const [dropdownData, setDropdownData] = useState({
    subSegments: [],
    projects: [],
    teams: []
  });
  
  const [dropdownLoading, setDropdownLoading] = useState({
    subSegments: false,
    projects: false,
    teams: false
  });
    // State for employees table
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalEmployees, setTotalEmployees] = useState(0);
  const pageSize = 10;
  
  // Page cache for lazy loading (stores fetched pages to avoid refetch)
  const pageCacheRef = useRef({});
  const filterKeyRef = useRef('');
  
  // Refresh trigger - increment to force re-fetch after add/edit
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
  // Add Employee Drawer state
  const [isAddEmployeeOpen, setIsAddEmployeeOpen] = useState(false);
  
  // Refs
  const searchDebounceRef = useRef(null);
  const searchInputRef = useRef(null);
  const suggestionsRef = useRef(null);
  
  // Load sub-segments on mount only (employees loaded by dependency effect)
  // FIX: Removed duplicate loadEmployees() call here to prevent double-fetch on mount.
  // The second useEffect with [currentPage, filters, searchQuery] handles initial + subsequent loads.
  useEffect(() => {
    // Diagnostic: record mount time
    mountStartRef.current = performance.now();
    if (DEBUG_EMPLOYEES) {
      console.groupCollapsed('[EMP] page-mount');
      console.log('timestamp:', new Date().toISOString());
      console.log('currentPage:', currentPage, 'filters:', filters, 'searchQuery:', searchQuery);
      console.groupEnd();
    }
    loadSubSegments();
  }, []);
  
  // Diagnostic: track time-to-first-row-render
  useEffect(() => {
    if (employees.length > 0 && !firstRenderDoneRef.current && mountStartRef.current) {
      firstRenderDoneRef.current = true;
      const msSinceMount = performance.now() - mountStartRef.current;
      if (DEBUG_EMPLOYEES) {
        console.log(`[EMP] render-data rows=${employees.length} msSinceMount=${msSinceMount.toFixed(1)}`);
      }
    }
  }, [employees]);
  
  // Load employees when page, filters, or search query change
  useEffect(() => {
    // Abort any inflight request from previous render (StrictMode fix)
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    
    loadEmployees(abortControllerRef.current.signal);
    
    // Cleanup: abort on unmount or dependency change
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [currentPage, filters, searchQuery, refreshTrigger]);
  
  // Debounced autocomplete search
  useEffect(() => {
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    
    if (searchTerm.trim().length >= 2) {
      setIsSearching(true);
      searchDebounceRef.current = setTimeout(() => {
        fetchSuggestions(searchTerm);
      }, 300);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
      setIsSearching(false);
    }
    
    return () => {
      if (searchDebounceRef.current) {
        clearTimeout(searchDebounceRef.current);
      }
    };
  }, [searchTerm]);
  
  // Close suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target) &&
        searchInputRef.current &&
        !searchInputRef.current.contains(event.target)
      ) {
        setShowSuggestions(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  // Load sub-segments
  const loadSubSegments = async () => {
    setDropdownLoading(prev => ({ ...prev, subSegments: true }));
    try {
      const data = await dropdownApi.getSubSegments();
      setDropdownData(prev => ({ ...prev, subSegments: data }));
    } catch (error) {
      console.error('Failed to load sub-segments:', error);
    } finally {
      setDropdownLoading(prev => ({ ...prev, subSegments: false }));
    }
  };
  
  // Load projects based on sub-segment
  const loadProjects = async (subSegmentId) => {
    setDropdownLoading(prev => ({ ...prev, projects: true }));
    try {
      const data = await dropdownApi.getProjects(subSegmentId);
      setDropdownData(prev => ({ ...prev, projects: data }));
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setDropdownLoading(prev => ({ ...prev, projects: false }));
    }
  };
  
  // Load teams based on project
  const loadTeams = async (projectId) => {
    setDropdownLoading(prev => ({ ...prev, teams: true }));
    try {
      const data = await dropdownApi.getTeams(projectId);
      setDropdownData(prev => ({ ...prev, teams: data }));
    } catch (error) {
      console.error('Failed to load teams:', error);
    } finally {
      setDropdownLoading(prev => ({ ...prev, teams: false }));
    }
  };
    // Fetch autocomplete suggestions
  const fetchSuggestions = async (query) => {
    try {
      const data = await employeeApi.getSuggestions(query, 8);
      // Backend returns array directly, not { suggestions: [...] }
      const suggestions = Array.isArray(data) ? data : (data.suggestions || []);
      setSuggestions(suggestions);
      setShowSuggestions(true);
      setSelectedSuggestionIndex(-1);
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
      setSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  };
  // Load employees with current filters and pagination (with page caching)
  const loadEmployees = async (signal) => {
    setLoading(true);
    const fetchStart = performance.now();
    
    try {
      const params = {
        page: currentPage,
        size: pageSize,
        ...(filters.subSegment && { sub_segment_id: filters.subSegment }),
        ...(filters.project && { project_id: filters.project }),
        ...(filters.team && { team_id: filters.team }),
        ...(searchQuery && { search: searchQuery })
      };
      
      if (DEBUG_EMPLOYEES) {
        console.log(`[EMP] fetch-start page=${currentPage} size=${pageSize} filters=${JSON.stringify(filters)} search="${searchQuery || ''}"`);
      }
      
      // Create a unique cache key based on filters AND search query
      const newFilterKey = `${filters.subSegment || 'all'}_${filters.project || 'all'}_${filters.team || 'all'}_${searchQuery || 'all'}`;
      
      // If filters or search changed, clear cache and reset to page 1
      if (filterKeyRef.current !== newFilterKey) {
        pageCacheRef.current = {};
        filterKeyRef.current = newFilterKey;
        
        // If we're not already on page 1, the useEffect will trigger again
        if (currentPage !== 1) {
          setCurrentPage(1);
          setLoading(false);
          if (DEBUG_EMPLOYEES) {
            console.log(`[EMP] fetch-redirect resetting to page 1 due to filter change`);
          }
          return;
        }
      }
      
      // Check if this page is already cached
      const cacheKey = `${newFilterKey}_page_${currentPage}`;
      if (pageCacheRef.current[cacheKey]) {
        const cachedData = pageCacheRef.current[cacheKey];
        setEmployees(cachedData.items);
        setTotalEmployees(cachedData.total);
        setTotalPages(Math.ceil(cachedData.total / pageSize));
        setLoading(false);
        if (DEBUG_EMPLOYEES) {
          console.log(`[EMP] cache-hit page=${currentPage} rows=${cachedData.items.length}`);
        }
        return;
      }
        // Fetch from API (lazy load only current page)
      const response = await employeeApi.getEmployees(params, { signal });
      const fetchEnd = performance.now();
      const rawItems = response.items || [];
      const total = response.total || 0;
      
      if (DEBUG_EMPLOYEES) {
        console.log(`[EMP] fetch-end ms=${(fetchEnd - fetchStart).toFixed(1)} rows=${rawItems.length} total=${total}`);
      }
      
      // Transform backend response to match table expectations
      const items = rawItems.map(emp => ({
        id: emp.employee_id,
        employee_id: emp.employee_id,
        zid: emp.zid,
        name: emp.full_name,
        full_name: emp.full_name,
        subSegment: emp.organization?.sub_segment || '—',
        sub_segment: emp.organization?.sub_segment || '—',
        project: emp.organization?.project || '—',
        team: emp.organization?.team || '—',
        role: emp.role?.role_name || '—',
        skills_count: emp.skills_count || 0
      }));
      
      // Cache the result
      pageCacheRef.current[cacheKey] = {
        items,
        total,
        timestamp: Date.now()
      };
      
      setEmployees(items);
      setTotalEmployees(total);
      setTotalPages(Math.ceil(total / pageSize));
      setLoading(false);
    } catch (error) {
      // Silently ignore aborted requests (expected during StrictMode cleanup)
      if (error.name === 'AbortError') {
        if (DEBUG_EMPLOYEES) {
          const fetchEnd = performance.now();
          console.log(`[EMP] fetch-abort ms=${(fetchEnd - fetchStart).toFixed(1)}`);
        }
        return; // Don't update state or setLoading for aborted requests
      }
      if (DEBUG_EMPLOYEES) {
        const fetchEnd = performance.now();
        console.log(`[EMP] fetch-fail ms=${(fetchEnd - fetchStart).toFixed(1)} error="${error.message}"`);
      }
      console.error('Failed to load employees:', error);
      setEmployees([]);
      setTotalEmployees(0);
      setTotalPages(0);
      setLoading(false);
    }
  };
  
  /**
   * Callback for when a new employee is saved from the Add Employee drawer.
   * Clears the cache and triggers a refresh of the employees list.
   * Keeps drawer open so user can add another employee.
   */
  const handleEmployeeSaved = (newEmployee) => {
    // Clear cache to force fresh data fetch
    pageCacheRef.current = {};
    filterKeyRef.current = '';
    // Trigger refresh by incrementing the counter
    setRefreshTrigger(prev => prev + 1);
  };
  
    // Handle sub-segment change
  const handleSubSegmentChange = (subSegmentId) => {
    setFilters({
      subSegment: subSegmentId,
      project: '',
      team: ''
    });
    setDropdownData(prev => ({ ...prev, projects: [], teams: [] }));
    
    // Clear cache and reset to page 1 (loadEmployees will handle cache clearing)
    setCurrentPage(1);
    
    if (subSegmentId) {
      loadProjects(subSegmentId);
    }
  };
  
  // Handle project change
  const handleProjectChange = (projectId) => {
    setFilters(prev => ({
      ...prev,
      project: projectId,
      team: ''
    }));
    setDropdownData(prev => ({ ...prev, teams: [] }));
    
    // Clear cache and reset to page 1
    setCurrentPage(1);
    
    if (projectId) {
      loadTeams(projectId);
    }
  };
  
  // Handle team change
  const handleTeamChange = (teamId) => {
    setFilters(prev => ({ ...prev, team: teamId }));
    
    // Clear cache and reset to page 1
    setCurrentPage(1);
  };
    // Handle search input change
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
    // Clear search query if user clears the input
    if (e.target.value.trim() === '') {
      setSearchQuery('');
    }
  };
  
  // Handle keyboard navigation in suggestions
  const handleSearchKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) {
      // If Enter is pressed without suggestions, trigger search
      if (e.key === 'Enter' && searchTerm.trim()) {
        e.preventDefault();
        performSearch();
      }
      return;
    }
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          selectSuggestion(suggestions[selectedSuggestionIndex]);
        } else {
          performSearch();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
      default:
        break;
    }
  };
  
  // Perform search with current search term
  const performSearch = () => {
    setSearchQuery(searchTerm.trim());
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    setCurrentPage(1);
  };
  
  // Select a suggestion
  const selectSuggestion = (suggestion) => {
    const displayText = `${suggestion.zid} — ${suggestion.full_name || suggestion.name}`;
    setSearchTerm(displayText);
    setSearchQuery(suggestion.zid); // Search by ZID when suggestion is selected
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    setCurrentPage(1);
  };
  
  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };
  
  // Render page numbers
  const renderPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
            i === currentPage
              ? 'bg-[#667eea] text-white'
              : 'bg-white text-[#64748b] border border-[#e2e8f0] hover:bg-[#f8fafc]'
          }`}
        >
          {i}
        </button>
      );
    }
    
    return pages;
  };  return (
    <div className="min-h-screen bg-[#f8fafc]">
      <PageHeader 
        title="Employees"
        actions={
          <button 
            className="px-5 py-2.5 bg-[#667eea] text-white rounded-md text-sm font-medium hover:bg-[#5568d3] transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[#667eea]/30"
            onClick={() => setIsAddEmployeeOpen(true)}
          >
            + Add Employee
          </button>
        }
      />
      
      {/* Add Employee Drawer - Only mount when open to avoid loading roles/skills on parent page */}
      {isAddEmployeeOpen && (
        <AddEmployeeDrawer 
          isOpen={isAddEmployeeOpen}
          onClose={() => setIsAddEmployeeOpen(false)}
          onSave={handleEmployeeSaved}
          mode="add"
        />
      )}

      <div className="px-8 py-8">
        <div className="max-w-screen-2xl mx-auto">
          {/* Search and Filter Bar */}
          <div className="bg-white border-2 border-[#e2e8f0] rounded-lg p-5 mb-6">
            <div className="flex gap-3 flex-wrap">              {/* Search Box with Autocomplete */}
              <div className="flex-1 min-w-[250px] relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 bg-[#94a3b8] rounded-full"></span>
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search by ZID or Name..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  onKeyDown={handleSearchKeyDown}
                  onFocus={() => searchTerm.length >= 2 && setShowSuggestions(true)}
                  className="w-full pl-9 pr-10 py-2.5 border-2 border-[#e2e8f0] rounded-md text-sm focus:outline-none focus:border-[#667eea] transition-colors"
                />
                
                {/* Clear search button */}
                {searchTerm && !isSearching && (
                  <button
                    onClick={() => {
                      setSearchTerm('');
                      setSearchQuery('');
                      setShowSuggestions(false);
                    }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#94a3b8] hover:text-[#64748b] transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}                {/* Loading indicator */}
                {isSearching && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <div className="w-4 h-4 border-2 border-[#667eea] border-t-transparent rounded-full animate-spin"></div>
                  </div>
                )}
                
                {/* Autocomplete Dropdown */}
                {showSuggestions && (
                  <div
                    ref={suggestionsRef}
                    className="absolute z-50 w-full mt-1 bg-white border-2 border-[#e2e8f0] rounded-md shadow-lg max-h-64 overflow-y-auto"
                  >
                    {suggestions.length > 0 ? (
                      suggestions.map((suggestion, index) => (
                        <div
                          key={suggestion.employee_id}
                          onClick={() => selectSuggestion(suggestion)}
                          className={`px-4 py-2.5 text-sm cursor-pointer transition-colors ${
                            index === selectedSuggestionIndex
                              ? 'bg-[#667eea] text-white'
                              : 'hover:bg-[#f8fafc]'
                          }`}
                        >
                          <span className="font-medium">{suggestion.zid}</span>
                          <span className={`mx-2 ${index === selectedSuggestionIndex ? 'text-white' : 'text-[#64748b]'}`}>—</span>
                          <span>{suggestion.full_name || suggestion.name}</span>
                        </div>
                      ))
                    ) : (
                      <div className="px-4 py-2.5 text-sm text-[#64748b] text-center">
                        No Record Found
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Filter: Sub-segments */}
              <select
                value={filters.subSegment}
                onChange={(e) => handleSubSegmentChange(e.target.value)}
                disabled={dropdownLoading.subSegments}
                className="px-4 py-2.5 border-2 border-[#e2e8f0] rounded-md text-sm min-w-[150px] cursor-pointer focus:outline-none focus:border-[#667eea] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="">All Sub-segments</option>
                {dropdownData.subSegments.map((subSegment) => (
                  <option key={subSegment.id} value={subSegment.id}>
                    {subSegment.name}
                  </option>
                ))}
              </select>

              {/* Filter: Projects */}
              <select
                value={filters.project}
                onChange={(e) => handleProjectChange(e.target.value)}
                disabled={!filters.subSegment || dropdownLoading.projects}
                className="px-4 py-2.5 border-2 border-[#e2e8f0] rounded-md text-sm min-w-[150px] cursor-pointer focus:outline-none focus:border-[#667eea] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="">All Projects</option>
                {dropdownData.projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>

              {/* Filter: Teams */}
              <select
                value={filters.team}
                onChange={(e) => handleTeamChange(e.target.value)}
                disabled={!filters.project || dropdownLoading.teams}
                className="px-4 py-2.5 border-2 border-[#e2e8f0] rounded-md text-sm min-w-[150px] cursor-pointer focus:outline-none focus:border-[#667eea] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="">All Teams</option>
                {dropdownData.teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Data Table */}
          <div className="bg-white rounded-lg border-2 border-[#e2e8f0] overflow-hidden">
            {/* Table Header */}
            <div className="grid grid-cols-[1fr_2fr_1.5fr_1.5fr_1.5fr_1.5fr_1fr] px-5 py-4 bg-[#f8fafc] border-b-2 border-[#e2e8f0]">
              <div className="text-xs font-semibold uppercase text-[#64748b]">ZID</div>
              <div className="text-xs font-semibold uppercase text-[#64748b]">Full Name</div>
              <div className="text-xs font-semibold uppercase text-[#64748b]">Sub-segment</div>
              <div className="text-xs font-semibold uppercase text-[#64748b]">Project</div>
              <div className="text-xs font-semibold uppercase text-[#64748b]">Team</div>
              <div className="text-xs font-semibold uppercase text-[#64748b]">Role</div>
              <div className="text-xs font-semibold uppercase text-[#64748b]">Actions</div>
            </div>

            {/* Loading State */}
            {loading ? (
              <div className="px-5 py-16 text-center">
                <div className="inline-block w-8 h-8 border-4 border-[#667eea] border-t-transparent rounded-full animate-spin mb-3"></div>
                <p className="text-sm text-[#64748b]">Loading employees...</p>
              </div>
            ) : employees.length === 0 ? (              /* Empty State */
              <div className="px-5 py-16 text-center">
                <div className="text-6xl mb-4 opacity-20">📋</div>
                <h3 className="text-lg font-semibold text-[#1e293b] mb-2">No Employees Found</h3>
                <p className="text-sm text-[#64748b]">
                  {searchQuery || filters.subSegment || filters.project || filters.team
                    ? 'Try adjusting your search or filters'
                    : 'No employees available in the system'}
                </p>
              </div>
            ) : (
              /* Table Rows */
              <>                {employees.map((employee) => (
                  <div
                    key={employee.id}
                    className="grid grid-cols-[1fr_2fr_1.5fr_1.5fr_1.5fr_1.5fr_1fr] px-5 py-4 border-b border-[#e2e8f0] last:border-b-0 items-center text-sm cursor-pointer hover:bg-[#f8fafc] transition-colors"
                    onClick={() => navigate(`/profile/employee/${employee.id}`)}
                  >
                    <div className="font-medium">{employee.zid || `Z${String(employee.id).padStart(4, '0')}`}</div>
                    <div>{employee.name || 'N/A'}</div>
                    <div>{employee.subSegment || employee.sub_segment || '—'}</div>
                    <div>{employee.project || '—'}</div>
                    <div>{employee.team || '—'}</div>
                    <div>{employee.role || '—'}</div>
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: Open edit drawer
                        }}
                        className="px-3 py-1.5 border border-[#e2e8f0] rounded bg-white text-xs hover:bg-[#f8fafc] hover:border-[#cbd5e1] transition-all"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Pagination */}
          {!loading && employees.length > 0 && totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-[#64748b]">
                Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalEmployees)} of {totalEmployees} employees
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-4 py-1.5 text-sm font-medium bg-white text-[#64748b] border border-[#e2e8f0] rounded hover:bg-[#f8fafc] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                
                <div className="flex gap-1">
                  {renderPageNumbers()}
                </div>
                
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-4 py-1.5 text-sm font-medium bg-white text-[#64748b] border border-[#e2e8f0] rounded hover:bg-[#f8fafc] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmployeesPage;
