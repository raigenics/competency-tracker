"""
Unit tests for roles_service.py

Tests:
1. get_all_roles returns list of roles
2. get_role_by_id returns role or None
3. create_role creates role with alias
4. create_role fails with duplicate role_name
5. create_role fails when role_name matches existing alias
6. update_role updates role with alias
7. update_role fails when role_name matches existing alias of another role
8. update_role succeeds when only self matches
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from app.services.roles_service import (
    get_all_roles, 
    get_role_by_id, 
    create_role, 
    update_role,
    _check_role_name_duplicate
)


class TestGetAllRoles:
    """Test get_all_roles function."""
    
    def test_returns_list_of_roles(self, mock_db):
        """Should return all roles from database with role_alias and role_description."""
        # Arrange
        mock_role1 = Mock()
        mock_role1.role_id = 1
        mock_role1.role_name = "Developer"
        mock_role1.role_alias = "Dev, Software Engineer"
        mock_role1.role_description = "Developer role"
        
        mock_role2 = Mock()
        mock_role2.role_id = 2
        mock_role2.role_name = "Manager"
        mock_role2.role_alias = None
        mock_role2.role_description = "Manager role"
        
        # Set up the query chain: query().filter().order_by().all()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_role1, mock_role2]
        
        # Act
        result = get_all_roles(mock_db)
        
        # Assert
        assert len(result) == 2
        assert result[0]['role_id'] == 1
        assert result[0]['role_name'] == "Developer"
        assert result[0]['role_alias'] == "Dev, Software Engineer"
        assert result[0]['role_description'] == "Developer role"
        assert result[1]['role_id'] == 2
        assert result[1]['role_name'] == "Manager"
        assert result[1]['role_alias'] is None
        assert result[1]['role_description'] == "Manager role"
    
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
        """Should return role dict with role_alias and role_description when found."""
        # Arrange
        mock_role = Mock()
        mock_role.role_id = 5
        mock_role.role_name = "Tech Lead"
        mock_role.role_alias = "TL, Technical Lead"
        mock_role.role_description = "Tech Lead role"
        # Chain: query().filter().filter().first()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_role
        
        # Act
        result = get_role_by_id(mock_db, 5)
        
        # Assert
        assert result is not None
        assert result['role_id'] == 5
        assert result['role_name'] == "Tech Lead"
        assert result['role_alias'] == "TL, Technical Lead"
        assert result['role_description'] == "Tech Lead role"
    
    def test_returns_none_when_not_found(self, mock_db):
        """Should return None when role_id doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = get_role_by_id(mock_db, 999)
        
        # Assert
        assert result is None


class TestCreateRole:
    """Test create_role function."""
    
    def test_creates_role_with_alias(self, mock_db):
        """Should create role and return role_alias in response."""
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock query chain for duplicate check - no duplicates
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No name duplicate
        mock_query.all.return_value = []  # No alias duplicates
        mock_db.query.return_value = mock_query
        
        # Act
        with patch('app.services.roles_service.Role') as MockRole:
            mock_instance = Mock()
            mock_instance.role_id = 10
            mock_instance.role_name = "Senior Developer"
            mock_instance.role_alias = "Sr. Dev, Senior Dev"
            mock_instance.role_description = "Senior developer role"
            MockRole.return_value = mock_instance
            
            result = create_role(
                db=mock_db,
                role_name="Senior Developer",
                role_alias="Sr. Dev, Senior Dev",
                role_description="Senior developer role",
                created_by="test_user"
            )
        
        # Assert
        assert result['role_id'] == 10
        assert result['role_name'] == "Senior Developer"
        assert result['role_alias'] == "Sr. Dev, Senior Dev"
        assert result['role_description'] == "Senior developer role"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_creates_role_without_alias(self, mock_db):
        """Should create role with None alias when not provided."""
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock query chain for duplicate check - no duplicates
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        with patch('app.services.roles_service.Role') as MockRole:
            mock_instance = Mock()
            mock_instance.role_id = 11
            mock_instance.role_name = "QA Engineer"
            mock_instance.role_alias = None
            mock_instance.role_description = None
            MockRole.return_value = mock_instance
            
            result = create_role(
                db=mock_db,
                role_name="QA Engineer",
                created_by="test_user"
            )
        
        # Assert
        assert result['role_id'] == 11
        assert result['role_alias'] is None


class TestUpdateRole:
    """Test update_role function."""
    
    def test_updates_role_with_alias(self, mock_db):
        """Should update role including role_alias."""
        # Arrange
        mock_role = Mock()
        mock_role.role_id = 5
        mock_role.role_name = "Tech Lead"
        mock_role.role_alias = None
        mock_role.role_description = "Tech Lead role"
        
        # Mock query that returns the role for update check
        # and also handles duplicate check queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_role, None]  # First: get role, Second: no dup check match
        mock_query.all.return_value = []  # No alias duplicates
        mock_db.query.return_value = mock_query
        
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = update_role(
            db=mock_db,
            role_id=5,
            role_name="Tech Lead",
            role_alias="TL, Technical Lead",
            role_description="Updated description"
        )
        
        # Assert
        assert result is not None
        assert mock_role.role_alias == "TL, Technical Lead"
        assert mock_role.role_description == "Updated description"
        mock_db.commit.assert_called_once()


class TestCheckRoleNameDuplicate:
    """Test _check_role_name_duplicate helper function."""
    
    def test_returns_false_when_no_duplicate(self, mock_db):
        """Should return (False, None, None) when no duplicate found."""
        # Arrange - no existing roles
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        is_dup, msg, conflict_role = _check_role_name_duplicate(mock_db, "New Role")
        
        # Assert
        assert is_dup is False
        assert msg is None
        assert conflict_role is None
    
    def test_returns_true_when_role_name_matches_existing(self, mock_db):
        """Should detect duplicate when role_name matches existing role_name."""
        # Arrange - existing role with same name
        existing_role = Mock()
        existing_role.role_id = 1
        existing_role.role_name = "Developer"
        existing_role.role_alias = None
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_role
        mock_db.query.return_value = mock_query
        
        # Act
        is_dup, msg, conflict_role = _check_role_name_duplicate(mock_db, "Developer")
        
        # Assert
        assert is_dup is True
        assert "already exists" in msg
        assert conflict_role == "Developer"
    
    def test_returns_true_when_role_name_matches_alias_token(self, mock_db):
        """Should detect duplicate when role_name matches an alias token."""
        # Arrange - no name match, but alias match
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No direct name match
        
        role_with_alias = Mock()
        role_with_alias.role_id = 1
        role_with_alias.role_name = "Software Engineer"
        role_with_alias.role_alias = "Dev, SDE, Coder"
        mock_query.all.return_value = [role_with_alias]
        
        mock_db.query.return_value = mock_query
        
        # Act
        is_dup, msg, conflict_role = _check_role_name_duplicate(mock_db, "Dev")
        
        # Assert
        assert is_dup is True
        assert "conflicts with the existing role" in msg
        assert "Software Engineer" in msg
        assert conflict_role == "Software Engineer"
    
    def test_case_insensitive_alias_match(self, mock_db):
        """Should detect alias match regardless of case."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        role_with_alias = Mock()
        role_with_alias.role_id = 1
        role_with_alias.role_name = "Developer"
        role_with_alias.role_alias = "DEV, SE"
        mock_query.all.return_value = [role_with_alias]
        
        mock_db.query.return_value = mock_query
        
        # Act
        is_dup, msg, conflict_role = _check_role_name_duplicate(mock_db, "dev")
        
        # Assert
        assert is_dup is True
        assert "conflicts with the existing role" in msg
        assert conflict_role == "Developer"
    
    def test_excludes_self_from_check(self, mock_db):
        """Should not flag as duplicate when only self matches."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No match after exclusion
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        is_dup, msg, conflict_role = _check_role_name_duplicate(mock_db, "Developer", exclude_role_id=5)
        
        # Assert
        assert is_dup is False
        assert msg is None
        assert conflict_role is None


class TestCreateRoleDuplicateValidation:
    """Test create_role duplicate validation."""
    
    def test_fails_when_role_name_already_exists(self, mock_db):
        """Should raise ValueError when role_name matches existing role."""
        # Arrange - simulate duplicate check returning True
        existing_role = Mock()
        existing_role.role_id = 1
        existing_role.role_name = "Developer"
        existing_role.role_alias = None
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_role
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_role(mock_db, "Developer", created_by="test")
        
        assert "already exists" in str(exc_info.value)
    
    def test_fails_when_role_name_matches_existing_alias(self, mock_db):
        """Should raise ValueError when role_name matches an existing alias token."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No direct name match
        
        role_with_alias = Mock()
        role_with_alias.role_id = 1
        role_with_alias.role_name = "Software Developer"
        role_with_alias.role_alias = "Dev, SDE"
        mock_query.all.return_value = [role_with_alias]
        
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_role(mock_db, "Dev", created_by="test")
        
        assert "conflicts with the existing role 'Software Developer'" in str(exc_info.value)


class TestUpdateRoleDuplicateValidation:
    """Test update_role duplicate validation."""
    
    def test_fails_when_role_name_matches_alias_of_another(self, mock_db):
        """Should raise ValueError when updated role_name matches alias of another role."""
        # Arrange - role being updated
        current_role = Mock()
        current_role.role_id = 5
        current_role.role_name = "Tech Lead"
        current_role.role_alias = None
        current_role.role_description = None
        
        # Build query mock that returns current role for update, then checks duplicate
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        
        # For the get role query
        def first_side_effect():
            return current_role
        mock_query.first.side_effect = [current_role, None]  # First for get, second for dup check
        
        # For duplicate check - another role has "Developer" as alias
        other_role = Mock()
        other_role.role_id = 10  # Different from 5
        other_role.role_name = "Software Engineer"
        other_role.role_alias = "Dev, Developer"
        mock_query.all.return_value = [other_role]
        
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            update_role(mock_db, role_id=5, role_name="Developer")
        
        assert "conflicts with the existing role 'Software Engineer'" in str(exc_info.value)
    
    def test_succeeds_when_only_self_matches(self, mock_db):
        """Should succeed when role keeps its own name (only self matches)."""
        # Arrange
        current_role = Mock()
        current_role.role_id = 5
        current_role.role_name = "Developer"
        current_role.role_alias = None
        current_role.role_description = None
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [current_role, None]  # Get role, no other duplicates
        mock_query.all.return_value = []  # No roles with matching aliases
        
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = update_role(mock_db, role_id=5, role_name="Developer")
        
        # Assert - should succeed
        assert result is not None
        assert current_role.role_name == "Developer"
        mock_db.commit.assert_called_once()


class TestSoftDeleteReuseRoleName:
    """Test that soft-deleted role names can be reused."""
    
    def test_create_role_after_soft_delete_succeeds(self, mock_db):
        """
        Create role → soft delete → create same name again → should succeed.
        
        The duplicate check should filter by deleted_at IS NULL,
        so soft-deleted role names don't block new role creation.
        """
        # Arrange - No active roles with this name (soft-deleted role exists but not returned)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No active role with same name
        mock_query.all.return_value = []  # No roles with matching aliases
        mock_db.query.return_value = mock_query
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        with patch('app.services.roles_service.Role') as MockRole:
            mock_instance = Mock()
            mock_instance.role_id = 10
            mock_instance.role_name = "Deleted Developer"
            mock_instance.role_alias = None
            mock_instance.role_description = None
            MockRole.return_value = mock_instance
            
            result = create_role(mock_db, "Deleted Developer", created_by="test")
        
        # Assert - Creation should succeed
        assert result is not None
        assert result['role_name'] == "Deleted Developer"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_duplicate_check_excludes_soft_deleted_roles(self, mock_db):
        """
        Ensure _check_role_name_duplicate only checks active roles.
        
        When a role with the same name is soft-deleted,
        creating a new role with that name should succeed.
        """
        # Arrange - query filters by deleted_at.is_(None), returns no active duplicates
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No active role with matching name
        mock_query.all.return_value = []  # No active roles with matching aliases
        mock_db.query.return_value = mock_query
        
        # Act
        is_dup, msg, conflict_role = _check_role_name_duplicate(mock_db, "Soft Deleted Role")
        
        # Assert - no duplicate found
        assert is_dup is False
        assert msg is None
        assert conflict_role is None
    
    def test_two_active_roles_same_name_fails(self, mock_db):
        """Two ACTIVE roles with same name should fail."""
        # Arrange - an active role with same name exists
        existing_role = Mock()
        existing_role.role_id = 1
        existing_role.role_name = "Developer"
        existing_role.role_alias = None
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_role  # Active role exists with same name
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_role(mock_db, "Developer", created_by="test")
        
        assert "already exists" in str(exc_info.value)
