/**
 * Unit tests for SkillProficiencyBreakdown component
 * 
 * Tests:
 * 1. Renders section title "Proficiency Breakdown"
 * 2. Renders all 5 proficiency levels in legend
 * 3. Displays correct values from props
 * 4. Shows loading skeleton when isLoading is true
 * 5. Handles null/undefined counts gracefully (no crash)
 * 6. Handles missing keys in counts object
 * 7. Handles all zero counts correctly
 * 8. Displays "—" for null avg/median
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SkillProficiencyBreakdown from '@/pages/Taxonomy/components/SkillProficiencyBreakdown';

describe('SkillProficiencyBreakdown', () => {
  const defaultProps = {
    counts: {
      'Novice': 10,
      'Adv. Beginner': 20,
      'Competent': 30,
      'Proficient': 25,
      'Expert': 15
    },
    avg: 2.8,
    median: 3,
    total: 100,
    isLoading: false
  };

  describe('Section Title', () => {
    it('renders Proficiency Breakdown title', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      expect(screen.getByText('Proficiency Breakdown')).toBeInTheDocument();
    });

    it('title has correct styling class', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      const title = screen.getByText('Proficiency Breakdown');
      expect(title).toHaveClass('co-pb-title');
    });
  });

  describe('Legend Rendering', () => {
    it('renders all 5 proficiency levels', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      expect(screen.getByText('Novice')).toBeInTheDocument();
      expect(screen.getByText('Adv. Beginner')).toBeInTheDocument();
      expect(screen.getByText('Competent')).toBeInTheDocument();
      expect(screen.getByText('Proficient')).toBeInTheDocument();
      expect(screen.getByText('Expert')).toBeInTheDocument();
    });

    it('displays correct counts in legend', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
    });
  });

  describe('Avg/Median Display', () => {
    it('displays formatted avg value', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      expect(screen.getByText('2.8')).toBeInTheDocument();
    });

    it('displays median value', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      // Check that median text includes the value
      const metaRight = document.querySelector('.co-pb-meta-right');
      expect(metaRight.textContent).toContain('Median:');
      expect(metaRight.textContent).toContain('3');
    });

    it('displays dash for null avg', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} avg={null} />);

      // Check avg displays dash
      const metaRight = document.querySelector('.co-pb-meta-right');
      expect(metaRight.textContent).toContain('Avg:');
      expect(metaRight.textContent).toContain('—');
    });

    it('displays dash for null median', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} median={null} />);

      // Check median displays dash
      const metaRight = document.querySelector('.co-pb-meta-right');
      expect(metaRight.textContent).toContain('Median:');
      expect(metaRight.textContent).toContain('—');
    });

    it('displays dash for undefined avg', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} avg={undefined} />);

      const metaRight = document.querySelector('.co-pb-meta-right');
      expect(metaRight.textContent).toContain('Avg:');
      expect(metaRight.textContent).toContain('—');
    });
  });

  describe('Loading State', () => {
    it('renders loading skeletons when isLoading is true', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} isLoading={true} />);

      // Should still show title
      expect(screen.getByText('Proficiency Breakdown')).toBeInTheDocument();

      // Should have skeleton elements
      const skeletons = document.querySelectorAll('.co-skeleton');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('does not render count values when loading', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} isLoading={true} />);

      // Count values should not be present
      expect(screen.queryByText('10')).not.toBeInTheDocument();
      expect(screen.queryByText('20')).not.toBeInTheDocument();
    });
  });

  describe('Null-Safety: counts = null', () => {
    it('does not crash when counts is null', () => {
      expect(() => {
        render(<SkillProficiencyBreakdown counts={null} total={0} />);
      }).not.toThrow();
    });

    it('renders all legend items with 0 when counts is null', () => {
      render(<SkillProficiencyBreakdown counts={null} total={0} />);

      // All 5 levels should show, each with count 0
      expect(screen.getByText('Novice')).toBeInTheDocument();
      expect(screen.getByText('Expert')).toBeInTheDocument();

      // Should have multiple zeros (one for each level)
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBe(5);
    });

    it('renders stacked bar as empty when counts is null', () => {
      render(<SkillProficiencyBreakdown counts={null} total={0} />);

      // Stacked bar should exist but have no segments
      const stackedBar = document.querySelector('.co-pb-stacked');
      expect(stackedBar).toBeInTheDocument();
      
      const segments = document.querySelectorAll('.co-pb-seg');
      expect(segments.length).toBe(0);
    });
  });

  describe('Null-Safety: counts missing some keys', () => {
    it('does not crash when counts is missing keys', () => {
      const partialCounts = { 'Novice': 5, 'Expert': 10 };
      expect(() => {
        render(<SkillProficiencyBreakdown counts={partialCounts} total={15} />);
      }).not.toThrow();
    });

    it('renders missing keys as 0', () => {
      const partialCounts = { 'Novice': 5, 'Expert': 10 };
      render(<SkillProficiencyBreakdown counts={partialCounts} total={15} />);

      // Provided counts should appear
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();

      // Missing keys should show as 0
      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBe(3); // Adv. Beginner, Competent, Proficient
    });
  });

  describe('Null-Safety: all zero counts', () => {
    it('does not crash when all counts are zero', () => {
      const zeroCounts = {
        'Novice': 0,
        'Adv. Beginner': 0,
        'Competent': 0,
        'Proficient': 0,
        'Expert': 0
      };
      expect(() => {
        render(<SkillProficiencyBreakdown counts={zeroCounts} total={0} />);
      }).not.toThrow();
    });

    it('renders stacked bar as empty when all counts are zero', () => {
      const zeroCounts = {
        'Novice': 0,
        'Adv. Beginner': 0,
        'Competent': 0,
        'Proficient': 0,
        'Expert': 0
      };
      render(<SkillProficiencyBreakdown counts={zeroCounts} total={0} />);

      const segments = document.querySelectorAll('.co-pb-seg');
      expect(segments.length).toBe(0);
    });

    it('shows all zeros in legend when all counts are zero', () => {
      const zeroCounts = {
        'Novice': 0,
        'Adv. Beginner': 0,
        'Competent': 0,
        'Proficient': 0,
        'Expert': 0
      };
      render(<SkillProficiencyBreakdown counts={zeroCounts} total={0} />);

      const zeros = screen.getAllByText('0');
      expect(zeros.length).toBe(5);
    });
  });

  describe('Null-Safety: undefined props', () => {
    it('does not crash when counts is undefined', () => {
      expect(() => {
        render(<SkillProficiencyBreakdown counts={undefined} total={0} />);
      }).not.toThrow();
    });

    it('handles completely missing props', () => {
      expect(() => {
        render(<SkillProficiencyBreakdown />);
      }).not.toThrow();
    });

    it('renders with all defaults when no props provided', () => {
      render(<SkillProficiencyBreakdown />);

      expect(screen.getByText('Proficiency Breakdown')).toBeInTheDocument();
      expect(screen.getByText('Novice')).toBeInTheDocument();
      expect(screen.getByText('Expert')).toBeInTheDocument();
    });
  });

  describe('Stacked Bar Segment Widths', () => {
    it('renders segments with correct percentage widths', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      // With total=100 and Competent=30, width should be 30%
      const segments = document.querySelectorAll('.co-pb-seg');
      expect(segments.length).toBeGreaterThan(0);

      // Find competent segment and check width
      const competentSeg = document.querySelector('.co-pb-s3');
      expect(competentSeg).toBeInTheDocument();
      expect(competentSeg.style.width).toBe('30%');
    });

    it('does not produce NaN widths when total is 0', () => {
      render(<SkillProficiencyBreakdown counts={defaultProps.counts} total={0} />);

      const segments = document.querySelectorAll('.co-pb-seg');
      segments.forEach(seg => {
        expect(seg.style.width).not.toBe('NaN%');
      });
    });
  });

  describe('Regression: Existing behavior preserved', () => {
    it('renders footnote text', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      expect(screen.getByText(/View Employees/)).toBeInTheDocument();
    });

    it('renders distribution description', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      expect(screen.getByText('Distribution across proficiency levels.')).toBeInTheDocument();
    });

    it('stacked bar has correct accessibility role', () => {
      render(<SkillProficiencyBreakdown {...defaultProps} />);

      const stackedBar = screen.getByRole('img');
      expect(stackedBar).toHaveAttribute('aria-label', 'Proficiency distribution stacked bar');
    });
  });
});
