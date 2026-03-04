/**
 * Unit tests for TwoPaneLayout component
 * 
 * Tests the reusable two-pane layout primitive:
 * - Basic rendering of left and right panes
 * - Header slot rendering
 * - Scroll flag behavior
 * - Custom width and gap
 * - CSS class application
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TwoPaneLayout from '@/layouts/TwoPaneLayout.jsx';

describe('TwoPaneLayout', () => {
  // =========================================================================
  // 1) Basic Rendering
  // =========================================================================
  describe('Basic Rendering', () => {
    it('should render left and right panes', () => {
      render(
        <TwoPaneLayout
          leftPane={<div data-testid="left-content">Left Content</div>}
          rightPane={<div data-testid="right-content">Right Content</div>}
        />
      );

      expect(screen.getByTestId('two-pane-layout')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-left')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-right')).toBeInTheDocument();
      expect(screen.getByTestId('left-content')).toHaveTextContent('Left Content');
      expect(screen.getByTestId('right-content')).toHaveTextContent('Right Content');
    });

    it('should render pane bodies without headers when no headers provided', () => {
      render(
        <TwoPaneLayout
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      expect(screen.getByTestId('two-pane-left-body')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-right-body')).toBeInTheDocument();
      expect(screen.queryByTestId('two-pane-left-header')).not.toBeInTheDocument();
      expect(screen.queryByTestId('two-pane-right-header')).not.toBeInTheDocument();
    });
  });

  // =========================================================================
  // 2) Header Slots
  // =========================================================================
  describe('Header Slots', () => {
    it('should render left header when provided', () => {
      render(
        <TwoPaneLayout
          leftHeader={<div data-testid="left-header-content">Left Header</div>}
          leftPane={<div>Left Body</div>}
          rightPane={<div>Right</div>}
        />
      );

      expect(screen.getByTestId('two-pane-left-header')).toBeInTheDocument();
      expect(screen.getByTestId('left-header-content')).toHaveTextContent('Left Header');
    });

    it('should render right header when provided', () => {
      render(
        <TwoPaneLayout
          rightHeader={<div data-testid="right-header-content">Right Header</div>}
          leftPane={<div>Left</div>}
          rightPane={<div>Right Body</div>}
        />
      );

      expect(screen.getByTestId('two-pane-right-header')).toBeInTheDocument();
      expect(screen.getByTestId('right-header-content')).toHaveTextContent('Right Header');
    });

    it('should render both headers when both provided', () => {
      render(
        <TwoPaneLayout
          leftHeader={<div>L Header</div>}
          rightHeader={<div>R Header</div>}
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      expect(screen.getByTestId('two-pane-left-header')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-right-header')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // 3) Scroll Behavior Flags
  // =========================================================================
  describe('Scroll Behavior', () => {
    it('should apply overflow-y auto to left pane body when leftScrollable is true (default)', () => {
      render(
        <TwoPaneLayout
          leftScrollable={true}
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const leftBody = screen.getByTestId('two-pane-left-body');
      expect(leftBody).toHaveStyle({ overflowY: 'auto' });
    });

    it('should apply overflow visible to left pane body when leftScrollable is false', () => {
      render(
        <TwoPaneLayout
          leftScrollable={false}
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const leftBody = screen.getByTestId('two-pane-left-body');
      expect(leftBody).toHaveStyle({ overflow: 'visible' });
    });

    it('should apply overflow-y auto to right pane body when rightScrollable is true', () => {
      render(
        <TwoPaneLayout
          rightScrollable={true}
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const rightBody = screen.getByTestId('two-pane-right-body');
      expect(rightBody).toHaveStyle({ overflowY: 'auto' });
    });

    it('should apply overflow visible to right pane body when rightScrollable is false (default)', () => {
      render(
        <TwoPaneLayout
          rightScrollable={false}
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const rightBody = screen.getByTestId('two-pane-right-body');
      expect(rightBody).toHaveStyle({ overflow: 'visible' });
    });
  });

  // =========================================================================
  // 4) Custom Styling Props
  // =========================================================================
  describe('Custom Styling', () => {
    it('should apply custom leftWidth via grid-template-columns', () => {
      render(
        <TwoPaneLayout
          leftWidth="400px"
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const container = screen.getByTestId('two-pane-layout');
      expect(container).toHaveStyle({ gridTemplateColumns: '400px 1fr' });
    });

    it('should apply custom gap', () => {
      render(
        <TwoPaneLayout
          gap="24px"
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const container = screen.getByTestId('two-pane-layout');
      expect(container).toHaveStyle({ gap: '24px' });
    });

    it('should apply additional className to container', () => {
      render(
        <TwoPaneLayout
          className="custom-class"
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const container = screen.getByTestId('two-pane-layout');
      expect(container).toHaveClass('two-pane-layout');
      expect(container).toHaveClass('custom-class');
    });

    it('should apply leftPaneClassName to left pane', () => {
      render(
        <TwoPaneLayout
          leftPaneClassName="left-custom-class"
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const leftPane = screen.getByTestId('two-pane-left');
      expect(leftPane).toHaveClass('two-pane-left');
      expect(leftPane).toHaveClass('left-custom-class');
    });

    it('should apply rightPaneClassName to right pane', () => {
      render(
        <TwoPaneLayout
          rightPaneClassName="right-custom-class"
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const rightPane = screen.getByTestId('two-pane-right');
      expect(rightPane).toHaveClass('two-pane-right');
      expect(rightPane).toHaveClass('right-custom-class');
    });

    it('should apply minHeight to container', () => {
      render(
        <TwoPaneLayout
          minHeight="600px"
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const container = screen.getByTestId('two-pane-layout');
      expect(container).toHaveStyle({ minHeight: '600px' });
    });

    it('should apply maxHeight when provided', () => {
      render(
        <TwoPaneLayout
          maxHeight="800px"
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      const container = screen.getByTestId('two-pane-layout');
      expect(container).toHaveStyle({ maxHeight: '800px' });
    });
  });

  // =========================================================================
  // 5) Accessibility
  // =========================================================================
  describe('Accessibility', () => {
    it('should render with appropriate test ids for automation', () => {
      render(
        <TwoPaneLayout
          leftHeader={<div>Header</div>}
          rightHeader={<div>Header</div>}
          leftPane={<div>Left</div>}
          rightPane={<div>Right</div>}
        />
      );

      // All key elements should have test IDs
      expect(screen.getByTestId('two-pane-layout')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-left')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-right')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-left-header')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-right-header')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-left-body')).toBeInTheDocument();
      expect(screen.getByTestId('two-pane-right-body')).toBeInTheDocument();
    });
  });
});
