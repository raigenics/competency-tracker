"""
Unit tests for capability_finder_service.py (Facade)

Tests that the facade correctly delegates to isolated service modules.
"""
import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from app.services.capability_finder_service import CapabilityFinderService
from app.schemas.capability_finder import EmployeeSearchResult, SkillInfo


# ============================================================================
# TEST: get_all_skills (Delegation)
# ============================================================================

class TestGetAllSkills:
    """Test get_all_skills delegation."""
    
    def test_delegates_to_skills_service(self, mock_db):
        """Should delegate to skills_service.get_all_skills."""
        # Arrange
        with patch('app.services.capability_finder_service._get_all_skills', return_value=['AWS', 'Docker']) as mock_fn:
            # Act
            result = CapabilityFinderService.get_all_skills(mock_db)
        
        # Assert
        mock_fn.assert_called_once_with(mock_db)
        assert result == ['AWS', 'Docker']
    
    def test_returns_skill_list(self, mock_db):
        """Should return list of skill names."""
        # Arrange
        with patch('app.services.capability_finder_service._get_all_skills', return_value=['Python', 'Java', 'React']):
            # Act
            result = CapabilityFinderService.get_all_skills(mock_db)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
    
    def test_returns_empty_list_when_no_skills(self, mock_db):
        """Should return empty list when no skills exist."""
        # Arrange
        with patch('app.services.capability_finder_service._get_all_skills', return_value=[]):
            # Act
            result = CapabilityFinderService.get_all_skills(mock_db)
        
        # Assert
        assert result == []


# ============================================================================
# TEST: get_skill_suggestions (Delegation)
# ============================================================================

class TestGetSkillSuggestions:
    """Test get_skill_suggestions delegation."""
    
    def test_delegates_to_skills_service_with_query(self, mock_db):
        """Should delegate to skills_service.get_skill_suggestions with query."""
        # Arrange
        with patch('app.services.capability_finder_service._get_skill_suggestions', return_value=[]) as mock_fn:
            # Act
            result = CapabilityFinderService.get_skill_suggestions(mock_db, query='python')
        
        # Assert
        mock_fn.assert_called_once_with(mock_db, 'python')
    
    def test_delegates_with_none_query(self, mock_db):
        """Should delegate with None query when not provided."""
        # Arrange
        with patch('app.services.capability_finder_service._get_skill_suggestions', return_value=[]) as mock_fn:
            # Act
            result = CapabilityFinderService.get_skill_suggestions(mock_db)
        
        # Assert
        mock_fn.assert_called_once_with(mock_db, None)
    
    def test_returns_suggestions_with_metadata(self, mock_db):
        """Should return skill suggestions with availability metadata."""
        # Arrange
        suggestions = [
            {'skill_id': 1, 'skill_name': 'Python', 'is_employee_available': True, 'is_selectable': True}
        ]
        with patch('app.services.capability_finder_service._get_skill_suggestions', return_value=suggestions):
            # Act
            result = CapabilityFinderService.get_skill_suggestions(mock_db)
        
        # Assert
        assert len(result) == 1
        assert result[0]['skill_name'] == 'Python'


# ============================================================================
# TEST: get_all_roles (Delegation)
# ============================================================================

class TestGetAllRoles:
    """Test get_all_roles delegation."""
    
    def test_delegates_to_roles_service(self, mock_db):
        """Should delegate to roles_service.get_all_roles."""
        # Arrange
        with patch('app.services.capability_finder_service._get_all_roles', return_value=['Developer', 'Manager']) as mock_fn:
            # Act
            result = CapabilityFinderService.get_all_roles(mock_db)
        
        # Assert
        mock_fn.assert_called_once_with(mock_db)
        assert result == ['Developer', 'Manager']
    
    def test_returns_role_list(self, mock_db):
        """Should return list of role names."""
        # Arrange
        with patch('app.services.capability_finder_service._get_all_roles', return_value=['QA', 'Architect', 'Lead']):
            # Act
            result = CapabilityFinderService.get_all_roles(mock_db)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 3


# ============================================================================
# TEST: search_matching_talent (Delegation)
# ============================================================================

class TestSearchMatchingTalent:
    """Test search_matching_talent delegation."""
    
    def test_delegates_to_search_service(self, mock_db):
        """Should delegate to search_service.search_matching_talent."""
        # Arrange
        with patch('app.services.capability_finder_service._search_matching_talent', return_value=[]) as mock_fn:
            # Act
            result = CapabilityFinderService.search_matching_talent(
                mock_db,
                skills=['Python', 'AWS']
            )
        
        # Assert
        mock_fn.assert_called_once()
    
    def test_passes_all_parameters(self, mock_db):
        """Should pass all filter parameters to search service."""
        # Arrange
        with patch('app.services.capability_finder_service._search_matching_talent', return_value=[]) as mock_fn:
            # Act
            CapabilityFinderService.search_matching_talent(
                mock_db,
                skills=['Python'],
                sub_segment_id=1,
                team_id=5,
                role='Developer',
                min_proficiency=3,
                min_experience_years=2
            )
        
        # Assert
        mock_fn.assert_called_once_with(
            db=mock_db,
            skills=['Python'],
            sub_segment_id=1,
            team_id=5,
            role='Developer',
            min_proficiency=3,
            min_experience_years=2
        )
    
    def test_returns_search_results(self, mock_db):
        """Should return list of EmployeeSearchResult."""
        # Arrange
        results = [
            EmployeeSearchResult(
                employee_id=1,
                employee_name='John Doe',
                sub_segment='Engineering',
                team='TeamA',
                role='Developer',
                top_skills=[SkillInfo(name='Python', proficiency=5)]
            )
        ]
        with patch('app.services.capability_finder_service._search_matching_talent', return_value=results):
            # Act
            result = CapabilityFinderService.search_matching_talent(
                mock_db,
                skills=['Python']
            )
        
        # Assert
        assert len(result) == 1
        assert result[0].employee_name == 'John Doe'
    
    def test_uses_default_values_for_optional_params(self, mock_db):
        """Should use default values for optional parameters."""
        # Arrange
        with patch('app.services.capability_finder_service._search_matching_talent', return_value=[]) as mock_fn:
            # Act
            CapabilityFinderService.search_matching_talent(
                mock_db,
                skills=['Python']
            )
        
        # Assert
        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs['sub_segment_id'] is None
        assert call_kwargs['team_id'] is None
        assert call_kwargs['role'] is None
        assert call_kwargs['min_proficiency'] == 0
        assert call_kwargs['min_experience_years'] == 0


# ============================================================================
# TEST: export_matching_talent_to_excel (Delegation)
# ============================================================================

class TestExportMatchingTalentToExcel:
    """Test export_matching_talent_to_excel delegation."""
    
    def test_delegates_to_export_service(self, mock_db):
        """Should delegate to export_service.export_matching_talent_to_excel."""
        # Arrange
        with patch('app.services.capability_finder_service._export_matching_talent_to_excel', return_value=BytesIO()) as mock_fn:
            # Act
            result = CapabilityFinderService.export_matching_talent_to_excel(
                mock_db,
                mode='all',
                skills=['Python']
            )
        
        # Assert
        mock_fn.assert_called_once()
    
    def test_passes_all_parameters(self, mock_db):
        """Should pass all parameters to export service."""
        # Arrange
        selected_ids = [1, 2, 3]
        with patch('app.services.capability_finder_service._export_matching_talent_to_excel', return_value=BytesIO()) as mock_fn:
            # Act
            CapabilityFinderService.export_matching_talent_to_excel(
                mock_db,
                mode='selected',
                skills=['Python', 'AWS'],
                sub_segment_id=1,
                team_id=5,
                role='Developer',
                min_proficiency=3,
                min_experience_years=2,
                selected_employee_ids=selected_ids
            )
        
        # Assert
        mock_fn.assert_called_once_with(
            db=mock_db,
            mode='selected',
            skills=['Python', 'AWS'],
            sub_segment_id=1,
            team_id=5,
            role='Developer',
            min_proficiency=3,
            min_experience_years=2,
            selected_employee_ids=selected_ids
        )
    
    def test_returns_bytesio_object(self, mock_db):
        """Should return BytesIO object from export service."""
        # Arrange
        excel_buffer = BytesIO(b'test excel content')
        with patch('app.services.capability_finder_service._export_matching_talent_to_excel', return_value=excel_buffer):
            # Act
            result = CapabilityFinderService.export_matching_talent_to_excel(
                mock_db,
                mode='all',
                skills=[]
            )
        
        # Assert
        assert isinstance(result, BytesIO)
    
    def test_all_mode_with_empty_selected_ids(self, mock_db):
        """Should accept 'all' mode with empty selected_employee_ids."""
        # Arrange
        with patch('app.services.capability_finder_service._export_matching_talent_to_excel', return_value=BytesIO()) as mock_fn:
            # Act
            CapabilityFinderService.export_matching_talent_to_excel(
                mock_db,
                mode='all',
                skills=['Python'],
                selected_employee_ids=[]
            )
        
        # Assert - should not raise
        mock_fn.assert_called_once()
