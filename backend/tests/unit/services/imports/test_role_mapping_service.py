"""
Unit tests for role_mapping_service.py

Tests:
1. get_roles_for_mapping - returns active roles
2. get_roles_for_mapping - filters by search query
3. get_roles_for_mapping - excludes soft-deleted roles
4. map_role_to_failed_row - successful mapping
5. map_role_to_failed_row - errors for invalid inputs
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.imports.role_mapping_service import (
    get_roles_for_mapping,
    map_role_to_failed_row,
    find_role_by_alias,
    add_alias_to_role,
    RolesForMappingResponse,
    MapRoleResponse,
    ImportJobNotFoundError,
    RoleNotFoundError,
    InvalidFailedRowError,
    AlreadyMappedError,
    NotRoleErrorError,
    AliasConflictError,
    MissingAliasTextError
)
from app.models.role import Role
from app.models.import_job import ImportJob


class TestGetRolesForMapping:
    """Tests for get_roles_for_mapping function."""
    
    def test_returns_active_roles(self):
        """Should return all active roles sorted alphabetically."""
        # Arrange
        mock_db = MagicMock()
        
        mock_role1 = MagicMock(spec=Role)
        mock_role1.role_id = 1
        mock_role1.role_name = "Senior Software Engineer"
        mock_role1.role_alias = "SSE, Sr. SWE"
        mock_role1.role_description = "Senior level engineer"
        
        mock_role2 = MagicMock(spec=Role)
        mock_role2.role_id = 2
        mock_role2.role_name = "Junior Developer"
        mock_role2.role_alias = None
        mock_role2.role_description = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_role2, mock_role1]  # Pre-sorted
        mock_db.query.return_value = mock_query
        
        # Act
        result = get_roles_for_mapping(mock_db)
        
        # Assert
        assert isinstance(result, RolesForMappingResponse)
        assert result.total_count == 2
        assert len(result.roles) == 2
        assert result.roles[0].role_id == 2
        assert result.roles[0].role_name == "Junior Developer"
        assert result.roles[1].role_id == 1
        assert result.roles[1].role_name == "Senior Software Engineer"
    
    def test_filters_by_search_query(self):
        """Should filter roles by search query on name and alias."""
        # Arrange
        mock_db = MagicMock()
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 1
        mock_role.role_name = "Senior Software Engineer"
        mock_role.role_alias = "SSE"
        mock_role.role_description = "Senior level"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_role]
        mock_db.query.return_value = mock_query
        
        # Act
        result = get_roles_for_mapping(mock_db, search_query="senior")
        
        # Assert
        assert result.total_count == 1
        assert result.roles[0].role_name == "Senior Software Engineer"
        # Verify filter was called (twice - once for deleted_at, once for search)
        assert mock_query.filter.call_count == 2
    
    def test_returns_empty_when_no_roles(self):
        """Should return empty list when no roles exist."""
        # Arrange
        mock_db = MagicMock()
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Act
        result = get_roles_for_mapping(mock_db)
        
        # Assert
        assert result.total_count == 0
        assert len(result.roles) == 0


class TestMapRoleToFailedRow:
    """Tests for map_role_to_failed_row function."""
    
    @patch('app.services.imports.role_mapping_service.find_role_by_alias')
    @patch('app.services.imports.role_mapping_service.add_alias_to_role')
    def test_successful_mapping_with_alias_persistence(self, mock_add_alias, mock_find_alias):
        """Should map MISSING_ROLE row to role and persist alias."""
        # Arrange
        mock_db = MagicMock()
        mock_find_alias.return_value = None  # No existing alias
        mock_add_alias.return_value = True   # Alias added successfully
        
        # Mock import job
        mock_job = MagicMock(spec=ImportJob)
        mock_job.job_id = "test-job-123"
        mock_job.result = {
            'failed_rows': [
                {
                    'sheet': 'Employee',
                    'error_code': 'MISSING_ROLE',
                    'role_name': 'Sr. Java Developer',
                    'zid': 'Z12345'
                }
            ]
        }
        
        # Mock role
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 42
        mock_role.role_name = "Senior Software Engineer"
        mock_role.deleted_at = None
        
        # Setup queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,  # First call for ImportJob
            mock_role  # Second call for Role
        ]
        
        # Act
        result = map_role_to_failed_row(
            db=mock_db,
            import_run_id="test-job-123",
            failed_row_index=0,
            target_role_id=42
        )
        
        # Assert
        assert isinstance(result, MapRoleResponse)
        assert result.failed_row_index == 0
        assert result.mapped_role_id == 42
        assert result.mapped_role_name == "Senior Software Engineer"
        assert result.alias_persisted is True  # New alias was added
        
        # Verify the failed row was updated
        assert mock_job.result['failed_rows'][0]['resolved'] is True
        assert mock_job.result['failed_rows'][0]['mapped_role_id'] == 42
        
        # Verify alias persistence was called
        mock_find_alias.assert_called_once_with(mock_db, 'Sr. Java Developer')
        mock_add_alias.assert_called_once_with(mock_db, mock_role, 'Sr. Java Developer')
        
        # Verify commit was called
        mock_db.commit.assert_called_once()
    
    def test_import_job_not_found(self):
        """Should raise ImportJobNotFoundError when job doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ImportJobNotFoundError) as exc_info:
            map_role_to_failed_row(
                db=mock_db,
                import_run_id="nonexistent-job",
                failed_row_index=0,
                target_role_id=1
            )
        
        assert "nonexistent-job" in str(exc_info.value)
    
    def test_role_not_found(self):
        """Should raise RoleNotFoundError when role doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        
        mock_job = MagicMock(spec=ImportJob)
        mock_job.result = {
            'failed_rows': [{'error_code': 'MISSING_ROLE'}]
        }
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,  # ImportJob found
            None       # Role not found
        ]
        
        # Act & Assert
        with pytest.raises(RoleNotFoundError) as exc_info:
            map_role_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_role_id=999
            )
        
        assert exc_info.value.role_id == 999
    
    def test_invalid_failed_row_index(self):
        """Should raise InvalidFailedRowError for out-of-range index."""
        # Arrange
        mock_db = MagicMock()
        
        mock_job = MagicMock(spec=ImportJob)
        mock_job.result = {
            'failed_rows': [{'error_code': 'MISSING_ROLE'}]
        }
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 1
        mock_role.deleted_at = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            mock_role
        ]
        
        # Act & Assert
        with pytest.raises(InvalidFailedRowError) as exc_info:
            map_role_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=5,  # Out of range
                target_role_id=1
            )
        
        assert exc_info.value.index == 5
    
    def test_already_mapped_row(self):
        """Should raise AlreadyMappedError when row is already resolved."""
        # Arrange
        mock_db = MagicMock()
        
        mock_job = MagicMock(spec=ImportJob)
        mock_job.result = {
            'failed_rows': [{
                'error_code': 'MISSING_ROLE',
                'resolved': True  # Already mapped
            }]
        }
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 1
        mock_role.deleted_at = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            mock_role
        ]
        
        # Act & Assert
        with pytest.raises(AlreadyMappedError) as exc_info:
            map_role_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_role_id=1
            )
        
        assert exc_info.value.index == 0
    
    def test_not_missing_role_error(self):
        """Should raise NotRoleErrorError when row is not MISSING_ROLE."""
        # Arrange
        mock_db = MagicMock()
        
        mock_job = MagicMock(spec=ImportJob)
        mock_job.result = {
            'failed_rows': [{
                'error_code': 'MISSING_PROJECT'  # Not MISSING_ROLE
            }]
        }
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 1
        mock_role.deleted_at = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            mock_role
        ]
        
        # Act & Assert
        with pytest.raises(NotRoleErrorError) as exc_info:
            map_role_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_role_id=1
            )
        
        assert exc_info.value.error_code == 'MISSING_PROJECT'


class TestRoleAliasResolutionDuringImport:
    """
    Tests verifying that role alias resolution works during employee import.
    
    These tests verify that when an employee is imported with a role name
    that matches an alias, the import resolves to the canonical role_id
    and does NOT raise MISSING_ROLE error.
    """
    
    def test_role_alias_resolves_to_canonical_role(self):
        """
        Role alias 'Sr. Java Developer' should resolve to canonical role.
        
        This test verifies the MasterDataValidator._get_role method
        properly resolves aliases to canonical role IDs.
        """
        from app.services.imports.employee_import.master_data_validator import MasterDataValidator
        from app.models.role import Role
        
        # Arrange
        mock_db = MagicMock()
        
        # Mock role with aliases
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 100
        mock_role.role_name = "Senior Software Engineer"
        mock_role.role_alias = "Sr. Java Developer, SSE, Senior SWE"
        mock_role.deleted_at = None
        
        # Mock query chain for roles (the validator calls .all() to preload)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_role]
        mock_db.query.return_value = mock_query
        
        validator = MasterDataValidator(mock_db)
        
        # Act - try to resolve by alias
        resolved_role = validator._get_role("Sr. Java Developer")
        
        # Assert - should resolve to the canonical role
        assert resolved_role is not None
        assert resolved_role.role_id == 100
        assert resolved_role.role_name == "Senior Software Engineer"
    
    def test_role_alias_case_insensitive_match(self):
        """Role alias matching should be case-insensitive."""
        from app.services.imports.employee_import.master_data_validator import MasterDataValidator
        from app.models.role import Role
        
        # Arrange
        mock_db = MagicMock()
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 100
        mock_role.role_name = "Senior Software Engineer"
        mock_role.role_alias = "Sr. Java Developer"
        mock_role.deleted_at = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_role]
        mock_db.query.return_value = mock_query
        
        validator = MasterDataValidator(mock_db)
        
        # Act - try with different case
        resolved_role = validator._get_role("SR. JAVA DEVELOPER")
        
        # Assert
        assert resolved_role is not None
        assert resolved_role.role_id == 100


class TestAliasConflictAndIdempotency:
    """Tests for alias conflict detection and idempotent mapping."""
    
    @patch('app.services.imports.role_mapping_service.find_role_by_alias')
    def test_alias_conflict_raises_409(self, mock_find_alias):
        """Should raise AliasConflictError when alias is mapped to different role."""
        # Arrange
        mock_db = MagicMock()
        
        # Existing role that has this alias
        existing_role = MagicMock(spec=Role)
        existing_role.role_id = 99
        existing_role.role_name = "Product Manager"
        mock_find_alias.return_value = existing_role  # Alias exists on different role
        
        # Mock import job
        mock_job = MagicMock(spec=ImportJob)
        mock_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_ROLE',
                    'role_name': 'Sr. Java Developer'
                }
            ]
        }
        
        # Target role (different from existing)
        target_role = MagicMock(spec=Role)
        target_role.role_id = 42  # Different from existing_role.role_id
        target_role.role_name = "Senior Software Engineer"
        target_role.deleted_at = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            target_role
        ]
        
        # Act & Assert
        with pytest.raises(AliasConflictError) as exc_info:
            map_role_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_role_id=42
            )
        
        assert exc_info.value.alias_text == 'Sr. Java Developer'
        assert exc_info.value.existing_role_name == "Product Manager"
    
    @patch('app.services.imports.role_mapping_service.find_role_by_alias')
    @patch('app.services.imports.role_mapping_service.add_alias_to_role')
    def test_idempotent_mapping_same_alias_same_role(self, mock_add_alias, mock_find_alias):
        """Should succeed without error when mapping same alias to same role."""
        # Arrange
        mock_db = MagicMock()
        
        # Same role already has this alias
        target_role = MagicMock(spec=Role)
        target_role.role_id = 42
        target_role.role_name = "Senior Software Engineer"
        target_role.deleted_at = None
        
        mock_find_alias.return_value = target_role  # Alias exists on same role
        
        # Mock import job
        mock_job = MagicMock(spec=ImportJob)
        mock_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_ROLE',
                    'role_name': 'Sr. Java Developer'
                }
            ]
        }
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            target_role
        ]
        
        # Act
        result = map_role_to_failed_row(
            db=mock_db,
            import_run_id="test-job",
            failed_row_index=0,
            target_role_id=42
        )
        
        # Assert - should succeed but alias_persisted should be False
        assert result.alias_persisted is False
        assert result.mapped_role_id == 42
        
        # add_alias should NOT be called since alias already exists
        mock_add_alias.assert_not_called()
    
    @patch('app.services.imports.role_mapping_service.find_role_by_alias')
    def test_missing_role_name_in_failed_row(self, mock_find_alias):
        """Should raise MissingAliasTextError when failed row has no role_name."""
        # Arrange
        mock_db = MagicMock()
        
        mock_job = MagicMock(spec=ImportJob)
        mock_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_ROLE',
                    # role_name is missing!
                    'zid': 'Z12345'
                }
            ]
        }
        
        target_role = MagicMock(spec=Role)
        target_role.role_id = 42
        target_role.deleted_at = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            target_role
        ]
        
        # Act & Assert
        with pytest.raises(MissingAliasTextError) as exc_info:
            map_role_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_role_id=42
            )
        
        assert exc_info.value.index == 0


class TestAddAliasToRole:
    """Tests for add_alias_to_role helper function."""
    
    def test_adds_first_alias(self):
        """Should set role_alias when role has no existing aliases."""
        mock_db = MagicMock()
        mock_role = MagicMock(spec=Role)
        mock_role.role_alias = None
        
        result = add_alias_to_role(mock_db, mock_role, "Sr. Java Developer")
        
        assert result is True
        assert mock_role.role_alias == "Sr. Java Developer"
    
    def test_appends_alias_to_existing(self):
        """Should append alias when role has existing aliases."""
        mock_db = MagicMock()
        mock_role = MagicMock(spec=Role)
        mock_role.role_alias = "SSE"
        
        result = add_alias_to_role(mock_db, mock_role, "Sr. Java Developer")
        
        assert result is True
        assert mock_role.role_alias == "SSE,Sr. Java Developer"
    
    def test_does_not_duplicate_alias(self):
        """Should not add alias if it already exists (case-insensitive)."""
        mock_db = MagicMock()
        mock_role = MagicMock(spec=Role)
        mock_role.role_alias = "Sr. Java Developer"
        
        result = add_alias_to_role(mock_db, mock_role, "sr. java developer")
        
        assert result is False  # Alias already exists
        assert mock_role.role_alias == "Sr. Java Developer"  # Unchanged
    
    def test_empty_alias_returns_false(self):
        """Should return False for empty alias text."""
        mock_db = MagicMock()
        mock_role = MagicMock(spec=Role)
        mock_role.role_alias = None
        
        result = add_alias_to_role(mock_db, mock_role, "   ")
        
        assert result is False


class TestFindRoleByAlias:
    """Tests for find_role_by_alias helper function."""
    
    def test_finds_role_by_alias(self):
        """Should find role when alias matches."""
        mock_db = MagicMock()
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 42
        mock_role.role_name = "Senior Software Engineer"
        mock_role.role_alias = "SSE, Sr. Java Developer"
        mock_role.deleted_at = None
        
        # Mock the query for roles with aliases
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_role]
        mock_db.query.return_value = mock_query
        
        result = find_role_by_alias(mock_db, "Sr. Java Developer")
        
        assert result is not None
        assert result.role_id == 42
    
    def test_returns_none_when_not_found(self):
        """Should return None when no matching alias exists."""
        mock_db = MagicMock()
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_name = "Senior Software Engineer"
        mock_role.role_alias = "SSE"
        mock_role.deleted_at = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_role]
        mock_db.query.return_value = mock_query
        
        result = find_role_by_alias(mock_db, "Unknown Role")
        
        assert result is None
    
    def test_finds_by_role_name(self):
        """Should find role when text matches role_name exactly."""
        mock_db = MagicMock()
        
        mock_role = MagicMock(spec=Role)
        mock_role.role_id = 42
        mock_role.role_name = "Senior Software Engineer"
        mock_role.role_alias = None
        mock_role.deleted_at = None
        
        # First query returns empty (no roles with aliases matching)
        # Second query returns all roles to check role_name
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        # First call: roles_with_aliases returns empty (no alias matches)
        # Second call: all roles returned for role_name check
        mock_query.all.side_effect = [[], [mock_role]]
        mock_db.query.return_value = mock_query
        
        result = find_role_by_alias(mock_db, "Senior Software Engineer")
        
        assert result is not None
        assert result.role_id == 42
