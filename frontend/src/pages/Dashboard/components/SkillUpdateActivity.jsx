import { useState, useEffect } from 'react';
import MiniProgressBar from './MiniProgressBar.jsx';

/**
 * SkillUpdateActivity - Skill Update Activity Section
 * 
 * Uses existing API data from dashboardApi.getSkillUpdateActivity
 * Preserves existing behavior and data source.
 * 
 * Progress bars show count / employeesInScope as a visual indicator.
 */
const SkillUpdateActivity = ({ activityData, loading, onDaysChange, employeesInScope = 0 }) => {
  const [selectedDays, setSelectedDays] = useState(90);
  const [isDimmed, setIsDimmed] = useState(false);

  // Inject pulse keyframe once on mount
  useEffect(() => {
    if (document.getElementById('sua-pulse-style')) return;
    const style = document.createElement('style');
    style.id = 'sua-pulse-style';
    style.textContent = '@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }';
    document.head.appendChild(style);
  }, []);

  // Delay isDimmed by 150ms to avoid flash on fast responses
  useEffect(() => {
    if (!loading) {
      setIsDimmed(false);
      return;
    }
    const timer = setTimeout(() => {
      setIsDimmed(true);
    }, 150);
    return () => clearTimeout(timer);
  }, [loading]);

  const _handleDaysChange = (newDays) => {
    setSelectedDays(newDays);
    if (onDaysChange) {
      onDaysChange(newDays);
    }
  };

  // Calculate progress percentage (clamped 0-100)
  const calcProgress = (count) => {
    if (!employeesInScope || employeesInScope <= 0) return 0;
    return Math.round((count / employeesInScope) * 100);
  };

  const cards = [
    {
      title: 'Engaged',
      value: activityData?.engaged || 0,
      caption: `2+ updates in last ${selectedDays} days`,
      chipLabel: 'Engaged',
      chipClass: 'ok',
      progressVariant: 'success'
    },
    {
      title: 'Active',
      value: activityData?.active || 0,
      caption: `Exactly 1 update in last ${selectedDays} days`,
      chipLabel: 'Active',
      chipClass: 'ok',
      progressVariant: 'success'
    },
    {
      title: 'Inactive',
      value: activityData?.inactive || 0,
      caption: `0 updates in last ${selectedDays} days`,
      chipLabel: 'Watch',
      chipClass: 'warn',
      progressVariant: 'warn'
    },
    {
      title: 'Stagnant',
      value: activityData?.stagnant_180_days || 0,
      caption: 'No updates in 180+ days (risk indicator)',
      chipLabel: 'Risk',
      chipClass: 'risk',
      progressVariant: 'danger'
    }
  ];

  return (
    <section className="db-card db-activity-card" style={{ gridColumn: '2 / span 1' }}>
      <div className="db-card-h">
        <div className="left">
          <h4>Skill Update Activity</h4>
          <p>Signals to spot engaged vs stagnant team members</p>
        </div>
        <select
          className="db-pill"
          value={selectedDays}
          onChange={(e) => _handleDaysChange(Number(e.target.value))}
          disabled={loading}
          style={{ cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1 }}
        >
          <option value={90}>Last 90 days</option>
          <option value={60}>Last 60 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>
      <div
        className="db-card-b"
        style={{
          opacity: isDimmed ? 0.45 : 1,
          transition: 'opacity 0.2s ease',
          pointerEvents: isDimmed ? 'none' : 'auto',
          position: 'relative'
        }}
      >
        {isDimmed && (
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2,
            pointerEvents: 'none'
          }}>
            <span style={{
              fontSize: '12px',
              color: '#64748b',
              fontStyle: 'italic',
              animation: 'pulse 1.2s ease-in-out infinite',
              background: 'rgba(255,255,255,0.7)',
              padding: '4px 12px',
              borderRadius: '999px'
            }}>
              Updating...
            </span>
          </div>
        )}
        <div className="db-activity">
          {cards.map((card, index) => (
            <div key={index} className="db-stat">
              <div className="top">
                <b>{card.title}</b>
                <span className={`db-chip ${card.chipClass}`}>{card.chipLabel}</span>
              </div>
              <div className="stat-value">{card.value}</div>
              <p className="sub">{card.caption}</p>
              <MiniProgressBar 
                value={calcProgress(card.value)} 
                variant={card.progressVariant} 
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SkillUpdateActivity;
