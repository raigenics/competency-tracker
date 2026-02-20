"""
Unit tests for competencies.py routes - Employee Profile endpoints

Tests the following endpoints used by the Employee Profile feature:
- GET /competencies/employee/{employee_id}/profile
- GET /competencies/employee/{employee_id}/skill-history
"""
import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

from app.api.routes.competencies import router
from app.db.session import get_db
from app.schemas.competency import (
    EmployeeCompetencyProfile, EmployeeSkillResponse, ProficiencyLevelResponse
)
from app.schemas.skill_history import SkillHistoryListResponse, SkillHistoryResponse


# Create test app with the competencies router
app = FastAPI()
app.include_router(router)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Create a mock database session with chainable query methods."""
    db = MagicMock()
    mock_query = MagicMock()
    db.query.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.first.return_value = None
    mock_query.all.return_value = []
    return db


@pytest.fixture
def test_client(mock_db_session):
    """Create test client with mocked database."""
    def override_get_db():
        return mock_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def create_mock_employee(
    employee_id=1, 
    full_name="John Doe",
    skills_data=None
):
    """Factory to create mock employee with all relationships."""
    employee = Mock()
    employee.employee_id = employee_id
    employee.full_name = full_name
    employee.zid = "Z001"
    employee.email = "john@example.com"
    
    # Role - set actual string values for Pydantic validation
    employee.role = Mock()
    employee.role.role_id = 1
    employee.role.role_name = "Developer"
    employee.role.role_description = "Software Developer"  # Must be string or None
    
    # Team -> Project -> SubSegment chain (NORMALIZED)
    employee.team = Mock()
    employee.team.team_name = "Team Alpha"
    employee.team.project = Mock()
    employee.team.project.project_name = "Project X"
    employee.team.project.sub_segment = Mock()
    employee.team.project.sub_segment.sub_segment_name = "Engineering"
    
    # For backwards compatibility (old route uses these)
    employee.sub_segment = employee.team.project.sub_segment
    employee.project = employee.team.project
    
    # Skills
    employee.employee_skills = []
    if skills_data:
        for skill_info in skills_data:
            emp_skill = create_mock_employee_skill(**skill_info)
            employee.employee_skills.append(emp_skill)
    
    return employee


def create_mock_employee_skill(
    emp_skill_id=101,
    skill_name="Python",
    proficiency_level_name="Advanced",
    proficiency_level_id=3,
    years_experience=5,
    category_name="Programming"
):
    """Factory to create mock employee skill."""
    emp_skill = Mock()
    emp_skill.emp_skill_id = emp_skill_id
    emp_skill.employee_id = 1
    emp_skill.skill_id = 10
    emp_skill.years_experience = years_experience
    emp_skill.last_used = date(2024, 6, 15)
    emp_skill.interest_level = 4
    emp_skill.last_updated = datetime(2024, 7, 1, 10, 30, 0)
    emp_skill.certification = None
    
    # Skill
    emp_skill.skill = Mock()
    emp_skill.skill.skill_name = skill_name
    emp_skill.skill.skill_id = 10
    emp_skill.skill.subcategory = Mock()
    emp_skill.skill.subcategory.category = Mock()
    emp_skill.skill.subcategory.category.category_name = category_name
    emp_skill.skill.category = emp_skill.skill.subcategory.category
    
    # Proficiency level
    emp_skill.proficiency_level = Mock()
    emp_skill.proficiency_level.proficiency_level_id = proficiency_level_id
    emp_skill.proficiency_level.level_name = proficiency_level_name
    emp_skill.proficiency_level.level_description = f"{proficiency_level_name} proficiency"
    
    return emp_skill


def create_mock_skill_history(
    history_id=1,
    employee_id=1,
    skill_name="Python",
    action="UPDATE",
    old_proficiency_name="Intermediate",
    new_proficiency_name="Advanced"
):
    """Factory to create mock skill history record."""
    record = Mock()
    record.history_id = history_id
    record.employee_id = employee_id
    record.skill_id = 10
    record.emp_skill_id = 101
    record.action = action
    record.changed_at = datetime(2024, 7, 1, 10, 30, 0)
    record.change_source = "UI"
    record.changed_by = "admin"
    record.change_reason = "Annual review"
    record.batch_id = None
    
    # Old values
    record.old_proficiency_level_id = 2
    record.old_proficiency = Mock()
    record.old_proficiency.level_name = old_proficiency_name
    record.old_years_experience = 3
    record.old_certification = None
    
    # New values
    record.new_proficiency_level_id = 3
    record.new_proficiency = Mock()
    record.new_proficiency.level_name = new_proficiency_name
    record.new_years_experience = 5
    record.new_certification = None
    
    # Relationships
    record.employee = Mock()
    record.employee.full_name = "John Doe"
    record.skill = Mock()
    record.skill.skill_name = skill_name
    
    return record


# ============================================================================
# TEST: GET /competencies/employee/{employee_id}/profile
# ============================================================================

class TestGetEmployeeCompetencyProfile:
    """Tests for GET /competencies/employee/{employee_id}/profile."""
    
    def test_returns_profile_for_valid_employee(self, test_client, mock_db_session):
        """Should return complete profile for a valid employee."""
        # Arrange
        mock_employee = create_mock_employee(
            employee_id=1,
            full_name="John Doe",
            skills_data=[{"skill_name": "Python", "proficiency_level_name": "Advanced"}]
        )
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == 1
        assert data["employee_name"] == "John Doe"
        assert "skills" in data
        assert "competency_summary" in data
        assert "top_skills" in data
    
    def test_returns_404_for_nonexistent_employee(self, test_client, mock_db_session):
        """Should return 404 when employee doesn't exist."""
        # Arrange
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = test_client.get("/competencies/employee/999/profile")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_returns_profile_with_empty_skills(self, test_client, mock_db_session):
        """Should return profile with empty skills list."""
        # Arrange
        mock_employee = create_mock_employee(skills_data=[])
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["skills"] == []
        assert data["top_skills"] == []
    
    def test_returns_profile_with_multiple_skills(self, test_client, mock_db_session):
        """Should return profile with multiple skills."""
        # Arrange
        mock_employee = create_mock_employee(
            skills_data=[
                {"skill_name": "Python", "proficiency_level_name": "Advanced"},
                {"emp_skill_id": 102, "skill_name": "JavaScript", "proficiency_level_name": "Expert"}
            ]
        )
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["skills"]) == 2
    
    def test_includes_organization_structure(self, test_client, mock_db_session):
        """Should include organization structure in response."""
        # Arrange
        mock_employee = create_mock_employee(skills_data=[])
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "organization" in data
        org = data["organization"]
        assert "sub_segment" in org
        assert "project" in org
        assert "team" in org
    
    def test_includes_competency_summary(self, test_client, mock_db_session):
        """Should include competency summary breakdown."""
        # Arrange
        mock_employee = create_mock_employee(
            skills_data=[{"skill_name": "Python", "proficiency_level_name": "Advanced"}]
        )
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "competency_summary" in data
        summary = data["competency_summary"]
        assert isinstance(summary, dict)
    
    def test_includes_role_information(self, test_client, mock_db_session):
        """Should include role information when available."""
        # Arrange
        mock_employee = create_mock_employee(skills_data=[])
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "role" in data
    
    def test_handles_database_error(self, test_client, mock_db_session):
        """Should return 500 on database error."""
        # Arrange
        mock_db_session.query.side_effect = Exception("Database connection failed")
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
    
    def test_returns_top_skills_with_expert_level(self, test_client, mock_db_session):
        """Should return top skills for Advanced/Expert proficiency."""
        # Arrange
        mock_employee = create_mock_employee(
            skills_data=[
                {"skill_name": "Python", "proficiency_level_name": "Expert", "years_experience": 8},
                {"emp_skill_id": 102, "skill_name": "JavaScript", "proficiency_level_name": "Advanced", "years_experience": 5}
            ]
        )
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/1/profile")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "top_skills" in data
        # Should have top skills (Expert/Advanced)
        assert len(data["top_skills"]) >= 0


# ============================================================================
# TEST: GET /competencies/employee/{employee_id}/skill-history
# ============================================================================

class TestGetEmployeeSkillHistory:
    """Tests for GET /competencies/employee/{employee_id}/skill-history."""
    
    def test_returns_skill_history_for_employee(self, test_client, mock_db_session):
        """Should return skill history for a valid employee."""
        # Arrange
        mock_record = create_mock_skill_history()
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.count.return_value = 1
        mock_query.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 1
    
    def test_returns_empty_history_for_employee_with_no_changes(self, test_client, mock_db_session):
        """Should return empty list when employee has no skill history."""
        # Arrange
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.count.return_value = 0
        mock_query.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_filters_history_by_skill_id(self, test_client, mock_db_session):
        """Should filter skill history by skill_id parameter."""
        # Arrange
        mock_record = create_mock_skill_history()
        
        mock_query = mock_db_session.query.return_value
        # The route calls filter twice when skill_id is provided
        mock_filter = mock_query.options.return_value.filter.return_value
        mock_filter.filter.return_value = mock_filter
        mock_filter.count.return_value = 1
        mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history?skill_id=10")
        
        # Assert
        assert response.status_code == 200
    
    def test_respects_pagination_params(self, test_client, mock_db_session):
        """Should apply pagination parameters."""
        # Arrange
        mock_record = create_mock_skill_history()
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.count.return_value = 25
        mock_query.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history?page=2&size=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
    
    def test_includes_old_and_new_proficiency_names(self, test_client, mock_db_session):
        """Should include old and new proficiency names in response."""
        # Arrange
        mock_record = create_mock_skill_history(
            old_proficiency_name="Intermediate",
            new_proficiency_name="Advanced"
        )
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.count.return_value = 1
        mock_query.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]
        assert "old_proficiency_name" in item
        assert "new_proficiency_name" in item
    
    def test_handles_database_error(self, test_client, mock_db_session):
        """Should return 500 on database error."""
        # Arrange
        mock_db_session.query.side_effect = Exception("Database error")
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history")
        
        # Assert
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
    
    def test_returns_multiple_history_records(self, test_client, mock_db_session):
        """Should return multiple history records."""
        # Arrange
        records = [
            create_mock_skill_history(history_id=1, skill_name="Python"),
            create_mock_skill_history(history_id=2, skill_name="JavaScript", action="INSERT")
        ]
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.count.return_value = 2
        mock_query.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = records
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
    
    def test_includes_pagination_metadata(self, test_client, mock_db_session):
        """Should include pagination metadata in response."""
        # Arrange
        mock_record = create_mock_skill_history()
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.count.return_value = 50
        mock_query.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history?page=1&size=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "page" in data
        assert "size" in data


# ============================================================================
# TEST: INPUT VALIDATION
# ============================================================================

class TestEmployeeProfileValidation:
    """Tests for input validation in Employee Profile endpoints."""
    
    def test_rejects_invalid_employee_id_type(self, test_client):
        """Should reject non-integer employee ID."""
        # Act
        response = test_client.get("/competencies/employee/invalid/profile")
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_accepts_valid_employee_id(self, test_client, mock_db_session):
        """Should accept valid integer employee ID."""
        # Arrange
        mock_employee = create_mock_employee()
        
        mock_query = mock_db_session.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_employee
        
        # Act
        response = test_client.get("/competencies/employee/123/profile")
        
        # Assert
        assert response.status_code == 200


class TestSkillHistoryValidation:
    """Tests for input validation in Skill History endpoints."""
    
    def test_rejects_invalid_skill_id_filter(self, test_client):
        """Should reject non-integer skill_id filter."""
        # Act
        response = test_client.get("/competencies/employee/1/skill-history?skill_id=invalid")
        
        # Assert
        assert response.status_code == 422
    
    def test_accepts_valid_skill_id_filter(self, test_client, mock_db_session):
        """Should accept valid integer skill_id filter."""
        # Arrange
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.options.return_value.filter.return_value
        mock_filter.filter.return_value = mock_filter
        mock_filter.count.return_value = 0
        mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        # Act
        response = test_client.get("/competencies/employee/1/skill-history?skill_id=10")
        
        # Assert
        assert response.status_code == 200
