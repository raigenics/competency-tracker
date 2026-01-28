import React, { useState, useEffect, useRef } from 'react';
import { Download, ChevronDown } from 'lucide-react';

/**
 * Reusable export menu component with dropdown for "Export All" and "Export Selected"
 * 
 * @param {number} totalCount - Total number of results available
 * @param {number} selectedCount - Number of selected items
 * @param {Function} onExportAll - Callback when "Export All" is clicked
 * @param {Function} onExportSelected - Callback when "Export Selected" is clicked
 * @param {boolean} isExporting - Whether export is in progress
 * @param {string} exportError - Error message to display (if any)
 */
const TalentExportMenu = ({
  totalCount = 0,
  selectedCount = 0,
  onExportAll,
  onExportSelected,
  isExporting = false,
  exportError = null
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        setShowMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscapeKey);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, []);

  const handleExportAll = () => {
    setShowMenu(false);
    onExportAll();
  };

  const handleExportSelected = () => {
    setShowMenu(false);
    onExportSelected();
  };

  const buttonLabel = selectedCount > 0 
    ? `Export Selected (${selectedCount})` 
    : 'Export';

  return (
    <div className="flex flex-col items-end gap-2">
      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setShowMenu(!showMenu)}
          disabled={isExporting}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            isExporting
              ? 'bg-blue-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          } text-white`}
        >
          {isExporting ? (
            <>
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
              Exporting...
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              {buttonLabel}
              <ChevronDown className="h-4 w-4" />
            </>
          )}
        </button>
        
        {showMenu && !isExporting && (
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-10">
            <button
              onClick={handleExportAll}
              className="w-full text-left px-4 py-2 hover:bg-slate-50 transition-colors text-slate-700"
            >
              Export All Results ({totalCount})
            </button>
            <button
              onClick={handleExportSelected}
              disabled={selectedCount === 0}
              className={`w-full text-left px-4 py-2 transition-colors ${
                selectedCount === 0 
                  ? 'text-slate-400 cursor-not-allowed' 
                  : 'text-slate-700 hover:bg-slate-50'
              }`}
            >
              Export Selected ({selectedCount})
            </button>
          </div>
        )}
      </div>
      
      {exportError && (
        <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded border border-red-200">
          {exportError}
        </div>
      )}
    </div>
  );
};

export default TalentExportMenu;
