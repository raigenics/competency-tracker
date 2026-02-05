"""
Unit tests for dashboard/top_skills_service.py

Tests top skills by employee count dashboard widget.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.dashboard import top_skills_service


class TestGetTopSkills:
    """Test the main public function get_top_skills()."""
    
    def test_returns_top_skills_list(self, mock_db):
        """Should return list of top skills with counts."""
        # Arrange
        with patch.object(top_skills_service, '_build_base_query') as mock_build, \
             patch.object(top_skills_service, '_apply_scope_filters') as mock_filter, \
             patch.object(top_skills_service, '_execute_and_format', return_value=[
                 {"skill": "Python", "total": 50, "expert": 20, "proficient": 15}
             ]) as mock_exec:
            
            mock_query = MagicMock()
            mock_build.return_value = mock_query
            mock_filter.return_value = mock_query
            
            # Act
            result = top_skills_service.get_top_skills(mock_db, limit=10)
            
            # Assert
            assert len(result) == 1
            assert result[0]["skill"] == "Python"
            assert result[0]["total"] == 50
    
    def test_applies_sub_segment_filter(self, mock_db):
        """Should apply sub-segment filter when provided."""
        # Arrange
        with patch.object(top_skills_service, '_build_base_query') as mock_build, \
             patch.object(top_skills_service, '_apply_scope_filters') as mock_filter, \
             patch.object(top_skills_service, '_execute_and_format', return_value=[]):
            
            mock_query = MagicMock()
            mock_build.return_value = mock_query
            mock_filter.return_value = mock_query
            
            # Act
            top_skills_service.get_top_skills(mock_db, sub_segment_id=1)
            
            # Assert
            mock_filter.assert_called_once_with(mock_query, 1, None, None)
    
    def test_applies_project_filter(self, mock_db):
        """Should apply project filter when provided."""
        # Arrange
        with patch.object(top_skills_service, '_build_base_query') as mock_build, \
             patch.object(top_skills_service, '_apply_scope_filters') as mock_filter, \
             patch.object(top_skills_service, '_execute_and_format', return_value=[]):
            
            mock_query = MagicMock()
            mock_build.return_value = mock_query
            mock_filter.return_value = mock_query
            
            # Act
            top_skills_service.get_top_skills(mock_db, project_id=2)
            
            # Assert
            mock_filter.assert_called_once_with(mock_query, None, 2, None)
    
    def test_applies_team_filter(self, mock_db):
        """Should apply team filter when provided."""
        # Arrange
        with patch.object(top_skills_service, '_build_base_query') as mock_build, \
             patch.object(top_skills_service, '_apply_scope_filters') as mock_filter, \
             patch.object(top_skills_service, '_execute_and_format', return_value=[]):
            
            mock_query = MagicMock()
            mock_build.return_value = mock_query
            mock_filter.return_value = mock_query
            
            # Act
            top_skills_service.get_top_skills(mock_db, team_id=3)
            
            # Assert
            mock_filter.assert_called_once_with(mock_query, None, None, 3)
    
    def test_respects_limit_parameter(self, mock_db):
        """Should pass limit parameter to execute function."""
        # Arrange
        with patch.object(top_skills_service, '_build_base_query') as mock_build, \
             patch.object(top_skills_service, '_apply_scope_filters') as mock_filter, \
             patch.object(top_skills_service, '_execute_and_format', return_value=[]) as mock_exec:
            
            mock_query = MagicMock()
            mock_build.return_value = mock_query
            mock_filter.return_value = mock_query
            
            # Act
            top_skills_service.get_top_skills(mock_db, limit=20)
            
            # Assert
            mock_exec.assert_called_once_with(mock_query, 20)


class TestBuildBaseQuery:
    """Test the _build_base_query() function."""
    
    def test_builds_query_with_aggregations(self, mock_db):
        """Should build query with skill name and aggregation functions."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        
        # Act
        result = top_skills_service._build_base_query(mock_db)
        
        # Assert
        mock_db.query.assert_called_once()
        # Should have two joins (EmployeeSkill and Employee)
        assert mock_query.join.call_count == 2
    
    def test_returns_query_object(self, mock_db):
        """Should return query object for further chaining."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        
        # Act
        result = top_skills_service._build_base_query(mock_db)
        
        # Assert
        assert result is not None


class TestApplyScopeFilters:
    """Test the _apply_scope_filters() function."""
    
    def test_applies_team_filter(self):
        """Should apply team_id filter when provided."""
        # Arrange
        mock_query = MagicMock()
        
        # Act
        result = top_skills_service._apply_scope_filters(mock_query, None, None, 5)
        
        # Assert
        mock_query.filter.assert_called_once()
    
    def test_applies_project_filter(self):
        """Should apply project_id filter when provided."""
        # Arrange
        mock_query = MagicMock()
        
        # Act
        result = top_skills_service._apply_scope_filters(mock_query, None, 3, None)
        
        # Assert
        mock_query.filter.assert_called_once()
    
    def test_applies_sub_segment_filter(self):
        """Should apply sub_segment_id filter when provided."""
        # Arrange
        mock_query = MagicMock()
        
        # Act
        result = top_skills_service._apply_scope_filters(mock_query, 1, None, None)
        
        # Assert
        mock_query.filter.assert_called_once()
    
    def test_applies_no_filter_when_all_none(self):
        """Should not apply any filter when all parameters are None."""
        # Arrange
        mock_query = MagicMock()
        
        # Act
        result = top_skills_service._apply_scope_filters(mock_query, None, None, None)
        
        # Assert
        # Query should be returned without modification
        assert result == mock_query
    
    def test_team_filter_takes_precedence(self):
        """Should apply only team filter when team and other filters provided."""
        # Arrange
        mock_query = MagicMock()
        
        # Act
        result = top_skills_service._apply_scope_filters(mock_query, 1, 2, 3)
        
        # Assert
        # Should only call filter once (for team, highest precedence)
        mock_query.filter.assert_called_once()


class TestExecuteAndFormat:
    """Test the _execute_and_format() function."""
    
    def test_executes_query_and_formats_results(self):
        """Should execute query, group by skill, order, limit, and format."""
        # Arrange
        mock_query = MagicMock()
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            ("Python", 50, 20, 15),
            ("SQL", 45, 18, 12)
        ]
        
        # Act
        result = top_skills_service._execute_and_format(mock_query, 10)
        
        # Assert
        assert len(result) == 2
        assert result[0] == {"skill": "Python", "total": 50, "expert": 20, "proficient": 15}
        assert result[1] == {"skill": "SQL", "total": 45, "expert": 18, "proficient": 12}
    
    def test_applies_group_by_order_by_limit(self):
        """Should apply group_by, order_by, and limit to query."""
        # Arrange
        mock_query = MagicMock()
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        top_skills_service._execute_and_format(mock_query, 5)
        
        # Assert
        mock_query.group_by.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(5)
    
    def test_returns_empty_list_when_no_results(self):
        """Should return empty list when query returns no results."""
        # Arrange
        mock_query = MagicMock()
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = top_skills_service._execute_and_format(mock_query, 10)
        
        # Assert
        assert result == []
    
    def test_formats_with_correct_keys(self):
        """Should format results with skill, total, expert, proficient keys."""
        # Arrange
        mock_query = MagicMock()
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [("Python", 100, 40, 30)]
        
        # Act
        result = top_skills_service._execute_and_format(mock_query, 10)
        
        # Assert
        assert "skill" in result[0]
        assert "total" in result[0]
        assert "expert" in result[0]
        assert "proficient" in result[0]
