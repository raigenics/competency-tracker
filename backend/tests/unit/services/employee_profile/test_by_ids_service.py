"""
Unit tests for employee_profile/by_ids_service.py

Tests batch employee fetching by IDs with top skills.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.employee_profile import by_ids_service
from app.schemas.employee import EmployeesByIdsResponse, TalentResultItem, SkillInfo


class TestGetEmployeesByIds:
    """Test the main public function get_employees_by_ids()."""
    
    def test_returns_employees_for_given_ids(self, mock_db, mock_employee):
        """Should return EmployeesByIdsResponse with employees matching IDs."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice"), mock_employee(2, "Z1002", "Bob")]
        
        with patch.object(by_ids_service, '_query_employees_by_ids', return_value=employees), \
             patch.object(by_ids_service, '_build_talent_result_items', return_value=[]):
            
            # Act
            result = by_ids_service.get_employees_by_ids(mock_db, [1, 2])
            
            # Assert
            assert isinstance(result, EmployeesByIdsResponse)
    
    def test_returns_empty_response_for_empty_ids_list(self, mock_db):
        """Should return empty response when given empty IDs list."""
        # Act
        result = by_ids_service.get_employees_by_ids(mock_db, [])
        
        # Assert
        assert isinstance(result, EmployeesByIdsResponse)
        assert result.results == []
    
    def test_calls_query_and_build_functions(self, mock_db, mock_employee):
        """Should call query and build functions with correct parameters."""
        # Arrange
        employees = [mock_employee(1)]
        
        with patch.object(by_ids_service, '_query_employees_by_ids', return_value=employees) as mock_query, \
             patch.object(by_ids_service, '_build_talent_result_items', return_value=[]) as mock_build:
            
            # Act
            by_ids_service.get_employees_by_ids(mock_db, [1, 2, 3])
            
            # Assert
            mock_query.assert_called_once_with(mock_db, [1, 2, 3])
            mock_build.assert_called_once_with(mock_db, employees)


class TestQueryEmployeesByIds:
    """Test the _query_employees_by_ids() function."""
    
    def test_queries_employees_by_id_list(self, mock_db):
        """Should query employees with IDs in the given list."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        by_ids_service._query_employees_by_ids(mock_db, [1, 2, 3])
        
        # Assert
        mock_db.query.assert_called_once()
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.all.assert_called_once()
    
    def test_eager_loads_organization_relationships(self, mock_db):
        """Should eager load sub_segment, project, team, and role."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        by_ids_service._query_employees_by_ids(mock_db, [1])
        
        # Assert
        # Verify options() was called (eager loading)
        assert mock_query.options.called


class TestQueryTopSkills:
    """Test the _query_top_skills() function."""
    
    def test_returns_top_skills_for_employee(self, mock_db):
        """Should return list of (skill_name, proficiency_level_id) tuples."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            ("Python", 5),
            ("SQL", 4),
            ("JavaScript", 3)
        ]
        
        # Act
        result = by_ids_service._query_top_skills(mock_db, employee_id=1)
        
        # Assert
        assert len(result) == 3
        assert result[0] == ("Python", 5)
    
    def test_respects_limit_parameter(self, mock_db):
        """Should limit results to specified number."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        by_ids_service._query_top_skills(mock_db, employee_id=1, limit=5)
        
        # Assert
        mock_query.limit.assert_called_once_with(5)
    
    def test_default_limit_is_10(self, mock_db):
        """Should use default limit of 10 when not specified."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        by_ids_service._query_top_skills(mock_db, employee_id=1)
        
        # Assert
        mock_query.limit.assert_called_once_with(10)


class TestBuildTalentResultItems:
    """Test the _build_talent_result_items() function."""
    
    def test_builds_talent_result_items_from_employees(self, mock_db, mock_employee, mock_organization):
        """Should transform Employee objects to TalentResultItem list."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        team = mock_organization("team", 1, "Team X")
        role = mock_organization("role", 1, "Developer")
        
        employees = [
            mock_employee(1, "Z1001", "Alice", sub_segment=sub_seg, team=team, role=role),
            mock_employee(2, "Z1002", "Bob", sub_segment=sub_seg, team=team, role=role)
        ]
        
        with patch.object(by_ids_service, '_query_top_skills', return_value=[("Python", 5)]):
            # Act
            result = by_ids_service._build_talent_result_items(mock_db, employees)
            
            # Assert
            assert len(result) == 2
            assert all(isinstance(item, TalentResultItem) for item in result)
            assert result[0].id == 1
            assert result[0].name == "Alice"
    
    def test_queries_top_skills_for_each_employee(self, mock_db, mock_employee):
        """Should call _query_top_skills for each employee."""
        # Arrange
        employees = [mock_employee(1), mock_employee(2), mock_employee(3)]
        
        with patch.object(by_ids_service, '_query_top_skills', return_value=[]) as mock_skills:
            # Act
            by_ids_service._build_talent_result_items(mock_db, employees)
            
            # Assert
            assert mock_skills.call_count == 3
    
    def test_returns_empty_list_for_empty_input(self, mock_db):
        """Should return empty list when given empty employee list."""
        # Act
        result = by_ids_service._build_talent_result_items(mock_db, [])
        
        # Assert
        assert result == []


class TestBuildSkillInfoList:
    """Test the _build_skill_info_list() pure function."""
    
    def test_transforms_tuples_to_skill_info_list(self):
        """Should transform list of tuples to SkillInfo list."""
        # Arrange
        skills_data = [
            ("Python", 5),
            ("SQL", 4),
            ("JavaScript", 3)
        ]
        
        # Act
        result = by_ids_service._build_skill_info_list(skills_data)
        
        # Assert
        assert len(result) == 3
        assert all(isinstance(skill, SkillInfo) for skill in result)
        assert result[0].name == "Python"
        assert result[0].proficiency == 5
    
    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when given empty input."""
        # Act
        result = by_ids_service._build_skill_info_list([])
        
        # Assert
        assert result == []
    
    def test_preserves_skill_order(self):
        """Should maintain the order of skills from input."""
        # Arrange
        skills_data = [
            ("Skill C", 3),
            ("Skill A", 5),
            ("Skill B", 4)
        ]
        
        # Act
        result = by_ids_service._build_skill_info_list(skills_data)
        
        # Assert
        assert result[0].name == "Skill C"
        assert result[1].name == "Skill A"
        assert result[2].name == "Skill B"


class TestBuildOrganizationValues:
    """Test the _build_organization_values() pure function."""
    
    def test_extracts_organization_values_from_employee(self, mock_employee, mock_organization):
        """Should extract organization strings from employee relationships."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        team = mock_organization("team", 1, "Team X")
        role = mock_organization("role", 1, "Developer")
        
        employee = mock_employee(1, "Z1001", "Alice", sub_segment=sub_seg, team=team, role=role)
        
        # Act
        sub_segment_name, team_name, role_name = by_ids_service._build_organization_values(employee)
        
        # Assert
        assert sub_segment_name == "Engineering"
        assert team_name == "Team X"
        assert role_name == "Developer"
    
    def test_handles_missing_organization_data(self, mock_employee):
        """Should return empty strings when organization data is missing."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Alice", sub_segment=None, team=None, role=None)
        
        # Act
        sub_segment_name, team_name, role_name = by_ids_service._build_organization_values(employee)
        
        # Assert
        assert sub_segment_name == ""
        assert team_name == ""
        assert role_name == ""
    
    def test_handles_partial_organization_data(self, mock_employee, mock_organization):
        """Should handle employees with some organization fields missing."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        employee = mock_employee(1, "Z1001", "Alice", sub_segment=sub_seg, team=None, role=None)
        
        # Act
        sub_segment_name, team_name, role_name = by_ids_service._build_organization_values(employee)
        
        # Assert
        assert sub_segment_name == "Engineering"
        assert team_name == ""
        assert role_name == ""
