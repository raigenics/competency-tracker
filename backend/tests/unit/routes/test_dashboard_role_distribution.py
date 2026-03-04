"""
Unit tests for Dashboard Role Distribution API route.

Tests the GET /dashboard/role-distribution endpoint with various
context levels and edge cases.

Uses mocked service layer to isolate route logic.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.dashboard_role_distribution import router
from app.services.dashboard.role_distribution_service import (
    RoleDistributionResult,
    ScopeData,
    BreakdownRowData,
    RoleCountData,
    EntityNotFoundError,
    InvalidHierarchyError
)


# Create test app with the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_segment_result():
    """Create a mock result for SEGMENT context."""
    return RoleDistributionResult(
        context_level="SEGMENT",
        title="Role Distribution by Segment DTS",
        subtitle="Employee count by role across Sub-Segments",
        breakdown_label="Sub-Segment",
        scope=ScopeData(
            segment_id=1,
            segment_name="DTS"
        ),
        rows=[
            BreakdownRowData(
                breakdown_id=1,
                breakdown_name="ADT",
                total_employees=54,
                roles=[
                    RoleCountData(role_id=1, role_name="Frontend Dev", employee_count=12),
                    RoleCountData(role_id=2, role_name="Backend Dev", employee_count=10),
                    RoleCountData(role_id=3, role_name="Full Stack", employee_count=8),
                    RoleCountData(role_id=4, role_name="Cloud Eng", employee_count=7),
                    RoleCountData(role_id=5, role_name="DevOps", employee_count=6),
                ]
            ),
            BreakdownRowData(
                breakdown_id=2,
                breakdown_name="AU",
                total_employees=65,
                roles=[
                    RoleCountData(role_id=1, role_name="Frontend Dev", employee_count=18),
                    RoleCountData(role_id=2, role_name="Backend Dev", employee_count=15),
                    RoleCountData(role_id=3, role_name="Full Stack", employee_count=11),
                ]
            )
        ]
    )


@pytest.fixture
def mock_sub_segment_result():
    """Create a mock result for SUB_SEGMENT context."""
    return RoleDistributionResult(
        context_level="SUB_SEGMENT",
        title="Role Distribution by Sub-Segment ADT",
        subtitle="Employee count by role across Projects",
        breakdown_label="Project",
        scope=ScopeData(
            segment_id=1,
            segment_name="DTS",
            sub_segment_id=1,
            sub_segment_name="ADT"
        ),
        rows=[
            BreakdownRowData(
                breakdown_id=10,
                breakdown_name="Aspire",
                total_employees=22,
                roles=[
                    RoleCountData(role_id=1, role_name="Frontend Dev", employee_count=5),
                    RoleCountData(role_id=2, role_name="Backend Dev", employee_count=4),
                    RoleCountData(role_id=3, role_name="Full Stack", employee_count=3),
                ]
            )
        ]
    )


@pytest.fixture
def mock_project_result():
    """Create a mock result for PROJECT context."""
    return RoleDistributionResult(
        context_level="PROJECT",
        title="Role Distribution by Sub-Segment → Project Aspire",
        subtitle="Employee count by role across Teams",
        breakdown_label="Team",
        scope=ScopeData(
            segment_id=1,
            segment_name="DTS",
            sub_segment_id=1,
            sub_segment_name="ADT",
            project_id=10,
            project_name="Aspire"
        ),
        rows=[
            BreakdownRowData(
                breakdown_id=100,
                breakdown_name="Team Alpha",
                total_employees=8,
                roles=[
                    RoleCountData(role_id=1, role_name="Frontend Dev", employee_count=2),
                    RoleCountData(role_id=2, role_name="Backend Dev", employee_count=2),
                ]
            )
        ]
    )


@pytest.fixture
def mock_team_result():
    """Create a mock result for TEAM context."""
    return RoleDistributionResult(
        context_level="TEAM",
        title="Role Distribution by Sub-Segment → Project → Team Team Alpha",
        subtitle="Employee count by role across Employees",
        breakdown_label="Team",
        scope=ScopeData(
            segment_id=1,
            segment_name="DTS",
            sub_segment_id=1,
            sub_segment_name="ADT",
            project_id=10,
            project_name="Aspire",
            team_id=100,
            team_name="Team Alpha"
        ),
        rows=[
            BreakdownRowData(
                breakdown_id=100,
                breakdown_name="Team Alpha",
                total_employees=8,
                roles=[
                    RoleCountData(role_id=1, role_name="Frontend Dev", employee_count=2),
                    RoleCountData(role_id=2, role_name="Backend Dev", employee_count=2),
                ]
            )
        ]
    )


# =============================================================================
# TEST: SEGMENT CONTEXT
# =============================================================================

class TestSegmentContext:
    """Test SEGMENT context (breakdown by sub-segments)."""
    
    def test_returns_segment_context_with_sub_segment_breakdown(self, mock_segment_result):
        """Should return SEGMENT context when only segment_id provided."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_segment_result
        ):
            response = client.get('/dashboard/role-distribution?segment_id=1')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['context_level'] == 'SEGMENT'
        assert data['breakdown_label'] == 'Sub-Segment'
        assert 'Role Distribution by Segment DTS' in data['title']
        assert 'Sub-Segments' in data['subtitle']
    
    def test_rows_include_adt_and_au(self, mock_segment_result):
        """Should include ADT and AU in breakdown rows."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_segment_result
        ):
            response = client.get('/dashboard/role-distribution?segment_id=1')
        
        data = response.json()
        row_names = [row['breakdown_name'] for row in data['rows']]
        
        assert 'ADT' in row_names
        assert 'AU' in row_names
    
    def test_counts_correct_and_top_roles_sorted_desc(self, mock_segment_result):
        """Should have correct counts with top_roles sorted by count descending."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_segment_result
        ):
            response = client.get('/dashboard/role-distribution?segment_id=1')
        
        data = response.json()
        adt_row = next(r for r in data['rows'] if r['breakdown_name'] == 'ADT')
        
        assert adt_row['total_employees'] == 54
        
        # Top roles should be sorted desc by count
        top_roles = adt_row['top_roles']
        counts = [r['employee_count'] for r in top_roles]
        assert counts == sorted(counts, reverse=True)


# =============================================================================
# TEST: SUB_SEGMENT CONTEXT
# =============================================================================

class TestSubSegmentContext:
    """Test SUB_SEGMENT context (breakdown by projects)."""
    
    def test_returns_sub_segment_context_with_project_breakdown(self, mock_sub_segment_result):
        """Should return SUB_SEGMENT context when sub_segment_id provided."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_sub_segment_result
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=1'
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['context_level'] == 'SUB_SEGMENT'
        assert data['breakdown_label'] == 'Project'
        assert 'Sub-Segment ADT' in data['title']
        assert 'Projects' in data['subtitle']
    
    def test_only_projects_under_selected_sub_segment(self, mock_sub_segment_result):
        """Should only include projects under the selected sub-segment."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_sub_segment_result
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=1'
            )
        
        data = response.json()
        
        # Should have Aspire project
        assert any(r['breakdown_name'] == 'Aspire' for r in data['rows'])


# =============================================================================
# TEST: PROJECT CONTEXT
# =============================================================================

class TestProjectContext:
    """Test PROJECT context (breakdown by teams)."""
    
    def test_returns_project_context_with_team_breakdown(self, mock_project_result):
        """Should return PROJECT context when project_id provided."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_project_result
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=1&project_id=10'
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['context_level'] == 'PROJECT'
        assert data['breakdown_label'] == 'Team'
        assert 'Project Aspire' in data['title']
        assert 'Teams' in data['subtitle']
    
    def test_only_teams_under_selected_project(self, mock_project_result):
        """Should only include teams under the selected project."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_project_result
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=1&project_id=10'
            )
        
        data = response.json()
        
        # Should have Team Alpha
        assert any(r['breakdown_name'] == 'Team Alpha' for r in data['rows'])


# =============================================================================
# TEST: TEAM CONTEXT
# =============================================================================

class TestTeamContext:
    """Test TEAM context (single team row)."""
    
    def test_returns_team_context_single_row(self, mock_team_result):
        """Should return TEAM context with single row when team_id provided."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_team_result
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=1&project_id=10&team_id=100'
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['context_level'] == 'TEAM'
        assert len(data['rows']) == 1
        assert data['rows'][0]['breakdown_name'] == 'Team Alpha'


# =============================================================================
# TEST: SOFT DELETE HANDLING
# =============================================================================

class TestSoftDeleteHandling:
    """Test soft delete rules are respected."""
    
    def test_soft_deleted_employee_reduces_count(self, mock_segment_result):
        """
        Service should exclude soft-deleted employees.
        This test verifies the route correctly returns the service result.
        """
        # Create modified result with reduced count (simulating soft delete)
        mock_segment_result.rows[0].total_employees = 53  # One employee deleted
        mock_segment_result.rows[0].roles[0].employee_count = 11  # One less
        
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_segment_result
        ):
            response = client.get('/dashboard/role-distribution?segment_id=1')
        
        data = response.json()
        adt_row = next(r for r in data['rows'] if r['breakdown_name'] == 'ADT')
        
        assert adt_row['total_employees'] == 53


# =============================================================================
# TEST: INCLUDE_EMPTY PARAMETER
# =============================================================================

class TestIncludeEmptyParameter:
    """Test include_empty parameter."""
    
    def test_include_empty_true_returns_empty_rows(self):
        """Should include breakdown items with zero employees when include_empty=true."""
        result_with_empty = RoleDistributionResult(
            context_level="SEGMENT",
            title="Role Distribution by Segment DTS",
            subtitle="Employee count by role across Sub-Segments",
            breakdown_label="Sub-Segment",
            scope=ScopeData(segment_id=1, segment_name="DTS"),
            rows=[
                BreakdownRowData(
                    breakdown_id=1,
                    breakdown_name="ADT",
                    total_employees=54,
                    roles=[RoleCountData(role_id=1, role_name="Frontend Dev", employee_count=12)]
                ),
                BreakdownRowData(
                    breakdown_id=3,
                    breakdown_name="EmptySeg",
                    total_employees=0,
                    roles=[]
                )
            ]
        )
        
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=result_with_empty
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&include_empty=true'
            )
        
        data = response.json()
        
        # Should include the empty row
        assert any(r['breakdown_name'] == 'EmptySeg' for r in data['rows'])
        empty_row = next(r for r in data['rows'] if r['breakdown_name'] == 'EmptySeg')
        assert empty_row['total_employees'] == 0
        assert empty_row['top_roles'] == []
        assert empty_row['all_roles'] == []
        assert empty_row['more_roles_count'] == 0


# =============================================================================
# TEST: INVALID HIERARCHY
# =============================================================================

class TestInvalidHierarchy:
    """Test invalid hierarchy returns 400."""
    
    def test_project_not_under_sub_segment_returns_400(self):
        """Should return 400 when project doesn't belong to sub_segment."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            side_effect=InvalidHierarchyError(
                "Project 999 does not belong to sub-segment 1"
            )
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=1&project_id=999'
            )
        
        assert response.status_code == 400
        assert 'does not belong' in response.json()['detail']
    
    def test_project_without_sub_segment_returns_400(self):
        """Should return 400 when project_id provided without sub_segment_id."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            side_effect=InvalidHierarchyError("project_id requires sub_segment_id")
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&project_id=10'
            )
        
        assert response.status_code == 400
        assert 'requires' in response.json()['detail']
    
    def test_team_without_project_returns_400(self):
        """Should return 400 when team_id provided without project_id."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            side_effect=InvalidHierarchyError("team_id requires project_id")
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=1&team_id=100'
            )
        
        assert response.status_code == 400
        assert 'requires' in response.json()['detail']


# =============================================================================
# TEST: ENTITY NOT FOUND
# =============================================================================

class TestEntityNotFound:
    """Test entity not found returns 404."""
    
    def test_segment_not_found_returns_404(self):
        """Should return 404 when segment doesn't exist."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            side_effect=EntityNotFoundError("Segment with ID 999 not found or deleted")
        ):
            response = client.get('/dashboard/role-distribution?segment_id=999')
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']
    
    def test_sub_segment_not_found_returns_404(self):
        """Should return 404 when sub-segment doesn't exist."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            side_effect=EntityNotFoundError("Sub-segment with ID 999 not found or deleted")
        ):
            response = client.get(
                '/dashboard/role-distribution?segment_id=1&sub_segment_id=999'
            )
        
        assert response.status_code == 404


# =============================================================================
# TEST: VALIDATION
# =============================================================================

class TestValidation:
    """Test parameter validation."""
    
    def test_missing_segment_id_returns_422(self):
        """Should return 422 when segment_id is missing."""
        response = client.get('/dashboard/role-distribution')
        
        assert response.status_code == 422
    
    def test_invalid_segment_id_returns_422(self):
        """Should return 422 when segment_id is invalid."""
        response = client.get('/dashboard/role-distribution?segment_id=invalid')
        
        assert response.status_code == 422
    
    def test_negative_segment_id_returns_422(self):
        """Should return 422 when segment_id is negative."""
        response = client.get('/dashboard/role-distribution?segment_id=-1')
        
        assert response.status_code == 422
    
    def test_top_n_exceeds_limit_returns_422(self):
        """Should return 422 when top_n exceeds max (10)."""
        response = client.get('/dashboard/role-distribution?segment_id=1&top_n=20')
        
        assert response.status_code == 422


# =============================================================================
# TEST: RESPONSE STRUCTURE
# =============================================================================

class TestResponseStructure:
    """Test response has correct structure."""
    
    def test_response_has_all_required_fields(self, mock_segment_result):
        """Should return response with all required fields."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_segment_result
        ):
            response = client.get('/dashboard/role-distribution?segment_id=1')
        
        assert response.status_code == 200
        data = response.json()
        
        # Top-level fields
        assert 'context_level' in data
        assert 'title' in data
        assert 'subtitle' in data
        assert 'breakdown_label' in data
        assert 'scope' in data
        assert 'rows' in data
        
        # Scope fields
        scope = data['scope']
        assert 'segment_id' in scope
        assert 'segment_name' in scope
        
        # Row fields
        if data['rows']:
            row = data['rows'][0]
            assert 'breakdown_id' in row
            assert 'breakdown_name' in row
            assert 'total_employees' in row
            assert 'top_roles' in row
            assert 'all_roles' in row
            assert 'more_roles_count' in row
    
    def test_more_roles_count_computed_correctly(self, mock_segment_result):
        """Should correctly compute more_roles_count."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            return_value=mock_segment_result
        ):
            response = client.get('/dashboard/role-distribution?segment_id=1&top_n=3')
        
        data = response.json()
        adt_row = next(r for r in data['rows'] if r['breakdown_name'] == 'ADT')
        
        # ADT has 5 roles, top_n=3, so more_roles_count = 2
        assert adt_row['more_roles_count'] == 2


# =============================================================================
# TEST: ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test error handling."""
    
    def test_service_exception_returns_500(self):
        """Should return 500 when service throws unexpected exception."""
        with patch(
            'app.api.routes.dashboard_role_distribution.get_role_distribution',
            side_effect=Exception("Unexpected database error")
        ):
            response = client.get('/dashboard/role-distribution?segment_id=1')
        
        assert response.status_code == 500
        assert 'Failed to retrieve' in response.json()['detail']
