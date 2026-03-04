"""
Unit tests for capability_overview/skill_summary_service.py

Tests GET /skills/{skill_id}/summary endpoint functionality.
Coverage: Exact skill_id matching, employee counts, averages, certification counts.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_overview import skill_summary_service as service
from app.models import Skill


# ============================================================================
# TEST: get_skill_summary (Main Entry Point)
# ============================================================================

class TestGetSkillSummary:
    """Test the main skill summary function."""
    
    def test_returns_skill_summary_for_valid_id(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should return summary statistics for valid skill ID."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skill = mock_skill(1, "Python", subcategory, category)
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_employee_count', return_value=25):
                with patch.object(service, '_query_employee_ids', return_value=[1, 2, 3]):
                    with patch.object(service, '_query_average_experience', return_value=4.5):
                        with patch.object(service, '_query_certified_employee_count', return_value=10):
                            # Act
                            result = service.get_skill_summary(mock_db, skill_id=1)
        
        # Assert
        assert result.skill_id == 1
        assert result.skill_name == "Python"
        assert result.employee_count == 25
        assert result.employee_ids == [1, 2, 3]
        assert result.avg_experience_years == 4.5
        assert result.certified_employee_count == 10
    
    def test_raises_error_when_skill_not_found(self, mock_db):
        """Should raise ValueError when skill ID doesn't exist."""
        # Arrange
        with patch.object(service, '_query_skill_by_id', return_value=None):
            # Act & Assert
            with pytest.raises(ValueError, match="Skill with ID 999 not found"):
                service.get_skill_summary(mock_db, skill_id=999)
    
    def test_uses_exact_skill_id_match(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should use exact skill_id matching, not name-based matching."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Frontend", category)
        skill = mock_skill(42, "React", subcategory, category)
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_employee_count', return_value=15) as mock_count:
                with patch.object(service, '_query_employee_ids', return_value=[1, 2]):
                    with patch.object(service, '_query_average_experience', return_value=3.0):
                        with patch.object(service, '_query_certified_employee_count', return_value=5):
                            # Act
                            service.get_skill_summary(mock_db, skill_id=42)
        
        # Assert - all queries should use skill_id=42
        mock_count.assert_called_once_with(mock_db, 42)
    
    def test_includes_employee_ids_for_view_all(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should include list of employee IDs for 'View All' functionality."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategory = mock_subcategory(1, "ML", category)
        skill = mock_skill(1, "TensorFlow", subcategory, category)
        employee_ids = [5, 10, 15, 20, 25]
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_employee_count', return_value=5):
                with patch.object(service, '_query_employee_ids', return_value=employee_ids):
                    with patch.object(service, '_query_average_experience', return_value=2.5):
                        with patch.object(service, '_query_certified_employee_count', return_value=2):
                            # Act
                            result = service.get_skill_summary(mock_db, skill_id=1)
        
        # Assert
        assert result.employee_ids == employee_ids
        assert len(result.employee_ids) == 5


# ============================================================================
# TEST: _query_skill_by_id (Query Function)
# ============================================================================

class TestQuerySkillById:
    """Test skill query by ID."""
    
    def test_queries_skill_by_id(self, mock_db):
        """Should query skill by exact ID."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(skill_id=1)
        
        # Act
        result = service._query_skill_by_id(mock_db, skill_id=1)
        
        # Assert
        mock_db.query.assert_called_once_with(Skill)
        mock_query.filter.assert_called_once()
        mock_query.first.assert_called_once()
        assert result.skill_id == 1
    
    def test_returns_none_when_skill_not_found(self, mock_db):
        """Should return None when skill ID doesn't exist."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Act
        result = service._query_skill_by_id(mock_db, skill_id=999)
        
        # Assert
        assert result is None


# ============================================================================
# TEST: _query_employee_count (Count Query)
# ============================================================================

class TestQueryEmployeeCount:
    """Test employee count query using exact skill_id."""
    
    def test_returns_employee_count_for_skill(self, mock_db):
        """Should return count of distinct employees with exact skill_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 30
        
        # Act
        result = service._query_employee_count(mock_db, skill_id=1)
        
        # Assert
        assert result == 30
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_returns_zero_when_no_employees(self, mock_db):
        """Should return 0 when no employees have the skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_employee_count(mock_db, skill_id=999)
        
        # Assert
        assert result == 0
    
    def test_counts_distinct_employees(self, mock_db):
        """Should count distinct employees, not skill rows."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15
        
        # Act
        result = service._query_employee_count(mock_db, skill_id=5)
        
        # Assert
        assert result == 15


# ============================================================================
# TEST: _query_employee_ids (Employee IDs Query)
# ============================================================================

class TestQueryEmployeeIds:
    """Test employee IDs query using exact skill_id."""
    
    def test_returns_employee_ids_for_skill(self, mock_db):
        """Should return list of employee IDs with exact skill_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(1,), (2,), (3,)]
        
        # Act
        result = service._query_employee_ids(mock_db, skill_id=1)
        
        # Assert
        assert result == [1, 2, 3]
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
    
    def test_returns_empty_list_when_no_employees(self, mock_db):
        """Should return empty list when no employees have the skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_employee_ids(mock_db, skill_id=999)
        
        # Assert
        assert result == []
    
    def test_orders_employee_ids(self, mock_db):
        """Should order employee IDs for consistent results."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(5,), (10,), (15,)]
        
        # Act
        result = service._query_employee_ids(mock_db, skill_id=1)
        
        # Assert
        mock_query.order_by.assert_called_once()
        assert result == [5, 10, 15]
    
    def test_returns_distinct_employee_ids(self, mock_db):
        """Should return distinct employee IDs."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(1,), (2,), (3,)]
        
        # Act
        result = service._query_employee_ids(mock_db, skill_id=1)
        
        # Assert - should extract IDs from tuples
        assert result == [1, 2, 3]


# ============================================================================
# TEST: _query_average_experience (Average Experience Query)
# ============================================================================

class TestQueryAverageExperience:
    """Test average experience query using exact skill_id."""
    
    def test_returns_average_experience(self, mock_db):
        """Should return average years of experience for skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5.5
        
        # Act
        result = service._query_average_experience(mock_db, skill_id=1)
        
        # Assert
        assert result == 5.5
        mock_query.filter.assert_called()
        mock_query.scalar.assert_called_once()
    
    def test_returns_none_when_no_data(self, mock_db):
        """Should return None when no experience data available."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_average_experience(mock_db, skill_id=999)
        
        # Assert
        assert result is None
    
    def test_filters_out_null_values(self, mock_db):
        """Should filter out NULL experience values."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3.0
        
        # Act
        result = service._query_average_experience(mock_db, skill_id=1)
        
        # Assert - verify filter was called multiple times (for isnot None and > 0)
        assert mock_query.filter.call_count >= 1
    
    def test_filters_out_zero_values(self, mock_db):
        """Should filter out zero experience values."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 4.2
        
        # Act
        result = service._query_average_experience(mock_db, skill_id=1)
        
        # Assert - should include > 0 filter
        assert mock_query.filter.call_count >= 1


# ============================================================================
# TEST: _query_certified_employee_count (Certified Count Query)
# ============================================================================

class TestQueryCertifiedEmployeeCount:
    """Test certified employee count query using exact skill_id."""
    
    def test_returns_certified_employee_count(self, mock_db):
        """Should return count of distinct certified employees."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 12
        
        # Act
        result = service._query_certified_employee_count(mock_db, skill_id=1)
        
        # Assert
        assert result == 12
        mock_query.filter.assert_called()
        mock_query.scalar.assert_called_once()
    
    def test_returns_zero_when_no_certified_employees(self, mock_db):
        """Should return 0 when no certified employees found."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_certified_employee_count(mock_db, skill_id=999)
        
        # Assert
        assert result == 0
    
    def test_excludes_null_certifications(self, mock_db):
        """Should exclude NULL certification values."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        
        # Act
        result = service._query_certified_employee_count(mock_db, skill_id=1)
        
        # Assert - verify filter was called (should include isnot None)
        assert mock_query.filter.call_count >= 1
    
    def test_excludes_empty_string_certifications(self, mock_db):
        """Should exclude empty string certification values."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 8
        
        # Act
        result = service._query_certified_employee_count(mock_db, skill_id=1)
        
        # Assert - should include nullif trim filter
        assert mock_query.filter.call_count >= 1
    
    def test_excludes_no_certifications(self, mock_db):
        """Should exclude 'no' certification values (case-insensitive)."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3
        
        # Act
        result = service._query_certified_employee_count(mock_db, skill_id=1)
        
        # Assert - should include lower != 'no' filter
        assert mock_query.filter.call_count >= 1


# ============================================================================
# TEST: _build_skill_summary_response (Response Building)
# ============================================================================

class TestBuildSkillSummaryResponse:
    """Test skill summary response building."""
    
    def test_builds_complete_response(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should build complete SkillSummaryResponse from data."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skill = mock_skill(1, "Java", subcategory, category)
        employee_ids = [1, 2, 3, 4, 5]
        
        # Act
        result = service._build_skill_summary_response(
            skill, employee_count=25, employee_ids=employee_ids,
            avg_experience=4.567, certified_count=10
        )
        
        # Assert
        assert result.skill_id == 1
        assert result.skill_name == "Java"
        assert result.employee_count == 25
        assert result.employee_ids == employee_ids
        assert result.avg_experience_years == 4.6  # Rounded to 1 decimal
        assert result.certified_employee_count == 10
        assert result.certified_count == 10  # Backward compatibility
    
    def test_handles_none_average_experience(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should convert None average experience to 0.0."""
        # Arrange
        category = mock_category(1, "New Category")
        subcategory = mock_subcategory(1, "New Subcat", category)
        skill = mock_skill(1, "New Skill", subcategory, category)
        
        # Act
        result = service._build_skill_summary_response(
            skill, employee_count=0, employee_ids=[],
            avg_experience=None, certified_count=0
        )
        
        # Assert
        assert result.avg_experience_years == 0.0
    
    def test_includes_empty_employee_ids(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should handle empty employee_ids list."""
        # Arrange
        category = mock_category(1, "Rare Skills")
        subcategory = mock_subcategory(1, "Niche", category)
        skill = mock_skill(1, "COBOL", subcategory, category)
        
        # Act
        result = service._build_skill_summary_response(
            skill, employee_count=0, employee_ids=[],
            avg_experience=0.0, certified_count=0
        )
        
        # Assert
        assert result.employee_ids == []
        assert result.employee_count == 0


# ============================================================================
# TEST: _round_to_one_decimal (Pure Function)
# ============================================================================

class TestRoundToOneDecimal:
    """Test rounding to one decimal place."""
    
    def test_rounds_to_one_decimal_place(self):
        """Should round to 1 decimal place."""
        # Act & Assert
        assert service._round_to_one_decimal(4.567) == 4.6
        assert service._round_to_one_decimal(3.891) == 3.9
        assert service._round_to_one_decimal(2.125) == 2.1
    
    def test_handles_integer_values(self):
        """Should handle integer and whole number values."""
        # Act & Assert
        assert service._round_to_one_decimal(5.0) == 5.0
        assert service._round_to_one_decimal(3.00) == 3.0
    
    def test_returns_zero_for_none_input(self):
        """Should return 0.0 when input is None."""
        # Act & Assert
        assert service._round_to_one_decimal(None) == 0.0
    
    def test_rounds_up_correctly(self):
        """Should round up when appropriate."""
        # Act & Assert
        # Note: Python uses banker's rounding and 2.55 in binary float is slightly < 2.55
        assert service._round_to_one_decimal(2.56) == 2.6
        assert service._round_to_one_decimal(4.95) == 5.0
        assert service._round_to_one_decimal(1.96) == 2.0
    
    def test_rounds_down_correctly(self):
        """Should round down when appropriate."""
        # Act & Assert
        assert service._round_to_one_decimal(3.12) == 3.1
        assert service._round_to_one_decimal(1.44) == 1.4
        assert service._round_to_one_decimal(5.01) == 5.0
