import React, { useState, useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, FileDown } from 'lucide-react';
import { employeeApi } from '../services/api/employeeApi';
import employeeProfilePdfExportService from '../services/employeeProfilePdfExportService';

/**
 * Right-side sliding drawer for employee profile quick view
 * 
 * @param {boolean} isOpen - Whether drawer is open
 * @param {Function} onClose - Close handler
 * @param {number} employeeId - Current employee ID to display
 * @param {Array} employees - Full list of employees from table
 * @param {number} currentIndex - Current employee index in the list
 * @param {Function} onNavigate - Handler for prev/next navigation
 */
const EmployeeProfileDrawer = ({ 
  isOpen, 
  onClose, 
  employeeId, 
  employees = [],
  currentIndex = 0,
  onNavigate 
}) => {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  // Handle slide-in animation
  useEffect(() => {
    if (isOpen) {
      // Trigger slide-in animation after a brief delay to ensure CSS transition works
      setTimeout(() => setIsAnimating(true), 10);
    } else {
      setIsAnimating(false);
    }
  }, [isOpen]);

  // Fetch employee profile when drawer opens or employeeId changes
  useEffect(() => {
    if (isOpen && employeeId) {
      fetchProfile(employeeId);
    }
  }, [isOpen, employeeId]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const fetchProfile = async (empId) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await employeeApi.getEmployeeProfile(empId);
      setProfile(data);
    } catch (err) {
      console.error('Failed to fetch employee profile:', err);
      setError('Failed to load employee profile');
      setProfile(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      onNavigate(currentIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < employees.length - 1) {
      onNavigate(currentIndex + 1);
    }
  };
  const handleExportPDF = async () => {
    if (!profile || !employees[currentIndex]) return;
    
    setIsExporting(true);
    try {
      // Reuse the same PDF export method used in MyProfilePage
      await employeeProfilePdfExportService.exportEmployeeProfile(profile, employees[currentIndex]);
    } catch (err) {
      console.error('PDF export failed:', err);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const renderStars = (level) => {
    const stars = '★'.repeat(level) + '☆'.repeat(5 - level);
    return stars;
  };

  const getBadgeColor = (proficiency) => {
    if (proficiency >= 5) return 'bg-green-100 text-green-700';
    if (proficiency >= 4) return 'bg-blue-100 text-blue-700';
    if (proficiency >= 3) return 'bg-yellow-100 text-yellow-700';
    if (proficiency >= 2) return 'bg-orange-100 text-orange-700';
    return 'bg-gray-100 text-gray-700';
  };

  const getMostRecentUpdate = (skills) => {
    if (!skills || skills.length === 0) return null;
    const dates = skills
      .map(s => s.lastUpdated)
      .filter(Boolean)
      .map(d => new Date(d));
    return dates.length > 0 ? new Date(Math.max(...dates)) : null;
  };  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className={`fixed inset-0 bg-black/30 z-40 transition-opacity duration-300 ${
          isAnimating ? 'opacity-100' : 'opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div 
        className={`fixed top-0 right-0 h-full w-[450px] bg-white shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out ${
          isAnimating ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="border-b border-slate-200 p-6 flex-shrink-0">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>

          {isLoading ? (
            <div className="text-slate-400">Loading...</div>
          ) : error ? (
            <div className="text-red-600">{error}</div>
          ) : profile ? (
            <>
              <h2 className="text-xl font-semibold text-slate-900 mb-1 pr-8">
                {profile.employee_name || 'Unknown Employee'}
              </h2>
              <div className="text-sm text-slate-600 space-y-1">
                <div>ZID: {employees[currentIndex]?.zid || profile.employee_id || 'N/A'}</div>
                <div>{profile.role || 'N/A'}</div>
                <div className="text-slate-500">
                  {[
                    profile.organization?.sub_segment,
                    profile.organization?.team,
                    profile.organization?.project
                  ].filter(Boolean).join(' • ')}
                </div>
              </div>
            </>
          ) : (
            <div className="text-slate-400">No employee selected</div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-slate-400">Loading profile...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-red-600 text-sm">{error}</div>
            </div>
          ) : profile ? (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {profile.total_skills || 0}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">Total Skills</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {profile.skills?.filter(s => s.certification && s.certification.trim() !== '').length || 0}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">Certified</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-3 text-center">
                  <div className="text-sm font-bold text-purple-600">
                    {formatDate(getMostRecentUpdate(profile.skills))}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">Last Update</div>
                </div>
              </div>

              {/* Core Expertise */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <span>🌟</span>
                  Core Expertise
                </h3>
                <div className="flex flex-wrap gap-2">
                  {profile.skills && profile.skills.length > 0 ? (
                    profile.skills
                      .filter(skill => skill.proficiencyLevelId >= 4)
                      .sort((a, b) => b.proficiencyLevelId - a.proficiencyLevelId)
                      .slice(0, 8)
                      .map((skill, index) => (
                        <div
                          key={index}
                          className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 ${getBadgeColor(skill.proficiencyLevelId)}`}
                        >
                          <span>{skill.skillName}</span>
                          <span className="text-yellow-600 text-xs">{renderStars(skill.proficiencyLevelId)}</span>
                        </div>
                      ))
                  ) : (
                    <div className="text-slate-400 text-sm">No core expertise available</div>
                  )}
                </div>
              </div>

              {/* Skills Preview Table */}
              <div>
                <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <span>📊</span>
                  Skills Overview ({profile.skills?.length || 0})
                </h3>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-slate-600">Skill</th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-slate-600">Category</th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-slate-600">Level</th>
                      </tr>
                    </thead>
                    <tbody>
                      {profile.skills && profile.skills.length > 0 ? (
                        profile.skills.slice(0, 8).map((skill, index) => (
                          <tr key={index} className="border-t border-slate-100 hover:bg-slate-50">
                            <td className="py-2 px-3 text-xs font-medium text-slate-900">
                              {skill.skillName}
                            </td>
                            <td className="py-2 px-3">
                              <span className="text-xs bg-slate-100 px-2 py-0.5 rounded text-slate-600">
                                {skill.category || '—'}
                              </span>
                            </td>
                            <td className="py-2 px-3">
                              <span className="text-yellow-500 text-xs">
                                {renderStars(skill.proficiencyLevelId || 0)}
                              </span>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="3" className="py-6 text-center text-slate-400 text-sm">
                            No skills data available
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                  {profile.skills && profile.skills.length > 8 && (
                    <div className="bg-slate-50 py-2 px-3 text-center text-xs text-slate-600 border-t border-slate-200">
                      +{profile.skills.length - 8} more skills
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-32">
              <div className="text-slate-400 text-sm">No profile data</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 p-4 flex-shrink-0 space-y-3">
          {/* Navigation Buttons */}
          <div className="flex gap-2 justify-center">
            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className="flex items-center gap-1 px-4 py-2 border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex >= employees.length - 1}
              className="flex items-center gap-1 px-4 py-2 border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          {/* Export Button */}
          <button
            onClick={handleExportPDF}
            disabled={isExporting || !profile}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-md text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <FileDown className="h-4 w-4" />
            {isExporting ? 'Exporting...' : 'Export Profile (PDF)'}
          </button>
        </div>
      </div>
    </>
  );
};

export default EmployeeProfileDrawer;
