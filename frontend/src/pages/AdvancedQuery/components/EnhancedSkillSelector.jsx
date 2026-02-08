/**
 * Enhanced Skill Selector for Capability Finder
 * 
 * Displays skill suggestions with employee availability metadata.
 * - Employee-available skills appear first (selectable)
 * - Master-only skills appear below with "No employees yet" badge (disabled)
 */
import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, X } from 'lucide-react';
import { capabilityFinderApi } from '../../../services/api/capabilityFinderApi';

const EnhancedSkillSelector = ({ value = [], onChange, placeholder = 'Type to search skills...' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Load suggestions when dropdown opens or search term changes
  useEffect(() => {
    if (isOpen) {
      loadSuggestions(searchTerm);
    }
  }, [isOpen, searchTerm]);

  const loadSuggestions = async (query) => {
    setIsLoading(true);
    try {
      const results = await capabilityFinderApi.getSkillSuggestions(query);
      setSuggestions(results);
    } catch (error) {
      console.error('Failed to load skill suggestions:', error);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectSkill = (skill) => {
    // Block selection of master-only skills
    if (!skill.is_selectable) {
      return;
    }

    // Add skill if not already selected
    if (!value.includes(skill.skill_name)) {
      onChange([...value, skill.skill_name]);
    }
    
    setSearchTerm('');
    inputRef.current?.focus();
  };

  const handleRemoveSkill = (skillName, e) => {
    e.stopPropagation();
    onChange(value.filter(s => s !== skillName));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && isOpen) {
      setIsOpen(false);
      setSearchTerm('');
      e.preventDefault();
    }
  };

  return (
    <div ref={containerRef} className="relative">
      {/* Input Field */}
      <div
        className={`
          flex flex-wrap items-center gap-2 w-full px-3 py-2 border rounded-lg
          bg-white border-gray-300 cursor-text hover:border-gray-400
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        `}
        onClick={() => {
          setIsOpen(true);
          inputRef.current?.focus();
        }}
      >
        {/* Selected skill chips */}
        {value.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {value.map((skillName) => (
              <span
                key={skillName}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-sm"
              >
                {skillName}
                <button
                  type="button"
                  onClick={(e) => handleRemoveSkill(skillName, e)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Search input */}
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={value.length === 0 ? placeholder : ''}
          className="flex-1 min-w-[120px] outline-none bg-transparent text-sm"
        />

        <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {/* Dropdown suggestions */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {isLoading ? (
            <div className="px-3 py-2 text-sm text-gray-500">Loading...</div>
          ) : suggestions.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500">No skills found</div>
          ) : (
            <ul>
              {suggestions.map((skill) => {
                const isSelected = value.includes(skill.skill_name);
                const isDisabled = !skill.is_selectable;

                return (
                  <li
                    key={skill.skill_id}
                    onClick={() => handleSelectSkill(skill)}
                    className={`
                      px-3 py-2 text-sm cursor-pointer
                      ${isSelected ? 'bg-blue-50 text-blue-700 font-medium' : ''}
                      ${isDisabled 
                        ? 'text-gray-400 cursor-not-allowed bg-gray-50' 
                        : 'hover:bg-gray-100'
                      }
                    `}
                  >
                    <div className="flex items-center justify-between">
                      <span className={isDisabled ? 'line-through' : ''}>
                        {skill.skill_name}
                      </span>
                      {isDisabled && (
                        <span className="text-xs text-gray-500 ml-2 bg-gray-200 px-1.5 py-0.5 rounded">
                          No employees yet
                        </span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default EnhancedSkillSelector;
