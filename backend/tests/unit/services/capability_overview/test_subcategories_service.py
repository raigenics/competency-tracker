"""
Unit tests for capability_overview/subcategories_service.py

Tests GET /skills/subcategories/ endpoint functionality.
Coverage: Query building, filtering, counting, response transformation.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_overview import subcategories_service as service
from app.models import SkillSubcategory, SkillCategory


# ============================================================================
# TEST: get_subcategories (Main Entry Point)
# ============================================================================

class TestGetSubcategories:
    """Test the main get_subcategories function."""
    
    def test_returns_all_subcategories_without_filter(
        self, mock_db, mock_subcategory, mock_category
    ):
        """Should return all subcategories when no category filter provided."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [
            mock_subcategory(1, "Web Dev", category),
            mock_subcategory(2, "Mobile Dev", category)
        ]
        
        with patch.object(service, '_query_subcategories_with_filter', return_value=subcategories):
            with patch.object(service, '_query_skill_count_for_subcategory', return_value=5):
                # Act
                result = service.get_subcategories(mock_db, category=None)
        
        # Assert
        assert len(result) == 2
        assert result[0].subcategory_name == "Web Dev"
        assert result[1].subcategory_name == "Mobile Dev"
    
    def test_returns_filtered_subcategories_when_category_provided(
        self, mock_db, mock_subcategory, mock_category
    ):
        """Should filter subcategories by category name."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategories = [mock_subcategory(1, "ML", category)]
        
        with patch.object(service, '_query_subcategories_with_filter', return_value=subcategories):
            with patch.object(service, '_query_skill_count_for_subcategory', return_value=3):
                # Act
                result = service.get_subcategories(mock_db, category="Data")
        
        # Assert
        assert len(result) == 1
        assert result[0].category_name == "Data Science"
    
    def test_returns_empty_list_when_no_subcategories_found(self, mock_db):
        """Should return empty list when no subcategories match."""
        # Arrange
        with patch.object(service, '_query_subcategories_with_filter', return_value=[]):
            # Act
            result = service.get_subcategories(mock_db, category="NonExistent")
        
        # Assert
        assert result == []
    
    def test_includes_skill_counts_in_response(
        self, mock_db, mock_subcategory, mock_category
    ):
        """Should include skill count for each subcategory."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [mock_subcategory(1, "Backend", category)]
        
        with patch.object(service, '_query_subcategories_with_filter', return_value=subcategories):
            with patch.object(service, '_query_skill_count_for_subcategory', return_value=15):
                # Act
                result = service.get_subcategories(mock_db)
        
        # Assert
        assert result[0].skill_count == 15


# ============================================================================
# TEST: _query_subcategories_with_filter (Query Function)
# ============================================================================

class TestQuerySubcategoriesWithFilter:
    """Test subcategory query building with optional category filter."""
    
    def test_queries_all_subcategories_without_filter(self, mock_db):
        """Should query all subcategories when no filter provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_subcategories_with_filter(mock_db, category=None)
        
        # Assert
        mock_db.query.assert_called_once_with(SkillSubcategory)
        mock_query.options.assert_called_once()
        mock_query.all.assert_called_once()
    
    def test_joins_category_when_filter_provided(self, mock_db):
        """Should join SkillCategory table when category filter provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_subcategories_with_filter(mock_db, category="Programming")
        
        # Assert
        mock_query.join.assert_called_once_with(SkillCategory)
        mock_query.filter.assert_called_once()
    
    def test_applies_case_insensitive_partial_match(self, mock_db):
        """Should apply ilike filter for partial case-insensitive match."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_subcategories_with_filter(mock_db, category="data")
        
        # Assert
        mock_query.filter.assert_called_once()
        # The filter should contain ilike with % wildcards
        filter_call = mock_query.filter.call_args[0][0]
        assert hasattr(filter_call, 'right')
    
    def test_eager_loads_category_relationship(self, mock_db):
        """Should use joinedload for category relationship."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_subcategories_with_filter(mock_db, category=None)
        
        # Assert
        mock_query.options.assert_called_once()


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
        mock_query.scalar.return_value = 10
        
        # Act
        result = service._query_skill_count_for_subcategory(mock_db, subcategory_id=1)
        
        # Assert
        assert result == 10
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_returns_zero_when_no_skills_found(self, mock_db):
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
# TEST: _build_subcategory_responses (Pure Response Building)
# ============================================================================

class TestBuildSubcategoryResponses:
    """Test response building from subcategory models."""
    
    def test_builds_responses_from_subcategories(
        self, mock_db, mock_subcategory, mock_category
    ):
        """Should build SubcategoryResponse list from models."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [
            mock_subcategory(1, "Web Dev", category),
            mock_subcategory(2, "Mobile", category)
        ]
        
        with patch.object(service, '_query_skill_count_for_subcategory', return_value=5):
            # Act
            result = service._build_subcategory_responses(mock_db, subcategories)
        
        # Assert
        assert len(result) == 2
        assert result[0].subcategory_id == 1
        assert result[0].subcategory_name == "Web Dev"
        assert result[1].subcategory_id == 2
        assert result[1].subcategory_name == "Mobile"
    
    def test_includes_category_name_in_response(
        self, mock_db, mock_subcategory, mock_category
    ):
        """Should include parent category name in response."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategories = [mock_subcategory(1, "ML", category)]
        
        with patch.object(service, '_query_skill_count_for_subcategory', return_value=3):
            # Act
            result = service._build_subcategory_responses(mock_db, subcategories)
        
        # Assert
        assert result[0].category_name == "Data Science"
    
    def test_queries_skill_count_for_each_subcategory(
        self, mock_db, mock_subcategory, mock_category
    ):
        """Should query skill count for each subcategory."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [
            mock_subcategory(1, "Backend", category),
            mock_subcategory(2, "Frontend", category)
        ]
        
        with patch.object(service, '_query_skill_count_for_subcategory', side_effect=[10, 15]) as mock_count:
            # Act
            result = service._build_subcategory_responses(mock_db, subcategories)
        
        # Assert
        assert mock_count.call_count == 2
        assert result[0].skill_count == 10
        assert result[1].skill_count == 15
    
    def test_handles_empty_subcategory_list(self, mock_db):
        """Should return empty list for empty input."""
        # Act
        result = service._build_subcategory_responses(mock_db, [])
        
        # Assert
        assert result == []
    
    def test_handles_zero_skill_count(
        self, mock_db, mock_subcategory, mock_category
    ):
        """Should handle subcategories with no skills."""
        # Arrange
        category = mock_category(1, "New Category")
        subcategories = [mock_subcategory(1, "Empty Subcat", category)]
        
        with patch.object(service, '_query_skill_count_for_subcategory', return_value=0):
            # Act
            result = service._build_subcategory_responses(mock_db, subcategories)
        
        # Assert
        assert result[0].skill_count == 0
