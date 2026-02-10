"""
Unit tests for employee_profile/employee_skills_service.py

Tests employee skills bulk save functionality.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from fastapi import HTTPException

from app.services.employee_profile import employee_skills_service
from app.schemas.employee import EmployeeSkillItem


class TestSaveEmployeeSkills:
    """Test save_employee_skills function."""
    
    def test_returns_tuple_of_saved_and_deleted_counts(self, mock_db):
        """Should return (skills_saved, skills_deleted) tuple, not an awaitable."""
        # Arrange
        mock_employee = Mock()
        mock_employee.employee_id = 1
        
        mock_proficiency = Mock()
        mock_proficiency.proficiency_level_id = 1
        
        # Setup mock_db query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_employee
        mock_query.count.return_value = 2
        mock_query.delete.return_value = 2
        # For validate_skills_exist - return the skill_id
        mock_query.all.return_value = [(1,)]
        
        mock_db.query.return_value = mock_query
        
        # Mock proficiency lookup
        with patch.object(
            employee_skills_service, 
            '_get_proficiency_level_id', 
            return_value=1
        ):
            # Create test skill item
            skill_item = EmployeeSkillItem(
                skill_id=1,
                proficiency='EXPERT',
                years_experience=5
            )
            
            # Act
            result = employee_skills_service.save_employee_skills(mock_db, 1, [skill_item])
            
            # Assert - Should be a tuple, not a coroutine
            assert isinstance(result, tuple)
            assert len(result) == 2
            skills_saved, skills_deleted = result
            assert skills_saved == 1
            assert skills_deleted == 2

    def test_validates_employee_exists(self, mock_db):
        """Should raise 404 when employee doesn't exist."""
        # Arrange - Employee not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        skill_item = EmployeeSkillItem(
            skill_id=1,
            proficiency='EXPERT',
            years_experience=5
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            employee_skills_service.save_employee_skills(mock_db, 999, [skill_item])
        
        assert exc_info.value.status_code == 404
        assert "Employee not found" in exc_info.value.detail

    def test_empty_skills_list_clears_all_skills(self, mock_db):
        """Should delete all skills and save 0 when empty list provided."""
        # Arrange
        mock_employee = Mock()
        mock_employee.employee_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_employee
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        
        # Act
        result = employee_skills_service.save_employee_skills(mock_db, 1, [])
        
        # Assert
        skills_saved, skills_deleted = result
        assert skills_saved == 0
        assert skills_deleted == 3


class TestValidateSkillsExist:
    """Test validate_skills_exist helper function."""
    
    def test_passes_for_empty_list(self, mock_db):
        """Should not raise when skill_ids list is empty."""
        # Act & Assert - Should not raise
        employee_skills_service.validate_skills_exist(mock_db, [])

    def test_raises_422_for_invalid_skill_ids(self, mock_db):
        """Should raise 422 when some skill_ids don't exist."""
        # Arrange - Only skill_id 1 exists
        mock_db.query.return_value.filter.return_value.all.return_value = [(1,)]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            employee_skills_service.validate_skills_exist(mock_db, [1, 2, 999])
        
        assert exc_info.value.status_code == 422
        assert "Invalid skill_id" in exc_info.value.detail
