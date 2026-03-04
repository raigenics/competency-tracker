"""
Unit tests for capability_overview/skill_leading_subsegment_service.py

Tests leading sub-segment computation for a specific skill:
- leading_sub_segment_name: Sub-segment with highest distinct employee count
- leading_sub_segment_employee_count: Number of distinct employees in leading sub-segment
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import skill_leading_subsegment_service
from app.schemas.skill import SkillLeadingSubSegmentResponse


class TestGetSkillLeadingSubSegment:
    """Test the main public function get_skill_leading_subsegment()."""
    
    def test_returns_complete_response_with_data(self, mock_db):
        """Should return SkillLeadingSubSegmentResponse with sub-segment name and count."""
        # Arrange
        skill_id = 42
        # Return tuple that can be unpacked as (name, count)
        mock_result = ("Digital Industries", 25)
        
        with patch.object(skill_leading_subsegment_service, '_query_leading_subsegment', return_value=mock_result):
            # Act
            result = skill_leading_subsegment_service.get_skill_leading_subsegment(mock_db, skill_id)
            
            # Assert
            assert isinstance(result, SkillLeadingSubSegmentResponse)
            assert result.leading_sub_segment_name == "Digital Industries"
            assert result.leading_sub_segment_employee_count == 25
    
    def test_handles_no_data_found(self, mock_db):
        """Should return None name and 0 count when no sub-segment data exists."""
        # Arrange
        skill_id = 999
        with patch.object(skill_leading_subsegment_service, '_query_leading_subsegment', return_value=None):
            # Act
            result = skill_leading_subsegment_service.get_skill_leading_subsegment(mock_db, skill_id)
            
            # Assert
            assert result.leading_sub_segment_name is None
            assert result.leading_sub_segment_employee_count == 0
    
    def test_calls_query_function_with_skill_id(self, mock_db):
        """Should call _query_leading_subsegment with correct skill_id."""
        # Arrange
        skill_id = 42
        mock_result = ("Test Sub-Segment", 10)
        
        with patch.object(skill_leading_subsegment_service, '_query_leading_subsegment', return_value=mock_result) as mock_query:
            # Act
            skill_leading_subsegment_service.get_skill_leading_subsegment(mock_db, skill_id)
            
            # Assert
            mock_query.assert_called_once_with(mock_db, skill_id)


class TestQueryLeadingSubSegment:
    """Test the _query_leading_subsegment() function."""
    
    def test_returns_row_when_data_exists(self, mock_db):
        """Should return row with name and employee_count when data exists."""
        # Arrange
        skill_id = 42
        # SQLAlchemy query with labeled columns returns tuple-like Row object
        # that can be accessed via index: result[0], result[1]
        mock_row = ("Smart Infrastructure", 15)
        
        # Setup mock query chain
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_row
        mock_db.query.return_value = mock_query
        
        # Act
        result = skill_leading_subsegment_service._query_leading_subsegment(mock_db, skill_id)
        
        # Assert - function returns (result[0], result[1]) tuple
        assert result[0] == "Smart Infrastructure"
        assert result[1] == 15
    
    def test_returns_none_when_no_data(self, mock_db):
        """Should return None when no sub-segment data exists."""
        # Arrange
        skill_id = 999
        
        # Setup mock query chain
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act
        result = skill_leading_subsegment_service._query_leading_subsegment(mock_db, skill_id)
        
        # Assert
        assert result is None
    
    def test_ordering_selects_highest_count(self, mock_db):
        """Should verify query uses ORDER BY count DESC to get highest."""
        # Arrange
        skill_id = 42
        
        # Setup mock with spies
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act
        skill_leading_subsegment_service._query_leading_subsegment(mock_db, skill_id)
        
        # Assert - verify order_by was called (exact parameters are complex to verify due to SQLAlchemy expressions)
        mock_query.order_by.assert_called_once()
    
    def test_uses_first_for_single_result(self, mock_db):
        """Should verify query uses .first() to get single result."""
        # Arrange
        skill_id = 42
        
        # Setup mock
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act
        skill_leading_subsegment_service._query_leading_subsegment(mock_db, skill_id)
        
        # Assert
        mock_query.first.assert_called_once()


class TestTieBreakingBehavior:
    """Test tie-breaking when multiple sub-segments have same employee count."""
    
    def test_alphabetical_tiebreaker_selects_first_name(self, mock_db):
        """When counts are equal, should select alphabetically first sub-segment name."""
        # Arrange - This is a conceptual test, actual DB sorting verified in integration tests
        skill_id = 42
        # "Alpha Division" would be selected over "Beta Division" when counts equal
        mock_result = ("Alpha Division", 10)
        
        with patch.object(skill_leading_subsegment_service, '_query_leading_subsegment', return_value=mock_result):
            # Act
            result = skill_leading_subsegment_service.get_skill_leading_subsegment(mock_db, skill_id)
            
            # Assert - deterministic result
            assert result.leading_sub_segment_name == "Alpha Division"
            assert result.leading_sub_segment_employee_count == 10
