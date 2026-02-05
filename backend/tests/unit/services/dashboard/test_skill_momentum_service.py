"""
Unit tests for dashboard/skill_momentum_service.py

Tests skill update momentum tracking across three time periods.
Coverage: Time period calculations, employee scoping, update counting.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from app.services.dashboard import skill_momentum_service as service
from app.models import Employee


# ============================================================================
# TEST: get_skill_momentum (Main Entry Point)
# ============================================================================

class TestGetSkillMomentum:
    """Test the main skill momentum function."""
    
    def test_returns_momentum_for_all_time_periods(self, mock_db):
        """Should return counts for all three time periods."""
        # Arrange
        employee_ids = [1, 2, 3]
        
        with patch.object(service, '_get_employee_ids_in_scope', return_value=employee_ids):
            with patch.object(service, '_calculate_time_cutoffs', return_value=(datetime.now(), datetime.now())):
                with patch.object(service, '_query_skills_updated_in_period', side_effect=[10, 5]):
                    with patch.object(service, '_query_skills_updated_before', return_value=3):
                        # Act
                        result = service.get_skill_momentum(mock_db)
        
        # Assert
        assert 'updated_last_3_months' in result
        assert 'updated_last_6_months' in result
        assert 'not_updated_6_months' in result
        assert result['updated_last_3_months'] == 10
        assert result['updated_last_6_months'] == 5
        assert result['not_updated_6_months'] == 3
    
    def test_returns_zeros_when_no_employees_in_scope(self, mock_db):
        """Should return all zeros when no employees match filters."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[]):
            # Act
            result = service.get_skill_momentum(mock_db)
        
        # Assert
        assert result['updated_last_3_months'] == 0
        assert result['updated_last_6_months'] == 0
        assert result['not_updated_6_months'] == 0
    
    def test_applies_sub_segment_filter(self, mock_db):
        """Should filter by sub_segment_id when provided."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[1, 2]) as mock_scope:
            with patch.object(service, '_calculate_time_cutoffs', return_value=(datetime.now(), datetime.now())):
                with patch.object(service, '_query_skills_updated_in_period', return_value=0):
                    with patch.object(service, '_query_skills_updated_before', return_value=0):
                        # Act
                        service.get_skill_momentum(mock_db, sub_segment_id=5)
        
        # Assert
        mock_scope.assert_called_once_with(mock_db, 5, None, None)
    
    def test_applies_project_filter(self, mock_db):
        """Should filter by project_id when provided."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[1]) as mock_scope:
            with patch.object(service, '_calculate_time_cutoffs', return_value=(datetime.now(), datetime.now())):
                with patch.object(service, '_query_skills_updated_in_period', return_value=0):
                    with patch.object(service, '_query_skills_updated_before', return_value=0):
                        # Act
                        service.get_skill_momentum(mock_db, project_id=10)
        
        # Assert
        mock_scope.assert_called_once_with(mock_db, None, 10, None)
    
    def test_applies_team_filter(self, mock_db):
        """Should filter by team_id when provided."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[1, 2, 3]) as mock_scope:
            with patch.object(service, '_calculate_time_cutoffs', return_value=(datetime.now(), datetime.now())):
                with patch.object(service, '_query_skills_updated_in_period', return_value=0):
                    with patch.object(service, '_query_skills_updated_before', return_value=0):
                        # Act
                        service.get_skill_momentum(mock_db, team_id=7)
        
        # Assert
        mock_scope.assert_called_once_with(mock_db, None, None, 7)
    
    def test_queries_all_three_time_periods(self, mock_db):
        """Should query counts for last 3 months, 3-6 months, and 6+ months."""
        # Arrange
        employee_ids = [1, 2]
        three_months_ago = datetime.now() - timedelta(days=90)
        six_months_ago = datetime.now() - timedelta(days=180)
        
        with patch.object(service, '_get_employee_ids_in_scope', return_value=employee_ids):
            with patch.object(service, '_calculate_time_cutoffs', return_value=(three_months_ago, six_months_ago)):
                with patch.object(service, '_query_skills_updated_in_period', side_effect=[15, 8]) as mock_period:
                    with patch.object(service, '_query_skills_updated_before', return_value=4) as mock_before:
                        # Act
                        result = service.get_skill_momentum(mock_db)
        
        # Assert
        assert mock_period.call_count == 2  # Called for 0-3 months and 3-6 months
        assert mock_before.call_count == 1  # Called for 6+ months


# ============================================================================
# TEST: _get_employee_ids_in_scope (Employee Filtering)
# ============================================================================

class TestGetEmployeeIdsInScope:
    """Test employee ID filtering by organizational hierarchy."""
    
    def test_returns_all_employees_when_no_filters(self, mock_db):
        """Should return all employee IDs when no filters provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(1,), (2,), (3,)]
        
        # Act
        result = service._get_employee_ids_in_scope(mock_db, None, None, None)
        
        # Assert
        assert result == [1, 2, 3]
        mock_db.query.assert_called_once_with(Employee.employee_id)
    
    def test_filters_by_team_when_provided(self, mock_db):
        """Should filter by team_id (highest priority)."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(5,), (6,)]
        
        # Act
        result = service._get_employee_ids_in_scope(mock_db, None, None, team_id=10)
        
        # Assert
        mock_query.filter.assert_called_once()
        assert result == [5, 6]
    
    def test_filters_by_project_when_no_team(self, mock_db):
        """Should filter by project_id when team not provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(7,), (8,)]
        
        # Act
        result = service._get_employee_ids_in_scope(mock_db, None, project_id=5, team_id=None)
        
        # Assert
        mock_query.filter.assert_called_once()
        assert result == [7, 8]
    
    def test_filters_by_sub_segment_when_no_team_or_project(self, mock_db):
        """Should filter by sub_segment_id when team and project not provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(9,), (10,)]
        
        # Act
        result = service._get_employee_ids_in_scope(mock_db, sub_segment_id=3, project_id=None, team_id=None)
        
        # Assert
        mock_query.filter.assert_called_once()
        assert result == [9, 10]
    
    def test_team_takes_precedence_over_project_and_sub_segment(self, mock_db):
        """Should use team filter when multiple filters provided (hierarchical)."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(11,)]
        
        # Act
        result = service._get_employee_ids_in_scope(
            mock_db, sub_segment_id=1, project_id=2, team_id=3
        )
        
        # Assert
        # Should only filter by team, not project or sub_segment
        assert mock_query.filter.call_count == 1
        assert result == [11]
    
    def test_returns_empty_list_when_no_employees_match(self, mock_db):
        """Should return empty list when no employees match filter."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._get_employee_ids_in_scope(mock_db, team_id=999)
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _calculate_time_cutoffs (Pure Function)
# ============================================================================

class TestCalculateTimeCutoffs:
    """Test time period calculation."""
    
    def test_returns_two_datetime_cutoffs(self):
        """Should return tuple of two datetime objects."""
        # Act
        three_months_ago, six_months_ago = service._calculate_time_cutoffs()
        
        # Assert
        assert isinstance(three_months_ago, datetime)
        assert isinstance(six_months_ago, datetime)
    
    def test_three_months_is_90_days_ago(self):
        """Should calculate 3 months as 90 days ago."""
        # Arrange
        now = datetime.now()
        expected_3m = now - timedelta(days=90)
        
        # Act
        three_months_ago, _ = service._calculate_time_cutoffs()
        
        # Assert - allow 1 second tolerance for test execution time
        diff = abs((three_months_ago - expected_3m).total_seconds())
        assert diff < 1
    
    def test_six_months_is_180_days_ago(self):
        """Should calculate 6 months as 180 days ago."""
        # Arrange
        now = datetime.now()
        expected_6m = now - timedelta(days=180)
        
        # Act
        _, six_months_ago = service._calculate_time_cutoffs()
        
        # Assert - allow 1 second tolerance
        diff = abs((six_months_ago - expected_6m).total_seconds())
        assert diff < 1
    
    def test_six_months_is_before_three_months(self):
        """Should ensure 6 months cutoff is before 3 months cutoff."""
        # Act
        three_months_ago, six_months_ago = service._calculate_time_cutoffs()
        
        # Assert
        assert six_months_ago < three_months_ago


# ============================================================================
# TEST: _query_skills_updated_in_period (Period Query)
# ============================================================================

class TestQuerySkillsUpdatedInPeriod:
    """Test skill count query for a time period."""
    
    def test_counts_skills_updated_in_period(self, mock_db):
        """Should count distinct skills updated within time range."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 25
        
        start_date = datetime.now() - timedelta(days=90)
        end_date = datetime.now()
        
        # Act
        result = service._query_skills_updated_in_period(
            mock_db, [1, 2, 3], start_date, end_date
        )
        
        # Assert
        assert result == 25
        assert mock_query.filter.call_count >= 1
        mock_query.scalar.assert_called_once()
    
    def test_filters_by_employee_ids(self, mock_db):
        """Should filter by provided employee IDs."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 10
        
        # Act
        service._query_skills_updated_in_period(
            mock_db, [5, 10, 15], datetime.now(), None
        )
        
        # Assert
        mock_query.filter.assert_called()
    
    def test_handles_no_end_date(self, mock_db):
        """Should handle None end_date (no upper bound)."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15
        
        start_date = datetime.now() - timedelta(days=90)
        
        # Act
        result = service._query_skills_updated_in_period(
            mock_db, [1, 2], start_date, None
        )
        
        # Assert
        assert result == 15
    
    def test_returns_zero_when_no_skills_in_period(self, mock_db):
        """Should return 0 when no skills updated in period."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_skills_updated_in_period(
            mock_db, [1], datetime.now(), datetime.now()
        )
        
        # Assert
        assert result == 0


# ============================================================================
# TEST: _query_skills_updated_before (Before Cutoff Query)
# ============================================================================

class TestQuerySkillsUpdatedBefore:
    """Test skill count query for skills NOT updated recently."""
    
    def test_counts_skills_updated_before_cutoff(self, mock_db):
        """Should count distinct skills updated before cutoff date."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 8
        
        cutoff = datetime.now() - timedelta(days=180)
        
        # Act
        result = service._query_skills_updated_before(mock_db, [1, 2, 3], cutoff)
        
        # Assert
        assert result == 8
        mock_query.filter.assert_called()
        mock_query.scalar.assert_called_once()
    
    def test_filters_by_employee_ids(self, mock_db):
        """Should filter by provided employee IDs."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        
        # Act
        service._query_skills_updated_before(mock_db, [7, 8, 9], datetime.now())
        
        # Assert
        mock_query.filter.assert_called()
    
    def test_returns_zero_when_no_old_skills(self, mock_db):
        """Should return 0 when no skills updated before cutoff."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_skills_updated_before(mock_db, [1], datetime.now())
        
        # Assert
        assert result == 0


# ============================================================================
# TEST: _build_response (Pure Function)
# ============================================================================

class TestBuildResponse:
    """Test response dictionary building."""
    
    def test_builds_response_with_all_required_keys(self):
        """Should build response dict with all three required keys."""
        # Act
        result = service._build_response(10, 5, 3)
        
        # Assert
        assert 'updated_last_3_months' in result
        assert 'updated_last_6_months' in result
        assert 'not_updated_6_months' in result
    
    def test_assigns_correct_values_to_keys(self):
        """Should assign counts to correct time period keys."""
        # Act
        result = service._build_response(
            updated_3m=20,
            updated_6m=15,
            not_updated=8
        )
        
        # Assert
        assert result['updated_last_3_months'] == 20
        assert result['updated_last_6_months'] == 15
        assert result['not_updated_6_months'] == 8
    
    def test_handles_zero_counts(self):
        """Should handle all zero counts."""
        # Act
        result = service._build_response(0, 0, 0)
        
        # Assert
        assert result['updated_last_3_months'] == 0
        assert result['updated_last_6_months'] == 0
        assert result['not_updated_6_months'] == 0
    
    def test_returns_dict_type(self):
        """Should return a dictionary."""
        # Act
        result = service._build_response(1, 2, 3)
        
        # Assert
        assert isinstance(result, dict)
