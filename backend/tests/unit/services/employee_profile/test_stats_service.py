"""
Unit tests for employee_profile/stats_service.py

Tests employee statistics and aggregations.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.employee_profile import stats_service
from app.schemas.employee import EmployeeStatsResponse


class TestGetEmployeeStats:
    """Test the main public function get_employee_stats()."""
    
    def test_returns_complete_stats_response(self, mock_db):
        """Should return EmployeeStatsResponse with all statistical fields."""
        # Arrange
        with patch.object(stats_service, '_query_total_employees', return_value=150), \
             patch.object(stats_service, '_query_employees_by_sub_segment', return_value={"Engineering": 50}), \
             patch.object(stats_service, '_query_employees_by_project', return_value={"Project A": 30}), \
             patch.object(stats_service, '_query_employees_by_team', return_value={"Team X": 20}), \
             patch.object(stats_service, '_query_average_skills_per_employee', return_value=12.5):
            
            # Act
            result = stats_service.get_employee_stats(mock_db)
            
            # Assert
            assert isinstance(result, EmployeeStatsResponse)
            assert result.total_employees == 150
            assert result.by_sub_segment == {"Engineering": 50}
            assert result.by_project == {"Project A": 30}
            assert result.by_team == {"Team X": 20}
            assert result.avg_skills_per_employee == 12.5
    
    def test_handles_zero_employees(self, mock_db):
        """Should handle case when no employees exist."""
        # Arrange
        with patch.object(stats_service, '_query_total_employees', return_value=0), \
             patch.object(stats_service, '_query_employees_by_sub_segment', return_value={}), \
             patch.object(stats_service, '_query_employees_by_project', return_value={}), \
             patch.object(stats_service, '_query_employees_by_team', return_value={}), \
             patch.object(stats_service, '_query_average_skills_per_employee', return_value=0.0):
            
            # Act
            result = stats_service.get_employee_stats(mock_db)
            
            # Assert
            assert result.total_employees == 0
            assert result.by_sub_segment == {}
            assert result.by_project == {}
            assert result.by_team == {}
            assert result.avg_skills_per_employee == 0.0
    
    def test_calls_all_query_functions(self, mock_db):
        """Should call all required query functions."""
        # Arrange
        with patch.object(stats_service, '_query_total_employees', return_value=10) as mock_total, \
             patch.object(stats_service, '_query_employees_by_sub_segment', return_value={}) as mock_sub, \
             patch.object(stats_service, '_query_employees_by_project', return_value={}) as mock_proj, \
             patch.object(stats_service, '_query_employees_by_team', return_value={}) as mock_team, \
             patch.object(stats_service, '_query_average_skills_per_employee', return_value=0.0) as mock_avg:
            
            # Act
            stats_service.get_employee_stats(mock_db)
            
            # Assert
            mock_total.assert_called_once_with(mock_db)
            mock_sub.assert_called_once_with(mock_db)
            mock_proj.assert_called_once_with(mock_db)
            mock_team.assert_called_once_with(mock_db)
            mock_avg.assert_called_once_with(mock_db)


class TestQueryTotalEmployees:
    """Test the _query_total_employees() function."""
    
    def test_returns_total_count(self, mock_db):
        """Should return count of all employees."""
        # Arrange - chain: query().filter().scalar()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 150
        
        # Act
        result = stats_service._query_total_employees(mock_db)
        
        # Assert
        assert result == 150
    
    def test_returns_zero_when_no_employees(self, mock_db):
        """Should return 0 when no employees exist."""
        # Arrange - chain: query().filter().scalar()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        
        # Act
        result = stats_service._query_total_employees(mock_db)
        
        # Assert
        assert result == 0


class TestQueryEmployeesBySubSegment:
    """Test the _query_employees_by_sub_segment() function."""
    
    def test_returns_sub_segment_counts_dict(self, mock_db):
        """Should return dictionary of sub-segment names to counts."""
        # Arrange - chain: query().join().filter().group_by().all()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("Engineering", 50),
            ("Sales", 30),
            ("HR", 15)
        ]
        
        # Act
        result = stats_service._query_employees_by_sub_segment(mock_db)
        
        # Assert
        assert result == {"Engineering": 50, "Sales": 30, "HR": 15}
        assert isinstance(result, dict)
    
    def test_returns_empty_dict_when_no_employees(self, mock_db):
        """Should return empty dict when no employees exist."""
        # Arrange - chain: query().join().filter().group_by().all()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = stats_service._query_employees_by_sub_segment(mock_db)
        
        # Assert
        assert result == {}


class TestQueryEmployeesByProject:
    """Test the _query_employees_by_project() function."""
    
    def test_returns_project_counts_dict(self, mock_db):
        """Should return dictionary of project names to counts."""
        # Arrange - chain: query().join().filter().group_by().all()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("Project A", 40),
            ("Project B", 35),
            ("Project C", 25)
        ]
        
        # Act
        result = stats_service._query_employees_by_project(mock_db)
        
        # Assert
        assert result == {"Project A": 40, "Project B": 35, "Project C": 25}
        assert isinstance(result, dict)


class TestQueryEmployeesByTeam:
    """Test the _query_employees_by_team() function."""
    
    def test_returns_team_counts_dict(self, mock_db):
        """Should return dictionary of team names to counts."""
        # Arrange - chain: query().join().filter().group_by().all()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("Team X", 20),
            ("Team Y", 18),
            ("Team Z", 15)
        ]
        
        # Act
        result = stats_service._query_employees_by_team(mock_db)
        
        # Assert
        assert result == {"Team X": 20, "Team Y": 18, "Team Z": 15}
        assert isinstance(result, dict)


class TestQueryAverageSkillsPerEmployee:
    """Test the _query_average_skills_per_employee() function."""
    
    def test_returns_average_skills_count(self, mock_db):
        """Should return average number of skills per employee."""
        # Arrange - chain: query().filter().scalar()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 12.75
        
        # Act
        result = stats_service._query_average_skills_per_employee(mock_db)
        
        # Assert
        assert result == 12.75
    
    def test_returns_zero_when_no_employees(self, mock_db):
        """Should return 0 when no employees exist."""
        # Arrange - chain: query().filter().scalar()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = stats_service._query_average_skills_per_employee(mock_db)
        
        # Assert
        assert result == 0.0
    
    def test_returns_exact_average_from_db(self, mock_db):
        """Should return exact average from database query."""
        # Arrange - chain: query().filter().scalar()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 12.123456
        
        # Act
        result = stats_service._query_average_skills_per_employee(mock_db)
        
        # Assert - implementation returns raw value, rounding done at response layer
        assert result == 12.123456


class TestBuildStatsResponse:
    """Test the _build_stats_response() pure function."""
    
    def test_builds_complete_response(self):
        """Should build EmployeeStatsResponse from input data."""
        # Arrange
        total = 150
        by_sub = {"Engineering": 50, "Sales": 30}
        by_proj = {"Project A": 40, "Project B": 35}
        by_team = {"Team X": 20, "Team Y": 18}
        avg = 12.5
        
        # Act
        result = stats_service._build_stats_response(
            total, by_sub, by_proj, by_team, avg
        )
        
        # Assert
        assert isinstance(result, EmployeeStatsResponse)
        assert result.total_employees == 150
        assert result.by_sub_segment == by_sub
        assert result.by_project == by_proj
        assert result.by_team == by_team
        assert result.avg_skills_per_employee == 12.5
    
    def test_handles_empty_breakdowns(self):
        """Should handle empty dictionaries for breakdowns."""
        # Act
        result = stats_service._build_stats_response(0, {}, {}, {}, 0.0)
        
        # Assert
        assert result.total_employees == 0
        assert result.by_sub_segment == {}
        assert result.by_project == {}
        assert result.by_team == {}
        assert result.avg_skills_per_employee == 0.0
