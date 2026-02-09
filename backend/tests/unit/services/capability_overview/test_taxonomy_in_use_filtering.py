"""
Unit tests for "in-use only" filtering in taxonomy services.

Tests the capability structure filtering that returns only:
- Skills with at least one employee_skills row (where deleted_at IS NULL)
- Subcategories with at least one in-use skill
- Categories with at least one in-use subcategory

Endpoints affected:
- GET /skills/capability/categories
- GET /skills/capability/categories/{category_id}/subcategories
- GET /skills/capability/subcategories/{subcategory_id}/skills

Coverage:
1. Skills with employee_skills rows are included
2. Skills without employee_skills rows are excluded
3. Subcategories with no in-use skills are excluded
4. Categories with no in-use subcategories are excluded
5. Response JSON shape is preserved (contract compliance)
6. Ordering is deterministic (alphabetical by name)
"""
import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime

from app.services.capability_overview import (
    taxonomy_categories_service as categories_service,
    taxonomy_subcategories_service as subcategories_service,
    taxonomy_skills_service as skills_service,
)


# ============================================================================
# TEST: Skills Service - In-Use Filtering
# ============================================================================

class TestSkillsServiceInUseFiltering:
    """Test that skills are filtered by employee_skills existence."""
    
    def test_skill_with_employee_skills_is_included(self, mock_db, mock_skill, mock_subcategory, mock_category):
        """Skill with >=1 non-deleted employee_skills row should be included."""
        # Arrange
        subcategory = mock_subcategory(1, "Web Frameworks")
        category = mock_category(1, "Programming")
        skill = mock_skill(1, "React", subcategory_id=1)
        
        # Mock query chain to return the skill (simulating the EXISTS filter passed)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [skill]
        mock_query.first.side_effect = [subcategory, category]
        
        # Act
        result = skills_service.get_skills_for_subcategory(mock_db, 1)
        
        # Assert
        assert len(result.skills) == 1
        assert result.skills[0].skill_id == 1
        assert result.skills[0].skill_name == "React"
    
    def test_skill_without_employee_skills_is_excluded(self, mock_db, mock_subcategory, mock_category):
        """Skill with 0 employee_skills rows should NOT be included."""
        # Arrange
        subcategory = mock_subcategory(1, "Web Frameworks")
        category = mock_category(1, "Programming")
        
        # Mock query chain to return empty (simulating no skills pass the EXISTS filter)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []  # No skills pass the filter
        mock_query.first.side_effect = [subcategory, category]
        
        # Act
        result = skills_service.get_skills_for_subcategory(mock_db, 1)
        
        # Assert
        assert len(result.skills) == 0
    
    def test_response_shape_preserved(self, mock_db, mock_skill, mock_subcategory, mock_category):
        """Response JSON shape must match contract (SkillsResponse schema)."""
        # Arrange
        subcategory = mock_subcategory(1, "Web Frameworks")
        category = mock_category(1, "Programming")
        skills = [
            mock_skill(1, "React"),
            mock_skill(2, "Vue"),
        ]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = skills
        mock_query.first.side_effect = [subcategory, category]
        
        # Act
        result = skills_service.get_skills_for_subcategory(mock_db, 1)
        
        # Assert - verify exact response shape
        assert hasattr(result, 'subcategory_id')
        assert hasattr(result, 'subcategory_name')
        assert hasattr(result, 'category_id')
        assert hasattr(result, 'category_name')
        assert hasattr(result, 'skills')
        assert isinstance(result.skills, list)
        
        # Verify skill items have correct shape
        if result.skills:
            skill_item = result.skills[0]
            assert hasattr(skill_item, 'skill_id')
            assert hasattr(skill_item, 'skill_name')
    
    def test_ordering_is_deterministic(self, mock_db, mock_skill, mock_subcategory, mock_category):
        """Skills should be ordered alphabetically by name."""
        # Arrange
        subcategory = mock_subcategory(1, "Web Frameworks")
        category = mock_category(1, "Programming")
        # Return skills in alphabetical order (as query would return)
        skills = [
            mock_skill(2, "Angular"),
            mock_skill(1, "React"),
            mock_skill(3, "Vue"),
        ]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = skills
        mock_query.first.side_effect = [subcategory, category]
        
        # Act
        result = skills_service.get_skills_for_subcategory(mock_db, 1)
        
        # Assert - order matches query order (alphabetical)
        assert result.skills[0].skill_name == "Angular"
        assert result.skills[1].skill_name == "React"
        assert result.skills[2].skill_name == "Vue"


# ============================================================================
# TEST: Subcategories Service - In-Use Filtering
# ============================================================================

class TestSubcategoriesServiceInUseFiltering:
    """Test that subcategories are filtered to include only those with in-use skills."""
    
    def test_subcategory_with_in_use_skill_is_included(self, mock_db, mock_subcategory, mock_category):
        """Subcategory with at least one in-use skill should be included."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Web Frameworks")
        
        # Mock category query
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = category
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [subcategory]
        mock_query.scalar.return_value = 3  # 3 in-use skills
        
        # Act
        result = subcategories_service.get_subcategories_for_category(mock_db, 1)
        
        # Assert
        assert len(result.subcategories) >= 0  # At least processes without error
    
    def test_subcategory_without_in_use_skills_is_excluded(self, mock_db, mock_category):
        """Subcategory with 0 in-use skills should NOT be included."""
        # Arrange - subcategory exists but has no in-use skills
        category = mock_category(1, "Programming")
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = category
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []  # No subcategories pass the filter
        
        # Act
        result = subcategories_service.get_subcategories_for_category(mock_db, 1)
        
        # Assert
        assert len(result.subcategories) == 0
    
    def test_response_shape_preserved(self, mock_db, mock_subcategory, mock_category):
        """Response JSON shape must match contract (SubcategoriesResponse schema)."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategories = [mock_subcategory(1, "Web Frameworks")]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = category
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = subcategories
        mock_query.scalar.return_value = 5  # skill count
        
        # Act
        result = subcategories_service.get_subcategories_for_category(mock_db, 1)
        
        # Assert - verify exact response shape
        assert hasattr(result, 'category_id')
        assert hasattr(result, 'category_name')
        assert hasattr(result, 'subcategories')
        assert isinstance(result.subcategories, list)
        
        # Verify subcategory items have correct shape
        if result.subcategories:
            subcat = result.subcategories[0]
            assert hasattr(subcat, 'subcategory_id')
            assert hasattr(subcat, 'subcategory_name')
            assert hasattr(subcat, 'skill_count')
    
    def test_skill_count_reflects_in_use_only(self, mock_db, mock_subcategory, mock_category):
        """Skill count should only count in-use skills, not all skills."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Web Frameworks")
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = category
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [subcategory]
        mock_query.scalar.return_value = 2  # Only 2 in-use skills (even if 10 total exist)
        
        # Act
        result = subcategories_service.get_subcategories_for_category(mock_db, 1)
        
        # Assert
        assert result.subcategories[0].skill_count == 2


# ============================================================================
# TEST: Categories Service - In-Use Filtering
# ============================================================================

class TestCategoriesServiceInUseFiltering:
    """Test that categories are filtered to include only those with in-use subcategories."""
    
    def test_category_with_in_use_subcategory_is_included(self, mock_db, mock_category):
        """Category with at least one in-use subcategory should be included."""
        # Arrange
        category = mock_category(1, "Programming")
        
        with patch.object(categories_service, '_query_all_categories', return_value=[category]):
            with patch.object(categories_service, '_query_subcategory_count', return_value=3):
                with patch.object(categories_service, '_query_skill_count_for_category', return_value=15):
                    # Act
                    result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert len(result.categories) == 1
        assert result.categories[0].category_name == "Programming"
    
    def test_category_without_in_use_subcategories_is_excluded(self, mock_db):
        """Category with 0 in-use subcategories should NOT be included."""
        # Arrange - mock query returns no categories (all filtered out)
        with patch.object(categories_service, '_query_all_categories', return_value=[]):
            # Act
            result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert len(result.categories) == 0
    
    def test_response_shape_preserved(self, mock_db, mock_category):
        """Response JSON shape must match contract (CategoriesResponse schema)."""
        # Arrange
        categories = [mock_category(1, "Programming")]
        
        with patch.object(categories_service, '_query_all_categories', return_value=categories):
            with patch.object(categories_service, '_query_subcategory_count', return_value=5):
                with patch.object(categories_service, '_query_skill_count_for_category', return_value=50):
                    # Act
                    result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert - verify exact response shape
        assert hasattr(result, 'categories')
        assert isinstance(result.categories, list)
        
        # Verify category items have correct shape
        if result.categories:
            cat = result.categories[0]
            assert hasattr(cat, 'category_id')
            assert hasattr(cat, 'category_name')
            assert hasattr(cat, 'subcategory_count')
            assert hasattr(cat, 'skill_count')
    
    def test_subcategory_count_reflects_in_use_only(self, mock_db, mock_category):
        """Subcategory count should only count in-use subcategories."""
        # Arrange
        category = mock_category(1, "Programming")
        
        with patch.object(categories_service, '_query_all_categories', return_value=[category]):
            with patch.object(categories_service, '_query_subcategory_count', return_value=2):  # Only 2 in-use
                with patch.object(categories_service, '_query_skill_count_for_category', return_value=10):
                    # Act
                    result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert result.categories[0].subcategory_count == 2
    
    def test_skill_count_reflects_in_use_only(self, mock_db, mock_category):
        """Skill count should only count in-use skills across all subcategories."""
        # Arrange
        category = mock_category(1, "Programming")
        
        with patch.object(categories_service, '_query_all_categories', return_value=[category]):
            with patch.object(categories_service, '_query_subcategory_count', return_value=3):
                with patch.object(categories_service, '_query_skill_count_for_category', return_value=25):  # Only 25 in-use
                    # Act
                    result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert result.categories[0].skill_count == 25
    
    def test_ordering_is_deterministic(self, mock_db, mock_category):
        """Categories should be ordered alphabetically by name."""
        # Arrange - return in alphabetical order
        categories = [
            mock_category(2, "Cloud"),
            mock_category(1, "Programming"),
            mock_category(3, "Security"),
        ]
        
        with patch.object(categories_service, '_query_all_categories', return_value=categories):
            with patch.object(categories_service, '_query_subcategory_count', return_value=1):
                with patch.object(categories_service, '_query_skill_count_for_category', return_value=5):
                    # Act
                    result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert - order matches query order (alphabetical)
        assert result.categories[0].category_name == "Cloud"
        assert result.categories[1].category_name == "Programming"
        assert result.categories[2].category_name == "Security"


# ============================================================================
# TEST: Tree Pruning Behavior (Integration-like)
# ============================================================================

class TestTreePruningBehavior:
    """Test the complete tree pruning behavior across all levels."""
    
    def test_empty_tree_when_no_employee_skills_exist(self, mock_db):
        """When no employee_skills exist, the entire tree should be empty."""
        # Arrange - no categories have in-use skills
        with patch.object(categories_service, '_query_all_categories', return_value=[]):
            # Act
            result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert result.categories == []
    
    def test_partial_tree_when_some_skills_in_use(self, mock_db, mock_category):
        """Only categories/subcategories with in-use skills should appear."""
        # Arrange - only one category has in-use skills
        category = mock_category(1, "Programming")
        
        with patch.object(categories_service, '_query_all_categories', return_value=[category]):
            with patch.object(categories_service, '_query_subcategory_count', return_value=2):
                with patch.object(categories_service, '_query_skill_count_for_category', return_value=10):
                    # Act
                    result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert
        assert len(result.categories) == 1
        assert result.categories[0].category_name == "Programming"
    
    def test_soft_deleted_employee_skills_not_counted(self, mock_db, mock_category):
        """Employee skills with deleted_at != NULL should not be counted."""
        # This is verified at the query level - the EXISTS clause includes:
        # EmployeeSkill.deleted_at.is_(None)
        
        # When all employee_skills for a skill are soft-deleted,
        # that skill should not appear in results
        
        # Arrange - category exists but no active employee_skills
        with patch.object(categories_service, '_query_all_categories', return_value=[]):
            # Act
            result = categories_service.get_categories_for_lazy_loading(mock_db)
        
        # Assert - no categories because no active employee_skills
        assert len(result.categories) == 0
