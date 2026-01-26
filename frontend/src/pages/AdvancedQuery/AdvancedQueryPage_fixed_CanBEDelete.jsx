import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, Save, Clock } from 'lucide-react';
import QueryBuilderPanel from './components/QueryBuilderPanel';
import QueryResultsTable from './components/QueryResultsTable';
import SkillDistributionPanel from './components/SkillDistributionPanel';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';
import { mockRecentQueries } from '../../data/mockRecentQueries';

const AdvancedQueryPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [queryResults, setQueryResults] = useState([]);
  const [currentQuery, setCurrentQuery] = useState({
    skills: [],
    teams: [],
    roles: [],
    proficiency: { min: 0, max: 5 },
    experience: { min: 0, max: 20 }
  });
  const [recentQueries, setRecentQueries] = useState([]);
  const [showQueryBuilder, setShowQueryBuilder] = useState(true);

  useEffect(() => {
    // Load recent queries
    setRecentQueries(mockRecentQueries);
  }, []);

  const handleSearch = async () => {
    setIsLoading(true);
    // TODO: Replace with actual API call
    setTimeout(() => {
      // Mock search results based on current query
      const mockResults = generateMockResults(currentQuery);
      setQueryResults(mockResults);
      setIsLoading(false);
    }, 1000);
  };

  const generateMockResults = (query) => {
    // Mock implementation - replace with actual API call
    return [
      {
        id: 1,
        name: "John Doe",
        role: "Senior Developer",
        team: "Frontend Team",
        skills: [
          { name: "React", proficiency: 4 },
          { name: "JavaScript", proficiency: 5 },
          { name: "TypeScript", proficiency: 3 }
        ],
        matchScore: 85
      },
      {
        id: 2,
        name: "Jane Smith",
        role: "DevOps Engineer",
        team: "Platform Team",
        skills: [
          { name: "AWS", proficiency: 4 },
          { name: "Docker", proficiency: 5 },
          { name: "Kubernetes", proficiency: 3 }
        ],
        matchScore: 92
      }
    ];
  };

  const handleSaveQuery = () => {
    const queryName = prompt("Enter a name for this query:");
    if (queryName) {
      const newQuery = {
        id: Date.now(),
        name: queryName,
        query: currentQuery,
        results: queryResults.length,
        lastRun: new Date().toISOString(),
        createdAt: new Date().toISOString()
      };
      setRecentQueries([newQuery, ...recentQueries.slice(0, 4)]);
    }
  };

  const handleLoadQuery = (savedQuery) => {
    setCurrentQuery(savedQuery.query);
    setQueryResults([]);
  };

  const handleExportResults = () => {
    // TODO: Implement CSV export
    console.log("Exporting results:", queryResults);
  };

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-screen-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Advanced Query</h1>
          <p className="text-slate-600">Build complex queries to find employees with specific skill combinations</p>
        </div>

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
                  isLoading={isLoading}
                />
              )}
            </div>

            {/* Recent Queries */}
            <div className="bg-white rounded-lg border border-slate-200 p-6 mt-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Recent Queries
              </h3>
              <div className="space-y-2">
                {recentQueries.map((query) => (
                  <div
                    key={query.id}
                    className="p-3 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer"
                    onClick={() => handleLoadQuery(query)}
                  >
                    <div className="font-medium text-slate-900">{query.name}</div>
                    <div className="text-sm text-slate-600">
                      {query.results} results • {new Date(query.lastRun).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-8">
            <div className="bg-white rounded-lg border border-slate-200">
              <div className="border-b border-slate-200 p-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-slate-900">
                    Query Results ({queryResults.length})
                  </h2>
                  {queryResults.length > 0 && (
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveQuery}
                        className="flex items-center gap-2 px-4 py-2 text-slate-600 hover:text-slate-800 border border-slate-300 rounded-lg hover:bg-slate-50"
                      >
                        <Save className="h-4 w-4" />
                        Save Query
                      </button>
                      <button
                        onClick={handleExportResults}
                        className="flex items-center gap-2 px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                      >
                        <Download className="h-4 w-4" />
                        Export
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-6">
                {isLoading ? (
                  <LoadingState message="Searching employees..." />
                ) : queryResults.length === 0 ? (
                  <EmptyState
                    icon={Search}
                    title="No results yet"
                    description="Build a query and click search to find matching employees"
                  />
                ) : (
                  <QueryResultsTable results={queryResults} />
                )}
              </div>
            </div>

            {/* Skill Distribution Panel */}
            {queryResults.length > 0 && (
              <div className="mt-6">
                <SkillDistributionPanel results={queryResults} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedQueryPage;
