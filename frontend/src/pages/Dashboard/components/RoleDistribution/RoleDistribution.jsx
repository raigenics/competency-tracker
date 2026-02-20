import { useState } from 'react';
import { ChevronRight, RefreshCw, AlertCircle } from 'lucide-react';
import { useRoleDistribution } from '../../../../hooks/useRoleDistribution';
import { getTopRoles, getHiddenRoles, hasRoleData, shouldShowExpand } from './roleDistributionHelpers.js';

// ============================================
// COMPONENTS
// ============================================

/**
 * Role chip component for inline display of top roles.
 */
const RoleChip = ({ roleName, count }) => (
  <div className="role-chip inline-flex items-center gap-2 px-2.5 py-1.5 bg-gray-100 border border-gray-200 rounded-full text-xs max-w-[160px]">
    <span className="role-chip-name font-medium text-gray-700 whitespace-nowrap overflow-hidden text-ellipsis">
      {roleName}
    </span>
    <span className="role-chip-count font-semibold text-gray-900 flex-shrink-0">{count}</span>
  </div>
);

/**
 * Role item for the expanded breakdown panel.
 */
const RoleItem = ({ roleName, count }) => (
  <div className="role-item flex justify-between items-center px-3 py-2 bg-slate-50 rounded-md text-sm">
    <span className="role-item-name text-slate-600 font-medium">{roleName}</span>
    <span className="role-item-count font-semibold text-slate-900 bg-white px-2 py-0.5 rounded text-xs">
      {count}
    </span>
  </div>
);

/**
 * Table row component with expandable additional roles panel.
 * Matches OrgRoles.html expand/collapse behavior exactly.
 */
const RoleDistributionRow = ({ row }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Use all_roles from API, or fall back to computing from top_roles
  const allRoles = row.all_roles || [];
  const topRoles = getTopRoles(allRoles);
  const hiddenRoles = getHiddenRoles(allRoles);
  const showExpand = shouldShowExpand(allRoles);
  const moreCount = hiddenRoles.length;
  
  const handleToggle = () => {
    if (showExpand) {
      setExpanded(!expanded);
    }
  };
  
  const handleKeyDown = (e) => {
    if ((e.key === 'Enter' || e.key === ' ') && showExpand) {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <>
      {/* Main row */}
      <tr 
        className={`border-b border-slate-100 hover:bg-slate-50 transition-colors ${showExpand ? 'cursor-pointer' : ''}`}
        onClick={showExpand ? handleToggle : undefined}
        role={showExpand ? "button" : undefined}
        tabIndex={showExpand ? 0 : undefined}
        onKeyDown={showExpand ? handleKeyDown : undefined}
        aria-expanded={showExpand ? expanded : undefined}
      >
        <td className="py-3.5 px-3">
          {/* Expand icon - only render when expand is available */}
          {showExpand && (
            <span 
              className={`expand-icon inline-block w-5 h-5 text-center leading-5 rounded mr-2 text-sm select-none transition-all ${
                expanded 
                  ? 'expanded bg-blue-100 text-blue-600 rotate-90' 
                  : 'bg-slate-200 text-slate-500'
              }`}
              aria-hidden="true"
            >
              ▸
            </span>
          )}
          <span className="cell-subsegment font-semibold text-slate-900">{row.breakdown_name}</span>
        </td>
        <td className="py-3.5 px-3 cell-total font-semibold text-slate-900 text-base">{row.total_employees}</td>
        <td className="py-3.5 px-3">
          <div className="top-roles-container flex items-center flex-wrap gap-2">
            {topRoles.map((role, i) => (
              <RoleChip key={i} roleName={role.role_name} count={role.employee_count} />
            ))}
            {/* "+ N more" indicator - only show when moreCount > 0 */}
            {moreCount > 0 && (
              <span 
                className="more-roles-indicator text-xs text-gray-500 font-medium whitespace-nowrap"
                onClick={showExpand ? (e) => { e.stopPropagation(); setExpanded(!expanded); } : undefined}
              >
                + {moreCount} more
              </span>
            )}
          </div>
        </td>
      </tr>
      
      {/* Expanded row - only renders remaining roles (not duplicating top 3) */}
      {showExpand && (
        <tr className={`expanded-row bg-slate-50 ${expanded ? 'show' : ''}`}
            style={{ display: expanded ? 'table-row' : 'none' }}>
          <td colSpan="3" className="p-0">
            <div className="expanded-content pl-14 pr-3 pb-5">
              <div className="expanded-inner bg-white border border-slate-200 rounded-lg p-4">
                <div className="breakdown-title text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                  Additional Roles
                </div>
                <div className="role-breakdown grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
                  {hiddenRoles.map((role, i) => (
                    <RoleItem key={i} roleName={role.role_name} count={role.employee_count} />
                  ))}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

/**
 * Loading skeleton component for the table.
 */
const LoadingSkeleton = () => (
  <div className="animate-pulse">
    <div className="h-6 bg-slate-200 rounded w-1/3 mb-2"></div>
    <div className="h-4 bg-slate-200 rounded w-1/2 mb-6"></div>
    <div className="space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-4">
          <div className="h-10 bg-slate-200 rounded w-1/4"></div>
          <div className="h-10 bg-slate-200 rounded w-16"></div>
          <div className="h-10 bg-slate-200 rounded flex-1"></div>
        </div>
      ))}
    </div>
  </div>
);

/**
 * Error state component with retry button.
 */
const ErrorState = ({ error, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
    <h4 className="text-lg font-semibold text-slate-900 mb-2">Failed to load role distribution</h4>
    <p className="text-sm text-slate-500 mb-4 max-w-md">
      {error?.message || 'An unexpected error occurred. Please try again.'}
    </p>
    <button
      type="button"
      onClick={onRetry}
      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
    >
      <RefreshCw className="w-4 h-4" />
      Retry
    </button>
  </div>
);

/**
 * Empty state component when no data is available.
 */
const EmptyState = () => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-4">
      <ChevronRight className="w-6 h-6 text-slate-400" />
    </div>
    <h4 className="text-lg font-semibold text-slate-900 mb-2">No role distribution data</h4>
    <p className="text-sm text-slate-500 max-w-md">
      There is no role data available for the selected filters. Try adjusting your filter selection.
    </p>
  </div>
);

/**
 * RoleDistribution component - replaces OrgCoverageTable
 * Shows role distribution based on current dashboard filter context.
 */
const RoleDistribution = ({ dashboardFilters }) => {
  // Fetch role distribution data from API
  const { data, isLoading, error, refetch } = useRoleDistribution(dashboardFilters);

  // Handle loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <LoadingSkeleton />
      </div>
    );
  }

  // Handle error state
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <ErrorState error={error} onRetry={refetch} />
      </div>
    );
  }

  // Filter out groups with zero role data (no roles with count > 0)
  const filteredRows = (data?.rows || []).filter((row) => hasRoleData(row.all_roles));

  // Handle empty state (after filtering)
  if (!data || filteredRows.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-slate-900 mb-1">{data.title}</h3>
          <p className="text-sm text-slate-500">{data.subtitle}</p>
        </div>
        
      </div>
      
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="drilldown-table w-full text-sm border-collapse mb-4">
          <thead className="bg-slate-50 border-b-2 border-slate-200">
            <tr>
              <th className="py-3 px-3 text-left font-semibold text-slate-600 text-xs uppercase tracking-wide">
                {data.breakdown_label}
              </th>
              <th className="py-3 px-3 text-left font-semibold text-slate-600 text-xs uppercase tracking-wide">
                Total
              </th>
              <th className="py-3 px-3 text-left font-semibold text-slate-600 text-xs uppercase tracking-wide">
                Top Roles
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, index) => (
              <RoleDistributionRow key={row.breakdown_id || index} row={row} />
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Footer */}
      <div className="pt-4 border-t border-slate-200 text-right text-xs text-slate-400">
        Last updated: just now
      </div>
    </div>
  );
};

export default RoleDistribution;
