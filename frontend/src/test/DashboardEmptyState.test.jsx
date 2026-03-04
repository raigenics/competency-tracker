/**
 * Dashboard Empty State Tests
 * 
 * Tests the Dashboard's empty state behavior when:
 * 1. DEFAULT segment has no sub-segments
 * 2. Verifies dashboard data APIs are NOT called when in empty state
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Use vi.hoisted to create mock functions available during hoisting
const { 
  mockGetSubSegmentsBySegment,
  mockGetDashboardMetrics,
  mockGetSkillDistribution,
  mockGetSkillUpdateActivity,
  mockGetDataFreshness
} = vi.hoisted(() => ({
  mockGetSubSegmentsBySegment: vi.fn(),
  mockGetDashboardMetrics: vi.fn(),
  mockGetSkillDistribution: vi.fn(),
  mockGetSkillUpdateActivity: vi.fn(),
  mockGetDataFreshness: vi.fn()
}));

// Mock the dashboardStore
vi.mock('@/pages/Dashboard/dashboardStore.js', () => ({
  default: vi.fn((selector) => {
    const state = {
      isCacheValid: () => false,
      cachedPayload: null,
      setCachedPayload: vi.fn()
    };
    return selector(state);
  })
}));

// Mock dropdownApi
vi.mock('@/services/api/dropdownApi.js', () => ({
  dropdownApi: {
    getSubSegmentsBySegment: mockGetSubSegmentsBySegment,
    getProjects: vi.fn().mockResolvedValue([]),
    getTeams: vi.fn().mockResolvedValue([])
  }
}));

// Mock dashboardApi
vi.mock('@/services/api/dashboardApi.js', () => ({
  dashboardApi: {
    getDashboardMetrics: mockGetDashboardMetrics,
    getSkillDistribution: mockGetSkillDistribution,
    getSkillUpdateActivity: mockGetSkillUpdateActivity,
    getDataFreshness: mockGetDataFreshness,
    getRoleDistribution: vi.fn().mockResolvedValue({ title: '', rows: [] })
  }
}));

// Mock featureFlags
vi.mock('@/config/featureFlags.js', () => ({
  DEFAULT_DASHBOARD_CONTEXT: {
    SEGMENT_CODE: 'TEST',
    SEGMENT_ID: 999,
    ROLE_CODE: 'SUPER_ADMIN',
    SCOPE_TYPE: 'SEGMENT',
    SCOPE_ID: 1
  }
}));

import DashboardPage from '@/pages/Dashboard/DashboardPage.jsx';

// Helper to render Dashboard with router
const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <DashboardPage />
    </BrowserRouter>
  );
};

describe('Dashboard Empty State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('When DEFAULT segment has no sub-segments', () => {
    beforeEach(() => {
      // Simulate empty sub-segments for the DEFAULT segment
      mockGetSubSegmentsBySegment.mockResolvedValue([]);
    });

    it('should show empty state UI', async () => {
      renderDashboard();

      // Wait for empty state to appear
      await waitFor(() => {
        expect(screen.getByText('Your dashboard is ready')).toBeInTheDocument();
      });

      // Check for empty state elements
      expect(screen.getByText(/Add employees and their skills/)).toBeInTheDocument();
      expect(screen.getByText('Go to Import Data')).toBeInTheDocument();
      expect(screen.getByText('Go to Employee Management')).toBeInTheDocument();
    });

    it('should NOT call dashboard data APIs', async () => {
      renderDashboard();

      // Wait for component to settle
      await waitFor(() => {
        expect(screen.getByText('Your dashboard is ready')).toBeInTheDocument();
      });

      // Verify dashboard APIs were NOT called
      expect(mockGetDashboardMetrics).not.toHaveBeenCalled();
      expect(mockGetSkillDistribution).not.toHaveBeenCalled();
      expect(mockGetSkillUpdateActivity).not.toHaveBeenCalled();
      expect(mockGetDataFreshness).not.toHaveBeenCalled();
    });

    it('should call getSubSegmentsBySegment with DEFAULT segment ID', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(mockGetSubSegmentsBySegment).toHaveBeenCalledWith(999);
      });
    });
  });

  describe('When DEFAULT segment has sub-segments', () => {
    beforeEach(() => {
      // Simulate segment with sub-segments
      mockGetSubSegmentsBySegment.mockResolvedValue([
        { id: 1, name: 'Sub-Segment A' },
        { id: 2, name: 'Sub-Segment B' }
      ]);
      
      // Mock dashboard APIs to return data
      mockGetDashboardMetrics.mockResolvedValue({ total_employees: 50 });
      mockGetSkillDistribution.mockResolvedValue([]);
      mockGetSkillUpdateActivity.mockResolvedValue({});
      mockGetDataFreshness.mockResolvedValue(null);
    });

    it('should call dashboard data APIs', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(mockGetDashboardMetrics).toHaveBeenCalled();
      });

      expect(mockGetSkillDistribution).toHaveBeenCalled();
      expect(mockGetSkillUpdateActivity).toHaveBeenCalled();
      expect(mockGetDataFreshness).toHaveBeenCalled();
    });

    it('should NOT show empty state when data exists', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(mockGetDashboardMetrics).toHaveBeenCalled();
      });

      // Wait for loading to complete and verify no empty state heading
      await waitFor(() => {
        expect(screen.queryByText('Your dashboard is ready')).not.toBeInTheDocument();
      });
    });
  });

  describe('When DEFAULT segment is invalid/missing', () => {
    // Note: This test scenario requires modifying featureFlags mock
    // For now, we test the error handling path
    beforeEach(() => {
      // Simulate API error
      mockGetSubSegmentsBySegment.mockRejectedValue(new Error('Segment not found'));
    });

    it('should show empty state on API error', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Your dashboard is ready')).toBeInTheDocument();
      });
    });

    it('should NOT call dashboard data APIs on error', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Your dashboard is ready')).toBeInTheDocument();
      });

      expect(mockGetDashboardMetrics).not.toHaveBeenCalled();
      expect(mockGetSkillDistribution).not.toHaveBeenCalled();
    });
  });
});
