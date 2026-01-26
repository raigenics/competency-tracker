import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import ComboBox from '../../../components/ComboBox';
import { capabilityFinderApi } from '../../../services/api/capabilityFinderApi';
import { dropdownApi } from '../../../services/api/dropdownApi';

const QueryBuilderPanel = ({ query, onQueryChange, onSearch, isLoading }) => {
  const [availableSkills, setAvailableSkills] = useState([]);
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
        // Fetch all dropdown data in parallel
        const [skills, roles, subSegs] = await Promise.all([
          capabilityFinderApi.getAllSkills(),
          capabilityFinderApi.getAllRoles(),
          dropdownApi.getSubSegments()
        ]);
        
        setAvailableSkills(skills);
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
    <div className="space-y-6">
      {/* Required Skills */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Required Skills
        </label>
        <ComboBox
          options={availableSkills}
          value={query.skills || []}
          onChange={handleAddSkill}
          placeholder="Type to search skills..."
          multi={true}
        />
      </div>

      {/* Sub-Segment */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sub-Segment
        </label>
        <ComboBox
          options={subSegments}
          value={query.subSegment || 'all'}
          onChange={handleSubSegmentChange}
          placeholder="Select sub-segment..."
          multi={false}
        />
      </div>

      {/* Teams */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Team
        </label>
        <ComboBox
          options={teams}
          value={query.team || ''}
          onChange={handleTeamChange}
          placeholder={teams.length === 0 ? "No teams available" : "Select team..."}
          multi={false}
          disabled={teams.length === 0}
        />
      </div>

      {/* Roles */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Role
        </label>
        <ComboBox
          options={availableRoles}
          value={query.role || ''}
          onChange={handleRoleChange}
          placeholder="Select role..."
          multi={false}
        />
      </div>

      {/* Proficiency Range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Proficiency Level
        </label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min="0"
            max="5"
            value={query.proficiency.min}
            onChange={(e) => handleProficiencyChange('min', e.target.value)}
            className="flex-1"
          />
          <span className="text-sm font-medium text-gray-700 min-w-0">
            {query.proficiency.min}/5
          </span>
        </div>
      </div>

      {/* Experience Range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Experience (years)
        </label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min="0"
            max="20"
            value={query.experience.min}
            onChange={(e) => handleExperienceChange('min', e.target.value)}
            className="flex-1"
          />
          <span className="text-sm font-medium text-gray-700 min-w-0">
            {query.experience.min}+ years
          </span>
        </div>
      </div>

      {/* Search Button */}
      <button
        onClick={onSearch}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Search className="h-5 w-5" />
        {isLoading ? 'Searching...' : 'Find Matching Talent'}
      </button>

      {/* Clear All */}
      <button
        onClick={() => onQueryChange({
          skills: [],
          subSegment: 'all',
          team: '',
          role: '',
          proficiency: { min: 0, max: 5 },
          experience: { min: 0, max: 20 }
        })}
        className="w-full px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
      >
        Clear All Filters
      </button>
    </div>
  );
};

export default QueryBuilderPanel;
