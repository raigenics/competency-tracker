/**
 * Unit tests for SkillCapabilitySnapshot component
 * 
 * Tests:
 * 1. Renders section title "Capability Snapshot"
 * 2. Renders all 3 KPI cards (Employees, Certified, Teams)
 * 3. Displays correct values from props
 * 4. Shows loading skeleton when isLoading is true
 * 5. Handles zero values correctly
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SkillCapabilitySnapshot from '@/pages/Taxonomy/components/SkillCapabilitySnapshot';

describe('SkillCapabilitySnapshot', () => {
  const defaultProps = {
    employeeCount: 128,
    certifiedCount: 36,
    teamCount: 14,
    isLoading: false
  };

  describe('Section Title', () => {
    it('renders Capability Snapshot title', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText('Capability Snapshot')).toBeInTheDocument();
    });

    it('title has uppercase styling class', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      const title = screen.getByText('Capability Snapshot');
      expect(title).toHaveClass('co-snapshot-title');
    });
  });

  describe('KPI Cards Rendering', () => {
    it('renders Employees card with label and sub-label', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText('Employees')).toBeInTheDocument();
      expect(screen.getByText('in scope')).toBeInTheDocument();
    });

    it('renders Certified card with label and sub-label', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText('Certified')).toBeInTheDocument();
      expect(screen.getByText('count')).toBeInTheDocument();
    });

    it('renders Teams card with label and sub-label', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText('Teams')).toBeInTheDocument();
      expect(screen.getByText('usage')).toBeInTheDocument();
    });

    it('renders hint text for each card', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText(/employees mapped to this skill/i)).toBeInTheDocument();
      expect(screen.getByText(/certification tagged/i)).toBeInTheDocument();
      expect(screen.getByText(/distinct teams/i)).toBeInTheDocument();
    });
  });

  describe('KPI Values', () => {
    it('displays correct employee count', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText('128')).toBeInTheDocument();
    });

    it('displays correct certified count', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText('36')).toBeInTheDocument();
    });

    it('displays correct team count', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(screen.getByText('14')).toBeInTheDocument();
    });

    it('handles zero values correctly', () => {
      render(
        <SkillCapabilitySnapshot
          employeeCount={0}
          certifiedCount={0}
          teamCount={0}
          isLoading={false}
        />
      );

      // Should render three 0 values
      const zeroElements = screen.getAllByText('0');
      expect(zeroElements).toHaveLength(3);
    });
  });

  describe('Loading State', () => {
    it('shows loading skeleton when isLoading is true', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} isLoading={true} />);

      // Should still show the title
      expect(screen.getByText('Capability Snapshot')).toBeInTheDocument();

      // Should render skeleton elements
      const skeletons = document.querySelectorAll('.co-skeleton');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('does not show actual values when loading', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} isLoading={true} />);

      // Should not show the actual values
      expect(screen.queryByText('128')).not.toBeInTheDocument();
      expect(screen.queryByText('36')).not.toBeInTheDocument();
      expect(screen.queryByText('14')).not.toBeInTheDocument();
    });

    it('renders 3 skeleton cards when loading', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} isLoading={true} />);

      const loadingCards = document.querySelectorAll('.co-snapshot-kpi--loading');
      expect(loadingCards).toHaveLength(3);
    });
  });

  describe('Default Props', () => {
    it('renders with default values when no props provided', () => {
      render(<SkillCapabilitySnapshot />);

      // Should render with 0 values
      const zeroElements = screen.getAllByText('0');
      expect(zeroElements).toHaveLength(3);
    });
  });

  describe('Regression Tests', () => {
    it('component renders without errors with minimal props', () => {
      expect(() => render(<SkillCapabilitySnapshot />)).not.toThrow();
    });

    it('component renders without errors with all props', () => {
      expect(() => render(<SkillCapabilitySnapshot {...defaultProps} />)).not.toThrow();
    });

    it('maintains correct structure with CSS classes', () => {
      render(<SkillCapabilitySnapshot {...defaultProps} />);

      expect(document.querySelector('.co-capability-snapshot')).toBeInTheDocument();
      expect(document.querySelector('.co-snapshot-kpis')).toBeInTheDocument();
      expect(document.querySelectorAll('.co-snapshot-kpi')).toHaveLength(3);
    });
  });
});
