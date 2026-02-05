"""
Unit tests for capability_overview/list_skills_service.py

Tests GET /skills endpoint functionality.
Coverage: Paginated listing, multi-filter queries, employee counts, response building.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_overview import list_skills_service as service
from app.models import Skill, SkillCategory, SkillSubcategory
from app.schemas.common import PaginationParams


# ============================================================================
# TEST: get_skills_paginated (Main Entry Point)
# ============================================================================

class TestGetSkillsPaginated:
    """Test the main paginated skill listing function."""
    
    def test_returns_paginated_skills_without_filters(
        self, mock_db, mock_skill, mock_subcategory, mock_category, mock_pagination
    ):
        """Should return paginated skills when no filters provided."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skills = [
            mock_skill(1, "Python", subcategory, category),
            mock_skill(2, "Java", subcategory, category)
        ]
        pagination = mock_pagination(page=1, size=10)
        
        mock_query = MagicMock()
        with patch.object(service, '_query_skills_with_filters', return_value=mock_query):
            with patch.object(service, '_count_skills', return_value=2):
                with patch.object(service, '_paginate_and_fetch', return_value=skills):
                    with patch.object(service, '_get_employee_count_for_skill', return_value=5):
                        # Act
                        result, total = service.get_skills_paginated(
                            mock_db, pagination, None, None, None
                        )
        
        # Assert
        assert len(result) == 2
        assert total == 2
        assert result[0].skill_name == "Python"
        assert result[1].skill_name == "Java"
    
    def test_applies_category_filter(
        self, mock_db, mock_skill, mock_subcategory, mock_category, mock_pagination
    ):
        """Should filter skills by category name."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategory = mock_subcategory(1, "ML", category)
        skills = [mock_skill(1, "TensorFlow", subcategory, category)]
        pagination = mock_pagination()
        
        mock_query = MagicMock()
        with patch.object(service, '_query_skills_with_filters', return_value=mock_query) as mock_filter:
            with patch.object(service, '_count_skills', return_value=1):
                with patch.object(service, '_paginate_and_fetch', return_value=skills):
                    with patch.object(service, '_get_employee_count_for_skill', return_value=3):
                        # Act
                        result, total = service.get_skills_paginated(
                            mock_db, pagination, category="Data", subcategory=None, search=None
                        )
        
        # Assert
        mock_filter.assert_called_once_with(mock_db, "Data", None, None)
        assert result[0].category.category_name == "Data Science"
    
    def test_applies_subcategory_filter(
        self, mock_db, mock_skill, mock_subcategory, mock_category, mock_pagination
    ):
        """Should filter skills by subcategory name."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Mobile", category)
        skills = [mock_skill(1, "Swift", subcategory, category)]
        pagination = mock_pagination()
        
        mock_query = MagicMock()
        with patch.object(service, '_query_skills_with_filters', return_value=mock_query) as mock_filter:
            with patch.object(service, '_count_skills', return_value=1):
                with patch.object(service, '_paginate_and_fetch', return_value=skills):
                    with patch.object(service, '_get_employee_count_for_skill', return_value=2):
                        # Act
                        result, total = service.get_skills_paginated(
                            mock_db, pagination, category=None, subcategory="Mobile", search=None
                        )
        
        # Assert
        mock_filter.assert_called_once_with(mock_db, None, "Mobile", None)
        assert result[0].category.subcategory_name == "Mobile"
    
    def test_applies_search_filter(
        self, mock_db, mock_skill, mock_subcategory, mock_category, mock_pagination
    ):
        """Should filter skills by name search."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skills = [mock_skill(1, "Python", subcategory, category)]
        pagination = mock_pagination()
        
        mock_query = MagicMock()
        with patch.object(service, '_query_skills_with_filters', return_value=mock_query) as mock_filter:
            with patch.object(service, '_count_skills', return_value=1):
                with patch.object(service, '_paginate_and_fetch', return_value=skills):
                    with patch.object(service, '_get_employee_count_for_skill', return_value=10):
                        # Act
                        result, total = service.get_skills_paginated(
                            mock_db, pagination, category=None, subcategory=None, search="Python"
                        )
        
        # Assert
        mock_filter.assert_called_once_with(mock_db, None, None, "Python")
        assert result[0].skill_name == "Python"
    
    def test_applies_all_filters_together(
        self, mock_db, mock_skill, mock_subcategory, mock_category, mock_pagination
    ):
        """Should apply category, subcategory, and search filters together."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Web", category)
        skills = [mock_skill(1, "React", subcategory, category)]
        pagination = mock_pagination()
        
        mock_query = MagicMock()
        with patch.object(service, '_query_skills_with_filters', return_value=mock_query) as mock_filter:
            with patch.object(service, '_count_skills', return_value=1):
                with patch.object(service, '_paginate_and_fetch', return_value=skills):
                    with patch.object(service, '_get_employee_count_for_skill', return_value=8):
                        # Act
                        result, total = service.get_skills_paginated(
                            mock_db, pagination, category="Prog", subcategory="Web", search="React"
                        )
        
        # Assert
        mock_filter.assert_called_once_with(mock_db, "Prog", "Web", "React")
    
    def test_returns_empty_list_when_no_skills_found(
        self, mock_db, mock_pagination
    ):
        """Should return empty list when no skills match filters."""
        # Arrange
        pagination = mock_pagination()
        mock_query = MagicMock()
        
        with patch.object(service, '_query_skills_with_filters', return_value=mock_query):
            with patch.object(service, '_count_skills', return_value=0):
                with patch.object(service, '_paginate_and_fetch', return_value=[]):
                    # Act
                    result, total = service.get_skills_paginated(
                        mock_db, pagination, category="NonExistent"
                    )
        
        # Assert
        assert result == []
        assert total == 0
    
    def test_includes_employee_counts_in_response(
        self, mock_db, mock_skill, mock_subcategory, mock_category, mock_pagination
    ):
        """Should include employee count for each skill."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skills = [mock_skill(1, "Go", subcategory, category)]
        pagination = mock_pagination()
        
        mock_query = MagicMock()
        with patch.object(service, '_query_skills_with_filters', return_value=mock_query):
            with patch.object(service, '_count_skills', return_value=1):
                with patch.object(service, '_paginate_and_fetch', return_value=skills):
                    with patch.object(service, '_get_employee_count_for_skill', return_value=25):
                        # Act
                        result, total = service.get_skills_paginated(mock_db, pagination)
        
        # Assert
        assert result[0].employee_count == 25


# ============================================================================
# TEST: _query_skills_with_filters (Query Building)
# ============================================================================

class TestQuerySkillsWithFilters:
    """Test skill query building with filters."""
    
    def test_queries_all_skills_without_filters(self, mock_db):
        """Should query all skills when no filters provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        
        # Act
        result = service._query_skills_with_filters(mock_db, None, None, None)
        
        # Assert
        mock_db.query.assert_called_once_with(Skill)
        mock_query.options.assert_called_once()
        assert result == mock_query
    
    def test_joins_category_when_filter_provided(self, mock_db):
        """Should join SkillCategory table when category filter provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        service._query_skills_with_filters(mock_db, category="Programming", subcategory=None, search=None)
        
        # Assert
        mock_query.join.assert_called()
    
    def test_joins_subcategory_when_filter_provided(self, mock_db):
        """Should join SkillSubcategory table when subcategory filter provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        service._query_skills_with_filters(mock_db, category=None, subcategory="Backend", search=None)
        
        # Assert
        mock_query.join.assert_called()
    
    def test_applies_case_insensitive_search(self, mock_db):
        """Should apply ilike filter for skill name search."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Act
        service._query_skills_with_filters(mock_db, category=None, subcategory=None, search="python")
        
        # Assert
        mock_query.filter.assert_called_once()
    
    def test_eager_loads_relationships(self, mock_db):
        """Should use joinedload for subcategory and category relationships."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        
        # Act
        service._query_skills_with_filters(mock_db, None, None, None)
        
        # Assert
        mock_query.options.assert_called_once()


# ============================================================================
# TEST: _count_skills (Count Function)
# ============================================================================

class TestCountSkills:
    """Test skill counting."""
    
    def test_returns_total_count(self):
        """Should return total count from query."""
        # Arrange
        mock_query = MagicMock()
        mock_query.count.return_value = 42
        
        # Act
        result = service._count_skills(mock_query)
        
        # Assert
        assert result == 42
        mock_query.count.assert_called_once()
    
    def test_returns_zero_when_no_results(self):
        """Should return 0 when query has no results."""
        # Arrange
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        
        # Act
        result = service._count_skills(mock_query)
        
        # Assert
        assert result == 0


# ============================================================================
# TEST: _paginate_and_fetch (Pagination)
# ============================================================================

class TestPaginateAndFetch:
    """Test pagination application."""
    
    def test_applies_offset_and_limit(self, mock_pagination):
        """Should apply offset and limit from pagination params."""
        # Arrange
        mock_query = MagicMock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        pagination = mock_pagination(page=2, size=10)
        
        # Act
        service._paginate_and_fetch(mock_query, pagination)
        
        # Assert
        mock_query.offset.assert_called_once_with(10)  # (page - 1) * size
        mock_query.limit.assert_called_once_with(10)
        mock_query.all.assert_called_once()
    
    def test_handles_first_page(self, mock_pagination):
        """Should apply correct offset for first page."""
        # Arrange
        mock_query = MagicMock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        pagination = mock_pagination(page=1, size=20)
        
        # Act
        service._paginate_and_fetch(mock_query, pagination)
        
        # Assert
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(20)


# ============================================================================
# TEST: _get_employee_count_for_skill (Employee Count Query)
# ============================================================================

class TestGetEmployeeCountForSkill:
    """Test employee count query for a skill."""
    
    def test_returns_employee_count_for_skill(self, mock_db):
        """Should return count of distinct employees with skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15
        
        # Act
        result = service._get_employee_count_for_skill(mock_db, skill_id=1)
        
        # Assert
        assert result == 15
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_returns_zero_when_no_employees_found(self, mock_db):
        """Should return 0 when no employees have the skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._get_employee_count_for_skill(mock_db, skill_id=999)
        
        # Assert
        assert result == 0


# ============================================================================
# TEST: _build_skill_responses (Response Building)
# ============================================================================

class TestBuildSkillResponses:
    """Test skill response building."""
    
    def test_builds_responses_from_skills(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should build SkillResponse list from Skill models."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skills = [
            mock_skill(1, "Python", subcategory, category),
            mock_skill(2, "Java", subcategory, category)
        ]
        
        with patch.object(service, '_get_employee_count_for_skill', return_value=5):
            # Act
            result = service._build_skill_responses(mock_db, skills)
        
        # Assert
        assert len(result) == 2
        assert result[0].skill_id == 1
        assert result[0].skill_name == "Python"
        assert result[1].skill_id == 2
        assert result[1].skill_name == "Java"
    
    def test_includes_category_info(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should include category information in response."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategory = mock_subcategory(1, "ML", category)
        skills = [mock_skill(1, "TensorFlow", subcategory, category)]
        
        with patch.object(service, '_get_employee_count_for_skill', return_value=10):
            # Act
            result = service._build_skill_responses(mock_db, skills)
        
        # Assert
        assert result[0].category.category_name == "Data Science"
        assert result[0].category.subcategory_name == "ML"
    
    def test_queries_employee_count_for_each_skill(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should query employee count for each skill."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skills = [
            mock_skill(1, "Python", subcategory, category),
            mock_skill(2, "Go", subcategory, category)
        ]
        
        with patch.object(service, '_get_employee_count_for_skill', side_effect=[20, 15]) as mock_count:
            # Act
            result = service._build_skill_responses(mock_db, skills)
        
        # Assert
        assert mock_count.call_count == 2
        assert result[0].employee_count == 20
        assert result[1].employee_count == 15
    
    def test_handles_empty_skills_list(self, mock_db):
        """Should return empty list for empty input."""
        # Act
        result = service._build_skill_responses(mock_db, [])
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _build_category_info (Pure Function)
# ============================================================================

class TestBuildCategoryInfo:
    """Test category info building from skill relationships."""
    
    def test_builds_category_info_from_skill(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should build CategoryInfo from skill's relationships."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(2, "Backend", category)
        skill = mock_skill(1, "Python", subcategory, category)
        
        # Act
        result = service._build_category_info(skill)
        
        # Assert
        assert result.category_id == 1
        assert result.category_name == "Programming"
        assert result.subcategory_id == 2
        assert result.subcategory_name == "Backend"
    
    def test_handles_skill_without_subcategory(
        self, mock_skill, mock_category
    ):
        """Should handle skill with category but no subcategory."""
        # Arrange
        category = mock_category(1, "General")
        skill = mock_skill(1, "Communication", None, category)
        
        # Act
        result = service._build_category_info(skill)
        
        # Assert
        assert result.category_id == 1
        assert result.category_name == "General"
        assert result.subcategory_id is None
        assert result.subcategory_name is None
