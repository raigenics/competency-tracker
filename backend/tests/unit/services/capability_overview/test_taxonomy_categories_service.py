"""
Unit tests for capability_overview/taxonomy_categories_service.py

Tests GET /skills/capability/categories endpoint functionality.
Coverage: Lazy-loading category list with counts, no subcategories/skills loaded.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_overview import taxonomy_categories_service as service
from app.models import SkillCategory


# ============================================================================
# TEST: get_categories_for_lazy_loading (Main Entry Point)
# ============================================================================

class TestGetCategoriesForLazyLoading:
    """Test the main lazy-loading categories function."""
    
    def test_returns_all_categories_with_counts(
        self, mock_db, mock_category
    ):
        """Should return all categories with subcategory and skill counts."""
        # Arrange
        categories = [
            mock_category(1, "Programming"),
            mock_category(2, "Data Science")
        ]
        
        with patch.object(service, '_query_all_categories', return_value=categories):
            with patch.object(service, '_query_subcategory_count', side_effect=[5, 3]):
                with patch.object(service, '_query_skill_count_for_category', side_effect=[50, 30]):
                    # Act
                    result = service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert len(result.categories) == 2
        assert result.categories[0].category_name == "Programming"
        assert result.categories[0].subcategory_count == 5
        assert result.categories[0].skill_count == 50
        assert result.categories[1].category_name == "Data Science"
        assert result.categories[1].subcategory_count == 3
        assert result.categories[1].skill_count == 30
    
    def test_returns_empty_list_when_no_categories(self, mock_db):
        """Should return empty categories list when no categories exist."""
        # Arrange
        with patch.object(service, '_query_all_categories', return_value=[]):
            # Act
            result = service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert result.categories == []
    
    def test_includes_categories_with_zero_counts(
        self, mock_db, mock_category
    ):
        """Should include categories with zero subcategories or skills."""
        # Arrange
        categories = [mock_category(1, "New Category")]
        
        with patch.object(service, '_query_all_categories', return_value=categories):
            with patch.object(service, '_query_subcategory_count', return_value=0):
                with patch.object(service, '_query_skill_count_for_category', return_value=0):
                    # Act
                    result = service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert len(result.categories) == 1
        assert result.categories[0].subcategory_count == 0
        assert result.categories[0].skill_count == 0
    
    def test_does_not_load_subcategories_or_skills(
        self, mock_db, mock_category
    ):
        """Should only return counts, not actual subcategory/skill objects (lazy loading)."""
        # Arrange
        categories = [mock_category(1, "Programming")]
        
        with patch.object(service, '_query_all_categories', return_value=categories):
            with patch.object(service, '_query_subcategory_count', return_value=10):
                with patch.object(service, '_query_skill_count_for_category', return_value=100):
                    # Act
                    result = service.get_categories_for_lazy_loading(mock_db)
        
        # Assert - only has counts, not lists of subcategories/skills
        category_item = result.categories[0]
        assert hasattr(category_item, 'subcategory_count')
        assert hasattr(category_item, 'skill_count')
        assert category_item.subcategory_count == 10
        assert category_item.skill_count == 100


# ============================================================================
# TEST: _query_all_categories (Query Function)
# ============================================================================

class TestQueryAllCategories:
    """Test category query."""
    
    def test_queries_all_categories(self, mock_db):
        """Should query all categories."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_all_categories(mock_db)
        
        # Assert
        mock_db.query.assert_called_once_with(SkillCategory)
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()
    
    def test_orders_categories_by_name(self, mock_db):
        """Should order categories alphabetically by name."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_all_categories(mock_db)
        
        # Assert
        mock_query.order_by.assert_called_once()
    
    def test_returns_all_categories(self, mock_db, mock_category):
        """Should return all categories from database."""
        # Arrange
        categories = [
            mock_category(1, "Category A"),
            mock_category(2, "Category B"),
            mock_category(3, "Category C")
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = categories
        
        # Act
        result = service._query_all_categories(mock_db)
        
        # Assert
        assert len(result) == 3
        assert result[0].category_name == "Category A"


# ============================================================================
# TEST: _query_subcategory_count (Subcategory Count Query)
# ============================================================================

class TestQuerySubcategoryCount:
    """Test subcategory count query."""
    
    def test_returns_subcategory_count_for_category(self, mock_db):
        """Should return count of subcategories in a category."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 8
        
        # Act
        result = service._query_subcategory_count(mock_db, category_id=1)
        
        # Assert
        assert result == 8
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_returns_zero_when_no_subcategories(self, mock_db):
        """Should return 0 when category has no subcategories."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_subcategory_count(mock_db, category_id=999)
        
        # Assert
        assert result == 0
    
    def test_filters_by_category_id(self, mock_db):
        """Should filter subcategories by category_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3
        
        # Act
        service._query_subcategory_count(mock_db, category_id=5)
        
        # Assert
        mock_query.filter.assert_called_once()


# ============================================================================
# TEST: _query_skill_count_for_category (Skill Count Query)
# ============================================================================

class TestQuerySkillCountForCategory:
    """Test skill count query for a category."""
    
    def test_returns_skill_count_for_category(self, mock_db):
        """Should return count of skills in category."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 45
        
        # Act
        result = service._query_skill_count_for_category(mock_db, category_id=1)
        
        # Assert
        assert result == 45
        mock_query.join.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_returns_zero_when_no_skills(self, mock_db):
        """Should return 0 when category has no skills."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_skill_count_for_category(mock_db, category_id=999)
        
        # Assert
        assert result == 0
    
    def test_joins_subcategory_table(self, mock_db):
        """Should join SkillSubcategory to access category_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 10
        
        # Act
        service._query_skill_count_for_category(mock_db, category_id=1)
        
        # Assert
        mock_query.join.assert_called_once()
    
    def test_filters_by_category_id(self, mock_db):
        """Should filter skills by category_id via subcategory join."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 20
        
        # Act
        service._query_skill_count_for_category(mock_db, category_id=3)
        
        # Assert
        mock_query.filter.assert_called_once()


# ============================================================================
# TEST: _build_category_summary_items (Response Building)
# ============================================================================

class TestBuildCategorySummaryItems:
    """Test category summary item building."""
    
    def test_builds_summary_items_from_categories(
        self, mock_db, mock_category
    ):
        """Should build CategorySummaryItem list from categories."""
        # Arrange
        categories = [
            mock_category(1, "Programming"),
            mock_category(2, "Data Science")
        ]
        
        with patch.object(service, '_query_subcategory_count', side_effect=[5, 3]):
            with patch.object(service, '_query_skill_count_for_category', side_effect=[50, 30]):
                # Act
                result = service._build_category_summary_items(mock_db, categories)
        
        # Assert
        assert len(result) == 2
        assert result[0].category_id == 1
        assert result[0].category_name == "Programming"
        assert result[0].subcategory_count == 5
        assert result[0].skill_count == 50
        assert result[1].category_id == 2
        assert result[1].category_name == "Data Science"
    
    def test_queries_counts_for_each_category(
        self, mock_db, mock_category
    ):
        """Should query subcategory and skill counts for each category."""
        # Arrange
        categories = [
            mock_category(1, "Cat 1"),
            mock_category(2, "Cat 2"),
            mock_category(3, "Cat 3")
        ]
        
        with patch.object(service, '_query_subcategory_count', side_effect=[1, 2, 3]) as mock_subcat:
            with patch.object(service, '_query_skill_count_for_category', side_effect=[10, 20, 30]) as mock_skill:
                # Act
                result = service._build_category_summary_items(mock_db, categories)
        
        # Assert
        assert mock_subcat.call_count == 3
        assert mock_skill.call_count == 3
        assert result[0].subcategory_count == 1
        assert result[1].skill_count == 20
    
    def test_handles_empty_category_list(self, mock_db):
        """Should return empty list for empty category input."""
        # Act
        result = service._build_category_summary_items(mock_db, [])
        
        # Assert
        assert result == []
    
    def test_handles_categories_with_zero_counts(
        self, mock_db, mock_category
    ):
        """Should handle categories with zero subcategories or skills."""
        # Arrange
        categories = [mock_category(1, "Empty Category")]
        
        with patch.object(service, '_query_subcategory_count', return_value=0):
            with patch.object(service, '_query_skill_count_for_category', return_value=0):
                # Act
                result = service._build_category_summary_items(mock_db, categories)
        
        # Assert
        assert len(result) == 1
        assert result[0].subcategory_count == 0
        assert result[0].skill_count == 0
