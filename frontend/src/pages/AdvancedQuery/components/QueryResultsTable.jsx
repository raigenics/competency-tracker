import React, { useState } from 'react';
import { User, ArrowUpDown, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const QueryResultsTable = ({ results }) => {
  const navigate = useNavigate();
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedResults = [...results].sort((a, b) => {
    if (sortConfig.key === 'name') {
      const aValue = a.name.toLowerCase();
      const bValue = b.name.toLowerCase();
      return sortConfig.direction === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    } else if (sortConfig.key === 'subSegment') {
      const aValue = (a.subSegment || '').toLowerCase();
      const bValue = (b.subSegment || '').toLowerCase();
      return sortConfig.direction === 'asc'
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    } else if (sortConfig.key === 'role') {
      const aValue = a.role.toLowerCase();
      const bValue = b.role.toLowerCase();
      return sortConfig.direction === 'asc'
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    } else if (sortConfig.key === 'team') {
      const aValue = a.team.toLowerCase();
      const bValue = b.team.toLowerCase();
      return sortConfig.direction === 'asc'
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }
    return 0;
  });
  const getProficiencyColor = (proficiency) => {
    if (proficiency >= 4) return 'text-green-600 bg-green-100';
    if (proficiency >= 3) return 'text-blue-600 bg-blue-100';
    if (proficiency >= 2) return 'text-yellow-600 bg-yellow-100';
    return 'text-gray-600 bg-gray-100';
  };

  const SortButton = ({ column, children }) => (
    <button
      onClick={() => handleSort(column)}
      className="flex items-center gap-1 font-medium text-gray-900 hover:text-blue-600"
    >
      {children}
      <ArrowUpDown className="h-4 w-4" />
    </button>
  );

  const handleViewProfile = (employeeId) => {
    navigate(`/profile/employee/${employeeId}`);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4">
              <SortButton column="name">Employee</SortButton>
            </th>
            <th className="text-left py-3 px-4">
              <SortButton column="subSegment">Sub-Segment</SortButton>
            </th>
            <th className="text-left py-3 px-4">
              <SortButton column="role">Role</SortButton>
            </th>
            <th className="text-left py-3 px-4">
              <SortButton column="team">Team</SortButton>
            </th>
            <th className="text-left py-3 px-4">Skills</th>
            <th className="text-left py-3 px-4">Actions</th>
          </tr>
        </thead>        <tbody>
          {sortedResults.map((employee) => (
            <tr key={employee.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-4 px-4">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                    <User className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{employee.name}</div>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4">
                <div className="text-sm text-gray-900">{employee.subSegment || '—'}</div>
              </td>
              <td className="py-4 px-4">
                <div className="text-sm text-gray-900">{employee.role}</div>
              </td>
              <td className="py-4 px-4">
                <div className="text-sm text-gray-900">{employee.team}</div>
              </td>
              <td className="py-4 px-4">
                <div className="flex flex-wrap gap-1">
                  {employee.skills.slice(0, 3).map((skill, index) => (
                    <span
                      key={index}
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getProficiencyColor(skill.proficiency)}`}
                    >
                      {skill.name} ({skill.proficiency})
                    </span>
                  ))}
                  {employee.skills.length > 3 && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-gray-600 bg-gray-100">
                      +{employee.skills.length - 3} more
                    </span>
                  )}
                </div>
              </td>
              <td className="py-4 px-4">
                <button
                  onClick={() => handleViewProfile(employee.id)}
                  className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  <Eye className="h-4 w-4" />
                  View Profile
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {sortedResults.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No employees found matching your criteria
        </div>
      )}
    </div>
  );
};

export default QueryResultsTable;
