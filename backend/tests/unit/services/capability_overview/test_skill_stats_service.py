"""
Unit tests for capability_overview/skill_stats_service.py

Tests skill statistics and overview queries.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import skill_stats_service
from app.schemas.skill import SkillStatsResponse


class TestGetSkillStats:
    """Test the main public function get_skill_stats()."""
    
    def test_returns_complete_stats_response(self, mock_db):
        """Should return complete SkillStatsResponse with all fields."""
        # Arrange
        with patch.object(skill_stats_service, '_query_total_skills', return_value=50), \
             patch.object(skill_stats_service, '_query_skills_by_category', return_value={"Programming": 20, "Database": 10}), \
             patch.object(skill_stats_service, '_query_skills_by_subcategory', return_value={"Backend": 15, "Frontend": 10}), \
             patch.object(skill_stats_service, '_query_most_popular_skills', return_value=[("Python", 30), ("SQL", 25)]):
            
            # Act
            result = skill_stats_service.get_skill_stats(mock_db)
            
            # Assert
            assert isinstance(result, SkillStatsResponse)
            assert result.total_skills == 50
            assert result.by_category == {"Programming": 20, "Database": 10}
            assert result.by_subcategory == {"Backend": 15, "Frontend": 10}
            assert len(result.most_popular_skills) == 2
    
    def test_handles_zero_skills(self, mock_db):
        """Should handle case when no skills exist."""
        # Arrange
        with patch.object(skill_stats_service, '_query_total_skills', return_value=0), \
             patch.object(skill_stats_service, '_query_skills_by_category', return_value={}), \
             patch.object(skill_stats_service, '_query_skills_by_subcategory', return_value={}), \
             patch.object(skill_stats_service, '_query_most_popular_skills', return_value=[]):
            
            # Act
            result = skill_stats_service.get_skill_stats(mock_db)
            
            # Assert
            assert result.total_skills == 0
            assert result.by_category == {}
            assert result.by_subcategory == {}
            assert result.most_popular_skills == []
    
    def test_calls_all_query_functions(self, mock_db):
        """Should call all required query functions."""
        # Arrange
        with patch.object(skill_stats_service, '_query_total_skills', return_value=10) as mock_total, \
             patch.object(skill_stats_service, '_query_skills_by_category', return_value={}) as mock_category, \
             patch.object(skill_stats_service, '_query_skills_by_subcategory', return_value={}) as mock_subcategory, \
             patch.object(skill_stats_service, '_query_most_popular_skills', return_value=[]) as mock_popular:
            
            # Act
            skill_stats_service.get_skill_stats(mock_db)
            
            # Assert
            mock_total.assert_called_once_with(mock_db)
            mock_category.assert_called_once_with(mock_db)
            mock_subcategory.assert_called_once_with(mock_db)
            mock_popular.assert_called_once_with(mock_db)


class TestQueryTotalSkills:
    """Test the _query_total_skills() function."""
    
    def test_returns_total_count(self, mock_db):
        """Should return count of all skills."""
        # Arrange
        mock_db.query.return_value.scalar.return_value = 42
        
        # Act
        result = skill_stats_service._query_total_skills(mock_db)
        
        # Assert
        assert result == 42
    
    def test_returns_zero_when_none(self, mock_db):
        """Should return 0 when scalar returns None."""
        # Arrange
        mock_db.query.return_value.scalar.return_value = None
        
        # Act
        result = skill_stats_service._query_total_skills(mock_db)
        
        # Assert
        assert result == 0


class TestQuerySkillsByCategory:
    """Test the _query_skills_by_category() function."""
    
    def test_returns_category_counts_dict(self, mock_db):
        """Should return dictionary of category names to counts."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("Programming", 25),
            ("Database", 15),
            ("Cloud", 10)
        ]
        
        # Act
        result = skill_stats_service._query_skills_by_category(mock_db)
        
        # Assert
        assert result == {"Programming": 25, "Database": 15, "Cloud": 10}
        assert isinstance(result, dict)
    
    def test_returns_empty_dict_when_no_categories(self, mock_db):
        """Should return empty dict when no skills/categories exist."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = skill_stats_service._query_skills_by_category(mock_db)
        
        # Assert
        assert result == {}
    
    def test_performs_join_and_group_by(self, mock_db):
        """Should join with Skill table and group by category name."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        skill_stats_service._query_skills_by_category(mock_db)
        
        # Assert
        mock_query.join.assert_called_once()
        mock_query.group_by.assert_called_once()


class TestQuerySkillsBySubcategory:
    """Test the _query_skills_by_subcategory() function."""
    
    def test_returns_subcategory_counts_dict(self, mock_db):
        """Should return dictionary of subcategory names to counts."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("Backend", 20),
            ("Frontend", 15),
            ("Mobile", 8)
        ]
        
        # Act
        result = skill_stats_service._query_skills_by_subcategory(mock_db)
        
        # Assert
        assert result == {"Backend": 20, "Frontend": 15, "Mobile": 8}
        assert isinstance(result, dict)
    
    def test_returns_empty_dict_when_no_subcategories(self, mock_db):
        """Should return empty dict when no subcategories exist."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = skill_stats_service._query_skills_by_subcategory(mock_db)
        
        # Assert
        assert result == {}


class TestQueryMostPopularSkills:
    """Test the _query_most_popular_skills() function."""
    
    def test_returns_top_skills_by_employee_count(self, mock_db):
        """Should return top N skills ordered by employee count."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            ("Python", 50),
            ("SQL", 45),
            ("JavaScript", 40)
        ]
        
        # Act
        result = skill_stats_service._query_most_popular_skills(mock_db, limit=3)
        
        # Assert
        assert len(result) == 3
        assert result[0] == ("Python", 50)
        assert result[1] == ("SQL", 45)
        assert result[2] == ("JavaScript", 40)
    
    def test_respects_limit_parameter(self, mock_db):
        """Should limit results to specified number."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        skill_stats_service._query_most_popular_skills(mock_db, limit=5)
        
        # Assert
        mock_query.limit.assert_called_once_with(5)
    
    def test_default_limit_is_10(self, mock_db):
        """Should use default limit of 10 when not specified."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        skill_stats_service._query_most_popular_skills(mock_db)
        
        # Assert
        mock_query.limit.assert_called_once_with(10)
    
    def test_returns_empty_list_when_no_skills(self, mock_db):
        """Should return empty list when no skills exist."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = skill_stats_service._query_most_popular_skills(mock_db)
        
        # Assert
        assert result == []


class TestBuildStatsResponse:
    """Test the _build_stats_response() pure function."""
    
    def test_builds_complete_response(self):
        """Should build SkillStatsResponse from input data."""
        # Arrange
        total = 100
        by_category = {"Programming": 50, "Database": 30}
        by_subcategory = {"Backend": 40, "Frontend": 35}
        most_popular = [("Python", 60), ("SQL", 55)]
        
        # Act
        result = skill_stats_service._build_stats_response(
            total, by_category, by_subcategory, most_popular
        )
        
        # Assert
        assert isinstance(result, SkillStatsResponse)
        assert result.total_skills == 100
        assert result.by_category == {"Programming": 50, "Database": 30}
        assert result.by_subcategory == {"Backend": 40, "Frontend": 35}
        assert len(result.most_popular_skills) == 2
    
    def test_transforms_popular_skills_to_dict_list(self):
        """Should transform tuples to list of dicts for most_popular_skills."""
        # Arrange
        most_popular = [("Python", 60), ("SQL", 55), ("JavaScript", 50)]
        
        # Act
        result = skill_stats_service._build_stats_response(
            50, {}, {}, most_popular
        )
        
        # Assert
        assert result.most_popular_skills == [
            {"skill_name": "Python", "employee_count": 60},
            {"skill_name": "SQL", "employee_count": 55},
            {"skill_name": "JavaScript", "employee_count": 50}
        ]
    
    def test_handles_empty_inputs(self):
        """Should handle empty dictionaries and lists."""
        # Act
        result = skill_stats_service._build_stats_response(0, {}, {}, [])
        
        # Assert
        assert result.total_skills == 0
        assert result.by_category == {}
        assert result.by_subcategory == {}
        assert result.most_popular_skills == []


class TestFormatPopularSkills:
    """Test the _format_popular_skills() pure function."""
    
    def test_transforms_tuples_to_dict_list(self):
        """Should transform list of tuples to list of dicts."""
        # Arrange
        raw_data = [
            ("Python", 100),
            ("SQL", 85),
            ("Java", 70)
        ]
        
        # Act
        result = skill_stats_service._format_popular_skills(raw_data)
        
        # Assert
        assert len(result) == 3
        assert result[0] == {"skill_name": "Python", "employee_count": 100}
        assert result[1] == {"skill_name": "SQL", "employee_count": 85}
        assert result[2] == {"skill_name": "Java", "employee_count": 70}
    
    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when given empty input."""
        # Act
        result = skill_stats_service._format_popular_skills([])
        
        # Assert
        assert result == []
    
    def test_preserves_skill_order(self):
        """Should maintain the order of skills from input."""
        # Arrange
        raw_data = [
            ("Skill C", 30),
            ("Skill A", 50),
            ("Skill B", 40)
        ]
        
        # Act
        result = skill_stats_service._format_popular_skills(raw_data)
        
        # Assert
        assert result[0]["skill_name"] == "Skill C"
        assert result[1]["skill_name"] == "Skill A"
        assert result[2]["skill_name"] == "Skill B"
    
    def test_handles_zero_employee_count(self):
        """Should handle skills with zero employees (edge case)."""
        # Arrange
        raw_data = [("Unused Skill", 0)]
        
        # Act
        result = skill_stats_service._format_popular_skills(raw_data)
        
        # Assert
        assert result == [{"skill_name": "Unused Skill", "employee_count": 0}]
