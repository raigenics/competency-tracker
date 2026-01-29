import ExcelJS from 'exceljs';
import { downloadExcelFile, generateTimestamp } from './talentExportService';

/**
 * Service for exporting employee profile data to Excel
 * Reuses existing export utilities from talentExportService
 */

/**
 * Exports employee profile data to Excel
 * @param {Object} employeeProfile - The employee profile data
 * @param {Object} selectedEmployee - The selected employee basic info
 * @returns {Promise<void>}
 */
export const exportEmployeeProfile = async (employeeProfile, selectedEmployee) => {
  if (!employeeProfile || !selectedEmployee) {
    throw new Error('Employee profile data is required for export');
  }

  try {
    const workbook = new ExcelJS.Workbook();
    
    // Set workbook properties
    workbook.creator = 'Competency Tracker';
    workbook.lastModifiedBy = 'Competency Tracker';
    workbook.created = new Date();
    workbook.modified = new Date();

    // Create Employee Profile sheet
    const profileSheet = workbook.addWorksheet('Employee Profile');
    
    // Define column widths
    profileSheet.columns = [
      { width: 25 },
      { width: 40 }
    ];

    // Title
    profileSheet.mergeCells('A1:B1');
    const titleCell = profileSheet.getCell('A1');
    titleCell.value = 'Employee Competency Profile';
    titleCell.font = { size: 16, bold: true, color: { argb: 'FFFFFFFF' } };
    titleCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF2563EB' } };
    titleCell.alignment = { horizontal: 'center', vertical: 'middle' };
    profileSheet.getRow(1).height = 30;

    // Employee Information Section
    let currentRow = 3;
    const addHeaderRow = (sheet, row, label) => {
      sheet.mergeCells(`A${row}:B${row}`);
      const cell = sheet.getCell(`A${row}`);
      cell.value = label;
      cell.font = { size: 12, bold: true, color: { argb: 'FF1E293B' } };
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF1F5F9' } };
      cell.alignment = { horizontal: 'left', vertical: 'middle' };
      sheet.getRow(row).height = 25;
    };

    const addDataRow = (sheet, row, label, value) => {
      const labelCell = sheet.getCell(`A${row}`);
      labelCell.value = label;
      labelCell.font = { bold: true, color: { argb: 'FF64748B' } };
      labelCell.alignment = { horizontal: 'left', vertical: 'middle' };
      
      const valueCell = sheet.getCell(`B${row}`);
      valueCell.value = value || 'N/A';
      valueCell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
      sheet.getRow(row).height = 20;
    };

    addHeaderRow(profileSheet, currentRow, 'Employee Information');
    currentRow++;
    
    addDataRow(profileSheet, currentRow++, 'Name', employeeProfile.employee_name);
    addDataRow(profileSheet, currentRow++, 'ZID', selectedEmployee.zid);
    addDataRow(profileSheet, currentRow++, 'Role', employeeProfile.role);
    addDataRow(profileSheet, currentRow++, 'Sub-Segment', employeeProfile.organization?.sub_segment);
    addDataRow(profileSheet, currentRow++, 'Project', employeeProfile.organization?.project);
    addDataRow(profileSheet, currentRow++, 'Team', employeeProfile.organization?.team);
    
    // Format date if available
    const startDate = employeeProfile.start_date_of_working 
      ? new Date(employeeProfile.start_date_of_working).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
      : 'N/A';
    addDataRow(profileSheet, currentRow++, 'Started Working', startDate);

    // Calculate experience
    let experienceText = 'N/A';
    if (employeeProfile.start_date_of_working) {
      const startDateObj = new Date(employeeProfile.start_date_of_working);
      const today = new Date();
      let years = today.getFullYear() - startDateObj.getFullYear();
      let months = today.getMonth() - startDateObj.getMonth();
      if (months < 0) {
        years--;
        months += 12;
      }
      experienceText = years === 0 
        ? `${months} month${months !== 1 ? 's' : ''}`
        : months === 0 
          ? `${years} year${years !== 1 ? 's' : ''}`
          : `${years} year${years !== 1 ? 's' : ''} ${months} month${months !== 1 ? 's' : ''}`;
    }
    addDataRow(profileSheet, currentRow++, 'Experience', experienceText);

    // Summary Metrics Section
    currentRow++;
    addHeaderRow(profileSheet, currentRow, 'Summary Metrics');
    currentRow++;

    const certifiedSkillsCount = employeeProfile.skills?.filter(s => s.certification && s.certification.trim() !== '').length || 0;
    const recentlyUpdatedCount = employeeProfile.skills?.filter(s => {
      if (!s.lastUpdated) return false;
      const lastUpdated = new Date(s.lastUpdated);
      const ninetyDaysAgo = new Date();
      ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
      return lastUpdated >= ninetyDaysAgo;
    }).length || 0;

    addDataRow(profileSheet, currentRow++, 'Total Skills', employeeProfile.total_skills || 0);
    addDataRow(profileSheet, currentRow++, 'Certified Skills', certifiedSkillsCount);
    addDataRow(profileSheet, currentRow++, 'Recently Updated Skills (90 days)', recentlyUpdatedCount);

    // Skills Details Sheet
    const skillsSheet = workbook.addWorksheet('Skills Details');
    
    // Skills table header
    const headerRow = skillsSheet.getRow(1);
    const headers = ['Skill Name', 'Category', 'Proficiency', 'Stars', 'Years Exp', 'Last Used', 'Certification'];
    headers.forEach((header, index) => {
      const cell = headerRow.getCell(index + 1);
      cell.value = header;
      cell.font = { bold: true, color: { argb: 'FFFFFFFF' } };
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF2563EB' } };
      cell.alignment = { horizontal: 'center', vertical: 'middle' };
    });
    headerRow.height = 25;

    // Define column widths
    skillsSheet.columns = [
      { width: 30 }, // Skill Name
      { width: 20 }, // Category
      { width: 15 }, // Proficiency
      { width: 10 }, // Stars
      { width: 12 }, // Years Exp
      { width: 15 }, // Last Used
      { width: 30 }  // Certification
    ];

    // Add skills data
    const skills = employeeProfile.skills || [];    skills.forEach((skill, index) => {
      const row = skillsSheet.getRow(index + 2);
      const stars = '★'.repeat(skill.proficiencyLevelId || 0) + '☆'.repeat(5 - (skill.proficiencyLevelId || 0));
      
      row.getCell(1).value = skill.skillName || skill.name || '–';
      row.getCell(2).value = skill.category || '–';
      row.getCell(3).value = skill.proficiency || '–';
      row.getCell(4).value = stars;
      row.getCell(5).value = skill.yearsOfExperience || 0;
      row.getCell(6).value = skill.lastUsed 
        ? new Date(skill.lastUsed).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
        : '–';
      row.getCell(7).value = (skill.certification && skill.certification.trim() !== '') ? skill.certification : '-';
      
      // Alternating row colors
      if (index % 2 === 1) {
        row.eachCell((cell) => {
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8FAFC' } };
        });
      }
      
      row.alignment = { vertical: 'middle' };
      row.height = 20;
    });

    // Add borders to skills table
    const lastRow = skills.length + 1;
    for (let row = 1; row <= lastRow; row++) {
      for (let col = 1; col <= 7; col++) {
        const cell = skillsSheet.getCell(row, col);
        cell.border = {
          top: { style: 'thin', color: { argb: 'FFE2E8F0' } },
          left: { style: 'thin', color: { argb: 'FFE2E8F0' } },
          bottom: { style: 'thin', color: { argb: 'FFE2E8F0' } },
          right: { style: 'thin', color: { argb: 'FFE2E8F0' } }
        };
      }
    }

    // Generate Excel file
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    
    // Create filename
    const employeeName = employeeProfile.employee_name.replace(/\s+/g, '_');
    const timestamp = generateTimestamp();
    const filename = `employee_profile_${employeeName}_${timestamp}.xlsx`;
    
    // Download file using existing utility
    downloadExcelFile(blob, filename);
  } catch (error) {
    console.error('Failed to export employee profile:', error);
    throw new Error('Failed to generate Excel file: ' + error.message);
  }
};

const employeeProfileExportService = {
  exportEmployeeProfile
};

export default employeeProfileExportService;
