"""
Unit tests for security/rbac_policy.py

Tests role definitions, permissions, and scope filtering.
"""
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from app.security.rbac_policy import (
    Role,
    Permission,
    Scope,
    RbacContext,
    ROLE_PERMISSIONS,
    get_rbac_context,
    apply_employee_scope_filter,
    check_crud_permission
)


class TestRoleDefinitions:
    """Test role enum and mapping."""
    
    def test_all_roles_have_permissions(self):
        """Every role should have an entry in ROLE_PERMISSIONS."""
        for role in Role:
            assert role in ROLE_PERMISSIONS, f"Role {role} missing from ROLE_PERMISSIONS"
    
    def test_super_admin_has_all_permissions(self):
        """SUPER_ADMIN should have full CRUD permissions."""
        perm = ROLE_PERMISSIONS[Role.SUPER_ADMIN]
        assert perm.can_view is True
        assert perm.can_create is True
        assert perm.can_update is True
        assert perm.can_delete is True
        assert perm.scope_level == "all"
    
    def test_segment_head_is_view_only(self):
        """SEGMENT_HEAD should have view-only permissions."""
        perm = ROLE_PERMISSIONS[Role.SEGMENT_HEAD]
        assert perm.can_view is True
        assert perm.can_create is False
        assert perm.can_update is False
        assert perm.can_delete is False
        assert perm.scope_level == "segment"
    
    def test_subsegment_head_is_view_only(self):
        """SUBSEGMENT_HEAD should have view-only permissions."""
        perm = ROLE_PERMISSIONS[Role.SUBSEGMENT_HEAD]
        assert perm.can_view is True
        assert perm.can_create is False
        assert perm.can_update is False
        assert perm.can_delete is False
        assert perm.scope_level == "sub_segment"
    
    def test_project_manager_has_full_crud(self):
        """PROJECT_MANAGER should have full CRUD for their project."""
        perm = ROLE_PERMISSIONS[Role.PROJECT_MANAGER]
        assert perm.can_view is True
        assert perm.can_create is True
        assert perm.can_update is True
        assert perm.can_delete is True
        assert perm.scope_level == "project"
    
    def test_team_lead_has_full_crud(self):
        """TEAM_LEAD should have full CRUD for their team."""
        perm = ROLE_PERMISSIONS[Role.TEAM_LEAD]
        assert perm.can_view is True
        assert perm.can_create is True
        assert perm.can_update is True
        assert perm.can_delete is True
        assert perm.scope_level == "team"
    
    def test_team_member_is_self_only(self):
        """TEAM_MEMBER should have self_only flag for CRUD."""
        perm = ROLE_PERMISSIONS[Role.TEAM_MEMBER]
        assert perm.can_view is True
        assert perm.can_create is True
        assert perm.can_update is True
        assert perm.can_delete is True
        assert perm.scope_level == "team"
        assert perm.self_only is True


class TestRbacContext:
    """Test RbacContext permission checking methods."""
    
    def test_super_admin_can_view_all(self):
        """SUPER_ADMIN can_view should return True."""
        ctx = RbacContext(
            role=Role.SUPER_ADMIN,
            scope=Scope(),
            permissions=ROLE_PERMISSIONS[Role.SUPER_ADMIN]
        )
        assert ctx.can_view() is True
    
    def test_super_admin_can_update_any_employee(self):
        """SUPER_ADMIN can update any employee."""
        ctx = RbacContext(
            role=Role.SUPER_ADMIN,
            scope=Scope(),
            permissions=ROLE_PERMISSIONS[Role.SUPER_ADMIN]
        )
        assert ctx.can_update(target_employee_id=999) is True
    
    def test_segment_head_cannot_create(self):
        """SEGMENT_HEAD cannot create."""
        ctx = RbacContext(
            role=Role.SEGMENT_HEAD,
            scope=Scope(segment_id=1),
            permissions=ROLE_PERMISSIONS[Role.SEGMENT_HEAD]
        )
        assert ctx.can_create() is False
    
    def test_team_member_can_update_self(self):
        """TEAM_MEMBER can update their own record."""
        ctx = RbacContext(
            role=Role.TEAM_MEMBER,
            scope=Scope(team_id=1, employee_id=100),
            permissions=ROLE_PERMISSIONS[Role.TEAM_MEMBER]
        )
        assert ctx.can_update(target_employee_id=100) is True
    
    def test_team_member_cannot_update_other(self):
        """TEAM_MEMBER cannot update another employee's record."""
        ctx = RbacContext(
            role=Role.TEAM_MEMBER,
            scope=Scope(team_id=1, employee_id=100),
            permissions=ROLE_PERMISSIONS[Role.TEAM_MEMBER]
        )
        assert ctx.can_update(target_employee_id=200) is False
    
    def test_team_member_can_delete_self(self):
        """TEAM_MEMBER can delete their own record."""
        ctx = RbacContext(
            role=Role.TEAM_MEMBER,
            scope=Scope(team_id=1, employee_id=100),
            permissions=ROLE_PERMISSIONS[Role.TEAM_MEMBER]
        )
        assert ctx.can_delete(target_employee_id=100) is True
    
    def test_team_member_cannot_delete_other(self):
        """TEAM_MEMBER cannot delete another employee's record."""
        ctx = RbacContext(
            role=Role.TEAM_MEMBER,
            scope=Scope(team_id=1, employee_id=100),
            permissions=ROLE_PERMISSIONS[Role.TEAM_MEMBER]
        )
        assert ctx.can_delete(target_employee_id=200) is False


class TestGetRbacContext:
    """Test the FastAPI dependency for extracting RBAC context."""
    
    @pytest.mark.asyncio
    async def test_default_to_super_admin_when_no_header(self):
        """Should default to SUPER_ADMIN when no role header provided."""
        ctx = await get_rbac_context(
            x_rbac_role=None,
            x_rbac_scope_segment=None,
            x_rbac_scope_sub_segment=None,
            x_rbac_scope_project=None,
            x_rbac_scope_team=None,
            x_rbac_scope_employee=None
        )
        assert ctx.role == Role.SUPER_ADMIN
    
    @pytest.mark.asyncio
    async def test_parses_valid_role_header(self):
        """Should parse valid role from header."""
        ctx = await get_rbac_context(
            x_rbac_role="TEAM_LEAD",
            x_rbac_scope_segment=None,
            x_rbac_scope_sub_segment=None,
            x_rbac_scope_project=None,
            x_rbac_scope_team=None,
            x_rbac_scope_employee=None
        )
        assert ctx.role == Role.TEAM_LEAD
    
    @pytest.mark.asyncio
    async def test_parses_scope_ids(self):
        """Should parse scope IDs from headers."""
        ctx = await get_rbac_context(
            x_rbac_role="PROJECT_MANAGER",
            x_rbac_scope_segment="1",
            x_rbac_scope_sub_segment="2",
            x_rbac_scope_project="3",
            x_rbac_scope_team="4",
            x_rbac_scope_employee="5"
        )
        assert ctx.scope.segment_id == 1
        assert ctx.scope.sub_segment_id == 2
        assert ctx.scope.project_id == 3
        assert ctx.scope.team_id == 4
        assert ctx.scope.employee_id == 5
    
    @pytest.mark.asyncio
    async def test_handles_null_string_scope(self):
        """Should treat 'null' string as None."""
        ctx = await get_rbac_context(
            x_rbac_role="SUPER_ADMIN",
            x_rbac_scope_segment="null",
            x_rbac_scope_sub_segment=None,
            x_rbac_scope_project=None,
            x_rbac_scope_team=None,
            x_rbac_scope_employee=None
        )
        assert ctx.scope.segment_id is None
    
    @pytest.mark.asyncio
    async def test_handles_invalid_role(self):
        """Should default to SUPER_ADMIN for invalid role."""
        ctx = await get_rbac_context(
            x_rbac_role="INVALID_ROLE",
            x_rbac_scope_segment=None,
            x_rbac_scope_sub_segment=None,
            x_rbac_scope_project=None,
            x_rbac_scope_team=None,
            x_rbac_scope_employee=None
        )
        assert ctx.role == Role.SUPER_ADMIN
    
    @pytest.mark.asyncio
    async def test_handles_invalid_scope_id(self):
        """Should set scope to None for non-integer values."""
        ctx = await get_rbac_context(
            x_rbac_role="TEAM_LEAD",
            x_rbac_scope_segment=None,
            x_rbac_scope_sub_segment=None,
            x_rbac_scope_project=None,
            x_rbac_scope_team="not_a_number",
            x_rbac_scope_employee=None
        )
        assert ctx.scope.team_id is None


class TestApplyEmployeeScopeFilter:
    """Test scope filtering for employee queries."""
    
    def test_super_admin_no_filter(self):
        """SUPER_ADMIN should not apply any filter."""
        ctx = RbacContext(
            role=Role.SUPER_ADMIN,
            scope=Scope(),
            permissions=ROLE_PERMISSIONS[Role.SUPER_ADMIN]
        )
        mock_query = MagicMock()
        mock_employee_model = MagicMock()
        
        result = apply_employee_scope_filter(mock_query, mock_employee_model, ctx)
        
        # Query should be returned unchanged
        assert result == mock_query
        mock_query.filter.assert_not_called()
    
    def test_team_lead_filters_by_team(self):
        """TEAM_LEAD should filter by team_id."""
        ctx = RbacContext(
            role=Role.TEAM_LEAD,
            scope=Scope(team_id=5),
            permissions=ROLE_PERMISSIONS[Role.TEAM_LEAD]
        )
        mock_query = MagicMock()
        mock_employee_model = MagicMock()
        mock_employee_model.team_id = "team_id_column"
        
        apply_employee_scope_filter(mock_query, mock_employee_model, ctx)
        
        mock_query.filter.assert_called()
    
    def test_team_scope_without_id_returns_empty(self):
        """Team scope without team_id should return empty result."""
        ctx = RbacContext(
            role=Role.TEAM_LEAD,
            scope=Scope(team_id=None),  # No team_id set
            permissions=ROLE_PERMISSIONS[Role.TEAM_LEAD]
        )
        mock_query = MagicMock()
        mock_employee_model = MagicMock()
        
        apply_employee_scope_filter(mock_query, mock_employee_model, ctx)
        
        # Should filter with False (empty result)
        mock_query.filter.assert_called_with(False)


class TestCheckCrudPermission:
    """Test the check_crud_permission utility function."""
    
    def test_view_permission(self):
        """Should check can_view for view action."""
        ctx = RbacContext(
            role=Role.SEGMENT_HEAD,
            scope=Scope(segment_id=1),
            permissions=ROLE_PERMISSIONS[Role.SEGMENT_HEAD]
        )
        assert check_crud_permission(ctx, "view") is True
    
    def test_create_permission_denied(self):
        """Should return False when role cannot create."""
        ctx = RbacContext(
            role=Role.SEGMENT_HEAD,
            scope=Scope(segment_id=1),
            permissions=ROLE_PERMISSIONS[Role.SEGMENT_HEAD]
        )
        assert check_crud_permission(ctx, "create") is False
    
    def test_create_permission_allowed(self):
        """Should return True when role can create."""
        ctx = RbacContext(
            role=Role.PROJECT_MANAGER,
            scope=Scope(project_id=1),
            permissions=ROLE_PERMISSIONS[Role.PROJECT_MANAGER]
        )
        assert check_crud_permission(ctx, "create") is True
    
    def test_invalid_action_returns_false(self):
        """Should return False for unknown action."""
        ctx = RbacContext(
            role=Role.SUPER_ADMIN,
            scope=Scope(),
            permissions=ROLE_PERMISSIONS[Role.SUPER_ADMIN]
        )
        assert check_crud_permission(ctx, "invalid_action") is False
