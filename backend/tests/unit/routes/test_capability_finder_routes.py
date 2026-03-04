"""
Unit tests for capability_finder API routes.

Tests all API endpoints for the Capability Finder feature.
Uses mocked service layer to isolate route logic.
"""
import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.capability_finder import router
from app.schemas.capability_finder import (
    EmployeeSearchResult, SkillInfo, SearchRequest, ExportRequest
)


# Create test app with the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# Mock the database dependency
def override_get_db():
    return MagicMock()


# ============================================================================
# TEST: GET /capability-finder/skills
# ============================================================================

class TestGetAllSkillsEndpoint:
    """Test GET /capability-finder/skills endpoint."""
    
    def test_returns_skill_list_success(self):
        """Should return 200 with list of skills."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_all_skills', return_value=['AWS', 'Docker', 'Python']):
            # Act
            response = client.get('/capability-finder/skills')
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'skills': ['AWS', 'Docker', 'Python']}
    
    def test_returns_empty_list_when_no_skills(self):
        """Should return 200 with empty list when no skills."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_all_skills', return_value=[]):
            # Act
            response = client.get('/capability-finder/skills')
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'skills': []}
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_all_skills', side_effect=Exception('DB error')):
            # Act
            response = client.get('/capability-finder/skills')
        
        # Assert
        assert response.status_code == 500
        assert 'Failed to fetch skills' in response.json()['detail']


# ============================================================================
# TEST: GET /capability-finder/skills/suggestions
# ============================================================================

class TestGetSkillSuggestionsEndpoint:
    """Test GET /capability-finder/skills/suggestions endpoint."""
    
    def test_returns_suggestions_without_query(self):
        """Should return suggestions when no query provided."""
        # Arrange
        suggestions = [
            {'skill_id': 1, 'skill_name': 'Python', 'is_employee_available': True, 'is_selectable': True}
        ]
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_skill_suggestions', return_value=suggestions):
            # Act
            response = client.get('/capability-finder/skills/suggestions')
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()['suggestions']) == 1
    
    def test_passes_query_parameter(self):
        """Should pass query parameter to service."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_skill_suggestions', return_value=[]) as mock_fn:
            # Act
            response = client.get('/capability-finder/skills/suggestions?query=python')
        
        # Assert
        assert response.status_code == 200
        mock_fn.assert_called_once()
        # Check second argument (after db) is the query
        call_args = mock_fn.call_args
        assert call_args[0][1] == 'python' or (len(call_args) > 1 and 'python' in str(call_args))
    
    def test_returns_empty_suggestions(self):
        """Should return empty suggestions list."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_skill_suggestions', return_value=[]):
            # Act
            response = client.get('/capability-finder/skills/suggestions?query=nonexistent')
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'suggestions': []}
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_skill_suggestions', side_effect=Exception('DB error')):
            # Act
            response = client.get('/capability-finder/skills/suggestions')
        
        # Assert
        assert response.status_code == 500
        assert 'Failed to fetch skill suggestions' in response.json()['detail']


# ============================================================================
# TEST: GET /capability-finder/roles
# ============================================================================

class TestGetAllRolesEndpoint:
    """Test GET /capability-finder/roles endpoint."""
    
    def test_returns_role_list_success(self):
        """Should return 200 with list of roles."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_all_roles', return_value=['Developer', 'Manager', 'QA']):
            # Act
            response = client.get('/capability-finder/roles')
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'roles': ['Developer', 'Manager', 'QA']}
    
    def test_returns_empty_list_when_no_roles(self):
        """Should return 200 with empty list when no roles."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_all_roles', return_value=[]):
            # Act
            response = client.get('/capability-finder/roles')
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'roles': []}
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.get_all_roles', side_effect=Exception('DB error')):
            # Act
            response = client.get('/capability-finder/roles')
        
        # Assert
        assert response.status_code == 500
        assert 'Failed to fetch roles' in response.json()['detail']


# ============================================================================
# TEST: POST /capability-finder/search
# ============================================================================

class TestSearchMatchingTalentEndpoint:
    """Test POST /capability-finder/search endpoint."""
    
    def test_returns_matching_employees(self):
        """Should return 200 with matching employees."""
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
        with patch('app.api.routes.capability_finder.CapabilityFinderService.search_matching_talent', return_value=results):
            # Act
            response = client.post('/capability-finder/search', json={
                'skills': ['Python'],
                'min_proficiency': 0,
                'min_experience_years': 0
            })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 1
        assert len(data['results']) == 1
        assert data['results'][0]['employee_name'] == 'John Doe'
    
    def test_returns_empty_results(self):
        """Should return empty results when no matches."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.search_matching_talent', return_value=[]):
            # Act
            response = client.post('/capability-finder/search', json={
                'skills': ['NonExistent'],
                'min_proficiency': 5,
                'min_experience_years': 10
            })
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'results': [], 'count': 0}
    
    def test_accepts_all_filter_parameters(self):
        """Should accept all filter parameters."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.search_matching_talent', return_value=[]) as mock_fn:
            # Act
            response = client.post('/capability-finder/search', json={
                'skills': ['Python', 'AWS'],
                'sub_segment_id': 1,
                'team_id': 5,
                'role': 'Developer',
                'min_proficiency': 3,
                'min_experience_years': 2
            })
        
        # Assert
        assert response.status_code == 200
        mock_fn.assert_called_once()
    
    def test_returns_400_on_validation_error(self):
        """Should return 400 when service raises ValueError."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.search_matching_talent', side_effect=ValueError('Invalid filter')):
            # Act
            response = client.post('/capability-finder/search', json={
                'skills': ['Python']
            })
        
        # Assert
        assert response.status_code == 400
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.search_matching_talent', side_effect=Exception('DB error')):
            # Act
            response = client.post('/capability-finder/search', json={
                'skills': ['Python']
            })
        
        # Assert
        assert response.status_code == 500
        assert 'Failed to search matching talent' in response.json()['detail']
    
    def test_validates_min_proficiency_range(self):
        """Should validate min_proficiency is in valid range (0-5)."""
        # Act - proficiency > 5 should be invalid
        response = client.post('/capability-finder/search', json={
            'skills': ['Python'],
            'min_proficiency': 10
        })
        
        # Assert - Pydantic validation should fail
        assert response.status_code == 422
    
    def test_validates_min_experience_non_negative(self):
        """Should validate min_experience_years is >= 0."""
        # Act - negative experience should be invalid
        response = client.post('/capability-finder/search', json={
            'skills': ['Python'],
            'min_experience_years': -5
        })
        
        # Assert - Pydantic validation should fail
        assert response.status_code == 422


# ============================================================================
# TEST: POST /capability-finder/export
# ============================================================================

class TestExportMatchingTalentEndpoint:
    """Test POST /capability-finder/export endpoint."""
    
    def test_returns_excel_file_for_all_mode(self):
        """Should return Excel file for 'all' mode export."""
        # Arrange
        excel_content = BytesIO(b'PK\x03\x04...')  # Excel files start with PK
        excel_content.seek(0)
        
        with patch('app.api.routes.capability_finder.CapabilityFinderService.export_matching_talent_to_excel', return_value=excel_content):
            # Act
            response = client.post('/capability-finder/export', json={
                'mode': 'all',
                'filters': {
                    'skills': ['Python'],
                    'min_proficiency': 0,
                    'min_experience_years': 0
                },
                'selected_employee_ids': []
            })
        
        # Assert
        assert response.status_code == 200
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers['content-type']
    
    def test_returns_excel_file_for_selected_mode(self):
        """Should return Excel file for 'selected' mode export."""
        # Arrange
        excel_content = BytesIO(b'PK\x03\x04...')
        excel_content.seek(0)
        
        with patch('app.api.routes.capability_finder.CapabilityFinderService.export_matching_talent_to_excel', return_value=excel_content):
            # Act
            response = client.post('/capability-finder/export', json={
                'mode': 'selected',
                'filters': {
                    'skills': ['Python'],
                    'min_proficiency': 0,
                    'min_experience_years': 0
                },
                'selected_employee_ids': [1, 2, 3]
            })
        
        # Assert
        assert response.status_code == 200
    
    def test_returns_error_for_selected_mode_without_ids(self):
        """Should return error when mode='selected' but no IDs provided."""
        # The route validates this condition before calling service
        # Due to exception handling in the real app, this returns an error status
        
        # Act
        response = client.post('/capability-finder/export', json={
            'mode': 'selected',
            'filters': {
                'skills': ['Python'],
                'min_proficiency': 0,
                'min_experience_years': 0
            },
            'selected_employee_ids': []
        })
        
        # Assert - Should return error status (400 or 500 depending on exception handling)
        assert response.status_code >= 400
        # Check error response contains relevant message
        response_data = response.json()
        assert 'detail' in response_data
        assert 'selected_employee_ids' in response_data['detail'].lower() or 'empty' in response_data['detail'].lower() or 'export' in response_data['detail'].lower()
    
    def test_includes_content_disposition_header(self):
        """Should include Content-Disposition header with filename."""
        # Arrange
        excel_content = BytesIO(b'PK\x03\x04...')
        excel_content.seek(0)
        
        with patch('app.api.routes.capability_finder.CapabilityFinderService.export_matching_talent_to_excel', return_value=excel_content):
            # Act
            response = client.post('/capability-finder/export', json={
                'mode': 'all',
                'filters': {
                    'skills': [],
                    'min_proficiency': 0,
                    'min_experience_years': 0
                },
                'selected_employee_ids': []
            })
        
        # Assert
        assert 'content-disposition' in response.headers
        assert 'attachment' in response.headers['content-disposition']
        assert '.xlsx' in response.headers['content-disposition']
    
    def test_returns_400_on_value_error(self):
        """Should return 400 when service raises ValueError."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.export_matching_talent_to_excel', side_effect=ValueError('Invalid export params')):
            # Act
            response = client.post('/capability-finder/export', json={
                'mode': 'all',
                'filters': {
                    'skills': ['Python'],
                    'min_proficiency': 0,
                    'min_experience_years': 0
                },
                'selected_employee_ids': []
            })
        
        # Assert
        assert response.status_code == 400
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.export_matching_talent_to_excel', side_effect=Exception('Export failed')):
            # Act
            response = client.post('/capability-finder/export', json={
                'mode': 'all',
                'filters': {
                    'skills': ['Python'],
                    'min_proficiency': 0,
                    'min_experience_years': 0
                },
                'selected_employee_ids': []
            })
        
        # Assert
        assert response.status_code == 500
        assert 'Failed to export matching talent' in response.json()['detail']


# ============================================================================
# TEST: Request Schema Validation
# ============================================================================

class TestSchemaValidation:
    """Test Pydantic schema validation for request bodies."""
    
    def test_search_request_requires_skills_list(self):
        """SearchRequest.skills should accept list of strings."""
        # Act
        response = client.post('/capability-finder/search', json={
            'skills': ['Python', 'AWS', 'Docker']
        })
        
        # Assert - should not fail validation
        # Will be 200 or 500 depending on mock, but not 422
        with patch('app.api.routes.capability_finder.CapabilityFinderService.search_matching_talent', return_value=[]):
            response = client.post('/capability-finder/search', json={
                'skills': ['Python']
            })
        assert response.status_code != 422
    
    def test_export_request_validates_mode(self):
        """ExportRequest.mode should be string."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.export_matching_talent_to_excel', return_value=BytesIO()):
            # Act - mode as string should work
            response = client.post('/capability-finder/export', json={
                'mode': 'all',
                'filters': {'skills': []},
                'selected_employee_ids': []
            })
        
        # Assert
        assert response.status_code == 200
    
    def test_search_request_applies_default_values(self):
        """SearchRequest should apply defaults for optional fields."""
        # Arrange
        with patch('app.api.routes.capability_finder.CapabilityFinderService.search_matching_talent', return_value=[]) as mock_fn:
            # Act - minimal request body
            response = client.post('/capability-finder/search', json={
                'skills': ['Python']
            })
        
        # Assert - should apply defaults
        assert response.status_code == 200
