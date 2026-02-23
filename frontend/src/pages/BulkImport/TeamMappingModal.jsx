import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { bulkImportApi } from '../../services/api/bulkImportApi.js';

/**
 * Modal for mapping MISSING_TEAM errors from import failures.
 * 
 * Displays a searchable list of available teams for the specific project
 * and allows mapping the failed row to an existing master team.
 * 
 * Teams are scoped by project - only shows teams belonging to the project
 * where the missing team was specified.
 */
const TeamMappingModal = ({ 
  isOpen, 
  onClose, 
  importRunId, 
  failedRow,
  failedRowIndex,
  onMapped 
}) => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mapping, setMapping] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selectedTeamId, setSelectedTeamId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [projectInfo, setProjectInfo] = useState({ name: '', id: null });
  const [_fetchAttempted, setFetchAttempted] = useState(false);  // Track if fetch was attempted
  const [missingProjectInfo, setMissingProjectInfo] = useState(false);  // Track if project_id is missing
  const [showCreateForm, setShowCreateForm] = useState(false);  // Toggle for create form
  const [newTeamName, setNewTeamName] = useState('');  // New team name input

  // Fetch teams when modal opens
  useEffect(() => {
    if (!isOpen) {
      // Reset state when modal closes
      setTeams([]);
      setSelectedTeamId(null);
      setSearchQuery('');
      setError(null);
      setProjectInfo({ name: '', id: null });
      setFetchAttempted(false);
      setMissingProjectInfo(false);
      setShowCreateForm(false);
      setNewTeamName('');
      return;
    }
    
    if (!importRunId) {
      console.error('[TeamMappingModal] Cannot fetch teams: missing importRunId');
      return;
    }

    // Get project info from failed row
    const projectId = failedRow?.project_id;
    const projectName = failedRow?.project_name || 'Unknown Project';

    if (!projectId) {
      console.error('[TeamMappingModal] Cannot fetch teams: missing project_id in failed row', failedRow);
      setMissingProjectInfo(true);
      setFetchAttempted(true);
      return;
    }
    
    setMissingProjectInfo(false);
    setProjectInfo({ name: projectName, id: projectId });
    
    const fetchTeams = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await bulkImportApi.getTeamsForMapping(importRunId, projectId);
        
        if (response.teams?.length > 0) {
          setTeams(response.teams);
          // Update project name from response if available
          if (response.project_name) {
            setProjectInfo(prev => ({ ...prev, name: response.project_name }));
          }
        } else {
          setTeams([]);
          console.warn('[TeamMappingModal] No teams found for project', projectId);
        }
      } catch (err) {
        console.error('[TeamMappingModal] Failed to fetch teams:', err);
        setError('Unable to load teams. Please try again.');
      } finally {
        setLoading(false);
        setFetchAttempted(true);
      }
    };
    
    fetchTeams();
  }, [isOpen, importRunId, failedRow]);

  // Handle team mapping
  const handleMap = useCallback(async () => {
    if (!selectedTeamId || failedRowIndex === undefined || failedRowIndex === null) {
      console.error('[TeamMappingModal] Cannot map: missing selectedTeamId or failedRowIndex');
      setError('Cannot map team: missing required data');
      return;
    }

    setMapping(true);
    setError(null);

    try {
      const result = await bulkImportApi.mapTeam(
        importRunId,
        failedRowIndex,
        selectedTeamId
      );
      
      onMapped?.(result);
      onClose();
    } catch (err) {
      console.error('Failed to map team:', err);
      
      if (err.response?.status === 409) {
        // Alias conflict - already mapped to different team
        setError(err.response.data?.detail || 'This team name is already mapped to a different team in this project. Contact admin to resolve this conflict.');
      } else if (err.response?.status === 400) {
        setError(err.response.data?.detail || 'This row has already been mapped, is not a MISSING_TEAM error, or the team does not belong to the expected project.');
      } else if (err.response?.status === 404) {
        setError(err.response.data?.detail || 'Team, project, or import job not found.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to map team');
      }
    } finally {
      setMapping(false);
    }
  }, [selectedTeamId, failedRowIndex, importRunId, onMapped, onClose]);

  // Handle create new team
  const handleCreateTeam = useCallback(async () => {
    if (!newTeamName.trim() || failedRowIndex === undefined || failedRowIndex === null) {
      console.error('[TeamMappingModal] Cannot create team: missing newTeamName or failedRowIndex');
      setError('Cannot create team: missing required data');
      return;
    }

    setCreating(true);
    setError(null);

    try {
      const result = await bulkImportApi.createTeamFromImport(
        importRunId,
        failedRowIndex,
        newTeamName.trim()
      );
      
      // Transform result to match onMapped expectations
      const mappedResult = {
        ...result,
        mapped_team_id: result.created_team_id,
        mapped_team_name: result.created_team_name,
      };
      
      onMapped?.(mappedResult);
      onClose();
    } catch (err) {
      console.error('Failed to create team:', err);
      
      if (err.response?.status === 400) {
        setError(err.response.data?.detail || 'Invalid team name or team already exists.');
      } else if (err.response?.status === 404) {
        setError(err.response.data?.detail || 'Import job not found.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to create team');
      }
    } finally {
      setCreating(false);
    }
  }, [newTeamName, failedRowIndex, importRunId, onMapped, onClose]);

  // Filter teams by search query (client-side) - memoized for performance
  const filteredTeams = useMemo(() => {
    return teams.filter(team => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase().trim();
      if (!query) return true;
      return team.team_name.toLowerCase().includes(query);
    });
  }, [teams, searchQuery]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-xl shadow-2xl w-[600px] max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#e2e8f0]">
          <h2 className="text-lg font-semibold text-[#1e293b]">
            Map Missing Team
          </h2>
          <p className="text-sm text-[#64748b] mt-1">
            Map "<span className="font-medium text-[#334155]">{failedRow?.team_name || 'Unknown Team'}</span>" to an existing team
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Project info (read-only) */}
          <div className="mb-4 p-3 bg-[#f1f5f9] rounded-lg">
            <span className="text-xs text-[#64748b]">Project: </span>
            <span className="text-sm text-[#334155] font-medium">
              {projectInfo.name}
            </span>
          </div>

          {/* Employee info */}
          {failedRow?.employee_name && (
            <div className="mb-4 p-3 bg-[#f8fafc] rounded-lg">
              <span className="text-xs text-[#64748b]">Employee: </span>
              <span className="text-sm text-[#334155] font-medium">
                {failedRow.employee_name || failedRow.full_name}
                {failedRow.zid && (
                  <span className="text-[#64748b] ml-1">({failedRow.zid})</span>
                )}
              </span>
            </div>
          )}

          {/* Search filter - only show when project info available */}
          {!missingProjectInfo && (
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search teams..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-[#e2e8f0] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#10b981]/20 focus:border-[#10b981]"
                disabled={loading}
              />
            </div>
          )}

          {/* Missing project info error - show when project_id is missing */}
          {missingProjectInfo && (
            <div className="mb-4 p-3 bg-[#fef2f2] border border-[#fecaca] rounded-lg text-sm text-[#dc2626]">
              Cannot load teams: missing project information. Please contact support.
            </div>
          )}

          {/* Fetch error message - show when fetch failed */}
          {error && !missingProjectInfo && (
            <div className="mb-4 p-3 bg-[#fef2f2] border border-[#fecaca] rounded-lg text-sm text-[#dc2626]">
              {error}
            </div>
          )}

          {/* Admin contact info - no team creation allowed (only show when project info available) */}
          {!missingProjectInfo && !showCreateForm && (
            <div className="mb-4 p-3 bg-[#fffbeb] border border-[#fef3c7] rounded-lg text-sm text-[#92400e] flex items-center justify-between">
              <span>Can&apos;t find the right team?</span>
              <button
                onClick={() => {
                  setShowCreateForm(true);
                  setSelectedTeamId(null);
                }}
                className="ml-2 text-[#059669] font-medium hover:underline"
              >
                Create New Team
              </button>
            </div>
          )}

          {/* Create new team form */}
          {!missingProjectInfo && showCreateForm && (
            <div className="mb-4 p-4 bg-[#f0fdf4] border border-[#bbf7d0] rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-[#166534]">Create New Team</h3>
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewTeamName('');
                    setError(null);
                  }}
                  className="text-xs text-[#64748b] hover:text-[#1e293b]"
                >
                  Cancel
                </button>
              </div>
              <p className="text-xs text-[#64748b] mb-2">
                Create a new team under <span className="font-medium">{projectInfo.name}</span>
              </p>
              <input
                type="text"
                placeholder="Enter team name..."
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                className="w-full px-3 py-2 border border-[#d1d5db] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#10b981]/20 focus:border-[#10b981]"
                disabled={creating}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && newTeamName.trim()) {
                    handleCreateTeam();
                  }
                }}
              />
            </div>
          )}

          {/* Teams list - only render when project info is available */}
          {!missingProjectInfo && (
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {loading ? (
                <div className="text-center py-8 text-[#64748b]">
                  Loading teams...
                </div>
              ) : error ? (
                // Don't show empty list message when there's a fetch error
                null
              ) : filteredTeams.length === 0 ? (
                <div className="text-center py-8 text-[#64748b]">
                  {searchQuery ? 'No teams match your search.' : 'No teams available for this project.'}
                </div>
              ) : (
                filteredTeams.map((team) => (
                  <label
                    key={team.team_id}
                    className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedTeamId === team.team_id
                      ? 'border-[#10b981] bg-[#10b981]/5'
                      : 'border-[#e2e8f0] hover:border-[#cbd5e1] hover:bg-[#f8fafc]'
                  }`}
                >
                  <input
                    type="radio"
                    name="team-selection"
                    value={team.team_id}
                    checked={selectedTeamId === team.team_id}
                    onChange={() => setSelectedTeamId(team.team_id)}
                    className="w-4 h-4 text-[#10b981] focus:ring-[#10b981]"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-[#1e293b]">
                      {team.team_name}
                    </div>
                  </div>
                </label>
              ))
            )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#e2e8f0] flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={mapping || creating}
            className="px-4 py-2 text-sm font-medium text-[#475569] bg-white border border-[#e2e8f0] rounded-lg hover:bg-[#f8fafc] disabled:opacity-50"
          >
            Cancel
          </button>
          {showCreateForm ? (
            <button
              onClick={handleCreateTeam}
              disabled={!newTeamName.trim() || creating}
              className="px-4 py-2 text-sm font-medium text-white bg-[#10b981] rounded-lg hover:bg-[#059669] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {creating ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Creating...
                </>
              ) : (
                'Create Team'
              )}
            </button>
          ) : (
            <button
              onClick={handleMap}
              disabled={!selectedTeamId || mapping}
              className="px-4 py-2 text-sm font-medium text-white bg-[#10b981] rounded-lg hover:bg-[#059669] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {mapping ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Mapping...
                </>
              ) : (
                'Map to Selected Team'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamMappingModal;
