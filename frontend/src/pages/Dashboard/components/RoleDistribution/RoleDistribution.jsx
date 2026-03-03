import { RefreshCw, AlertCircle } from 'lucide-react';
import { useRoleDistribution } from '../../../../hooks/useRoleDistribution';
import { getTopRoles, getHiddenRoles, hasRoleData, shouldShowExpand } from './roleDistributionHelpers.js';

/**
 * RoleDistribution component - Role Distribution by Sub-Segment
 * 
 * Uses existing API data from useRoleDistribution hook → dashboardApi.getRoleDistribution
 * Preserves existing expand/collapse behavior.
 * 
 * Wireframe structure:
 * - Uses native HTML <details>/<summary> for expand/collapse
 * - Grid layout: seg-name | count | top role chips | chevron
 * - Expanded view shows additional roles not in top chips
 */

// ============================================
// COMPONENTS
// ============================================

/**
 * Role chip component for inline display of top roles.
 * Matches wireframe .role-chip styling
 */
const RoleChip = ({ roleName, count }) => (
  <span className="role-chip">
    {roleName} <b>{count}</b>
  </span>
);

/**
 * Single expandable row for a sub-segment
 */
const RoleDistributionRow = ({ row }) => {
  const allRoles = row.all_roles || [];
  const topRoles = getTopRoles(allRoles);
  const hiddenRoles = getHiddenRoles(allRoles);
  const showExpand = shouldShowExpand(allRoles);
  const moreCount = hiddenRoles.length;

  // If no expand needed, render without details/summary
  if (!showExpand) {
    return (
      <div style={{ borderBottom: '1px solid var(--db-border)', padding: '10px 0' }}>
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: '140px 90px 1fr 70px',
            gap: '12px',
            alignItems: 'center',
            padding: '8px 8px',
            borderRadius: '12px'
          }}
        >
          <div className="seg-name">{row.breakdown_name}</div>
          <div><span className="count">{row.total_employees}</span></div>
          <div className="chips">
            {topRoles.map((role, i) => (
              <RoleChip key={i} roleName={role.role_name} count={role.employee_count} />
            ))}
          </div>
          <div></div>
        </div>
      </div>
    );
  }

  return (
    <details>
      <summary>
        <div className="seg-name">{row.breakdown_name}</div>
        <div><span className="count">{row.total_employees}</span></div>
        <div className="chips">
          {topRoles.map((role, i) => (
            <RoleChip key={i} roleName={role.role_name} count={role.employee_count} />
          ))}
          {moreCount > 0 && (
            <span className="more">+{moreCount} more</span>
          )}
        </div>
        <div className="chev">›</div>
      </summary>
      <div className="detail">
        <b>Other roles in {row.breakdown_name}:</b>
        <ul>
          {hiddenRoles.map((role, i) => (
            <li key={i}>{role.role_name} ({role.employee_count})</li>
          ))}
        </ul>
      </div>
    </details>
  );
};

/**
 * Loading skeleton component
 */
const LoadingSkeleton = () => (
  <div style={{ padding: '20px' }}>
    <div style={{ background: '#e2e8f0', height: '20px', width: '200px', borderRadius: '6px', marginBottom: '12px' }}></div>
    <div style={{ background: '#e2e8f0', height: '14px', width: '300px', borderRadius: '4px', marginBottom: '24px' }}></div>
    {[1, 2, 3].map(i => (
      <div key={i} style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
        <div style={{ background: '#e2e8f0', height: '40px', width: '120px', borderRadius: '8px' }}></div>
        <div style={{ background: '#e2e8f0', height: '40px', width: '60px', borderRadius: '8px' }}></div>
        <div style={{ background: '#e2e8f0', height: '40px', flex: 1, borderRadius: '8px' }}></div>
      </div>
    ))}
  </div>
);

/**
 * Error state component
 */
const ErrorState = ({ error, onRetry }) => (
  <div style={{ padding: '40px', textAlign: 'center' }}>
    <AlertCircle size={40} style={{ color: '#ef4444', marginBottom: '16px' }} />
    <h4 style={{ margin: '0 0 8px', fontSize: '16px', fontWeight: '600' }}>Failed to load role distribution</h4>
    <p style={{ color: 'var(--db-muted)', fontSize: '13px', marginBottom: '16px' }}>
      {error?.message || 'An unexpected error occurred.'}
    </p>
    <button
      type="button"
      onClick={onRetry}
      className="db-btn primary"
      style={{ display: 'inline-flex' }}
    >
      <RefreshCw size={14} />
      Retry
    </button>
  </div>
);

/**
 * Empty state component
 */
const EmptyState = () => (
  <div style={{ padding: '40px', textAlign: 'center' }}>
    <div style={{ 
      width: '48px', 
      height: '48px', 
      background: '#f1f5f9', 
      borderRadius: '50%', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      margin: '0 auto 16px'
    }}>
      <span style={{ color: '#94a3b8', fontSize: '20px' }}>↓</span>
    </div>
    <h4 style={{ margin: '0 0 8px', fontSize: '16px', fontWeight: '600' }}>No role distribution data</h4>
    <p style={{ color: 'var(--db-muted)', fontSize: '13px' }}>
      There is no role data available for the selected filters.
    </p>
  </div>
);

/**
 * Main RoleDistribution component
 * 
 * Uses existing useRoleDistribution hook - NO API CHANGES
 */
const RoleDistribution = ({ dashboardFilters }) => {
  // Pass segmentId explicitly from dashboardFilters to ensure segment scope is respected
  const { data, isLoading, error, refetch } = useRoleDistribution(dashboardFilters, {
    segmentId: dashboardFilters.segment
  });

  // Loading state
  if (isLoading) {
    return (
      <section className="db-card">
        <LoadingSkeleton />
      </section>
    );
  }

  // Error state
  if (error) {
    return (
      <section className="db-card">
        <ErrorState error={error} onRetry={refetch} />
      </section>
    );
  }

  // Filter out groups with zero role data
  const filteredRows = (data?.rows || []).filter((row) => hasRoleData(row.all_roles));

  // Empty state
  if (!data || filteredRows.length === 0) {
    return (
      <section className="db-card">
        <EmptyState />
      </section>
    );
  }

  return (
    <section className="db-card">
      <div className="db-card-h">
        <div className="left">
          <h4>Role Distribution by Sub-Segment</h4>
          <p>Shows top roles and allows drill-down for the rest</p>
        </div>
        
      </div>
      <div className="db-card-b db-roles">
        {filteredRows.map((row, index) => (
          <RoleDistributionRow key={row.breakdown_id || index} row={row} />
        ))}
      </div>
    </section>
  );
};

export default RoleDistribution;