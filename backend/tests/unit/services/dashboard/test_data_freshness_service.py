"""
Unit tests for dashboard/data_freshness_service.py

Tests data freshness calculation (% of employees with recent skill updates).
Coverage: Parameter validation, employee scoping, percentage calculation, edge cases.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from app.services.dashboard import data_freshness_service as service


# ============================================================================
# TEST: get_data_freshness (Main Entry Point)
# ============================================================================

class TestGetDataFreshness:
    """Test the main data freshness function."""
    
    def test_returns_correct_structure(self, mock_db):
        """Should return dict with all required fields."""
        # Arrange
        employee_ids = [1, 2, 3, 4, 5]
        
        with patch.object(service, '_get_employee_ids_in_scope', return_value=employee_ids):
            with patch.object(service, '_count_employees_with_updates', return_value=4):
                # Act
                result = service.get_data_freshness(mock_db, days=90)
        
        # Assert
        assert 'window_days' in result
        assert 'employees_in_scope' in result
        assert 'employees_with_update' in result
        assert 'freshness_percent' in result
    
    def test_calculates_correct_percentage(self, mock_db):
        """Should calculate freshness_percent = (employees_with_update / employees_in_scope) * 100."""
        # Arrange
        employee_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # 10 employees
        
        with patch.object(service, '_get_employee_ids_in_scope', return_value=employee_ids):
            with patch.object(service, '_count_employees_with_updates', return_value=8):  # 8 with updates
                # Act
                result = service.get_data_freshness(mock_db, days=90)
        
        # Assert
        assert result['employees_in_scope'] == 10
        assert result['employees_with_update'] == 8
        assert result['freshness_percent'] == 80.0
    
    def test_rounds_percentage_to_one_decimal(self, mock_db):
        """Should round freshness_percent to 1 decimal place."""
        # Arrange
        employee_ids = [1, 2, 3]  # 3 employees
        
        with patch.object(service, '_get_employee_ids_in_scope', return_value=employee_ids):
            with patch.object(service, '_count_employees_with_updates', return_value=2):  # 2/3 = 66.666...
                # Act
                result = service.get_data_freshness(mock_db, days=90)
        
        # Assert
        assert result['freshness_percent'] == 66.7
    
    def test_returns_zeros_when_no_employees_in_scope(self, mock_db):
        """Should return 0% freshness when no employees match filters."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[]):
            # Act
            result = service.get_data_freshness(mock_db, days=90)
        
        # Assert
        assert result['employees_in_scope'] == 0
        assert result['employees_with_update'] == 0
        assert result['freshness_percent'] == 0.0
    
    def test_returns_100_percent_when_all_employees_have_updates(self, mock_db):
        """Should return 100% when all employees have updates."""
        # Arrange
        employee_ids = [1, 2, 3, 4, 5]
        
        with patch.object(service, '_get_employee_ids_in_scope', return_value=employee_ids):
            with patch.object(service, '_count_employees_with_updates', return_value=5):
                # Act
                result = service.get_data_freshness(mock_db, days=90)
        
        # Assert
        assert result['freshness_percent'] == 100.0
    
    def test_echoes_days_parameter(self, mock_db):
        """Should echo the days parameter in response."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[1]):
            with patch.object(service, '_count_employees_with_updates', return_value=1):
                # Act
                result = service.get_data_freshness(mock_db, days=30)
        
        # Assert
        assert result['window_days'] == 30
    
    def test_applies_sub_segment_filter(self, mock_db):
        """Should filter by sub_segment_id when provided."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[1, 2]) as mock_scope:
            with patch.object(service, '_count_employees_with_updates', return_value=1):
                # Act
                service.get_data_freshness(mock_db, days=90, sub_segment_id=5)
        
        # Assert
        mock_scope.assert_called_once_with(mock_db, 5, None, None)
    
    def test_applies_project_filter(self, mock_db):
        """Should filter by project_id when provided."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[1]) as mock_scope:
            with patch.object(service, '_count_employees_with_updates', return_value=1):
                # Act
                service.get_data_freshness(mock_db, days=90, project_id=10)
        
        # Assert
        mock_scope.assert_called_once_with(mock_db, None, 10, None)
    
    def test_applies_team_filter(self, mock_db):
        """Should filter by team_id when provided."""
        # Arrange
        with patch.object(service, '_get_employee_ids_in_scope', return_value=[1]) as mock_scope:
            with patch.object(service, '_count_employees_with_updates', return_value=1):
                # Act
                service.get_data_freshness(mock_db, days=90, team_id=15)
        
        # Assert
        mock_scope.assert_called_once_with(mock_db, None, None, 15)


# ============================================================================
# TEST: _validate_days_parameter
# ============================================================================

class TestValidateDaysParameter:
    """Test days parameter validation."""
    
    def test_valid_days_passes(self):
        """Should not raise for valid days values."""
        # These should not raise
        service._validate_days_parameter(1)
        service._validate_days_parameter(90)
        service._validate_days_parameter(365)
    
    def test_zero_days_raises(self):
        """Should raise InvalidDaysParameterError for 0 days."""
        with pytest.raises(service.InvalidDaysParameterError):
            service._validate_days_parameter(0)
    
    def test_negative_days_raises(self):
        """Should raise InvalidDaysParameterError for negative days."""
        with pytest.raises(service.InvalidDaysParameterError):
            service._validate_days_parameter(-1)
    
    def test_over_365_raises(self):
        """Should raise InvalidDaysParameterError for days > 365."""
        with pytest.raises(service.InvalidDaysParameterError):
            service._validate_days_parameter(366)


# ============================================================================
# TEST: _build_response
# ============================================================================

class TestBuildResponse:
    """Test response builder helper."""
    
    def test_builds_correct_structure(self):
        """Should build response with all required fields."""
        # Act
        result = service._build_response(
            window_days=90,
            employees_in_scope=100,
            employees_with_update=85,
            freshness_percent=85.0
        )
        
        # Assert
        assert result == {
            "window_days": 90,
            "employees_in_scope": 100,
            "employees_with_update": 85,
            "freshness_percent": 85.0
        }


# ============================================================================
# TEST: _count_employees_with_updates (DB Query Integration)
# ============================================================================

class TestCountEmployeesWithUpdates:
    """Test the DB query for counting employees with updates."""
    
    def test_queries_with_correct_filters(self, mock_db):
        """Should query EmployeeSkill with employee_id and date filters."""
        # Arrange
        employee_ids = [1, 2, 3]
        cutoff = datetime.utcnow() - timedelta(days=90)
        
        mock_count_query = MagicMock()
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.scalar.return_value = 2
        mock_db.query.return_value = mock_count_query
        
        # Act
        result = service._count_employees_with_updates(mock_db, employee_ids, cutoff)
        
        # Assert
        assert result == 2
        mock_db.query.assert_called_once()
    
    def test_returns_zero_when_no_updates(self, mock_db):
        """Should return 0 when scalar returns None."""
        # Arrange
        mock_count_query = MagicMock()
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.scalar.return_value = None
        mock_db.query.return_value = mock_count_query
        
        # Act
        result = service._count_employees_with_updates(
            mock_db, [1, 2], datetime.utcnow()
        )
        
        # Assert
        assert result == 0
