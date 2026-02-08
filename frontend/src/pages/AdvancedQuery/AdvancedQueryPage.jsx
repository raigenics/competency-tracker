import React, { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';
import QueryBuilderPanel from './components/QueryBuilderPanel';
import QueryResultsTable from './components/QueryResultsTable';
import TalentExportMenu from '../../components/TalentExportMenu';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';
import PageHeader from '../../components/PageHeader.jsx';
import capabilityFinderApi from '../../services/api/capabilityFinderApi';
import talentExportService from '../../services/talentExportService';

const AdvancedQueryPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [queryResults, setQueryResults] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);  const [currentQuery, setCurrentQuery] = useState({
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
  };  const handleSaveQuery = () => {
    const queryName = prompt("Enter a name for this query:");
    if (queryName) {
      // Query saving logic can be implemented here if needed
      console.log("Query saved:", queryName, currentQuery);
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
    <div className="min-h-screen bg-[#f8fafc]">
      <PageHeader 
        title="Capability Finder"
        subtitle="Start by selecting one or more skills. You can optionally refine by sub-segment, team, role, proficiency, or experience."
      />
      
      <div className="p-8">
        <div className="max-w-screen-2xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Query Builder Panel */}
          <div className="lg:col-span-4">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Find Talent By
                </h2>
                <button
                  onClick={() => setShowQueryBuilder(!showQueryBuilder)}
                  className="lg:hidden text-slate-500 hover:text-slate-700"
                >
                  {showQueryBuilder ? 'Hide' : 'Show'}
                </button>
              </div>
              
              {showQueryBuilder && (
                <QueryBuilderPanel
                  query={currentQuery}
                  onQueryChange={setCurrentQuery}
                  onSearch={handleSearch}
                  onClearFilters={handleClearFilters}
                  isLoading={isLoading}
                  hasSearched={hasSearched}
                />
              )}
            </div>
          </div>          {/* Results Panel */}
          <div className="lg:col-span-8">
            <div className="bg-white rounded-lg border border-slate-200">
              <div className="border-b border-slate-200 p-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-slate-900">
                    Matching Talent ({queryResults.length})
                  </h2>
                  {queryResults.length > 0 && (
                    <TalentExportMenu
                      totalCount={queryResults.length}
                      selectedCount={selectedIds.size}
                      onExportAll={handleExportAll}
                      onExportSelected={handleExportSelected}
                      isExporting={isExporting}
                      exportError={exportError}
                    />
                  )}
                </div>
              </div>              <div className="p-6">
                {isLoading ? (
                  <LoadingState message="Searching employees..." />
                ) : error ? (
                  <EmptyState
                    icon={Search}
                    title="Search failed"
                    description={error}
                  />
                ) : queryResults.length === 0 ? (
                  hasSearched ? (
                    <EmptyState
                      icon={Search}
                      title="❌ No matching talent found"
                      description="Try adjusting skills, proficiency, or experience filters."
                    />
                  ) : currentQuery.skills.length > 0 ? (
                    <EmptyState
                      icon={Search}
                      title="🔍 Ready to search"
                      description='Click "Find Matching Talent" to see matching employees.'
                    />
                  ) : (
                    <EmptyState
                      icon={Search}
                      title="🔍 No results yet"
                      description='Select skills and click "Find Matching Talent" to discover employees.'
                    />
                  )
                ) : (
                  <QueryResultsTable
                    results={queryResults}
                    selectedIds={selectedIds}
                    onSelectionChange={handleSelectionChange}
                  />
                )}
              </div>
            </div>
          </div>        </div>
      </div>
    </div>
    </div>
  );
};

export default AdvancedQueryPage;
