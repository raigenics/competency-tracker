import { useState } from 'react';
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

  if (loading) {
    return (
      <section className="db-card db-activity-card" style={{ gridColumn: '2 / span 1' }}>
        <div className="db-card-h">
          <div className="left">
            <h4>Skill Update Activity</h4>
            <p>Loading...</p>
          </div>
        </div>
        <div className="db-card-b">
          <div className="db-activity">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="db-stat" style={{ opacity: 0.5 }}>
                <div className="top">
                  <b style={{ background: '#e2e8f0', width: '60px', height: '14px', display: 'block', borderRadius: '4px' }}></b>
                </div>
                <div style={{ background: '#e2e8f0', width: '50px', height: '28px', borderRadius: '6px', marginTop: '10px' }}></div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  const cards = [
    {
      title: 'Updates',
      value: activityData?.total_updates || 0,
      caption: 'Employees with ≥ 1 update',
      chipLabel: 'Active',
      chipClass: 'ok',
      progressVariant: 'success'
    },
    {
      title: 'Active Learners',
      value: activityData?.active_learners || 0,
      caption: 'Employees with ≥ 2 updates',
      chipLabel: 'Engaged',
      chipClass: 'ok',
      progressVariant: 'success'
    },
    {
      title: 'Low Activity',
      value: activityData?.low_activity || 0,
      caption: 'Employees with 0–1 update',
      chipLabel: 'Watch',
      chipClass: 'warn',
      progressVariant: 'warn'
    },
    {
      title: 'Stagnant',
      value: activityData?.stagnant_180_days || 0,
      caption: 'No updates in 180+ days',
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
        <span className="db-pill">Last {selectedDays} days</span>
      </div>
      <div className="db-card-b">
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
