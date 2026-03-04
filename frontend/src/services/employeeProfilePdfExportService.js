/**
 * Employee Profile PDF Export Service
 * 
 * Generates a professional PDF export of an employee's profile including:
 * - Identity section (name, ZID, organization details)
 * - Summary metrics (Total Skills, Certified Skills, etc.)
 * - Core Expertise (top skills with proficiency)
 * - All Skills table with pagination
 * 
 * Uses jsPDF and jsPDF-AutoTable for PDF generation.
 * This is a separate, isolated module that does not affect existing functionality.
 */

import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

class EmployeeProfilePdfExportService {
  /**
   * Export employee profile to PDF
   * @param {Object} employeeProfile - The employee profile data
   * @param {Object} selectedEmployee - The selected employee info (includes ZID)
   * @returns {Promise<void>}
   */
  async exportEmployeeProfile(employeeProfile, selectedEmployee) {
    if (!employeeProfile || !selectedEmployee) {
      throw new Error('Employee profile data is required for PDF export');
    }

    try {
      // Create new PDF document (A4 portrait)
      const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      });

      // Page dimensions
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 15;
      let yPosition = margin;

      // Color scheme
      const colors = {
        primary: [37, 99, 235], // blue-600
        secondary: [71, 85, 105], // slate-600
        lightGray: [241, 245, 249], // slate-100
        darkGray: [51, 65, 85], // slate-700
        text: [15, 23, 42] // slate-900
      };      // === HEADER SECTION ===
      const headerHeight = 28;
      doc.setFillColor(...colors.primary);
      doc.rect(0, 0, pageWidth, headerHeight, 'F');
      
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text('Employee Skills & Competency Profile', margin, 12);
      
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.text(`Generated: ${new Date().toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })}`, margin, 20);

      yPosition = headerHeight + 10;

      // === IDENTITY SECTION ===
      doc.setTextColor(...colors.text);
      doc.setFontSize(20);
      doc.setFont('helvetica', 'bold');
      doc.text(employeeProfile.employee_name || 'N/A', margin, yPosition);
      
      yPosition += 8;
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setFillColor(...colors.lightGray);
      doc.setTextColor(...colors.secondary);
      const zidText = `ZID: ${selectedEmployee?.zid || 'N/A'}`;
      const zidWidth = doc.getTextWidth(zidText) + 4;
      doc.roundedRect(margin, yPosition - 4, zidWidth, 6, 1, 1, 'F');
      doc.text(zidText, margin + 2, yPosition);
      
      yPosition += 12;

      // Organization details in 2 columns
      const detailsData = [
        ['Sub-Segment:', employeeProfile.organization?.sub_segment || 'N/A'],
        ['Project:', employeeProfile.organization?.project || 'N/A'],
        ['Team:', employeeProfile.organization?.team || 'N/A'],
        ['Role:', employeeProfile.role || 'N/A'],
        ['Started Working:', this.formatDate(employeeProfile.start_date_of_working)],
        ['Experience:', this.calculateExperience(employeeProfile.start_date_of_working)]
      ];

      doc.setFontSize(9);
      const colWidth = (pageWidth - 2 * margin - 10) / 2;
      let xPos = margin;
      let tempY = yPosition;

      detailsData.forEach((item, index) => {
        if (index === 3) {
          xPos = margin + colWidth + 10;
          tempY = yPosition;
        }
        
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...colors.secondary);
        doc.text(item[0], xPos, tempY);
        
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...colors.text);
        doc.text(item[1], xPos + 30, tempY);
        
        tempY += 6;
      });

      yPosition = Math.max(yPosition + 18, tempY);

      // === SUMMARY METRICS (2x2 Grid) ===
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...colors.text);
      doc.text('Summary Metrics', margin, yPosition);
      yPosition += 8;

      const metrics = [
        { label: 'Total Skills', value: employeeProfile.total_skills || 0 },
        { 
          label: 'Certified Skills', 
          value: employeeProfile.skills?.filter(s => s.certification && s.certification.trim() !== '').length || 0 
        },
        { 
          label: 'Recently Updated', 
          value: this.getRecentlyUpdatedCount(employeeProfile.skills) 
        },
        { 
          label: 'Last Updated', 
          value: this.getMostRecentUpdateFormatted(employeeProfile.skills) 
        }
      ];

      const cardWidth = (pageWidth - 2 * margin - 5) / 2;
      const cardHeight = 20;
      
      metrics.forEach((metric, index) => {
        const row = Math.floor(index / 2);
        const col = index % 2;
        const x = margin + col * (cardWidth + 5);
        const y = yPosition + row * (cardHeight + 5);

        // Card background
        doc.setFillColor(...colors.lightGray);
        doc.roundedRect(x, y, cardWidth, cardHeight, 2, 2, 'F');
        
        // Value
        doc.setFontSize(18);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...colors.primary);
        const valueText = String(metric.value);
        const valueWidth = doc.getTextWidth(valueText);
        doc.text(valueText, x + cardWidth / 2 - valueWidth / 2, y + 10);
        
        // Label
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...colors.secondary);
        const labelWidth = doc.getTextWidth(metric.label);
        doc.text(metric.label, x + cardWidth / 2 - labelWidth / 2, y + 16);
      });

      yPosition += 50;

      // === CORE EXPERTISE ===
      const coreSkills = this.getCoreExpertiseSkills(employeeProfile.skills);
      
      if (coreSkills.length > 0) {
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...colors.text);
        doc.text('Core Expertise', margin, yPosition);
        yPosition += 8;        // Render skills as chips (wrapped)
        doc.setFontSize(9);
        let chipX = margin;
        let chipY = yPosition;
        const chipPadding = 4;
        const chipSpacing = 4;
        const maxChipWidth = pageWidth - 2 * margin;

        coreSkills.forEach((skill) => {
          const skillText = skill.skillName || skill.name;
          const stars = this.renderStars(skill.proficiencyLevelId);
          const fullText = `${skillText} ${stars}`;
          
          doc.setFont('helvetica', 'normal');
          const textWidth = doc.getTextWidth(fullText);
          const chipWidth = textWidth + 2 * chipPadding;

          // Check if we need to wrap to next line
          if (chipX + chipWidth > margin + maxChipWidth && chipX > margin) {
            chipX = margin;
            chipY += 8;
          }

          // Draw chip background
          const bgColor = this.getBadgeColorRGB(skill.proficiency);
          doc.setFillColor(...bgColor.bg);
          doc.roundedRect(chipX, chipY - 4, chipWidth, 6, 1, 1, 'F');
          
          // Draw text
          doc.setTextColor(...bgColor.text);
          doc.text(fullText, chipX + chipPadding, chipY);

          chipX += chipWidth + chipSpacing;
        });

        yPosition = chipY + 10;
      }

      // === ALL SKILLS TABLE ===
      // Check if we need a new page
      if (yPosition > pageHeight - 60) {
        doc.addPage();
        yPosition = margin;
      }

      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...colors.text);
      doc.text(`All Skills (${employeeProfile.skills?.length || 0})`, margin, yPosition);
      yPosition += 5;      // Prepare table data
      const tableData = (employeeProfile.skills || []).map(skill => [
        skill.skillName || skill.name,
        skill.category || '–',
        this.renderStars(skill.proficiencyLevelId),
        String(skill.yearsOfExperience || 0),
        skill.lastUsed ? this.formatDate(skill.lastUsed) : 'N/A',
        skill.certification && skill.certification.trim() !== '' ? skill.certification : '-'
      ]);

      // Generate table with autoTable
      autoTable(doc, {
        startY: yPosition,
        head: [['Skill Name', 'Category', 'Proficiency', 'Years Exp', 'Last Used', 'Certifications']],
        body: tableData,
        theme: 'striped',
        headStyles: {
          fillColor: colors.primary,
          textColor: [255, 255, 255],
          fontSize: 9,
          fontStyle: 'bold',
          halign: 'left'
        },
        bodyStyles: {
          fontSize: 8,
          textColor: colors.text
        },
        alternateRowStyles: {
          fillColor: [248, 250, 252] // slate-50
        },
        columnStyles: {
          0: { cellWidth: 45, fontStyle: 'bold' }, // Skill Name
          1: { cellWidth: 30 }, // Category
          2: { cellWidth: 25, halign: 'left' }, // Proficiency (stars)
          3: { cellWidth: 20, halign: 'center' }, // Years Exp
          4: { cellWidth: 25, halign: 'left' }, // Last Used
          5: { cellWidth: 'auto' } // Certifications
        },
        margin: { left: margin, right: margin },
        didDrawPage: (_data) => {
          // Add page numbers
          const pageCount = doc.internal.getNumberOfPages();
          const currentPage = doc.internal.getCurrentPageInfo().pageNumber;
          
          doc.setFontSize(8);
          doc.setTextColor(...colors.secondary);
          doc.text(
            `Page ${currentPage} of ${pageCount}`,
            pageWidth - margin - 20,
            pageHeight - 10
          );
        }
      });

      // === SAVE PDF ===
      const fileName = `${employeeProfile.employee_name.replace(/\s+/g, '_')}_Profile_${new Date().toISOString().split('T')[0]}.pdf`;
      doc.save(fileName);

    } catch (error) {
      console.error('PDF export failed:', error);
      throw new Error(`Failed to export PDF: ${error.message}`);
    }
  }

  /**
   * Get core expertise skills (proficiency >= 4, top 10)
   */
  getCoreExpertiseSkills(skills) {
    if (!skills || skills.length === 0) return [];
    
    return skills
      .filter(skill => skill.proficiencyLevelId && skill.proficiencyLevelId >= 4)
      .sort((a, b) => {
        if (b.proficiencyLevelId !== a.proficiencyLevelId) {
          return b.proficiencyLevelId - a.proficiencyLevelId;
        }
        return (b.yearsOfExperience || 0) - (a.yearsOfExperience || 0);
      })
      .slice(0, 10);
  }
  /**
   * Render stars based on proficiency level (PDF-safe ASCII representation)
   */
  renderStars(level) {
    const validLevel = level || 3;
    // Use ASCII asterisks to avoid font encoding issues in PDF
    return '*'.repeat(validLevel);
  }

  /**
   * Get RGB color values for badge based on proficiency
   */
  getBadgeColorRGB(proficiency) {
    if (proficiency === 'Expert') {
      return { bg: [220, 252, 231], text: [22, 101, 52] }; // green
    }
    if (proficiency === 'Advanced' || proficiency === 'Proficient') {
      return { bg: [219, 234, 254], text: [30, 64, 175] }; // blue
    }
    return { bg: [254, 249, 195], text: [133, 77, 14] }; // yellow
  }

  /**
   * Format date to readable format
   */
  formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return 'N/A';
    }
  }

  /**
   * Calculate experience from start date
   */
  calculateExperience(startDateString) {
    if (!startDateString) return 'N/A';
    try {
      const startDate = new Date(startDateString);
      const today = new Date();
      
      let years = today.getFullYear() - startDate.getFullYear();
      let months = today.getMonth() - startDate.getMonth();
      
      if (months < 0) {
        years--;
        months += 12;
      }
      
      if (years === 0) {
        return `${months} month${months !== 1 ? 's' : ''}`;
      } else if (months === 0) {
        return `${years} year${years !== 1 ? 's' : ''}`;
      } else {
        return `${years} year${years !== 1 ? 's' : ''} ${months} month${months !== 1 ? 's' : ''}`;
      }
    } catch {
      return 'N/A';
    }
  }

  /**
   * Get count of recently updated skills (within 90 days)
   */
  getRecentlyUpdatedCount(skills) {
    if (!skills) return 0;
    
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
    
    return skills.filter(s => {
      if (!s.lastUpdated) return false;
      const lastUpdated = new Date(s.lastUpdated);
      return lastUpdated >= ninetyDaysAgo;
    }).length;
  }

  /**
   * Get most recent update date formatted
   */
  getMostRecentUpdateFormatted(skills) {
    if (!skills || skills.length === 0) return '–';
    
    const datesWithValues = skills
      .map(s => s.lastUpdated)
      .filter(date => date != null);
    
    if (datesWithValues.length === 0) return '–';
    
    const mostRecent = new Date(Math.max(...datesWithValues.map(d => new Date(d).getTime())));
    return this.formatDate(mostRecent);
  }
}

// Export singleton instance
const employeeProfilePdfExportService = new EmployeeProfilePdfExportService();
export default employeeProfilePdfExportService;
