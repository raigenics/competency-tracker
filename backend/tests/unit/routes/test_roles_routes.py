"""
Unit tests for Roles API routes (/roles/*).

Tests:
- GET /roles/ - returns list of roles with role_description
- GET /roles/{id} - returns single role with role_description
- POST /roles/ - create role, handles duplicates and IntegrityError
- PUT /roles/{id} - update role, handles duplicates and IntegrityError
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from app.api.routes.roles import router


# Create test app with router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestGetRolesEndpoint:
    """Test GET /roles/ endpoint."""
    
    def test_returns_roles_with_description(self):
        """GET /roles/ should return role_description field for each role."""
        # Arrange
        mock_roles = [
            {"role_id": 1, "role_name": "Developer", "role_description": "Software developer role"},
            {"role_id": 2, "role_name": "Manager", "role_description": "Team manager role"},
            {"role_id": 3, "role_name": "Architect", "role_description": None}
        ]
        
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.get_all_roles.return_value = mock_roles
            
            # Act
            response = client.get("/roles/")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            
            # Verify role_description is present in response
            assert data[0]["role_id"] == 1
            assert data[0]["role_name"] == "Developer"
            assert data[0]["role_description"] == "Software developer role"
            
            assert data[1]["role_id"] == 2
            assert data[1]["role_name"] == "Manager"
            assert data[1]["role_description"] == "Team manager role"
            
            # Null description should still be in response
            assert data[2]["role_id"] == 3
            assert data[2]["role_name"] == "Architect"
            assert data[2]["role_description"] is None
    
    def test_returns_empty_list_when_no_roles(self):
        """GET /roles/ should return empty list when no roles exist."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.get_all_roles.return_value = []
            
            response = client.get("/roles/")
            
            assert response.status_code == 200
            assert response.json() == []


class TestGetRoleByIdEndpoint:
    """Test GET /roles/{id} endpoint."""
    
    def test_returns_role_with_description(self):
        """GET /roles/{id} should return role_description field."""
        mock_role = {"role_id": 5, "role_name": "Tech Lead", "role_description": "Technical leadership role"}
        
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.get_role_by_id.return_value = mock_role
            
            response = client.get("/roles/5")
            
            assert response.status_code == 200
            data = response.json()
            assert data["role_id"] == 5
            assert data["role_name"] == "Tech Lead"
            assert data["role_description"] == "Technical leadership role"
    
    def test_returns_404_when_not_found(self):
        """GET /roles/{id} should return 404 when role doesn't exist."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.get_role_by_id.return_value = None
            
            response = client.get("/roles/999")
            
            assert response.status_code == 404


class TestCreateRoleEndpoint:
    """Test POST /roles/ endpoint."""
    
    def test_create_role_success(self):
        """POST /roles/ should create role and return 201."""
        mock_role = {
            "role_id": 1,
            "role_name": "Developer",
            "role_alias": "Dev",
            "role_description": "Software developer"
        }
        
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.create_role.return_value = mock_role
            
            response = client.post("/roles/", json={
                "role_name": "Developer",
                "role_alias": "Dev",
                "role_description": "Software developer"
            })
            
            assert response.status_code == 201
            data = response.json()
            assert data["role_id"] == 1
            assert data["role_name"] == "Developer"
    
    def test_create_role_duplicate_returns_409_not_500(self):
        """POST /roles/ with duplicate name should return 409 (not 500)."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.create_role.side_effect = ValueError("Role 'Developer' already exists")
            
            response = client.post("/roles/", json={
                "role_name": "Developer",
                "role_alias": None,
                "role_description": None
            })
            
            assert response.status_code == 409
            data = response.json()
            assert "already exists" in data["detail"]
            # Should NOT have stack trace or SQL
            assert "psycopg" not in data["detail"].lower()
            assert "integrity" not in data["detail"].lower()
    
    def test_create_role_integrity_error_returns_409(self):
        """POST /roles/ with DB IntegrityError should return 409 (not 500)."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            # Simulate race condition where pre-check passes but DB constraint fails
            mock_service.create_role.side_effect = IntegrityError(
                "INSERT INTO roles ...",
                {},
                Exception("UniqueViolation: duplicate key value violates unique constraint")
            )
            
            response = client.post("/roles/", json={
                "role_name": "Developer",
                "role_alias": None,
                "role_description": None
            })
            
            assert response.status_code == 409
            data = response.json()
            assert "already exists" in data["detail"]
            # Should NOT have stack trace or SQL
            assert "psycopg" not in data["detail"].lower()
            assert "INSERT INTO" not in data["detail"]
            assert "UniqueViolation" not in data["detail"]
    
    def test_create_role_conflicts_with_alias_returns_409(self):
        """POST /roles/ with name matching existing alias should return 409."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.create_role.side_effect = ValueError("'Dev' conflicts with the existing role 'Developer'")
            
            response = client.post("/roles/", json={
                "role_name": "Dev",
                "role_alias": None,
                "role_description": None
            })
            
            assert response.status_code == 409
            data = response.json()
            assert "conflicts with" in data["detail"]


class TestUpdateRoleEndpoint:
    """Test PUT /roles/{id} endpoint."""
    
    def test_update_role_success(self):
        """PUT /roles/{id} should update role and return 200."""
        mock_role = {
            "role_id": 1,
            "role_name": "Senior Developer",
            "role_alias": "Sr. Dev",
            "role_description": "Senior software developer"
        }
        
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.update_role.return_value = mock_role
            
            response = client.put("/roles/1", json={
                "role_name": "Senior Developer",
                "role_alias": "Sr. Dev",
                "role_description": "Senior software developer"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["role_name"] == "Senior Developer"
    
    def test_update_role_duplicate_returns_409(self):
        """PUT /roles/{id} with duplicate name should return 409."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.update_role.side_effect = ValueError("Role 'Developer' already exists")
            
            response = client.put("/roles/1", json={
                "role_name": "Developer",
                "role_alias": None,
                "role_description": None
            })
            
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"]
    
    def test_update_role_integrity_error_returns_409(self):
        """PUT /roles/{id} with DB IntegrityError should return 409 (not 500)."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.update_role.side_effect = IntegrityError(
                "UPDATE roles ...",
                {},
                Exception("UniqueViolation")
            )
            
            response = client.put("/roles/1", json={
                "role_name": "Developer",
                "role_alias": None,
                "role_description": None
            })
            
            assert response.status_code == 409
            data = response.json()
            assert "already exists" in data["detail"]
            # Should NOT leak DB details
            assert "UPDATE" not in data["detail"]
            assert "UniqueViolation" not in data["detail"]
    
    def test_update_role_not_found_returns_404(self):
        """PUT /roles/{id} with non-existent role returns 404."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.update_role.return_value = None
            
            response = client.put("/roles/999", json={
                "role_name": "New Name",
                "role_alias": None,
                "role_description": None
            })
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    def test_update_role_conflicts_with_alias_returns_409(self):
        """PUT /roles/{id} with name matching another role's alias returns 409."""
        with patch("app.api.routes.roles.roles_service") as mock_service:
            mock_service.update_role.side_effect = ValueError("'Dev' conflicts with the existing role 'Developer'")
            
            response = client.put("/roles/1", json={
                "role_name": "Dev",
                "role_alias": None,
                "role_description": None
            })
            
            assert response.status_code == 409
            data = response.json()
            assert "conflicts with" in data["detail"]
