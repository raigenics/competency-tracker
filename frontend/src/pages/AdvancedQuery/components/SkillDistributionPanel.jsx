import React from 'react';
import { BarChart3, Users } from 'lucide-react';

const SkillDistributionPanel = ({ results }) => {
  // Aggregate skill data from results
  const skillData = results.reduce((acc, employee) => {
    employee.skills.forEach(skill => {
      if (!acc[skill.name]) {
        acc[skill.name] = {
          name: skill.name,
          totalEmployees: 0,
          averageProficiency: 0,
          proficiencyLevels: [0, 0, 0, 0, 0, 0] // 0-5
        };
      }
      acc[skill.name].totalEmployees += 1;
      acc[skill.name].proficiencyLevels[skill.proficiency] += 1;
    });
    return acc;
  }, {});

  // Calculate average proficiency for each skill
  Object.keys(skillData).forEach(skillName => {
    const skill = skillData[skillName];
    const totalProficiency = skill.proficiencyLevels.reduce((sum, count, level) => sum + (count * level), 0);
    skill.averageProficiency = totalProficiency / skill.totalEmployees;
  });

  // Sort skills by number of employees (most common first)
  const sortedSkills = Object.values(skillData).sort((a, b) => b.totalEmployees - a.totalEmployees);

  const getProficiencyColor = (level) => {
    const colors = [
      'bg-gray-300',   // 0
      'bg-red-400',    // 1
      'bg-orange-400', // 2
      'bg-yellow-400', // 3
      'bg-blue-400',   // 4
      'bg-green-400'   // 5
    ];
    return colors[level] || 'bg-gray-300';
  };

  const getProficiencyLabel = (level) => {
    const labels = ['None', 'Beginner', 'Basic', 'Intermediate', 'Advanced', 'Expert'];
    return labels[level] || 'Unknown';
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="border-b border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Skill Distribution Analysis
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Skill proficiency breakdown across {results.length} matching employees
        </p>
      </div>

      <div className="p-6">
        <div className="space-y-6">
          {sortedSkills.slice(0, 10).map((skill) => (
            <div key={skill.name} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">{skill.name}</h4>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    {skill.totalEmployees} employees
                  </span>
                  <span>
                    Avg: {skill.averageProficiency.toFixed(1)}/5
                  </span>
                </div>
              </div>

              {/* Proficiency Distribution Bar */}
              <div className="mb-3">
                <div className="flex h-6 bg-gray-200 rounded overflow-hidden">
                  {skill.proficiencyLevels.map((count, level) => {
                    const percentage = (count / skill.totalEmployees) * 100;
                    return percentage > 0 ? (
                      <div
                        key={level}
                        className={`${getProficiencyColor(level)} transition-all duration-300`}
                        style={{ width: `${percentage}%` }}
                        title={`${getProficiencyLabel(level)}: ${count} employees (${percentage.toFixed(1)}%)`}
                      />
                    ) : null;
                  })}
                </div>
              </div>

              {/* Proficiency Legend */}
              <div className="flex flex-wrap gap-4 text-xs text-gray-600">
                {skill.proficiencyLevels.map((count, level) => (
                  count > 0 && (
                    <div key={level} className="flex items-center gap-1">
                      <div className={`w-3 h-3 rounded ${getProficiencyColor(level)}`} />
                      <span>
                        {getProficiencyLabel(level)}: {count}
                      </span>
                    </div>
                  )
                ))}
              </div>
            </div>
          ))}
        </div>

        {sortedSkills.length > 10 && (
          <div className="mt-6 text-center">
            <button className="text-blue-600 hover:text-blue-800 font-medium">
              Show {sortedSkills.length - 10} more skills
            </button>
          </div>
        )}

        {sortedSkills.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No skills data available for analysis
          </div>
        )}
      </div>
    </div>
  );
};

export default SkillDistributionPanel;
