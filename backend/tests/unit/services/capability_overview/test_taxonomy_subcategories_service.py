"""
Unit tests for capability_overview/taxonomy_subcategories_service.py

Tests GET /skills/capability/categories/{category_id}/subcategories endpoint.
Coverage: Lazy-loading subcategory expansion with skill counts.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_overview import taxonomy_subcategories_service as service
from app.models import SkillCategory, SkillSubcategory


# ============================================================================
# TEST: get_subcategories_for_category (Main Entry Point)
# ============================================================================

class TestGetSubcategoriesForCategory:
    """Test the main subcategories query function."""
    
    def test_returns_subcategories_for_valid_category(
        self, mock_db, mock_category, mock_subcategory
    ):
        """Should return subcategories with skill counts for valid category."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [
            mock_subcategory(1, "Backend"),
            mock_subcategory(2, "Frontend")
        ]
        
        with patch.object(service, '_query_category_by_id', return_value=category):
            with patch.object(service, '_query_subcategories_for_category', return_value=subcategories):
                with patch.object(service, '_query_skill_count_for_subcategory', return_value=10):
                    # Act
                    result = service.get_subcategories_for_category(mock_db, category_id=1)
        
        # Assert
        assert result.category_id == 1
        assert result.category_name == "Programming"
        assert len(result.subcategories) == 2
        assert result.subcategories[0].subcategory_name == "Backend"
        assert result.subcategories[1].subcategory_name == "Frontend"
    
    def test_raises_error_when_category_not_found(self, mock_db):
        """Should raise ValueError when category ID doesn't exist."""
        # Arrange
        with patch.object(service, '_query_category_by_id', return_value=None):
            # Act & Assert
            with pytest.raises(ValueError, match="Category 999 not found"):
                service.get_subcategories_for_category(mock_db, category_id=999)
    
    def test_includes_skill_counts_for_each_subcategory(
        self, mock_db, mock_category, mock_subcategory
    ):
        """Should include skill count for each subcategory."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategories = [mock_subcategory(1, "ML")]
        
        with patch.object(service, '_query_category_by_id', return_value=category):
            with patch.object(service, '_query_subcategories_for_category', return_value=subcategories):
                with patch.object(service, '_query_skill_count_for_subcategory', return_value=25):
                    # Act
                    result = service.get_subcategories_for_category(mock_db, category_id=1)
        
        # Assert
        assert result.subcategories[0].skill_count == 25
    
    def test_returns_empty_subcategories_when_category_has_none(
        self, mock_db, mock_category
    ):
        """Should return empty subcategories list when category has no subcategories."""
        # Arrange
        category = mock_category(1, "Empty Category")
        
        with patch.object(service, '_query_category_by_id', return_value=category):
            with patch.object(service, '_query_subcategories_for_category', return_value=[]):
                # Act
                result = service.get_subcategories_for_category(mock_db, category_id=1)
        
        # Assert
        assert result.subcategories == []
        assert result.category_name == "Empty Category"


# ============================================================================
# TEST: _query_category_by_id (Query Function)
# ============================================================================

class TestQueryCategoryById:
    """Test category query by ID."""
    
    def test_queries_category_by_id(self, mock_db):
        """Should query category by ID."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(category_id=1, category_name="Test")
        
        # Act
        result = service._query_category_by_id(mock_db, category_id=1)
        
        # Assert
        mock_db.query.assert_called_once_with(SkillCategory)
        mock_query.filter.assert_called_once()
        mock_query.first.assert_called_once()
        assert result.category_id == 1
    
    def test_returns_none_when_category_not_found(self, mock_db):
        """Should return None when category ID doesn't exist."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Act
        result = service._query_category_by_id(mock_db, category_id=999)
        
        # Assert
        assert result is None


# ============================================================================
# TEST: _query_subcategories_for_category (Query Function)
# ============================================================================

class TestQuerySubcategoriesForCategory:
    """Test subcategories query for a category."""
    
    def test_queries_subcategories_for_category(self, mock_db):
        """Should query subcategories filtered by category_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_subcategories_for_category(mock_db, category_id=1)
        
        # Assert
        mock_db.query.assert_called_once_with(SkillSubcategory)
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()
    
    def test_orders_subcategories_by_name(self, mock_db):
        """Should order subcategories alphabetically by name."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_subcategories_for_category(mock_db, category_id=1)
        
        # Assert
        mock_query.order_by.assert_called_once()
    
    def test_returns_all_subcategories_for_category(
        self, mock_db, mock_category, mock_subcategory
    ):
        """Should return all subcategories that pass the in-use filter."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [
            mock_subcategory(1, "Backend"),
            mock_subcategory(2, "Frontend"),
            mock_subcategory(3, "Mobile")
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = subcategories
        
        # Act
        result = service._query_subcategories_for_category(mock_db, category_id=1)
        
        # Assert
        assert len(result) == 3
        assert result[0].subcategory_name == "Backend"


# ============================================================================
# TEST: _query_skill_count_for_subcategory (Count Query)
# ============================================================================

class TestQuerySkillCountForSubcategory:
    """Test skill count query for a subcategory."""
    
    def test_returns_skill_count_for_subcategory(self, mock_db):
        """Should return count of skills in subcategory."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15
        
        # Act
        result = service._query_skill_count_for_subcategory(mock_db, subcategory_id=1)
        
        # Assert
        assert result == 15
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_returns_zero_when_no_skills(self, mock_db):
        """Should return 0 when subcategory has no skills."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_skill_count_for_subcategory(mock_db, subcategory_id=999)
        
        # Assert
        assert result == 0
    
    def test_filters_by_subcategory_id(self, mock_db):
        """Should filter skills by subcategory_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        
        # Act
        service._query_skill_count_for_subcategory(mock_db, subcategory_id=42)
        
        # Assert
        mock_query.filter.assert_called_once()


# ============================================================================
# TEST: _build_subcategory_summary_items (Response Building)
# ============================================================================

class TestBuildSubcategorySummaryItems:
    """Test subcategory summary item building."""
    
    def test_builds_summary_items_from_subcategories(
        self, mock_db, mock_category, mock_subcategory
    ):
        """Should build SubcategorySummaryItem list from subcategories."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [
            mock_subcategory(1, "Backend"),
            mock_subcategory(2, "Frontend")
        ]
        
        with patch.object(service, '_query_skill_count_for_subcategory', side_effect=[20, 15]):
            # Act
            result = service._build_subcategory_summary_items(mock_db, subcategories)
        
        # Assert
        assert len(result) == 2
        assert result[0].subcategory_id == 1
        assert result[0].subcategory_name == "Backend"
        assert result[0].skill_count == 20
        assert result[1].subcategory_id == 2
        assert result[1].skill_count == 15
    
    def test_queries_skill_count_for_each_subcategory(
        self, mock_db, mock_category, mock_subcategory
    ):
        """Should query skill count for each subcategory."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategories = [
            mock_subcategory(1, "ML"),
            mock_subcategory(2, "AI"),
            mock_subcategory(3, "Analytics")
        ]
        
        with patch.object(service, '_query_skill_count_for_subcategory', side_effect=[10, 12, 8]) as mock_count:
            # Act
            result = service._build_subcategory_summary_items(mock_db, subcategories)
        
        # Assert
        assert mock_count.call_count == 3
        assert result[0].skill_count == 10
        assert result[1].skill_count == 12
        assert result[2].skill_count == 8
    
    def test_handles_empty_subcategories_list(self, mock_db):
        """Should return empty list for empty subcategories input."""
        # Act
        result = service._build_subcategory_summary_items(mock_db, [])
        
        # Assert
        assert result == []
    
    def test_handles_subcategories_with_zero_skills(
        self, mock_db, mock_category, mock_subcategory
    ):
        """Should handle subcategories with no skills (now excluded due to in-use filter)."""
        # Note: With in-use filtering, subcategories with 0 skills are typically
        # excluded at the query level. This test verifies the builder handles 
        # edge cases correctly if such data somehow arrives.
        # Arrange
        category = mock_category(1, "New Category")
        subcategories = [mock_subcategory(1, "Empty Subcat")]
        
        with patch.object(service, '_query_skill_count_for_subcategory', return_value=0):
            # Act
            result = service._build_subcategory_summary_items(mock_db, subcategories)
        
        # Assert
        assert len(result) == 1
        assert result[0].skill_count == 0
