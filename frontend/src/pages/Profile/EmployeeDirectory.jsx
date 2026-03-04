import React, { useState, useEffect, useRef } from 'react';
import { employeeApi } from '../../services/api/employeeApi.js';
import employeeProfileExportService from '../../services/employeeProfileExportService.js';
import employeeProfilePdfExportService from '../../services/employeeProfilePdfExportService.js';
import './EmployeeProfile.css';

// Empty State Component - matches new wireframe
const EmployeeEmptyState = () => {
  return (
    <div className="section-card">
      <div className="empty-state">
        <div>
          <div className="icon">👤</div>
          <h2>No employee selected</h2>
          <p>Search for an employee by <strong>name</strong> or <strong>ZID</strong> to view their skills, proficiency, certifications, and last updated details.</p>
          <div className="help-text">
            You can press <code>Enter</code> to search, then pick from the suggestions list.
          </div>
        </div>
      </div>
    </div>
  );
};

// No Match Found State Component
const NoMatchFoundState = () => {
  return (
    <div className="section-card">
      <div className="empty-state">
        <div>
          <div className="icon">🔍</div>
          <h2>No matching employee found</h2>
          <p>We couldn't find any employee with the name you entered. Please select an employee from the suggestions or try a different name.</p>
        </div>
      </div>
    </div>
  );
};

const EmployeeDirectory = () => {
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
  const [_exportError, setExportError] = useState(null);
  
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
  
  // Helper: Get proficiency level name from level ID
  const getProficiencyLevelName = (levelId) => {
    const names = {
      1: 'Novice',
      2: 'Adv. Beginner',
      3: 'Competent',
      4: 'Proficient',
      5: 'Expert'
    };
    return names[levelId] || 'Unknown';
  };
  
  // Helper: Get initials from employee name (e.g., "James, Binu" → "BJ")
  const getInitials = (name) => {
    if (!name) return '??';
    // Handle "LastName, FirstName" format
    const parts = name.split(',').map(p => p.trim());
    if (parts.length >= 2) {
      return (parts[1][0] + parts[0][0]).toUpperCase();
    }
    // Handle "FirstName LastName" format
    const spaceParts = name.split(' ').filter(p => p.trim());
    if (spaceParts.length >= 2) {
      return (spaceParts[0][0] + spaceParts[spaceParts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };
  
  // Helper: Check if a skill is stale (lastUsed > 12 months ago)
  const isSkillStale = (lastUsed) => {
    if (!lastUsed) return false;
    const lastUsedDate = new Date(lastUsed);
    const twelveMonthsAgo = new Date();
    twelveMonthsAgo.setMonth(twelveMonthsAgo.getMonth() - 12);
    return lastUsedDate < twelveMonthsAgo;
  };
  
  // Helper: Calculate years since lastUsed
  const getYearsStale = (lastUsed) => {
    if (!lastUsed) return 0;
    const lastUsedDate = new Date(lastUsed);
    const now = new Date();
    const diffYears = (now - lastUsedDate) / (1000 * 60 * 60 * 24 * 365);
    return Math.floor(diffYears);
  };
  
  // Helper: Get proficiency bar width based on level
  const getProficiencyBarWidth = (levelId) => {
    const widths = { 1: '20%', 2: '40%', 3: '60%', 4: '80%', 5: '100%' };
    return widths[levelId] || '60%';
  };
  
  // Helper: Format last used date for display (e.g., "Jun 2025")
  const formatLastUsed = (dateString) => {
    if (!dateString) return '–';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    } catch {
      return '–';
    }
  };
  
  // Helper: Check if category is DevOps related
  const isDevOpsCategory = (category) => {
    if (!category) return false;
    const lc = category.toLowerCase();
    return lc.includes('devops') || lc.includes('platform') || lc.includes('infrastructure');
  };
  
  // Helper: Render stars based on proficiency level
  const _renderStars = (level) => {
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
  const _getProfileUpdatedText = () => {
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
      <main className="ep-main">
        {/* TOPBAR - Sticky header with search */}
        <div className="topbar">
          <div className="topbar-title">
            <h1>Employee Profile</h1>
            <p>Search and view detailed employee skill profiles</p>
          </div>
          <div className="search-row">
            <div className="search-wrap">
              <span className="search-icon">⌕</span>
              <input
                ref={inputRef}
                type="text"
                value={searchValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Search by name or ZID…"
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
                  <div style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>No results found</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>Try a different search term</div>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleSearchSubmit}
              className="btn-primary"
            >
              Search
            </button>

            {/* Export Button with Dropdown */}
            <div style={{ position: 'relative' }} ref={exportMenuRef}>
              <button
                type="button"
                onClick={() => hasSelectedEmployee && setShowExportMenu(!showExportMenu)}
                className={`btn-outline ${!hasSelectedEmployee ? 'disabled' : ''}`}
                disabled={!hasSelectedEmployee || isExporting}
              >
                {isExporting ? 'Exporting...' : '↑ Export ▾'}
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
        </div>

        {/* PAGE CONTENT */}
        <div className="content">
          {/* Conditional Content - Empty State or Employee Profile */}
          {showNoMatchState ? (
            <NoMatchFoundState />
          ) : !hasSelectedEmployee ? (
            <EmployeeEmptyState />
          ) : isLoadingProfile ? (
            <div className="section-card">
              <div className="loading-state">
                <div className="icon">⏳</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>Loading employee profile...</div>
              </div>
            </div>
          ) : employeeProfile ? (
            <>
              {/* PROFILE HEADER CARD */}
              <div className="profile-header">
                <div className="profile-left">
                  <div className="avatar">
                    {getInitials(employeeProfile.employee_name)}
                  </div>
                  <div className="profile-name-block">
                    <h2>{employeeProfile.employee_name || 'N/A'}</h2>
                    <span className="zid-badge">ZID: {selectedEmployee?.zid || 'N/A'}</span>
                    <div className="meta-strip">
                      <div className="meta-chip">
                        <span className="meta-chip-label">Sub-Seg</span>
                        <span className="meta-chip-val">{employeeProfile.organization?.sub_segment || 'N/A'}</span>
                      </div>
                      <div className="meta-chip">
                        <span className="meta-chip-label">Project</span>
                        <span className="meta-chip-val">{employeeProfile.organization?.project || 'N/A'}</span>
                      </div>
                      <div className="meta-chip">
                        <span className="meta-chip-label">Team</span>
                        <span className="meta-chip-val">{employeeProfile.organization?.team || 'N/A'}</span>
                      </div>
                      <div className="meta-chip">
                        <span className="meta-chip-label">Role</span>
                        <span className="meta-chip-val">{employeeProfile.role || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="profile-right">
                  <div className="stat-pills">
                    <div className="stat-pill">
                      <div className="val">{employeeProfile.total_skills || 0}</div>
                      <div className="lbl">Total Skills</div>
                    </div>
                    <div className="stat-pill">
                      <div className="val">
                        {employeeProfile.skills?.filter(s => s.certification && s.certification.trim() !== '').length || 0}
                      </div>
                      <div className="lbl">Certified</div>
                    </div>
                  </div>
                  <span className="freshness-tag">
                    Last updated: {(() => {
                      const mostRecentDate = getMostRecentUpdate(employeeProfile.skills);
                      return mostRecentDate ? formatDate(mostRecentDate) : '–';
                    })()}
                  </span>
                </div>
              </div>

              {/* CORE EXPERTISE CARD */}
              <div className="section-card">
                <div className="section-header">
                  <div className="section-title">Core Expertise</div>
                  <div className="section-subtitle">Top 3 by proficiency · recently used</div>
                </div>
                <div className="expertise-grid">
                  {employeeProfile.skills && employeeProfile.skills.length > 0 ? (
                    (() => {
                      const sortedSkills = [...employeeProfile.skills]
                        .sort((a, b) => {
                          if (b.proficiencyLevelId !== a.proficiencyLevelId) {
                            return (b.proficiencyLevelId || 0) - (a.proficiencyLevelId || 0);
                          }
                          return (b.yearsOfExperience || 0) - (a.yearsOfExperience || 0);
                        });

                      return sortedSkills.slice(0, 3).map((skill, index) => {
                        const level = skill.proficiencyLevelId || getProficiencyLevel(skill.proficiency);
                        const stale = isSkillStale(skill.lastUsed);
                        
                        return (
                          <div 
                            key={index} 
                            className={`expertise-card ${stale ? 'stale' : ''}`}
                          >
                            <div className="expertise-top">
                              <div>
                                <div className="skill-name">{skill.skillName || skill.name}</div>
                                <div className="skill-cat">{skill.category || '–'}</div>
                              </div>
                              {stale && (
                                <span className="signal-badge signal-stale">⚠ Stale</span>
                              )}
                            </div>
                            <div className="proficiency-bar-wrap">
                              <div className="proficiency-bar">
                                <div 
                                  className={`proficiency-fill ${stale ? 'stale' : ''}`}
                                  style={{ width: getProficiencyBarWidth(level) }}
                                />
                              </div>
                              <span className="proficiency-label">
                                {getProficiencyLevelName(level)} · {skill.yearsOfExperience || 0} yrs
                              </span>
                            </div>
                          </div>
                        );
                      });
                    })()
                  ) : (
                    <div style={{ gridColumn: '1 / -1', color: 'var(--text-muted)', fontSize: '13.5px', padding: '20px', textAlign: 'center' }}>
                      No core expertise data available
                    </div>
                  )}
                </div>
              </div>

              {/* ALL SKILLS TABLE CARD */}
              <div className="section-card">
                <div className="section-header">
                  <div className="section-title">
                    All Skills <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({getFilteredSkills(employeeProfile.skills).length})</span>
                  </div>
                </div>

                <div className="table-toolbar">
                  <div className="table-search">
                    <span className="search-icon">⌕</span>
                    <input
                      type="text"
                      placeholder="Search within skills…"
                      value={skillsSearchTerm}
                      onChange={(e) => setSkillsSearchTerm(e.target.value)}
                    />
                  </div>
                  <div className="filter-group">
                    <button 
                      className={`filter-btn ${skillsFilter === 'All' ? 'active' : ''}`}
                      onClick={() => setSkillsFilter('All')}
                    >
                      All Levels
                    </button>
                    <button 
                      className={`filter-btn ${skillsFilter === '5' ? 'active' : ''}`}
                      onClick={() => setSkillsFilter('5')}
                    >
                      Expert
                    </button>
                    <button 
                      className={`filter-btn ${skillsFilter === '4' ? 'active' : ''}`}
                      onClick={() => setSkillsFilter('4')}
                    >
                      Proficient
                    </button>
                    <button 
                      className={`filter-btn ${skillsFilter === '3' ? 'active' : ''}`}
                      onClick={() => setSkillsFilter('3')}
                    >
                      Competent
                    </button>
                    <button 
                      className={`filter-btn ${skillsFilter === '2' ? 'active' : ''}`}
                      onClick={() => setSkillsFilter('2')}
                    >
                      Adv. Beginner
                    </button>
                    <button 
                      className={`filter-btn ${skillsFilter === '1' ? 'active' : ''}`}
                      onClick={() => setSkillsFilter('1')}
                    >
                      Novice
                    </button>
                  </div>
                </div>

                <table>
                  <thead>
                    <tr>
                      <th>Skill Name</th>
                      <th>Category</th>
                      <th>Proficiency</th>
                      <th>Yrs Exp</th>
                      <th>Last Used</th>
                      <th>Signal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getFilteredSkills(employeeProfile.skills).length > 0 ? (
                      getFilteredSkills(employeeProfile.skills).map((skill, index) => {
                        const level = skill.proficiencyLevelId || getProficiencyLevel(skill.proficiency);
                        const stale = isSkillStale(skill.lastUsed);
                        const yearsStale = getYearsStale(skill.lastUsed);
                        const isDevOps = isDevOpsCategory(skill.category);
                        
                        return (
                          <tr key={index} className={stale ? 'stale-row' : ''}>
                            <td className="skill-name-cell">{skill.skillName || skill.name}</td>
                            <td>
                              <span className={`cat-tag ${stale ? 'stale' : ''} ${isDevOps && !stale ? 'devops' : ''}`}>
                                {skill.category || '–'}
                              </span>
                            </td>
                            <td>
                              <div className="proficiency-cell">
                                <div className="prof-dots">
                                  {[1, 2, 3, 4, 5].map((dot) => (
                                    <div 
                                      key={dot} 
                                      className={`prof-dot ${dot <= level ? 'filled' : ''} ${dot <= level && stale ? 'stale' : ''}`}
                                    />
                                  ))}
                                </div>
                                <span className={`prof-text ${stale ? 'stale' : ''}`}>
                                  {getProficiencyLevelName(level)}
                                </span>
                              </div>
                            </td>
                            <td className="yoe-cell">{skill.yearsOfExperience || 0}</td>
                            <td className="date-cell">
                              {stale ? (
                                <span className="stale-warn">
                                  <span className="dot"></span>
                                  {formatLastUsed(skill.lastUsed)}
                                </span>
                              ) : (
                                <span className="fresh-date">{formatLastUsed(skill.lastUsed)}</span>
                              )}
                            </td>
                            <td>
                              {stale ? (
                                <span className="signal-badge signal-stale">
                                  ⚠ Stale · {yearsStale}+ yrs
                                </span>
                              ) : (
                                <span className="signal-badge signal-fresh">● Current</span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>
                          {skillsFilter !== 'All' || skillsSearchTerm.trim()
                            ? 'No skills found matching your criteria'
                            : 'No skills data available'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>

                {/* LEGEND ROW */}
                <div className="legend-row">
                  <div className="legend-item">
                    <div className="legend-dot" style={{ background: 'var(--accent)' }}></div>
                    <span>Active — used within 12 months</span>
                  </div>
                  <div className="legend-item">
                    <div className="legend-dot" style={{ background: '#D97706' }}></div>
                    <span>Stale — not used in 12–36 months</span>
                  </div>
                  <div className="legend-item">
                    <div className="legend-dot" style={{ background: 'var(--red)' }}></div>
                    <span>At Risk — no usage in 3+ years</span>
                  </div>
                  <div className="legend-item last">
                    <span>Proficiency: Novice → Adv. Beginner → Competent → Proficient → Expert</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="section-card">
              <div className="empty-state">
                <div>
                  <div className="icon">⚠️</div>
                  <h2>Failed to load profile</h2>
                  <p>An error occurred while loading the employee profile. Please try again.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default EmployeeDirectory;
