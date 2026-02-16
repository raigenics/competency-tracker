"""
Unit tests for capability_finder/roles_service.py

Tests for fetching role names for typeahead/autocomplete.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_finder import roles_service as service
from app.models.role import Role


# ============================================================================
# TEST: get_all_roles (Main Entry Point)
# ============================================================================

class TestGetAllRoles:
    """Test the main get all roles function."""
    
    def test_returns_role_names_from_query(self, mock_db):
        """Should return role names from database query."""
        # Arrange
        with patch.object(service, '_query_all_roles', return_value=['Analyst', 'Developer', 'Manager']):
            # Act
            result = service.get_all_roles(mock_db)
        
        # Assert
        assert result == ['Analyst', 'Developer', 'Manager']
    
    def test_returns_empty_list_when_no_roles(self, mock_db):
        """Should return empty list when no roles in database."""
        # Arrange
        with patch.object(service, '_query_all_roles', return_value=[]):
            # Act
            result = service.get_all_roles(mock_db)
        
        # Assert
        assert result == []
    
    def test_calls_query_function_with_db_session(self, mock_db):
        """Should pass db session to query function."""
        # Arrange
        with patch.object(service, '_query_all_roles', return_value=[]) as mock_query:
            # Act
            service.get_all_roles(mock_db)
        
        # Assert
        mock_query.assert_called_once_with(mock_db)
    
    def test_returns_sorted_roles(self, mock_db):
        """Should return roles sorted alphabetically A-Z."""
        # Arrange
        with patch.object(service, '_query_all_roles', return_value=['Analyst', 'Developer', 'Tester']):
            # Act
            result = service.get_all_roles(mock_db)
        
        # Assert
        assert result == ['Analyst', 'Developer', 'Tester']


# ============================================================================
# TEST: _query_all_roles (Query Helper)
# ============================================================================

class TestQueryAllRoles:
    """Test the roles query helper."""
    
    def test_queries_distinct_role_names(self, mock_db):
        """Should query distinct role names from database."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [('Analyst',), ('Developer',), ('Manager',)]
        
        # Act
        result = service._query_all_roles(mock_db)
        
        # Assert
        mock_db.query.assert_called_once_with(Role.role_name)
        mock_query.distinct.assert_called_once()
    
    def test_orders_by_role_name_ascending(self, mock_db):
        """Should order roles by name alphabetically."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_all_roles(mock_db)
        
        # Assert
        mock_query.order_by.assert_called_once()
    
    def test_extracts_role_names_from_tuples(self, mock_db):
        """Should extract role names from query result tuples."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [('Developer',), ('QA',), ('Architect',)]
        
        # Act
        result = service._query_all_roles(mock_db)
        
        # Assert
        assert result == ['Developer', 'QA', 'Architect']
    
    def test_returns_empty_list_when_no_roles(self, mock_db):
        """Should return empty list when no roles found."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_all_roles(mock_db)
        
        # Assert
        assert result == []
    
    def test_handles_single_role(self, mock_db):
        """Should handle database with single role."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [('Admin',)]
        
        # Act
        result = service._query_all_roles(mock_db)
        
        # Assert
        assert result == ['Admin']
    
    def test_handles_many_roles(self, mock_db):
        """Should handle database with many roles."""
        # Arrange
        roles = [(f'Role{i}',) for i in range(100)]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = roles
        
        # Act
        result = service._query_all_roles(mock_db)
        
        # Assert
        assert len(result) == 100
        assert result[0] == 'Role0'
        assert result[99] == 'Role99'
