"""
Unit tests for employee_profile/suggest_service.py

Tests the autocomplete suggestion functionality for employees.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.employee_profile import suggest_service
from app.schemas.employee import EmployeeSuggestion


class TestGetEmployeeSuggestions:
    """Test the main public function get_employee_suggestions()."""
    
    def test_returns_suggestions_for_valid_query(self, mock_db, mock_employee, mock_organization):
        """Should return employee suggestions when employees are found."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        proj = mock_organization("project", 1, "Project A")
        team = mock_organization("team", 1, "Team X")
        
        emp1 = mock_employee(1, "Z1001", "John Doe", sub_segment=sub_seg, project=proj, team=team)
        emp2 = mock_employee(2, "Z1002", "Jane Doe", sub_segment=sub_seg, project=proj, team=team)
        
        with patch.object(suggest_service, '_query_employees_by_search', return_value=[emp1, emp2]):
            # Act
            result = suggest_service.get_employee_suggestions(mock_db, "Doe", 10)
            
            # Assert
            assert len(result) == 2
            assert all(isinstance(s, EmployeeSuggestion) for s in result)
            assert result[0].full_name == "John Doe"
            assert result[1].full_name == "Jane Doe"
    
    def test_returns_empty_list_when_no_employees_found(self, mock_db):
        """Should return empty list when no employees match query."""
        # Arrange
        with patch.object(suggest_service, '_query_employees_by_search', return_value=[]):
            # Act
            result = suggest_service.get_employee_suggestions(mock_db, "XYZ", 10)
            
            # Assert
            assert result == []
    
    def test_respects_limit_parameter(self, mock_db, mock_employee):
        """Should pass limit parameter to query function."""
        # Arrange
        employees = [mock_employee(i, f"Z100{i}", f"Employee {i}") for i in range(5)]
        
        with patch.object(suggest_service, '_query_employees_by_search', return_value=employees[:3]) as mock_query:
            # Act
            suggest_service.get_employee_suggestions(mock_db, "Employee", 3)
            
            # Assert
            mock_query.assert_called_once_with(mock_db, "Employee", 3)


class TestQueryEmployeesBySearch:
    """Test the _query_employees_by_search() database query function."""
    
    def test_searches_by_full_name(self, mock_db):
        """Should search employees by full name with ILIKE."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        suggest_service._query_employees_by_search(mock_db, "John", 10)
        
        # Assert
        mock_db.query.assert_called_once()
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.limit.assert_called_once_with(10)
        mock_query.all.assert_called_once()
    
    def test_searches_by_zid(self, mock_db):
        """Should search employees by ZID with ILIKE."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        suggest_service._query_employees_by_search(mock_db, "Z1001", 10)
        
        # Assert
        mock_query.filter.assert_called_once()
        mock_query.limit.assert_called_once_with(10)
    
    def test_eager_loads_organization_relationships(self, mock_db):
        """Should eager load sub_segment, project, and team."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        suggest_service._query_employees_by_search(mock_db, "test", 5)
        
        # Assert
        # Verify options() was called (eager loading relationships)
        assert mock_query.options.called


class TestBuildSuggestions:
    """Test the _build_suggestions() pure function."""
    
    def test_builds_suggestions_from_employees(self, mock_employee, mock_organization):
        """Should transform Employee objects to EmployeeSuggestion list."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        proj = mock_organization("project", 1, "Project A")
        team = mock_organization("team", 1, "Team X")
        
        emp1 = mock_employee(1, "Z1001", "Alice Smith", sub_segment=sub_seg, project=proj, team=team)
        emp2 = mock_employee(2, "Z1002", "Bob Jones", sub_segment=sub_seg, project=proj, team=team)
        
        # Act
        result = suggest_service._build_suggestions([emp1, emp2])
        
        # Assert
        assert len(result) == 2
        assert result[0].employee_id == 1
        assert result[0].zid == "Z1001"
        assert result[0].full_name == "Alice Smith"
        assert result[0].sub_segment == "Engineering"
        assert result[0].project == "Project A"
        assert result[0].team == "Team X"
        
        assert result[1].employee_id == 2
        assert result[1].full_name == "Bob Jones"
    
    def test_handles_missing_organization_data(self, mock_employee):
        """Should handle employees without organization relationships."""
        # Arrange
        emp = mock_employee(1, "Z1001", "John Doe", sub_segment=None, project=None, team=None)
        
        # Act
        result = suggest_service._build_suggestions([emp])
        
        # Assert
        assert len(result) == 1
        assert result[0].sub_segment is None
        assert result[0].project is None
        assert result[0].team is None
    
    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when given empty employee list."""
        # Act
        result = suggest_service._build_suggestions([])
        
        # Assert
        assert result == []
    
    def test_preserves_employee_order(self, mock_employee):
        """Should maintain the order of employees in output."""
        # Arrange
        employees = [
            mock_employee(3, "Z1003", "Charlie"),
            mock_employee(1, "Z1001", "Alice"),
            mock_employee(2, "Z1002", "Bob")
        ]
        
        # Act
        result = suggest_service._build_suggestions(employees)
        
        # Assert
        assert result[0].employee_id == 3
        assert result[1].employee_id == 1
        assert result[2].employee_id == 2
    
    def test_handles_partial_organization_data(self, mock_employee, mock_organization):
        """Should handle employees with some organization fields missing."""
        # Arrange
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        emp = mock_employee(1, "Z1001", "John Doe", sub_segment=sub_seg, project=None, team=None)
        
        # Act
        result = suggest_service._build_suggestions([emp])
        
        # Assert
        assert result[0].sub_segment == "Engineering"
        assert result[0].project is None
        assert result[0].team is None
