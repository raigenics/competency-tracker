import React, { useState, useEffect } from 'react';
import { Info, Users, Award, ArrowRight, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { skillApi } from '../../../services/api/skillApi';
import { employeeApi } from '../../../services/api/employeeApi';
import TalentResultsTable from '../../../components/TalentResultsTable';
import TalentExportMenu from '../../../components/TalentExportMenu';
import talentExportService from '../../../services/talentExportService';

const SkillDetailsPanel = ({ skill, showViewAll = false, onViewAll, onBackToSummary }) => {
  const [summaryData, setSummaryData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [employeeResults, setEmployeeResults] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(null);
  const navigate = useNavigate();  // Fetch skill summary when skill changes
  useEffect(() => {
    // Normalize skill ID - handle both 'id' (from mock data) and 'skill_id' (from API)
    const skillId = skill?.skill_id || skill?.id;
    
    if (!skill || !skillId) {
      setSummaryData(null);
      return;
    }

    const fetchSummary = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await skillApi.getSkillSummary(skillId);
        setSummaryData(data);
      } catch (err) {
        console.error('Error fetching skill summary:', err);
        setError(err.message || 'Failed to load skill data');
        setSummaryData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, [skill]);

  // Fetch employee details when "View All" is shown
  useEffect(() => {
    if (showViewAll && summaryData?.employee_ids?.length > 0) {
      const fetchEmployees = async () => {
        setIsLoading(true);
        try {
          const results = await employeeApi.getEmployeesByIds(summaryData.employee_ids);
          setEmployeeResults(results);
        } catch (err) {
          console.error('Error fetching employees:', err);
          setError(err.message || 'Failed to load employees');
          setEmployeeResults([]);
        } finally {
          setIsLoading(false);
        }
      };
      fetchEmployees();
    }
  }, [showViewAll, summaryData]);

  // Clear selection when results change
  useEffect(() => {
    setSelectedIds(new Set());
  }, [employeeResults]);

  const handleSelectionChange = (newSelection) => {
    setSelectedIds(newSelection);
  };

  const handleExportAll = async () => {
    setIsExporting(true);
    setExportError(null);
    
    try {
      // Create a mock filters object with just the skill name
      const filters = {
        skills: [skill.name],
        subSegment: 'all',
        team: '',
        role: '',
        proficiency: { min: 0, max: 5 },
        experience: { min: 0, max: 20 }
      };
      await talentExportService.exportAllTalent(filters, `skill_${skill.name.replace(/\s+/g, '_')}_all`);
    } catch (err) {
      console.error('Export all failed:', err);
      setExportError(err.message || 'Failed to export results');
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportSelected = async () => {
    setIsExporting(true);
    setExportError(null);
    
    try {
      const selectedEmployeeIds = Array.from(selectedIds);
      const filters = {
        skills: [skill.name],
        subSegment: 'all',
        team: '',
        role: '',
        proficiency: { min: 0, max: 5 },
        experience: { min: 0, max: 20 }
      };
      await talentExportService.exportSelectedTalent(filters, selectedEmployeeIds, `skill_${skill.name.replace(/\s+/g, '_')}_selected`);
    } catch (err) {
      console.error('Export selected failed:', err);
      setExportError(err.message || 'Failed to export selected results');
    } finally {
      setIsExporting(false);
    }
  };

  const handleViewAllClick = () => {
    if (onViewAll) {
      onViewAll();
    }
  };

  const handleBackClick = () => {
    if (onBackToSummary) {
      onBackToSummary();
    }
  };  if (!skill) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-8">
          <Info className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">Select a skill</h3>
          <p className="text-sm text-gray-500">
            Click on any skill from the capability structure to view insights
          </p>
        </div>
      </div>
    );
  }

  // Show "View All" results view
  if (showViewAll) {
    return (
      <div className="bg-white rounded-lg border border-gray-200">
        {/* Header with Back button */}
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={handleBackClick}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Summary
            </button>
            <TalentExportMenu
              totalCount={employeeResults.length}
              selectedCount={selectedIds.size}
              onExportAll={handleExportAll}
              onExportSelected={handleExportSelected}
              isExporting={isExporting}
              exportError={exportError}
            />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Employees with {skill.name}</h2>
            <p className="text-sm text-gray-600 mt-1">
              {employeeResults.length} {employeeResults.length === 1 ? 'employee' : 'employees'} found
            </p>
          </div>        </div>

        {/* Results Table */}
        <div className="p-6">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-gray-600">Loading employees...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600 mb-2">Failed to load employees</p>
              <p className="text-sm text-gray-500">{error}</p>
            </div>
          ) : employeeResults.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">No employees found with this skill</p>
            </div>          ) : (
            <TalentResultsTable
              results={employeeResults}
              selectedIds={selectedIds}
              onSelectionChange={handleSelectionChange}
            />
          )}
        </div>
      </div>
    );
  }
  // Show summary view (default)
  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">{skill.name}</h2>
            <p className="text-sm text-gray-600">
              {typeof skill.category === 'object' && skill.category?.category_name 
                ? skill.category.category_name 
                : skill.category || 'General'}
            </p>
          </div>
          {skill.isCore && (
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
              <Award className="h-3 w-3" />
              Core Skill
            </span>
          )}        </div>
      </div>      <div className="p-6 space-y-6">
        {/* Statistics - Always Show Data (0 if loading/error) */}
        {isLoading ? (
          <div>
            <div className="grid grid-cols-2 gap-4">
              {[1, 2].map((i) => (
                <div key={i} className="text-center p-4 bg-gray-50 rounded-lg animate-pulse">
                  <div className="h-5 w-5 mx-auto mb-2 bg-gray-300 rounded"></div>
                  <div className="h-6 w-12 mx-auto mb-1 bg-gray-300 rounded"></div>
                  <div className="h-3 w-20 mx-auto bg-gray-300 rounded"></div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Users className="h-5 w-5 mx-auto mb-2 text-blue-600" />
                <div className="text-2xl font-semibold text-gray-900">
                  {summaryData?.employee_count ?? 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Employees</div>
              </div>              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Award className="h-5 w-5 mx-auto mb-2 text-purple-600" />
                <div className="text-2xl font-semibold text-gray-900">
                  {summaryData?.certified_employee_count ?? summaryData?.certified_count ?? 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Certified</div>
              </div>
            </div>
          </div>
        )}        {/* CTA Button - Always Visible */}
        <div>
          <button
            onClick={handleViewAllClick}
            disabled={isLoading || (summaryData?.employee_count ?? 0) === 0}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-colors font-medium ${
              isLoading || (summaryData?.employee_count ?? 0) === 0
                ? 'bg-blue-400 cursor-not-allowed text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            View All with {skill.name}
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SkillDetailsPanel;
