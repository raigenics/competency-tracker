"""
Unit tests for capability_overview/categories_service.py

Tests skill category listing with counts.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import categories_service
from app.schemas.skill import CategoryResponse


class TestGetCategories:
    """Test the main public function get_categories()."""
    
    def test_returns_list_of_categories(self, mock_db, mock_category):
        """Should return list of CategoryResponse objects."""
        # Arrange
        categories = [mock_category(1, "Programming"), mock_category(2, "Database")]
        
        with patch.object(categories_service, '_query_all_categories', return_value=categories), \
             patch.object(categories_service, '_build_category_responses', return_value=[]):
            
            # Act
            result = categories_service.get_categories(mock_db)
            
            # Assert
            assert isinstance(result, list)
    
    def test_calls_query_and_build_functions(self, mock_db, mock_category):
        """Should call query and build functions."""
        # Arrange
        categories = [mock_category(1, "Programming")]
        
        with patch.object(categories_service, '_query_all_categories', return_value=categories) as mock_query, \
             patch.object(categories_service, '_build_category_responses', return_value=[]) as mock_build:
            
            # Act
            categories_service.get_categories(mock_db)
            
            # Assert
            mock_query.assert_called_once_with(mock_db)
            mock_build.assert_called_once_with(mock_db, categories)
    
    def test_returns_empty_list_when_no_categories(self, mock_db):
        """Should return empty list when no categories exist."""
        # Arrange
        with patch.object(categories_service, '_query_all_categories', return_value=[]), \
             patch.object(categories_service, '_build_category_responses', return_value=[]):
            
            # Act
            result = categories_service.get_categories(mock_db)
            
            # Assert
            assert result == []


class TestQueryAllCategories:
    """Test the _query_all_categories() function."""
    
    def test_queries_all_categories(self, mock_db, mock_category):
        """Should query all categories from database."""
        # Arrange
        expected = [mock_category(1, "Programming"), mock_category(2, "Database")]
        mock_db.query.return_value.all.return_value = expected
        
        # Act
        result = categories_service._query_all_categories(mock_db)
        
        # Assert
        mock_db.query.assert_called_once()
        assert result == expected
    
    def test_returns_empty_list_when_no_categories(self, mock_db):
        """Should return empty list when no categories exist."""
        # Arrange
        mock_db.query.return_value.all.return_value = []
        
        # Act
        result = categories_service._query_all_categories(mock_db)
        
        # Assert
        assert result == []


class TestQuerySkillCountForCategory:
    """Test the _query_skill_count_for_category() function."""
    
    def test_returns_skill_count_for_category(self, mock_db):
        """Should return count of skills in category."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 25
        
        # Act
        result = categories_service._query_skill_count_for_category(mock_db, category_id=1)
        
        # Assert
        assert result == 25
    
    def test_returns_zero_when_no_skills(self, mock_db):
        """Should return 0 when category has no skills."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = categories_service._query_skill_count_for_category(mock_db, category_id=1)
        
        # Assert
        assert result == 0
    
    def test_joins_with_subcategories(self, mock_db):
        """Should join with SkillSubcategory table."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        
        # Act
        categories_service._query_skill_count_for_category(mock_db, category_id=1)
        
        # Assert
        mock_query.join.assert_called_once()
        mock_query.filter.assert_called_once()


class TestQuerySubcategoryCountForCategory:
    """Test the _query_subcategory_count_for_category() function."""
    
    def test_returns_subcategory_count_for_category(self, mock_db):
        """Should return count of subcategories in category."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        
        # Act
        result = categories_service._query_subcategory_count_for_category(mock_db, category_id=1)
        
        # Assert
        assert result == 5
    
    def test_returns_zero_when_no_subcategories(self, mock_db):
        """Should return 0 when category has no subcategories."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = categories_service._query_subcategory_count_for_category(mock_db, category_id=1)
        
        # Assert
        assert result == 0


class TestBuildCategoryResponses:
    """Test the _build_category_responses() function."""
    
    def test_builds_response_list_from_categories(self, mock_db, mock_category):
        """Should transform category objects to CategoryResponse list."""
        # Arrange
        categories = [
            mock_category(1, "Programming"),
            mock_category(2, "Database")
        ]
        
        with patch.object(categories_service, '_query_skill_count_for_category', return_value=20), \
             patch.object(categories_service, '_query_subcategory_count_for_category', return_value=5):
            
            # Act
            result = categories_service._build_category_responses(mock_db, categories)
            
            # Assert
            assert len(result) == 2
            assert all(isinstance(r, CategoryResponse) for r in result)
    
    def test_queries_counts_for_each_category(self, mock_db, mock_category):
        """Should call count functions for each category."""
        # Arrange
        categories = [mock_category(1), mock_category(2)]
        
        with patch.object(categories_service, '_query_skill_count_for_category', return_value=0) as mock_skill, \
             patch.object(categories_service, '_query_subcategory_count_for_category', return_value=0) as mock_sub:
            
            # Act
            categories_service._build_category_responses(mock_db, categories)
            
            # Assert
            assert mock_skill.call_count == 2
            assert mock_sub.call_count == 2
    
    def test_returns_empty_list_for_empty_input(self, mock_db):
        """Should return empty list when given empty category list."""
        # Act
        result = categories_service._build_category_responses(mock_db, [])
        
        # Assert
        assert result == []
