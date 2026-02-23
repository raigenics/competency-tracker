import React, { useState, useEffect } from 'react';
import ComboBox from '../../../components/ComboBox';
import EnhancedSkillSelector from './EnhancedSkillSelector';
import { capabilityFinderApi } from '../../../services/api/capabilityFinderApi';
import { dropdownApi } from '../../../services/api/dropdownApi';

const QueryBuilderPanel = ({ query, onQueryChange, onSearch, onClearFilters, isLoading, hasSearched: _hasSearched, matchMode, onMatchModeChange }) => {
  const [availableRoles, setAvailableRoles] = useState([]);
  const [subSegments, setSubSegments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load initial dropdown data
  useEffect(() => {
    const loadDropdownData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch roles and sub-segments (skills handled by EnhancedSkillSelector)
        const [roles, subSegs] = await Promise.all([
          capabilityFinderApi.getAllRoles(),
          dropdownApi.getSubSegments()
        ]);
        
        setAvailableRoles(roles);
        setSubSegments([{ id: 'all', name: 'All Sub-Segments' }, ...subSegs]);
      } catch (err) {
        console.error('Failed to load dropdown data:', err);
        setError('Failed to load filter options. Please refresh the page.');
      } finally {
        setLoading(false);
      }
    };

    loadDropdownData();
  }, []);

  // Load teams when sub-segment changes
  useEffect(() => {
    const loadTeams = async () => {
      if (!query.subSegment || query.subSegment === 'all') {
        // Load all teams across all sub-segments
        try {
          const allTeams = [];
          for (const subSeg of subSegments) {
            if (subSeg.id !== 'all') {
              const projects = await dropdownApi.getProjects(subSeg.id);
              for (const project of projects) {
                const projectTeams = await dropdownApi.getTeams(project.id);
                allTeams.push(...projectTeams);
              }
            }
          }
          // Remove duplicates
          const uniqueTeams = Array.from(
            new Map(allTeams.map(t => [t.id, t])).values()
          );
          setTeams(uniqueTeams);
        } catch (err) {
          console.error('Failed to load teams:', err);
          setTeams([]);
        }
      } else {
        // Load teams for specific sub-segment
        try {
          const projects = await dropdownApi.getProjects(query.subSegment);
          const allTeams = [];
          for (const project of projects) {
            const projectTeams = await dropdownApi.getTeams(project.id);
            allTeams.push(...projectTeams);
          }
          setTeams(allTeams);
        } catch (err) {
          console.error('Failed to load teams:', err);
          setTeams([]);
        }
      }
    };

    if (subSegments.length > 0) {
      loadTeams();
    }
  }, [query.subSegment, subSegments]);
  const handleAddSkill = (skills) => {
    onQueryChange({
      ...query,
      skills: skills
    });
  };

  const handleSubSegmentChange = (subSegmentId) => {
    onQueryChange({
      ...query,
      subSegment: subSegmentId,
      team: '' // Reset team when sub-segment changes
    });
  };

  const handleTeamChange = (teamName) => {
    onQueryChange({
      ...query,
      team: teamName
    });
  };

  const handleRoleChange = (roleName) => {
    onQueryChange({
      ...query,
      role: roleName
    });
  };
  const handleProficiencyChange = (type, value) => {
    onQueryChange({
      ...query,
      proficiency: {
        ...query.proficiency,
        [type]: parseInt(value)
      }
    });
  };

  const handleExperienceChange = (type, value) => {
    onQueryChange({
      ...query,
      experience: {
        ...query.experience,
        [type]: parseInt(value)
      }
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-sm text-gray-500">Loading filters...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div>
      {/* Skills to Match */}
      <div className="cf-field">
        <label className="cf-label">Skills to Match</label>
        <EnhancedSkillSelector
          value={query.skills || []}
          onChange={handleAddSkill}
          placeholder="Type to search skills…"
        />
        <div className="cf-help">Multi-select skills. Choose match mode below.</div>
      </div>

      {/* Match Mode */}
      <div className="cf-field">
        <label className="cf-label">Match Mode</label>
        <div className="cf-segmented" role="tablist" aria-label="Match mode">
          <button
            type="button"
            onClick={() => onMatchModeChange('all')}
            className={matchMode === 'all' ? 'active' : ''}
          >
            All skills
          </button>
          <button
            type="button"
            onClick={() => onMatchModeChange('any')}
            className={matchMode === 'any' ? 'active' : ''}
          >
            Any skill
          </button>
        </div>
      </div>

      {/* Sub-Segment */}
      <div className="cf-field">
        <label className="cf-label">Sub-Segment (optional)</label>
        <ComboBox
          options={subSegments}
          value={query.subSegment || 'all'}
          onChange={handleSubSegmentChange}
          placeholder="All Sub-Segments"
          multi={false}
        />
      </div>

      {/* Team */}
      <div className="cf-field">
        <label className="cf-label">Team (optional)</label>
        <ComboBox
          options={teams}
          value={query.team || ''}
          onChange={handleTeamChange}
          placeholder={
            query.subSegment === 'all' 
              ? "Select a sub-segment to filter teams" 
              : teams.length === 0 
                ? "No teams available" 
                : "Select team..."
          }
          multi={false}
          clearable={true}
          disabled={query.subSegment === 'all' || teams.length === 0}
        />
      </div>

      {/* Role */}
      <div className="cf-field">
        <label className="cf-label">Role (optional)</label>
        <ComboBox
          options={availableRoles}
          value={query.role || ''}
          onChange={handleRoleChange}
          placeholder="Any role"
          multi={false}
          clearable={true}
        />
      </div>

      {/* Proficiency & Experience Row (side-by-side) */}
      <div className="cf-row cf-field">
        <div>
          <label className="cf-label">Minimum Proficiency</label>
          <select
            value={query.proficiency.min}
            onChange={(e) => handleProficiencyChange('min', e.target.value)}
            className="cf-select"
          >
            <option value="0">Any (0)</option>
            <option value="1">1+</option>
            <option value="2">2+</option>
            <option value="3">3+</option>
            <option value="4">4+</option>
            <option value="5">5 (Expert)</option>
          </select>
        </div>
        <div>
          <label className="cf-label">Minimum Experience</label>
          <select
            value={query.experience.min}
            onChange={(e) => handleExperienceChange('min', e.target.value)}
            className="cf-select"
          >
            <option value="0">Any (0+ years)</option>
            <option value="3">3+ years</option>
            <option value="5">5+ years</option>
            <option value="8">8+ years</option>
          </select>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="cf-actions">
        <button
          type="button"
          onClick={onSearch}
          disabled={isLoading || !query.skills || query.skills.length === 0}
          className="cf-btn primary"
        >
          {isLoading ? 'Searching...' : '🔍 Search'}
        </button>
        <button
          type="button"
          onClick={onClearFilters}
          className="cf-btn link"
        >
          Reset
        </button>
      </div>

      {/* Tip text */}
      <div className="cf-help" style={{ marginTop: '10px' }}>
        Tip: If results look too narrow, reduce proficiency/experience or switch to "Any skill".
      </div>
    </div>
  );
};

export default QueryBuilderPanel;
