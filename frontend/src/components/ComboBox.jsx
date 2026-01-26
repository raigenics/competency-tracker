/**
 * Reusable ComboBox component for typeahead/autocomplete functionality.
 * Supports both single-select and multi-select modes.
 */
import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, X, Check } from 'lucide-react';

/**
 * ComboBox component with typeahead functionality.
 * 
 * @param {Object} props
 * @param {Array<string|{id: number, name: string}>} props.options - Available options
 * @param {string|Array<string>} props.value - Current selection (string for single, array for multi)
 * @param {Function} props.onChange - Callback when selection changes
 * @param {string} props.placeholder - Placeholder text
 * @param {boolean} props.multi - Enable multi-select mode
 * @param {boolean} props.disabled - Disable the input
 * @param {string} props.className - Additional CSS classes
 */
const ComboBox = ({
  options = [],
  value,
  onChange,
  placeholder = 'Select...',
  multi = false,
  disabled = false,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef(null);
  const inputRef = useRef(null);
  // Normalize options to always have {id, name} structure
  const normalizedOptions = options.map(opt => 
    typeof opt === 'string' ? { id: opt, name: opt } : opt
  );

  // Filter options based on search term
  const filteredOptions = normalizedOptions.filter(opt =>
    opt.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get selected values as array (handles both id and name comparisons)
  const selectedValues = multi 
    ? (Array.isArray(value) ? value : [])
    : (value ? [value] : []);
  // Check if an option is selected (compare by id for object options, by name for string options)
  const isOptionSelected = (opt) => {
    const compareValue = typeof options[0] === 'string' ? opt.name : opt.id;
    return selectedValues.includes(compareValue);
  };

  // Get display name for a selected value (lookup name by id for object options)
  const getDisplayName = (val) => {
    if (typeof options[0] === 'string') {
      return val;
    }
    const foundOption = normalizedOptions.find(opt => opt.id === val);
    return foundOption ? foundOption.name : val;
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
  const handleToggleOption = (opt) => {
    // For string options, use name; for object options, use id
    const optionValue = typeof options[0] === 'string' ? opt.name : opt.id;
    
    if (multi) {
      const newValue = selectedValues.includes(optionValue)
        ? selectedValues.filter(v => v !== optionValue)
        : [...selectedValues, optionValue];
      onChange(newValue);
      setSearchTerm('');
      inputRef.current?.focus();
    } else {
      onChange(optionValue);
      setIsOpen(false);
      setSearchTerm('');
    }
  };

  const handleRemoveValue = (valueToRemove, e) => {
    e.stopPropagation();
    if (multi) {
      onChange(selectedValues.filter(v => v !== valueToRemove));
    } else {
      onChange('');
    }
  };

  const getDisplayValue = () => {
    if (multi) {
      return selectedValues.length > 0 
        ? `${selectedValues.length} selected`
        : '';
    }
    return value || '';
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Input Field */}
      <div
        className={`
          flex items-center gap-2 w-full px-3 py-2 border rounded-lg
          ${disabled 
            ? 'bg-gray-100 border-gray-300 cursor-not-allowed' 
            : 'bg-white border-gray-300 cursor-text hover:border-gray-400'
          }
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        `}
        onClick={() => !disabled && setIsOpen(true)}
      >        {/* Selected chips (multi-select mode) */}
        {multi && selectedValues.length > 0 && (
          <div className="flex flex-wrap gap-1 flex-1">
            {selectedValues.map((val) => (
              <span
                key={val}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-sm"
              >
                {getDisplayName(val)}
                <button
                  type="button"
                  onClick={(e) => handleRemoveValue(val, e)}
                  className="text-blue-600 hover:text-blue-800"
                  disabled={disabled}
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
          className={`
            flex-1 outline-none bg-transparent text-sm
            ${disabled ? 'cursor-not-allowed' : ''}
            ${multi && selectedValues.length > 0 ? 'min-w-[100px]' : ''}
          `}
          placeholder={!multi && value ? getDisplayName(value) : (selectedValues.length === 0 ? placeholder : '')}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => !disabled && setIsOpen(true)}
          disabled={disabled}
        />

        {/* Dropdown icon */}
        <ChevronDown 
          className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </div>      {/* Dropdown List */}
      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredOptions.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500">
              No options found
            </div>
          ) : (
            filteredOptions.map((opt) => {
              const isSelected = isOptionSelected(opt);
              return (
                <button
                  key={opt.id}
                  type="button"
                  className={`
                    w-full px-3 py-2 text-left text-sm flex items-center justify-between
                    hover:bg-gray-50 transition-colors
                    ${isSelected ? 'bg-blue-50 text-blue-700' : 'text-gray-900'}
                  `}
                  onClick={() => handleToggleOption(opt)}
                >
                  <span>{opt.name}</span>
                  {isSelected && <Check className="h-4 w-4 text-blue-600" />}
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default ComboBox;
