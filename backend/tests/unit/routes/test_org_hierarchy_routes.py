"""
Unit tests for Organization Hierarchy API routes (/org-hierarchy/*).

Tests segment, sub-segment, project and team creation with duplicate name handling:
- POST /org-hierarchy/segments - Create segment (duplicate returns 409 with message)
- POST /org-hierarchy/sub-segments - Create sub-segment (duplicate returns 409 with message)
- POST /org-hierarchy/projects - Create project (duplicate returns 409 with message)
- POST /org-hierarchy/teams - Create team (duplicate returns 409 with message)
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.org_hierarchy import router


# Create test app with router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


# ============================================================================
# POST /org-hierarchy/segments TESTS
# ============================================================================

class TestCreateSegment:
    """Tests for POST /org-hierarchy/segments endpoint."""

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_segment")
    def test_create_segment_success(self, mock_create_segment, mock_get_db, mock_db):
        """Test successful segment creation."""
        mock_get_db.return_value = iter([mock_db])
        mock_create_segment.return_value = MagicMock(
            segment_id=1,
            segment_name="Engineering",
            created_at="2024-01-15T10:00:00",
            created_by="system",
            message="Segment created successfully"
        )

        response = client.post(
            "/org-hierarchy/segments",
            json={"name": "Engineering"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["segment_id"] == 1
        assert data["segment_name"] == "Engineering"
        assert data["message"] == "Segment created successfully"

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_segment")
    def test_create_segment_duplicate_returns_409_with_message(
        self, mock_create_segment, mock_get_db, mock_db
    ):
        """
        Test that creating a segment with an existing name returns HTTP 409
        with a user-friendly error message in the 'detail' field.
        """
        mock_get_db.return_value = iter([mock_db])
        # Service raises ValueError for duplicate
        mock_create_segment.side_effect = ValueError(
            "Segment with name 'Engineering' already exists"
        )

        response = client.post(
            "/org-hierarchy/segments",
            json={"name": "Engineering"}
        )

        # Verify 409 Conflict status
        assert response.status_code == 409
        
        # Verify error message is user-friendly
        data = response.json()
        assert "detail" in data
        assert "Engineering" in data["detail"]
        assert "already exists" in data["detail"]
        # Ensure it's NOT the raw HTTP error message
        assert "HTTP error" not in data["detail"]

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_segment")
    def test_create_segment_empty_name_returns_422(
        self, mock_create_segment, mock_get_db, mock_db
    ):
        """Test that empty segment name returns HTTP 422 (Pydantic validation)."""
        mock_get_db.return_value = iter([mock_db])

        response = client.post(
            "/org-hierarchy/segments",
            json={"name": ""}
        )

        # Pydantic validates min_length before service is called
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ============================================================================
# POST /org-hierarchy/sub-segments TESTS
# ============================================================================

class TestCreateSubSegment:
    """Tests for POST /org-hierarchy/sub-segments endpoint."""

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_sub_segment")
    def test_create_sub_segment_success(self, mock_create_sub_segment, mock_get_db, mock_db):
        """Test successful sub-segment creation."""
        mock_get_db.return_value = iter([mock_db])
        mock_create_sub_segment.return_value = MagicMock(
            sub_segment_id=1,
            sub_segment_name="ADT",
            segment_id=1,
            created_at="2024-01-15T10:00:00",
            created_by="system",
            message="Sub-segment created successfully"
        )

        response = client.post(
            "/org-hierarchy/sub-segments",
            json={"segment_id": 1, "name": "ADT"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["sub_segment_id"] == 1
        assert data["sub_segment_name"] == "ADT"
        assert data["message"] == "Sub-segment created successfully"

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_sub_segment")
    def test_create_sub_segment_duplicate_returns_409_with_friendly_message(
        self, mock_create_sub_segment, mock_get_db, mock_db
    ):
        """
        Test that creating a sub-segment with an existing name returns HTTP 409
        with a user-friendly error message including segment name.
        """
        mock_get_db.return_value = iter([mock_db])
        # Service raises ValueError for duplicate with new message format
        mock_create_sub_segment.side_effect = ValueError(
            "'ADT' sub-segment already exists in Segment 'DTS'."
        )

        response = client.post(
            "/org-hierarchy/sub-segments",
            json={"segment_id": 1, "name": "ADT"}
        )

        # Verify 409 Conflict status
        assert response.status_code == 409
        
        # Verify error message is user-friendly and includes both names
        data = response.json()
        assert "detail" in data
        assert "ADT" in data["detail"]
        assert "already exists" in data["detail"]
        assert "Segment" in data["detail"]
        # Ensure it's NOT the raw HTTP error message
        assert "HTTP error" not in data["detail"]

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_sub_segment")
    def test_create_sub_segment_parent_not_found_returns_404(
        self, mock_create_sub_segment, mock_get_db, mock_db
    ):
        """Test that non-existent parent segment returns HTTP 404."""
        mock_get_db.return_value = iter([mock_db])
        mock_create_sub_segment.side_effect = ValueError(
            "Parent segment with id 999 not found"
        )

        response = client.post(
            "/org-hierarchy/sub-segments",
            json={"segment_id": 999, "name": "TestSubSegment"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]


# ============================================================================
# POST /org-hierarchy/projects TESTS
# ============================================================================

class TestCreateProject:
    """Tests for POST /org-hierarchy/projects endpoint."""

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_project")
    def test_create_project_success(self, mock_create_project, mock_get_db, mock_db):
        """Test successful project creation."""
        mock_get_db.return_value = iter([mock_db])
        mock_create_project.return_value = MagicMock(
            project_id=1,
            project_name="MyProject",
            sub_segment_id=1,
            created_at="2024-01-15T10:00:00",
            created_by="system",
            message="Project created successfully"
        )

        response = client.post(
            "/org-hierarchy/projects",
            json={"sub_segment_id": 1, "name": "MyProject"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == 1
        assert data["project_name"] == "MyProject"
        assert data["message"] == "Project created successfully"

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_project")
    def test_create_project_duplicate_returns_409_with_friendly_message(
        self, mock_create_project, mock_get_db, mock_db
    ):
        """
        Test that creating a project with an existing name returns HTTP 409
        with a user-friendly error message including sub-segment name.
        """
        mock_get_db.return_value = iter([mock_db])
        # Service raises ValueError for duplicate with new message format
        mock_create_project.side_effect = ValueError(
            "'MyProject' project already exists in Sub-segment 'ADT'."
        )

        response = client.post(
            "/org-hierarchy/projects",
            json={"sub_segment_id": 1, "name": "MyProject"}
        )

        # Verify 409 Conflict status
        assert response.status_code == 409
        
        # Verify error message is user-friendly and includes both names
        data = response.json()
        assert "detail" in data
        assert "MyProject" in data["detail"]
        assert "already exists" in data["detail"]
        assert "Sub-segment" in data["detail"]
        # Ensure it's NOT the raw HTTP error message
        assert "HTTP error" not in data["detail"]

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_project")
    def test_create_project_parent_not_found_returns_404(
        self, mock_create_project, mock_get_db, mock_db
    ):
        """Test that non-existent parent sub-segment returns HTTP 404."""
        mock_get_db.return_value = iter([mock_db])
        mock_create_project.side_effect = ValueError(
            "Parent sub-segment with id 999 not found"
        )

        response = client.post(
            "/org-hierarchy/projects",
            json={"sub_segment_id": 999, "name": "TestProject"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]


# ============================================================================
# POST /org-hierarchy/teams TESTS
# ============================================================================

class TestCreateTeam:
    """Tests for POST /org-hierarchy/teams endpoint."""

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_team")
    def test_create_team_success(self, mock_create_team, mock_get_db, mock_db):
        """Test successful team creation."""
        mock_get_db.return_value = iter([mock_db])
        mock_create_team.return_value = MagicMock(
            team_id=1,
            team_name="MyTeam",
            project_id=1,
            created_at="2024-01-15T10:00:00",
            created_by="system",
            message="Team created successfully"
        )

        response = client.post(
            "/org-hierarchy/teams",
            json={"project_id": 1, "name": "MyTeam"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["team_id"] == 1
        assert data["team_name"] == "MyTeam"
        assert data["message"] == "Team created successfully"

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_team")
    def test_create_team_duplicate_returns_409_with_friendly_message(
        self, mock_create_team, mock_get_db, mock_db
    ):
        """
        Test that creating a team with an existing name returns HTTP 409
        with a user-friendly error message including project name.
        """
        mock_get_db.return_value = iter([mock_db])
        # Service raises ValueError for duplicate with new message format
        mock_create_team.side_effect = ValueError(
            "'MyTeam' team already exists in Project 'MyProject'."
        )

        response = client.post(
            "/org-hierarchy/teams",
            json={"project_id": 1, "name": "MyTeam"}
        )

        # Verify 409 Conflict status
        assert response.status_code == 409
        
        # Verify error message is user-friendly and includes both names
        data = response.json()
        assert "detail" in data
        assert "MyTeam" in data["detail"]
        assert "already exists" in data["detail"]
        assert "Project" in data["detail"]
        # Ensure it's NOT the raw HTTP error message
        assert "HTTP error" not in data["detail"]

    @patch("app.api.routes.org_hierarchy.get_db")
    @patch("app.api.routes.org_hierarchy.create_team")
    def test_create_team_parent_not_found_returns_404(
        self, mock_create_team, mock_get_db, mock_db
    ):
        """Test that non-existent parent project returns HTTP 404."""
        mock_get_db.return_value = iter([mock_db])
        mock_create_team.side_effect = ValueError(
            "Parent project with id 999 not found"
        )

        response = client.post(
            "/org-hierarchy/teams",
            json={"project_id": 999, "name": "TestTeam"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
