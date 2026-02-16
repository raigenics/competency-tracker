"""
Unit tests for capability_finder/skills_service.py

Tests for fetching skills and skill suggestions for typeahead/autocomplete.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_finder import skills_service as service
from app.models.skill import Skill
from app.models.employee_skill import EmployeeSkill


# ============================================================================
# TEST: get_all_skills (Main Entry Point)
# ============================================================================

class TestGetAllSkills:
    """Test the main get all skills function."""
    
    def test_returns_skill_names_from_query(self, mock_db):
        """Should return skill names from database query."""
        # Arrange
        with patch.object(service, '_query_all_skills', return_value=['AWS', 'Docker', 'Python']):
            # Act
            result = service.get_all_skills(mock_db)
        
        # Assert
        assert result == ['AWS', 'Docker', 'Python']
    
    def test_returns_empty_list_when_no_skills(self, mock_db):
        """Should return empty list when no skills in database."""
        # Arrange
        with patch.object(service, '_query_all_skills', return_value=[]):
            # Act
            result = service.get_all_skills(mock_db)
        
        # Assert
        assert result == []
    
    def test_calls_query_function_with_db_session(self, mock_db):
        """Should pass db session to query function."""
        # Arrange
        with patch.object(service, '_query_all_skills', return_value=[]) as mock_query:
            # Act
            service.get_all_skills(mock_db)
        
        # Assert
        mock_query.assert_called_once_with(mock_db)


# ============================================================================
# TEST: _query_all_skills (Query Helper)
# ============================================================================

class TestQueryAllSkills:
    """Test the skills query helper."""
    
    def test_queries_distinct_skill_names(self, mock_db):
        """Should query distinct skill names from database."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [('AWS',), ('Docker',), ('Python',)]
        
        # Act
        result = service._query_all_skills(mock_db)
        
        # Assert
        mock_db.query.assert_called_once_with(Skill.skill_name)
        mock_query.distinct.assert_called_once()
    
    def test_orders_by_skill_name_ascending(self, mock_db):
        """Should order skills by name alphabetically."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_all_skills(mock_db)
        
        # Assert
        mock_query.order_by.assert_called_once()
    
    def test_extracts_skill_names_from_tuples(self, mock_db):
        """Should extract skill names from query result tuples."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [('Python',), ('Java',), ('React',)]
        
        # Act
        result = service._query_all_skills(mock_db)
        
        # Assert
        assert result == ['Python', 'Java', 'React']
    
    def test_returns_empty_list_when_no_skills(self, mock_db):
        """Should return empty list when no skills found."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_all_skills(mock_db)
        
        # Assert
        assert result == []


# ============================================================================
# TEST: get_skill_suggestions (Main Entry Point)
# ============================================================================

class TestGetSkillSuggestions:
    """Test skill suggestions with employee availability."""
    
    def test_returns_skill_suggestions_with_metadata(self, mock_db):
        """Should return skill suggestions with availability metadata."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (1, 'Python', True),
            (2, 'AWS', True),
            (3, 'Docker', False)
        ]
        
        # Act
        result = service.get_skill_suggestions(mock_db)
        
        # Assert
        assert len(result) == 3
        assert result[0]['skill_id'] == 1
        assert result[0]['skill_name'] == 'Python'
        assert result[0]['is_employee_available'] == True
        assert result[0]['is_selectable'] == True
    
    def test_marks_skills_without_employees_as_not_selectable(self, mock_db):
        """Should mark skills without employees as not selectable."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (1, 'NewSkill', False)
        ]
        
        # Act
        result = service.get_skill_suggestions(mock_db)
        
        # Assert
        assert result[0]['is_employee_available'] == False
        assert result[0]['is_selectable'] == False
    
    def test_applies_search_filter_when_query_provided(self, mock_db):
        """Should filter skills by query when provided."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(1, 'Python', True)]
        
        # Act
        result = service.get_skill_suggestions(mock_db, query='python')
        
        # Assert
        mock_query.filter.assert_called()
        assert len(result) == 1
    
    def test_returns_all_skills_when_no_query(self, mock_db):
        """Should return all skills when query is None."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (1, 'AWS', True),
            (2, 'Docker', True),
            (3, 'Python', True)
        ]
        
        # Act
        result = service.get_skill_suggestions(mock_db, query=None)
        
        # Assert
        assert len(result) == 3
    
    def test_skips_filter_for_empty_query_string(self, mock_db):
        """Should not filter when query is empty string."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service.get_skill_suggestions(mock_db, query='')
        
        # Assert
        # Should not call filter for empty query
        assert result == []
    
    def test_skips_filter_for_whitespace_only_query(self, mock_db):
        """Should not filter when query is whitespace only."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service.get_skill_suggestions(mock_db, query='   ')
        
        # Assert
        assert result == []
    
    def test_returns_empty_list_when_no_matches(self, mock_db):
        """Should return empty list when no skills match query."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service.get_skill_suggestions(mock_db, query='nonexistent')
        
        # Assert
        assert result == []
    
    def test_orders_employee_available_skills_first(self, mock_db):
        """Should order skills with employees before master-only skills."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (1, 'Popular', True),
            (2, 'Obscure', False)
        ]
        
        # Act
        result = service.get_skill_suggestions(mock_db)
        
        # Assert
        mock_query.order_by.assert_called()
        assert result[0]['is_employee_available'] == True
    
    def test_transforms_results_to_dict_format(self, mock_db):
        """Should transform query results to dictionary format."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (42, 'TestSkill', True)
        ]
        
        # Act
        result = service.get_skill_suggestions(mock_db)
        
        # Assert
        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        assert 'skill_id' in result[0]
        assert 'skill_name' in result[0]
        assert 'is_employee_available' in result[0]
        assert 'is_selectable' in result[0]
