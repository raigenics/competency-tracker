import { CheckCircle, TrendingUp, Clock } from 'lucide-react';

const SkillProgressMomentum = ({ momentum }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900">Skill Progress Momentum</h3>
        <span className="text-xs text-slate-500">Based on last skill/proficiency update date</span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div 
          className="flex items-center justify-between p-5 bg-green-50 rounded-lg border-2 border-green-200" 
          title="Employees with at least one skill/proficiency update in the last 3 months"
        >
          <div>
            <div className="text-xs text-green-700 font-semibold mb-1">Updated in last 3 months</div>
            <div className="text-3xl font-bold text-green-700">{momentum.updated_last_3_months}</div>
            <div className="text-xs text-slate-600 mt-1">employees</div>
          </div>
          <CheckCircle className="w-10 h-10 text-green-600" />
        </div>
        <div 
          className="flex items-center justify-between p-5 bg-yellow-50 rounded-lg border-2 border-yellow-200" 
          title="Employees with at least one skill/proficiency update in the last 6 months (but not in the last 3 months)"
        >
          <div>
            <div className="text-xs text-yellow-700 font-semibold mb-1">Updated in last 6 months</div>
            <div className="text-3xl font-bold text-yellow-700">{momentum.updated_last_6_months}</div>
            <div className="text-xs text-slate-600 mt-1">employees</div>
          </div>
          <TrendingUp className="w-10 h-10 text-yellow-600" />
        </div>
        <div 
          className="flex items-center justify-between p-5 bg-orange-50 rounded-lg border-2 border-orange-200" 
          title="Employees whose skill/proficiency data has not been updated in more than 6 months"
        >
          <div>
            <div className="text-xs text-orange-700 font-semibold mb-1">Not updated in &gt; 6 months</div>
            <div className="text-3xl font-bold text-orange-700">{momentum.not_updated_6_months}</div>
            <div className="text-xs text-slate-600 mt-1">employees</div>
          </div>
          <Clock className="w-10 h-10 text-orange-600" />
        </div>
      </div>
    </div>
  );
};

export default SkillProgressMomentum;
