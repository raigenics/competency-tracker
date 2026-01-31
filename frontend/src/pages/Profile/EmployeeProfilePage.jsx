import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { User, Mail, MapPin, Calendar, Users } from 'lucide-react';
import SkillsTable from './components/SkillsTable';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';
import { employeeApi } from '../../services/api/employeeApi';

const EmployeeProfilePage = () => {
  const { id } = useParams();
  
  const [employee, setEmployee] = useState(null);
  const [isLoading, setIsLoading] = useState(!!id); // Only show loading if ID is present
  const [error, setError] = useState(null);

  useEffect(() => {
    if (id) {
      loadEmployee();
    } else {
      // No ID provided - set loading to false to show search/empty state
      setIsLoading(false);
    }
  }, [id]);

  const loadEmployee = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const employeeData = await employeeApi.getEmployeeProfile(parseInt(id));
      setEmployee(employeeData);
    } catch (error) {
      console.error('Failed to load employee:', error);
      setError('Failed to load employee profile');
    } finally {
      setIsLoading(false);
    }  };
  
  if (isLoading) {
    return <LoadingState message="Loading employee profile..." />;
  }
  
  // Show error only if there was an actual error OR if ID was provided but employee not found
  if (error || (id && !employee)) {
    return (
      <div className="p-8 bg-slate-50 min-h-screen">
        <div className="max-w-screen-2xl mx-auto">
          <EmptyState
            icon={User}
            title="Employee not found"
            description={error || "The requested employee profile could not be found."}
          />
        </div>
      </div>
    );
  }
  
  // No ID provided and no employee - show message to use URL
  if (!id && !employee) {
    return (
      <div className="p-8 bg-slate-50 min-h-screen">
        <div className="max-w-screen-2xl mx-auto">
          <EmptyState
            icon={User}
            title="No employee selected"
            description="Please use a valid employee profile URL."
          />
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-screen-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900">Employee Profile</h1>
          <p className="text-slate-600">View detailed information about this team member</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Information */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="text-center mb-6">
                <div className="w-24 h-24 bg-slate-300 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <User className="h-12 w-12 text-slate-600" />
                </div>
                <h2 className="text-xl font-semibold text-slate-900">{employee.name}</h2>
                <p className="text-slate-600">{employee.role}</p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-3 text-slate-600">
                  <Users className="h-5 w-5 flex-shrink-0" />
                  <div>
                    <div className="text-sm text-slate-500">Team</div>
                    <div className="font-medium text-slate-900">{employee.team}</div>
                  </div>
                </div>

                {employee.email && (
                  <div className="flex items-center gap-3 text-slate-600">
                    <Mail className="h-5 w-5 flex-shrink-0" />
                    <div>
                      <div className="text-sm text-slate-500">Email</div>
                      <div className="font-medium text-slate-900">{employee.email}</div>
                    </div>
                  </div>
                )}

                {employee.location && (
                  <div className="flex items-center gap-3 text-slate-600">
                    <MapPin className="h-5 w-5 flex-shrink-0" />
                    <div>
                      <div className="text-sm text-slate-500">Location</div>
                      <div className="font-medium text-slate-900">{employee.location}</div>
                    </div>
                  </div>
                )}

                {employee.yearsExperience && (                  <div className="flex items-center gap-3 text-slate-600">
                    <Calendar className="h-5 w-5 flex-shrink-0" />
                    <div>
                      <div className="text-sm text-slate-500">Experience</div>
                      <div className="font-medium text-slate-900">{employee.yearsExperience} years</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Skills Summary */}
              <div className="mt-6 pt-6 border-t border-slate-200">
                <h3 className="font-semibold text-slate-900 mb-3">Skills Overview</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-center">
                    <div className="font-semibold text-2xl text-blue-600">{employee.skills?.length || 0}</div>
                    <div className="text-slate-600">Total Skills</div>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-2xl text-green-600">
                      {employee.skills?.filter(s => s.proficiency >= 4).length || 0}
                    </div>
                    <div className="text-slate-600">Expert Level</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Skills Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-slate-200">
              <div className="border-b border-slate-200 p-6">
                <h3 className="text-lg font-semibold text-slate-900">Skills & Proficiencies</h3>
                <p className="text-sm text-slate-600 mt-1">
                  Detailed breakdown of technical and professional skills
                </p>
              </div>
              <div className="p-6">
                <SkillsTable 
                  employeeId={employee.id} 
                  skills={employee.skills} 
                  isEditable={false}
                  showHistory={true}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeProfilePage;
