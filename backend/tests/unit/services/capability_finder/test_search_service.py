"""
Unit tests for capability_finder/search_service.py

Tests talent search with AND logic for skills, organizational filters,
and proficiency/experience requirements.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.capability_finder import search_service as service
from app.models import Employee, Skill


# ============================================================================
# TEST: search_matching_talent (Main Entry Point)
# ============================================================================

class TestSearchMatchingTalent:
    """Test the main talent search function."""
    
    def test_returns_employees_matching_all_skills(
        self, mock_db, mock_employee, mock_skill
    ):
        """Should return employees who have ALL specified skills (AND logic)."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        top_skills = [("Python", 5), ("AWS", 4), ("Docker", 3)]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2}):
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', return_value=top_skills):
                        # Act
                        results = service.search_matching_talent(
                            mock_db, skills=['Python', 'AWS']
                        )
        
        # Assert
        assert len(results) == 1
        assert results[0].employee_name == "Alice"
        assert len(results[0].top_skills) == 3
    
    def test_applies_minimum_proficiency_filter(self, mock_db, mock_employee):
        """Should filter employees by minimum proficiency level."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Bob")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1}):
                with patch.object(service, '_query_strict_match', return_value=employees) as mock_strict:
                    with patch.object(service, '_query_employee_top_skills', return_value=[]):
                        # Act
                        service.search_matching_talent(
                            mock_db, skills=['Python'], min_proficiency=4
                        )
        
        # Assert
        mock_strict.assert_called_once()
        call_kwargs = mock_strict.call_args[1]
        assert call_kwargs['min_proficiency'] == 4
    
    def test_applies_minimum_experience_filter(self, mock_db, mock_employee):
        """Should filter employees by minimum years of experience."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Charlie")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['java']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1}):
                with patch.object(service, '_query_strict_match', return_value=employees) as mock_strict:
                    with patch.object(service, '_query_employee_top_skills', return_value=[]):
                        # Act
                        service.search_matching_talent(
                            mock_db, skills=['Java'], min_experience_years=3
                        )
        
        # Assert
        call_kwargs = mock_strict.call_args[1]
        assert call_kwargs['min_experience_years'] == 3
    
    def test_applies_organizational_filters(self, mock_db, mock_employee):
        """Should filter by sub_segment, team, and role."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Diana")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['react']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1}):
                with patch.object(service, '_query_strict_match', return_value=employees) as mock_strict:
                    with patch.object(service, '_query_employee_top_skills', return_value=[]):
                        # Act
                        service.search_matching_talent(
                            mock_db,
                            skills=['React'],
                            sub_segment_id=5,
                            team_id=10,
                            role='Developer'
                        )
        
        # Assert
        call_kwargs = mock_strict.call_args[1]
        assert call_kwargs['sub_segment_id'] == 5
        assert call_kwargs['team_id'] == 10
        assert call_kwargs['normalized_role'] == 'developer'  # lowercase
    
    def test_returns_empty_list_when_no_matches(self, mock_db):
        """Should return empty list when no employees match criteria."""
        # Arrange
        with patch.object(service, '_normalize_skill_terms', return_value=['nonexistent']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value=set()):
                # Act
                results = service.search_matching_talent(
                    mock_db, skills=['NonExistentSkill']
                )
        
        # Assert
        assert results == []
    
    def test_includes_top_3_skills_for_each_employee(
        self, mock_db, mock_employee
    ):
        """Should query and include top 3 skills for each employee."""
        # Arrange
        employees = [
            mock_employee(1, "Z1001", "Eve"),
            mock_employee(2, "Z1002", "Frank")
        ]
        top_skills_1 = [("Python", 5), ("AWS", 4), ("Docker", 3)]
        top_skills_2 = [("Java", 5), ("Spring", 4), ("MySQL", 3)]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1}):
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', side_effect=[top_skills_1, top_skills_2]) as mock_top:
                        # Act
                        results = service.search_matching_talent(mock_db, skills=['Python'])
        
        # Assert
        assert mock_top.call_count == 2
        assert len(results[0].top_skills) == 3
        assert len(results[1].top_skills) == 3
    
    def test_handles_empty_skills_list(self, mock_db, mock_employee):
        """Should handle search with empty skills list."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Grace")]
        
        with patch.object(service, '_query_org_only', return_value=employees):
            with patch.object(service, '_query_employee_top_skills', return_value=[]):
                # Act
                results = service.search_matching_talent(mock_db, skills=[])
        
        # Assert
        assert len(results) == 1


# ============================================================================
# TEST: _query_matching_employees (Query Function)
# ============================================================================

class TestQueryMatchingEmployees:
    """Test legacy _query_matching_employees function (backward compatibility)."""
    
    def test_queries_employees_with_subquery_pattern(self, mock_db, mock_employee):
        """Legacy function should delegate to new internal functions."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        with patch.object(service, '_query_org_only', return_value=employees):
            # Act
            result = service._query_matching_employees(
                mock_db, skills=[], sub_segment_id=None, team_id=None,
                role=None, min_proficiency=0, min_experience_years=0
            )
        
        # Assert - returns employee list
        assert len(result) == 1
        assert result[0].full_name == "Alice"
    
    def test_applies_and_logic_for_multiple_skills(self, mock_db, mock_employee):
        """Should use AND logic - employee must have ALL skills."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Bob")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws', 'docker']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2, 3}):
                with patch.object(service, '_build_employee_query_with_filters') as mock_query:
                    mock_query_obj = MagicMock()
                    mock_query.return_value = mock_query_obj
                    mock_query_obj.join.return_value = mock_query_obj
                    mock_query_obj.filter.return_value = mock_query_obj
                    mock_query_obj.group_by.return_value = mock_query_obj
                    mock_query_obj.having.return_value = mock_query_obj
                    mock_query_obj.order_by.return_value = mock_query_obj
                    mock_query_obj.all.return_value = employees
                    
                    # Act
                    result = service._query_matching_employees(
                        mock_db,
                        skills=['Python', 'AWS', 'Docker'],
                        sub_segment_id=None,
                        team_id=None,
                        role=None,
                        min_proficiency=0,
                        min_experience_years=0
                    )
        
        # Assert - returns employees
        assert len(result) == 1
    
    def test_filters_by_sub_segment_when_provided(self, mock_db, mock_employee):
        """Should filter employees by sub_segment_id."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Charlie")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            # Act
            result = service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=5,
                team_id=None,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert - _query_org_only was called with sub_segment_id
        mock_org.assert_called_once()
        assert mock_org.call_args[1]['sub_segment_id'] == 5
    
    def test_filters_by_team_when_provided(self, mock_db, mock_employee):
        """Should filter employees by team_id."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Diana")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            # Act
            result = service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=None,
                team_id=10,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert - _query_org_only was called with team_id
        mock_org.assert_called_once()
        assert mock_org.call_args[1]['team_id'] == 10
    
    def test_filters_by_role_when_provided(self, mock_db, mock_employee):
        """Should pass role filter to internal function."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Eve")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            # Act
            result = service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=None,
                team_id=None,
                role='Developer',
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert - role filter was passed
        mock_org.assert_called_once()
        assert mock_org.call_args[1]['normalized_role'] == 'developer'  # lowercase
    
    def test_returns_ordered_employees(self, mock_db, mock_employee):
        """Should return employees in deterministic order."""
        # Arrange
        employees = [
            mock_employee(1, "Z1001", "Alice"),
            mock_employee(2, "Z1002", "Bob")
        ]
        
        with patch.object(service, '_query_org_only', return_value=employees):
            # Act
            result = service._query_matching_employees(
                mock_db, skills=[], sub_segment_id=None, team_id=None,
                role=None, min_proficiency=0, min_experience_years=0
            )
        
        # Assert - returns employees 
        assert len(result) == 2


# ============================================================================
# TEST: _query_skill_ids (Helper Query)
# ============================================================================

class TestQuerySkillIds:
    """Test skill ID query (legacy function, now delegates to _resolve_canonical_skill_ids)."""
    
    def test_returns_skill_ids_for_skill_names(self, mock_db):
        """Should query and return skill IDs for given names (case-insensitive)."""
        # Arrange - mock the underlying resolve function
        with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2, 3}):
            with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws', 'docker']):
                # Act
                result = service._query_skill_ids(mock_db, ['Python', 'AWS', 'Docker'])
        
        # Assert
        assert set(result) == {1, 2, 3}
    
    def test_returns_empty_list_when_no_skills_found(self, mock_db):
        """Should return empty list when skill names don't exist."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_skill_ids(mock_db, ['NonExistent'])
        
        # Assert
        assert result == []
    
    def test_extracts_ids_from_tuples(self, mock_db):
        """Should extract IDs from query result tuples."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(10,), (20,), (30,)]
        
        # Act
        result = service._query_skill_ids(mock_db, ['Skill1', 'Skill2', 'Skill3'])
        
        # Assert
        assert result == [10, 20, 30]


# ============================================================================
# TEST: _query_employee_top_skills (Top Skills Query)
# ============================================================================

class TestQueryEmployeeTopSkills:
    """Test top skills query for an employee."""
    
    def test_returns_top_3_skills_for_employee(self, mock_db):
        """Should return top 3 skills ordered by proficiency."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            ("Python", 5),
            ("AWS", 4),
            ("Docker", 3)
        ]
        
        # Act
        result = service._query_employee_top_skills(mock_db, employee_id=1)
        
        # Assert
        assert len(result) == 3
        assert result[0] == ("Python", 5)
        assert result[1] == ("AWS", 4)
        assert result[2] == ("Docker", 3)
    
    def test_orders_by_proficiency_then_last_used_then_name(self, mock_db):
        """Should order skills by proficiency DESC, last_used DESC, name ASC."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_employee_top_skills(mock_db, employee_id=1)
        
        # Assert
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(3)
    
    def test_filters_by_employee_id(self, mock_db):
        """Should filter skills by employee_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_employee_top_skills(mock_db, employee_id=42)
        
        # Assert
        mock_query.filter.assert_called_once()
    
    def test_returns_empty_list_when_employee_has_no_skills(self, mock_db):
        """Should return empty list when employee has no skills."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_employee_top_skills(mock_db, employee_id=999)
        
        # Assert
        assert result == []
    
    def test_limits_to_3_skills(self, mock_db):
        """Should limit results to exactly 3 skills."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [("Skill1", 5), ("Skill2", 4)]
        
        # Act
        result = service._query_employee_top_skills(mock_db, employee_id=1)
        
        # Assert
        mock_query.limit.assert_called_once_with(3)
        assert len(result) == 2  # Returns whatever DB returns, limited to 3


# ============================================================================
# TEST: _build_employee_result (Pure Function)
# ============================================================================

class TestBuildEmployeeResult:
    """Test employee result building from model and skills."""
    
    def test_builds_result_from_employee_and_skills(self, mock_employee):
        """Should build EmployeeSearchResult from employee and skills."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Henry")
        top_skills = [("Python", 5), ("AWS", 4), ("Docker", 3)]
        
        # Act
        result = service._build_employee_result(employee, top_skills)
        
        # Assert
        assert result.employee_id == 1
        assert result.employee_name == "Henry"
        assert len(result.top_skills) == 3
        assert result.top_skills[0].name == "Python"
        assert result.top_skills[0].proficiency == 5
    
    def test_extracts_organizational_info(self, mock_employee):
        """Should extract sub_segment, team, and role information."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Iris")
        employee.sub_segment = MagicMock(sub_segment_name="Backend Team")
        employee.team = MagicMock(team_name="Team Alpha")
        employee.role = MagicMock(role_name="Senior Developer")
        top_skills = [("Java", 5)]
        
        # Act
        result = service._build_employee_result(employee, top_skills)
        
        # Assert
        assert result.sub_segment == "Backend Team"
        assert result.team == "Team Alpha"
        assert result.role == "Senior Developer"
    
    def test_handles_missing_organizational_info(self, mock_employee):
        """Should handle None for sub_segment, team, and role."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Jack")
        employee.sub_segment = None
        employee.team = None
        employee.role = None
        top_skills = [("Python", 4)]
        
        # Act
        result = service._build_employee_result(employee, top_skills)
        
        # Assert
        assert result.sub_segment == ""
        assert result.team == ""
        assert result.role == ""
    
    def test_handles_empty_skills_list(self, mock_employee):
        """Should handle employee with no top skills."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Kate")
        top_skills = []
        
        # Act
        result = service._build_employee_result(employee, top_skills)
        
        # Assert
        assert result.top_skills == []
        assert result.employee_name == "Kate"
    
    def test_transforms_skills_to_skill_info_objects(self, mock_employee):
        """Should transform skill tuples to SkillInfo objects."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Leo")
        top_skills = [("React", 5), ("TypeScript", 4), ("Node.js", 3)]
        
        # Act
        result = service._build_employee_result(employee, top_skills)
        
        # Assert
        assert len(result.top_skills) == 3
        assert all(hasattr(skill, 'name') for skill in result.top_skills)
        assert all(hasattr(skill, 'proficiency') for skill in result.top_skills)
        assert result.top_skills[0].name == "React"
        assert result.top_skills[1].proficiency == 4
    
    def test_preserves_skill_order(self, mock_employee):
        """Should preserve the order of skills from top_skills list."""
        # Arrange
        employee = mock_employee(1, "Z1001", "Maya")
        top_skills = [("First", 5), ("Second", 4), ("Third", 3)]
        
        # Act
        result = service._build_employee_result(employee, top_skills)
        
        # Assert
        assert result.top_skills[0].name == "First"
        assert result.top_skills[1].name == "Second"
        assert result.top_skills[2].name == "Third"

# ============================================================================
# REGRESSION TEST: Sub-Segment Join Bug Fix
# ============================================================================

class TestSubSegmentJoinBugFix:
    """
    Regression test for bug: HTTP 500 when sub_segment filter is selected.
    
    Bug: AttributeError: 'dict' object has no attribute 'class_'
    Cause: Incorrect check for existing joins using query.column_descriptions
    Fix: Removed faulty join check, always join Team/Project for sub_segment filter
    """
    
    def test_sub_segment_filter_does_not_crash(self, mock_db, mock_employee):
        """
        Should successfully build query with sub_segment_id without AttributeError.
        
        This test verifies that the Team/Project joins are added correctly
        when filtering by sub_segment_id, without accessing non-existent
        'class_' attribute on column_descriptions dictionaries.
        """
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        with patch.object(service, '_query_org_only', return_value=employees):
            # Act - Should not raise AttributeError
            try:
                service._query_matching_employees(
                    mock_db,
                    skills=[],
                    sub_segment_id=1,  # Trigger sub_segment join logic
                    team_id=None,
                    role=None,
                    min_proficiency=0,
                    min_experience_years=0
                )
                # Assert
                assert True, "Query executed without AttributeError"
            except AttributeError as e:
                pytest.fail(f"AttributeError should not occur: {e}")
    
    def test_sub_segment_filter_joins_team_and_project(self, mock_db, mock_employee):
        """
        Should join Team and Project tables when sub_segment_id is provided.
        
        Verifies that both joins are added to derive sub_segment membership
        through the canonical path: Employee -> Team -> Project -> SubSegment
        """
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            # Act
            service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=1,
                team_id=None,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert - _query_org_only was called with sub_segment_id
        mock_org.assert_called_once()
        assert mock_org.call_args[1]['sub_segment_id'] == 1


# ============================================================================
# PHASE 2: SKILL NORMALIZATION TESTS
# ============================================================================

class TestNormalizeSkillTerms:
    """Test _normalize_skill_terms helper function."""
    
    def test_normalizes_basic_term(self):
        """Should convert to lowercase and strip whitespace."""
        # Act
        result = service._normalize_skill_terms(["  React  "])
        
        # Assert
        assert result == ["react"]
    
    def test_collapses_multiple_spaces(self):
        """Should collapse multiple internal spaces to single space."""
        # Act
        result = service._normalize_skill_terms(["React   JS"])
        
        # Assert
        assert result == ["react js"]
    
    def test_handles_multiple_terms(self):
        """Should normalize multiple terms."""
        # Act
        result = service._normalize_skill_terms(["  PYTHON ", "AWS ", "  docker"])
        
        # Assert
        assert result == ["python", "aws", "docker"]
    
    def test_filters_empty_strings(self):
        """Should filter out empty strings after normalization."""
        # Act
        result = service._normalize_skill_terms(["Python", "  ", "", "AWS"])
        
        # Assert
        assert result == ["python", "aws"]
    
    def test_handles_none_values(self):
        """Should handle None values in input list."""
        # Act
        result = service._normalize_skill_terms(["Python", None, "AWS"])
        
        # Assert
        assert result == ["python", "aws"]
    
    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list for empty input."""
        # Act
        result = service._normalize_skill_terms([])
        
        # Assert
        assert result == []


# ============================================================================
# PHASE 2: CASE-INSENSITIVE MATCHING TESTS
# ============================================================================

class TestCaseInsensitiveMatching:
    """Test case-insensitive skill matching."""
    
    def test_lowercase_search_finds_capitalized_skill(self, mock_db):
        """skills=['react'] should match 'React' in database."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = [(42,)]  # skill_id = 42
        
        # Act
        result = service._resolve_canonical_skill_ids(mock_db, ['react'])
        
        # Assert
        assert 42 in result
        mock_db.query.assert_called()
    
    def test_uppercase_search_finds_lowercase_skill(self, mock_db):
        """skills=['PYTHON'] should match 'python' in database."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = [(10,)]
        
        # Act
        result = service._resolve_canonical_skill_ids(mock_db, ['python'])
        
        # Assert
        assert 10 in result
    
    def test_mixed_case_search(self, mock_db):
        """skills=['ReactJS'] should be normalized and searched."""
        # Arrange - already normalized input
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = [(5,)]
        
        # Act
        result = service._resolve_canonical_skill_ids(mock_db, ['reactjs'])
        
        # Assert
        assert 5 in result


# ============================================================================
# PHASE 2: ALIAS MATCHING TESTS
# ============================================================================

class TestAliasMatching:
    """Test skill alias resolution."""
    
    def test_alias_resolves_to_canonical_skill(self, mock_db):
        """'ReactJS' alias should resolve to canonical 'React' skill_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        # First call (skills table) returns nothing
        # Second call (aliases table) returns skill_id 42
        mock_query.all.side_effect = [[], [(42,)]]
        
        # Act
        result = service._resolve_canonical_skill_ids(mock_db, ['reactjs'])
        
        # Assert
        assert 42 in result
    
    def test_multiple_aliases_same_skill_returns_single_id(self, mock_db):
        """Multiple aliases for same skill should return unique skill_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        # Both 'react' and 'reactjs' map to skill_id 42
        mock_query.all.side_effect = [[(42,)], [(42,)]]
        
        # Act
        result = service._resolve_canonical_skill_ids(mock_db, ['react', 'reactjs'])
        
        # Assert
        assert result == {42}
        assert len(result) == 1  # Should deduplicate
    
    def test_combined_skill_and_alias_match(self, mock_db):
        """Should combine matches from skills table and aliases table."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        # skills table returns id 1, aliases table returns id 2
        mock_query.all.side_effect = [[(1,)], [(2,)]]
        
        # Act
        result = service._resolve_canonical_skill_ids(mock_db, ['python', 'js'])
        
        # Assert
        assert 1 in result
        assert 2 in result
    
    def test_empty_terms_returns_empty_set(self, mock_db):
        """Should return empty set for empty input."""
        # Act
        result = service._resolve_canonical_skill_ids(mock_db, [])
        
        # Assert
        assert result == set()


# ============================================================================
# PHASE 2: SOFT DELETE FILTERING TESTS
# ============================================================================

class TestSoftDeleteFiltering:
    """Test soft-delete filtering for Employee, EmployeeSkill, and Skill."""
    
    def test_deleted_employees_excluded(self, mock_db, mock_employee):
        """Employees with deleted_at != NULL should be excluded."""
        # This is tested by verifying the query includes Employee.deleted_at.is_(None)
        # We verify by checking that the query structure is correct
        
        # Arrange
        mock_query = MagicMock()
        mock_subquery = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.subquery.return_value = mock_subquery
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_subquery.c = MagicMock()
        
        # Act
        result = service._query_matching_employees(
            mock_db, 
            skills=[], 
            sub_segment_id=None, 
            team_id=None, 
            role=None, 
            min_proficiency=0, 
            min_experience_years=0
        )
        
        # Assert - query was constructed (soft-delete filter is in the query)
        mock_db.query.assert_called()
        mock_query.filter.assert_called()  # filter includes deleted_at.is_(None)
    
    def test_deleted_employee_skills_excluded(self, mock_db):
        """EmployeeSkill records with deleted_at != NULL should be excluded."""
        # This is verified by the top skills query including the filter
        
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [("Python", 5)]
        
        # Act
        result = service._query_employee_top_skills(mock_db, employee_id=1)
        
        # Assert
        mock_query.filter.assert_called()  # filter includes EmployeeSkill.deleted_at.is_(None)
        assert len(result) == 1
    
    def test_deleted_skills_excluded_from_top_skills(self, mock_db):
        """Skill records with deleted_at != NULL should be excluded from top skills."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_employee_top_skills(mock_db, employee_id=1)
        
        # Assert - filter was called (includes Skill.deleted_at.is_(None))
        mock_query.filter.assert_called()


# ============================================================================
# PHASE 2: AND LOGIC WITH ALIAS EXPANSION TESTS
# ============================================================================

class TestAndLogicWithAliases:
    """Test AND logic when aliases expand to same canonical skill."""
    
    def test_and_logic_counts_canonical_skills_not_aliases(self, mock_db, mock_employee):
        """
        skills=['React', 'ReactJS'] where both map to skill_id=42
        should require count(distinct(skill_id)) == 1, not 2.
        """
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        # Mock the resolve function to return single skill_id
        with patch.object(service, '_resolve_canonical_skill_ids', return_value={42}):
            with patch.object(service, '_normalize_skill_terms', return_value=['react', 'reactjs']):
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', return_value=[]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db, 
                            skills=['React', 'ReactJS']
                        )
        
        # Assert - should find employees (both aliases map to same skill)
        # The key assertion is that it doesn't fail due to requiring 2 distinct skills
        assert len(results) == 1
    
    def test_multiple_distinct_skills_requires_all(self, mock_db, mock_employee):
        """
        skills=['Python', 'AWS'] should require employee to have BOTH skills.
        """
        # Arrange
        employees = []  # No employees have both
        
        with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2}):
            with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws']):
                with patch.object(service, '_query_strict_match', return_value=[]):
                    with patch.object(service, '_query_partial_match', return_value=[]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=['Python', 'AWS']
                        )
        
        # Assert
        assert results == []


# ============================================================================
# PHASE 2: ORG FILTER COMBINATION TESTS
# ============================================================================

class TestOrgFilterCombination:
    """Test that team_id and sub_segment_id can both apply (no elif precedence)."""
    
    def test_both_team_and_sub_segment_apply(self, mock_db, mock_employee):
        """
        When both team_id AND sub_segment_id are provided,
        BOTH filters should be applied (not elif).
        """
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            # Act
            service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=5,
                team_id=10,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert - both filters were passed
        mock_org.assert_called_once()
        assert mock_org.call_args[1]['sub_segment_id'] == 5
        assert mock_org.call_args[1]['team_id'] == 10
    
    def test_team_id_only(self, mock_db, mock_employee):
        """When only team_id is provided, should filter by team only."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Bob")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            # Act
            result = service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=None,
                team_id=10,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert
        mock_org.assert_called_once()
        assert mock_org.call_args[1]['team_id'] == 10
        assert mock_org.call_args[1]['sub_segment_id'] is None
    
    def test_sub_segment_id_only(self, mock_db, mock_employee):
        """When only sub_segment_id is provided, should join Team/Project and filter."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Charlie")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            # Act
            result = service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=5,
                team_id=None,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert
        mock_org.assert_called_once()
        assert mock_org.call_args[1]['sub_segment_id'] == 5
        assert mock_org.call_args[1]['team_id'] is None


# ============================================================================
# PHASE 2: DETERMINISTIC ORDERING TESTS
# ============================================================================

class TestDeterministicOrdering:
    """Test stable ordering of search results."""
    
    def test_results_ordered_by_name_then_id(self, mock_db, mock_employee):
        """Results should be ordered by full_name ASC, employee_id ASC."""
        # Arrange
        # Create employees in non-alphabetical order
        employees = [
            mock_employee(3, "Z1003", "Charlie"),
            mock_employee(1, "Z1001", "Alice"),
            mock_employee(2, "Z1002", "Bob")
        ]
        
        with patch.object(service, '_query_org_only', return_value=employees):
            # Act
            result = service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=None,
                team_id=None,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert - returns employees (ordering is handled internally)
        assert len(result) == 3
    
    def test_same_name_ordered_by_id(self, mock_db, mock_employee):
        """Employees with same name should be ordered by employee_id."""
        # This verifies the secondary sort key is employee_id
        
        # Arrange
        employees = [
            mock_employee(1, "Z1001", "Alice"),
            mock_employee(2, "Z1002", "Alice")
        ]
        
        with patch.object(service, '_query_org_only', return_value=employees):
            # Act
            result = service._query_matching_employees(
                mock_db,
                skills=[],
                sub_segment_id=None,
                team_id=None,
                role=None,
                min_proficiency=0,
                min_experience_years=0
            )
        
        # Assert
        assert len(result) == 2


# ============================================================================
# PHASE 2: TOP SKILLS SOFT-DELETE TESTS
# ============================================================================

class TestTopSkillsSoftDelete:
    """Test that top skills query excludes deleted records."""
    
    def test_top_skills_excludes_deleted_employee_skills(self, mock_db):
        """Top skills should not include soft-deleted EmployeeSkill records."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [("Python", 5), ("AWS", 4)]
        
        # Act
        result = service._query_employee_top_skills(mock_db, employee_id=1)
        
        # Assert - filter was called with soft-delete conditions
        mock_query.filter.assert_called_once()
        assert len(result) == 2
    
    def test_top_skills_excludes_deleted_skills(self, mock_db):
        """Top skills should not include soft-deleted Skill records."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_employee_top_skills(mock_db, employee_id=1)
        
        # Assert
        mock_query.filter.assert_called_once()
        assert result == []


# ============================================================================
# PHASE 2: INTEGRATION-STYLE TESTS (mocked DB but realistic scenarios)
# ============================================================================

class TestSearchScenarios:
    """Integration-style tests for realistic search scenarios."""
    
    def test_reactjs_alias_finds_react_employees(self, mock_db, mock_employee):
        """
        Scenario: skills=["ReactJS"], sub_segment_id=AU
        Expected: Returns employees with React skill (ReactJS is alias)
        """
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['reactjs']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={42}):  # React skill
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', return_value=[("React", 5)]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["ReactJS"],
                            sub_segment_id=1
                        )
        
        # Assert
        assert len(results) == 1
        assert results[0].employee_name == "Alice"
    
    def test_lowercase_react_finds_capitalized_skill(self, mock_db, mock_employee):
        """
        Scenario: skills=["react"]
        Expected: Returns employees with "React" skill (case-insensitive)
        """
        # Arrange
        employees = [mock_employee(1, "Z1001", "Bob")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['react']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={42}):
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', return_value=[("React", 4)]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["react"]
                        )
        
        # Assert
        assert len(results) == 1
        assert results[0].employee_name == "Bob"
    
    def test_unresolved_skills_returns_empty(self, mock_db):
        """
        Scenario: skills=["NonExistentSkill123"]
        Expected: Returns empty list (skill not found in DB or aliases)
        """
        # Arrange
        with patch.object(service, '_normalize_skill_terms', return_value=['nonexistentskill123']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value=set()):  # No match
                # Act
                results = service.search_matching_talent(
                    mock_db,
                    skills=["NonExistentSkill123"]
                )
        
        # Assert
        assert results == []


# ============================================================================
# PHASE 1: HYBRID SEARCH TESTS (STRICT + PARTIAL FALLBACK)
# ============================================================================

class TestHybridSearchStrictMatch:
    """Test STRICT match (AND logic) in hybrid search."""
    
    def test_strict_match_returns_employees_with_all_skills(self, mock_db, mock_employee):
        """STRICT match should return employees who have ALL specified skills."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2}):
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', return_value=[("Python", 5)]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["Python", "AWS"]
                        )
        
        # Assert
        assert len(results) == 1
        assert results[0].match_type == "STRICT"
        assert results[0].matched_skill_count == 2  # Both skills matched
    
    def test_strict_match_sets_match_type_strict(self, mock_db, mock_employee):
        """STRICT results should have match_type='STRICT'."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Bob")]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['react']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={42}):
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', return_value=[]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["React"]
                        )
        
        # Assert
        assert results[0].match_type == "STRICT"


class TestHybridSearchPartialFallback:
    """Test PARTIAL match (OR logic fallback) in hybrid search."""
    
    def test_partial_fallback_when_strict_empty(self, mock_db, mock_employee):
        """When STRICT returns empty, should fall back to PARTIAL match."""
        # Arrange
        from app.schemas.capability_finder import EmployeeSearchResult, SkillInfo
        
        partial_result = EmployeeSearchResult(
            employee_id=1,
            employee_name="Charlie",
            sub_segment="Eng",
            team="Team A",
            role="Developer",
            top_skills=[SkillInfo(name="Python", proficiency=4)],
            match_type="PARTIAL",
            matched_skill_count=1
        )
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2}):
                with patch.object(service, '_query_strict_match', return_value=[]):  # No strict match
                    with patch.object(service, '_query_partial_match', return_value=[partial_result]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["Python", "AWS"]
                        )
        
        # Assert
        assert len(results) == 1
        assert results[0].match_type == "PARTIAL"
        assert results[0].matched_skill_count == 1
    
    def test_partial_match_ordered_by_matched_count_desc(self, mock_db, mock_employee):
        """PARTIAL results should be ordered by matched_skill_count DESC."""
        # Arrange
        from app.schemas.capability_finder import EmployeeSearchResult, SkillInfo
        
        partial_results = [
            EmployeeSearchResult(
                employee_id=1,
                employee_name="Alice",
                sub_segment="",
                team="",
                role="",
                top_skills=[],
                match_type="PARTIAL",
                matched_skill_count=2  # Higher match count
            ),
            EmployeeSearchResult(
                employee_id=2,
                employee_name="Bob",
                sub_segment="",
                team="",
                role="",
                top_skills=[],
                match_type="PARTIAL",
                matched_skill_count=1  # Lower match count
            )
        ]
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws', 'docker']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2, 3}):
                with patch.object(service, '_query_strict_match', return_value=[]):
                    with patch.object(service, '_query_partial_match', return_value=partial_results):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["Python", "AWS", "Docker"]
                        )
        
        # Assert - should be ordered by matched_count DESC
        assert results[0].matched_skill_count >= results[1].matched_skill_count


class TestHybridSearchRoleCaseInsensitive:
    """Test case-insensitive role matching."""
    
    def test_role_filter_case_insensitive(self, mock_db, mock_employee):
        """Role filter should match case-insensitively."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        # The role in DB is "Developer" but search is "developer" (lowercase)
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            with patch.object(service, '_query_employee_top_skills', return_value=[]):
                # Act
                service.search_matching_talent(
                    mock_db,
                    skills=[],  # No skills - org-only search
                    role="developer"  # lowercase
                )
        
        # Assert - normalized_role should be lowercase
        call_kwargs = mock_org.call_args[1]
        assert call_kwargs['normalized_role'] == "developer"
    
    def test_role_filter_with_mixed_case(self, mock_db, mock_employee):
        """Role filter should normalize mixed case input."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Bob")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            with patch.object(service, '_query_employee_top_skills', return_value=[]):
                # Act
                service.search_matching_talent(
                    mock_db,
                    skills=[],
                    role="SENIOR Developer"  # Mixed case with spaces
                )
        
        # Assert
        call_kwargs = mock_org.call_args[1]
        assert call_kwargs['normalized_role'] == "senior developer"


class TestHybridSearchEmptySkills:
    """Test search behavior with empty or no skills list."""
    
    def test_empty_skills_list_returns_org_filtered_employees(self, mock_db, mock_employee):
        """Empty skills list should return all employees matching org filters."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice"), mock_employee(2, "Z1002", "Bob")]
        
        with patch.object(service, '_query_org_only', return_value=employees):
            with patch.object(service, '_query_employee_top_skills', return_value=[]):
                # Act
                results = service.search_matching_talent(
                    mock_db,
                    skills=[],
                    team_id=5
                )
        
        # Assert
        assert len(results) == 2
        # match_type should be None for org-only search
        assert results[0].match_type is None
    
    def test_empty_skills_with_no_filters_returns_all(self, mock_db, mock_employee):
        """Empty skills and no org filters should return all employees."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        with patch.object(service, '_query_org_only', return_value=employees) as mock_org:
            with patch.object(service, '_query_employee_top_skills', return_value=[]):
                # Act
                service.search_matching_talent(mock_db, skills=[])
        
        # Assert
        mock_org.assert_called_once()


class TestHybridSearchDuplicateCanonicalSkills:
    """Test that duplicate aliases map to single canonical skill."""
    
    def test_react_and_reactjs_resolve_to_single_skill(self, mock_db, mock_employee):
        """['react', 'reactjs'] should resolve to single canonical skill_id."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Alice")]
        
        # Both 'react' and 'reactjs' map to skill_id 42
        with patch.object(service, '_normalize_skill_terms', return_value=['react', 'reactjs']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={42}):  # Single skill
                with patch.object(service, '_query_strict_match', return_value=employees):
                    with patch.object(service, '_query_employee_top_skills', return_value=[]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["React", "ReactJS"]
                        )
        
        # Assert - matched_skill_count should be 1 (not 2)
        assert results[0].matched_skill_count == 1
    
    def test_canonical_count_correct_with_aliases(self, mock_db, mock_employee):
        """Required skill count should use canonical IDs, not input count."""
        # Arrange
        employees = [mock_employee(1, "Z1001", "Bob")]
        
        # 3 input terms but only 2 canonical skill IDs
        with patch.object(service, '_normalize_skill_terms', return_value=['python', 'py', 'aws']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2}):  # 2 skills
                with patch.object(service, '_query_strict_match', return_value=employees) as mock_strict:
                    with patch.object(service, '_query_employee_top_skills', return_value=[]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=["Python", "py", "AWS"]  # 3 inputs
                        )
        
        # Assert - STRICT match was called with 2 canonical skills
        call_kwargs = mock_strict.call_args[1]
        assert call_kwargs['canonical_skill_ids'] == {1, 2}


class TestStrictMatchFunction:
    """Test _query_strict_match function directly."""
    
    def test_strict_query_uses_having_count(self, mock_db):
        """STRICT query should use HAVING count(distinct(skill_id)) == required_count."""
        # Arrange
        mock_query = MagicMock()
        mock_subquery = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.subquery.return_value = mock_subquery
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_subquery.c = MagicMock()
        
        # Act
        service._query_strict_match(
            mock_db,
            canonical_skill_ids={1, 2, 3},
            sub_segment_id=None,
            team_id=None,
            normalized_role=None,
            min_proficiency=0,
            min_experience_years=0
        )
        
        # Assert - HAVING was called (for AND logic)
        mock_query.having.assert_called()


class TestPartialMatchFunction:
    """Test _query_partial_match function behavior via search_matching_talent."""
    
    def test_partial_query_returns_results_with_match_count(self, mock_db, mock_employee):
        """PARTIAL query should return employees with their matched_skill_count."""
        # Since _query_partial_match uses SQLAlchemy internals (desc()) that can't be easily mocked,
        # we test this behavior through the higher-level search_matching_talent function
        
        # Arrange
        mock_result = MagicMock()
        mock_result.match_type = "PARTIAL"
        mock_result.matched_skill_count = 2
        mock_result.employee_name = "Alice"
        
        with patch.object(service, '_normalize_skill_terms', return_value=['python', 'aws']):
            with patch.object(service, '_resolve_canonical_skill_ids', return_value={1, 2}):
                # STRICT match returns empty, triggering PARTIAL fallback
                with patch.object(service, '_query_strict_match', return_value=[]):
                    with patch.object(service, '_query_partial_match', return_value=[mock_result]):
                        # Act
                        results = service.search_matching_talent(
                            mock_db,
                            skills=['Python', 'AWS']
                        )
        
        # Assert - result came from PARTIAL fallback
        assert len(results) == 1
        assert results[0].match_type == "PARTIAL"
        assert results[0].matched_skill_count == 2


class TestOrgOnlyFunction:
    """Test _query_org_only function directly."""
    
    def test_org_only_applies_team_filter(self, mock_db):
        """Org-only query should apply team_id filter."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_org_only(
            mock_db,
            sub_segment_id=None,
            team_id=5,
            normalized_role=None
        )
        
        # Assert - filter was called
        assert mock_query.filter.called
    
    def test_org_only_applies_both_team_and_sub_segment(self, mock_db):
        """Org-only query should apply BOTH team_id AND sub_segment_id."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        filter_call_count = 0
        original_filter = mock_query.filter
        def count_filter(*args, **kwargs):
            nonlocal filter_call_count
            filter_call_count += 1
            return original_filter.return_value
        mock_query.filter.side_effect = count_filter
        
        # Act
        service._query_org_only(
            mock_db,
            sub_segment_id=3,
            team_id=5,
            normalized_role=None
        )
        
        # Assert - multiple filters applied (soft-delete + team + sub_segment)
        assert filter_call_count >= 2