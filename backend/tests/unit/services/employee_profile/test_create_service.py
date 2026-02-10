"""
Unit tests for employee_profile/create_service.py

Tests employee creation and update functionality.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from fastapi import HTTPException

from app.services.employee_profile import create_service


class TestValidateRoleId:
    """Test validate_role_id helper function."""
    
    def test_returns_role_when_valid_id(self, mock_db):
        """Should return Role object when role_id exists."""
        # Arrange
        existing_role = Mock()
        existing_role.role_id = 5
        existing_role.role_name = "Developer"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_role
        
        # Act
        result = create_service.validate_role_id(mock_db, 5)
        
        # Assert
        assert result == existing_role
        assert result.role_id == 5
    
    def test_raises_422_when_role_not_found(self, mock_db):
        """Should raise 422 when role_id doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_service.validate_role_id(mock_db, 999)
        
        assert exc_info.value.status_code == 422
        assert "Invalid role_id: 999" in exc_info.value.detail


class TestGetOrCreateRole:
    """Test get_or_create_role helper function."""
    
    def test_returns_none_for_empty_role_name(self, mock_db):
        """Should return None when role_name is empty or None."""
        assert create_service.get_or_create_role(mock_db, None) is None
        assert create_service.get_or_create_role(mock_db, "") is None
        assert create_service.get_or_create_role(mock_db, "   ") is None
    
    def test_returns_existing_role_id(self, mock_db):
        """Should return existing role_id when role exists."""
        # Arrange
        existing_role = Mock()
        existing_role.role_id = 42
        mock_db.query.return_value.filter.return_value.first.return_value = existing_role
        
        # Act
        result = create_service.get_or_create_role(mock_db, "Developer")
        
        # Assert
        assert result == 42
        mock_db.add.assert_not_called()
    
    def test_creates_new_role_when_not_exists(self, mock_db):
        """Should create new role and return its ID when doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        def flush_side_effect():
            # Simulate role getting an ID after flush
            pass
        mock_db.flush.side_effect = flush_side_effect
        
        # Act
        with patch('app.services.employee_profile.create_service.Role') as MockRole:
            mock_new_role = Mock()
            mock_new_role.role_id = 99
            MockRole.return_value = mock_new_role
            
            result = create_service.get_or_create_role(mock_db, "Manager")
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result == 99


class TestCreateEmployee:
    """Test create_employee function."""
    
    def test_creates_employee_with_valid_data(self, mock_db):
        """Should create employee and return it with all required fields."""
        # Arrange
        mock_team = Mock()
        mock_team.team_id = 1
        mock_role = Mock()
        mock_role.role_id = 5
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_team,  # Team lookup
            mock_role,  # Role lookup
            None       # ZID uniqueness check (no existing)
        ]
        
        with patch('app.services.employee_profile.create_service.Employee') as MockEmployee:
            
            mock_employee = Mock()
            mock_employee.employee_id = 100
            mock_employee.zid = "Z0123456"
            mock_employee.full_name = "Test User"
            mock_employee.team_id = 1
            mock_employee.role_id = 5
            MockEmployee.return_value = mock_employee
            
            # Act
            result = create_service.create_employee(
                mock_db,
                zid="Z0123456",
                full_name="Test User",
                team_id=1,
                role_id=5,
                email="test@example.com"
            )
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result.zid == "Z0123456"
        assert result.role_id == 5
    
    def test_raises_404_when_team_not_found(self, mock_db):
        """Should raise 404 when team_id is invalid."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_service.create_employee(
                mock_db,
                zid="Z0123456",
                full_name="Test User",
                team_id=999,
                role_id=1,
                email="test@example.com"
            )
        
        assert exc_info.value.status_code == 404
        assert "Team with ID 999 not found" in exc_info.value.detail
    
    def test_raises_422_when_role_id_invalid(self, mock_db):
        """Should raise 422 when role_id doesn't exist."""
        # Arrange
        mock_team = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_team,  # Team lookup (found)
            None       # Role lookup (not found)
        ]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_service.create_employee(
                mock_db,
                zid="Z0123456",
                full_name="Test User",
                team_id=1,
                role_id=999,
                email="test@example.com"
            )
        
        assert exc_info.value.status_code == 422
        assert "Invalid role_id: 999" in exc_info.value.detail
    
    def test_raises_409_when_zid_exists(self, mock_db):
        """Should raise 409 when ZID already exists."""
        # Arrange
        mock_team = Mock()
        mock_role = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_team,     # Team lookup (found)
            mock_role,     # Role lookup (found)
            Mock()         # ZID lookup (exists!)
        ]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_service.create_employee(
                mock_db,
                zid="Z9999999",
                full_name="Test User",
                team_id=1,
                role_id=1,
                email="test@example.com"
            )
        
        assert exc_info.value.status_code == 409
        assert "ZID 'Z9999999' already exists" in exc_info.value.detail
    
    def test_strips_whitespace_from_inputs(self, mock_db):
        """Should trim whitespace from zid, full_name, and email."""
        # Arrange
        mock_team = Mock()
        mock_role = Mock()
        mock_role.role_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_team, 
            mock_role, 
            None
        ]
        
        with patch('app.services.employee_profile.create_service.Employee') as MockEmployee:
            
            mock_employee = Mock()
            MockEmployee.return_value = mock_employee
            
            # Act
            create_service.create_employee(
                mock_db,
                zid="  Z0123456  ",
                full_name="  Test User  ",
                team_id=1,
                role_id=1,
                email="  test@example.com  "
            )
        
        # Assert - check call args
        call_kwargs = MockEmployee.call_args.kwargs
        assert call_kwargs['zid'] == "Z0123456"
        assert call_kwargs['full_name'] == "Test User"
        assert call_kwargs['email'] == "test@example.com"
    
    def test_creates_with_required_role_id(self, mock_db):
        """Should use validated role_id from roles table."""
        # Arrange
        mock_team = Mock()
        mock_role = Mock()
        mock_role.role_id = 7
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_team, 
            mock_role, 
            None
        ]
        
        with patch('app.services.employee_profile.create_service.Employee') as MockEmployee:
            mock_employee = Mock()
            MockEmployee.return_value = mock_employee
            
            # Act
            create_service.create_employee(
                mock_db,
                zid="Z0123456",
                full_name="Test User",
                team_id=1,
                role_id=7,
                email="test@example.com"
            )
        
        # Assert - check role_id is passed to Employee constructor
        call_kwargs = MockEmployee.call_args.kwargs
        assert call_kwargs['role_id'] == 7
    
    def test_does_not_include_skills(self, mock_db):
        """Should NOT include any skills in created employee - per requirements."""
        # Arrange
        mock_team = Mock()
        mock_role = Mock()
        mock_role.role_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_team, 
            mock_role, 
            None
        ]
        
        with patch('app.services.employee_profile.create_service.Employee') as MockEmployee:
            
            MockEmployee.return_value = Mock()
            
            # Act
            create_service.create_employee(
                mock_db,
                zid="Z0123456",
                full_name="Test User",
                team_id=1,
                role_id=1,
                email="test@example.com"
            )
        
        # Assert - verify Employee constructor was NOT called with employee_skills
        call_kwargs = MockEmployee.call_args.kwargs
        assert 'employee_skills' not in call_kwargs
        assert 'skills' not in call_kwargs


class TestUpdateEmployee:
    """Test update_employee function."""
    
    def test_updates_employee_with_partial_data(self, mock_db):
        """Should update only provided fields."""
        # Arrange
        existing_employee = Mock()
        existing_employee.employee_id = 100
        existing_employee.full_name = "Old Name"
        existing_employee.email = "old@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_employee
        
        with patch.object(create_service, 'get_or_create_role', return_value=None):
            # Act
            result = create_service.update_employee(
                mock_db,
                employee_id=100,
                full_name="New Name"
            )
        
        # Assert
        assert result.full_name == "New Name"
        mock_db.commit.assert_called_once()
    
    def test_raises_404_when_employee_not_found(self, mock_db):
        """Should raise 404 when employee_id doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_service.update_employee(
                mock_db,
                employee_id=999,
                full_name="New Name"
            )
        
        assert exc_info.value.status_code == 404
        assert "Employee with ID 999 not found" in exc_info.value.detail
    
    def test_validates_team_when_provided(self, mock_db):
        """Should validate team_id exists when updating team."""
        # Arrange
        existing_employee = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            existing_employee,  # Employee lookup
            None               # Team lookup (not found)
        ]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_service.update_employee(
                mock_db,
                employee_id=100,
                team_id=999
            )
        
        assert exc_info.value.status_code == 404
        assert "Team" in exc_info.value.detail
