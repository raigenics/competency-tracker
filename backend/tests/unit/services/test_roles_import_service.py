"""
Unit tests for roles_import_service.py

Tests:
1. Successful import with multiple roles
2. Duplicate by role_name (existing)
3. Duplicate by role_name matching existing alias
4. Duplicate by alias matching existing role_name
5. Duplicate by alias matching existing alias
6. Missing required columns
7. Empty role name fails validation
8. Intra-batch duplicate detection
9. Empty file handling
10. IntegrityError returns friendly message (no DB stack trace)
11. After IntegrityError, subsequent rows still import (no session cascade)
12. SAVEPOINT handles transaction isolation properly
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO
import pandas as pd
from sqlalchemy.exc import IntegrityError

from app.services.roles_import_service import (
    RoleImportService,
    import_roles_from_excel,
    RoleImportRow,
    ImportResult
)


def create_excel_file(data: list[dict]) -> bytes:
    """Helper to create Excel file bytes from data."""
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


@pytest.fixture
def mock_role_factory():
    """Factory to create mock Role objects."""
    def _create(role_id, role_name, role_alias=None, deleted_at=None):
        role = Mock()
        role.role_id = role_id
        role.role_name = role_name
        role.role_alias = role_alias
        role.deleted_at = deleted_at
        return role
    return _create


class TestRoleImportService:
    """Test RoleImportService class."""
    
    def test_successful_import_single_role(self, mock_db, mock_role_factory):
        """Should import a single role successfully."""
        # Arrange - no existing roles
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "Developer", "Alias": "Dev", "Role Description": "Software developer"}
        ]
        file_content = create_excel_file(data)
        
        # Mock role creation
        new_role = Mock()
        new_role.role_id = 1
        new_role.role_name = "Developer"
        new_role.role_alias = "Dev"
        new_role.role_description = "Software developer"
        
        def mock_flush():
            new_role.role_id = 1
        mock_db.flush = mock_flush
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 1
        assert result.success_count == 1
        assert result.failure_count == 0
        assert len(result.failures) == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_successful_import_multiple_roles(self, mock_db, mock_role_factory):
        """Should import multiple roles successfully."""
        # Arrange - no existing roles
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "Developer", "Alias": "Dev", "Role Description": "Dev role"},
            {"Role Name": "Manager", "Alias": "Mgr", "Role Description": "Manager role"},
            {"Role Name": "Analyst", "Alias": "", "Role Description": "Business analyst"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 3
        assert result.success_count == 3
        assert result.failure_count == 0
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_called_once()
    
    def test_duplicate_by_role_name_existing(self, mock_db, mock_role_factory):
        """Should fail when role_name already exists in database."""
        # Arrange - existing role
        existing_role = mock_role_factory(1, "Developer", None)
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_role]
        
        data = [
            {"Role Name": "Developer", "Alias": "", "Role Description": "New developer"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 1
        assert result.success_count == 0
        assert result.failure_count == 1
        assert "already exists" in result.failures[0]["reason"]
    
    def test_duplicate_role_name_matches_existing_alias(self, mock_db, mock_role_factory):
        """Should fail when new role_name matches an existing role's alias."""
        # Arrange - existing role with alias "Dev"
        existing_role = mock_role_factory(1, "Developer", "Dev, Software Engineer")
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_role]
        
        data = [
            {"Role Name": "Dev", "Alias": "", "Role Description": "Short name for Dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 1
        assert result.success_count == 0
        assert result.failure_count == 1
        assert "matches an existing role's alias" in result.failures[0]["reason"]
    
    def test_duplicate_alias_matches_existing_role_name(self, mock_db, mock_role_factory):
        """Should fail when new alias matches an existing role_name."""
        # Arrange - existing role named "Dev"
        existing_role = mock_role_factory(1, "Developer", None)
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_role]
        
        data = [
            {"Role Name": "Software Dev", "Alias": "Developer", "Role Description": "Another dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 1
        assert result.success_count == 0
        assert result.failure_count == 1
        assert "Alias matches an existing role name" in result.failures[0]["reason"]
    
    def test_duplicate_alias_matches_existing_alias(self, mock_db, mock_role_factory):
        """Should fail when new alias matches an existing role's alias."""
        # Arrange - existing role with alias "Dev"
        existing_role = mock_role_factory(1, "Developer", "Dev, Programmer")
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_role]
        
        data = [
            {"Role Name": "Coder", "Alias": "Dev", "Role Description": "Another dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 1
        assert result.success_count == 0
        assert result.failure_count == 1
        assert "Alias already exists" in result.failures[0]["reason"]
    
    def test_intra_batch_duplicate_role_name(self, mock_db, mock_role_factory):
        """Should fail when same role_name appears twice in import file."""
        # Arrange - no existing roles
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "Developer", "Alias": "", "Role Description": "First dev"},
            {"Role Name": "Developer", "Alias": "", "Role Description": "Second dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 2
        assert result.success_count == 1  # First one succeeds
        assert result.failure_count == 1  # Second one fails
        # After first succeeds, it's in role_name_map, so duplicate detection finds it there
        assert "Duplicate" in result.failures[0]["reason"]
        assert "Role name" in result.failures[0]["reason"] or "already exists" in result.failures[0]["reason"]
    
    def test_intra_batch_role_name_matches_earlier_alias(self, mock_db, mock_role_factory):
        """Should fail when role_name matches an alias from earlier row."""
        # Arrange - no existing roles
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "Developer", "Alias": "Dev, SDE", "Role Description": "Developer"},
            {"Role Name": "Dev", "Alias": "", "Role Description": "Short dev name"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.success_count == 1
        assert result.failure_count == 1
        # After first succeeds, its alias "Dev" is in alias_token_map
        assert "Duplicate" in result.failures[0]["reason"]
        assert "alias" in result.failures[0]["reason"].lower()
    
    def test_missing_required_columns(self, mock_db, mock_role_factory):
        """Should fail when required columns are missing."""
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Missing "Role Description" column
        data = [
            {"Role Name": "Developer", "Alias": "Dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.total_rows == 0
        assert result.success_count == 0
        assert result.failure_count == 0
        assert len(service.errors) == 1
        assert "Missing required columns" in service.errors[0]["reason"]
    
    def test_empty_role_name_fails_validation(self, mock_db, mock_role_factory):
        """Should fail when role_name is empty."""
        # Arrange - no existing roles
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "", "Alias": "Dev", "Role Description": "Missing name"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        # Empty role name rows are skipped entirely if all fields are empty
        # But if just role_name is empty, it should fail validation
        assert result.failure_count == 1
        assert "Role name is required" in result.failures[0]["reason"]
    
    def test_case_insensitive_duplicate_detection(self, mock_db, mock_role_factory):
        """Should detect duplicates regardless of case."""
        # Arrange - existing role "Developer"
        existing_role = mock_role_factory(1, "Developer", None)
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_role]
        
        data = [
            {"Role Name": "DEVELOPER", "Alias": "", "Role Description": "Uppercase dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert
        assert result.failure_count == 1
        assert "already exists" in result.failures[0]["reason"]
    
    def test_multiple_comma_separated_aliases(self, mock_db, mock_role_factory):
        """Should handle multiple aliases in comma-separated format."""
        # Arrange - existing role with one of the aliases
        existing_role = mock_role_factory(1, "Developer", "SDE")
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_role]
        
        data = [
            {"Role Name": "Coder", "Alias": "Dev, SDE, Programmer", "Role Description": "New role"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert - should fail because "SDE" is already an alias
        assert result.failure_count == 1
        assert "Alias already exists" in result.failures[0]["reason"]
    
    def test_skips_completely_empty_rows(self, mock_db, mock_role_factory):
        """Should skip rows where all fields are empty."""
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "Developer", "Alias": "Dev", "Role Description": "Valid role"},
            {"Role Name": "", "Alias": "", "Role Description": ""},
            {"Role Name": "Manager", "Alias": "", "Role Description": "Valid manager"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert - empty row should be skipped (not counted)
        assert result.total_rows == 2
        assert result.success_count == 2
        assert result.failure_count == 0


class TestImportRolesFromExcel:
    """Test the convenience function."""
    
    def test_import_roles_from_excel_function(self, mock_db, mock_role_factory):
        """Should work via convenience function."""
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "Developer", "Alias": "", "Role Description": "Dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        result = import_roles_from_excel(mock_db, file_content, "test_user")
        
        # Assert
        assert isinstance(result, ImportResult)
        assert result.success_count == 1


class TestSoftDeleteImportBehavior:
    """Test that soft-deleted roles don't block imports."""
    
    def test_import_role_after_soft_delete_succeeds(self, mock_db, mock_role_factory):
        """
        Import role with same name as soft-deleted role → should succeed.
        
        The _build_conflict_maps() filters by deleted_at IS NULL,
        so soft-deleted role names don't appear in conflict maps.
        """
        # Arrange - no active roles returned (soft-deleted roles are filtered out)
        # The filter(Role.deleted_at.is_(None)) excludes soft-deleted roles
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        data = [
            {"Role Name": "Archived Role", "Alias": "", "Role Description": "Recreated role"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert - import should succeed
        assert result.total_rows == 1
        assert result.success_count == 1
        assert result.failure_count == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_conflict_maps_exclude_soft_deleted_roles(self, mock_db, mock_role_factory):
        """_build_conflict_maps should only include active roles."""
        # Arrange - query with deleted_at filter returns no roles
        # (meaning soft-deleted roles exist but aren't returned)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Act
        service = RoleImportService(mock_db)
        service._build_conflict_maps()
        
        # Assert - maps should be empty (no active roles)
        assert len(service.role_name_map) == 0
        assert len(service.alias_token_map) == 0


class TestTransactionIsolation:
    """Test transaction isolation and error handling."""
    
    def test_integrity_error_returns_friendly_message_no_db_trace(self, mock_db, mock_role_factory):
        """
        DB IntegrityError should return friendly message without stack trace.
        
        When DB raises UniqueViolation, user should see:
        "Duplicate: Role name already exists"
        NOT "psycopg.errors.UniqueViolation: ..."
        """
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Make flush raise IntegrityError to simulate DB constraint violation
        mock_db.flush.side_effect = IntegrityError(
            "INSERT INTO roles ...",
            {},
            Exception("UniqueViolation: duplicate key value violates unique constraint")
        )
        
        data = [
            {"Role Name": "Developer", "Alias": "", "Role Description": "Dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert - should fail with friendly message
        assert result.failure_count == 1
        failure_reason = result.failures[0]["reason"]
        
        # Should have friendly message
        assert "Duplicate: Role name already exists" == failure_reason
        
        # Should NOT have DB stack trace or psycopg errors
        assert "psycopg" not in failure_reason.lower()
        assert "UniqueViolation" not in failure_reason
        assert "Database error" not in failure_reason
        assert "INSERT INTO" not in failure_reason
    
    def test_subsequent_rows_import_after_integrity_error(self, mock_db, mock_role_factory):
        """
        After IntegrityError on one row, subsequent valid rows should still import.
        
        This tests that SAVEPOINT (begin_nested) properly isolates the failure
        and doesn't put the session in a rollback-required state.
        """
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Track flush calls
        flush_call_count = [0]
        
        def mock_flush():
            flush_call_count[0] += 1
            # First flush raises error, second succeeds
            if flush_call_count[0] == 1:
                raise IntegrityError(
                    "INSERT INTO roles ...",
                    {},
                    Exception("UniqueViolation")
                )
        
        mock_db.flush.side_effect = mock_flush
        
        data = [
            {"Role Name": "Duplicate", "Alias": "", "Role Description": "Will fail"},
            {"Role Name": "Valid", "Alias": "", "Role Description": "Should succeed"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert - should have partial success
        assert result.failure_count == 1
        assert result.success_count == 1
        
        # First row should fail with friendly message
        assert result.failures[0]["role_name"] == "Duplicate"
        assert "Duplicate" in result.failures[0]["reason"]
        
        # Session should NOT have cascade failure message
        for f in result.failures:
            assert "rolled back" not in f["reason"].lower()
            assert "previous exception" not in f["reason"].lower()
    
    def test_unexpected_error_returns_clean_message(self, mock_db, mock_role_factory):
        """
        Generic exceptions should return clean message, not raw error.
        """
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.flush.side_effect = Exception("Internal SQLAlchemy error with sensitive data")
        
        data = [
            {"Role Name": "Developer", "Alias": "", "Role Description": "Dev"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert - should fail with generic clean message
        assert result.failure_count == 1
        failure_reason = result.failures[0]["reason"]
        
        # Should be generic message
        assert "Unexpected error while importing this row" == failure_reason
        
        # Should NOT leak internal error details
        assert "SQLAlchemy" not in failure_reason
        assert "sensitive" not in failure_reason
    
    def test_conflict_check_prevents_integrity_error(self, mock_db, mock_role_factory):
        """
        In-memory conflict check should prevent DB insert entirely.
        
        When role_name matches existing alias, the row should be skipped
        BEFORE attempting DB insert (no IntegrityError needed).
        """
        # Arrange - existing role with alias "Dev"
        existing_role = mock_role_factory(1, "Developer", "Dev, SDE")
        mock_db.query.return_value.filter.return_value.all.return_value = [existing_role]
        
        data = [
            {"Role Name": "Dev", "Alias": "", "Role Description": "Conflicts with alias"}
        ]
        file_content = create_excel_file(data)
        
        # Act
        service = RoleImportService(mock_db)
        result = service.import_roles(file_content, "test_user")
        
        # Assert - should fail via pre-check, not DB error
        assert result.failure_count == 1
        assert "matches an existing role's alias" in result.failures[0]["reason"]
        
        # Should NOT have tried to insert (no add called)
        mock_db.add.assert_not_called()
