/**
 * SkillRowEditor Component
 * 
 * SRP: Renders a single skill row with all fields.
 * Handles autocomplete for skill selection with:
 * - Two-line display (skill name + category path)
 * - Highlight matching text in suggestions
 * - Keyboard navigation (Arrow Up/Down, Enter, Escape)
 * 
 * Fields:
 * - Skill (required, autocomplete from API)
 * - Proficiency (required)
 * - Experience Years (required)
 * - Certification (optional)
 */
import React, { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Highlights matching text in a string by wrapping matches in span.highlight
 * @param {string} text - Text to search in
 * @param {string} query - Search query to highlight
 * @returns {JSX.Element[]|string} Array of text/highlighted spans or original text
 */
function highlightMatch(text, query) {
  if (!query || !text) {
    return text;
  }
  
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase().trim();
  
  if (!lowerQuery || !lowerText.includes(lowerQuery)) {
    return text;
  }
  
  const parts = [];
  let lastIndex = 0;
  let index = lowerText.indexOf(lowerQuery);
  
  while (index !== -1) {
    // Add text before the match
    if (index > lastIndex) {
      parts.push(text.slice(lastIndex, index));
    }
    
    // Add highlighted match (preserving original case)
    parts.push(
      <span key={index} className="highlight">
        {text.slice(index, index + lowerQuery.length)}
      </span>
    );
    
    lastIndex = index + lowerQuery.length;
    index = lowerText.indexOf(lowerQuery, lastIndex);
  }
  
  // Add remaining text after last match
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  
  return parts;
}

/**
 * @param {Object} props
 * @param {Object} props.skill - Skill row data
 * @param {Function} props.onChange - Callback when field changes: (skillId, field, value) => void
 * @param {Function} props.onSelectSkill - Callback when skill selected: (skillId, skillData) => void
 * @param {Function} props.onDelete - Callback to delete row: (skillId) => void
 * @param {Array} props.suggestions - Skill suggestions for autocomplete
 * @param {Function} props.onSearch - Callback when user types in skill input
 * @param {boolean} props.loading - Whether suggestions are loading
 * @param {Array} props.proficiencies - Proficiency options
 * @param {Object} props.errors - Validation errors for this row
 * @param {boolean} props.canDelete - Whether row can be deleted
 */
export function SkillRowEditor({
  skill,
  onChange,
  onSelectSkill,
  onDelete,
  suggestions = [],
  onSearch,
  loading = false,
  proficiencies = [],
  errors = {},
  canDelete = true
}) {
  // Local state for autocomplete
  const [showDropdown, setShowDropdown] = useState(false);
  const [inputValue, setInputValue] = useState(skill.skillName || '');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  // Track previous skill for render-time sync
  const [prevSkillId, setPrevSkillId] = useState(skill.skill_id);
  const [prevSkillName, setPrevSkillName] = useState(skill.skillName);
  
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Sync input value with skill.skillName when it changes externally (React recommended pattern)
  if (skill.skill_id !== prevSkillId || skill.skillName !== prevSkillName) {
    setPrevSkillId(skill.skill_id);
    setPrevSkillName(skill.skillName);
    if (skill.skill_id && skill.skillName !== inputValue) {
      setInputValue(skill.skillName);
    }
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false);
        // Reset input to selected value if user clicked away
        if (skill.skill_id && skill.skillName) {
          setInputValue(skill.skillName);
        } else {
          setInputValue('');
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [skill.skill_id, skill.skillName]);

  // Handle input change
  const handleInputChange = useCallback((e) => {
    const value = e.target.value;
    setInputValue(value);
    setShowDropdown(true);
    setHighlightedIndex(-1);
    
    // Clear the skill selection when typing (user is searching again)
    if (skill.skill_id) {
      onChange(skill.id, 'skill_id', null);
      onChange(skill.id, 'skillName', '');
    }
    
    // Trigger search
    if (onSearch) {
      onSearch(value);
    }
  }, [skill.id, skill.skill_id, onChange, onSearch]);

  // Handle input focus
  const handleInputFocus = useCallback(() => {
    setShowDropdown(true);
    if (onSearch) {
      onSearch(inputValue);
    }
  }, [inputValue, onSearch]);

  // Handle selecting a suggestion
  const handleSelectSuggestion = useCallback((suggestion) => {
    setInputValue(suggestion.skill_name);
    setShowDropdown(false);
    setHighlightedIndex(-1);
    
    if (onSelectSkill) {
      onSelectSkill(skill.id, suggestion);
    }
  }, [skill.id, onSelectSkill]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (!showDropdown || suggestions.length === 0) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setShowDropdown(true);
        if (onSearch) onSearch(inputValue);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : 0);
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
          handleSelectSuggestion(suggestions[highlightedIndex]);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setHighlightedIndex(-1);
        break;
      default:
        break;
    }
  }, [showDropdown, suggestions, highlightedIndex, inputValue, onSearch, handleSelectSuggestion]);

  // Handle field change
  const handleFieldChange = useCallback((field, value) => {
    onChange(skill.id, field, value);
  }, [skill.id, onChange]);

  return (
    <tr className="skill-row" data-testid={`skill-row-${skill.id}`}>
      {/* Skill Name with Autocomplete - wider column */}
      <td style={{ minWidth: '180px' }}>
        <div 
          className="skills-input-container" 
          ref={containerRef}
          data-testid="skill-autocomplete"
        >
          <input
            ref={inputRef}
            type="text"
            placeholder="Type to search skills..."
            value={inputValue}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onKeyDown={handleKeyDown}
            className={`skills-input${errors.skillName ? ' input-error' : ''}`}
            data-testid="skill-name-input"
            aria-label="Skill name"
          />
          {showDropdown && (
            <div 
              className={`autocomplete-dropdown ${showDropdown ? 'show' : ''}`}
              data-testid="skill-dropdown"
            >
              {loading ? (
                <div className="autocomplete-loading">Loading...</div>
              ) : suggestions.length > 0 ? (
                suggestions.map((suggestion, idx) => (
                  <div
                    key={suggestion.skill_id}
                    className={`autocomplete-item ${idx === highlightedIndex ? 'selected' : ''}`}
                    onMouseDown={() => handleSelectSuggestion(suggestion)}
                    onMouseEnter={() => setHighlightedIndex(idx)}
                    data-testid={`skill-suggestion-${suggestion.skill_id}`}
                  >
                    <div className="skill-name" data-testid="skill-suggestion-name">
                      {highlightMatch(suggestion.skill_name, inputValue)}
                    </div>
                    <div className="skill-path" data-testid="skill-category-meta">
                      <span>{suggestion.category_name}</span>
                      {suggestion.subcategory_name && (
                        <>
                          <span className="path-separator">›</span>
                          <span>{suggestion.subcategory_name}</span>
                        </>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="autocomplete-no-results" data-testid="skill-no-results">
                  No matching skills found
                </div>
              )}
            </div>
          )}
          {errors.skillName && (
            <div className="error-message" data-testid="skill-name-error">{errors.skillName}</div>
          )}
        </div>
      </td>

      {/* Proficiency / Level */}
      <td>
        <select
          value={skill.proficiency || ''}
          onChange={(e) => handleFieldChange('proficiency', e.target.value)}
          className={errors.proficiency ? 'input-error' : ''}
          data-testid="proficiency-select"
          aria-label="Proficiency level"
        >
          <option value="">Select</option>
          {proficiencies.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {errors.proficiency && (
          <div className="error-message" data-testid="proficiency-error">{errors.proficiency}</div>
        )}
      </td>

      {/* Experience (Years) */}
      <td>
        <input
          type="number"
          placeholder="Years"
          min="0"
          step="0.5"
          value={skill.yearsExperience || ''}
          onChange={(e) => handleFieldChange('yearsExperience', e.target.value)}
          className={errors.yearsExperience ? 'input-error' : ''}
          data-testid="experience-input"
          aria-label="Years of experience"
        />
        {errors.yearsExperience && (
          <div className="error-message" data-testid="experience-error">{errors.yearsExperience}</div>
        )}
      </td>

      {/* Last Used (Month + Year) - Designer specification: month-year-input structure */}
      <td>
        <div className="month-year-input" data-testid="last-used-container">
          <select
            value={skill.lastUsedMonth || ''}
            onChange={(e) => handleFieldChange('lastUsedMonth', e.target.value)}
            data-testid="last-used-month"
            aria-label="Last used month"
          >
            <option value="">Month</option>
            <option value="01">Jan</option>
            <option value="02">Feb</option>
            <option value="03">Mar</option>
            <option value="04">Apr</option>
            <option value="05">May</option>
            <option value="06">Jun</option>
            <option value="07">Jul</option>
            <option value="08">Aug</option>
            <option value="09">Sep</option>
            <option value="10">Oct</option>
            <option value="11">Nov</option>
            <option value="12">Dec</option>
          </select>
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={2}
            placeholder="YY"
            value={skill.lastUsedYear || ''}
            onChange={(e) => {
              // Allow only digits, max 2 characters (YY format)
              const val = e.target.value.replace(/\D/g, '').slice(0, 2);
              handleFieldChange('lastUsedYear', val);
            }}
            data-testid="last-used-year"
            aria-label="Last used year"
          />
        </div>
      </td>

      {/* Started From (Date) - FIX: Restored field that was accidentally removed */}
      <td>
        <input
          type="date"
          value={skill.startedFrom || ''}
          onChange={(e) => handleFieldChange('startedFrom', e.target.value)}
          data-testid="started-from-input"
          aria-label="Started learning from"
        />
      </td>

      {/* Certification (Optional) */}
      <td>
        <input
          type="text"
          placeholder="Optional"
          value={skill.certification || ''}
          onChange={(e) => handleFieldChange('certification', e.target.value)}
          data-testid="certification-input"
          aria-label="Certification"
        />
      </td>

      {/* Delete Action - aligned to extreme right, minimal width */}
      <td style={{ width: '40px', textAlign: 'right', padding: '4px 8px' }}>
        <div className="skill-row-actions" style={{ justifyContent: 'flex-end' }}>
          <button
            className="icon-btn danger"
            title="Delete skill"
            onClick={() => onDelete(skill.id)}
            disabled={!canDelete}
            data-testid="delete-skill-btn"
            aria-label="Delete skill row"
          >
            🗑️
          </button>
        </div>
      </td>
    </tr>
  );
}

export default SkillRowEditor;
