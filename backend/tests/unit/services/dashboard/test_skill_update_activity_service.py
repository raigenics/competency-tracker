"""
Unit tests for dashboard/skill_update_activity_service.py

Tests skill update activity metrics with mutually exclusive buckets:
- engaged: >= 2 updates
- active: exactly 1 update
- inactive: 0 updates
- stagnant_180_days: no updates in 180 days
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.dashboard import skill_update_activity_service
from app.services.dashboard.skill_update_activity_service import (
    InvalidDaysParameterError,
    _calculate_activity_metrics,
    _build_response,
    _validate_days_parameter,
    _calculate_cutoff_dates,
)


class TestGetSkillUpdateActivity:
    """Test the main public function get_skill_update_activity()."""
    
    def test_returns_activity_metrics(self, mock_db):
        """Should return dict with engaged, active, inactive, stagnant_180_days."""
        # Arrange
        with patch.object(skill_update_activity_service, '_validate_days_parameter'), \
             patch.object(skill_update_activity_service, '_calculate_cutoff_dates', return_value=(datetime.utcnow(), datetime.utcnow())), \
             patch.object(skill_update_activity_service, '_get_employee_ids_in_scope', return_value=[1, 2, 3, 4, 5]), \
             patch.object(skill_update_activity_service, '_query_updates_per_employee', return_value={1: 3, 2: 1, 3: 2}), \
             patch.object(skill_update_activity_service, '_query_stagnant_employees', return_value=1):
            
            # Act
            result = skill_update_activity_service.get_skill_update_activity(mock_db, 90)
            
            # Assert
            assert "days" in result
            assert "engaged" in result
            assert "active" in result
            assert "inactive" in result
            assert "stagnant_180_days" in result
    
    def test_empty_scope_returns_zeros(self, mock_db):
        """Should return all zeros when no employees in scope."""
        # Arrange
        with patch.object(skill_update_activity_service, '_validate_days_parameter'), \
             patch.object(skill_update_activity_service, '_calculate_cutoff_dates', return_value=(datetime.utcnow(), datetime.utcnow())), \
             patch.object(skill_update_activity_service, '_get_employee_ids_in_scope', return_value=[]):
            
            # Act
            result = skill_update_activity_service.get_skill_update_activity(mock_db, 90)
            
            # Assert
            assert result["engaged"] == 0
            assert result["active"] == 0
            assert result["inactive"] == 0
            assert result["stagnant_180_days"] == 0
    
    def test_invalid_days_raises_error(self, mock_db):
        """Should raise InvalidDaysParameterError for invalid days."""
        with pytest.raises(InvalidDaysParameterError):
            skill_update_activity_service.get_skill_update_activity(mock_db, 0)
        
        with pytest.raises(InvalidDaysParameterError):
            skill_update_activity_service.get_skill_update_activity(mock_db, 400)


class TestCalculateActivityMetrics:
    """Test the _calculate_activity_metrics function."""
    
    def test_mutually_exclusive_buckets(self):
        """Engaged, active, inactive should be mutually exclusive."""
        # Arrange: 5 employees
        # emp 1: 3 updates -> engaged
        # emp 2: 2 updates -> engaged
        # emp 3: 1 update -> active
        # emp 4, 5: 0 updates -> inactive
        employee_ids = [1, 2, 3, 4, 5]
        update_counts = {1: 3, 2: 2, 3: 1}  # emp 4, 5 have 0
        
        # Act
        engaged, active, inactive = _calculate_activity_metrics(employee_ids, update_counts)
        
        # Assert
        assert engaged == 2  # emp 1, 2
        assert active == 1   # emp 3
        assert inactive == 2 # emp 4, 5
        assert engaged + active + inactive == len(employee_ids)
    
    def test_employees_with_exactly_one_update_in_active(self):
        """Employees with exactly 1 update should appear in active, not engaged."""
        employee_ids = [1, 2, 3]
        update_counts = {1: 1, 2: 1, 3: 1}  # all have exactly 1 update
        
        engaged, active, inactive = _calculate_activity_metrics(employee_ids, update_counts)
        
        assert engaged == 0
        assert active == 3
        assert inactive == 0
    
    def test_employees_with_two_plus_updates_in_engaged(self):
        """Employees with >= 2 updates should be in engaged."""
        employee_ids = [1, 2, 3]
        update_counts = {1: 2, 2: 5, 3: 10}
        
        engaged, active, inactive = _calculate_activity_metrics(employee_ids, update_counts)
        
        assert engaged == 3
        assert active == 0
        assert inactive == 0
    
    def test_all_inactive_when_no_updates(self):
        """All employees should be inactive when no updates."""
        employee_ids = [1, 2, 3, 4, 5]
        update_counts = {}  # no updates
        
        engaged, active, inactive = _calculate_activity_metrics(employee_ids, update_counts)
        
        assert engaged == 0
        assert active == 0
        assert inactive == 5
    
    def test_sum_equals_total_employees(self):
        """engaged + active + inactive must equal total employees in scope."""
        employee_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        update_counts = {1: 5, 2: 3, 3: 2, 4: 1, 5: 1}
        
        engaged, active, inactive = _calculate_activity_metrics(employee_ids, update_counts)
        
        assert engaged + active + inactive == len(employee_ids)


class TestBuildResponse:
    """Test the _build_response function."""
    
    def test_returns_correct_keys(self):
        """Should return dict with correct keys."""
        result = _build_response(90, 10, 5, 15, 3)
        
        assert result["days"] == 90
        assert result["engaged"] == 10
        assert result["active"] == 5
        assert result["inactive"] == 15
        assert result["stagnant_180_days"] == 3
    
    def test_does_not_include_old_keys(self):
        """Should not include old keys like total_updates, active_learners, low_activity."""
        result = _build_response(90, 10, 5, 15, 3)
        
        assert "total_updates" not in result
        assert "active_learners" not in result
        assert "low_activity" not in result


class TestValidateDaysParameter:
    """Test the _validate_days_parameter function."""
    
    def test_valid_days_passes(self):
        """Should not raise for valid days (1-365)."""
        _validate_days_parameter(1)
        _validate_days_parameter(90)
        _validate_days_parameter(365)
    
    def test_zero_raises_error(self):
        """Should raise for days = 0."""
        with pytest.raises(InvalidDaysParameterError):
            _validate_days_parameter(0)
    
    def test_negative_raises_error(self):
        """Should raise for negative days."""
        with pytest.raises(InvalidDaysParameterError):
            _validate_days_parameter(-1)
    
    def test_over_365_raises_error(self):
        """Should raise for days > 365."""
        with pytest.raises(InvalidDaysParameterError):
            _validate_days_parameter(366)


class TestCalculateCutoffDates:
    """Test the _calculate_cutoff_dates function."""
    
    def test_returns_two_dates(self):
        """Should return tuple of two datetime objects."""
        cutoff, stagnant = _calculate_cutoff_dates(90)
        
        assert isinstance(cutoff, datetime)
        assert isinstance(stagnant, datetime)
    
    def test_stagnant_always_180_days(self):
        """Stagnant cutoff should always be 180 days regardless of days param."""
        cutoff_30, stagnant_30 = _calculate_cutoff_dates(30)
        cutoff_90, stagnant_90 = _calculate_cutoff_dates(90)
        
        # Stagnant dates should be approximately the same (within a few seconds)
        diff = abs((stagnant_30 - stagnant_90).total_seconds())
        assert diff < 5  # less than 5 seconds difference
