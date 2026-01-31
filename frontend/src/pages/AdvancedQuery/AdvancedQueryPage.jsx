import React, { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';
import QueryBuilderPanel from './components/QueryBuilderPanel';
import QueryResultsTable from './components/QueryResultsTable';
import TalentExportMenu from '../../components/TalentExportMenu';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';
import capabilityFinderApi from '../../services/api/capabilityFinderApi';
import talentExportService from '../../services/talentExportService';

const AdvancedQueryPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [queryResults, setQueryResults] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(null);  const [currentQuery, setCurrentQuery] = useState({
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
    setIsLoading(true);
    setError(null);
    
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
    <div className="p-8 bg-slate-50 min-h-screen">      <div className="max-w-screen-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Capability Finder</h1>
          <p className="text-slate-600">Build complex queries to find employees with specific skill combinations</p>
        </div>        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
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
                  isLoading={isLoading}
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
                  <EmptyState
                    icon={Search}
                    title="No results yet"
                    description="Build a query and click search to find matching employees"
                  />                ) : (
                  <QueryResultsTable
                    results={queryResults}
                    selectedIds={selectedIds}
                    onSelectionChange={handleSelectionChange}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedQueryPage;
