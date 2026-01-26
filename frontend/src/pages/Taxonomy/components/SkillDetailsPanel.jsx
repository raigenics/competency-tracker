import React from 'react';
import { Info, Users, TrendingUp, Award, ExternalLink } from 'lucide-react';

const SkillDetailsPanel = ({ skill }) => {
  if (!skill) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-8">
          <Info className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">Select a skill</h3>
          <p className="text-sm text-gray-500">
            Click on any skill from the taxonomy tree to view detailed information
          </p>
        </div>
      </div>
    );
  }

  // Mock data for skill statistics and details
  const skillStats = {
    totalEmployees: Math.floor(Math.random() * 50) + 5,
    averageProficiency: (Math.random() * 2 + 3).toFixed(1),
    expertEmployees: Math.floor(Math.random() * 10) + 1,
    growthRate: Math.floor(Math.random() * 30) + 5
  };

  const proficiencyDistribution = [
    { level: 1, label: 'Beginner', count: Math.floor(Math.random() * 5) + 1 },
    { level: 2, label: 'Basic', count: Math.floor(Math.random() * 8) + 2 },
    { level: 3, label: 'Intermediate', count: Math.floor(Math.random() * 12) + 5 },
    { level: 4, label: 'Advanced', count: Math.floor(Math.random() * 8) + 3 },
    { level: 5, label: 'Expert', count: Math.floor(Math.random() * 5) + 1 }
  ];

  const learningResources = [
    {
      title: `${skill.name} Fundamentals`,
      type: 'Course',
      provider: 'Learning Platform',
      url: '#'
    },
    {
      title: `Advanced ${skill.name}`,
      type: 'Tutorial',
      provider: 'Tech Docs',
      url: '#'
    },
    {
      title: `${skill.name} Best Practices`,
      type: 'Article',
      provider: 'Industry Blog',
      url: '#'
    }
  ];

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">{skill.name}</h2>
            <p className="text-sm text-gray-600">{skill.category || 'General'}</p>
          </div>
          {skill.isCore && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
              <Award className="h-3 w-3" />
              Core Skill
            </span>
          )}
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Description */}
        {skill.description && (
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Description</h3>
            <p className="text-sm text-gray-600">{skill.description}</p>
          </div>
        )}

        {/* Statistics */}
        <div>
          <h3 className="font-medium text-gray-900 mb-3">Organization Statistics</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <Users className="h-5 w-5 mx-auto mb-1 text-blue-600" />
              <div className="text-lg font-semibold text-gray-900">{skillStats.totalEmployees}</div>
              <div className="text-xs text-gray-600">Total Employees</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <TrendingUp className="h-5 w-5 mx-auto mb-1 text-green-600" />
              <div className="text-lg font-semibold text-gray-900">{skillStats.averageProficiency}</div>
              <div className="text-xs text-gray-600">Avg Proficiency</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <Award className="h-5 w-5 mx-auto mb-1 text-purple-600" />
              <div className="text-lg font-semibold text-gray-900">{skillStats.expertEmployees}</div>
              <div className="text-xs text-gray-600">Experts</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <TrendingUp className="h-5 w-5 mx-auto mb-1 text-orange-600" />
              <div className="text-lg font-semibold text-gray-900">+{skillStats.growthRate}%</div>
              <div className="text-xs text-gray-600">6M Growth</div>
            </div>
          </div>
        </div>

        {/* Proficiency Distribution */}
        <div>
          <h3 className="font-medium text-gray-900 mb-3">Proficiency Distribution</h3>
          <div className="space-y-2">
            {proficiencyDistribution.map((item) => {
              const percentage = (item.count / skillStats.totalEmployees) * 100;
              const colors = {
                1: 'bg-red-400',
                2: 'bg-orange-400', 
                3: 'bg-yellow-400',
                4: 'bg-blue-400',
                5: 'bg-green-400'
              };

              return (
                <div key={item.level} className="flex items-center gap-3">
                  <span className="text-xs font-medium text-gray-700 w-16">
                    {item.label}
                  </span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${colors[item.level]} transition-all duration-300`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-600 w-8">
                    {item.count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Learning Resources */}
        <div>
          <h3 className="font-medium text-gray-900 mb-3">Learning Resources</h3>
          <div className="space-y-2">
            {learningResources.map((resource, index) => (
              <a
                key={index}
                href={resource.url}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 group"
              >
                <div>
                  <div className="font-medium text-gray-900 group-hover:text-blue-600">
                    {resource.title}
                  </div>
                  <div className="text-sm text-gray-600">
                    {resource.type} • {resource.provider}
                  </div>
                </div>
                <ExternalLink className="h-4 w-4 text-gray-400 group-hover:text-blue-600" />
              </a>
            ))}
          </div>
        </div>

        {/* Related Skills */}
        {skill.relatedSkills && skill.relatedSkills.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Related Skills</h3>
            <div className="flex flex-wrap gap-2">
              {skill.relatedSkills.map((relatedSkill, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs cursor-pointer hover:bg-blue-200"
                >
                  {relatedSkill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Prerequisites */}
        {skill.prerequisites && skill.prerequisites.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Prerequisites</h3>
            <div className="flex flex-wrap gap-2">
              {skill.prerequisites.map((prerequisite, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs"
                >
                  {prerequisite}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SkillDetailsPanel;
