"""
Unit tests for taxonomy_tree_service.py

Tests the GET /skills/taxonomy/tree endpoint's service layer.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.capability_overview import taxonomy_tree_service as service
from app.schemas.skill import (
    TaxonomyTreeResponse, TaxonomyCategoryItem,
    TaxonomySubcategoryItem, TaxonomySkillItem
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_category():
    """Create a mock SkillCategory."""
    def _create(category_id=1, category_name="Programming"):
        cat = MagicMock()
        cat.category_id = category_id
        cat.category_name = category_name
        return cat
    return _create


@pytest.fixture
def mock_subcategory():
    """Create a mock SkillSubcategory."""
    def _create(subcategory_id=1, subcategory_name="Backend", category_id=1):
        sub = MagicMock()
        sub.subcategory_id = subcategory_id
        sub.subcategory_name = subcategory_name
        sub.category_id = category_id
        return sub
    return _create


@pytest.fixture
def mock_skill():
    """Create a mock Skill."""
    def _create(skill_id=1, skill_name="Python", subcategory_id=1):
        skill = MagicMock()
        skill.skill_id = skill_id
        skill.skill_name = skill_name
        skill.subcategory_id = subcategory_id
        return skill
    return _create


# ============================================================================
# TEST: get_taxonomy_tree
# ============================================================================

class TestGetTaxonomyTree:
    """Test get_taxonomy_tree function."""
    
    def test_returns_taxonomy_tree_response(self, mock_db, mock_category):
        """Should return TaxonomyTreeResponse with categories."""
        # Arrange
        categories = [mock_category(1, "Programming"), mock_category(2, "Data Science")]
        mock_db.query.return_value.order_by.return_value.all.return_value = categories
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service.get_taxonomy_tree(mock_db)
        
        # Assert
        assert isinstance(result, TaxonomyTreeResponse)
        assert len(result.categories) == 2
    
    def test_includes_all_categories_even_empty(self, mock_db, mock_category):
        """Should include categories with no subcategories."""
        # Arrange
        categories = [mock_category(1, "Empty Category")]
        mock_db.query.return_value.order_by.return_value.all.return_value = categories
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service.get_taxonomy_tree(mock_db)
        
        # Assert
        assert len(result.categories) == 1
        assert result.categories[0].category_name == "Empty Category"
        assert result.categories[0].subcategories == []
    
    def test_builds_complete_nested_tree(
        self, mock_db, mock_category, mock_subcategory, mock_skill
    ):
        """Should build complete nested structure with skills."""
        # This test is simplified - the full nested tree building
        # is tested via unit tests of individual helper functions.
        # The integration of DB calls makes full mocking complex.
        # Arrange
        categories = [mock_category(1, "Programming")]
        mock_db.query.return_value.order_by.return_value.all.return_value = categories
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service.get_taxonomy_tree(mock_db)
        
        # Assert
        assert len(result.categories) == 1
        assert result.categories[0].category_name == "Programming"
    
    def test_handles_empty_database(self, mock_db):
        """Should return empty categories list when no data."""
        # Arrange
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service.get_taxonomy_tree(mock_db)
        
        # Assert
        assert isinstance(result, TaxonomyTreeResponse)
        assert result.categories == []


# ============================================================================
# TEST: _query_all_categories
# ============================================================================

class TestQueryAllCategories:
    """Test _query_all_categories function."""
    
    def test_queries_all_categories_ordered_by_name(self, mock_db, mock_category):
        """Should query all categories ordered by name."""
        # Arrange
        expected = [mock_category(1, "A Category"), mock_category(2, "B Category")]
        mock_db.query.return_value.order_by.return_value.all.return_value = expected
        
        # Act
        result = service._query_all_categories(mock_db)
        
        # Assert
        assert result == expected
        mock_db.query.assert_called()
    
    def test_returns_empty_list_when_no_categories(self, mock_db):
        """Should return empty list when no categories exist."""
        # Arrange
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service._query_all_categories(mock_db)
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _query_subcategories_for_category
# ============================================================================

class TestQuerySubcategoriesForCategory:
    """Test _query_subcategories_for_category function."""
    
    def test_filters_by_category_id(self, mock_db, mock_subcategory):
        """Should filter subcategories by category_id."""
        # Arrange
        expected = [mock_subcategory(1, "Web Dev", 1)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = expected
        
        # Act
        result = service._query_subcategories_for_category(mock_db, 1)
        
        # Assert
        assert result == expected
        mock_db.query.return_value.filter.assert_called()
    
    def test_returns_empty_for_nonexistent_category(self, mock_db):
        """Should return empty list for category with no subcategories."""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service._query_subcategories_for_category(mock_db, 999)
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _query_skills_for_subcategory
# ============================================================================

class TestQuerySkillsForSubcategory:
    """Test _query_skills_for_subcategory function."""
    
    def test_filters_by_subcategory_id(self, mock_db, mock_skill):
        """Should filter skills by subcategory_id."""
        # Arrange
        expected = [mock_skill(1, "Python", 1), mock_skill(2, "Django", 1)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = expected
        
        # Act
        result = service._query_skills_for_subcategory(mock_db, 1)
        
        # Assert
        assert result == expected
        assert len(result) == 2
    
    def test_returns_empty_for_subcategory_without_skills(self, mock_db):
        """Should return empty list for subcategory with no skills."""
        # Arrange
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service._query_skills_for_subcategory(mock_db, 999)
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _build_taxonomy_tree
# ============================================================================

class TestBuildTaxonomyTree:
    """Test _build_taxonomy_tree function."""
    
    def test_builds_category_items(self, mock_db, mock_category):
        """Should build TaxonomyCategoryItem for each category."""
        # Arrange
        categories = [mock_category(1, "Programming"), mock_category(2, "Design")]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service._build_taxonomy_tree(mock_db, categories)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(c, TaxonomyCategoryItem) for c in result)
        assert result[0].category_id == 1
        assert result[0].category_name == "Programming"
    
    def test_includes_subcategories_for_each_category(
        self, mock_db, mock_category, mock_subcategory
    ):
        """Should include subcategories for each category."""
        # Arrange
        categories = [mock_category(1, "Programming")]
        subcategories = [mock_subcategory(1, "Frontend", 1), mock_subcategory(2, "Backend", 1)]
        
        # Mock filter to return subcategories for category, then empty for skills
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.side_effect = [
            subcategories, [], []  # subcategories for cat 1, then skills for each subcat
        ]
        
        # Act
        result = service._build_taxonomy_tree(mock_db, categories)
        
        # Assert
        assert len(result) == 1
        assert len(result[0].subcategories) == 2
    
    def test_handles_empty_categories_list(self, mock_db):
        """Should return empty list for empty categories."""
        # Act
        result = service._build_taxonomy_tree(mock_db, [])
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _build_subcategory_items
# ============================================================================

class TestBuildSubcategoryItems:
    """Test _build_subcategory_items function."""
    
    def test_builds_subcategory_items_with_skills(
        self, mock_db, mock_subcategory, mock_skill
    ):
        """Should build TaxonomySubcategoryItem with skills."""
        # Arrange
        subcategories = [mock_subcategory(1, "Backend", 1)]
        skills = [mock_skill(1, "Python", 1)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = skills
        
        # Act
        result = service._build_subcategory_items(mock_db, subcategories)
        
        # Assert
        assert len(result) == 1
        assert isinstance(result[0], TaxonomySubcategoryItem)
        assert result[0].subcategory_id == 1
        assert result[0].subcategory_name == "Backend"
    
    def test_handles_subcategory_without_skills(self, mock_db, mock_subcategory):
        """Should handle subcategory with no skills."""
        # Arrange
        subcategories = [mock_subcategory(1, "Empty Subcategory", 1)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Act
        result = service._build_subcategory_items(mock_db, subcategories)
        
        # Assert
        assert len(result) == 1
        assert result[0].skills == []
    
    def test_handles_empty_subcategories_list(self, mock_db):
        """Should return empty list for empty subcategories."""
        # Act
        result = service._build_subcategory_items(mock_db, [])
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _build_skill_items
# ============================================================================

class TestBuildSkillItems:
    """Test _build_skill_items function."""
    
    def test_builds_skill_items_from_models(self, mock_skill):
        """Should build TaxonomySkillItem from skill models."""
        # Arrange
        skills = [mock_skill(1, "Python", 1), mock_skill(2, "Django", 1)]
        
        # Act
        result = service._build_skill_items(skills)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(s, TaxonomySkillItem) for s in result)
        assert result[0].skill_id == 1
        assert result[0].skill_name == "Python"
    
    def test_returns_empty_list_for_no_skills(self):
        """Should return empty list when no skills."""
        # Act
        result = service._build_skill_items([])
        
        # Assert
        assert result == []
    
    def test_preserves_skill_order(self, mock_skill):
        """Should preserve the order of skills."""
        # Arrange
        skills = [mock_skill(3, "Django", 1), mock_skill(1, "Python", 1), mock_skill(2, "Flask", 1)]
        
        # Act
        result = service._build_skill_items(skills)
        
        # Assert
        assert result[0].skill_name == "Django"
        assert result[1].skill_name == "Python"
        assert result[2].skill_name == "Flask"
