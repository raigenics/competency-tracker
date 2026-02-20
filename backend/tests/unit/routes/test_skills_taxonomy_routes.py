"""
Unit tests for skills API routes used by Organizational Skill Map.

Tests all API endpoints in /skills that support the Organizational Skill Map feature:
- GET /skills/taxonomy/tree
- GET /skills/capability/categories
- GET /skills/capability/categories/{category_id}/subcategories
- GET /skills/capability/subcategories/{subcategory_id}/skills
- GET /skills/capability/search
- GET /skills/{skill_id}/summary
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.skills import router
from app.schemas.skill import (
    TaxonomyTreeResponse, TaxonomyCategoryItem, TaxonomySubcategoryItem, TaxonomySkillItem,
    CategoriesResponse, SubcategoriesResponse, SkillsResponse, SkillSearchResponse,
    SkillSummaryResponse, CategoryInfo
)


# Create test app with the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# ============================================================================
# TEST: GET /skills/taxonomy/tree
# ============================================================================

class TestGetTaxonomyTree:
    """Test GET /skills/taxonomy/tree endpoint."""
    
    def test_returns_taxonomy_tree_success(self):
        """Should return 200 with complete taxonomy tree."""
        # Arrange
        mock_response = TaxonomyTreeResponse(categories=[
            TaxonomyCategoryItem(
                category_id=1,
                category_name="Programming",
                subcategories=[
                    TaxonomySubcategoryItem(
                        subcategory_id=1,
                        subcategory_name="Backend",
                        skills=[
                            TaxonomySkillItem(skill_id=1, skill_name="Python")
                        ]
                    )
                ]
            )
        ])
        with patch('app.api.routes.skills.taxonomy_tree_service.get_taxonomy_tree', return_value=mock_response):
            # Act
            response = client.get('/skills/taxonomy/tree')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'categories' in data
        assert len(data['categories']) == 1
        assert data['categories'][0]['category_name'] == "Programming"
    
    def test_returns_empty_categories_when_no_data(self):
        """Should return 200 with empty categories when no data."""
        # Arrange
        mock_response = TaxonomyTreeResponse(categories=[])
        with patch('app.api.routes.skills.taxonomy_tree_service.get_taxonomy_tree', return_value=mock_response):
            # Act
            response = client.get('/skills/taxonomy/tree')
        
        # Assert
        assert response.status_code == 200
        assert response.json()['categories'] == []
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.skills.taxonomy_tree_service.get_taxonomy_tree', side_effect=Exception('DB error')):
            # Act
            response = client.get('/skills/taxonomy/tree')
        
        # Assert
        assert response.status_code == 500
        assert 'Error fetching skill taxonomy tree' in response.json()['detail']


# ============================================================================
# TEST: GET /skills/capability/categories
# ============================================================================

class TestGetCapabilityCategories:
    """Test GET /skills/capability/categories endpoint."""
    
    def test_returns_categories_success(self):
        """Should return 200 with categories list."""
        # Arrange
        mock_response = CategoriesResponse(categories=[
            {'category_id': 1, 'category_name': 'Programming', 'subcategory_count': 5, 'skill_count': 20}
        ])
        with patch('app.api.routes.skills.taxonomy_categories_service.get_categories_for_lazy_loading', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/categories')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'categories' in data
    
    def test_returns_empty_list_when_no_categories(self):
        """Should return 200 with empty list when no categories."""
        # Arrange
        mock_response = CategoriesResponse(categories=[])
        with patch('app.api.routes.skills.taxonomy_categories_service.get_categories_for_lazy_loading', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/categories')
        
        # Assert
        assert response.status_code == 200
        assert response.json()['categories'] == []
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.skills.taxonomy_categories_service.get_categories_for_lazy_loading', side_effect=Exception('DB error')):
            # Act
            response = client.get('/skills/capability/categories')
        
        # Assert
        assert response.status_code == 500
        assert 'Error fetching categories' in response.json()['detail']


# ============================================================================
# TEST: GET /skills/capability/categories/{category_id}/subcategories
# ============================================================================

class TestGetSubcategoriesForCategory:
    """Test GET /skills/capability/categories/{category_id}/subcategories endpoint."""
    
    def test_returns_subcategories_success(self):
        """Should return 200 with subcategories for valid category."""
        # Arrange
        mock_response = SubcategoriesResponse(
            category_id=1,
            category_name='Programming',
            subcategories=[
                {'subcategory_id': 1, 'subcategory_name': 'Backend', 'skill_count': 10}
            ]
        )
        with patch('app.api.routes.skills.taxonomy_subcategories_service.get_subcategories_for_category', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/categories/1/subcategories')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'subcategories' in data
    
    def test_returns_empty_list_for_category_without_subcategories(self):
        """Should return 200 with empty list for category without subcategories."""
        # Arrange
        mock_response = SubcategoriesResponse(
            category_id=1,
            category_name='Empty Category',
            subcategories=[]
        )
        with patch('app.api.routes.skills.taxonomy_subcategories_service.get_subcategories_for_category', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/categories/1/subcategories')
        
        # Assert
        assert response.status_code == 200
        assert response.json()['subcategories'] == []
    
    def test_returns_404_for_nonexistent_category(self):
        """Should return 404 when category not found."""
        # Arrange
        with patch('app.api.routes.skills.taxonomy_subcategories_service.get_subcategories_for_category', side_effect=ValueError('Category not found')):
            # Act
            response = client.get('/skills/capability/categories/999/subcategories')
        
        # Assert
        assert response.status_code == 404
        assert 'Category not found' in response.json()['detail']
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.skills.taxonomy_subcategories_service.get_subcategories_for_category', side_effect=Exception('DB error')):
            # Act
            response = client.get('/skills/capability/categories/1/subcategories')
        
        # Assert
        assert response.status_code == 500


# ============================================================================
# TEST: GET /skills/capability/subcategories/{subcategory_id}/skills
# ============================================================================

class TestGetSkillsForSubcategory:
    """Test GET /skills/capability/subcategories/{subcategory_id}/skills endpoint."""
    
    def test_returns_skills_success(self):
        """Should return 200 with skills for valid subcategory."""
        # Arrange
        mock_response = SkillsResponse(
            subcategory_id=1,
            subcategory_name='Backend',
            category_id=1,
            category_name='Programming',
            skills=[
                {'skill_id': 1, 'skill_name': 'Python'}
            ]
        )
        with patch('app.api.routes.skills.taxonomy_skills_service.get_skills_for_subcategory', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/subcategories/1/skills')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'skills' in data
    
    def test_returns_empty_list_for_subcategory_without_skills(self):
        """Should return 200 with empty list for subcategory without skills."""
        # Arrange
        mock_response = SkillsResponse(
            subcategory_id=1,
            subcategory_name='Empty Subcategory',
            category_id=1,
            category_name='Programming',
            skills=[]
        )
        with patch('app.api.routes.skills.taxonomy_skills_service.get_skills_for_subcategory', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/subcategories/1/skills')
        
        # Assert
        assert response.status_code == 200
        assert response.json()['skills'] == []
    
    def test_returns_404_for_nonexistent_subcategory(self):
        """Should return 404 when subcategory not found."""
        # Arrange
        with patch('app.api.routes.skills.taxonomy_skills_service.get_skills_for_subcategory', side_effect=ValueError('Subcategory not found')):
            # Act
            response = client.get('/skills/capability/subcategories/999/skills')
        
        # Assert
        assert response.status_code == 404
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.skills.taxonomy_skills_service.get_skills_for_subcategory', side_effect=Exception('DB error')):
            # Act
            response = client.get('/skills/capability/subcategories/1/skills')
        
        # Assert
        assert response.status_code == 500


# ============================================================================
# TEST: GET /skills/capability/search
# ============================================================================

class TestSearchSkillsInTaxonomy:
    """Test GET /skills/capability/search endpoint."""
    
    def test_returns_search_results_success(self):
        """Should return 200 with search results."""
        # Arrange
        mock_response = SkillSearchResponse(
            results=[
                {
                    'skill_id': 1,
                    'skill_name': 'Python',
                    'category_id': 1,
                    'category_name': 'Programming',
                    'subcategory_id': 1,
                    'subcategory_name': 'Backend'
                }
            ],
            count=1
        )
        with patch('app.api.routes.skills.taxonomy_search_service.search_skills_in_taxonomy', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/search?q=python')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
    
    def test_returns_empty_list_when_no_matches(self):
        """Should return 200 with empty results when no matches."""
        # Arrange
        mock_response = SkillSearchResponse(results=[], count=0)
        with patch('app.api.routes.skills.taxonomy_search_service.search_skills_in_taxonomy', return_value=mock_response):
            # Act
            response = client.get('/skills/capability/search?q=nonexistent')
        
        # Assert
        assert response.status_code == 200
        assert response.json()['results'] == []
    
    def test_requires_minimum_query_length(self):
        """Should return 422 when query is less than 2 characters."""
        # Act
        response = client.get('/skills/capability/search?q=a')
        
        # Assert
        assert response.status_code == 422
    
    def test_requires_query_parameter(self):
        """Should return 422 when query parameter is missing."""
        # Act
        response = client.get('/skills/capability/search')
        
        # Assert
        assert response.status_code == 422
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.skills.taxonomy_search_service.search_skills_in_taxonomy', side_effect=Exception('DB error')):
            # Act
            response = client.get('/skills/capability/search?q=test')
        
        # Assert
        assert response.status_code == 500


# ============================================================================
# TEST: GET /skills/{skill_id}/summary
# ============================================================================

class TestGetSkillSummary:
    """Test GET /skills/{skill_id}/summary endpoint."""
    
    def test_returns_skill_summary_success(self):
        """Should return 200 with skill summary for valid skill ID."""
        # Arrange
        mock_response = SkillSummaryResponse(
            skill_id=1,
            skill_name="Python",
            employee_count=10,
            employee_ids=[1, 2, 3],
            avg_experience_years=3.5,
            certified_count=5,
            certified_employee_count=5,
            category_info=None
        )
        with patch('app.api.routes.skills.skill_summary_service.get_skill_summary', return_value=mock_response):
            # Act
            response = client.get('/skills/1/summary')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['skill_id'] == 1
        assert data['skill_name'] == 'Python'
        assert data['employee_count'] == 10
    
    def test_returns_summary_with_zero_employees(self):
        """Should return 200 with zero counts for skill without employees."""
        # Arrange
        mock_response = SkillSummaryResponse(
            skill_id=1,
            skill_name="New Skill",
            employee_count=0,
            employee_ids=[],
            avg_experience_years=0.0,
            certified_count=0,
            certified_employee_count=0,
            category_info=None
        )
        with patch('app.api.routes.skills.skill_summary_service.get_skill_summary', return_value=mock_response):
            # Act
            response = client.get('/skills/1/summary')
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['employee_count'] == 0
        assert data['employee_ids'] == []
    
    def test_returns_404_for_nonexistent_skill(self):
        """Should return 404 when skill not found."""
        # Arrange
        with patch('app.api.routes.skills.skill_summary_service.get_skill_summary', side_effect=ValueError('Skill not found')):
            # Act
            response = client.get('/skills/999/summary')
        
        # Assert
        assert response.status_code == 404
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws exception."""
        # Arrange
        with patch('app.api.routes.skills.skill_summary_service.get_skill_summary', side_effect=Exception('DB error')):
            # Act
            response = client.get('/skills/1/summary')
        
        # Assert
        assert response.status_code == 500
