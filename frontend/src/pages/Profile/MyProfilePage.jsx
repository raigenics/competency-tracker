import React, { useState, useEffect } from 'react';
import { User, Edit, Save, X } from 'lucide-react';
import SkillsTable from './components/SkillsTable';
import LoadingState from '../../components/LoadingState';
import { employeeApi } from '../../services/api/employeeApi';

const MyProfilePage = () => {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setIsLoading(true);
    try {
      // TODO: Get current user ID from auth context
      const currentUserId = 1; // Mock current user ID
      const profileData = await employeeApi.getEmployeeProfile(currentUserId);
      setProfile(profileData);
      setEditedProfile(profileData);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = () => {
    setEditedProfile({ ...profile });
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock API call
      setProfile(editedProfile);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setEditedProfile({ ...profile });
    setIsEditing(false);
  };

  const handleProfileChange = (field, value) => {
    setEditedProfile({
      ...editedProfile,
      [field]: value
    });
  };

  if (isLoading && !profile) {
    return <LoadingState message="Loading your profile..." />;
  }
  if (!profile) {
    return (
      <div className="p-8 bg-slate-50 min-h-screen">
        <div className="max-w-screen-2xl mx-auto">
          <div className="text-center py-8">
            <p className="text-slate-600">Failed to load profile. Please try again.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-screen-2xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-slate-900">My Profile</h1>
          {!isEditing ? (
            <button
              onClick={handleEdit}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Edit className="h-4 w-4" />
              Edit Profile
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                {isLoading ? 'Saving...' : 'Save'}
              </button>              <button
                onClick={handleCancel}
                className="flex items-center gap-2 px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                <X className="h-4 w-4" />
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Information */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="text-center mb-6">
              <div className="w-24 h-24 bg-slate-300 rounded-full mx-auto mb-4 flex items-center justify-center">
                <User className="h-12 w-12 text-slate-600" />
              </div>
              {!isEditing ? (
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">{profile.name}</h2>
                  <p className="text-slate-600">{profile.role}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={editedProfile.name}
                    onChange={(e) => handleProfileChange('name', e.target.value)}
                    className="w-full text-center text-xl font-semibold px-3 py-1 border border-slate-300 rounded"
                    placeholder="Full Name"
                  />
                  <input
                    type="text"
                    value={editedProfile.role}
                    onChange={(e) => handleProfileChange('role', e.target.value)}
                    className="w-full text-center text-slate-600 px-3 py-1 border border-slate-300 rounded"
                    placeholder="Job Title"
                  />
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Team</label>
                {!isEditing ? (
                  <p className="text-slate-900">{profile.team}</p>
                ) : (
                  <input
                    type="text"
                    value={editedProfile.team}
                    onChange={(e) => handleProfileChange('team', e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Team"
                  />
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                {!isEditing ? (
                  <p className="text-slate-900">{profile.email}</p>
                ) : (
                  <input
                    type="email"
                    value={editedProfile.email}
                    onChange={(e) => handleProfileChange('email', e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Email"
                  />
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
                {!isEditing ? (
                  <p className="text-slate-900">{profile.location || 'Not specified'}</p>
                ) : (
                  <input
                    type="text"
                    value={editedProfile.location || ''}
                    onChange={(e) => handleProfileChange('location', e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Location"
                  />
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Years of Experience</label>
                {!isEditing ? (
                  <p className="text-slate-900">{profile.yearsExperience || 'Not specified'}</p>
                ) : (
                  <input
                    type="number"
                    value={editedProfile.yearsExperience || ''}
                    onChange={(e) => handleProfileChange('yearsExperience', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Years"
                    min="0"
                    max="50"
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Skills Section */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-slate-200">
            <div className="border-b border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900">My Skills</h3>
              <p className="text-sm text-slate-600 mt-1">
                Manage your skill proficiencies and track your progress
              </p>
            </div>
            <div className="p-6">
              <SkillsTable 
                employeeId={profile.id} 
                skills={profile.skills} 
                isEditable={true}
                onSkillUpdate={loadProfile}
              />
            </div>
          </div>
        </div>        </div>
      </div>
    </div>
  );
};

export default MyProfilePage;
