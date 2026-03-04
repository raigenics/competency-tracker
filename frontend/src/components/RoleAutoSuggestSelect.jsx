/**
 * RoleAutoSuggestSelect Component
 * 
 * Dropdown with typeable filter for role/designation selection.
 * Filters roles client-side as user types.
 * Only allows selection from the roles list.
 * 
 * Uses existing CSS classes from AddEmployeeDrawer styles.
 */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';

/**
 * @param {Object} props
 * @param {number|null} props.value - Selected role_id
 * @param {Function} props.onChange - Callback when role is selected: (roleId, roleName) => void
 * @param {Array} props.roles - List of roles with role_id and role_name
 * @param {string} props.error - Error message to display
 * @param {boolean} props.loading - Whether roles are loading
 * @param {boolean} props.disabled - Whether the field is disabled
 */
export function RoleAutoSuggestSelect({ 
  value, 
  onChange, 
  roles = [], 
  error: _error,
  loading = false,
  disabled = false
}) {
  // Input text (for filtering)
  const [inputValue, setInputValue] = useState('');
  // Track previous value prop for sync in render
  const [prevValue, setPrevValue] = useState(value);
  // Whether dropdown is open
  const [isOpen, setIsOpen] = useState(false);
  // Highlighted index for keyboard nav
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  // Sync inputValue when value prop changes (React recommended pattern)
  if (value !== prevValue) {
    setPrevValue(value);
    if (value && roles.length > 0) {
      const selectedRole = roles.find(r => r.role_id === value);
      if (selectedRole && inputValue !== selectedRole.role_name) {
        setInputValue(selectedRole.role_name);
      }
    } else if (!value && inputValue !== '') {
      setInputValue('');
    }
  }

  // Derive filtered roles from inputValue and roles (no useState needed)
  const filteredRoles = useMemo(() => {
    if (!inputValue.trim()) {
      return roles;
    }
    const searchTerm = inputValue.toLowerCase();
    return roles.filter(r => r.role_name.toLowerCase().includes(searchTerm));
  }, [inputValue, roles]);

  // Track previous filtered roles length for render-time sync
  const [prevFilteredRolesLength, setPrevFilteredRolesLength] = useState(filteredRoles.length);
  if (filteredRoles.length !== prevFilteredRolesLength) {
    setPrevFilteredRolesLength(filteredRoles.length);
    if (highlightedIndex !== -1) {
      setHighlightedIndex(-1);
    }
  }
  
  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
        // Reset input to selected value if user clicked away without selecting
        if (value && roles.length > 0) {
          const selectedRole = roles.find(r => r.role_id === value);
          if (selectedRole) {
            setInputValue(selectedRole.role_name);
          }
        }
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [value, roles]);

  // Handle input change
  const handleInputChange = useCallback((e) => {
    const val = e.target.value;
    setInputValue(val);
    setIsOpen(true);
  }, []);

  // Handle input focus
  const handleFocus = useCallback(() => {
    setIsOpen(true);
  }, []);

  // Handle selecting a role
  const handleSelect = useCallback((role) => {
    console.log('[RoleAutoSuggestSelect] Selected role:', role);
    setInputValue(role.role_name);
    setIsOpen(false);
    onChange(role.role_id, role.role_name);
  }, [onChange]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < filteredRoles.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : 0);
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredRoles[highlightedIndex]) {
          handleSelect(filteredRoles[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  }, [isOpen, highlightedIndex, filteredRoles, handleSelect]);

  // Scroll highlighted item into view
  useEffect(() => {
    if (listRef.current && highlightedIndex >= 0) {
      const items = listRef.current.querySelectorAll('.role-option');
      if (items[highlightedIndex]) {
        items[highlightedIndex].scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex]);

  const showDropdown = isOpen && !loading && filteredRoles.length > 0;
  const showNoResults = isOpen && !loading && inputValue && filteredRoles.length === 0;

  return (
    <div 
      ref={containerRef} 
      className="role-autosuggest-container"
      style={{ position: 'relative' }}
    >
      <div style={{ position: 'relative' }}>
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onKeyDown={handleKeyDown}
          placeholder={loading ? 'Loading roles...' : 'Select or type to search...'}
          disabled={disabled || loading}
          data-testid="role-input"
          autoComplete="off"
          style={{ paddingRight: '30px' }}
        />
        {/* Dropdown arrow indicator */}
        <span
          style={{
            position: 'absolute',
            right: '10px',
            top: '50%',
            transform: `translateY(-50%) rotate(${isOpen ? '180deg' : '0deg'})`,
            transition: 'transform 0.2s',
            pointerEvents: 'none',
            color: '#64748b',
            fontSize: '12px'
          }}
        >
          ▼
        </span>
      </div>
      
      {/* Dropdown list */}
      {showDropdown && (
        <ul
          ref={listRef}
          className="role-dropdown"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            maxHeight: '200px',
            overflow: 'auto',
            background: 'white',
            border: '1px solid #cbd5e1',
            borderTop: 'none',
            borderRadius: '0 0 6px 6px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            zIndex: 1000,
            listStyle: 'none',
            margin: 0,
            padding: 0
          }}
          data-testid="role-dropdown"
        >
          {filteredRoles.map((role, index) => (
            <li
              key={role.role_id}
              className={`role-option ${highlightedIndex === index ? 'highlighted' : ''}`}
              onClick={() => handleSelect(role)}
              onMouseEnter={() => setHighlightedIndex(index)}
              style={{
                padding: '10px 12px',
                cursor: 'pointer',
                fontSize: '14px',
                background: highlightedIndex === index ? '#e2e8f0' : 'white',
                transition: 'background 0.15s'
              }}
              data-testid={`role-option-${role.role_id}`}
            >
              {role.role_name}
            </li>
          ))}
        </ul>
      )}
      
      {/* No results message */}
      {showNoResults && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            padding: '10px 12px',
            background: 'white',
            border: '1px solid #cbd5e1',
            borderTop: 'none',
            borderRadius: '0 0 6px 6px',
            fontSize: '13px',
            color: '#64748b',
            zIndex: 1000
          }}
          data-testid="role-no-results"
        >
          No matching roles found
        </div>
      )}
    </div>
  );
}

export default RoleAutoSuggestSelect;
