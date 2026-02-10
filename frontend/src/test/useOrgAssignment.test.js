/**
 * useOrgAssignment Hook Unit Tests
 * 
 * Tests:
 * 1. Role-based locking states
 * 2. Cascading selection triggers
 * 3. Reset functionality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useOrgAssignment } from '@/hooks/useOrgAssignment.js';

// Mock the API
vi.mock('@/services/api/dropdownApi.js', () => ({
  dropdownApi: {
    getSegments: vi.fn(),
    getSubSegmentsBySegment: vi.fn(),
    getProjects: vi.fn(),
    getTeams: vi.fn()
  }
}));

// Mock featureFlags
vi.mock('@/config/featureFlags.js', () => ({
  getRbacContext: vi.fn(() => ({
    role: 'SUPER_ADMIN',
    scope: {}
  })),
  RBAC_ROLES: {
    SUPER_ADMIN: 'SUPER_ADMIN',
    SEGMENT_HEAD: 'SEGMENT_HEAD',
    SUBSEGMENT_HEAD: 'SUBSEGMENT_HEAD',
    PROJECT_MANAGER: 'PROJECT_MANAGER',
    TEAM_LEAD: 'TEAM_LEAD',
    TEAM_MEMBER: 'TEAM_MEMBER'
  }
}));

import { dropdownApi } from '@/services/api/dropdownApi.js';
import { getRbacContext, RBAC_ROLES } from '@/config/featureFlags.js';

describe('useOrgAssignment', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default API mocks
    dropdownApi.getSegments.mockResolvedValue([
      { id: 1, name: 'DTS' },
      { id: 2, name: 'SALES' }
    ]);
    
    dropdownApi.getSubSegmentsBySegment.mockResolvedValue([
      { id: 1, name: 'AU' },
      { id: 2, name: 'ADT' }
    ]);
    
    dropdownApi.getProjects.mockResolvedValue([
      { id: 1, name: 'IT' },
      { id: 2, name: 'PDT' }
    ]);
    
    dropdownApi.getTeams.mockResolvedValue([
      { id: 1, name: 'PIM' },
      { id: 2, name: 'Backend' }
    ]);
    
    // Default role: Super Admin
    getRbacContext.mockReturnValue({
      role: RBAC_ROLES.SUPER_ADMIN,
      scope: {}
    });
  });

  describe('1. Role-based Locking States', () => {
    it('Super Admin: nothing locked', async () => {
      const { result } = renderHook(() => useOrgAssignment());
      
      await waitFor(() => {
        expect(result.current.isLocked.segment).toBe(false);
        expect(result.current.isLocked.subSegment).toBe(false);
        expect(result.current.isLocked.project).toBe(false);
        expect(result.current.isLocked.team).toBe(false);
      });
    });

    it('Segment Head: segment is locked', async () => {
      getRbacContext.mockReturnValue({
        role: RBAC_ROLES.SEGMENT_HEAD,
        scope: { segment_id: 1 }
      });
      
      const { result } = renderHook(() => useOrgAssignment());
      
      await waitFor(() => {
        expect(result.current.isLocked.segment).toBe(true);
        expect(result.current.isLocked.subSegment).toBe(false);
        expect(result.current.isLocked.project).toBe(false);
        expect(result.current.isLocked.team).toBe(false);
      });
    });

    it('Subsegment Head: segment + subSegment are locked', async () => {
      getRbacContext.mockReturnValue({
        role: RBAC_ROLES.SUBSEGMENT_HEAD,
        scope: { segment_id: 1, sub_segment_id: 2 }
      });
      
      const { result } = renderHook(() => useOrgAssignment());
      
      await waitFor(() => {
        expect(result.current.isLocked.segment).toBe(true);
        expect(result.current.isLocked.subSegment).toBe(true);
        expect(result.current.isLocked.project).toBe(false);
        expect(result.current.isLocked.team).toBe(false);
      });
    });

    it('Project Manager: segment + subSegment + project are locked', async () => {
      getRbacContext.mockReturnValue({
        role: RBAC_ROLES.PROJECT_MANAGER,
        scope: { segment_id: 1, sub_segment_id: 2, project_id: 3 }
      });
      
      const { result } = renderHook(() => useOrgAssignment());
      
      await waitFor(() => {
        expect(result.current.isLocked.segment).toBe(true);
        expect(result.current.isLocked.subSegment).toBe(true);
        expect(result.current.isLocked.project).toBe(true);
        expect(result.current.isLocked.team).toBe(false);
      });
    });

    it('Team Lead: all dropdowns are locked', async () => {
      getRbacContext.mockReturnValue({
        role: RBAC_ROLES.TEAM_LEAD,
        scope: { segment_id: 1, sub_segment_id: 2, project_id: 3, team_id: 4 }
      });
      
      const { result } = renderHook(() => useOrgAssignment());
      
      await waitFor(() => {
        expect(result.current.isLocked.segment).toBe(true);
        expect(result.current.isLocked.subSegment).toBe(true);
        expect(result.current.isLocked.project).toBe(true);
        expect(result.current.isLocked.team).toBe(true);
      });
    });
  });

  describe('2. Cascading Selection Triggers', () => {
    it('selecting segment triggers subSegment fetch', async () => {
      const { result } = renderHook(() => useOrgAssignment());
      
      // Wait for initial load
      await waitFor(() => {
        expect(result.current.segments.length).toBeGreaterThan(0);
      });
      
      // Select a segment
      act(() => {
        result.current.handleSegmentChange('1');
      });
      
      await waitFor(() => {
        expect(dropdownApi.getSubSegmentsBySegment).toHaveBeenCalledWith(1);
      });
    });

    it('selecting subSegment triggers project fetch', async () => {
      const { result } = renderHook(() => useOrgAssignment());
      
      // Select segment first
      act(() => {
        result.current.handleSegmentChange('1');
      });
      
      await waitFor(() => {
        expect(result.current.subSegments.length).toBeGreaterThan(0);
      });
      
      // Select sub-segment
      act(() => {
        result.current.handleSubSegmentChange('1');
      });
      
      await waitFor(() => {
        expect(dropdownApi.getProjects).toHaveBeenCalled();
      });
    });

    it('selecting project triggers team fetch', async () => {
      const { result } = renderHook(() => useOrgAssignment());
      
      // Set up cascade path
      act(() => {
        result.current.handleSegmentChange('1');
      });
      
      await waitFor(() => expect(result.current.subSegments.length).toBeGreaterThan(0));
      
      act(() => {
        result.current.handleSubSegmentChange('1');
      });
      
      await waitFor(() => expect(result.current.projects.length).toBeGreaterThan(0));
      
      // Select project
      act(() => {
        result.current.handleProjectChange('1');
      });
      
      await waitFor(() => {
        expect(dropdownApi.getTeams).toHaveBeenCalled();
      });
    });

    it('changing segment clears downstream selections', async () => {
      const { result } = renderHook(() => useOrgAssignment());
      
      // Set up full selection
      act(() => {
        result.current.handleSegmentChange('1');
      });
      await waitFor(() => expect(result.current.subSegments.length).toBeGreaterThan(0));
      
      act(() => {
        result.current.handleSubSegmentChange('1');
      });
      await waitFor(() => expect(result.current.projects.length).toBeGreaterThan(0));
      
      act(() => {
        result.current.handleProjectChange('1');
      });
      await waitFor(() => expect(result.current.teams.length).toBeGreaterThan(0));
      
      act(() => {
        result.current.handleTeamChange('1');
      });
      
      // Now change segment - should clear downstream
      act(() => {
        result.current.handleSegmentChange('2');
      });
      
      expect(result.current.selectedSubSegmentId).toBeNull();
      expect(result.current.selectedProjectId).toBeNull();
      expect(result.current.selectedTeamId).toBeNull();
    });
  });

  describe('3. Reset Functionality', () => {
    it('reset clears all selections except locked ones', async () => {
      // Super Admin can reset everything
      const { result } = renderHook(() => useOrgAssignment());
      
      // Make selections
      act(() => {
        result.current.handleSegmentChange('1');
      });
      await waitFor(() => expect(result.current.subSegments.length).toBeGreaterThan(0));
      
      act(() => {
        result.current.handleSubSegmentChange('1');
      });
      
      // Reset
      act(() => {
        result.current.reset();
      });
      
      expect(result.current.selectedSegmentId).toBeNull();
      expect(result.current.selectedSubSegmentId).toBeNull();
      expect(result.current.selectedProjectId).toBeNull();
      expect(result.current.selectedTeamId).toBeNull();
    });

    it('reset preserves locked selections for Segment Head', async () => {
      getRbacContext.mockReturnValue({
        role: RBAC_ROLES.SEGMENT_HEAD,
        scope: { segment_id: 1 }
      });
      
      const { result } = renderHook(() => useOrgAssignment());
      
      // Wait for preselection from scope
      await waitFor(() => {
        expect(result.current.selectedSegmentId).toBe(1);
      });
      
      // Make additional selection
      act(() => {
        result.current.handleSubSegmentChange('1');
      });
      
      // Reset
      act(() => {
        result.current.reset();
      });
      
      // Segment should remain (locked by role)
      expect(result.current.selectedSegmentId).toBe(1);
      // Sub-segment cleared
      expect(result.current.selectedSubSegmentId).toBeNull();
    });
  });
});
