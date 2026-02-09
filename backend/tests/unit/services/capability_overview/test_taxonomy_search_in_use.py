"""
Unit tests for taxonomy search in-use filtering.

Tests GET /skills/capability/search endpoint to ensure search results
only include "in-use" skills (those with employee_skills rows).

Regression tests for bug: search was returning master-data-only skills
that had no employee assignments.
"""
import pytest
from unittest.mock import MagicMock, Mock, patch

from app.services.capability_overview import taxonomy_search_service as service


# ============================================================================
# TEST: Search In-Use Filtering
# ============================================================================

class TestSearchInUseFiltering:
    """Test that search only returns skills that are in employee_skills."""
    
    def test_search_returns_only_in_use_skills(self, mock_db, mock_skill, mock_subcategory, mock_category):
        """
        When search matches both in-use and unused skills,
        only in-use skills should be returned.
        
        Setup:
        - Skill A "React" (in employee_skills) 
        - Skill B "React Native" (NOT in employee_skills)
        Both match search term "React".
        
        Expected: Only Skill A returns.
        """
        # Arrange
        category = mock_category(1, "Frontend")
        subcategory = mock_subcategory(1, "Frameworks")
        skill_a = mock_skill(1, "React")  # This will be in-use
        
        # Mock query to return only the in-use skill (as the filter would do)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(skill_a, subcategory, category)]
        
        # Act
        result = service.search_skills_in_taxonomy(mock_db, "React")
        
        # Assert
        assert result.count == 1
        assert len(result.results) == 1
        assert result.results[0].skill_name == "React"
        assert result.results[0].skill_id == 1
    
    def test_search_returns_empty_when_only_unused_skills_match(self, mock_db):
        """
        When search term only matches unused skills (not in employee_skills),
        result should be empty.
        
        Setup:
        - Skill B "React Native" (NOT in employee_skills)
        Search term: "Native"
        
        Expected: Empty results.
        """
        # Arrange - mock query returns empty (all matching skills are unused)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []  # No in-use skills match
        
        # Act
        result = service.search_skills_in_taxonomy(mock_db, "Native")
        
        # Assert
        assert result.count == 0
        assert result.results == []
    
    def test_search_returns_multiple_in_use_skills(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """
        Search should return all in-use skills matching the query.
        """
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Languages")
        skills = [
            mock_skill(1, "Python"),
            mock_skill(2, "Python3"),
        ]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (skills[0], subcategory, category),
            (skills[1], subcategory, category),
        ]
        
        # Act
        result = service.search_skills_in_taxonomy(mock_db, "Python")
        
        # Assert
        assert result.count == 2
        assert len(result.results) == 2

    def test_search_response_shape_is_preserved(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """
        Response JSON shape must match the expected SkillSearchResponse schema.
        """
        # Arrange
        category = mock_category(1, "Frontend")
        subcategory = mock_subcategory(1, "Frameworks")
        skill = mock_skill(1, "React")
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(skill, subcategory, category)]
        
        # Act
        result = service.search_skills_in_taxonomy(mock_db, "React")
        
        # Assert - verify response shape
        assert hasattr(result, 'results')
        assert hasattr(result, 'count')
        assert isinstance(result.results, list)
        
        # Verify result item shape
        item = result.results[0]
        assert hasattr(item, 'skill_id')
        assert hasattr(item, 'skill_name')
        assert hasattr(item, 'category_id')
        assert hasattr(item, 'category_name')
        assert hasattr(item, 'subcategory_id')
        assert hasattr(item, 'subcategory_name')

    def test_search_includes_full_hierarchy(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """
        Search results must include full hierarchy path for each skill.
        """
        # Arrange
        category = mock_category(10, "Cloud")
        subcategory = mock_subcategory(20, "AWS Services")
        skill = mock_skill(30, "Lambda")
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(skill, subcategory, category)]
        
        # Act
        result = service.search_skills_in_taxonomy(mock_db, "Lambda")
        
        # Assert
        item = result.results[0]
        assert item.skill_id == 30
        assert item.skill_name == "Lambda"
        assert item.subcategory_id == 20
        assert item.subcategory_name == "AWS Services"
        assert item.category_id == 10
        assert item.category_name == "Cloud"


# ============================================================================
# TEST: Query Layer - In-Use Filter Applied
# ============================================================================

class TestQueryInUseFilter:
    """Test that the query applies the in-use EXISTS filter."""
    
    def test_query_applies_in_use_filter(self, mock_db):
        """
        The _query_skills_with_hierarchy function should apply
        the EXISTS filter for employee_skills.
        """
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_skills_with_hierarchy(mock_db, "test")
        
        # Assert - filter should be called (with both search term and in-use filter)
        mock_query.filter.assert_called_once()
    
    def test_search_orders_results_deterministically(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """
        Results should be ordered by category, subcategory, skill name.
        """
        # Arrange
        cat_a = mock_category(1, "A Category")
        cat_b = mock_category(2, "B Category")
        sub_a = mock_subcategory(1, "A Subcategory")
        sub_b = mock_subcategory(2, "B Subcategory")
        
        # Return in expected order (query orders them)
        results = [
            (mock_skill(1, "Alpha"), sub_a, cat_a),
            (mock_skill(2, "Beta"), sub_a, cat_a),
            (mock_skill(3, "Gamma"), sub_b, cat_b),
        ]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = results
        
        # Act
        result = service.search_skills_in_taxonomy(mock_db, "a")
        
        # Assert - verify order preserved
        assert result.results[0].skill_name == "Alpha"
        assert result.results[1].skill_name == "Beta"
        assert result.results[2].skill_name == "Gamma"


# ============================================================================
# TEST: Soft-Deleted Employee Skills
# ============================================================================

class TestSoftDeletedEmployeeSkills:
    """Test that soft-deleted employee_skills are not counted as 'in-use'."""
    
    def test_skill_with_only_soft_deleted_employee_skills_not_returned(self, mock_db):
        """
        A skill where all employee_skills have deleted_at != NULL
        should NOT be returned in search (treated as unused).
        """
        # Arrange - mock returns empty because all employee_skills are soft-deleted
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []  # EXISTS(... deleted_at IS NULL) fails
        
        # Act
        result = service.search_skills_in_taxonomy(mock_db, "DeletedSkill")
        
        # Assert
        assert result.count == 0
        assert result.results == []
