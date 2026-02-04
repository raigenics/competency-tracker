import { useState } from 'react';
import { TrendingUp, Users, AlertTriangle, AlertCircle } from 'lucide-react';

const SkillUpdateActivity = ({ activityData, loading, onDaysChange }) => {
  const [selectedDays, setSelectedDays] = useState(90);

  const handleDaysChange = (newDays) => {
    setSelectedDays(newDays);
    if (onDaysChange) {
      onDaysChange(newDays);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-slate-200 rounded w-2/3 mb-6"></div>
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-40 bg-slate-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }
  const cards = [
    {
      title: 'Updates in last 90 days',
      value: activityData?.total_updates || 0,
      caption: 'Employees with ≥ 1 update in last 90 days',
      badge: { label: 'Activity', color: 'bg-blue-100 text-blue-700' },
      icon: TrendingUp,
      iconColor: 'text-blue-600',
      iconBg: 'bg-blue-100'
    },
    {
      title: 'Active learners',
      value: activityData?.active_learners || 0,
      caption: 'Employees with ≥ 2 updates in last 90 days',
      badge: { label: 'Engaged', color: 'bg-green-100 text-green-700' },
      icon: Users,
      iconColor: 'text-green-600',
      iconBg: 'bg-green-100'
    },
    {
      title: 'Low activity',
      value: activityData?.low_activity || 0,
      caption: 'Employees with 0–1 update in last 90 days',
      badge: { label: 'Watch', color: 'bg-yellow-100 text-yellow-700' },
      icon: AlertTriangle,
      iconColor: 'text-yellow-600',
      iconBg: 'bg-yellow-100'
    },
    {
      title: 'Stagnant',
      value: activityData?.stagnant_180_days || 0,
      caption: 'Employees with no updates in 180+ days',
      badge: { label: 'Risk', color: 'bg-red-100 text-red-700' },
      icon: AlertCircle,
      iconColor: 'text-red-600',
      iconBg: 'bg-red-100'
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Skill Update Activity</h3>
          <p className="text-sm text-slate-600 mt-1">
            Based on skill/proficiency updates captured in the system.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-600">Time window:</span>
          <select
            value={selectedDays}
            onChange={(e) => handleDaysChange(Number(e.target.value))}
            className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={180}>Last 180 days</option>
          </select>
        </div>
      </div>      {/* Cards Grid */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div
              key={index}
              className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-md transition-shadow"
            >
              {/* Header with Icon and Badge */}
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg ${card.iconBg} flex items-center justify-center`}>
                  <Icon className={`w-5 h-5 ${card.iconColor}`} />
                </div>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded ${card.badge.color}`}>
                  {card.badge.label}
                </span>
              </div>

              {/* Title */}
              <h4 className="text-sm font-medium text-slate-700 mb-1">
                {card.title}
              </h4>

              {/* Value */}
              <div className="text-3xl font-bold text-slate-900 mb-2">
                {card.value.toLocaleString()}
              </div>

              {/* Caption */}
              <p className="text-xs text-slate-600">
                {card.caption}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SkillUpdateActivity;
