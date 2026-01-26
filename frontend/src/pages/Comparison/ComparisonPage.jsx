import React, { useState, useEffect } from 'react';
import { Search, Users, X, Plus, BarChart3, ArrowUpDown } from 'lucide-react';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';
import { mockEmployees } from '../../data/mockEmployees';

const ComparisonPage = () => {
  const [availableEmployees, setAvailableEmployees] = useState([]);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredEmployees, setFilteredEmployees] = useState([]);

  useEffect(() => {
    loadEmployees();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = availableEmployees.filter(emp => 
        emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.role.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.team.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredEmployees(filtered);
    } else {
      setFilteredEmployees(availableEmployees);
    }
  }, [searchTerm, availableEmployees]);

  const loadEmployees = async () => {
    setIsLoading(true);
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 500));
      setAvailableEmployees(mockEmployees);
      setFilteredEmployees(mockEmployees);
    } catch (error) {
      console.error('Failed to load employees:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddEmployee = (employee) => {
    if (selectedEmployees.length < 4 && !selectedEmployees.find(emp => emp.id === employee.id)) {
      setSelectedEmployees([...selectedEmployees, employee]);
    }
  };

  const handleRemoveEmployee = (employeeId) => {
    setSelectedEmployees(selectedEmployees.filter(emp => emp.id !== employeeId));
  };

  const getAllSkills = () => {
    const skillsMap = new Map();
    selectedEmployees.forEach(employee => {
      employee.skills.forEach(skill => {
        if (!skillsMap.has(skill.name)) {
          skillsMap.set(skill.name, {
            name: skill.name,
            category: skill.category || 'General',
            employeeSkills: {}
          });
        }
        skillsMap.get(skill.name).employeeSkills[employee.id] = skill.proficiency;
      });
    });
    return Array.from(skillsMap.values()).sort((a, b) => a.name.localeCompare(b.name));
  };
  const getProficiencyColor = (proficiency) => {
    if (proficiency === undefined) return 'bg-slate-200 text-slate-400';
    if (proficiency >= 4) return 'bg-green-500 text-white';
    if (proficiency >= 3) return 'bg-blue-500 text-white';
    if (proficiency >= 2) return 'bg-yellow-500 text-white';
    return 'bg-red-500 text-white';
  };

  if (isLoading) {
    return <LoadingState message="Loading employees for comparison..." />;
  }

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-screen-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Employee Comparison</h1>
          <p className="text-slate-600">
            Compare skills and proficiencies across team members (max 4 employees)
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Employee Selection */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Select Employees</h2>
              
              {/* Search */}
              <div className="mb-4">
                <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search employees..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Selected Employees */}
            {selectedEmployees.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Selected ({selectedEmployees.length}/4)
                </h3>
                <div className="space-y-2">
                  {selectedEmployees.map(employee => (
                    <div
                      key={employee.id}
                      className="flex items-center justify-between p-2 bg-blue-50 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-gray-900">{employee.name}</div>
                        <div className="text-sm text-gray-600">{employee.role}</div>
                      </div>
                      <button
                        onClick={() => handleRemoveEmployee(employee.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Available Employees */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Available Employees</h3>
              <div className="max-h-64 overflow-y-auto space-y-1">
                {filteredEmployees
                  .filter(emp => !selectedEmployees.find(selected => selected.id === emp.id))
                  .map(employee => (
                    <button
                      key={employee.id}
                      onClick={() => handleAddEmployee(employee)}
                      disabled={selectedEmployees.length >= 4}
                      className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-50 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div>
                        <div className="font-medium text-gray-900">{employee.name}</div>
                        <div className="text-sm text-gray-600">{employee.role} • {employee.team}</div>
                      </div>
                      <Plus className="h-4 w-4 text-gray-400" />
                    </button>
                  ))}
              </div>
            </div>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="border-b border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Skills Comparison
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Side-by-side comparison of skill proficiencies
              </p>
            </div>

            <div className="p-6">
              {selectedEmployees.length === 0 ? (
                <EmptyState
                  icon={Users}
                  title="No employees selected"
                  description="Select 2-4 employees from the left panel to compare their skills"
                />
              ) : selectedEmployees.length === 1 ? (
                <EmptyState
                  icon={ArrowUpDown}
                  title="Add more employees"
                  description="Select at least 2 employees to enable skill comparison"
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-700">Skill</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-700">Category</th>
                        {selectedEmployees.map(employee => (
                          <th key={employee.id} className="text-center py-3 px-4 font-medium text-gray-700 min-w-24">
                            <div className="truncate">{employee.name}</div>
                            <div className="text-xs text-gray-500 font-normal">{employee.role}</div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {getAllSkills().map(skill => (
                        <tr key={skill.name} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-4 px-4">
                            <div className="font-medium text-gray-900">{skill.name}</div>
                          </td>
                          <td className="py-4 px-4">
                            <span className="text-sm text-gray-600">{skill.category}</span>
                          </td>
                          {selectedEmployees.map(employee => {
                            const proficiency = skill.employeeSkills[employee.id];
                            return (
                              <td key={employee.id} className="py-4 px-4 text-center">
                                {proficiency !== undefined ? (
                                  <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${getProficiencyColor(proficiency)}`}>
                                    {proficiency}
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium bg-gray-100 text-gray-400">
                                    -
                                  </span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {getAllSkills().length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <p>No skills data available for comparison</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Legend */}
          {selectedEmployees.length >= 2 && (
            <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Proficiency Legend</h3>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium bg-red-500 text-white">1</span>
                  <span className="text-sm text-gray-600">Beginner</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium bg-yellow-500 text-white">2</span>
                  <span className="text-sm text-gray-600">Basic</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium bg-blue-500 text-white">3</span>
                  <span className="text-sm text-gray-600">Intermediate</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium bg-blue-500 text-white">4</span>
                  <span className="text-sm text-gray-600">Advanced</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium bg-green-500 text-white">5</span>
                  <span className="text-sm text-gray-600">Expert</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium bg-gray-200 text-gray-400">-</span>
                  <span className="text-sm text-gray-600">No data</span>
                </div>
              </div>
            </div>
          )}
        </div>        </div>
      </div>
    </div>
  );
};

export default ComparisonPage;
