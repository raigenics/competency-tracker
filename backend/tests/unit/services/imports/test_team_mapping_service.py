"""
Unit tests for team_mapping_service.py

Tests:
1. get_teams_for_mapping - returns active teams for a project
2. get_teams_for_mapping - filters by search query
3. get_teams_for_mapping - excludes soft-deleted teams
4. map_team_to_failed_row - successful mapping
5. map_team_to_failed_row - errors for invalid inputs
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.imports.team_mapping_service import (
    get_teams_for_mapping,
    map_team_to_failed_row,
    normalize_team_name,
    TeamsForMappingResponse,
    MapTeamResponse,
    ImportJobNotFoundError,
    ProjectNotFoundError,
    TeamNotFoundError,
    TeamNotInProjectError,
    InvalidFailedRowError,
    AlreadyMappedError,
    NotTeamErrorError,
    MissingTeamTextError,
    MissingProjectInfoError
)
from app.models.team import Team
from app.models.project import Project
from app.models.import_job import ImportJob


class TestNormalizeTeamName:
    """Tests for normalize_team_name function."""
    
    def test_normalizes_whitespace(self):
        """Should normalize whitespace in team names."""
        assert normalize_team_name("  DevOps  Team  ") == "devops team"
    
    def test_lowercase(self):
        """Should convert to lowercase."""
        assert normalize_team_name("DevOps TEAM") == "devops team"
    
    def test_empty_string(self):
        """Should handle empty string."""
        assert normalize_team_name("") == ""


class TestGetTeamsForMapping:
    """Tests for get_teams_for_mapping function."""
    
    def test_returns_active_teams_for_project(self):
        """Should return all active teams for a project sorted alphabetically."""
        # Arrange
        mock_db = MagicMock()
        
        mock_project = MagicMock(spec=Project)
        mock_project.project_id = 10
        mock_project.project_name = "IT Project"
        
        mock_team1 = MagicMock(spec=Team)
        mock_team1.team_id = 1
        mock_team1.team_name = "DevOps Team"
        mock_team1.project_id = 10
        
        mock_team2 = MagicMock(spec=Team)
        mock_team2.team_id = 2
        mock_team2.team_name = "Backend Team"
        mock_team2.project_id = 10
        
        # Setup query chain for project lookup
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        # Setup query chain for teams lookup
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value = mock_team_query
        mock_team_query.order_by.return_value = mock_team_query
        mock_team_query.all.return_value = [mock_team2, mock_team1]  # Pre-sorted
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            return mock_team_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = get_teams_for_mapping(mock_db, project_id=10)
        
        # Assert
        assert isinstance(result, TeamsForMappingResponse)
        assert result.total_count == 2
        assert result.project_id == 10
        assert result.project_name == "IT Project"
        assert len(result.teams) == 2
        assert result.teams[0].team_id == 2
        assert result.teams[0].team_name == "Backend Team"
        assert result.teams[1].team_id == 1
        assert result.teams[1].team_name == "DevOps Team"
    
    def test_filters_by_search_query(self):
        """Should filter teams by search query on name."""
        # Arrange
        mock_db = MagicMock()
        
        mock_project = MagicMock(spec=Project)
        mock_project.project_id = 10
        mock_project.project_name = "IT Project"
        
        mock_team = MagicMock(spec=Team)
        mock_team.team_id = 1
        mock_team.team_name = "DevOps Team"
        mock_team.project_id = 10
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value = mock_team_query
        mock_team_query.order_by.return_value = mock_team_query
        mock_team_query.all.return_value = [mock_team]
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            return mock_team_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = get_teams_for_mapping(mock_db, project_id=10, search_query="devops")
        
        # Assert
        assert result.total_count == 1
        assert result.teams[0].team_name == "DevOps Team"
    
    def test_raises_error_when_project_not_found(self):
        """Should raise ProjectNotFoundError when project doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_project_query
        
        # Act & Assert
        with pytest.raises(ProjectNotFoundError) as exc_info:
            get_teams_for_mapping(mock_db, project_id=999)
        
        assert exc_info.value.project_id == 999
    
    def test_returns_empty_when_no_teams(self):
        """Should return empty list when no teams exist for project."""
        # Arrange
        mock_db = MagicMock()
        
        mock_project = MagicMock(spec=Project)
        mock_project.project_id = 10
        mock_project.project_name = "Empty Project"
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = mock_project
        
        mock_team_query = MagicMock()
        mock_team_query.filter.return_value = mock_team_query
        mock_team_query.order_by.return_value = mock_team_query
        mock_team_query.all.return_value = []
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            return mock_team_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = get_teams_for_mapping(mock_db, project_id=10)
        
        # Assert
        assert result.total_count == 0
        assert len(result.teams) == 0


class TestMapTeamToFailedRow:
    """Tests for map_team_to_failed_row function."""
    
    def test_successful_mapping(self):
        """Should successfully map a MISSING_TEAM row to a team."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.job_id = "test-job-123"
        mock_import_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_TEAM',
                    'team_name': 'eCOM Ops (DevOps)',
                    'project_name': 'IT Project',
                    'project_id': 10,
                    'resolved': False
                }
            ]
        }
        
        mock_project = MagicMock(spec=Project)
        mock_project.project_id = 10
        mock_project.project_name = "IT Project"
        
        mock_team = MagicMock(spec=Team)
        mock_team.team_id = 1
        mock_team.team_name = "DevOps"
        mock_team.project_id = 10
        
        # Setup query chain
        def query_side_effect(model):
            if model == ImportJob:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_import_job
                return mock_query
            elif model == Team:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_team
                return mock_query
            elif model == Project:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_project
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = map_team_to_failed_row(
            db=mock_db,
            import_run_id="test-job-123",
            failed_row_index=0,
            target_team_id=1
        )
        
        # Assert
        assert isinstance(result, MapTeamResponse)
        assert result.failed_row_index == 0
        assert result.mapped_team_id == 1
        assert result.mapped_team_name == "DevOps"
        assert result.project_id == 10
        mock_db.commit.assert_called_once()
    
    def test_raises_import_job_not_found(self):
        """Should raise ImportJobNotFoundError when job doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(ImportJobNotFoundError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="nonexistent-job",
                failed_row_index=0,
                target_team_id=1
            )
        
        assert exc_info.value.job_id == "nonexistent-job"
    
    def test_raises_not_team_error_error(self):
        """Should raise NotTeamErrorError when row is not MISSING_TEAM."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_ROLE',  # Not MISSING_TEAM
                    'role_name': 'Some Role',
                    'team_name': 'Some Team'
                }
            ]
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_import_job
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(NotTeamErrorError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_team_id=1
            )
        
        assert exc_info.value.error_code == 'MISSING_ROLE'
    
    def test_raises_already_mapped_error(self):
        """Should raise AlreadyMappedError when row is already resolved."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_TEAM',
                    'team_name': 'Some Team',
                    'resolved': True  # Already mapped
                }
            ]
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_import_job
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(AlreadyMappedError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_team_id=1
            )
        
        assert exc_info.value.index == 0
    
    def test_raises_team_not_found_error(self):
        """Should raise TeamNotFoundError when target team doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_TEAM',
                    'team_name': 'Some Team',
                    'project_name': 'IT Project',
                    'project_id': 10,
                    'resolved': False
                }
            ]
        }
        
        def query_side_effect(model):
            if model == ImportJob:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_import_job
                return mock_query
            elif model == Team:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = None  # Team not found
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Act & Assert
        with pytest.raises(TeamNotFoundError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_team_id=999
            )
        
        assert exc_info.value.team_id == 999
    
    def test_raises_team_not_in_project_error(self):
        """Should raise TeamNotInProjectError when team belongs to different project."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_TEAM',
                    'team_name': 'Some Team',
                    'project_name': 'IT Project',
                    'project_id': 10,
                    'resolved': False
                }
            ]
        }
        
        mock_team = MagicMock(spec=Team)
        mock_team.team_id = 1
        mock_team.team_name = "DevOps"
        mock_team.project_id = 20  # Different project
        
        def query_side_effect(model):
            if model == ImportJob:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_import_job
                return mock_query
            elif model == Team:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_team
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Act & Assert
        with pytest.raises(TeamNotInProjectError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_team_id=1
            )
        
        assert exc_info.value.team_id == 1
        assert exc_info.value.expected_project_id == 10
        assert exc_info.value.actual_project_id == 20
    
    def test_raises_invalid_failed_row_error_for_out_of_range(self):
        """Should raise InvalidFailedRowError when index is out of range."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.result = {
            'failed_rows': [
                {'error_code': 'MISSING_TEAM', 'team_name': 'Team1'}
            ]
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_import_job
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(InvalidFailedRowError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=5,  # Out of range
                target_team_id=1
            )
        
        assert exc_info.value.index == 5
    
    def test_raises_missing_team_text_error(self):
        """Should raise MissingTeamTextError when team_name is empty."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_TEAM',
                    'team_name': '',  # Empty
                    'project_id': 10,
                    'resolved': False
                }
            ]
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_import_job
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(MissingTeamTextError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_team_id=1
            )
        
        assert exc_info.value.index == 0
    
    def test_raises_missing_project_info_error(self):
        """Should raise MissingProjectInfoError when project info is missing."""
        # Arrange
        mock_db = MagicMock()
        
        mock_import_job = MagicMock(spec=ImportJob)
        mock_import_job.result = {
            'failed_rows': [
                {
                    'error_code': 'MISSING_TEAM',
                    'team_name': 'Some Team',
                    # No project_name or project_id
                    'resolved': False
                }
            ]
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_import_job
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(MissingProjectInfoError) as exc_info:
            map_team_to_failed_row(
                db=mock_db,
                import_run_id="test-job",
                failed_row_index=0,
                target_team_id=1
            )
        
        assert exc_info.value.index == 0
