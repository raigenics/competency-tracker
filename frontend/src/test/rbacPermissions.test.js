/**
 * RBAC Permissions Helper Unit Tests
 * 
 * Tests for src/rbac/permissions.js
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Use vi.hoisted to create mock state that's available during mock hoisting
const { mockRbacConfig } = vi.hoisted(() => ({
  mockRbacConfig: {
    currentRole: 'SUPER_ADMIN',
    currentScope: { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: null }
  }
}));

// Mock featureFlags before importing permissions
vi.mock('@/config/featureFlags.js', () => ({
  RBAC_ROLES: {
    SUPER_ADMIN: 'SUPER_ADMIN',
    SEGMENT_HEAD: 'SEGMENT_HEAD',
    SUBSEGMENT_HEAD: 'SUBSEGMENT_HEAD',
    PROJECT_MANAGER: 'PROJECT_MANAGER',
    TEAM_LEAD: 'TEAM_LEAD',
    TEAM_MEMBER: 'TEAM_MEMBER'
  },
  ROLE_PERMISSIONS: {
    SUPER_ADMIN: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'all' },
    SEGMENT_HEAD: { canView: true, canCreate: false, canUpdate: false, canDelete: false, scopeLevel: 'segment' },
    SUBSEGMENT_HEAD: { canView: true, canCreate: false, canUpdate: false, canDelete: false, scopeLevel: 'sub_segment' },
    PROJECT_MANAGER: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'project' },
    TEAM_LEAD: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'team' },
    TEAM_MEMBER: { canView: true, canCreate: true, canUpdate: true, canDelete: true, scopeLevel: 'team', selfOnly: true }
  },
  RBAC_CONFIG: mockRbacConfig
}));

// Import after mocks are set up
import {
  getPermissionsForRole,
  getCurrentRole,
  getCurrentScope,
  canShowAddEmployee,
  getRowActions,
  isViewOnlyRole,
  RBAC_ROLES
} from '@/rbac/permissions.js';

describe('RBAC Permissions Helper', () => {
  beforeEach(() => {
    // Reset to SUPER_ADMIN defaults
    mockRbacConfig.currentRole = 'SUPER_ADMIN';
    mockRbacConfig.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: null };
  });

  describe('getPermissionsForRole', () => {
    it('returns correct permissions for SUPER_ADMIN', () => {
      const permissions = getPermissionsForRole(RBAC_ROLES.SUPER_ADMIN);
      expect(permissions.canView).toBe(true);
      expect(permissions.canCreate).toBe(true);
      expect(permissions.canUpdate).toBe(true);
      expect(permissions.canDelete).toBe(true);
      expect(permissions.scopeLevel).toBe('all');
    });

    it('returns correct permissions for SEGMENT_HEAD', () => {
      const permissions = getPermissionsForRole(RBAC_ROLES.SEGMENT_HEAD);
      expect(permissions.canView).toBe(true);
      expect(permissions.canCreate).toBe(false);
      expect(permissions.canUpdate).toBe(false);
      expect(permissions.canDelete).toBe(false);
    });

    it('returns correct permissions for TEAM_MEMBER with selfOnly', () => {
      const permissions = getPermissionsForRole(RBAC_ROLES.TEAM_MEMBER);
      expect(permissions.canView).toBe(true);
      expect(permissions.canCreate).toBe(true);
      expect(permissions.selfOnly).toBe(true);
    });

    it('returns TEAM_MEMBER permissions for unknown role', () => {
      const permissions = getPermissionsForRole('UNKNOWN_ROLE');
      expect(permissions.selfOnly).toBe(true);
    });
  });

  describe('getCurrentRole', () => {
    it('returns the current role from config', () => {
      mockRbacConfig.currentRole = 'PROJECT_MANAGER';
      expect(getCurrentRole()).toBe('PROJECT_MANAGER');
    });
  });

  describe('getCurrentScope', () => {
    it('returns the current scope from config', () => {
      mockRbacConfig.currentScope = { segment_id: 1, sub_segment_id: 2, project_id: null, team_id: 3, employee_id: 10 };
      const scope = getCurrentScope();
      expect(scope.segment_id).toBe(1);
      expect(scope.team_id).toBe(3);
      expect(scope.employee_id).toBe(10);
    });
  });

  describe('canShowAddEmployee', () => {
    it('returns true for SUPER_ADMIN', () => {
      mockRbacConfig.currentRole = 'SUPER_ADMIN';
      expect(canShowAddEmployee()).toBe(true);
    });

    it('returns false for SEGMENT_HEAD (view-only)', () => {
      mockRbacConfig.currentRole = 'SEGMENT_HEAD';
      expect(canShowAddEmployee()).toBe(false);
    });

    it('returns false for SUBSEGMENT_HEAD (view-only)', () => {
      mockRbacConfig.currentRole = 'SUBSEGMENT_HEAD';
      expect(canShowAddEmployee()).toBe(false);
    });

    it('returns true for PROJECT_MANAGER', () => {
      mockRbacConfig.currentRole = 'PROJECT_MANAGER';
      expect(canShowAddEmployee()).toBe(true);
    });

    it('returns true for TEAM_LEAD', () => {
      mockRbacConfig.currentRole = 'TEAM_LEAD';
      expect(canShowAddEmployee()).toBe(true);
    });

    it('returns false for TEAM_MEMBER without employee_id (selfOnly)', () => {
      mockRbacConfig.currentRole = 'TEAM_MEMBER';
      mockRbacConfig.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: null };
      expect(canShowAddEmployee()).toBe(false);
    });

    it('returns false for TEAM_MEMBER with employee_id (already has record)', () => {
      mockRbacConfig.currentRole = 'TEAM_MEMBER';
      mockRbacConfig.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: 10 };
      expect(canShowAddEmployee()).toBe(false);
    });
  });

  describe('getRowActions', () => {
    it('returns all actions for SUPER_ADMIN', () => {
      mockRbacConfig.currentRole = 'SUPER_ADMIN';
      const actions = getRowActions({ employee: { employee_id: 1 } });
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(true);
      expect(actions.canDelete).toBe(true);
    });

    it('returns only View for SEGMENT_HEAD', () => {
      mockRbacConfig.currentRole = 'SEGMENT_HEAD';
      const actions = getRowActions({ employee: { employee_id: 1 } });
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(false);
      expect(actions.canDelete).toBe(false);
    });

    it('returns only View for TEAM_MEMBER on other employee row', () => {
      mockRbacConfig.currentRole = 'TEAM_MEMBER';
      mockRbacConfig.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: 10 };
      const actions = getRowActions({ employee: { employee_id: 99 } }); // Different employee
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(false);
      expect(actions.canDelete).toBe(false);
    });

    it('returns Edit/Delete for TEAM_MEMBER on own row', () => {
      mockRbacConfig.currentRole = 'TEAM_MEMBER';
      mockRbacConfig.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: 10 };
      const actions = getRowActions({ employee: { employee_id: 10 } }); // Same employee
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(true);
      expect(actions.canDelete).toBe(true);
    });

    it('returns Edit/Delete for TEAM_MEMBER on own row using id field', () => {
      mockRbacConfig.currentRole = 'TEAM_MEMBER';
      mockRbacConfig.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: 10 };
      const actions = getRowActions({ employee: { id: 10 } }); // Using id field
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(true);
      expect(actions.canDelete).toBe(true);
    });

    it('returns all actions for PROJECT_MANAGER', () => {
      mockRbacConfig.currentRole = 'PROJECT_MANAGER';
      const actions = getRowActions({ employee: { employee_id: 1 } });
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(true);
      expect(actions.canDelete).toBe(true);
    });

    it('returns all actions for TEAM_LEAD', () => {
      mockRbacConfig.currentRole = 'TEAM_LEAD';
      const actions = getRowActions({ employee: { employee_id: 1 } });
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(true);
      expect(actions.canDelete).toBe(true);
    });

    it('handles missing employee gracefully for TEAM_MEMBER', () => {
      mockRbacConfig.currentRole = 'TEAM_MEMBER';
      mockRbacConfig.currentScope = { segment_id: null, sub_segment_id: null, project_id: null, team_id: null, employee_id: 10 };
      const actions = getRowActions({}); // No employee
      expect(actions.canView).toBe(true);
      expect(actions.canEdit).toBe(false);
      expect(actions.canDelete).toBe(false);
    });
  });

  describe('isViewOnlyRole', () => {
    it('returns false for SUPER_ADMIN', () => {
      expect(isViewOnlyRole(RBAC_ROLES.SUPER_ADMIN)).toBe(false);
    });

    it('returns true for SEGMENT_HEAD', () => {
      expect(isViewOnlyRole(RBAC_ROLES.SEGMENT_HEAD)).toBe(true);
    });

    it('returns true for SUBSEGMENT_HEAD', () => {
      expect(isViewOnlyRole(RBAC_ROLES.SUBSEGMENT_HEAD)).toBe(true);
    });

    it('returns false for PROJECT_MANAGER', () => {
      expect(isViewOnlyRole(RBAC_ROLES.PROJECT_MANAGER)).toBe(false);
    });

    it('returns false for TEAM_LEAD', () => {
      expect(isViewOnlyRole(RBAC_ROLES.TEAM_LEAD)).toBe(false);
    });

    it('returns false for TEAM_MEMBER (has CRUD for self)', () => {
      expect(isViewOnlyRole(RBAC_ROLES.TEAM_MEMBER)).toBe(false);
    });
  });
});
