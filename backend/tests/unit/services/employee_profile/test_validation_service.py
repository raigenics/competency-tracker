"""
Unit tests for employee_profile/validation_service.py

Tests ZID and email uniqueness validation.
"""
import pytest
from unittest.mock import Mock, MagicMock

from app.services.employee_profile import validation_service


def setup_mock_query_chain(mock_db, first_return_value):
    """Helper to set up a mock query that is chainable and returns specified value."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query  # Make filter chainable
    mock_query.first.return_value = first_return_value
    mock_db.query.return_value = mock_query
    return mock_query


class TestCheckZidExists:
    """Test check_zid_exists function."""
    
    def test_returns_false_for_empty_zid(self, mock_db):
        """Should return False when ZID is empty or None."""
        assert validation_service.check_zid_exists(mock_db, None) is False
        assert validation_service.check_zid_exists(mock_db, "") is False
        assert validation_service.check_zid_exists(mock_db, "   ") is False
    
    def test_returns_true_when_zid_exists(self, mock_db):
        """Should return True when ZID is found in database."""
        # Arrange
        existing_employee = Mock()
        existing_employee.employee_id = 1
        existing_employee.zid = "Z123456"
        setup_mock_query_chain(mock_db, existing_employee)
        
        # Act
        result = validation_service.check_zid_exists(mock_db, "Z123456")
        
        # Assert
        assert result is True
    
    def test_returns_false_when_zid_not_found(self, mock_db):
        """Should return False when ZID is not in database."""
        # Arrange
        setup_mock_query_chain(mock_db, None)
        
        # Act
        result = validation_service.check_zid_exists(mock_db, "Z999999")
        
        # Assert
        assert result is False
    
    def test_excludes_employee_when_exclude_id_provided(self, mock_db):
        """Should return False when the only match is the excluded employee."""
        # Arrange - ZID exists but belongs to excluded employee
        setup_mock_query_chain(mock_db, None)
        
        # Act
        result = validation_service.check_zid_exists(mock_db, "Z123456", exclude_employee_id=1)
        
        # Assert
        assert result is False


class TestCheckEmailExists:
    """Test check_email_exists function."""
    
    def test_returns_false_for_empty_email(self, mock_db):
        """Should return False when email is empty or None."""
        assert validation_service.check_email_exists(mock_db, None) is False
        assert validation_service.check_email_exists(mock_db, "") is False
        assert validation_service.check_email_exists(mock_db, "   ") is False
    
    def test_returns_true_when_email_exists(self, mock_db):
        """Should return True when email is found in database."""
        # Arrange
        existing_employee = Mock()
        existing_employee.employee_id = 1
        existing_employee.email = "john@example.com"
        setup_mock_query_chain(mock_db, existing_employee)
        
        # Act
        result = validation_service.check_email_exists(mock_db, "john@example.com")
        
        # Assert
        assert result is True
    
    def test_returns_false_when_email_not_found(self, mock_db):
        """Should return False when email is not in database."""
        # Arrange
        setup_mock_query_chain(mock_db, None)
        
        # Act
        result = validation_service.check_email_exists(mock_db, "new@example.com")
        
        # Assert
        assert result is False
    
    def test_excludes_employee_when_exclude_id_provided(self, mock_db):
        """Should return False when the only match is the excluded employee."""
        # Arrange - email exists but belongs to excluded employee
        setup_mock_query_chain(mock_db, None)
        
        # Act
        result = validation_service.check_email_exists(mock_db, "john@example.com", exclude_employee_id=1)
        
        # Assert
        assert result is False


class TestValidateUnique:
    """Test validate_unique combined function."""
    
    def test_returns_both_false_when_neither_exists(self, mock_db):
        """Should return both flags as False when ZID and email are unique."""
        # Arrange
        setup_mock_query_chain(mock_db, None)
        
        # Act
        result = validation_service.validate_unique(mock_db, zid="Z999999", email="new@example.com")
        
        # Assert
        assert result["zid_exists"] is False
        assert result["email_exists"] is False
    
    def test_returns_zid_exists_true_when_zid_found(self, mock_db):
        """Should return zid_exists=True when ZID is already in use."""
        # Arrange
        existing = Mock()
        setup_mock_query_chain(mock_db, existing)
        
        # Act
        result = validation_service.validate_unique(mock_db, zid="Z123456")
        
        # Assert
        assert result["zid_exists"] is True
    
    def test_returns_email_exists_true_when_email_found(self, mock_db):
        """Should return email_exists=True when email is already in use."""
        # Arrange
        existing = Mock()
        setup_mock_query_chain(mock_db, existing)
        
        # Act
        result = validation_service.validate_unique(mock_db, email="existing@example.com")
        
        # Assert
        assert result["email_exists"] is True
    
    def test_returns_false_for_both_when_excluded_matches(self, mock_db):
        """Should return False for both when exclude_employee_id matches."""
        # Arrange - no matches after exclusion
        setup_mock_query_chain(mock_db, None)
        
        # Act
        result = validation_service.validate_unique(
            mock_db, 
            zid="Z123456", 
            email="john@example.com",
            exclude_employee_id=1
        )
        
        # Assert
        assert result["zid_exists"] is False
        assert result["email_exists"] is False
    
    def test_returns_false_when_params_not_provided(self, mock_db):
        """Should return False for both when neither zid nor email provided."""
        # Act
        result = validation_service.validate_unique(mock_db)
        
        # Assert
        assert result["zid_exists"] is False
        assert result["email_exists"] is False
