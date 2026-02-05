"""
Unit tests for employee_profile/list_service.py

Tests paginated employee listing with filters.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.employee_profile import list_service
from app.schemas.employee import EmployeeResponse, OrganizationInfo


class TestGetEmployeesPaginated:
    """Test the main public function get_employees_paginated()."""
    
    def test_returns_employees_and_total_count(self, mock_db, mock_pagination, mock_employee):
        """Should return list of employees and total count."""
        # Arrange
        pagination = mock_pagination(page=1, size=10)
        employees = [mock_employee(1, "Z1001", "Alice"), mock_employee(2, "Z1002", "Bob")]
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query, \
             patch.object(list_service, '_get_skills_count', return_value=5):
            mock_query = MagicMock()
            mock_build_query.return_value = mock_query
            mock_query.count.return_value = 2
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = employees
            
            # Act
            result, total = list_service.get_employees_paginated(mock_db, pagination)
            
            # Assert
            assert len(result) == 2
            assert total == 2
            assert all(isinstance(emp, EmployeeResponse) for emp in result)
    
    def test_applies_all_filters(self, mock_db, mock_pagination):
        """Should pass all filter parameters to query builder."""
        # Arrange
        pagination = mock_pagination(page=1, size=10)
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query:
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
                mock_db, 1, 2, 3, 4, "test"
            )
    
    def test_applies_pagination_correctly(self, mock_db, mock_pagination):
        """Should apply offset and limit based on pagination params."""
        # Arrange
        pagination = mock_pagination(page=3, size=20)
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query:
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
        
        with patch.object(list_service, '_build_employee_query') as mock_build_query:
            mock_query = MagicMock()
            mock_build_query.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            # Act
            result, total = list_service.get_employees_paginated(mock_db, pagination)
            
            # Assert
            assert result == []
            assert total == 0


class TestBuildEmployeeQuery:
    """Test the _build_employee_query() function."""
    
    def test_builds_base_query_with_no_filters(self, mock_db):
        """Should build query with eager loading when no filters provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        
        # Act
        result = list_service._build_employee_query(mock_db, None, None, None, None, None)
        
        # Assert
        mock_db.query.assert_called_once()
        mock_query.options.assert_called_once()
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
        
        # Assert
        assert mock_query.filter.call_count == 5  # All 5 filters applied


class TestGetSkillsCount:
    """Test the _get_skills_count() function."""
    
    def test_returns_skills_count_for_employee(self, mock_db):
        """Should return count of skills for given employee."""
        # Arrange
        mock_db.query.return_value.filter.return_value.scalar.return_value = 12
        
        # Act
        result = list_service._get_skills_count(mock_db, employee_id=1)
        
        # Assert
        assert result == 12
    
    def test_returns_zero_when_no_skills(self, mock_db):
        """Should return 0 when employee has no skills."""
        # Arrange
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        
        # Act
        result = list_service._get_skills_count(mock_db, employee_id=1)
        
        # Assert
        assert result == 0
    
    def test_returns_zero_when_scalar_returns_none(self, mock_db):
        """Should return 0 when scalar() returns None."""
        # Arrange
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = list_service._get_skills_count(mock_db, employee_id=1)
        
        # Assert
        assert result == 0


class TestBuildEmployeeResponses:
    """Test the _build_employee_responses() function."""
    
    def test_builds_response_list_from_employees(self, mock_db, mock_employee, mock_organization):
        """Should transform Employee objects to EmployeeResponse list."""
        # Arrange
        role = mock_organization("role", 1, "Developer")
        employees = [
            mock_employee(1, "Z1001", "Alice", role=role),
            mock_employee(2, "Z1002", "Bob", role=role)
        ]
        
        with patch.object(list_service, '_get_skills_count', return_value=5):
            # Act
            result = list_service._build_employee_responses(mock_db, employees)
            
            # Assert
            assert len(result) == 2
            assert all(isinstance(r, EmployeeResponse) for r in result)
            assert result[0].employee_id == 1
            assert result[0].zid == "Z1001"
            assert result[0].full_name == "Alice"
            assert result[0].skills_count == 5
    
    def test_queries_skills_count_for_each_employee(self, mock_db, mock_employee):
        """Should call _get_skills_count for each employee."""
        # Arrange
        employees = [mock_employee(1), mock_employee(2), mock_employee(3)]
        
        with patch.object(list_service, '_get_skills_count', return_value=0) as mock_count:
            # Act
            list_service._build_employee_responses(mock_db, employees)
            
            # Assert
            assert mock_count.call_count == 3
    
    def test_returns_empty_list_for_empty_input(self, mock_db):
        """Should return empty list when given empty employee list."""
        # Act
        result = list_service._build_employee_responses(mock_db, [])
        
        # Assert
        assert result == []
    
    def test_includes_organization_info(self, mock_db, mock_employee, mock_organization):
        """Should include organization information in response."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        proj = mock_organization("project", 1, "Project A")
        team = mock_organization("team", 1, "Team X")
        role = mock_organization("role", 1, "Developer")
        
        employees = [mock_employee(1, "Z1001", "Alice", sub_segment=sub_seg, 
                                   project=proj, team=team, role=role)]
        
        with patch.object(list_service, '_get_skills_count', return_value=0):
            # Act
            result = list_service._build_employee_responses(mock_db, employees)
            
            # Assert
            assert result[0].organization is not None
            assert isinstance(result[0].organization, OrganizationInfo)


class TestBuildOrganizationInfo:
    """Test the _build_organization_info() pure function."""
    
    def test_builds_organization_info_from_employee(self, mock_employee, mock_organization):
        """Should extract organization information from employee relationships."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        proj = mock_organization("project", 1, "Project A")
        team = mock_organization("team", 1, "Team X")
        
        employee = mock_employee(1, "Z1001", "Alice", sub_segment=sub_seg, 
                                project=proj, team=team)
        
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
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        employee = mock_employee(1, "Z1001", "Alice", sub_segment=sub_seg,
                                project=None, team=None)
        
        # Act
        result = list_service._build_organization_info(employee)
        
        # Assert
        assert isinstance(result, OrganizationInfo)
        assert result.sub_segment == "Engineering"
