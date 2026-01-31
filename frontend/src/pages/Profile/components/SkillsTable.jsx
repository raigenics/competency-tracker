import React, { useState } from 'react';
import { Edit, Save, X, Plus, TrendingUp, Calendar } from 'lucide-react';
import { employeeApi } from '../../../services/api/employeeApi';

const SkillsTable = ({ employeeId, skills = [], isEditable = false, showHistory = false, onSkillUpdate }) => {
  const [editingSkill, setEditingSkill] = useState(null);
  const [newSkillProficiency, setNewSkillProficiency] = useState(1);
  const [isAdding, setIsAdding] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');
  const [loading, setLoading] = useState(false);

  const proficiencyLevels = [
    { value: 0, label: 'None', color: 'bg-gray-200' },
    { value: 1, label: 'Beginner', color: 'bg-red-400' },
    { value: 2, label: 'Basic', color: 'bg-orange-400' },
    { value: 3, label: 'Intermediate', color: 'bg-yellow-400' },
    { value: 4, label: 'Advanced', color: 'bg-blue-400' },
    { value: 5, label: 'Expert', color: 'bg-green-400' }
  ];

  const getProficiencyInfo = (level) => {
    return proficiencyLevels[level] || proficiencyLevels[0];
  };

  const handleEditClick = (skill) => {
    setEditingSkill({
      ...skill,
      newProficiency: skill.proficiency
    });
  };

  const handleSaveEdit = async () => {
    if (!editingSkill) return;

    setLoading(true);
    try {
      await employeeApi.updateEmployeeSkill(
        employeeId, 
        editingSkill.skillId, 
        editingSkill.newProficiency
      );
      setEditingSkill(null);
      if (onSkillUpdate) {
        onSkillUpdate();
      }
    } catch (error) {
      console.error('Failed to update skill:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingSkill(null);
  };

  const handleAddSkill = async () => {
    if (!newSkillName.trim()) return;

    setLoading(true);
    try {
      await employeeApi.createEmployeeSkill(
        employeeId,
        newSkillName.trim(),
        newSkillProficiency
      );
      setIsAdding(false);
      setNewSkillName('');
      setNewSkillProficiency(1);
      if (onSkillUpdate) {
        onSkillUpdate();
      }
    } catch (error) {
      console.error('Failed to add skill:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelAdd = () => {
    setIsAdding(false);
    setNewSkillName('');
    setNewSkillProficiency(1);
  };

  const ProficiencyBar = ({ level, isEditing, onChange }) => {
    const proficiencyInfo = getProficiencyInfo(level);

    if (isEditing) {
      return (
        <select
          value={level}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {proficiencyLevels.slice(1).map((profLevel) => (
            <option key={profLevel.value} value={profLevel.value}>
              {profLevel.value} - {profLevel.label}
            </option>
          ))}
        </select>
      );
    }

    return (
      <div className="flex items-center gap-3">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${proficiencyInfo.color} transition-all duration-300`}
            style={{ width: `${(level / 5) * 100}%` }}
          />
        </div>
        <span className="text-sm font-medium text-gray-700 min-w-0">
          {level}/5
        </span>
        <span className={`text-xs px-2 py-1 rounded-full text-white ${proficiencyInfo.color}`}>
          {proficiencyInfo.label}
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Skills Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-gray-700">Skill</th>
              <th className="text-left py-3 px-4 font-medium text-gray-700">Proficiency</th>
              <th className="text-left py-3 px-4 font-medium text-gray-700">Category</th>
              {showHistory && (
                <th className="text-left py-3 px-4 font-medium text-gray-700">Last Updated</th>
              )}
              {isEditable && (
                <th className="text-left py-3 px-4 font-medium text-gray-700">Actions</th>
              )}
            </tr>
          </thead>
          <tbody>
            {skills.map((skill) => (
              <tr key={skill.skillId || skill.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-4 px-4">
                  <div className="font-medium text-gray-900">{skill.name}</div>
                  {skill.description && (
                    <div className="text-sm text-gray-600">{skill.description}</div>
                  )}                </td>                <td className="py-4 px-4">
                  {/* Guard against null editingSkill - can occur when navigating from Capability Overview/Finder */}
                  <ProficiencyBar
                    level={editingSkill?.skillId === (skill.skillId || skill.id) ? (editingSkill?.newProficiency ?? skill.proficiency) : skill.proficiency}
                    isEditing={editingSkill?.skillId === (skill.skillId || skill.id)}
                    onChange={(newLevel) => setEditingSkill({ ...editingSkill, newProficiency: newLevel })}
                  />
                </td>
                <td className="py-4 px-4">
                  <span className="text-sm text-gray-600">{skill.category || 'General'}</span>
                </td>
                {showHistory && (
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Calendar className="h-4 w-4" />
                      {skill.lastUpdated ? new Date(skill.lastUpdated).toLocaleDateString() : 'Never'}
                    </div>
                  </td>
                )}
                {isEditable && (
                  <td className="py-4 px-4">
                    {editingSkill?.skillId === (skill.skillId || skill.id) ? (
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveEdit}
                          disabled={loading}
                          className="text-green-600 hover:text-green-800 disabled:opacity-50"
                        >
                          <Save className="h-4 w-4" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          disabled={loading}
                          className="text-gray-600 hover:text-gray-800"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleEditClick(skill)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}

            {/* Add New Skill Row */}
            {isEditable && isAdding && (
              <tr className="border-b border-gray-100 bg-blue-50">
                <td className="py-4 px-4">
                  <input
                    type="text"
                    value={newSkillName}
                    onChange={(e) => setNewSkillName(e.target.value)}
                    placeholder="Skill name..."
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </td>
                <td className="py-4 px-4">
                  <ProficiencyBar
                    level={newSkillProficiency}
                    isEditing={true}
                    onChange={setNewSkillProficiency}
                  />
                </td>
                <td className="py-4 px-4">
                  <span className="text-sm text-gray-600">General</span>
                </td>
                {showHistory && (
                  <td className="py-4 px-4">
                    <span className="text-sm text-gray-600">New</span>
                  </td>
                )}
                <td className="py-4 px-4">
                  <div className="flex gap-2">
                    <button
                      onClick={handleAddSkill}
                      disabled={loading || !newSkillName.trim()}
                      className="text-green-600 hover:text-green-800 disabled:opacity-50"
                    >
                      <Save className="h-4 w-4" />
                    </button>
                    <button
                      onClick={handleCancelAdd}
                      disabled={loading}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add Skill Button */}
      {isEditable && !isAdding && (
        <button
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-2 px-4 py-2 text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50"
        >
          <Plus className="h-4 w-4" />
          Add New Skill
        </button>
      )}

      {/* Empty State */}
      {skills.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-600">No skills recorded yet</p>
          <p className="text-sm text-gray-500">
            {isEditable ? 'Add your first skill to get started' : 'This employee has no skills on record'}
          </p>
        </div>
      )}
    </div>
  );
};

export default SkillsTable;
