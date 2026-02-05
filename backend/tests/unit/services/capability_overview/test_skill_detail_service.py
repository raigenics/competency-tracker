"""
Unit tests for capability_overview/skill_detail_service.py

Tests GET /skills/{skill_id} endpoint functionality.
Coverage: Skill detail fetching, proficiency distribution, averages, response building.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_overview import skill_detail_service as service
from app.models import Skill


# ============================================================================
# TEST: get_skill_detail (Main Entry Point)
# ============================================================================

class TestGetSkillDetail:
    """Test the main skill detail function."""
    
    def test_returns_skill_detail_for_valid_id(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should return detailed skill information for valid skill ID."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skill = mock_skill(1, "Python", subcategory, category)
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_proficiency_distribution', return_value={"Expert": 5}):
                with patch.object(service, '_query_average_experience', return_value=3.5):
                    with patch.object(service, '_query_average_interest', return_value=4.2):
                        with patch.object(service, '_query_employee_count', return_value=10):
                            # Act
                            result = service.get_skill_detail(mock_db, skill_id=1)
        
        # Assert
        assert result.skill_id == 1
        assert result.skill_name == "Python"
        assert result.employee_count == 10
        assert result.proficiency_distribution == {"Expert": 5}
        assert result.avg_years_experience == 3.5
        assert result.avg_interest_level == 4.2
    
    def test_raises_error_when_skill_not_found(self, mock_db):
        """Should raise ValueError when skill ID doesn't exist."""
        # Arrange
        with patch.object(service, '_query_skill_by_id', return_value=None):
            # Act & Assert
            with pytest.raises(ValueError, match="Skill with ID 999 not found"):
                service.get_skill_detail(mock_db, skill_id=999)
    
    def test_includes_proficiency_distribution(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should include proficiency level distribution in response."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skill = mock_skill(1, "Java", subcategory, category)
        proficiency_dist = {"Beginner": 2, "Intermediate": 5, "Expert": 3}
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_proficiency_distribution', return_value=proficiency_dist):
                with patch.object(service, '_query_average_experience', return_value=4.0):
                    with patch.object(service, '_query_average_interest', return_value=3.8):
                        with patch.object(service, '_query_employee_count', return_value=10):
                            # Act
                            result = service.get_skill_detail(mock_db, skill_id=1)
        
        # Assert
        assert result.proficiency_distribution == proficiency_dist
    
    def test_includes_average_experience(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should include average years of experience."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategory = mock_subcategory(1, "ML", category)
        skill = mock_skill(1, "TensorFlow", subcategory, category)
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_proficiency_distribution', return_value={}):
                with patch.object(service, '_query_average_experience', return_value=5.75):
                    with patch.object(service, '_query_average_interest', return_value=4.5):
                        with patch.object(service, '_query_employee_count', return_value=8):
                            # Act
                            result = service.get_skill_detail(mock_db, skill_id=1)
        
        # Assert
        assert result.avg_years_experience == 5.75
    
    def test_includes_average_interest_level(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should include average interest level."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Frontend", category)
        skill = mock_skill(1, "React", subcategory, category)
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_proficiency_distribution', return_value={}):
                with patch.object(service, '_query_average_experience', return_value=2.5):
                    with patch.object(service, '_query_average_interest', return_value=4.8):
                        with patch.object(service, '_query_employee_count', return_value=12):
                            # Act
                            result = service.get_skill_detail(mock_db, skill_id=1)
        
        # Assert
        assert result.avg_interest_level == 4.8
    
    def test_handles_null_averages(
        self, mock_db, mock_skill, mock_subcategory, mock_category
    ):
        """Should handle None values for averages when no data available."""
        # Arrange
        category = mock_category(1, "New Category")
        subcategory = mock_subcategory(1, "New Subcat", category)
        skill = mock_skill(1, "New Skill", subcategory, category)
        
        with patch.object(service, '_query_skill_by_id', return_value=skill):
            with patch.object(service, '_query_proficiency_distribution', return_value={}):
                with patch.object(service, '_query_average_experience', return_value=None):
                    with patch.object(service, '_query_average_interest', return_value=None):
                        with patch.object(service, '_query_employee_count', return_value=0):
                            # Act
                            result = service.get_skill_detail(mock_db, skill_id=1)
        
        # Assert
        assert result.avg_years_experience is None
        assert result.avg_interest_level is None


# ============================================================================
# TEST: _query_skill_by_id (Query Function)
# ============================================================================

class TestQuerySkillById:
    """Test skill query by ID with eager loading."""
    
    def test_queries_skill_by_id(self, mock_db):
        """Should query skill by ID."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
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
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Act
        result = service._query_skill_by_id(mock_db, skill_id=999)
        
        # Assert
        assert result is None
    
    def test_eager_loads_category_relationships(self, mock_db):
        """Should use joinedload for subcategory and category relationships."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Act
        service._query_skill_by_id(mock_db, skill_id=1)
        
        # Assert
        mock_query.options.assert_called_once()


# ============================================================================
# TEST: _query_proficiency_distribution (Proficiency Query)
# ============================================================================

class TestQueryProficiencyDistribution:
    """Test proficiency level distribution query."""
    
    def test_returns_proficiency_distribution(self, mock_db):
        """Should return dict of proficiency levels and counts."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [("Beginner", 3), ("Expert", 5)]
        
        # Act
        result = service._query_proficiency_distribution(mock_db, skill_id=1)
        
        # Assert
        assert result == {"Beginner": 3, "Expert": 5}
        mock_query.filter.assert_called_once()
        mock_query.group_by.assert_called_once()
    
    def test_returns_empty_dict_when_no_employees(self, mock_db):
        """Should return empty dict when no employees have the skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_proficiency_distribution(mock_db, skill_id=999)
        
        # Assert
        assert result == {}
    
    def test_groups_by_proficiency_level(self, mock_db):
        """Should group employee skills by proficiency level."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [("Intermediate", 10)]
        
        # Act
        result = service._query_proficiency_distribution(mock_db, skill_id=1)
        
        # Assert
        mock_query.group_by.assert_called_once()
        assert "Intermediate" in result


# ============================================================================
# TEST: _query_average_experience (Average Experience Query)
# ============================================================================

class TestQueryAverageExperience:
    """Test average years of experience query."""
    
    def test_returns_average_experience(self, mock_db):
        """Should return average years of experience for skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 4.5
        
        # Act
        result = service._query_average_experience(mock_db, skill_id=1)
        
        # Assert
        assert result == 4.5
        mock_query.filter.assert_called()
        mock_query.scalar.assert_called_once()
    
    def test_returns_none_when_no_data(self, mock_db):
        """Should return None when no employees have experience data."""
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
        
        # Assert
        # Verify that filter was called (should include isnot(None) check)
        assert mock_query.filter.call_count >= 1


# ============================================================================
# TEST: _query_average_interest (Average Interest Query)
# ============================================================================

class TestQueryAverageInterest:
    """Test average interest level query."""
    
    def test_returns_average_interest(self, mock_db):
        """Should return average interest level for skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 4.2
        
        # Act
        result = service._query_average_interest(mock_db, skill_id=1)
        
        # Assert
        assert result == 4.2
        mock_query.filter.assert_called()
        mock_query.scalar.assert_called_once()
    
    def test_returns_none_when_no_data(self, mock_db):
        """Should return None when no employees have interest data."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        # Act
        result = service._query_average_interest(mock_db, skill_id=999)
        
        # Assert
        assert result is None
    
    def test_filters_out_null_values(self, mock_db):
        """Should filter out NULL interest values."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 4.0
        
        # Act
        result = service._query_average_interest(mock_db, skill_id=1)
        
        # Assert
        # Verify that filter was called (should include isnot(None) check)
        assert mock_query.filter.call_count >= 1


# ============================================================================
# TEST: _query_employee_count (Employee Count Query)
# ============================================================================

class TestQueryEmployeeCount:
    """Test employee count query for a skill."""
    
    def test_returns_employee_count(self, mock_db):
        """Should return count of distinct employees with skill."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 25
        
        # Act
        result = service._query_employee_count(mock_db, skill_id=1)
        
        # Assert
        assert result == 25
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


# ============================================================================
# TEST: _build_skill_detail_response (Response Building)
# ============================================================================

class TestBuildSkillDetailResponse:
    """Test skill detail response building."""
    
    def test_builds_complete_response(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should build complete SkillDetailResponse from data."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skill = mock_skill(1, "Python", subcategory, category)
        proficiency_dist = {"Beginner": 2, "Expert": 5}
        
        # Act
        result = service._build_skill_detail_response(
            skill, employee_count=10, proficiency_dist=proficiency_dist,
            avg_experience=4.567, avg_interest=3.891
        )
        
        # Assert
        assert result.skill_id == 1
        assert result.skill_name == "Python"
        assert result.employee_count == 10
        assert result.proficiency_distribution == proficiency_dist
        assert result.avg_years_experience == 4.57  # Rounded
        assert result.avg_interest_level == 3.89  # Rounded
    
    def test_handles_none_averages(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should handle None values for averages."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(1, "Backend", category)
        skill = mock_skill(1, "Go", subcategory, category)
        
        # Act
        result = service._build_skill_detail_response(
            skill, employee_count=0, proficiency_dist={},
            avg_experience=None, avg_interest=None
        )
        
        # Assert
        assert result.avg_years_experience is None
        assert result.avg_interest_level is None
    
    def test_includes_category_info(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should include category information in response."""
        # Arrange
        category = mock_category(1, "Data Science")
        subcategory = mock_subcategory(2, "ML", category)
        skill = mock_skill(3, "TensorFlow", subcategory, category)
        
        # Act
        result = service._build_skill_detail_response(
            skill, employee_count=8, proficiency_dist={},
            avg_experience=3.0, avg_interest=4.0
        )
        
        # Assert
        assert result.category.category_id == 1
        assert result.category.category_name == "Data Science"
        assert result.category.subcategory_id == 2
        assert result.category.subcategory_name == "ML"


# ============================================================================
# TEST: _build_category_info (Pure Function)
# ============================================================================

class TestBuildCategoryInfo:
    """Test category info building from skill relationships."""
    
    def test_builds_category_info_with_subcategory(
        self, mock_skill, mock_subcategory, mock_category
    ):
        """Should build CategoryInfo with both category and subcategory."""
        # Arrange
        category = mock_category(1, "Programming")
        subcategory = mock_subcategory(2, "Frontend", category)
        skill = mock_skill(3, "React", subcategory, category)
        
        # Act
        result = service._build_category_info(skill)
        
        # Assert
        assert result.category_id == 1
        assert result.category_name == "Programming"
        assert result.subcategory_id == 2
        assert result.subcategory_name == "Frontend"
    
    def test_handles_skill_without_subcategory(
        self, mock_skill, mock_category
    ):
        """Should handle skill with category but no subcategory."""
        # Arrange
        category = mock_category(1, "Soft Skills")
        skill = mock_skill(1, "Communication", None, category)
        
        # Act
        result = service._build_category_info(skill)
        
        # Assert
        assert result.category_id == 1
        assert result.category_name == "Soft Skills"
        assert result.subcategory_id is None
        assert result.subcategory_name is None


# ============================================================================
# TEST: _round_average (Pure Function)
# ============================================================================

class TestRoundAverage:
    """Test average rounding function."""
    
    def test_rounds_to_two_decimal_places(self):
        """Should round average to 2 decimal places."""
        # Act & Assert
        assert service._round_average(4.567) == 4.57
        assert service._round_average(3.891) == 3.89
        assert service._round_average(2.125) == 2.12
    
    def test_handles_integer_values(self):
        """Should handle integer values."""
        # Act & Assert
        assert service._round_average(5.0) == 5.0
        assert service._round_average(3.00) == 3.0
    
    def test_returns_none_for_none_input(self):
        """Should return None when input is None."""
        # Act & Assert
        assert service._round_average(None) is None
    
    def test_rounds_up_correctly(self):
        """Should round up when appropriate."""
        # Act & Assert
        assert service._round_average(2.555) == 2.56
        assert service._round_average(4.995) == 5.0
    
    def test_rounds_down_correctly(self):
        """Should round down when appropriate."""
        # Act & Assert
        assert service._round_average(3.123) == 3.12
        assert service._round_average(1.444) == 1.44
