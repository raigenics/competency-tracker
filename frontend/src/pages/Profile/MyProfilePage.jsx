import React, { useState, useEffect, useRef } from 'react';
import { employeeApi } from '../../services/api/employeeApi.js';
import employeeProfileExportService from '../../services/employeeProfileExportService.js';
import employeeProfilePdfExportService from '../../services/employeeProfilePdfExportService.js';

// Empty State Component
const EmployeeEmptyState = () => {
  return (
    <div className="bg-white rounded-lg p-20 shadow-sm text-center">
      <div className="text-8xl mb-6 opacity-30">👤</div>
      <h2 className="text-xl font-semibold text-slate-900 mb-3">No Employee Selected</h2>
      <p className="text-slate-600 text-sm max-w-md mx-auto mb-8 leading-relaxed">
        Search for an employee by name to view their detailed skill profile and competency information.
      </p>
      
      <div className="flex justify-center gap-10 flex-wrap mt-8">
        <div className="flex flex-col items-center gap-2.5 max-w-[150px]">
          <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-lg">
            1
          </div>
          <div className="text-xs text-slate-600 text-center">
            Type employee name in search box
          </div>
        </div>
        <div className="flex flex-col items-center gap-2.5 max-w-[150px]">
          <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-lg">
            2
          </div>
          <div className="text-xs text-slate-600 text-center">
            Select employee from dropdown
          </div>
        </div>
        <div className="flex flex-col items-center gap-2.5 max-w-[150px]">
          <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-lg">
            3
          </div>
          <div className="text-xs text-slate-600 text-center">
            View profile & export if needed
          </div>
        </div>
      </div>
    </div>
  );
};

// No Match Found State Component
const NoMatchFoundState = () => {
  return (
    <div className="bg-white rounded-lg p-20 shadow-sm text-center">
      <div className="text-8xl mb-6 opacity-30">🔍</div>
      <h2 className="text-xl font-semibold text-slate-900 mb-3">No matching employee found</h2>
      <p className="text-slate-600 text-sm max-w-md mx-auto mb-8 leading-relaxed">
        We couldn't find any employee with the name you entered. Please select an employee from the suggestions or try a different name.
      </p>
    </div>
  );
};

const MyProfilePage = () => {
  // State management
  const [hasSelectedEmployee, setHasSelectedEmployee] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [showNoMatchState, setShowNoMatchState] = useState(false);
  
  // Autocomplete state
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
    // Filter state for All Skills table
  const [skillsFilter, setSkillsFilter] = useState('All');
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  
  // Export state
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(null);
  
  // Refs
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const filterMenuRef = useRef(null);
  const exportMenuRef = useRef(null);
  // Fetch employee suggestions with debounce
  useEffect(() => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Only fetch if search has >= 2 characters
    if (searchValue.trim().length >= 2) {
      setIsLoading(true);
      
      debounceTimerRef.current = setTimeout(async () => {
        try {
          const results = await employeeApi.getSuggestions(searchValue.trim(), 8);
          setSuggestions(results || []);
          setShowDropdown(true);
          setHighlightedIndex(-1);
        } catch (error) {
          console.error('Failed to fetch suggestions:', error);
          setSuggestions([]);
          setShowDropdown(false);
        } finally {
          setIsLoading(false);
        }
      }, 300);
    } else {
      setSuggestions([]);
      setShowDropdown(false);
      setIsLoading(false);
    }

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchValue]);  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        !inputRef.current.contains(event.target)
      ) {
        setShowDropdown(false);
      }
      
      // Close filter menu when clicking outside
      if (
        filterMenuRef.current &&
        !filterMenuRef.current.contains(event.target)
      ) {
        setShowFilterMenu(false);
      }
      
      // Close export menu when clicking outside
      if (
        exportMenuRef.current &&
        !exportMenuRef.current.contains(event.target)
      ) {
        setShowExportMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);  // Handle employee selection
  const handleSelectEmployee = async (employee) => {
    setSelectedEmployee(employee);
    setSearchValue(employee.full_name);
    setHasSelectedEmployee(true);
    setShowDropdown(false);
    setSuggestions([]);
    setHighlightedIndex(-1);
    setShowNoMatchState(false);
    
    // Fetch employee profile
    await fetchEmployeeProfile(employee.employee_id);
  };
  
  // Fetch employee profile data
  const fetchEmployeeProfile = async (employeeId) => {
    // Prevent duplicate fetches
    if (isLoadingProfile || (employeeProfile && employeeProfile.employee_id === employeeId)) {
      return;
    }
    
    setIsLoadingProfile(true);
    
    try {
      const profile = await employeeApi.getEmployeeProfile(employeeId);
      setEmployeeProfile(profile);
    } catch (error) {
      console.error('Failed to fetch employee profile:', error);
      setEmployeeProfile(null);
      // Optionally show error message to user
    } finally {
      setIsLoadingProfile(false);
    }
  };
  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showDropdown || suggestions.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      
      case 'Enter':
        e.preventDefault();
        // If an item is highlighted, select it; otherwise select the first suggestion
        const indexToSelect = highlightedIndex >= 0 ? highlightedIndex : 0;
        if (indexToSelect < suggestions.length) {
          handleSelectEmployee(suggestions[indexToSelect]);
        }
        break;
      
      case 'Escape':
        e.preventDefault();
        setShowDropdown(false);
        setHighlightedIndex(-1);
        break;
      
      default:
        break;
    }
  };
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    
    // Case 1: Employee already selected - reload their profile
    if (hasSelectedEmployee && selectedEmployee) {
      setShowDropdown(false);
      setShowNoMatchState(false);
      fetchEmployeeProfile(selectedEmployee.employee_id);
      return;
    }
    
    // Case 2: No employee selected, but user has typed a name
    if (searchValue.trim()) {
      const trimmedSearch = searchValue.trim().toLowerCase();
      
      // Try to find exact match first
      let matchedEmployee = suggestions.find(emp => 
        emp.full_name.toLowerCase().trim() === trimmedSearch
      );
      
      // If no exact match, use first suggestion (best match)
      if (!matchedEmployee && suggestions.length > 0) {
        matchedEmployee = suggestions[0];
      }
      
      // If we found a match, auto-select it
      if (matchedEmployee) {
        handleSelectEmployee(matchedEmployee);
      } else {
        // No match found - show error state
        setShowNoMatchState(true);
        setShowDropdown(false);
        setHasSelectedEmployee(false);
        setSelectedEmployee(null);
        setEmployeeProfile(null);
      }
    }
    // Case 3: Empty search value - do nothing
  };const handleClearSearch = () => {
    setSearchValue('');
    setSelectedEmployee(null);
    setHasSelectedEmployee(false);
    setEmployeeProfile(null);
    setSuggestions([]);
    setShowDropdown(false);
    setHighlightedIndex(-1);
    setShowNoMatchState(false);
    inputRef.current?.focus();
  };const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchValue(value);
    setShowNoMatchState(false);
    
    // If user modifies the input after selection, reset selection state
    if (hasSelectedEmployee) {
      setHasSelectedEmployee(false);
      setSelectedEmployee(null);
      setEmployeeProfile(null);
    }
  };
  
  // Helper: Format date to readable format (e.g., "Jan 15, 2019")
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return 'N/A';
    }
  };
    // Helper: Calculate experience from start date to today
  const calculateExperience = (startDateString) => {
    if (!startDateString) return 'N/A';
    try {
      const startDate = new Date(startDateString);
      const today = new Date();
      
      let years = today.getFullYear() - startDate.getFullYear();
      let months = today.getMonth() - startDate.getMonth();
      
      if (months < 0) {
        years--;
        months += 12;
      }
      
      if (years === 0) {
        return `${months} month${months !== 1 ? 's' : ''}`;
      } else if (months === 0) {
        return `${years} year${years !== 1 ? 's' : ''}`;
      } else {
        return `${years} year${years !== 1 ? 's' : ''} ${months} month${months !== 1 ? 's' : ''}`;
      }
    } catch {
      return 'N/A';
    }
  };
  
  // Helper: Get most recent skill update date
  const getMostRecentUpdate = (skills) => {
    if (!skills || skills.length === 0) return null;
    
    const datesWithValues = skills
      .map(s => s.lastUpdated)
      .filter(date => date != null);
    
    if (datesWithValues.length === 0) return null;
    
    const mostRecent = new Date(Math.max(...datesWithValues.map(d => new Date(d).getTime())));
    return mostRecent;
  };
  
  // Helper: Get filtered skills based on proficiency filter
  const getFilteredSkills = (skills) => {
    if (!skills) return [];
    if (skillsFilter === 'All') return skills;
    
    const filterLevel = parseInt(skillsFilter);
    return skills.filter(skill => skill.proficiencyLevelId === filterLevel);
  };
    // Helper: Get proficiency level (1-5) from proficiency name
  const getProficiencyLevel = (proficiency) => {
    const levels = {
      'Expert': 5,
      'Advanced': 4,
      'Proficient': 4, // Legacy support
      'Intermediate': 3,
      'Beginner': 2,
      'Aware': 1
    };
    return levels[proficiency] || 3;
  };
  
  // Helper: Render stars based on proficiency level
  const renderStars = (level) => {
    return '★'.repeat(level) + '☆'.repeat(5 - level);
  };
  
  // Helper: Get badge color based on proficiency
  const getBadgeColor = (proficiency) => {
    if (proficiency === 'Expert') return 'bg-green-100 text-green-800';
    if (proficiency === 'Advanced' || proficiency === 'Proficient') return 'bg-blue-100 text-blue-800';
    return 'bg-yellow-100 text-yellow-800';
  };

  // Handler: Export employee profile to Excel
  const handleExportToExcel = async () => {
    setShowExportMenu(false);
    setIsExporting(true);
    setExportError(null);
    
    try {
      await employeeProfileExportService.exportEmployeeProfile(employeeProfile, selectedEmployee);
    } catch (error) {
      console.error('Export failed:', error);
      setExportError(error.message || 'Failed to export profile');
      // Clear error after 5 seconds
      setTimeout(() => setExportError(null), 5000);
    } finally {
      setIsExporting(false);
    }
  };

  // Handler: Export employee profile to PDF
  const handleExportToPdf = async () => {
    setShowExportMenu(false);
    setIsExporting(true);
    setExportError(null);
    
    try {
      await employeeProfilePdfExportService.exportEmployeeProfile(employeeProfile, selectedEmployee);
    } catch (error) {
      console.error('PDF export failed:', error);
      setExportError(error.message || 'Failed to export PDF');
      // Clear error after 5 seconds
      setTimeout(() => setExportError(null), 5000);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen -m-8">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Page Title */}
        <h1 className="text-3xl font-semibold text-slate-900 mb-2">Employee Profile</h1>
        <p className="text-slate-600 text-sm mb-8">Search and view detailed employee skill profiles</p>        {/* Search Toolbar - Always Visible */}
        <div className="bg-white rounded-lg p-8 mb-5 shadow-sm">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-4">
            <div className="flex-1 relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg">🔍</span>
              <input 
                ref={inputRef}
                type="text" 
                value={searchValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                className="w-full pl-12 pr-12 py-3 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search employee by name..."
                autoComplete="off"
              />
              {isLoading && (
                <div className="absolute right-12 top-1/2 -translate-y-1/2 text-slate-400 text-sm">
                  Loading...
                </div>
              )}
              {searchValue && !isLoading && (
                <button 
                  type="button"
                  onClick={handleClearSearch}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  ✕
                </button>
              )}
              
              {/* Autocomplete Dropdown */}
              {showDropdown && suggestions.length > 0 && (
                <div 
                  ref={dropdownRef}
                  className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-300 rounded-md shadow-lg z-50 max-h-80 overflow-y-auto"
                >
                  {suggestions.map((employee, index) => (
                    <div
                      key={employee.employee_id || employee.zid || index}
                      onClick={() => handleSelectEmployee(employee)}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      className={`px-4 py-3 cursor-pointer transition-colors border-b border-slate-100 last:border-b-0 ${
                        highlightedIndex === index 
                          ? 'bg-blue-50 border-l-4 border-l-blue-600' 
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="font-semibold text-slate-900 text-sm">
                        {employee.full_name}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {[
                          employee.sub_segment,
                          employee.project,
                          employee.team
                        ].filter(Boolean).join(' • ')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* No Results Message */}
              {showDropdown && !isLoading && suggestions.length === 0 && searchValue.trim().length >= 2 && (
                <div 
                  ref={dropdownRef}
                  className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-300 rounded-md shadow-lg z-50 px-4 py-6 text-center"
                >
                  <div className="text-slate-400 text-sm">No results found</div>
                  <div className="text-slate-400 text-xs mt-1">Try a different search term</div>
                </div>
              )}
            </div>            <button 
              type="submit"
              disabled={!hasSelectedEmployee && !searchValue.trim()}
              className="px-5 py-3 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 whitespace-nowrap disabled:bg-slate-300 disabled:cursor-not-allowed disabled:text-slate-500 transition-colors"
            >
              Search
            </button>
            
            {/* Export Dropdown Menu */}
            <div className="relative" ref={exportMenuRef}>
              <button 
                type="button"
                disabled={!hasSelectedEmployee || isExporting}
                onClick={() => setShowExportMenu(!showExportMenu)}
                className={`px-5 py-3 rounded-md text-sm font-medium whitespace-nowrap flex items-center gap-2 transition-colors ${
                  isExporting
                    ? 'bg-green-400 cursor-not-allowed text-white'
                    : 'bg-green-600 text-white hover:bg-green-700 disabled:bg-slate-300 disabled:cursor-not-allowed disabled:text-slate-500'
                }`}
              >
                {isExporting ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                    <span>Exporting...</span>
                  </>
                ) : (
                  <>
                    <span>📄</span>
                    <span>Export</span>
                    <span>▼</span>
                  </>
                )}
              </button>
              
              {/* Export Dropdown */}
              {showExportMenu && !isExporting && hasSelectedEmployee && (
                <div className="absolute right-0 top-full mt-2 bg-white border border-slate-300 rounded-md shadow-lg z-50 min-w-[180px]">
                  <button 
                    onClick={handleExportToExcel}
                    className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors text-slate-700 flex items-center gap-2"
                  >
                    <span>📊</span>
                    <span>Export to Excel</span>
                  </button>                  <button 
                    onClick={handleExportToPdf}
                    className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors text-slate-700 flex items-center gap-2 border-t border-slate-100"
                  >
                    <span>📄</span>
                    <span>Export to PDF</span>
                  </button>
                </div>
              )}
            </div>
            
            {/* Export Error Message */}
            {exportError && (
              <div className="absolute right-0 top-full mt-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded border border-red-200 shadow-sm">
                {exportError}
              </div>
            )}
          </form>
          
          {/* Export error display (outside form but visible) */}
          {exportError && (
            <div className="mt-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded border border-red-200">
              ⚠️ {exportError}
            </div>
          )}
        </div>{/* Conditional Content - Empty State or Employee Profile */}
        {showNoMatchState ? (
          <NoMatchFoundState />
        ) : !hasSelectedEmployee ? (
          <EmployeeEmptyState />
        ) : isLoadingProfile ? (
          <div className="bg-white rounded-lg p-20 shadow-sm text-center">
            <div className="text-4xl mb-4">⏳</div>
            <div className="text-slate-600 text-sm">Loading employee profile...</div>
          </div>
        ) : employeeProfile ? (
          <>
            {/* Employee Profile Content - Dynamic Data */}

        {/* Identity Card */}
        <div className="bg-white rounded-lg p-8 mb-5 shadow-sm">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-3xl font-semibold text-slate-900 mb-1.5">{employeeProfile.employee_name || 'N/A'}</h2>
              <span className="inline-block text-sm text-slate-600 bg-slate-100 px-3 py-1 rounded">
                ZID: {selectedEmployee?.zid || 'N/A'}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-5">
            <div className="flex items-start gap-2.5">
              <span className="text-blue-600 text-lg mt-0.5">📍</span>
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Sub-Segment</div>
                <div className="text-sm font-medium text-slate-900">{employeeProfile.organization?.sub_segment || 'N/A'}</div>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <span className="text-blue-600 text-lg mt-0.5">🏢</span>
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Project</div>
                <div className="text-sm font-medium text-slate-900">{employeeProfile.organization?.project || 'N/A'}</div>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <span className="text-blue-600 text-lg mt-0.5">👥</span>
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Team</div>
                <div className="text-sm font-medium text-slate-900">{employeeProfile.organization?.team || 'N/A'}</div>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <span className="text-blue-600 text-lg mt-0.5">💼</span>
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Role</div>
                <div className="text-sm font-medium text-slate-900">{employeeProfile.role || 'N/A'}</div>
              </div>
            </div>            <div className="flex items-start gap-2.5">
              <span className="text-blue-600 text-lg mt-0.5">📅</span>
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Started Working</div>
                <div className="text-sm font-medium text-slate-900">{formatDate(employeeProfile.start_date_of_working)}</div>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <span className="text-blue-600 text-lg mt-0.5">⏱️</span>
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Experience</div>
                <div className="text-sm font-medium text-slate-900">{calculateExperience(employeeProfile.start_date_of_working)}</div>
              </div>
            </div>
          </div>
        </div>        {/* Metrics Cards */}
        <div className="grid grid-cols-4 gap-5 mb-5">
          <div className="bg-white rounded-lg p-6 shadow-sm text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">{employeeProfile.total_skills || 0}</div>
            <div className="text-xs font-medium text-slate-600">Total Skills</div>
          </div>
          <div className="bg-white rounded-lg p-6 shadow-sm text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">
              {employeeProfile.skills?.filter(s => s.certification && s.certification.trim() !== '').length || 0}
            </div>
            <div className="text-xs font-medium text-slate-600">Certified Skills</div>
          </div>          <div className="bg-white rounded-lg p-6 shadow-sm text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">
              {employeeProfile.skills?.filter(s => {
                if (!s.lastUpdated) return false;
                const lastUpdated = new Date(s.lastUpdated);
                const ninetyDaysAgo = new Date();
                ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
                return lastUpdated >= ninetyDaysAgo;
              }).length || 0}
            </div>
            <div className="text-xs font-medium text-slate-600">Recently Updated</div>
          </div>          <div className="bg-white rounded-lg p-6 shadow-sm text-center">
            <div className="text-2xl font-bold text-blue-600 mb-2">
              {(() => {
                const mostRecentDate = getMostRecentUpdate(employeeProfile.skills);
                return mostRecentDate ? formatDate(mostRecentDate) : '–';
              })()}
            </div>
            <div className="text-xs font-medium text-slate-600">Last Updated</div>
          </div>
        </div>{/* Core Expertise */}
        <div className="bg-white rounded-lg p-8 mb-5 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-5 flex items-center gap-2">
            <span className="text-xl">🌟</span>
            Core Expertise
          </h3>          <div className="flex flex-wrap gap-3">
            {employeeProfile.skills && employeeProfile.skills.length > 0 ? (
              employeeProfile.skills
                .filter(skill => skill.proficiencyLevelId && skill.proficiencyLevelId >= 4)                .sort((a, b) => {
                  // Sort by proficiency level DESC (5 first, then 4)
                  if (b.proficiencyLevelId !== a.proficiencyLevelId) {
                    return b.proficiencyLevelId - a.proficiencyLevelId;
                  }
                  // Secondary sort by years of experience DESC
                  return (b.yearsOfExperience || 0) - (a.yearsOfExperience || 0);
                })
                .slice(0, 10)
                .map((skill, index) => {
                  // ALWAYS use proficiencyLevelId for accurate star rendering (5 → ★★★★★, 4 → ★★★★)
                  const level = skill.proficiencyLevelId;
                  return (
                    <div 
                      key={index}
                      className={`px-4 py-2.5 rounded-md text-sm font-medium flex items-center gap-2 ${getBadgeColor(skill.proficiency)}`}
                    >
                      <span>{skill.skillName || skill.name}</span>
                      <span className="text-yellow-500">{renderStars(level)}</span>
                    </div>
                  );
                })
            ) : (
              <div className="text-slate-400 text-sm">No core expertise data available</div>
            )}
          </div>
        </div>{/* Skills Table */}
        <div className="bg-white rounded-lg p-8 shadow-sm">
          <div className="flex justify-between items-center mb-5">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <span className="text-xl">📊</span>
              All Skills ({getFilteredSkills(employeeProfile.skills).length})
            </h3>
            <div className="flex gap-2.5 relative">
              {/* Filter Dropdown */}
              <div className="relative" ref={filterMenuRef}>
                <button 
                  onClick={() => setShowFilterMenu(!showFilterMenu)}
                  className="px-4 py-2 border border-slate-300 bg-white rounded-md text-xs font-medium text-slate-600 hover:border-slate-400"
                >
                  Filter: {skillsFilter === 'All' ? 'All Levels' : `${skillsFilter} Star${skillsFilter === '1' ? '' : 's'}`} ▼
                </button>
                
                {showFilterMenu && (
                  <div className="absolute right-0 top-full mt-2 bg-white border border-slate-300 rounded-md shadow-lg z-50 min-w-[160px]">
                    <button 
                      onClick={() => { setSkillsFilter('All'); setShowFilterMenu(false); }}
                      className={`w-full text-left px-4 py-2.5 text-xs hover:bg-slate-50 transition-colors border-b border-slate-100 ${
                        skillsFilter === 'All' ? 'bg-blue-50 font-semibold text-blue-700' : 'text-slate-700'
                      }`}
                    >
                      All Levels
                    </button>
                    <button 
                      onClick={() => { setSkillsFilter('5'); setShowFilterMenu(false); }}
                      className={`w-full text-left px-4 py-2.5 text-xs hover:bg-slate-50 transition-colors border-b border-slate-100 ${
                        skillsFilter === '5' ? 'bg-blue-50 font-semibold text-blue-700' : 'text-slate-700'
                      }`}
                    >
                      ★★★★★ Expert (5)
                    </button>
                    <button 
                      onClick={() => { setSkillsFilter('4'); setShowFilterMenu(false); }}
                      className={`w-full text-left px-4 py-2.5 text-xs hover:bg-slate-50 transition-colors border-b border-slate-100 ${
                        skillsFilter === '4' ? 'bg-blue-50 font-semibold text-blue-700' : 'text-slate-700'
                      }`}
                    >
                      ★★★★☆ Advanced (4)
                    </button>
                    <button 
                      onClick={() => { setSkillsFilter('3'); setShowFilterMenu(false); }}
                      className={`w-full text-left px-4 py-2.5 text-xs hover:bg-slate-50 transition-colors border-b border-slate-100 ${
                        skillsFilter === '3' ? 'bg-blue-50 font-semibold text-blue-700' : 'text-slate-700'
                      }`}
                    >
                      ★★★☆☆ Intermediate (3)
                    </button>
                    <button 
                      onClick={() => { setSkillsFilter('2'); setShowFilterMenu(false); }}
                      className={`w-full text-left px-4 py-2.5 text-xs hover:bg-slate-50 transition-colors border-b border-slate-100 ${
                        skillsFilter === '2' ? 'bg-blue-50 font-semibold text-blue-700' : 'text-slate-700'
                      }`}
                    >
                      ★★☆☆☆ Beginner (2)
                    </button>
                    <button 
                      onClick={() => { setSkillsFilter('1'); setShowFilterMenu(false); }}
                      className={`w-full text-left px-4 py-2.5 text-xs hover:bg-slate-50 transition-colors ${
                        skillsFilter === '1' ? 'bg-blue-50 font-semibold text-blue-700' : 'text-slate-700'
                      }`}
                    >
                      ★☆☆☆☆ Aware (1)
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-slate-200">
                  <th className="text-left py-3 px-3 bg-slate-50 text-xs font-semibold text-slate-600">Skill Name</th>
                  <th className="text-left py-3 px-3 bg-slate-50 text-xs font-semibold text-slate-600">Category</th>
                  <th className="text-left py-3 px-3 bg-slate-50 text-xs font-semibold text-slate-600">Proficiency</th>
                  <th className="text-left py-3 px-3 bg-slate-50 text-xs font-semibold text-slate-600">Years Exp</th>
                  <th className="text-left py-3 px-3 bg-slate-50 text-xs font-semibold text-slate-600">Last Used</th>
                  <th className="text-left py-3 px-3 bg-slate-50 text-xs font-semibold text-slate-600">Certifications</th>
                </tr>
              </thead>              <tbody>
                {employeeProfile.skills && employeeProfile.skills.length > 0 ? (
                  getFilteredSkills(employeeProfile.skills).map((skill, index) => {
                    // Use proficiencyLevelId directly for accurate star rendering
                    const level = skill.proficiencyLevelId || getProficiencyLevel(skill.proficiency);
                    return (
                      <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">                        <td className="py-4 px-3 text-sm"><strong>{skill.skillName || skill.name}</strong></td>
                        <td className="py-4 px-3 text-sm">
                          <span className="bg-slate-100 px-2.5 py-1 rounded text-xs text-slate-600">
                            {skill.category || '–'}
                          </span>
                        </td>
                        <td className="py-4 px-3">
                          <span className="text-yellow-500">{renderStars(level)}</span>
                        </td>
                        <td className="py-4 px-3 text-sm">{skill.yearsOfExperience || 0}</td>
                        <td className="py-4 px-3 text-xs text-green-600">
                          {skill.lastUsed ? formatDate(skill.lastUsed) : 'N/A'}
                        </td>
                        <td className="py-4 px-3 text-xs text-slate-600">
                          {skill.certification && skill.certification.trim() !== '' ? skill.certification : '-'}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan="6" className="py-8 text-center text-slate-400 text-sm">
                      {skillsFilter !== 'All' 
                        ? `No skills found with ${skillsFilter} star proficiency level` 
                        : 'No skills data available'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
          </>
        ) : (
          <div className="bg-white rounded-lg p-20 shadow-sm text-center">
            <div className="text-slate-400 text-sm">Failed to load employee profile</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyProfilePage;
