import { Users } from 'lucide-react';

const EmployeesInScopeCard = ({ totalEmployees, filteredScope, scopeLevel }) => {
  const getScopeLevelStyle = (level) => {
    const styles = {
      team: 'bg-green-100 text-green-700',
      project: 'bg-blue-100 text-blue-700',
      subsegment: 'bg-purple-100 text-purple-700',
      organization: 'bg-slate-100 text-slate-700'
    };
    return styles[level] || styles.organization;
  };

  const getScopeLevelLabel = (level) => {
    const labels = {
      team: 'Team',
      project: 'Project',
      subsegment: 'Sub-Segment',
      organization: 'Organization'
    };
    return labels[level] || 'Organization';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
            <Users className="w-8 h-8 text-blue-600" />
          </div>
          <div>
            <div className="text-xs text-slate-600 font-medium uppercase tracking-wide">Employees in Scope</div>
            <div className="text-4xl font-bold text-slate-900 mt-1">{totalEmployees}</div>
            <div className="text-sm text-slate-600 mt-1">{filteredScope}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-600 mb-1">Scope Level</div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getScopeLevelStyle(scopeLevel)}`}>
            {getScopeLevelLabel(scopeLevel)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default EmployeesInScopeCard;
