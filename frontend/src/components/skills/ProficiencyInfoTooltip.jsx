/**
 * ProficiencyInfoTooltip Component
 * 
 * SRP: Renders an info icon (ⓘ) with a tooltip that explains proficiency levels.
 * Accessible: keyboard focusable, opens on hover/focus/click, closes on ESC/outside click.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';

/**
 * @param {Object} props
 * @param {Array} props.levels - Array of { level_name, level_description }
 */
export function ProficiencyInfoTooltip({ levels = [] }) {
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef(null);
  const buttonRef = useRef(null);

  // Close on ESC key
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape' && isOpen) {
      setIsOpen(false);
      buttonRef.current?.focus();
    }
  }, [isOpen]);

  // Close on click outside
  const handleClickOutside = useCallback((e) => {
    if (
      tooltipRef.current &&
      !tooltipRef.current.contains(e.target) &&
      buttonRef.current &&
      !buttonRef.current.contains(e.target)
    ) {
      setIsOpen(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, handleKeyDown, handleClickOutside]);

  // If no levels, don't render
  if (!levels || levels.length === 0) {
    return null;
  }

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const handleMouseEnter = () => {
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    setIsOpen(false);
  };

  const handleFocus = () => {
    setIsOpen(true);
  };

  return (
    <span
      className="proficiency-info-wrapper"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      data-testid="proficiency-info-wrapper"
    >
      <button
        ref={buttonRef}
        type="button"
        className="proficiency-info-icon"
        onClick={handleToggle}
        onFocus={handleFocus}
        aria-label="Proficiency level definitions"
        aria-expanded={isOpen}
        aria-haspopup="true"
        data-testid="proficiency-info-icon"
      >
        ⓘ
      </button>
      {isOpen && (
        <div
          ref={tooltipRef}
          className="proficiency-info-tooltip"
          role="tooltip"
          data-testid="proficiency-info-tooltip"
        >
          <ul className="proficiency-info-list">
            {levels.map((level) => (
              <li key={level.level_name} className="proficiency-info-item">
                <strong>{level.level_name}</strong> — {level.level_description}
              </li>
            ))}
          </ul>
        </div>
      )}
    </span>
  );
}

export default ProficiencyInfoTooltip;
