"""
Unit tests for capability_overview/skill_proficiency_breakdown_service.py

Tests proficiency breakdown for a specific skill:
- counts: Dict of proficiency level -> employee count
- avg: Average proficiency (1-5)
- median: Median proficiency (1-5)
- total: Total employees with this skill
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import skill_proficiency_breakdown_service
from app.schemas.skill import SkillProficiencyBreakdownResponse


class TestGetSkillProficiencyBreakdown:
    """Test the main public function get_skill_proficiency_breakdown()."""
    
    def test_returns_complete_breakdown_response(self, mock_db):
        """Should return complete SkillProficiencyBreakdownResponse with all fields."""
        # Arrange
        skill_id = 42
        raw_counts = {"Beginner": 10, "Advanced Beginner": 20, "Competent": 30, "Proficient": 15, "Expert": 5}
        expected_counts = {"Novice": 10, "Adv. Beginner": 20, "Competent": 30, "Proficient": 15, "Expert": 5}
        
        # Create proficiency IDs: 10*1 + 20*2 + 30*3 + 15*4 + 5*5
        ids = [1]*10 + [2]*20 + [3]*30 + [4]*15 + [5]*5
        
        with patch.object(skill_proficiency_breakdown_service, '_query_proficiency_counts', return_value=raw_counts), \
             patch.object(skill_proficiency_breakdown_service, '_query_proficiency_ids', return_value=ids):
            
            # Act
            result = skill_proficiency_breakdown_service.get_skill_proficiency_breakdown(mock_db, skill_id)
            
            # Assert
            assert isinstance(result, SkillProficiencyBreakdownResponse)
            assert result.counts == expected_counts
            assert result.avg == 2.8
            assert result.median == 3
            assert result.total == 80
    
    def test_handles_zero_data(self, mock_db):
        """Should handle case when no employees have this skill."""
        # Arrange
        skill_id = 999
        raw_counts = {}
        
        with patch.object(skill_proficiency_breakdown_service, '_query_proficiency_counts', return_value=raw_counts), \
             patch.object(skill_proficiency_breakdown_service, '_query_proficiency_ids', return_value=[]):
            
            # Act
            result = skill_proficiency_breakdown_service.get_skill_proficiency_breakdown(mock_db, skill_id)
            
            # Assert
            assert result.total == 0
            assert result.avg is None
            assert result.median is None
            # All levels should be 0
            for level in ["Novice", "Adv. Beginner", "Competent", "Proficient", "Expert"]:
                assert result.counts[level] == 0
    
    def test_calls_query_functions_with_skill_id(self, mock_db):
        """Should call query functions with correct skill_id."""
        # Arrange
        skill_id = 42
        with patch.object(skill_proficiency_breakdown_service, '_query_proficiency_counts', return_value={}) as mock_qpc, \
             patch.object(skill_proficiency_breakdown_service, '_query_proficiency_ids', return_value=[]) as mock_qpi:
            
            # Act
            skill_proficiency_breakdown_service.get_skill_proficiency_breakdown(mock_db, skill_id)
            
            # Assert
            mock_qpc.assert_called_once_with(mock_db, skill_id)
            mock_qpi.assert_called_once_with(mock_db, skill_id)


class TestQueryProficiencyCounts:
    """Test the _query_proficiency_counts() function."""
    
    def test_returns_counts_dict(self, mock_db):
        """Should return dict from query results."""
        # Arrange
        skill_id = 42
        mock_results = [
            ("Beginner", 10),
            ("Expert", 5)
        ]
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = mock_results
        
        # Act
        result = skill_proficiency_breakdown_service._query_proficiency_counts(mock_db, skill_id)
        
        # Assert
        assert result == {"Beginner": 10, "Expert": 5}
    
    def test_returns_empty_dict_when_no_data(self, mock_db):
        """Should return empty dict when no data."""
        # Arrange
        skill_id = 999
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = []
        
        # Act
        result = skill_proficiency_breakdown_service._query_proficiency_counts(mock_db, skill_id)
        
        # Assert
        assert result == {}


class TestNormalizeCounts:
    """Test the _normalize_counts() function."""
    
    def test_normalizes_level_names(self):
        """Should map DB level names to canonical names."""
        # Arrange
        raw_counts = {
            "Beginner": 10,
            "Advanced Beginner": 20,
            "Competent": 30,
            "Proficient": 15,
            "Expert": 5
        }
        
        # Act
        result = skill_proficiency_breakdown_service._normalize_counts(raw_counts)
        
        # Assert
        assert result["Novice"] == 10
        assert result["Adv. Beginner"] == 20
        assert result["Competent"] == 30
        assert result["Proficient"] == 15
        assert result["Expert"] == 5
    
    def test_returns_zeros_for_missing_levels(self):
        """Should return 0 for levels not in raw counts."""
        # Arrange
        raw_counts = {"Expert": 5}
        
        # Act
        result = skill_proficiency_breakdown_service._normalize_counts(raw_counts)
        
        # Assert
        assert result["Novice"] == 0
        assert result["Adv. Beginner"] == 0
        assert result["Competent"] == 0
        assert result["Proficient"] == 0
        assert result["Expert"] == 5
    
    def test_empty_raw_counts(self):
        """Should return all zeros for empty input."""
        # Act
        result = skill_proficiency_breakdown_service._normalize_counts({})
        
        # Assert
        for level in ["Novice", "Adv. Beginner", "Competent", "Proficient", "Expert"]:
            assert result[level] == 0


class TestCalculateAverage:
    """Test the _calculate_average() function."""
    
    def test_calculates_correct_average(self):
        """Should calculate average of proficiency IDs."""
        # Arrange: [1,1,1,2,2,3,3,3,3,5] = (3 + 4 + 12 + 5) / 10 = 2.4
        ids = [1, 1, 1, 2, 2, 3, 3, 3, 3, 5]
        
        # Act
        result = skill_proficiency_breakdown_service._calculate_average(ids)
        
        # Assert
        assert result == 2.4
    
    def test_returns_none_when_empty(self):
        """Should return None when list is empty."""
        # Act
        result = skill_proficiency_breakdown_service._calculate_average([])
        
        # Assert
        assert result is None
    
    def test_single_value(self):
        """Should return the single value."""
        # Act
        result = skill_proficiency_breakdown_service._calculate_average([3])
        
        # Assert
        assert result == 3.0


class TestCalculateMedian:
    """Test the _calculate_median() function."""
    
    def test_calculates_median_odd_count(self):
        """Should return middle element for odd count."""
        # Arrange: 5 elements, median is 3rd
        ids = [1, 2, 3, 4, 5]
        
        # Act
        result = skill_proficiency_breakdown_service._calculate_median(ids)
        
        # Assert
        assert result == 3
    
    def test_calculates_median_even_count(self):
        """Should return rounded average of two middle elements for even count."""
        # Arrange: 4 elements, median is avg(2,3) = 2.5 -> rounds to 2
        ids = [1, 2, 3, 4]
        
        # Act
        result = skill_proficiency_breakdown_service._calculate_median(ids)
        
        # Assert
        assert result == 2  # (2+3)/2 = 2.5 rounds to 2
    
    def test_returns_none_when_empty(self):
        """Should return None when list is empty."""
        # Act
        result = skill_proficiency_breakdown_service._calculate_median([])
        
        # Assert
        assert result is None
    
    def test_single_value(self):
        """Should return the single value."""
        # Act
        result = skill_proficiency_breakdown_service._calculate_median([4])
        
        # Assert
        assert result == 4
    
    def test_median_with_duplicates(self):
        """Should handle duplicates correctly."""
        # Arrange: sorted = [1,1,2,2,2,3,5]  median is 4th element = 2
        ids = [2, 1, 5, 2, 3, 1, 2]
        
        # Act
        result = skill_proficiency_breakdown_service._calculate_median(ids)
        
        # Assert
        assert result == 2


class TestLevelNameMapping:
    """Test the LEVEL_NAME_MAPPING constant."""
    
    def test_beginner_maps_to_novice(self):
        """Should map 'Beginner' to 'Novice'."""
        mapping = skill_proficiency_breakdown_service.LEVEL_NAME_MAPPING
        assert mapping["Beginner"] == "Novice"
    
    def test_advanced_beginner_maps_correctly(self):
        """Should map 'Advanced Beginner' to 'Adv. Beginner'."""
        mapping = skill_proficiency_breakdown_service.LEVEL_NAME_MAPPING
        assert mapping["Advanced Beginner"] == "Adv. Beginner"
    
    def test_competent_maps_to_competent(self):
        """Should map 'Competent' to 'Competent'."""
        mapping = skill_proficiency_breakdown_service.LEVEL_NAME_MAPPING
        assert mapping["Competent"] == "Competent"
    
    def test_proficient_maps_to_proficient(self):
        """Should map 'Proficient' to 'Proficient'."""
        mapping = skill_proficiency_breakdown_service.LEVEL_NAME_MAPPING
        assert mapping["Proficient"] == "Proficient"
    
    def test_expert_maps_to_expert(self):
        """Should map 'Expert' to 'Expert'."""
        mapping = skill_proficiency_breakdown_service.LEVEL_NAME_MAPPING
        assert mapping["Expert"] == "Expert"
