"""
Unit tests for MasterDataValidator.

Target: backend/app/services/imports/employee_import/master_data_validator.py
Coverage: Master data validation for employee bulk import.

Test Strategy:
- Validate SubSegment, Project, Team, Role existence
- Validate hierarchy relationships (Project under SubSegment, Team under Project)
- Test error codes and messages
- Test caching behavior
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.services.imports.employee_import.master_data_validator import (
    MasterDataValidator,
    MasterDataValidationResult
)
from app.models import SubSegment, Project, Team, Role


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock()
    db.query.return_value = db
    db.filter.return_value = db
    db.first.return_value = None
    return db


@pytest.fixture
def validator(mock_db):
    """Create MasterDataValidator instance."""
    return MasterDataValidator(mock_db)


@pytest.fixture
def mock_sub_segment():
    """Create mock SubSegment."""
    sub_segment = MagicMock(spec=SubSegment)
    sub_segment.sub_segment_id = 1
    sub_segment.sub_segment_name = "Test SubSegment"
    return sub_segment


@pytest.fixture
def mock_project():
    """Create mock Project."""
    project = MagicMock(spec=Project)
    project.project_id = 10
    project.project_name = "Test Project"
    project.sub_segment_id = 1
    return project


@pytest.fixture
def mock_team():
    """Create mock Team."""
    team = MagicMock(spec=Team)
    team.team_id = 100
    team.team_name = "Test Team"
    team.project_id = 10
    return team


@pytest.fixture
def mock_role():
    """Create mock Role."""
    role = MagicMock(spec=Role)
    role.role_id = 500
    role.role_name = "Engineer"
    return role


# ============================================================================
# TEST: validate_row - SubSegment validation
# ============================================================================

class TestValidateRowSubSegment:
    """Test SubSegment validation."""
    
    def test_fails_when_sub_segment_not_found(self, mock_db, validator):
        """Should return MISSING_SUB_SEGMENT error when SubSegment doesn't exist."""
        # Arrange - DB returns None for SubSegment query
        mock_db.first.return_value = None
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Nonexistent SubSeg",
            project_name="Some Project",
            team_name="Some Team"
        )
        
        # Assert
        assert result.is_valid is False
        assert result.error_code == "MISSING_SUB_SEGMENT"
        assert "Sub-Segment 'Nonexistent SubSeg' not found" in result.error_message
    
    def test_normalizes_sub_segment_name(self, mock_db, validator, mock_sub_segment):
        """Should normalize SubSegment name (trim whitespace)."""
        # Arrange
        mock_db.first.side_effect = [mock_sub_segment, None]  # Sub found, Project not
        
        # Act
        result = validator.validate_row(
            sub_segment_name="  Test SubSegment  ",  # Extra whitespace
            project_name="Some Project",
            team_name="Some Team"
        )
        
        # Assert - validation moved past SubSegment to Project
        assert result.error_code == "MISSING_PROJECT"


# ============================================================================
# TEST: validate_row - Project validation
# ============================================================================

class TestValidateRowProject:
    """Test Project validation."""
    
    def test_fails_when_project_not_found(self, mock_db, validator, mock_sub_segment):
        """Should return MISSING_PROJECT error when Project doesn't exist."""
        # Arrange - SubSegment exists, Project doesn't
        mock_db.first.side_effect = [mock_sub_segment, None]
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Nonexistent Project",
            team_name="Some Team"
        )
        
        # Assert
        assert result.is_valid is False
        assert result.error_code == "MISSING_PROJECT"
        assert "Project 'Nonexistent Project' not found" in result.error_message
        assert "under Sub-Segment 'Test SubSegment'" in result.error_message
    
    def test_fails_when_project_under_wrong_sub_segment(self, mock_db, validator, mock_sub_segment):
        """Should fail if Project exists but not under the correct SubSegment."""
        # Arrange - SubSegment exists, but project query returns None 
        # (simulating project not being under that sub_segment)
        mock_db.first.side_effect = [mock_sub_segment, None]
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Project Under Different SubSeg",
            team_name="Some Team"
        )
        
        # Assert
        assert result.is_valid is False
        assert result.error_code == "MISSING_PROJECT"


# ============================================================================
# TEST: validate_row - Team validation
# ============================================================================

class TestValidateRowTeam:
    """Test Team validation."""
    
    def test_fails_when_team_not_found(self, mock_db, validator, mock_sub_segment, mock_project):
        """Should return MISSING_TEAM error when Team doesn't exist."""
        # Arrange - SubSegment and Project exist, Team doesn't
        mock_db.first.side_effect = [mock_sub_segment, mock_project, None]
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Nonexistent Team"
        )
        
        # Assert
        assert result.is_valid is False
        assert result.error_code == "MISSING_TEAM"
        assert "Team 'Nonexistent Team' not found" in result.error_message
        assert "under Project 'Test Project'" in result.error_message
    
    def test_fails_when_team_under_wrong_project(self, mock_db, validator, mock_sub_segment, mock_project):
        """Should fail if Team exists but not under the correct Project."""
        # Arrange - All parent entities exist, but team query returns None
        mock_db.first.side_effect = [mock_sub_segment, mock_project, None]
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Team Under Different Project"
        )
        
        # Assert
        assert result.is_valid is False
        assert result.error_code == "MISSING_TEAM"


# ============================================================================
# TEST: validate_row - Role validation
# ============================================================================

class TestValidateRowRole:
    """Test Role validation."""
    
    def test_fails_when_role_not_found(self, mock_db, mock_sub_segment, mock_project, mock_team):
        """Should return MISSING_ROLE error when Role doesn't exist."""
        # Arrange - All org entities exist, no active roles
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = []  # No roles in master data
        
        validator = MasterDataValidator(mock_db)
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="Nonexistent Role"
        )
        
        # Assert
        assert result.is_valid is False
        assert result.error_code == "MISSING_ROLE"
        assert "Role/Designation 'Nonexistent Role' not found" in result.error_message
    
    def test_skips_role_validation_when_not_provided(
        self, mock_db, validator, mock_sub_segment, mock_project, mock_team
    ):
        """Should skip role validation when role_name is None or empty."""
        # Arrange - All org entities exist
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        
        # Act - No role provided
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name=None
        )
        
        # Assert - validation passes
        assert result.is_valid is True


# ============================================================================
# TEST: validate_row - Role alias matching
# ============================================================================

class TestValidateRowRoleAlias:
    """Test Role alias matching in validation."""
    
    def test_role_matches_by_alias_token(self, mock_db, mock_sub_segment, mock_project, mock_team):
        """Should match role when input matches an alias token."""
        # Arrange - Role with alias
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 500
        mock_role.role_name = "Software Engineer"
        mock_role.role_alias = "SWE, Software Dev, Developer"
        mock_role.deleted_at = None
        
        # Setup db mock for org entities (first calls) and all roles query
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = [mock_role]
        
        validator = MasterDataValidator(mock_db)
        
        # Act - Input matches alias token
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="Developer"  # Matches alias token
        )
        
        # Assert - Should match via alias
        assert result.is_valid is True
        assert result.role_id == 500
    
    def test_role_alias_matching_is_case_insensitive(self, mock_db, mock_sub_segment, mock_project, mock_team):
        """Should match alias token case-insensitively."""
        # Arrange
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 501
        mock_role.role_name = "Frontend Engineer"
        mock_role.role_alias = "FE Developer, UI Engineer"
        mock_role.deleted_at = None
        
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = [mock_role]
        
        validator = MasterDataValidator(mock_db)
        
        # Act - Mixed case input
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="fe developer"  # lowercase alias
        )
        
        # Assert
        assert result.is_valid is True
        assert result.role_id == 501
    
    def test_role_name_match_takes_precedence(self, mock_db, mock_sub_segment, mock_project, mock_team):
        """Should match role_name before checking aliases."""
        # Arrange - Two roles, one where alias matches another's role_name
        mock_role1 = MagicMock(spec=Role)
        mock_role1.role_id = 510
        mock_role1.role_name = "Developer"
        mock_role1.role_alias = None
        mock_role1.deleted_at = None
        
        mock_role2 = MagicMock(spec=Role)
        mock_role2.role_id = 511
        mock_role2.role_name = "Software Engineer"
        mock_role2.role_alias = "Developer"  # Same as role1's role_name
        mock_role2.deleted_at = None
        
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = [mock_role1, mock_role2]
        
        validator = MasterDataValidator(mock_db)
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="Developer"
        )
        
        # Assert - Should match role_name first (role1), not alias (role2)
        assert result.is_valid is True
        assert result.role_id == 510
    
    def test_soft_deleted_role_not_matched(self, mock_db, mock_sub_segment, mock_project, mock_team):
        """Should not match soft-deleted roles by name or alias."""
        # Arrange - Soft-deleted role (filtered out by query, but testing lookup)
        # The query filters deleted_at IS NULL, so soft-deleted roles won't be in results
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = []  # No active roles returned
        
        validator = MasterDataValidator(mock_db)
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="Deleted Role"
        )
        
        # Assert - MISSING_ROLE since no active roles exist
        assert result.is_valid is False
        assert result.error_code == "MISSING_ROLE"
    
    def test_role_neither_name_nor_alias_fails(self, mock_db, mock_sub_segment, mock_project, mock_team):
        """Should fail with MISSING_ROLE when neither name nor alias matches."""
        # Arrange
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 520
        mock_role.role_name = "Backend Engineer"
        mock_role.role_alias = "BE Dev, Server Engineer"
        mock_role.deleted_at = None
        
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = [mock_role]
        
        validator = MasterDataValidator(mock_db)
        
        # Act - Input doesn't match name or any alias
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="Data Scientist"
        )
        
        # Assert - Same error code and message format
        assert result.is_valid is False
        assert result.error_code == "MISSING_ROLE"
        assert "Role/Designation 'Data Scientist' not found in master data" in result.error_message
    
    def test_role_alias_with_whitespace_normalized(self, mock_db, mock_sub_segment, mock_project, mock_team):
        """Should normalize whitespace in alias tokens and input."""
        # Arrange
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 530
        mock_role.role_name = "DevOps Engineer"
        mock_role.role_alias = "  DevOps  ,  Site Reliability  "  # Extra whitespace
        mock_role.deleted_at = None
        
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = [mock_role]
        
        validator = MasterDataValidator(mock_db)
        
        # Act - Input with extra whitespace
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="  Site   Reliability  "  # Extra spaces
        )
        
        # Assert
        assert result.is_valid is True
        assert result.role_id == 530
    
    def test_skips_role_validation_when_empty_string(
        self, mock_db, validator, mock_sub_segment, mock_project, mock_team
    ):
        """Should skip role validation when role_name is empty string."""
        # Arrange
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name=""
        )
        
        # Assert
        assert result.is_valid is True


# ============================================================================
# TEST: validate_row - Success cases
# ============================================================================

class TestValidateRowSuccess:
    """Test successful validation scenarios."""
    
    def test_returns_all_ids_on_success_without_role(
        self, mock_db, validator, mock_sub_segment, mock_project, mock_team
    ):
        """Should return all entity IDs when validation passes (no role)."""
        # Arrange
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team"
        )
        
        # Assert
        assert result.is_valid is True
        assert result.sub_segment_id == 1
        assert result.project_id == 10
        assert result.team_id == 100
        assert result.role_id is None
        assert result.error_code is None
        assert result.error_message is None
    
    def test_returns_all_ids_on_success_with_role(
        self, mock_db, mock_sub_segment, mock_project, mock_team
    ):
        """Should return all entity IDs including role when validation passes."""
        # Arrange - Create role with required attributes
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 500
        mock_role.role_name = "Engineer"
        mock_role.role_alias = None
        mock_role.deleted_at = None
        
        mock_db.first.side_effect = [mock_sub_segment, mock_project, mock_team]
        mock_db.all.return_value = [mock_role]
        
        validator = MasterDataValidator(mock_db)
        
        # Act
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Test Project",
            team_name="Test Team",
            role_name="Engineer"
        )
        
        # Assert
        assert result.is_valid is True
        assert result.sub_segment_id == 1
        assert result.project_id == 10
        assert result.team_id == 100
        assert result.role_id == 500


# ============================================================================
# TEST: Caching behavior
# ============================================================================

class TestValidatorCaching:
    """Test caching behavior for performance."""
    
    def test_caches_sub_segment_lookup(self, mock_db, validator, mock_sub_segment):
        """Should cache SubSegment lookup to avoid repeated DB queries."""
        # Arrange
        mock_db.first.side_effect = [mock_sub_segment, None]  # First call returns sub
        
        # Act - First call
        validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Project1",
            team_name="Team1"
        )
        
        # Clear side_effect for second call
        mock_db.first.side_effect = [None, None]
        
        # Second validation with same SubSegment should use cache
        result = validator.validate_row(
            sub_segment_name="Test SubSegment",
            project_name="Project2",
            team_name="Team2"
        )
        
        # Assert - SubSegment was cached, so we moved to Project validation
        assert result.error_code == "MISSING_PROJECT"
    
    def test_clear_cache_resets_all_caches(self, mock_db, validator, mock_sub_segment):
        """Should clear all caches when clear_cache() is called."""
        # Arrange - populate cache
        mock_db.first.return_value = mock_sub_segment
        validator._get_sub_segment("Test SubSegment")
        
        # Verify cache is populated
        assert "Test SubSegment" in validator._sub_segment_cache
        
        # Act
        validator.clear_cache()
        
        # Assert
        assert len(validator._sub_segment_cache) == 0
        assert len(validator._project_cache) == 0
        assert len(validator._team_cache) == 0
        assert len(validator._role_lookup) == 0
        assert validator._roles_loaded is False


# ============================================================================
# TEST: String normalization
# ============================================================================

class TestStringNormalization:
    """Test string normalization for master data lookup."""
    
    def test_normalizes_whitespace_in_names(self, mock_db, validator, mock_sub_segment):
        """Should normalize multiple spaces to single space."""
        # Arrange
        mock_db.first.side_effect = [mock_sub_segment, None]
        
        # Act - name with multiple spaces
        result = validator.validate_row(
            sub_segment_name="Test   SubSegment",  # Multiple spaces
            project_name="Some Project",
            team_name="Some Team"
        )
        
        # Assert - normalized to "Test SubSegment" before lookup
        # Verification: moved past SubSegment validation to Project
        assert result.error_code == "MISSING_PROJECT"
    
    def test_handles_none_values_gracefully(self, mock_db, validator):
        """Should handle None values without error."""
        # Act
        result = validator.validate_row(
            sub_segment_name=None,
            project_name=None,
            team_name=None
        )
        
        # Assert - empty string normalized, not found
        assert result.is_valid is False
        assert result.error_code == "MISSING_SUB_SEGMENT"
    
    def test_handles_pandas_nan_values(self, mock_db, validator):
        """Should handle pandas NaN values without error."""
        import pandas as pd
        
        # Act
        result = validator.validate_row(
            sub_segment_name=pd.NA,
            project_name=pd.NA,
            team_name=pd.NA
        )
        
        # Assert
        assert result.is_valid is False
        assert result.error_code == "MISSING_SUB_SEGMENT"


# ============================================================================
# TEST: MasterDataValidationResult dataclass
# ============================================================================

class TestMasterDataValidationResult:
    """Test the MasterDataValidationResult dataclass."""
    
    def test_default_values(self):
        """Should have correct default values."""
        result = MasterDataValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.sub_segment_id is None
        assert result.project_id is None
        assert result.team_id is None
        assert result.role_id is None
        assert result.error_code is None
        assert result.error_message is None
    
    def test_failure_result(self):
        """Should store error details on failure."""
        result = MasterDataValidationResult(
            is_valid=False,
            error_code="MISSING_SUB_SEGMENT",
            error_message="Sub-Segment 'XYZ' not found"
        )
        
        assert result.is_valid is False
        assert result.error_code == "MISSING_SUB_SEGMENT"
        assert "XYZ" in result.error_message
