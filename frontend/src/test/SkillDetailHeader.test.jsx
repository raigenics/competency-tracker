/**
 * Unit tests for SkillDetailHeader component
 * 
 * Tests:
 * 1. Renders breadcrumb with category, subcategory, and skill name
 * 2. Renders skill title
 * 3. Renders View Employees button with correct count
 * 4. Button is disabled when isDisabled prop is true
 * 5. Button is disabled when employeeCount is 0
 * 6. Calls onViewEmployees when button is clicked
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SkillDetailHeader from '@/pages/Taxonomy/components/SkillDetailHeader';

describe('SkillDetailHeader', () => {
  const defaultProps = {
    categoryName: 'AI & Developer Productivity',
    subCategoryName: 'AI Agents & Orchestration',
    skillName: 'LangChain',
    employeeCount: 128,
    onViewEmployees: vi.fn(),
    isDisabled: false
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Breadcrumb Rendering', () => {
    it('renders full breadcrumb with category, subcategory, and skill', () => {
      render(<SkillDetailHeader {...defaultProps} />);

      const crumbs = screen.getByText(/Capability Structure/i);
      expect(crumbs).toBeInTheDocument();
      expect(crumbs).toHaveTextContent('AI & Developer Productivity');
      expect(crumbs).toHaveTextContent('AI Agents & Orchestration');
      expect(crumbs).toHaveTextContent('LangChain');
    });

    it('renders breadcrumb without subcategory when not provided', () => {
      render(<SkillDetailHeader {...defaultProps} subCategoryName={null} />);

      const crumbs = screen.getByText(/Capability Structure/i);
      expect(crumbs).toHaveTextContent('AI & Developer Productivity');
      expect(crumbs).toHaveTextContent('LangChain');
      expect(crumbs).not.toHaveTextContent('AI Agents & Orchestration');
    });

    it('renders skill name in bold within breadcrumb', () => {
      render(<SkillDetailHeader {...defaultProps} />);

      const boldSkill = screen.getByText('LangChain', { selector: 'b' });
      expect(boldSkill).toBeInTheDocument();
    });
  });

  describe('Title Rendering', () => {
    it('renders skill title as h1', () => {
      render(<SkillDetailHeader {...defaultProps} />);

      const title = screen.getByRole('heading', { level: 1, name: 'LangChain' });
      expect(title).toBeInTheDocument();
    });
  });

  describe('View Employees Button', () => {
    it('renders button with correct employee count', () => {
      render(<SkillDetailHeader {...defaultProps} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('View Employees (128)');
    });

    it('calls onViewEmployees when clicked', () => {
      const onViewEmployees = vi.fn();
      render(<SkillDetailHeader {...defaultProps} onViewEmployees={onViewEmployees} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      fireEvent.click(button);

      expect(onViewEmployees).toHaveBeenCalledTimes(1);
    });

    it('is disabled when isDisabled prop is true', () => {
      render(<SkillDetailHeader {...defaultProps} isDisabled={true} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      expect(button).toBeDisabled();
    });

    it('is disabled when employeeCount is 0', () => {
      render(<SkillDetailHeader {...defaultProps} employeeCount={0} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      expect(button).toBeDisabled();
    });

    it('is not disabled when employeeCount > 0 and isDisabled is false', () => {
      render(<SkillDetailHeader {...defaultProps} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      expect(button).not.toBeDisabled();
    });

    it('does not call onViewEmployees when disabled and clicked', () => {
      const onViewEmployees = vi.fn();
      render(<SkillDetailHeader {...defaultProps} isDisabled={true} onViewEmployees={onViewEmployees} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      fireEvent.click(button);

      expect(onViewEmployees).not.toHaveBeenCalled();
    });
  });

  describe('Dynamic Employee Count', () => {
    it('displays 0 employees correctly', () => {
      render(<SkillDetailHeader {...defaultProps} employeeCount={0} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      expect(button).toHaveTextContent('View Employees (0)');
    });

    it('displays large employee count correctly', () => {
      render(<SkillDetailHeader {...defaultProps} employeeCount={1500} />);

      const button = screen.getByRole('button', { name: /view employees/i });
      expect(button).toHaveTextContent('View Employees (1500)');
    });
  });
});
