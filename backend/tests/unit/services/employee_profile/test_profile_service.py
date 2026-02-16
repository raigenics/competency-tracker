"""
Unit tests for employee_profile/profile_service.py

Tests employee profile detail with all skills.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from app.services.employee_profile import profile_service


class TestGetEmployeeProfile:
    """Test the main public function get_employee_profile()."""
    
    def test_returns_employee_profile_for_valid_id(self, mock_db, mock_employee):
        """Should return complete employee profile when employee exists."""
        # Arrange
        employee = mock_employee(1, "Z1001", "John Doe")
        employee.employee_skills = []
        
        with patch.object(profile_service, '_query_employee_by_id', return_value=employee):
            # Act
            result = profile_service.get_employee_profile(mock_db, 1)
            
            # Assert
            assert result is not None
            assert result["employee_id"] == 1
            assert result["full_name"] == "John Doe"
            assert "skills" in result
    
    def test_raises_value_error_when_employee_not_found(self, mock_db):
        """Should raise ValueError when employee doesn't exist."""
        # Arrange
        with patch.object(profile_service, '_query_employee_by_id', return_value=None):
            # Act & Assert
            with pytest.raises(ValueError, match="Employee with ID 999 not found"):
                profile_service.get_employee_profile(mock_db, 999)
    
    def test_calls_query_and_build_functions(self, mock_db, mock_employee):
        """Should call query and build functions with correct parameters."""
        # Arrange
        employee = mock_employee(1)
        employee.employee_skills = []
        employee.email = 'test@example.com'
        employee.team_id = 1
        # Set up team relationship chain
        employee.team = Mock()
        employee.team.project = Mock()
        employee.team.project.sub_segment = Mock()
        employee.team.project.sub_segment.segment = Mock()
        employee.team.project.sub_segment.segment.segment_id = 1
        employee.team.project.sub_segment.sub_segment_id = 10
        employee.team.project.project_id = 100
        employee.team.team_name = 'Team A'
        employee.team.project.project_name = 'Project A'
        employee.team.project.sub_segment.sub_segment_name = 'Sub A'
        employee.role = None
        
        with patch.object(profile_service, '_query_employee_by_id', return_value=employee) as mock_query:
            
            # Act
            result = profile_service.get_employee_profile(mock_db, 1)
            
            # Assert
            mock_query.assert_called_once_with(mock_db, 1)
            assert 'skills' in result
            assert 'organization' in result


class TestQueryEmployeeById:
    """Test the _query_employee_by_id() function."""
    
    def test_queries_employee_with_eager_loading(self, mock_db):
        """Should query employee with all relationships eager loaded."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = Mock()
        
        # Act
        profile_service._query_employee_by_id(mock_db, 1)
        
        # Assert
        mock_db.query.assert_called_once()
        mock_query.options.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.first.assert_called_once()
    
    def test_returns_none_when_employee_not_found(self, mock_db):
        """Should return None when employee doesn't exist."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Act
        result = profile_service._query_employee_by_id(mock_db, 999)
        
        # Assert
        assert result is None


class TestBuildProfileResponse:
    """Test the _build_profile_response() pure function."""
    
    def test_builds_complete_profile_dict(self, mock_employee, mock_organization):
        """Should build complete profile dict from employee model."""
        # Arrange
        role = mock_organization("role", 1, "Developer")
        employee = mock_employee(1, "Z1001", "John Doe", role=role, start_date=date(2020, 1, 15))
        employee.employee_skills = []
        employee.email = 'john@example.com'
        employee.team_id = 1
        
        # Set up org relationship chain (team -> project -> sub_segment -> segment)
        segment = mock_organization("segment", 100, "DTS")
        sub_seg = mock_organization("sub_segment", 10, "FW")
        sub_seg.segment = segment
        proj = mock_organization("project", 1, "Project A")
        proj.sub_segment = sub_seg
        team = mock_organization("team", 1, "Team X")
        team.project = proj
        employee.team = team
        
        # Act
        result = profile_service._build_profile_response(employee)
        
        # Assert
        assert result["employee_id"] == 1
        assert result["zid"] == "Z1001"
        assert result["full_name"] == "John Doe"
        assert result["role"]["role_name"] == "Developer"
        assert "organization" in result
        assert "skills" in result
        assert "skills_count" in result
        # New org IDs should be present
        assert result["team_id"] == 1
        assert result["project_id"] == 1
        assert result["sub_segment_id"] == 10
        assert result["segment_id"] == 100
    
    def test_includes_skills_count(self, mock_employee):
        """Should include count of skills in profile."""
        # Arrange
        employee = mock_employee(1)
        employee.employee_skills = []
        mock_skills = [{"skill_name": "Python"}, {"skill_name": "SQL"}, {"skill_name": "Java"}]
        
        with patch.object(profile_service, '_build_skills_list', return_value=mock_skills), \
             patch.object(profile_service, '_build_organization_dict', return_value={}), \
             patch.object(profile_service, '_format_date', return_value=None):
            
            # Act
            result = profile_service._build_profile_response(employee)
            
            # Assert
            assert result["skills_count"] == 3


class TestBuildSkillsList:
    """Test the _build_skills_list() pure function."""
    
    def test_builds_skills_list_from_employee_skills(self, mock_employee, mock_employee_skill, 
                                                      mock_skill, mock_proficiency):
        """Should transform employee_skills to list of skill dicts."""
        # Arrange
        skill1 = mock_skill(1, "Python")
        skill2 = mock_skill(2, "SQL")
        prof1 = mock_proficiency(5, "Expert")
        prof2 = mock_proficiency(4, "Advanced")
        
        emp_skill1 = mock_employee_skill(1, 1, 1, skill=skill1, proficiency_level=prof1)
        emp_skill2 = mock_employee_skill(2, 1, 2, skill=skill2, proficiency_level=prof2)
        
        employee = mock_employee(1, "Z1001", "John Doe")
        employee.employee_skills = [emp_skill1, emp_skill2]
        
        with patch.object(profile_service, '_build_proficiency_dict', return_value={}):
            # Act
            result = profile_service._build_skills_list(employee)
            
            # Assert
            assert len(result) == 2
            assert result[0]["skill_name"] == "Python"
            assert result[1]["skill_name"] == "SQL"
    
    def test_includes_all_skill_fields(self, mock_employee, mock_employee_skill, mock_skill, mock_proficiency):
        """Should include all required skill fields in output."""
        # Arrange
        skill = mock_skill(1, "Python")
        prof = mock_proficiency(5, "Expert")
        emp_skill = mock_employee_skill(
            emp_skill_id=10,
            employee_id=1,
            skill_id=1,
            skill=skill,
            proficiency_level=prof,
            years_experience=5,
            last_used=2024,
            interest_level=5
        )
        
        employee = mock_employee(1, "Z1001", "John Doe")
        employee.employee_skills = [emp_skill]
        
        with patch.object(profile_service, '_build_proficiency_dict', return_value={}):
            # Act
            result = profile_service._build_skills_list(employee)
            
            # Assert
            assert result[0]["emp_skill_id"] == 10
            assert result[0]["employee_id"] == 1
            assert result[0]["employee_name"] == "John Doe"
            assert result[0]["skill_id"] == 1
            assert result[0]["skill_name"] == "Python"
            assert result[0]["years_experience"] == 5
            assert result[0]["last_used"] == 2024
            assert result[0]["interest_level"] == 5
    
    def test_returns_empty_list_when_no_skills(self, mock_employee):
        """Should return empty list when employee has no skills."""
        # Arrange
        employee = mock_employee(1)
        employee.employee_skills = []
        
        # Act
        result = profile_service._build_skills_list(employee)
        
        # Assert
        assert result == []


class TestExtractOrgIds:
    """Test the _extract_org_ids() pure function."""
    
    def test_extracts_all_org_ids_from_relationship_chain(self, mock_organization):
        """Should extract segment_id, sub_segment_id, project_id, team_id from relationships."""
        # Arrange
        segment = mock_organization("segment", 100, "DI")
        segment.segment_id = 100
        
        sub_seg = mock_organization("sub_segment", 200, "Engineering")
        sub_seg.segment = segment
        
        proj = mock_organization("project", 300, "Project A")
        proj.sub_segment = sub_seg
        
        team = mock_organization("team", 400, "Team X")
        team.project = proj
        
        employee = Mock()
        employee.team_id = 400
        employee.team = team
        
        # Act
        result = profile_service._extract_org_ids(employee)
        
        # Assert
        assert result["team_id"] == 400
        assert result["project_id"] == 300
        assert result["sub_segment_id"] == 200
        assert result["segment_id"] == 100
    
    def test_returns_none_for_missing_relationships(self):
        """Should return None values when relationships are missing."""
        # Arrange
        employee = Mock()
        employee.team_id = None
        employee.team = None
        
        # Act
        result = profile_service._extract_org_ids(employee)
        
        # Assert
        assert result["team_id"] is None
        assert result["project_id"] is None
        assert result["sub_segment_id"] is None
        assert result["segment_id"] is None


class TestBuildOrganizationDict:
    """Test the _build_organization_dict() pure function."""
    
    def test_builds_organization_dict_from_employee(self, mock_employee, mock_organization):
        """Should extract organization info from employee relationships via team chain."""
        # Arrange - set up relationship chain: team -> project -> sub_segment
        sub_seg = mock_organization("sub_segment", 1, "Engineering")
        proj = mock_organization("project", 1, "Project A")
        proj.sub_segment = sub_seg
        team = mock_organization("team", 1, "Team X")
        team.project = proj
        
        employee = mock_employee(1, "Z1001", "Alice", team=team)
        
        # Act
        result = profile_service._build_organization_dict(employee)
        
        # Assert
        assert result["sub_segment"] == "Engineering"
        assert result["project"] == "Project A"
        assert result["team"] == "Team X"


class TestBuildProficiencyDict:
    """Test the _build_proficiency_dict() pure function."""
    
    def test_builds_proficiency_dict_from_proficiency_level(self, mock_proficiency):
        """Should extract proficiency info from proficiency level object."""
        # Arrange
        proficiency = mock_proficiency(5, "Expert", description="Expert level mastery")
        
        # Act
        result = profile_service._build_proficiency_dict(proficiency)
        
        # Assert
        assert result["proficiency_level_id"] == 5
        assert result["level_name"] == "Expert"
        assert result["level_description"] == "Expert level mastery"


class TestFormatDate:
    """Test the _format_date() pure function."""
    
    def test_formats_date_to_iso_string(self):
        """Should format date object to ISO string."""
        # Arrange
        test_date = date(2024, 3, 15)
        
        # Act
        result = profile_service._format_date(test_date)
        
        # Assert
        assert result == "2024-03-15"
    
    def test_returns_none_for_none_input(self):
        """Should return None when given None."""
        # Act
        result = profile_service._format_date(None)
        
        # Assert
        assert result is None
    
    def test_handles_different_date_formats(self):
        """Should handle various date values."""
        # Arrange
        dates = [
            (date(2020, 1, 1), "2020-01-01"),
            (date(2024, 12, 31), "2024-12-31"),
            (None, None)
        ]
        
        # Act & Assert
        for input_date, expected in dates:
            result = profile_service._format_date(input_date)
            assert result == expected


class TestGetCurrentAllocation:
    """Test the _get_current_allocation() function."""
    
    def test_returns_allocation_for_current_project(self):
        """Should return allocation percentage for current project."""
        # Arrange
        employee = Mock()
        employee.project_id = 100
        
        allocation = Mock()
        allocation.project_id = 100
        allocation.end_date = None  # Active allocation
        allocation.allocation_pct = 75
        
        employee.project_allocations = [allocation]
        
        # Act
        result = profile_service._get_current_allocation(employee)
        
        # Assert
        assert result == 75
    
    def test_returns_none_when_no_allocations(self):
        """Should return None when employee has no project allocations."""
        # Arrange
        employee = Mock()
        employee.project_id = 100
        employee.project_allocations = []
        
        # Act
        result = profile_service._get_current_allocation(employee)
        
        # Assert
        assert result is None
    
    def test_returns_none_when_no_current_project(self):
        """Should return None when employee has no current project_id."""
        # Arrange
        employee = Mock()
        employee.project_id = None
        
        # Must have allocations to pass first check and reach project_id check
        allocation = Mock()
        allocation.project_id = 100
        allocation.end_date = None
        allocation.allocation_pct = 50
        employee.project_allocations = [allocation]
        
        # Act
        result = profile_service._get_current_allocation(employee)
        
        # Assert
        assert result is None
    
    def test_returns_none_when_allocation_has_end_date(self):
        """Should return None when allocation is not active (has end_date)."""
        # Arrange
        employee = Mock()
        employee.project_id = 100
        
        allocation = Mock()
        allocation.project_id = 100
        allocation.end_date = date(2024, 12, 31)  # Ended allocation
        allocation.allocation_pct = 50
        
        employee.project_allocations = [allocation]
        
        # Act
        result = profile_service._get_current_allocation(employee)
        
        # Assert
        assert result is None
    
    def test_returns_none_when_allocation_is_for_different_project(self):
        """Should return None when allocations are for different projects."""
        # Arrange
        employee = Mock()
        employee.project_id = 100
        
        allocation = Mock()
        allocation.project_id = 200  # Different project
        allocation.end_date = None
        allocation.allocation_pct = 100
        
        employee.project_allocations = [allocation]
        
        # Act
        result = profile_service._get_current_allocation(employee)
        
        # Assert
        assert result is None
    
    def test_finds_correct_allocation_among_multiple(self):
        """Should find the active allocation for current project among multiple."""
        # Arrange
        employee = Mock()
        employee.project_id = 100
        
        # Past allocation (ended)
        old_allocation = Mock()
        old_allocation.project_id = 100
        old_allocation.end_date = date(2023, 12, 31)
        old_allocation.allocation_pct = 50
        
        # Current allocation (active)
        current_allocation = Mock()
        current_allocation.project_id = 100
        current_allocation.end_date = None
        current_allocation.allocation_pct = 80
        
        # Different project allocation
        other_allocation = Mock()
        other_allocation.project_id = 200
        other_allocation.end_date = None
        other_allocation.allocation_pct = 100
        
        employee.project_allocations = [old_allocation, current_allocation, other_allocation]
        
        # Act
        result = profile_service._get_current_allocation(employee)
        
        # Assert
        assert result == 80
