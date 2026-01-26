import { Award, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const SkillDistributionTable = ({ skillDistribution, topSkillsCount, scopeLevel }) => {
  const navigate = useNavigate();

  const handleSkillClick = () => {
    navigate('/query');
  };

  return (
    <div className="bg-white rounded-lg shadow-md border-2 border-blue-200 p-6 mb-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-xl font-bold text-slate-900 flex items-center">
            <Award className="w-6 h-6 mr-2 text-blue-600" />
            Top {topSkillsCount} Skills by Employee Count
          </h3>
          <p className="text-sm text-slate-600 mt-2">
            Primary skills in this scope with proficiency breakdown • Showing {topSkillsCount} skills for {scopeLevel} level
          </p>
        </div>
        <button
          onClick={handleSkillClick}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center space-x-1"
        >
          <span>Detailed View</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 border-b-2 border-slate-300">
            <tr>
              <th className="text-left py-4 px-4 font-bold text-slate-700 text-sm">Skill Name</th>
              <th className="text-center py-4 px-4 font-bold text-slate-700 text-sm">Total Employees</th>
              <th className="text-center py-4 px-4 font-bold text-slate-700 text-sm">
                <div className="flex items-center justify-center space-x-1">
                  <div className="w-3 h-3 bg-green-600 rounded-full"></div>
                  <span>Expert</span>
                </div>
              </th>
              <th className="text-center py-4 px-4 font-bold text-slate-700 text-sm">
                <div className="flex items-center justify-center space-x-1">
                  <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                  <span>Proficient</span>
                </div>
              </th>
              <th className="text-left py-4 px-4 font-bold text-slate-700 text-sm">Proficiency Breakdown</th>
            </tr>
          </thead>
          <tbody>
            {skillDistribution.map((skill, i) => {
              const expertPercent = (skill.expert / skill.total) * 100;
              const proficientPercent = (skill.proficient / skill.total) * 100;
              const otherPercent = 100 - expertPercent - proficientPercent;

              return (
                <tr key={i} className="border-b border-slate-200 hover:bg-blue-50 transition-colors">
                  <td className="py-4 px-4">
                    <span className="font-bold text-slate-900 text-base">{skill.skill}</span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold text-base">
                      {skill.total}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <div className="font-bold text-green-700 text-lg">{skill.expert}</div>
                    <div className="text-xs text-slate-500 font-semibold mt-1">{expertPercent.toFixed(0)}%</div>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <div className="font-bold text-blue-700 text-lg">{skill.proficient}</div>
                    <div className="text-xs text-slate-500 font-semibold mt-1">{proficientPercent.toFixed(0)}%</div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 h-4 bg-slate-200 rounded-full overflow-hidden flex">
                        <div 
                          className="bg-green-600 h-full" 
                          style={{ width: `${expertPercent}%` }}
                          title={`Expert: ${skill.expert} (${expertPercent.toFixed(0)}%)`}
                        ></div>
                        <div 
                          className="bg-blue-600 h-full" 
                          style={{ width: `${proficientPercent}%` }}
                          title={`Proficient: ${skill.proficient} (${proficientPercent.toFixed(0)}%)`}
                        ></div>
                        <div 
                          className="bg-slate-400 h-full" 
                          style={{ width: `${otherPercent}%` }}
                          title={`Other: ${skill.total - skill.expert - skill.proficient} (${otherPercent.toFixed(0)}%)`}
                        ></div>
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-5 pt-5 border-t border-slate-200 flex items-center space-x-6 text-sm bg-slate-50 p-4 rounded-lg">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-green-600 rounded"></div>
          <span className="text-slate-700 font-medium">Expert</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-blue-600 rounded"></div>
          <span className="text-slate-700 font-medium">Proficient</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-slate-400 rounded"></div>
          <span className="text-slate-700 font-medium">Intermediate/Beginner</span>
        </div>
        <div className="ml-auto text-xs text-slate-600">
          Skills ranked by total employee count • Proficiency based on Dreyfus model
        </div>
      </div>
    </div>
  );
};

export default SkillDistributionTable;
