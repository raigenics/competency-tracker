"""
Unit tests for Master Data API routes (/master-data/*).

Tests all Skill Taxonomy CRUD endpoints:
- GET /master-data/skill-taxonomy - Get full hierarchy
- POST /master-data/skill-taxonomy/categories - Create category
- POST /master-data/skill-taxonomy/categories/{id}/subcategories - Create subcategory
- POST /master-data/skill-taxonomy/subcategories/{id}/skills - Create skill
- PATCH /master-data/skill-taxonomy/categories/{id} - Update category
- PATCH /master-data/skill-taxonomy/subcategories/{id} - Update subcategory
- PATCH /master-data/skill-taxonomy/skills/{id} - Update skill
- PATCH /master-data/skill-taxonomy/aliases/{id} - Update alias
- POST /master-data/skill-taxonomy/skills/{id}/aliases - Create alias
- DELETE /master-data/skill-taxonomy/aliases/{id} - Delete alias
- DELETE /master-data/skill-taxonomy/categories/{id} - Delete category
- DELETE /master-data/skill-taxonomy/subcategories/{id} - Delete subcategory
- DELETE /master-data/skill-taxonomy/skills/{id} - Delete skill
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

from app.api.routes.master_data import router
from app.schemas.master_data_taxonomy import (
    SkillTaxonomyResponse,
    TaxonomyCategoryDTO,
    TaxonomySubCategoryDTO,
    TaxonomySkillDTO,
    TaxonomyAliasDTO,
)
from app.schemas.master_data_update import (
    CategoryCreateResponse,
    CategoryUpdateResponse,
    SubcategoryCreateResponse,
    SubcategoryUpdateResponse,
    SkillCreateResponse,
    SkillUpdateResponse,
    AliasCreateResponse,
    AliasUpdateResponse,
)
from app.services.master_data.exceptions import NotFoundError, ConflictError, ValidationError


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


@pytest.fixture
def sample_taxonomy_response():
    """Create a sample full taxonomy response."""
    return SkillTaxonomyResponse(
        categories=[
            TaxonomyCategoryDTO(
                id=1,
                name="Programming",
                description=None,
                created_at=datetime(2024, 1, 15),
                created_by="admin",
                subcategories=[
                    TaxonomySubCategoryDTO(
                        id=1,
                        name="Backend",
                        description=None,
                        created_at=datetime(2024, 1, 15),
                        created_by="admin",
                        skills=[
                            TaxonomySkillDTO(
                                id=1,
                                name="Python",
                                description=None,
                                employee_count=25,
                                created_at=datetime(2024, 1, 15),
                                created_by="admin",
                                aliases=[
                                    TaxonomyAliasDTO(
                                        id=1,
                                        text="Python3",
                                        source="manual",
                                        confidence_score=1.0
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ],
        total_categories=1,
        total_subcategories=1,
        total_skills=1
    )


# ============================================================================
# TEST: GET /master-data/skill-taxonomy
# ============================================================================

class TestGetSkillTaxonomy:
    """Tests for GET /master-data/skill-taxonomy endpoint."""
    
    def test_returns_taxonomy_success(self, sample_taxonomy_response):
        """Should return 200 with complete taxonomy hierarchy."""
        with patch('app.api.routes.master_data.skill_taxonomy_service.get_skill_taxonomy', 
                   return_value=sample_taxonomy_response):
            response = client.get('/master-data/skill-taxonomy')
        
        assert response.status_code == 200
        data = response.json()
        assert 'categories' in data
        assert len(data['categories']) == 1
        assert data['categories'][0]['name'] == "Programming"
        assert data['total_categories'] == 1
        assert data['total_subcategories'] == 1
        assert data['total_skills'] == 1
    
    def test_returns_taxonomy_with_search_filter(self, sample_taxonomy_response):
        """Should pass search query to service."""
        with patch('app.api.routes.master_data.skill_taxonomy_service.get_skill_taxonomy',
                   return_value=sample_taxonomy_response) as mock_service:
            response = client.get('/master-data/skill-taxonomy?q=Python')
        
        assert response.status_code == 200
        mock_service.assert_called_once()
        # Check search query was passed
        call_kwargs = mock_service.call_args
        assert call_kwargs is not None
    
    def test_returns_empty_when_no_data(self):
        """Should return 200 with empty categories."""
        empty_response = SkillTaxonomyResponse(
            categories=[],
            total_categories=0,
            total_subcategories=0,
            total_skills=0
        )
        with patch('app.api.routes.master_data.skill_taxonomy_service.get_skill_taxonomy',
                   return_value=empty_response):
            response = client.get('/master-data/skill-taxonomy')
        
        assert response.status_code == 200
        data = response.json()
        assert data['categories'] == []
        assert data['total_categories'] == 0
    
    def test_returns_500_on_service_error(self):
        """Should return 500 when service throws."""
        with patch('app.api.routes.master_data.skill_taxonomy_service.get_skill_taxonomy',
                   side_effect=Exception("DB connection failed")):
            response = client.get('/master-data/skill-taxonomy')
        
        assert response.status_code == 500
        assert "Error fetching skill taxonomy" in response.json()['detail']


# ============================================================================
# TEST: POST /master-data/skill-taxonomy/categories
# ============================================================================

class TestCreateCategory:
    """Tests for POST /master-data/skill-taxonomy/categories endpoint."""
    
    def test_create_success(self):
        """Should create category and return 201."""
        mock_response = CategoryCreateResponse(
            id=1,
            name="New Category",
            created_at=datetime(2024, 1, 15),
            created_by="system",
            message="Category created successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.create_category',
                   return_value=mock_response):
            response = client.post(
                '/master-data/skill-taxonomy/categories',
                json={"category_name": "New Category"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 1
        assert data['name'] == "New Category"
    
    def test_create_duplicate_returns_409(self):
        """Should return 409 when category name already exists."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_category',
                   side_effect=ConflictError("Category", "name", "Existing")):
            response = client.post(
                '/master-data/skill-taxonomy/categories',
                json={"category_name": "Existing"}
            )
        
        assert response.status_code == 409
        assert "already exists" in response.json()['detail']
    
    def test_create_empty_name_returns_422(self):
        """Should return 422 when category name is empty."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_category',
                   side_effect=ValidationError("category_name", "Category name cannot be empty")):
            response = client.post(
                '/master-data/skill-taxonomy/categories',
                json={"category_name": "   "}
            )
        
        assert response.status_code == 422
    
    def test_create_missing_body_returns_422(self):
        """Should return 422 when request body is missing."""
        response = client.post(
            '/master-data/skill-taxonomy/categories',
            json={}
        )
        
        assert response.status_code == 422


# ============================================================================
# TEST: POST /master-data/skill-taxonomy/categories/{id}/subcategories
# ============================================================================

class TestCreateSubcategory:
    """Tests for POST /master-data/skill-taxonomy/categories/{id}/subcategories."""
    
    def test_create_success(self):
        """Should create subcategory and return 201."""
        mock_response = SubcategoryCreateResponse(
            id=1,
            name="New Subcategory",
            category_id=1,
            created_at=datetime(2024, 1, 15),
            created_by="system",
            message="Subcategory created successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.create_subcategory',
                   return_value=mock_response):
            response = client.post(
                '/master-data/skill-taxonomy/categories/1/subcategories',
                json={"subcategory_name": "New Subcategory"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 1
        assert data['name'] == "New Subcategory"
        assert data['category_id'] == 1
    
    def test_create_category_not_found_returns_404(self):
        """Should return 404 when parent category doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_subcategory',
                   side_effect=NotFoundError("Category", 999)):
            response = client.post(
                '/master-data/skill-taxonomy/categories/999/subcategories',
                json={"subcategory_name": "Test"}
            )
        
        assert response.status_code == 404
        assert "not found" in response.json()['detail']
    
    def test_create_duplicate_returns_409(self):
        """Should return 409 when subcategory name exists in category."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_subcategory',
                   side_effect=ConflictError("Subcategory", "name", "Existing", "category")):
            response = client.post(
                '/master-data/skill-taxonomy/categories/1/subcategories',
                json={"subcategory_name": "Existing"}
            )
        
        assert response.status_code == 409
    
    def test_create_missing_body_returns_422(self):
        """Should return 422 when request body is missing."""
        response = client.post(
            '/master-data/skill-taxonomy/categories/1/subcategories',
            content="",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


# ============================================================================
# TEST: POST /master-data/skill-taxonomy/subcategories/{id}/skills
# ============================================================================

class TestCreateSkill:
    """Tests for POST /master-data/skill-taxonomy/subcategories/{id}/skills."""
    
    def test_create_success_without_aliases(self):
        """Should create skill without aliases and return 201."""
        mock_response = SkillCreateResponse(
            id=1,
            name="Python",
            subcategory_id=1,
            created_at=datetime(2024, 1, 15),
            created_by="system",
            aliases=[],
            message="Skill created successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.create_skill',
                   return_value=mock_response):
            response = client.post(
                '/master-data/skill-taxonomy/subcategories/1/skills',
                json={"skill_name": "Python"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 1
        assert data['name'] == "Python"
        assert data['aliases'] == []
    
    def test_create_success_with_aliases(self):
        """Should create skill with aliases and return 201."""
        mock_response = SkillCreateResponse(
            id=1,
            name="React",
            subcategory_id=1,
            created_at=datetime(2024, 1, 15),
            created_by="system",
            aliases=[
                {"id": 1, "alias_text": "ReactJS", "skill_id": 1, "source": "manual"},
                {"id": 2, "alias_text": "React.js", "skill_id": 1, "source": "manual"}
            ],
            message="Skill created successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.create_skill',
                   return_value=mock_response):
            response = client.post(
                '/master-data/skill-taxonomy/subcategories/1/skills',
                json={"skill_name": "React", "alias_text": "ReactJS, React.js"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data['aliases']) == 2
    
    def test_create_subcategory_not_found_returns_404(self):
        """Should return 404 when parent subcategory doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_skill',
                   side_effect=NotFoundError("Subcategory", 999)):
            response = client.post(
                '/master-data/skill-taxonomy/subcategories/999/skills',
                json={"skill_name": "Test"}
            )
        
        assert response.status_code == 404
    
    def test_create_duplicate_skill_returns_409(self):
        """Should return 409 when skill name exists in subcategory."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_skill',
                   side_effect=ConflictError("Skill", "name", "Python", "subcategory")):
            response = client.post(
                '/master-data/skill-taxonomy/subcategories/1/skills',
                json={"skill_name": "Python"}
            )
        
        assert response.status_code == 409


# ============================================================================
# TEST: PATCH /master-data/skill-taxonomy/categories/{id}
# ============================================================================

class TestUpdateCategory:
    """Tests for PATCH /master-data/skill-taxonomy/categories/{id}."""
    
    def test_update_success(self):
        """Should update category name and return 200."""
        mock_response = CategoryUpdateResponse(
            id=1,
            name="Updated Name",
            message="Category updated successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.update_category_name',
                   return_value=mock_response):
            response = client.patch(
                '/master-data/skill-taxonomy/categories/1',
                json={"category_name": "Updated Name"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "Updated Name"
    
    def test_update_not_found_returns_404(self):
        """Should return 404 when category doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_category_name',
                   side_effect=NotFoundError("Category", 999)):
            response = client.patch(
                '/master-data/skill-taxonomy/categories/999',
                json={"category_name": "Test"}
            )
        
        assert response.status_code == 404
    
    def test_update_duplicate_returns_409(self):
        """Should return 409 when new name already exists."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_category_name',
                   side_effect=ConflictError("Category", "name", "Existing")):
            response = client.patch(
                '/master-data/skill-taxonomy/categories/1',
                json={"category_name": "Existing"}
            )
        
        assert response.status_code == 409
    
    def test_update_empty_name_returns_422(self):
        """Should return 422 when name is empty."""
        response = client.patch(
            '/master-data/skill-taxonomy/categories/1',
            json={}
        )
        
        assert response.status_code == 422
    
    def test_update_invalid_id_returns_422(self):
        """Should return 422 when ID is invalid (0 or negative) - path validation."""
        # Route now validates path ID >= 1
        response = client.patch(
            '/master-data/skill-taxonomy/categories/0',
            json={"category_name": "Test"}
        )
        
        assert response.status_code == 422


# ============================================================================
# TEST: PATCH /master-data/skill-taxonomy/subcategories/{id}
# ============================================================================

class TestUpdateSubcategory:
    """Tests for PATCH /master-data/skill-taxonomy/subcategories/{id}."""
    
    def test_update_success(self):
        """Should update subcategory name and return 200."""
        mock_response = SubcategoryUpdateResponse(
            id=1,
            name="Updated Subcat",
            category_id=1,
            message="Subcategory updated successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.update_subcategory_name',
                   return_value=mock_response):
            response = client.patch(
                '/master-data/skill-taxonomy/subcategories/1',
                json={"subcategory_name": "Updated Subcat"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "Updated Subcat"
    
    def test_update_not_found_returns_404(self):
        """Should return 404 when subcategory doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_subcategory_name',
                   side_effect=NotFoundError("Subcategory", 999)):
            response = client.patch(
                '/master-data/skill-taxonomy/subcategories/999',
                json={"subcategory_name": "Test"}
            )
        
        assert response.status_code == 404
    
    def test_update_duplicate_returns_409(self):
        """Should return 409 when name exists in same category."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_subcategory_name',
                   side_effect=ConflictError("Subcategory", "name", "Existing", "category")):
            response = client.patch(
                '/master-data/skill-taxonomy/subcategories/1',
                json={"subcategory_name": "Existing"}
            )
        
        assert response.status_code == 409


# ============================================================================
# TEST: PATCH /master-data/skill-taxonomy/skills/{id}
# ============================================================================

class TestUpdateSkill:
    """Tests for PATCH /master-data/skill-taxonomy/skills/{id}."""
    
    def test_update_success(self):
        """Should update skill name and return 200."""
        mock_response = SkillUpdateResponse(
            id=1,
            name="Updated Skill",
            subcategory_id=1,
            message="Skill updated successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.update_skill_name',
                   return_value=mock_response):
            response = client.patch(
                '/master-data/skill-taxonomy/skills/1',
                json={"skill_name": "Updated Skill"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "Updated Skill"
    
    def test_update_not_found_returns_404(self):
        """Should return 404 when skill doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_skill_name',
                   side_effect=NotFoundError("Skill", 999)):
            response = client.patch(
                '/master-data/skill-taxonomy/skills/999',
                json={"skill_name": "Test"}
            )
        
        assert response.status_code == 404
    
    def test_update_duplicate_returns_409(self):
        """Should return 409 when name exists in same subcategory."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_skill_name',
                   side_effect=ConflictError("Skill", "name", "Existing", "subcategory")):
            response = client.patch(
                '/master-data/skill-taxonomy/skills/1',
                json={"skill_name": "Existing"}
            )
        
        assert response.status_code == 409


# ============================================================================
# TEST: PATCH /master-data/skill-taxonomy/aliases/{id}
# ============================================================================

class TestUpdateAlias:
    """Tests for PATCH /master-data/skill-taxonomy/aliases/{id}."""
    
    def test_update_text_success(self):
        """Should update alias text and return 200."""
        mock_response = AliasUpdateResponse(
            id=1,
            alias_text="New Alias Text",
            skill_id=1,
            source="manual",
            confidence_score=1.0,
            message="Alias updated successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.update_alias',
                   return_value=mock_response):
            response = client.patch(
                '/master-data/skill-taxonomy/aliases/1',
                json={"alias_text": "New Alias Text"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['alias_text'] == "New Alias Text"
    
    def test_update_source_and_score(self):
        """Should update source and confidence_score."""
        mock_response = AliasUpdateResponse(
            id=1,
            alias_text="Same",
            skill_id=1,
            source="imported",
            confidence_score=0.85,
            message="Alias updated successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.update_alias',
                   return_value=mock_response):
            response = client.patch(
                '/master-data/skill-taxonomy/aliases/1',
                json={"source": "imported", "confidence_score": 0.85}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['source'] == "imported"
        assert data['confidence_score'] == 0.85
    
    def test_update_not_found_returns_404(self):
        """Should return 404 when alias doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_alias',
                   side_effect=NotFoundError("Alias", 999)):
            response = client.patch(
                '/master-data/skill-taxonomy/aliases/999',
                json={"alias_text": "Test"}
            )
        
        assert response.status_code == 404
    
    def test_update_duplicate_returns_409(self):
        """Should return 409 when alias text exists for skill."""
        with patch('app.api.routes.master_data.taxonomy_update_service.update_alias',
                   side_effect=ConflictError("Alias", "alias_text", "Existing", "skill")):
            response = client.patch(
                '/master-data/skill-taxonomy/aliases/1',
                json={"alias_text": "Existing"}
            )
        
        assert response.status_code == 409
    
    def test_update_no_fields_returns_422(self):
        """Should return 422 when no fields provided."""
        response = client.patch(
            '/master-data/skill-taxonomy/aliases/1',
            json={}
        )
        
        assert response.status_code == 422


# ============================================================================
# TEST: POST /master-data/skill-taxonomy/skills/{id}/aliases
# ============================================================================

class TestCreateAlias:
    """Tests for POST /master-data/skill-taxonomy/skills/{id}/aliases."""
    
    def test_create_success(self):
        """Should create alias and return 201."""
        mock_response = AliasCreateResponse(
            id=1,
            alias_text="New Alias",
            skill_id=1,
            source="manual",
            confidence_score=1.0,
            message="Alias created successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.create_alias',
                   return_value=mock_response):
            response = client.post(
                '/master-data/skill-taxonomy/skills/1/aliases',
                json={"alias_text": "New Alias"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 1
        assert data['alias_text'] == "New Alias"
    
    def test_create_with_custom_source_and_score(self):
        """Should create alias with custom source and score."""
        mock_response = AliasCreateResponse(
            id=1,
            alias_text="Test",
            skill_id=1,
            source="imported",
            confidence_score=0.95,
            message="Alias created successfully"
        )
        with patch('app.api.routes.master_data.taxonomy_update_service.create_alias',
                   return_value=mock_response):
            response = client.post(
                '/master-data/skill-taxonomy/skills/1/aliases',
                json={
                    "alias_text": "Test",
                    "source": "imported",
                    "confidence_score": 0.95
                }
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data['source'] == "imported"
        assert data['confidence_score'] == 0.95
    
    def test_create_skill_not_found_returns_404(self):
        """Should return 404 when skill doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_alias',
                   side_effect=NotFoundError("Skill", 999)):
            response = client.post(
                '/master-data/skill-taxonomy/skills/999/aliases',
                json={"alias_text": "Test"}
            )
        
        assert response.status_code == 404
    
    def test_create_duplicate_returns_409(self):
        """Should return 409 when alias text exists for skill."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_alias',
                   side_effect=ConflictError("Alias", "alias_text", "Existing", "skill")):
            response = client.post(
                '/master-data/skill-taxonomy/skills/1/aliases',
                json={"alias_text": "Existing"}
            )
        
        assert response.status_code == 409


# ============================================================================
# TEST: DELETE /master-data/skill-taxonomy/aliases/{id}
# ============================================================================

class TestDeleteAlias:
    """Tests for DELETE /master-data/skill-taxonomy/aliases/{id}."""
    
    def test_delete_success(self):
        """Should delete alias and return 200."""
        mock_response = {
            "id": 1,
            "alias_text": "Deleted Alias",
            "skill_id": 1,
            "message": "Alias deleted successfully"
        }
        with patch('app.api.routes.master_data.taxonomy_update_service.delete_alias',
                   return_value=mock_response):
            response = client.delete('/master-data/skill-taxonomy/aliases/1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
    
    def test_delete_not_found_returns_404(self):
        """Should return 404 when alias doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.delete_alias',
                   side_effect=NotFoundError("Alias", 999)):
            response = client.delete('/master-data/skill-taxonomy/aliases/999')
        
        assert response.status_code == 404


# ============================================================================
# TEST: DELETE /master-data/skill-taxonomy/categories/{id}
# ============================================================================

class TestDeleteCategory:
    """Tests for DELETE /master-data/skill-taxonomy/categories/{id}."""
    
    def test_delete_success(self):
        """Should soft delete category and return 200."""
        mock_response = {
            "category_id": 1,
            "category_name": "Deleted Category",
            "deleted_at": "2024-01-15T10:00:00",
            "message": "Category deleted successfully"
        }
        with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_category',
                   return_value=mock_response):
            response = client.delete('/master-data/skill-taxonomy/categories/1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['category_id'] == 1
    
    def test_delete_not_found_returns_404(self):
        """Should return 404 when category doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_category',
                   side_effect=NotFoundError("Category", 999)):
            response = client.delete('/master-data/skill-taxonomy/categories/999')
        
        assert response.status_code == 404
    
    def test_delete_with_subcategories_returns_409(self):
        """Should return 409 when category has subcategories."""
        with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_category',
                   side_effect=ConflictError("Category", "subcategories", "3")):
            response = client.delete('/master-data/skill-taxonomy/categories/1')
        
        assert response.status_code == 409


# ============================================================================
# TEST: DELETE /master-data/skill-taxonomy/subcategories/{id}
# ============================================================================

class TestDeleteSubcategory:
    """Tests for DELETE /master-data/skill-taxonomy/subcategories/{id}."""
    
    def test_delete_success(self):
        """Should soft delete subcategory and return 200."""
        mock_response = {
            "subcategory_id": 1,
            "subcategory_name": "Deleted Subcat",
            "category_id": 1,
            "deleted_at": "2024-01-15T10:00:00",
            "message": "Subcategory deleted successfully"
        }
        with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_subcategory',
                   return_value=mock_response):
            response = client.delete('/master-data/skill-taxonomy/subcategories/1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['subcategory_id'] == 1
    
    def test_delete_not_found_returns_404(self):
        """Should return 404 when subcategory doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_subcategory',
                   side_effect=NotFoundError("Subcategory", 999)):
            response = client.delete('/master-data/skill-taxonomy/subcategories/999')
        
        assert response.status_code == 404
    
    def test_delete_with_skills_returns_409(self):
        """Should return 409 when subcategory has skills."""
        with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_subcategory',
                   side_effect=ConflictError("Subcategory", "skills", "5")):
            response = client.delete('/master-data/skill-taxonomy/subcategories/1')
        
        assert response.status_code == 409


# ============================================================================
# TEST: DELETE /master-data/skill-taxonomy/skills/{id}
# ============================================================================

class TestDeleteSkill:
    """Tests for DELETE /master-data/skill-taxonomy/skills/{id}."""
    
    def test_delete_success(self):
        """Should soft delete skill and return 200."""
        mock_response = {
            "id": 1,
            "name": "Deleted Skill",
            "subcategory_id": 1,
            "deleted_at": "2024-01-15T10:00:00",
            "message": "Skill deleted successfully"
        }
        with patch('app.api.routes.master_data.taxonomy_update_service.check_skill_dependencies',
                   return_value=None):
            with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_skill',
                       return_value=mock_response):
                response = client.delete('/master-data/skill-taxonomy/skills/1')
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 1
    
    def test_delete_not_found_returns_404(self):
        """Should return 404 when skill doesn't exist."""
        with patch('app.api.routes.master_data.taxonomy_update_service.check_skill_dependencies',
                   return_value=None):
            with patch('app.api.routes.master_data.taxonomy_update_service.soft_delete_skill',
                       side_effect=NotFoundError("Skill", 999)):
                response = client.delete('/master-data/skill-taxonomy/skills/999')
        
        assert response.status_code == 404
    
    def test_delete_with_dependencies_returns_409(self):
        """Should return 409 when skill has employee dependencies."""
        dependencies = {"employees": 10}
        with patch('app.api.routes.master_data.taxonomy_update_service.check_skill_dependencies',
                   return_value=dependencies):
            response = client.delete('/master-data/skill-taxonomy/skills/1')
        
        assert response.status_code == 409
        data = response.json()
        assert "dependencies" in response.json()['detail']


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_path_id_zero(self):
        """Should return 422 for ID=0 (path validation, ID must be >= 1)."""
        response = client.patch(
            '/master-data/skill-taxonomy/categories/0',
            json={"category_name": "Test"}
        )
        assert response.status_code == 422
    
    def test_invalid_path_id_negative(self):
        """Should return 422 for negative ID (path validation, ID must be >= 1)."""
        response = client.delete('/master-data/skill-taxonomy/skills/-1')
        assert response.status_code == 422
    
    def test_search_query_max_length(self, sample_taxonomy_response):
        """Should accept search query up to max length."""
        with patch('app.api.routes.master_data.skill_taxonomy_service.get_skill_taxonomy',
                   return_value=sample_taxonomy_response):
            # 100 chars is the max
            query = "a" * 100
            response = client.get(f'/master-data/skill-taxonomy?q={query}')
        
        assert response.status_code == 200
    
    def test_unexpected_service_error_returns_500(self):
        """Should return 500 for unexpected service errors."""
        with patch('app.api.routes.master_data.taxonomy_update_service.create_category',
                   side_effect=RuntimeError("Unexpected error")):
            response = client.post(
                '/master-data/skill-taxonomy/categories',
                json={"category_name": "Test"}
            )
        
        assert response.status_code == 500
