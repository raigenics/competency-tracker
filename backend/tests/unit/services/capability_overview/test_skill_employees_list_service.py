"""
Unit tests for capability_overview/skill_employees_list_service.py

Tests employee list retrieval for View Employees table:
- Returns list of employees with proficiency, certification, and last_updated_days
- Handles missing skill gracefully
- Calculates days since last update correctly
- Determines certification status from string field
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch
from app.services.capability_overview import skill_employees_list_service
from app.schemas.skill import SkillEmployeesListResponse, SkillEmployeeListItem


class TestGetSkillEmployeesList:
    """Test the main public function get_skill_employees_list()."""
    
    def test_returns_complete_response_with_employees(self, mock_db):
        """Should return SkillEmployeesListResponse with employee list."""
        # Arrange
        skill_id = 42
        mock_skill = Mock()
        mock_skill.skill_name = "Python"
        
        mock_employee_data = [
            (1, "John Doe", "Core Engineering", "Project X", "Team Alpha", 4, "Proficient", "AWS Certified", datetime(2024, 1, 15, tzinfo=timezone.utc)),
            (2, "Jane Smith", "Data Science", "Project Y", "Team Beta", 3, "Competent", None, datetime(2024, 1, 10, tzinfo=timezone.utc)),
        ]
        
        with patch.object(skill_employees_list_service, '_query_skill', return_value=mock_skill), \
             patch.object(skill_employees_list_service, '_query_employee_skill_data', return_value=mock_employee_data):
            
            # Act
            result = skill_employees_list_service.get_skill_employees_list(mock_db, skill_id)
            
            # Assert
            assert isinstance(result, SkillEmployeesListResponse)
            assert result.skill_id == skill_id
            assert result.skill_name == "Python"
            assert result.total_count == 2
            assert len(result.employees) == 2
    
    def test_raises_value_error_when_skill_not_found(self, mock_db):
        """Should raise ValueError when skill does not exist."""
        # Arrange
        skill_id = 999
        with patch.object(skill_employees_list_service, '_query_skill', return_value=None):
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                skill_employees_list_service.get_skill_employees_list(mock_db, skill_id)
            
            assert "Skill with id 999 not found" in str(exc_info.value)
    
    def test_returns_empty_list_when_no_employees(self, mock_db):
        """Should return empty list when no employees have the skill."""
        # Arrange
        skill_id = 42
        mock_skill = Mock()
        mock_skill.skill_name = "Rare Skill"
        
        with patch.object(skill_employees_list_service, '_query_skill', return_value=mock_skill), \
             patch.object(skill_employees_list_service, '_query_employee_skill_data', return_value=[]):
            
            # Act
            result = skill_employees_list_service.get_skill_employees_list(mock_db, skill_id)
            
            # Assert
            assert result.employees == []
            assert result.total_count == 0
    
    def test_builds_correct_employee_list_items(self, mock_db):
        """Should build SkillEmployeeListItem with all required fields."""
        # Arrange
        skill_id = 42
        mock_skill = Mock()
        mock_skill.skill_name = "Python"
        
        mock_employee_data = [
            (100, "Alice Johnson", "Engineering", "Project A", "Team A", 5, "Expert", "Python Pro", datetime.now(timezone.utc) - timedelta(days=10)),
        ]
        
        with patch.object(skill_employees_list_service, '_query_skill', return_value=mock_skill), \
             patch.object(skill_employees_list_service, '_query_employee_skill_data', return_value=mock_employee_data):
            
            # Act
            result = skill_employees_list_service.get_skill_employees_list(mock_db, skill_id)
            
            # Assert
            emp = result.employees[0]
            assert emp.employee_id == 100
            assert emp.employee_name == "Alice Johnson"
            assert emp.sub_segment == "Engineering"
            assert emp.team_name == "Team A"
            assert emp.proficiency_level == 5
            assert emp.proficiency_label == "Expert"
            assert emp.certified == True
            assert emp.skill_last_updated_days == 10


class TestCalculateDaysSinceUpdate:
    """Test the _calculate_days_since_update() pure function."""
    
    def test_returns_none_when_last_updated_is_none(self):
        """Should return None when last_updated is None."""
        result = skill_employees_list_service._calculate_days_since_update(None)
        assert result is None
    
    def test_returns_zero_for_today(self):
        """Should return 0 for today's timestamp."""
        now = datetime.now(timezone.utc)
        result = skill_employees_list_service._calculate_days_since_update(now)
        assert result == 0
    
    def test_returns_correct_days_for_past_date(self):
        """Should return correct number of days for past dates."""
        ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
        result = skill_employees_list_service._calculate_days_since_update(ten_days_ago)
        assert result == 10
    
    def test_handles_timezone_naive_datetime(self):
        """Should handle timezone-naive datetime by treating as UTC."""
        naive_datetime = datetime.now() - timedelta(days=5)
        result = skill_employees_list_service._calculate_days_since_update(naive_datetime)
        # Should be approximately 5 days (may vary slightly due to test execution time)
        assert 4 <= result <= 6
    
    def test_never_returns_negative_days(self):
        """Should never return negative days (edge case for future dates)."""
        # Even if somehow a future date creeps in, return 0
        future_date = datetime.now(timezone.utc) + timedelta(days=10)
        result = skill_employees_list_service._calculate_days_since_update(future_date)
        assert result >= 0


class TestDetermineCertified:
    """Test the _determine_certified() pure function."""
    
    def test_returns_true_for_non_empty_string(self):
        """Should return True when certification has value."""
        assert skill_employees_list_service._determine_certified("AWS Certified") == True
        assert skill_employees_list_service._determine_certified("Python Pro") == True
        assert skill_employees_list_service._determine_certified("x") == True
    
    def test_returns_false_for_none(self):
        """Should return False when certification is None."""
        assert skill_employees_list_service._determine_certified(None) == False
    
    def test_returns_false_for_empty_string(self):
        """Should return False when certification is empty string."""
        assert skill_employees_list_service._determine_certified("") == False
    
    def test_returns_false_for_whitespace_only(self):
        """Should return False when certification is whitespace only."""
        assert skill_employees_list_service._determine_certified("   ") == False
        assert skill_employees_list_service._determine_certified("\t\n") == False


class TestBuildEmployeeListItems:
    """Test the _build_employee_list_items() transformation function."""
    
    def test_transforms_raw_data_to_schema_items(self):
        """Should transform raw tuples to SkillEmployeeListItem list."""
        raw_data = [
            (1, "John Doe", "Engineering", "Project Alpha", "Team A", 4, "Proficient", "Cert", datetime.now(timezone.utc) - timedelta(days=5)),
            (2, "Jane Smith", None, None, None, 2, "Adv. Beginner", None, None),
        ]
        
        result = skill_employees_list_service._build_employee_list_items(raw_data)
        
        assert len(result) == 2
        assert all(isinstance(item, SkillEmployeeListItem) for item in result)
        
        # First employee
        assert result[0].employee_id == 1
        assert result[0].employee_name == "John Doe"
        assert result[0].sub_segment == "Engineering"
        assert result[0].project_name == "Project Alpha"
        assert result[0].team_name == "Team A"
        assert result[0].proficiency_level == 4
        assert result[0].proficiency_label == "Proficient"
        assert result[0].certified == True
        assert result[0].skill_last_updated_days == 5
        
        # Second employee (with None values)
        assert result[1].employee_id == 2
        assert result[1].employee_name == "Jane Smith"
        assert result[1].sub_segment is None
        assert result[1].project_name is None
        assert result[1].team_name is None
        assert result[1].proficiency_level == 2
        assert result[1].proficiency_label == "Adv. Beginner"
        assert result[1].certified == False
        assert result[1].skill_last_updated_days is None
    
    def test_handles_empty_input(self):
        """Should return empty list for empty input."""
        result = skill_employees_list_service._build_employee_list_items([])
        assert result == []


class TestQuerySkill:
    """Test the _query_skill() repository function."""
    
    def test_queries_skill_by_id(self, mock_db):
        """Should query skill by ID and filter deleted records."""
        # Arrange
        skill_id = 42
        mock_skill = Mock()
        mock_skill.skill_name = "Python"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_skill
        
        # Act
        result = skill_employees_list_service._query_skill(mock_db, skill_id)
        
        # Assert
        assert result == mock_skill
        mock_db.query.assert_called_once()
    
    def test_returns_none_when_not_found(self, mock_db):
        """Should return None when skill not found."""
        # Arrange
        skill_id = 999
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = skill_employees_list_service._query_skill(mock_db, skill_id)
        
        # Assert
        assert result is None


# Pytest fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()
