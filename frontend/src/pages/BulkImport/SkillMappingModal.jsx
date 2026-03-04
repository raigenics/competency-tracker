import React, { useState, useEffect, useCallback } from 'react';
import { bulkImportApi } from '../../services/api/bulkImportApi.js';

/**
 * Modal for resolving unmatched skills from import failures.
 * 
 * Displays skill suggestions and allows mapping raw skill text to existing master skills.
 */
const SkillMappingModal = ({ 
  isOpen, 
  onClose, 
  importRunId, 
  unresolvedSkill,
  onResolved 
}) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resolving, setResolving] = useState(false);
  const [selectedSkillId, setSelectedSkillId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [resolvedRawSkillId, setResolvedRawSkillId] = useState(null);

  // Fetch suggestions when modal opens
  useEffect(() => {
    // Reset state when modal closes
    if (!isOpen) {
      setSuggestions([]);
      setSelectedSkillId(null);
      setSearchQuery('');
      setError(null);
      setResolvedRawSkillId(null);
      return;
    }
    
    // If suggestions are already provided, use them
    if (unresolvedSkill?.suggestions?.length > 0) {
      setSuggestions(unresolvedSkill.suggestions);
      setSelectedSkillId(unresolvedSkill.suggestions[0]?.skill_id || null);
      setResolvedRawSkillId(unresolvedSkill.raw_skill_id || null);
      return;
    }
    
    // Otherwise, fetch suggestions from API
    if (!importRunId || !unresolvedSkill) {
      console.error('[SkillMappingModal] Cannot fetch suggestions: missing importRunId or unresolvedSkill');
      return;
    }
    
    const fetchSuggestions = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // MUST have raw_skill_id to use optimized single-skill endpoint
        if (!unresolvedSkill.raw_skill_id) {
          console.error('[SkillMappingModal] Missing raw_skill_id - cannot fetch suggestions');
          setError('Cannot load suggestions (missing skill ID). Please refresh the page and try again.');
          setLoading(false);
          return;
        }
        
        const response = await bulkImportApi.getSingleSkillSuggestions(
          importRunId,
          unresolvedSkill.raw_skill_id,
          { maxSuggestions: 10, includeEmbeddings: true }
        );
        
        setResolvedRawSkillId(response.raw_skill_id);
        
        if (response.suggestions?.length > 0) {
          setSuggestions(response.suggestions);
          setSelectedSkillId(response.suggestions[0]?.skill_id || null);
        } else {
          setSuggestions([]);
          console.warn('[SkillMappingModal] No suggestions found for skill:', unresolvedSkill.raw_text);
        }
      } catch (err) {
        console.error('[SkillMappingModal] Failed to fetch suggestions:', err);
        setError('Failed to load skill suggestions. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSuggestions();
  }, [isOpen, unresolvedSkill, importRunId]);

  // Handle skill resolution - use resolvedRawSkillId from API if original was null
  const handleResolve = useCallback(async () => {
    const rawSkillId = unresolvedSkill?.raw_skill_id || resolvedRawSkillId;
    if (!selectedSkillId || !rawSkillId) {
      console.error('[SkillMappingModal] Cannot resolve: missing selectedSkillId or rawSkillId');
      setError('Cannot resolve skill: missing required data');
      return;
    }

    setResolving(true);
    setError(null);

    try {
      const result = await bulkImportApi.resolveSkill(
        importRunId,
        rawSkillId,
        selectedSkillId
      );
      
      onResolved?.(result);
      onClose();
    } catch (err) {
      console.error('Failed to resolve skill:', err);
      
      // Handle conflict error (alias exists for different skill)
      if (err.response?.status === 409) {
        const detail = err.response.data?.detail;
        setError(
          `Cannot map: "${detail?.alias_text || unresolvedSkill.raw_text}" is already an alias for "${detail?.existing_skill_name || 'another skill'}".`
        );
      } else if (err.response?.status === 400) {
        setError(err.response.data?.detail || 'This skill has already been resolved.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to resolve skill');
      }
    } finally {
      setResolving(false);
    }
  }, [selectedSkillId, unresolvedSkill, importRunId, resolvedRawSkillId, onResolved, onClose]);

  // Filter suggestions by search query
  const filteredSuggestions = suggestions.filter(s => 
    !searchQuery || 
    s.skill_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.subcategory.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
            Map Unresolved Skill
          </h2>
          <p className="text-sm text-[#64748b] mt-1">
            Map "<span className="font-medium text-[#334155]">{unresolvedSkill?.raw_text}</span>" to an existing skill
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Employee info */}
          {unresolvedSkill?.employee_name && (
            <div className="mb-4 p-3 bg-[#f8fafc] rounded-lg">
              <span className="text-xs text-[#64748b]">Employee: </span>
              <span className="text-sm text-[#334155] font-medium">
                {unresolvedSkill.employee_name}
                {unresolvedSkill.employee_zid && (
                  <span className="text-[#64748b] ml-1">({unresolvedSkill.employee_zid})</span>
                )}
              </span>
            </div>
          )}

          {/* Search filter */}
          <div className="mb-4">
            <input
              type="text"
              placeholder="Filter suggestions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-[#e2e8f0] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#667eea]/20 focus:border-[#667eea]"
            />
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-[#fef2f2] border border-[#fecaca] rounded-lg text-sm text-[#dc2626]">
              {error}
            </div>
          )}

          {/* Suggestions list */}
          <div className="space-y-2">
            {loading ? (
              <div className="text-center py-8 text-[#64748b]">
                Loading suggestions...
              </div>
            ) : filteredSuggestions.length === 0 ? (
              <div className="text-center py-8 text-[#64748b]">
                No suggestions found. Skill not in master data. Contact admin to create it, then re-import or add via Data Management &gt; Employees.
              </div>
            ) : (
              filteredSuggestions.map((suggestion) => (
                <label
                  key={suggestion.skill_id}
                  className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedSkillId === suggestion.skill_id
                      ? 'border-[#667eea] bg-[#667eea]/5'
                      : 'border-[#e2e8f0] hover:border-[#cbd5e1] hover:bg-[#f8fafc]'
                  }`}
                >
                  <input
                    type="radio"
                    name="skill-selection"
                    value={suggestion.skill_id}
                    checked={selectedSkillId === suggestion.skill_id}
                    onChange={() => setSelectedSkillId(suggestion.skill_id)}
                    className="w-4 h-4 text-[#667eea] focus:ring-[#667eea]"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-[#1e293b]">
                      {suggestion.skill_name}
                    </div>
                    <div className="text-xs text-[#64748b]">
                      {suggestion.category} → {suggestion.subcategory}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      suggestion.match_type === 'exact'
                        ? 'bg-[#dcfce7] text-[#16a34a]'
                        : suggestion.match_type === 'alias'
                        ? 'bg-[#dbeafe] text-[#1e40af]'
                        : 'bg-[#fef3c7] text-[#92400e]'
                    }`}>
                      {suggestion.match_type}
                    </span>
                    <span className="text-xs text-[#64748b]">
                      {Math.round(suggestion.confidence * 100)}%
                    </span>
                  </div>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#e2e8f0] flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={resolving}
            className="px-4 py-2 text-sm font-medium text-[#475569] bg-white border border-[#e2e8f0] rounded-lg hover:bg-[#f8fafc] disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleResolve}
            disabled={!selectedSkillId || resolving}
            className="px-4 py-2 text-sm font-medium text-white bg-[#667eea] rounded-lg hover:bg-[#5568d3] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {resolving ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Mapping...
              </>
            ) : (
              'Map to Selected Skill'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SkillMappingModal;
