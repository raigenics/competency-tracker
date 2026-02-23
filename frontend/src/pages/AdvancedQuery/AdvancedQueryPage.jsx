import React, { useState, useEffect } from 'react';
import QueryBuilderPanel from './components/QueryBuilderPanel';
import QueryResultsTable from './components/QueryResultsTable';
import TalentExportMenu from '../../components/TalentExportMenu';
import LoadingState from '../../components/LoadingState';
import capabilityFinderApi from '../../services/api/capabilityFinderApi';
import talentExportService from '../../services/talentExportService';
import './CapabilityFinder.css';

const AdvancedQueryPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [queryResults, setQueryResults] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [matchMode, setMatchMode] = useState('all'); // 'all' or 'any'
  const [currentQuery, setCurrentQuery] = useState({
    skills: [],
    subSegment: 'all',
    team: '',
    role: '',
    proficiency: { min: 0, max: 5 },
    experience: { min: 0, max: 20 }
  });

  const [showQueryBuilder, setShowQueryBuilder] = useState(true);

  // Clear selection when new search results load
  useEffect(() => {
    setSelectedIds(new Set());
  }, [queryResults]);

  const handleSearch = async () => {
    // Prevent search if no skills selected
    if (!currentQuery.skills || currentQuery.skills.length === 0) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    
    try {
      // Build API payload
      const payload = {
        skills: currentQuery.skills,
        match_mode: matchMode.toUpperCase(), // 'ALL' or 'ANY'
        sub_segment_id: currentQuery.subSegment === 'all' ? null : parseInt(currentQuery.subSegment),
        team_id: currentQuery.team ? parseInt(currentQuery.team) : null,
        role: currentQuery.role || null,
        min_proficiency: currentQuery.proficiency.min,
        min_experience_years: currentQuery.experience.min
      };
      
      // Call API
      const response = await capabilityFinderApi.searchMatchingTalent(payload);
        // Transform API response to match table format
      const transformedResults = response.results.map(emp => ({
        id: emp.employee_id,
        name: emp.employee_name,
        role: emp.role,
        team: emp.team,
        subSegment: emp.sub_segment,
        project: emp.project || '',
        skills: emp.top_skills.map(skill => ({
          name: skill.name,
          proficiency: skill.proficiency
        }))
      }));
      
      setQueryResults(transformedResults);
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Failed to search for matching talent');
      setQueryResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectionChange = (newSelection) => {
    setSelectedIds(newSelection);
  };

  const handleClearFilters = () => {
    setCurrentQuery({
      skills: [],
      subSegment: 'all',
      team: '',
      role: '',
      proficiency: { min: 0, max: 5 },
      experience: { min: 0, max: 20 }
    });
    setHasSearched(false);
    setQueryResults([]);
    setError(null);
  };

  const handleExportAll = async () => {
    setIsExporting(true);
    setExportError(null);
    
    try {
      await talentExportService.exportAllTalent(currentQuery);
    } catch (err) {
      console.error('Export all failed:', err);
      setExportError(err.message || 'Failed to export results');
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportSelected = async () => {
    setIsExporting(true);
    setExportError(null);
    
    try {
      const selectedEmployeeIds = Array.from(selectedIds);
      await talentExportService.exportSelectedTalent(currentQuery, selectedEmployeeIds);
    } catch (err) {
      console.error('Export selected failed:', err);
      setExportError(err.message || 'Failed to export selected results');
    } finally {
      setIsExporting(false);
    }
  };
  return (
    <div className="capability-finder">
      {/* Header - matches HTML wireframe */}
      <div className="cf-header">
        <h1>Capability Finder</h1>
        <p>Select skills and optional filters to find matching employees.</p>
      </div>

      {/* Main Grid - 380px left, flex right */}
      <div className="cf-grid">
        {/* LEFT: Filters Card */}
        <section className="cf-card" aria-label="Filters">
          <h3>Find Talent By</h3>
          
          <QueryBuilderPanel
            query={currentQuery}
            onQueryChange={setCurrentQuery}
            onSearch={handleSearch}
            onClearFilters={handleClearFilters}
            isLoading={isLoading}
            hasSearched={hasSearched}
            matchMode={matchMode}
            onMatchModeChange={setMatchMode}
          />
        </section>

        {/* RIGHT: Results Card */}
        <section className="cf-card" aria-label="Results">
          <div className="cf-topbar">
            <div className="cf-count">Matching Talent ({queryResults.length})</div>
            <TalentExportMenu
              totalCount={queryResults.length}
              selectedCount={selectedIds.size}
              onExportAll={handleExportAll}
              onExportSelected={handleExportSelected}
              isExporting={isExporting}
              exportError={exportError}
              disabled={queryResults.length === 0}
            />
          </div>

          {isLoading ? (
            <LoadingState message="Searching employees..." />
          ) : error ? (
            <div className="cf-empty">
              <div className="cf-empty-title">Search failed</div>
              <div className="cf-empty-sub">{error}</div>
            </div>
          ) : queryResults.length === 0 ? (
            hasSearched ? (
              <div className="cf-empty">
                <div className="cf-empty-title">No matching employees found</div>
                <div className="cf-empty-sub">Try lowering proficiency or switching Match Mode to "Any skill".</div>
              </div>
            ) : (
              <div className="cf-empty">
                <div className="cf-empty-title">No search performed</div>
                <div className="cf-empty-sub">Select skills and click Search to view matching employees.</div>
              </div>
            )
          ) : (
            <QueryResultsTable
              results={queryResults}
              selectedIds={selectedIds}
              onSelectionChange={handleSelectionChange}
              selectedSkillsCount={currentQuery.skills?.length || 0}
            />
          )}
        </section>
      </div>
    </div>
  );
};

export default AdvancedQueryPage;
