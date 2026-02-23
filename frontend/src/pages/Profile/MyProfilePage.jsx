import React, { useState, useEffect, useRef } from 'react';
import { employeeApi } from '../../services/api/employeeApi.js';
import employeeProfileExportService from '../../services/employeeProfileExportService.js';
import employeeProfilePdfExportService from '../../services/employeeProfilePdfExportService.js';
import './EmployeeProfile.css';

// Empty State Component - matches HTML wireframe exactly
const EmployeeEmptyState = () => {
  return (
    <section className="card">
      <div className="empty">
        <div>
          <div className="icon">👤</div>
          <h2>No employee selected</h2>
          <p>Search for an employee by <strong>name</strong> or <strong>ZID</strong> to view their skills, proficiency, certifications, and last updated details.</p>
          <div className="help" style={{ marginTop: '12px' }}>
            You can press <code>Enter</code> to search, then pick from the suggestions list.
          </div>
        </div>
      </div>
    </section>
  );
};

// No Match Found State Component
const NoMatchFoundState = () => {
  return (
    <section className="card">
      <div className="empty">
        <div>
          <div className="icon">🔍</div>
          <h2>No matching employee found</h2>
          <p>We couldn't find any employee with the name you entered. Please select an employee from the suggestions or try a different name.</p>
        </div>
      </div>
    </section>
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
  const [skillsSearchTerm, setSkillsSearchTerm] = useState('');
  
  // Export state
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(null);
  
  // Refs
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const debounceTimerRef = useRef(null);
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
      
      case 'Enter': {
        e.preventDefault();
        // If an item is highlighted, select it; otherwise select the first suggestion
        const indexToSelect = highlightedIndex >= 0 ? highlightedIndex : 0;
        if (indexToSelect < suggestions.length) {
          handleSelectEmployee(suggestions[indexToSelect]);
        }
        break;
      }
      
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
  };

  const handleInputChange = (e) => {
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
  
  // Helper: Get filtered skills based on proficiency filter and search term
  const getFilteredSkills = (skills) => {
    if (!skills) return [];
    
    let filtered = skills;
    
    // Filter by search term
    if (skillsSearchTerm.trim()) {
      const search = skillsSearchTerm.trim().toLowerCase();
      filtered = filtered.filter(skill => 
        (skill.skillName || skill.name || '').toLowerCase().includes(search) ||
        (skill.category || '').toLowerCase().includes(search)
      );
    }
    
    // Filter by proficiency level
    if (skillsFilter !== 'All') {
      const filterLevel = parseInt(skillsFilter);
      filtered = filtered.filter(skill => skill.proficiencyLevelId === filterLevel);
    }
    
    return filtered;
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

  // Calculate "profile updated X days ago"
  const getProfileUpdatedText = () => {
    const mostRecent = getMostRecentUpdate(employeeProfile?.skills);
    if (!mostRecent) return '';
    const now = new Date();
    const diffDays = Math.floor((now - mostRecent) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Profile updated: today';
    if (diffDays === 1) return 'Profile updated: 1 day ago';
    return `Profile updated: ${diffDays} days ago`;
  };

  return (
    <div className="employee-profile">
      {/* Main Content - matches .main { padding: 22px } */}
      <main className="ep-main">
        {/* Page Header - matches .pagehead */}
        <div className="pagehead">
          <h1>Employee Profile</h1>
          <p>Search and view detailed employee skill profiles</p>
        </div>

        {/* Search Card - matches HTML exactly */}
        <section className="card" style={{ marginTop: '14px' }}>
          <div className="searchbar">
            <div className="search-input-wrapper">
              <input
                ref={inputRef}
                type="text"
                value={searchValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Search by name or ZID (e.g., Binu or Z003HD1U)..."
                autoComplete="off"
              />
              
              {/* Autocomplete Dropdown */}
              {showDropdown && suggestions.length > 0 && (
                <div ref={dropdownRef} className="dropdown">
                  {suggestions.map((employee, index) => (
                    <div
                      key={employee.employee_id || employee.zid || index}
                      onClick={() => handleSelectEmployee(employee)}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      className={`dropdown-item ${highlightedIndex === index ? 'highlighted' : ''}`}
                    >
                      <div className="emp-name">{employee.full_name}</div>
                      <div className="emp-meta">
                        {[employee.sub_segment, employee.project, employee.team].filter(Boolean).join(' • ')}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* No Results Message */}
              {showDropdown && !isLoading && suggestions.length === 0 && searchValue.trim().length >= 2 && (
                <div ref={dropdownRef} className="dropdown" style={{ padding: '18px', textAlign: 'center' }}>
                  <div style={{ color: '#64748b', fontSize: '14px' }}>No results found</div>
                  <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px' }}>Try a different search term</div>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleSearchSubmit}
              className="btn primary"
            >
              Search
            </button>

            {/* Export Button with Dropdown */}
            <div style={{ position: 'relative' }} ref={exportMenuRef}>
              <button
                type="button"
                onClick={() => hasSelectedEmployee && setShowExportMenu(!showExportMenu)}
                className={`btn ${!hasSelectedEmployee ? 'disabled' : ''}`}
                disabled={!hasSelectedEmployee || isExporting}
                aria-disabled={!hasSelectedEmployee}
              >
                {isExporting ? 'Exporting...' : 'Export ▾'}
              </button>

              {showExportMenu && hasSelectedEmployee && !isExporting && (
                <div className="export-menu">
                  <button onClick={handleExportToExcel}>
                    <span>📊</span> Export to Excel
                  </button>
                  <button onClick={handleExportToPdf}>
                    <span>📄</span> Export to PDF
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="help">
            Tip: Start typing at least <strong>2 characters</strong>. Example: <code>Binu</code> or <code>Z003HD1U</code>.
          </div>

          {exportError && (
            <div style={{ marginTop: '8px', color: '#dc2626', fontSize: '12px' }}>
              ⚠️ {exportError}
            </div>
          )}
        </section>

        {/* Conditional Content - Empty State or Employee Profile */}
        {showNoMatchState ? (
          <NoMatchFoundState />
        ) : !hasSelectedEmployee ? (
          <EmployeeEmptyState />
        ) : isLoadingProfile ? (
          <section className="card">
            <div className="loading-card">
              <div className="icon">⏳</div>
              <div style={{ color: '#64748b', fontSize: '14px' }}>Loading employee profile...</div>
            </div>
          </section>
        ) : employeeProfile ? (
          <>
            {/* Profile Header Card */}
            <section className="card">
              <div className="profilehead">
                <div>
                  <p className="name">{employeeProfile.employee_name || 'N/A'}</p>
                  <div className="idchip">ZID: {selectedEmployee?.zid || 'N/A'}</div>
                  <div className="subline">{getProfileUpdatedText()}</div>
                </div>
                <div>
                  <button
                    className="btn"
                    onClick={() => setShowExportMenu(!showExportMenu)}
                    disabled={isExporting}
                  >
                    {isExporting ? 'Exporting...' : 'Export Profile ▾'}
                  </button>
                </div>
              </div>

              {/* Meta Grid - matches HTML exactly */}
              <div className="metaGrid">
                <div className="metaItem">
                  <div className="dot">S</div>
                  <div>
                    <p className="label">Sub-Segment</p>
                    <div className="value">{employeeProfile.organization?.sub_segment || 'N/A'}</div>
                  </div>
                </div>
                <div className="metaItem">
                  <div className="dot">P</div>
                  <div>
                    <p className="label">Project</p>
                    <div className="value">{employeeProfile.organization?.project || 'N/A'}</div>
                  </div>
                </div>
                <div className="metaItem">
                  <div className="dot">T</div>
                  <div>
                    <p className="label">Team</p>
                    <div className="value">{employeeProfile.organization?.team || 'N/A'}</div>
                  </div>
                </div>
                <div className="metaItem">
                  <div className="dot">R</div>
                  <div>
                    <p className="label">Role</p>
                    <div className="value">{employeeProfile.role || 'N/A'}</div>
                  </div>
                </div>
              </div>

              {/* Stats Strip - matches HTML exactly */}
              <div className="statsStrip">
                <div className="stat">
                  <span className="k">Total Skills</span>
                  <span className="v">{employeeProfile.total_skills || 0}</span>
                </div>
                <span className="sep"></span>
                <div className="stat">
                  <span className="k">Certified</span>
                  <span className="v">
                    {employeeProfile.skills?.filter(s => s.certification && s.certification.trim() !== '').length || 0}
                  </span>
                </div>
                <span className="sep"></span>
                <div className="stat">
                  <span className="k">Recently Updated</span>
                  <span className="v">
                    {employeeProfile.skills?.filter(s => {
                      if (!s.lastUpdated) return false;
                      const lastUpdated = new Date(s.lastUpdated);
                      const ninetyDaysAgo = new Date();
                      ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
                      return lastUpdated >= ninetyDaysAgo;
                    }).length || 0}
                  </span>
                </div>
                <span className="sep"></span>
                <div className="stat">
                  <span className="k">Last Updated</span>
                  <span className="v">
                    {(() => {
                      const mostRecentDate = getMostRecentUpdate(employeeProfile.skills);
                      return mostRecentDate ? formatDate(mostRecentDate) : '–';
                    })()}
                  </span>
                </div>
              </div>
            </section>

            {/* Core Expertise Card */}
            <section className="card">
              <div className="sectionTitle">
                <h3>Core Expertise</h3>
                <span className="help" style={{ margin: 0 }}>Top skills based on proficiency + recency</span>
              </div>
              <div>
                {employeeProfile.skills && employeeProfile.skills.length > 0 ? (
                  (() => {
                    const expertSkills = employeeProfile.skills
                      .filter(skill => skill.proficiencyLevelId && skill.proficiencyLevelId >= 3)
                      .sort((a, b) => {
                        if (b.proficiencyLevelId !== a.proficiencyLevelId) {
                          return b.proficiencyLevelId - a.proficiencyLevelId;
                        }
                        return (b.yearsOfExperience || 0) - (a.yearsOfExperience || 0);
                      });

                    const visibleSkills = expertSkills.slice(0, 6);
                    const remainingCount = expertSkills.length - 6;

                    return (
                      <>
                        {visibleSkills.map((skill, index) => {
                          const level = skill.proficiencyLevelId || getProficiencyLevel(skill.proficiency);
                          return (
                            <span key={index} className="pill">
                              {skill.skillName || skill.name} {renderStars(level)}
                            </span>
                          );
                        })}
                        {remainingCount > 0 && (
                          <span className="more">+{remainingCount} more</span>
                        )}
                      </>
                    );
                  })()
                ) : (
                  <div style={{ color: '#64748b', fontSize: '14px' }}>No core expertise data available</div>
                )}
              </div>
            </section>

            {/* All Skills Card */}
            <section className="card">
              <div className="sectionTitle">
                <h3>All Skills ({getFilteredSkills(employeeProfile.skills).length})</h3>
                <div className="tableTop">
                  <div className="left">
                    <input
                      type="text"
                      placeholder="Search within skills..."
                      value={skillsSearchTerm}
                      onChange={(e) => setSkillsSearchTerm(e.target.value)}
                    />
                    <select
                      value={skillsFilter}
                      onChange={(e) => setSkillsFilter(e.target.value)}
                    >
                      <option value="All">Filter: All Levels</option>
                      <option value="5">Expert</option>
                      <option value="4">Proficient</option>
                      <option value="3">Intermediate</option>
                      <option value="2">Beginner</option>
                      <option value="1">Aware</option>
                    </select>
                  </div>
                </div>
              </div>

              <table>
                <thead>
                  <tr>
                    <th>Skill Name</th>
                    <th>Category</th>
                    <th>Proficiency</th>
                    <th>Years Exp</th>
                    <th>Last Used</th>
                    <th>Certifications</th>
                  </tr>
                </thead>
                <tbody>
                  {getFilteredSkills(employeeProfile.skills).length > 0 ? (
                    getFilteredSkills(employeeProfile.skills).map((skill, index) => {
                      const level = skill.proficiencyLevelId || getProficiencyLevel(skill.proficiency);
                      return (
                        <tr key={index}>
                          <td><strong>{skill.skillName || skill.name}</strong></td>
                          <td><span className="badge">{skill.category || '–'}</span></td>
                          <td>{renderStars(level)}</td>
                          <td>{skill.yearsOfExperience || 0}</td>
                          <td>{skill.lastUsed ? formatDate(skill.lastUsed) : '–'}</td>
                          <td>{skill.certification && skill.certification.trim() !== '' ? skill.certification : '—'}</td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', color: '#94a3b8', padding: '24px' }}>
                        {skillsFilter !== 'All' || skillsSearchTerm.trim()
                          ? 'No skills found matching your criteria'
                          : 'No skills data available'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>
          </>
        ) : (
          <section className="card">
            <div className="empty">
              <div>
                <div className="icon">⚠️</div>
                <h2>Failed to load profile</h2>
                <p>An error occurred while loading the employee profile. Please try again.</p>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default MyProfilePage;
