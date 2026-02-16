"""
Unit tests for roles_service.py

Tests:
1. get_all_roles returns list of roles
2. get_role_by_id returns role or None
"""
import pytest
from unittest.mock import Mock, MagicMock

from app.services.roles_service import get_all_roles, get_role_by_id


class TestGetAllRoles:
    """Test get_all_roles function."""
    
    def test_returns_list_of_roles(self, mock_db):
        """Should return all roles from database."""
        # Arrange
        mock_role1 = Mock()
        mock_role1.role_id = 1
        mock_role1.role_name = "Developer"
        mock_role1.role_description = "Developer role"
        
        mock_role2 = Mock()
        mock_role2.role_id = 2
        mock_role2.role_name = "Manager"
        mock_role2.role_description = "Manager role"
        
        # Set up the query chain: query().filter().order_by().all()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_role1, mock_role2]
        
        # Act
        result = get_all_roles(mock_db)
        
        # Assert
        assert len(result) == 2
        assert result[0]['role_id'] == 1
        assert result[0]['role_name'] == "Developer"
        assert result[1]['role_id'] == 2
        assert result[1]['role_name'] == "Manager"
    
    def test_returns_empty_list_when_no_roles(self, mock_db):
        """Should return empty list when no roles exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = get_all_roles(mock_db)
        
        # Assert
        assert result == []
    
    def test_returns_ordered_by_role_name(self, mock_db):
        """Should call order_by on query."""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = get_all_roles(mock_db)
        
        # Assert - verify order_by was called
        mock_db.query.return_value.filter.return_value.order_by.assert_called_once()


class TestGetRoleById:
    """Test get_role_by_id function."""
    
    def test_returns_role_when_found(self, mock_db):
        """Should return role dict when found."""
        # Arrange
        mock_role = Mock()
        mock_role.role_id = 5
        mock_role.role_name = "Tech Lead"
        mock_role.role_description = "Tech Lead role"
        # Chain: query().filter().filter().first()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_role
        
        # Act
        result = get_role_by_id(mock_db, 5)
        
        # Assert
        assert result is not None
        assert result['role_id'] == 5
        assert result['role_name'] == "Tech Lead"
    
    def test_returns_none_when_not_found(self, mock_db):
        """Should return None when role_id doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = get_role_by_id(mock_db, 999)
        
        # Assert
        assert result is None
