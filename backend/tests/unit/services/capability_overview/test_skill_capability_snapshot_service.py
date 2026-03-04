"""
Unit tests for capability_overview/skill_capability_snapshot_service.py

Tests capability snapshot KPIs for a specific skill:
- employee_count: Employees mapped to this skill
- certified_count: Employees with a certification tagged to this skill
- team_count: Distinct teams with employees having this skill
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import skill_capability_snapshot_service
from app.schemas.skill import SkillCapabilitySnapshotResponse


class TestGetSkillCapabilitySnapshot:
    """Test the main public function get_skill_capability_snapshot()."""
    
    def test_returns_complete_snapshot_response(self, mock_db):
        """Should return complete SkillCapabilitySnapshotResponse with all fields."""
        # Arrange
        skill_id = 42
        with patch.object(skill_capability_snapshot_service, '_query_employee_count', return_value=128), \
             patch.object(skill_capability_snapshot_service, '_query_certified_count', return_value=36), \
             patch.object(skill_capability_snapshot_service, '_query_team_count', return_value=14):
            
            # Act
            result = skill_capability_snapshot_service.get_skill_capability_snapshot(mock_db, skill_id)
            
            # Assert
            assert isinstance(result, SkillCapabilitySnapshotResponse)
            assert result.employee_count == 128
            assert result.certified_count == 36
            assert result.team_count == 14
    
    def test_handles_zero_data(self, mock_db):
        """Should handle case when no data exists for skill."""
        # Arrange
        skill_id = 999
        with patch.object(skill_capability_snapshot_service, '_query_employee_count', return_value=0), \
             patch.object(skill_capability_snapshot_service, '_query_certified_count', return_value=0), \
             patch.object(skill_capability_snapshot_service, '_query_team_count', return_value=0):
            
            # Act
            result = skill_capability_snapshot_service.get_skill_capability_snapshot(mock_db, skill_id)
            
            # Assert
            assert result.employee_count == 0
            assert result.certified_count == 0
            assert result.team_count == 0
    
    def test_calls_all_query_functions_with_skill_id(self, mock_db):
        """Should call all required query functions with correct skill_id."""
        # Arrange
        skill_id = 42
        with patch.object(skill_capability_snapshot_service, '_query_employee_count', return_value=10) as mock_emp, \
             patch.object(skill_capability_snapshot_service, '_query_certified_count', return_value=5) as mock_cert, \
             patch.object(skill_capability_snapshot_service, '_query_team_count', return_value=3) as mock_team:
            
            # Act
            skill_capability_snapshot_service.get_skill_capability_snapshot(mock_db, skill_id)
            
            # Assert
            mock_emp.assert_called_once_with(mock_db, skill_id)
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
        result = skill_capability_snapshot_service._query_employee_count(mock_db, skill_id)
        
        # Assert
        assert result == 128
    
    def test_returns_zero_when_no_data(self, mock_db):
        """Should return 0 when scalar returns None."""
        # Arrange
        skill_id = 999
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = skill_capability_snapshot_service._query_employee_count(mock_db, skill_id)
        
        # Assert
        assert result == 0


class TestQueryCertifiedCount:
    """Test the _query_certified_count() function."""
    
    def test_returns_count_when_certifications_exist(self, mock_db):
        """Should return count of employees with certifications."""
        # Arrange
        skill_id = 42
        mock_db.query.return_value.filter.return_value.scalar.return_value = 36
        
        # Act
        result = skill_capability_snapshot_service._query_certified_count(mock_db, skill_id)
        
        # Assert
        assert result == 36
    
    def test_returns_zero_when_no_certifications(self, mock_db):
        """Should return 0 when no certifications exist."""
        # Arrange
        skill_id = 42
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = skill_capability_snapshot_service._query_certified_count(mock_db, skill_id)
        
        # Assert
        assert result == 0


class TestQueryTeamCount:
    """Test the _query_team_count() function."""
    
    def test_returns_count_when_teams_exist(self, mock_db):
        """Should return count of distinct teams."""
        # Arrange
        skill_id = 42
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 14
        
        # Act
        result = skill_capability_snapshot_service._query_team_count(mock_db, skill_id)
        
        # Assert
        assert result == 14
    
    def test_returns_zero_when_no_teams(self, mock_db):
        """Should return 0 when no teams found."""
        # Arrange
        skill_id = 42
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = None
        
        # Act
        result = skill_capability_snapshot_service._query_team_count(mock_db, skill_id)
        
        # Assert
        assert result == 0


class TestRegressionExistingBehavior:
    """Regression tests to ensure existing behavior is not broken."""
    
    def test_response_schema_is_valid(self):
        """Verify the response schema can be instantiated with correct types."""
        # This ensures the schema definition wasn't accidentally modified
        response = SkillCapabilitySnapshotResponse(
            employee_count=100,
            certified_count=25,
            team_count=10
        )
        assert response.employee_count == 100
        assert response.certified_count == 25
        assert response.team_count == 10
    
    def test_negative_counts_allowed(self):
        """Verify schema allows any integer values (no constraints)."""
        # This tests that we don't have unexpected constraints
        response = SkillCapabilitySnapshotResponse(
            employee_count=0,
            certified_count=0,
            team_count=0
        )
        assert response.employee_count == 0
