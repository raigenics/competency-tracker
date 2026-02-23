"""
Unit tests for dropdown_service.py

Tests:
1. get_sub_segments_scope returns sub-segments with employee and project counts
2. get_sub_segments_scope excludes soft-deleted sub-segments
3. get_sub_segments_scope returns zero counts when no data
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call

from app.services.dropdown_service import DropdownService


class TestGetSubSegmentsScope:
    """Test get_sub_segments_scope function."""
    
    def test_returns_sub_segments_with_counts(self, mock_db, mock_query):
        """Should return sub-segments with employee and project counts."""
        # Arrange
        mock_sub_segment1 = Mock()
        mock_sub_segment1.sub_segment_id = 1
        mock_sub_segment1.sub_segment_name = "ADT"
        mock_sub_segment1.sub_segment_fullname = "Advanced Digital Technologies"
        mock_sub_segment1.deleted_at = None
        
        mock_sub_segment2 = Mock()
        mock_sub_segment2.sub_segment_id = 2
        mock_sub_segment2.sub_segment_name = "Cloud"
        mock_sub_segment2.sub_segment_fullname = None  # No fullname
        mock_sub_segment2.deleted_at = None
        
        # Setup query chains for different queries
        sub_segments_query = MagicMock()
        sub_segments_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_sub_segment1, mock_sub_segment2
        ]
        
        employee_count_query = MagicMock()
        employee_count_query.scalar.return_value = 124
        
        project_count_query = MagicMock()
        project_count_query.filter.return_value.scalar.return_value = 11
        
        # mock_db.query returns different mocks for different models
        query_calls = [sub_segments_query, employee_count_query, project_count_query]
        mock_db.query.side_effect = query_calls
        
        # Act
        result = DropdownService.get_sub_segments_scope(mock_db)
        
        # Assert
        assert "sub_segments" in result
        assert "total_employees" in result
        assert "total_projects" in result
        
        assert len(result["sub_segments"]) == 2
        assert result["sub_segments"][0].sub_segment_id == 1
        assert result["sub_segments"][0].sub_segment_name == "ADT"
        assert result["sub_segments"][0].sub_segment_fullname == "Advanced Digital Technologies"
        assert result["sub_segments"][1].sub_segment_id == 2
        assert result["sub_segments"][1].sub_segment_fullname is None
        
        assert result["total_employees"] == 124
        assert result["total_projects"] == 11
    
    def test_returns_zero_counts_when_no_data(self, mock_db):
        """Should return empty sub-segments and zero counts when no data."""
        # Arrange
        sub_segments_query = MagicMock()
        sub_segments_query.filter.return_value.order_by.return_value.all.return_value = []
        
        employee_count_query = MagicMock()
        employee_count_query.scalar.return_value = 0
        
        project_count_query = MagicMock()
        project_count_query.filter.return_value.scalar.return_value = 0
        
        mock_db.query.side_effect = [sub_segments_query, employee_count_query, project_count_query]
        
        # Act
        result = DropdownService.get_sub_segments_scope(mock_db)
        
        # Assert
        assert result["sub_segments"] == []
        assert result["total_employees"] == 0
        assert result["total_projects"] == 0
    
    def test_handles_none_scalar_results(self, mock_db):
        """Should handle None scalar results gracefully."""
        # Arrange
        sub_segments_query = MagicMock()
        sub_segments_query.filter.return_value.order_by.return_value.all.return_value = []
        
        employee_count_query = MagicMock()
        employee_count_query.scalar.return_value = None  # Possible in edge cases
        
        project_count_query = MagicMock()
        project_count_query.filter.return_value.scalar.return_value = None
        
        mock_db.query.side_effect = [sub_segments_query, employee_count_query, project_count_query]
        
        # Act
        result = DropdownService.get_sub_segments_scope(mock_db)
        
        # Assert
        assert result["total_employees"] == 0
        assert result["total_projects"] == 0
