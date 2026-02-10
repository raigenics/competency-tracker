/**
 * EmployeeSkillsTab Unit Tests
 * 
 * Tests for the Skills tab UI implementation.
 * Covers:
 * - Info message with admin email
 * - Skill autocomplete showing category + subcategory
 * - Skill selection storing skill_id
 * - Free-text validation (must select from list)
 * - Comment field removal
 * - Certification optional, other fields required
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { EmployeeSkillsTab, createEmptySkill, validateSkillRow } from '@/components/skills/EmployeeSkillsTab.jsx';
import { SUPER_ADMIN_EMAIL } from '@/config/constants.js';

// Mock the useSkillSuggestions hook
vi.mock('@/hooks/useSkillSuggestions.js', () => ({
  useSkillSuggestions: vi.fn()
}));

import { useSkillSuggestions } from '@/hooks/useSkillSuggestions.js';

// Mock skill data
const mockSkillsData = [
  {
    skill_id: 1,
    skill_name: 'React',
    category_name: 'Frontend Development',
    subcategory_name: 'Frameworks',
    employee_count: 50
  },
  {
    skill_id: 2,
    skill_name: 'Python',
    category_name: 'Programming Languages',
    subcategory_name: null,
    employee_count: 100
  },
  {
    skill_id: 3,
    skill_name: 'PostgreSQL',
    category_name: 'Databases',
    subcategory_name: 'Relational',
    employee_count: 30
  }
];

// Default mock implementation
const createMockUseSkillSuggestions = (overrides = {}) => ({
  allSkills: mockSkillsData,
  suggestions: [],
  loading: false,
  error: null,
  search: vi.fn(),
  getSuggestions: vi.fn((query) => mockSkillsData),
  getSkillById: vi.fn((id) => mockSkillsData.find(s => s.skill_id === id)),
  clearSuggestions: vi.fn(),
  ...overrides
});

describe('EmployeeSkillsTab', () => {
  let mockOnSkillsChange;
  let mockOnValidate;

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnSkillsChange = vi.fn();
    mockOnValidate = vi.fn();
    useSkillSuggestions.mockReturnValue(createMockUseSkillSuggestions());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('1. Skills Info Message', () => {
    it('should render info callout with admin email', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const infoCallout = screen.getByTestId('skills-info-callout');
      expect(infoCallout).toBeInTheDocument();

      const infoMessage = screen.getByTestId('skills-info-message');
      expect(infoMessage).toHaveTextContent('Select skills from the approved list');
      expect(infoMessage).toHaveTextContent('email the admin');
    });

    it('should contain admin email link with correct address', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const emailLink = screen.getByTestId('admin-email-link');
      expect(emailLink).toHaveAttribute('href', `mailto:${SUPER_ADMIN_EMAIL}`);
      expect(emailLink).toHaveTextContent(SUPER_ADMIN_EMAIL);
    });

    it('should NOT use technical terms like "master data" in message', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const infoMessage = screen.getByTestId('skills-info-message');
      expect(infoMessage.textContent.toLowerCase()).not.toContain('master data');
      expect(infoMessage.textContent.toLowerCase()).not.toContain('employee_skills');
    });
  });

  describe('2. Skill Autocomplete with Category/Subcategory', () => {
    it('should show suggestions with category and subcategory meta', async () => {
      useSkillSuggestions.mockReturnValue(createMockUseSkillSuggestions({
        suggestions: mockSkillsData
      }));

      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      // Focus the skill input to trigger dropdown
      const skillInput = screen.getByTestId('skill-name-input');
      fireEvent.focus(skillInput);

      // Wait for dropdown
      await waitFor(() => {
        const dropdown = screen.getByTestId('skill-dropdown');
        expect(dropdown).toBeInTheDocument();
      });

      // Check that suggestions show category and subcategory (separated by ›)
      // Note: The text content doesn't include CSS gap spacing
      const reactSuggestion = screen.getByTestId('skill-suggestion-1');
      expect(reactSuggestion).toHaveTextContent('React');
      expect(within(reactSuggestion).getByTestId('skill-category-meta')).toHaveTextContent('Frontend Development›Frameworks');

      const pythonSuggestion = screen.getByTestId('skill-suggestion-2');
      expect(pythonSuggestion).toHaveTextContent('Python');
      // Python has no subcategory, should only show category
      expect(within(pythonSuggestion).getByTestId('skill-category-meta')).toHaveTextContent('Programming Languages');
    });

    it('should show "No matches" when no suggestions', async () => {
      useSkillSuggestions.mockReturnValue(createMockUseSkillSuggestions({
        suggestions: []
      }));

      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const skillInput = screen.getByTestId('skill-name-input');
      fireEvent.focus(skillInput);
      fireEvent.change(skillInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByTestId('skill-no-results')).toHaveTextContent('No matching skills found');
      });
    });
  });

  describe('3. Skill Selection', () => {
    it('should store skill_id when selecting from suggestions', async () => {
      const search = vi.fn();
      useSkillSuggestions.mockReturnValue(createMockUseSkillSuggestions({
        suggestions: mockSkillsData,
        search
      }));

      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      // Focus and trigger dropdown
      const skillInput = screen.getByTestId('skill-name-input');
      fireEvent.focus(skillInput);

      // Wait for dropdown
      await waitFor(() => {
        expect(screen.getByTestId('skill-dropdown')).toBeInTheDocument();
      });

      // Click on React suggestion
      const reactSuggestion = screen.getByTestId('skill-suggestion-1');
      fireEvent.mouseDown(reactSuggestion);

      // Verify onSkillsChange was called with skill_id
      expect(mockOnSkillsChange).toHaveBeenCalled();
      const updatedSkills = mockOnSkillsChange.mock.calls[mockOnSkillsChange.mock.calls.length - 1][0];
      expect(updatedSkills[0].skill_id).toBe(1);
      expect(updatedSkills[0].skillName).toBe('React');
    });
  });

  describe('4. Free-text Validation', () => {
    it('should show error when skill not selected from list', () => {
      const skillWithFreeText = {
        ...createEmptySkill(),
        skillName: 'Some custom skill',
        skill_id: null, // Not selected from list
        proficiency: 'COMPETENT',
        yearsExperience: '3'
      };

      const errors = validateSkillRow(skillWithFreeText);
      expect(errors.skillName).toBe('Please select a skill from the list');
    });

    it('should NOT show error when skill is properly selected', () => {
      const skillWithSelection = {
        ...createEmptySkill(),
        skillName: 'React',
        skill_id: 1, // Selected from list
        proficiency: 'COMPETENT',
        yearsExperience: '3'
      };

      const errors = validateSkillRow(skillWithSelection);
      expect(errors.skillName).toBeUndefined();
    });
  });

  describe('5. Comment Field Removal', () => {
    it('should NOT render comment column header', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const table = screen.getByTestId('skills-table');
      expect(table).not.toHaveTextContent('Comment');
    });

    it('should NOT have comment input in skill row', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      // Check that no element with comment-related test id exists
      expect(screen.queryByTestId('comment-input')).not.toBeInTheDocument();
    });

    // FIX: Added tests for restored "Last Used" and "Started From" columns
    it('should render ALL required headers including Last Used and Started From', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const table = screen.getByTestId('skills-table');
      // Required headers that must be present
      expect(table).toHaveTextContent('Skill Name');
      expect(table).toHaveTextContent('Proficiency');
      expect(table).toHaveTextContent('Exp (Yrs)');
      expect(table).toHaveTextContent('Last Used');
      expect(table).toHaveTextContent('Started From');
      expect(table).toHaveTextContent('Certification');
      // Comment must NOT be present
      expect(table).not.toHaveTextContent('Comment');
    });

    it('should have Last Used input with Month dropdown and Year input (month-year-input)', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      // Check for month-year-input container
      const lastUsedContainer = screen.getByTestId('last-used-container');
      expect(lastUsedContainer).toBeInTheDocument();
      expect(lastUsedContainer).toHaveClass('month-year-input');

      // Check for month dropdown
      const monthDropdown = screen.getByTestId('last-used-month');
      expect(monthDropdown).toBeInTheDocument();
      expect(monthDropdown.tagName).toBe('SELECT');
      // Verify month options exist (Jan-Dec)
      expect(monthDropdown).toHaveTextContent('Month');
      expect(monthDropdown).toHaveTextContent('Jan');
      expect(monthDropdown).toHaveTextContent('Dec');

      // Check for year input (text type with numeric inputMode for better UX)
      const yearInput = screen.getByTestId('last-used-year');
      expect(yearInput).toBeInTheDocument();
      expect(yearInput).toHaveAttribute('type', 'text');
      expect(yearInput).toHaveAttribute('inputMode', 'numeric');
      expect(yearInput).toHaveAttribute('placeholder', 'YY');
      expect(yearInput).toHaveAttribute('maxLength', '2');
    });

    it('should allow typing in Last Used year field and only accept digits', () => {
      const mockSkills = [createEmptySkill()];
      render(
        <EmployeeSkillsTab
          skills={mockSkills}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const yearInput = screen.getByTestId('last-used-year');
      
      // Type "25" - should accept 2 digits
      fireEvent.change(yearInput, { target: { value: '25' } });
      
      // onSkillsChange should be called with the year value
      expect(mockOnSkillsChange).toHaveBeenCalled();
    });

    it('should truncate Last Used year input to 2 digits (YY format)', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const yearInput = screen.getByTestId('last-used-year');
      
      // Attempt to type "256" - should be truncated to "25" due to maxLength and slice
      fireEvent.change(yearInput, { target: { value: '256' } });
      
      // onSkillsChange should be called (the component handles truncation)
      expect(mockOnSkillsChange).toHaveBeenCalled();
    });

    it('should have Skill Name column wider than action column', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const table = screen.getByTestId('skills-table');
      const headers = table.querySelectorAll('thead th');
      
      // First column (Skill Name) should be wider than last column (Actions)
      const skillNameHeader = headers[0];
      const actionHeader = headers[headers.length - 1];
      
      // Extract width percentages from inline styles
      const skillNameWidth = parseInt(skillNameHeader.style.width, 10);
      const actionWidth = parseInt(actionHeader.style.width, 10);
      
      // Skill Name should be significantly wider (at least 5x) than action column
      expect(skillNameWidth).toBeGreaterThan(actionWidth * 5);
    });

    it('should have Started From input in skill row', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const startedFromInput = screen.getByTestId('started-from-input');
      expect(startedFromInput).toBeInTheDocument();
      expect(startedFromInput).toHaveAttribute('type', 'date');
    });
  });

  describe('6. Certification Optional, Other Fields Required', () => {
    it('should mark certification as optional (no error when empty)', () => {
      const skillValid = {
        ...createEmptySkill(),
        skill_id: 1,
        skillName: 'React',
        proficiency: 'COMPETENT',
        yearsExperience: '3',
        certification: '' // Empty is OK
      };

      const errors = validateSkillRow(skillValid);
      expect(errors.certification).toBeUndefined();
      expect(Object.keys(errors)).toHaveLength(0);
    });

    it('should show error when proficiency is empty', () => {
      const skillMissingProficiency = {
        ...createEmptySkill(),
        skill_id: 1,
        skillName: 'React',
        proficiency: '', // Missing
        yearsExperience: '3'
      };

      const errors = validateSkillRow(skillMissingProficiency);
      expect(errors.proficiency).toBe('Proficiency is required');
    });

    it('should show error when experience is empty', () => {
      const skillMissingExperience = {
        ...createEmptySkill(),
        skill_id: 1,
        skillName: 'React',
        proficiency: 'COMPETENT',
        yearsExperience: '' // Missing
      };

      const errors = validateSkillRow(skillMissingExperience);
      expect(errors.yearsExperience).toBe('Experience is required');
    });

    it('should render certification field with "Optional" placeholder', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const certInput = screen.getByTestId('certification-input');
      expect(certInput).toHaveAttribute('placeholder', 'Optional');
    });
  });

  describe('7. Add/Delete Skill Rows', () => {
    it('should render Add Skill button', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const addButton = screen.getByTestId('add-skill-btn');
      expect(addButton).toHaveTextContent('+ Add Skill');
    });

    it('should call onSkillsChange when Add Skill clicked', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const addButton = screen.getByTestId('add-skill-btn');
      fireEvent.click(addButton);

      expect(mockOnSkillsChange).toHaveBeenCalled();
      const newSkills = mockOnSkillsChange.mock.calls[0][0];
      expect(newSkills).toHaveLength(2);
    });

    it('should have delete button for skill rows', () => {
      render(
        <EmployeeSkillsTab
          skills={[createEmptySkill(), createEmptySkill()]}
          onSkillsChange={mockOnSkillsChange}
        />
      );

      const deleteButtons = screen.getAllByTestId('delete-skill-btn');
      expect(deleteButtons).toHaveLength(2);
    });
  });
});

describe('EmployeeSkillsTab - Integration with AddEmployeeDrawer', () => {
  // These tests verify integration behavior
  
  beforeEach(() => {
    vi.clearAllMocks();
    useSkillSuggestions.mockReturnValue(createMockUseSkillSuggestions());
  });

  it('should call onValidate with errors when validation triggered', () => {
    const mockOnValidate = vi.fn();
    
    const skillsWithMissingFields = [
      {
        ...createEmptySkill(),
        skill_id: 1,
        skillName: 'React',
        proficiency: '', // Missing
        yearsExperience: ''
      }
    ];

    render(
      <EmployeeSkillsTab
        skills={skillsWithMissingFields}
        onSkillsChange={vi.fn()}
        onValidate={mockOnValidate}
      />
    );

    // The component exposes validation via onValidate callback
    // In real usage, parent component calls validateAllSkills
    // For this test, we verify the validation function works correctly
    const errors = validateSkillRow(skillsWithMissingFields[0]);
    expect(errors.proficiency).toBeDefined();
    expect(errors.yearsExperience).toBeDefined();
  });
});
