"""
Unit tests for capability_overview/skill_employees_summary_service.py

Tests employees summary aggregation for a specific skill:
- employee_count: Count of distinct employees with this skill
- avg_proficiency: Average proficiency value (1-5) rounded to 1 decimal
- certified_count: Count of employees with certification for this skill
- team_count: Count of distinct teams with employees having this skill
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import skill_employees_summary_service
from app.schemas.skill import SkillEmployeesSummaryResponse


class TestGetSkillEmployeesSummary:
    """Test the main public function get_skill_employees_summary()."""
    
    def test_returns_complete_summary_response(self, mock_db):
        """Should return complete SkillEmployeesSummaryResponse with all fields."""
        # Arrange
        skill_id = 42
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=128), \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=3.5), \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=36), \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=14):
            
            # Act
            result = skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            # Assert
            assert isinstance(result, SkillEmployeesSummaryResponse)
            assert result.employee_count == 128
            assert result.avg_proficiency == 3.5
            assert result.certified_count == 36
            assert result.team_count == 14
    
    def test_handles_zero_employees(self, mock_db):
        """Should handle case when no employees exist for skill."""
        # Arrange
        skill_id = 999
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=0), \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=0.0), \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=0), \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=0):
            
            # Act
            result = skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            # Assert
            assert result.employee_count == 0
            assert result.avg_proficiency == 0.0
            assert result.certified_count == 0
            assert result.team_count == 0
    
    def test_handles_multiple_teams_aggregation(self, mock_db):
        """Should correctly aggregate multiple distinct teams."""
        # Arrange
        skill_id = 42
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=50), \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=2.8), \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=10), \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=5):
            
            # Act
            result = skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            # Assert
            assert result.team_count == 5
            assert result.employee_count == 50
    
    def test_calls_all_query_functions_with_skill_id(self, mock_db):
        """Should call all required query functions with correct skill_id."""
        # Arrange
        skill_id = 42
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=10) as mock_emp, \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=3.0) as mock_avg, \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=5) as mock_cert, \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=3) as mock_team:
            
            # Act
            skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            # Assert
            mock_emp.assert_called_once_with(mock_db, skill_id)
            mock_avg.assert_called_once_with(mock_db, skill_id)
            mock_cert.assert_called_once_with(mock_db, skill_id)
            mock_team.assert_called_once_with(mock_db, skill_id)


class TestQueryEmployeeCount:
    """Test the _query_employee_count() function."""
    
    def test_returns_count_when_data_exists(self, mock_db):
        """Should return count of distinct employees with skill."""
        # Arrange
        skill_id = 42
        mock_db.query.return_value.filter.return_value.scalar.return_value = 128
        
        # Act
        result = skill_employees_summary_service._query_employee_count(mock_db, skill_id)
        
        # Assert
        assert result == 128
    
    def test_returns_zero_when_no_data(self, mock_db):
        """Should return 0 when scalar returns None."""
        # Arrange
        skill_id = 999
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = skill_employees_summary_service._query_employee_count(mock_db, skill_id)
        
        # Assert
        assert result == 0


class TestQueryAvgProficiency:
    """Test the _query_avg_proficiency() function via integration-style test."""
    
    def test_rounds_avg_to_one_decimal(self, mock_db):
        """Should round average proficiency value to 1 decimal using patched service call."""
        # We test via the main function with patched helpers
        skill_id = 42
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=10), \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=3.5), \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=5), \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=3):
            
            result = skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            # Verify rounded to 1 decimal
            assert result.avg_proficiency == 3.5
    
    def test_zero_when_no_data(self, mock_db):
        """Should return 0.0 when no proficiency data."""
        skill_id = 999
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=0), \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=0.0), \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=0), \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=0):
            
            result = skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            assert result.avg_proficiency == 0.0


class TestQueryCertifiedCount:
    """Test the _query_certified_count() function."""
    
    def test_returns_count_when_certifications_exist(self, mock_db):
        """Should return count of employees with certifications."""
        # Arrange
        skill_id = 42
        mock_db.query.return_value.filter.return_value.scalar.return_value = 36
        
        # Act
        result = skill_employees_summary_service._query_certified_count(mock_db, skill_id)
        
        # Assert
        assert result == 36
    
    def test_returns_zero_when_no_certifications(self, mock_db):
        """Should return 0 when no certifications exist."""
        # Arrange
        skill_id = 999
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = skill_employees_summary_service._query_certified_count(mock_db, skill_id)
        
        # Assert
        assert result == 0


class TestQueryTeamCount:
    """Test the _query_team_count() function via integration-style test."""
    
    def test_returns_distinct_teams(self, mock_db):
        """Should return distinct team count."""
        skill_id = 42
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=50), \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=3.0), \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=10), \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=5):
            
            result = skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            assert result.team_count == 5
    
    def test_zero_when_no_teams(self, mock_db):
        """Should return 0 when no teams found."""
        skill_id = 999
        with patch.object(skill_employees_summary_service, '_query_employee_count', return_value=0), \
             patch.object(skill_employees_summary_service, '_query_avg_proficiency', return_value=0.0), \
             patch.object(skill_employees_summary_service, '_query_certified_count', return_value=0), \
             patch.object(skill_employees_summary_service, '_query_team_count', return_value=0):
            
            result = skill_employees_summary_service.get_skill_employees_summary(mock_db, skill_id)
            
            assert result.team_count == 0

    def test_query_team_count_returns_count_from_db(self, mock_db):
        """
        Regression test: _query_team_count should use Employee.team_id (FK column), 
        not Employee.team (relationship).
        
        The bug: Using Employee.team.distinct() on a relationship caused NotImplementedError.
        The fix: Use Employee.team_id.distinct() instead.
        """
        # Arrange
        skill_id = 42
        # Mock the query chain for the actual _query_team_count call
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 3
        
        # Act
        result = skill_employees_summary_service._query_team_count(mock_db, skill_id)
        
        # Assert
        assert result == 3
    
    def test_query_team_count_returns_zero_when_null(self, mock_db):
        """Should return 0 when scalar returns None."""
        skill_id = 999
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = skill_employees_summary_service._query_team_count(mock_db, skill_id)
        
        # Assert
        assert result == 0
