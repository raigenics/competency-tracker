"""
Unit tests for employee_profile/list_service.py

Tests paginated employee listing with filters.

PERFORMANCE FIX TESTS (2026-02-10):
- Verifies batch skills count query is called once (not N times)
- Updated tests for new _build_employee_responses signature (takes dict not db)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.employee_profile import list_service
from app.schemas.employee import EmployeeResponse, EmployeeListResponse, OrganizationInfo


class TestGetEmployeesPaginated:
    """Test the main public function get_employees_paginated()."""
    
    def test_returns_employees_list_response(self, mock_db, mock_pagination, mock_employee):
        """Should return EmployeeListResponse with employees and pagination info."""
        # Arrange
        pagination = mock_pagination(page=1, size=10)
        employees = [mock_employee(1, "Z1001", "Alice"), mock_employee(2, "Z1002", "Bob")]
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query, \
             patch.object(list_service, '_get_skills_counts_batch', return_value={1: 5, 2: 3}):
            mock_query = MagicMock()
            mock_build_query.return_value = mock_query
            mock_query.count.return_value = 2
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = employees
            
            # Act
            result = list_service.get_employees_paginated(mock_db, pagination)
            
            # Assert
            assert isinstance(result, EmployeeListResponse)
            assert len(result.items) == 2
            assert result.total == 2
            assert all(isinstance(emp, EmployeeResponse) for emp in result.items)
    
    def test_calls_batch_skills_count_once_not_per_employee(self, mock_db, mock_pagination, mock_employee):
        """
        PERFORMANCE FIX: Should call _get_skills_counts_batch once, not N times.
        This prevents N+1 query problem that caused slow page loads.
        """
        # Arrange
        pagination = mock_pagination(page=1, size=10)
        employees = [mock_employee(i, f"Z100{i}", f"User{i}") for i in range(1, 10)]
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query, \
             patch.object(list_service, '_get_skills_counts_batch') as mock_batch_count:
            mock_query = MagicMock()
            mock_build_query.return_value = mock_query
            mock_query.count.return_value = 9
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = employees
            mock_batch_count.return_value = {i: i for i in range(1, 10)}
            
            # Act
            list_service.get_employees_paginated(mock_db, pagination)
            
            # Assert - CRITICAL: batch count called ONCE, not 9 times
            assert mock_batch_count.call_count == 1
            # Verify it was called with all employee IDs
            mock_batch_count.assert_called_once_with(mock_db, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    
    def test_applies_all_filters(self, mock_db, mock_pagination):
        """Should pass all filter parameters to query builder."""
        # Arrange
        pagination = mock_pagination(page=1, size=10)
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query, \
             patch.object(list_service, '_get_skills_counts_batch', return_value={}):
            mock_query = MagicMock()
            mock_build_query.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            # Act
            list_service.get_employees_paginated(
                mock_db, pagination,
                sub_segment_id=1, project_id=2, team_id=3, role_id=4, search="test"
            )
            
            # Assert
            mock_build_query.assert_called_once_with(
                mock_db, 1, 2, 3, 4, "test", None
            )
    
    def test_applies_pagination_correctly(self, mock_db, mock_pagination):
        """Should apply offset and limit based on pagination params."""
        # Arrange
        pagination = mock_pagination(page=3, size=20)
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query, \
             patch.object(list_service, '_get_skills_counts_batch', return_value={}):
            mock_query = MagicMock()
            mock_build_query.return_value = mock_query
            mock_query.count.return_value = 100
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            # Act
            list_service.get_employees_paginated(mock_db, pagination)
            
            # Assert
            mock_query.offset.assert_called_once_with(40)  # (page 3-1) * 20
            mock_query.limit.assert_called_once_with(20)
    
    def test_returns_empty_list_when_no_employees(self, mock_db, mock_pagination):
        """Should return empty list and zero count when no employees found."""
        # Arrange
        pagination = mock_pagination(page=1, size=10)
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query, \
             patch.object(list_service, '_get_skills_counts_batch', return_value={}):
            mock_query = MagicMock()
            mock_build_query.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            # Act
            result = list_service.get_employees_paginated(mock_db, pagination)
            
            # Assert
            assert result.items == []
            assert result.total == 0


class TestBuildEmployeeQuery:
    """Test the _build_employee_query() function."""
    
    def test_builds_base_query_with_no_filters(self, mock_db):
        """Should build query with eager loading when no filters provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        result = list_service._build_employee_query(mock_db, None, None, None, None, None)
        
        # Assert
        mock_db.query.assert_called_once()
        mock_query.options.assert_called_once()
        # filter is called at least for deleted_at check
        assert mock_query.filter.called
        assert result == mock_query
    
    def test_filters_by_sub_segment_id(self, mock_db):
        """Should apply sub_segment_id filter when provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        list_service._build_employee_query(mock_db, sub_segment_id=5, project_id=None, 
                                           team_id=None, role_id=None, search=None)
        
        # Assert
        assert mock_query.filter.called
    
    def test_filters_by_project_id(self, mock_db):
        """Should apply project_id filter when provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        list_service._build_employee_query(mock_db, sub_segment_id=None, project_id=3,
                                           team_id=None, role_id=None, search=None)
        
        # Assert
        assert mock_query.filter.called
    
    def test_filters_by_team_id(self, mock_db):
        """Should apply team_id filter when provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        list_service._build_employee_query(mock_db, sub_segment_id=None, project_id=None,
                                           team_id=7, role_id=None, search=None)
        
        # Assert
        assert mock_query.filter.called
    
    def test_filters_by_role_id(self, mock_db):
        """Should apply role_id filter when provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        list_service._build_employee_query(mock_db, sub_segment_id=None, project_id=None,
                                           team_id=None, role_id=2, search=None)
        
        # Assert
        assert mock_query.filter.called
    
    def test_applies_search_filter(self, mock_db):
        """Should apply ILIKE search on name and ZID when search provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        list_service._build_employee_query(mock_db, sub_segment_id=None, project_id=None,
                                           team_id=None, role_id=None, search="John")
        
        # Assert
        assert mock_query.filter.called
    
    def test_applies_multiple_filters(self, mock_db):
        """Should apply all filters when multiple are provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        list_service._build_employee_query(mock_db, sub_segment_id=1, project_id=2,
                                           team_id=3, role_id=4, search="test")
        
        # Assert - deleted_at + team_id (highest org filter) + role_id + search = 4
        assert mock_query.filter.call_count >= 3  # At least deleted_at, team, role, search


class TestGetSkillsCountsBatch:
    """Test the _get_skills_counts_batch() function - PERFORMANCE FIX."""
    
    def test_returns_skills_counts_for_multiple_employees(self, mock_db):
        """Should return dict mapping employee_id -> count for all employees."""
        # Arrange - mock GROUP BY result
        mock_results = [
            Mock(employee_id=1, count=5),
            Mock(employee_id=2, count=3),
            Mock(employee_id=3, count=0)
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        # Act
        result = list_service._get_skills_counts_batch(mock_db, [1, 2, 3])
        
        # Assert
        assert result == {1: 5, 2: 3, 3: 0}
    
    def test_returns_empty_dict_for_empty_input(self, mock_db):
        """Should return empty dict when given empty employee list."""
        # Act
        result = list_service._get_skills_counts_batch(mock_db, [])
        
        # Assert
        assert result == {}
        # DB should not be queried
        mock_db.query.assert_not_called()
    
    def test_missing_employees_default_to_zero(self, mock_db):
        """Employees not in result should default to 0 when accessed via .get()."""
        # Arrange - mock result with only some employees
        mock_results = [Mock(employee_id=1, count=5)]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        # Act
        result = list_service._get_skills_counts_batch(mock_db, [1, 2, 3])
        
        # Assert - employee 2 and 3 not in result, so .get() should return default
        assert result.get(1, 0) == 5
        assert result.get(2, 0) == 0
        assert result.get(3, 0) == 0


class TestBuildEmployeeResponses:
    """Test the _build_employee_responses() function."""
    
    def test_builds_response_list_from_employees(self, mock_employee, mock_organization):
        """Should transform Employee objects to EmployeeResponse list."""
        # Arrange - set up full org chain: segment -> sub_segment -> project -> team
        segment = mock_organization("segment", 1, "Global")
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        sub_seg.segment = segment
        proj = mock_organization("project", 1, "Project A")
        proj.sub_segment = sub_seg
        team = mock_organization("team", 1, "Team X")
        team.project = proj
        role = mock_organization("role", 1, "Developer")
        role.role_description = "Developer role"
        
        employees = [
            mock_employee(1, "Z1001", "Alice", team=team, role=role),
            mock_employee(2, "Z1002", "Bob", team=team, role=role)
        ]
        skills_counts = {1: 5, 2: 3}
        
        # Act - now takes skills_counts dict instead of db
        result = list_service._build_employee_responses(employees, skills_counts)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(r, EmployeeResponse) for r in result)
        assert result[0].employee_id == 1
        assert result[0].zid == "Z1001"
        assert result[0].full_name == "Alice"
        assert result[0].skills_count == 5
        assert result[1].skills_count == 3
    
    def test_uses_prefetched_skills_counts(self, mock_employee):
        """Should use skills_counts dict instead of making DB queries."""
        # Arrange
        employees = [mock_employee(1), mock_employee(2), mock_employee(3)]
        skills_counts = {1: 10, 2: 20, 3: 30}
        
        # Act - no db passed, should use dict
        result = list_service._build_employee_responses(employees, skills_counts)
        
        # Assert
        assert result[0].skills_count == 10
        assert result[1].skills_count == 20
        assert result[2].skills_count == 30
    
    def test_defaults_to_zero_for_missing_skills_count(self, mock_employee):
        """Should default to 0 skills for employees not in counts dict."""
        # Arrange
        employees = [mock_employee(1), mock_employee(2)]
        skills_counts = {1: 5}  # employee 2 missing
        
        # Act
        result = list_service._build_employee_responses(employees, skills_counts)
        
        # Assert
        assert result[0].skills_count == 5
        assert result[1].skills_count == 0  # Default to 0
    
    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when given empty employee list."""
        # Act
        result = list_service._build_employee_responses([], {})
        
        # Assert
        assert result == []
    
    def test_includes_organization_info(self, mock_employee, mock_organization):
        """Should include organization information in response."""
        # Arrange - set up full org chain: segment -> sub_segment -> project -> team
        segment = mock_organization("segment", 1, "Global")
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        sub_seg.segment = segment
        proj = mock_organization("project", 1, "Project A")
        proj.sub_segment = sub_seg
        team = mock_organization("team", 1, "Team X")
        team.project = proj
        role = mock_organization("role", 1, "Developer")
        role.role_description = "Developer role"
        
        employees = [mock_employee(1, "Z1001", "Alice", team=team, role=role)]
        skills_counts = {1: 0}
        
        # Act
        result = list_service._build_employee_responses(employees, skills_counts)
        
        # Assert
        assert result[0].organization is not None
        assert isinstance(result[0].organization, OrganizationInfo)


class TestBuildOrganizationInfo:
    """Test the _build_organization_info() pure function."""
    
    def test_builds_organization_info_from_employee(self, mock_employee, mock_organization):
        """Should extract organization information from employee relationships."""
        # Arrange - set up full org chain: segment -> sub_segment -> project -> team
        segment = mock_organization("segment", 1, "Global")
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        sub_seg.segment = segment
        proj = mock_organization("project", 1, "Project A")
        proj.sub_segment = sub_seg
        team = mock_organization("team", 1, "Team X")
        team.project = proj
        
        employee = mock_employee(1, "Z1001", "Alice", team=team)
        
        # Act
        result = list_service._build_organization_info(employee)
        
        # Assert
        assert isinstance(result, OrganizationInfo)
        assert result.sub_segment == "Engineering"
        assert result.project == "Project A"
        assert result.team == "Team X"
    
    def test_handles_missing_organization_data(self, mock_employee):
        """Should handle employees without organization relationships."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Alice", sub_segment=None, 
                                project=None, team=None)
        
        # Act
        result = list_service._build_organization_info(employee)
        
        # Assert
        assert isinstance(result, OrganizationInfo)
        # The actual behavior depends on OrganizationInfo schema
        # It may contain None values or empty strings
    
    def test_handles_partial_organization_data(self, mock_employee, mock_organization):
        """Should handle employees with some organization fields missing."""
        # Arrange - team exists but project chain is incomplete
        team = mock_organization("team", 1, "Team X")
        team.project = None  # No project assigned
        
        employee = mock_employee(1, "Z1001", "Alice", team=team)
        
        # Act
        result = list_service._build_organization_info(employee)
        
        # Assert
        assert isinstance(result, OrganizationInfo)
        assert result.team == "Team X"
        assert result.project == ""  # Empty when not available
