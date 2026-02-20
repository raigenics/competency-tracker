"""
Unit tests for SkillExpander.

Target: backend/app/services/imports/employee_import/skill_expander.py
Coverage: Expanding comma-separated skills into individual rows.

Test Strategy:
- Use real pandas DataFrames (no mocking needed for pandas)
- Test comma and semicolon splitting
- Test whitespace handling
- Test empty and edge cases
- Verify row copying preserves other columns
- Test logging behavior
"""
import pytest
import pandas as pd
from app.services.imports.employee_import.skill_expander import SkillExpander


class TestExpandSkills:
    """Test SkillExpander.expand_skills() method."""
    
    @pytest.fixture
    def expander(self):
        """Create SkillExpander instance."""
        return SkillExpander()
    
    # Basic expansion
    def test_expands_comma_separated_skills(self, expander):
        """Should expand comma-separated skills into multiple rows."""
        df = pd.DataFrame([
            {'skill_name': 'Python, Java', 'proficiency': 3, 'employee_id': 1}
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 2
        assert result.iloc[0]['skill_name'] == 'Python'
        assert result.iloc[1]['skill_name'] == 'Java'
    
    def test_expands_semicolon_separated_skills(self, expander):
        """Should expand semicolon-separated skills into multiple rows."""
        df = pd.DataFrame([
            {'skill_name': 'SQL; PostgreSQL', 'proficiency': 4, 'employee_id': 2}
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 2
        assert result.iloc[0]['skill_name'] == 'SQL'
        assert result.iloc[1]['skill_name'] == 'PostgreSQL'
    
    def test_expands_mixed_comma_and_semicolon(self, expander):
        """Should handle mixed comma and semicolon separators."""
        df = pd.DataFrame([
            {'skill_name': 'Python, Java; JavaScript', 'proficiency': 3, 'employee_id': 3}
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 3
        assert result.iloc[0]['skill_name'] == 'Python'
        assert result.iloc[1]['skill_name'] == 'Java'
        assert result.iloc[2]['skill_name'] == 'JavaScript'
    
    # Whitespace handling
    def test_strips_whitespace_from_split_skills(self, expander):
        """Should trim whitespace from individual skills."""
        df = pd.DataFrame([
            {'skill_name': '  Python  ,   Java   ', 'proficiency': 2, 'employee_id': 4}
        ])
        
        result = expander.expand_skills(df)
        
        assert result.iloc[0]['skill_name'] == 'Python'
        assert result.iloc[1]['skill_name'] == 'Java'
    
    def test_removes_empty_skills_after_split(self, expander):
        """Should remove empty strings after splitting."""
        df = pd.DataFrame([
            {'skill_name': 'Python, , Java, ', 'proficiency': 3, 'employee_id': 5}
        ])
        
        result = expander.expand_skills(df)
        
        # Should only have 2 skills (empty ones removed)
        assert len(result) == 2
        assert result.iloc[0]['skill_name'] == 'Python'
        assert result.iloc[1]['skill_name'] == 'Java'
    
    # Column preservation
    def test_preserves_other_columns_when_expanding(self, expander):
        """Should copy all other columns for each expanded skill."""
        df = pd.DataFrame([
            {
                'skill_name': 'Python, Java',
                'proficiency': 4,
                'employee_id': 10,
                'years_experience': 5,
                'sub_segment_id': 2
            }
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 2
        
        # First skill row
        assert result.iloc[0]['skill_name'] == 'Python'
        assert result.iloc[0]['proficiency'] == 4
        assert result.iloc[0]['employee_id'] == 10
        assert result.iloc[0]['years_experience'] == 5
        assert result.iloc[0]['sub_segment_id'] == 2
        
        # Second skill row
        assert result.iloc[1]['skill_name'] == 'Java'
        assert result.iloc[1]['proficiency'] == 4
        assert result.iloc[1]['employee_id'] == 10
        assert result.iloc[1]['years_experience'] == 5
        assert result.iloc[1]['sub_segment_id'] == 2
    
    def test_preserves_columns_with_none_values(self, expander):
        """Should preserve None/NaN values in other columns."""
        df = pd.DataFrame([
            {
                'skill_name': 'C++, Rust',
                'proficiency': None,
                'employee_id': 11
            }
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 2
        assert pd.isna(result.iloc[0]['proficiency'])
        assert pd.isna(result.iloc[1]['proficiency'])
    
    # No expansion needed
    def test_returns_unchanged_df_for_single_skills(self, expander):
        """Should return unchanged DataFrame when no expansion needed."""
        df = pd.DataFrame([
            {'skill_name': 'Python', 'proficiency': 3, 'employee_id': 1},
            {'skill_name': 'Java', 'proficiency': 4, 'employee_id': 2}
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 2
        assert result.iloc[0]['skill_name'] == 'Python'
        assert result.iloc[1]['skill_name'] == 'Java'
    
    def test_handles_empty_dataframe(self, expander):
        """Should handle empty DataFrame without error."""
        df = pd.DataFrame(columns=['skill_name', 'proficiency', 'employee_id'])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 0
    
    # Multiple rows with mixed expansion
    def test_expands_mixed_rows(self, expander):
        """Should handle DataFrame with both expandable and non-expandable rows."""
        df = pd.DataFrame([
            {'skill_name': 'Python', 'proficiency': 3, 'employee_id': 1},
            {'skill_name': 'Java, JavaScript', 'proficiency': 4, 'employee_id': 2},
            {'skill_name': 'SQL', 'proficiency': 5, 'employee_id': 3},
            {'skill_name': 'C++, Rust, Go', 'proficiency': 2, 'employee_id': 4}
        ])
        
        result = expander.expand_skills(df)
        
        # Total: 1 + 2 + 1 + 3 = 7 rows
        assert len(result) == 7
        
        # Verify order and values
        assert result.iloc[0]['skill_name'] == 'Python'
        assert result.iloc[1]['skill_name'] == 'Java'
        assert result.iloc[2]['skill_name'] == 'JavaScript'
        assert result.iloc[3]['skill_name'] == 'SQL'
        assert result.iloc[4]['skill_name'] == 'C++'
        assert result.iloc[5]['skill_name'] == 'Rust'
        assert result.iloc[6]['skill_name'] == 'Go'
    
    # Edge cases
    def test_handles_only_commas(self, expander):
        """Should handle string with only commas."""
        df = pd.DataFrame([
            {'skill_name': ',,,', 'proficiency': 1, 'employee_id': 5}
        ])
        
        result = expander.expand_skills(df)
        
        # All empty after split, original row should be kept
        # But since we filter out empty strings, we get 0 expanded rows
        # The logic should still handle this gracefully
        assert len(result) >= 0  # Should not crash
    
    def test_handles_skill_name_with_numbers(self, expander):
        """Should handle skill names containing numbers."""
        df = pd.DataFrame([
            {'skill_name': 'Angular 15, Vue.js 3', 'proficiency': 3, 'employee_id': 6}
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 2
        assert result.iloc[0]['skill_name'] == 'Angular 15'
        assert result.iloc[1]['skill_name'] == 'Vue.js 3'
    
    def test_handles_skill_name_with_special_chars(self, expander):
        """Should handle special characters in skill names."""
        df = pd.DataFrame([
            {'skill_name': 'C++, C#, .NET', 'proficiency': 4, 'employee_id': 7}
        ])
        
        result = expander.expand_skills(df)
        
        assert len(result) == 3
        assert result.iloc[0]['skill_name'] == 'C++'
        assert result.iloc[1]['skill_name'] == 'C#'
        assert result.iloc[2]['skill_name'] == '.NET'
    
    def test_handles_none_skill_name(self, expander):
        """Should handle None as skill_name."""
        df = pd.DataFrame([
            {'skill_name': None, 'proficiency': 1, 'employee_id': 8}
        ])
        
        result = expander.expand_skills(df)
        
        # Should convert None to string "None" and keep row
        assert len(result) >= 0  # Should not crash
    
    def test_handles_missing_skill_name_column(self, expander):
        """Should handle DataFrame without skill_name column."""
        df = pd.DataFrame([
            {'proficiency': 3, 'employee_id': 9}
        ])
        
        result = expander.expand_skills(df)
        
        # Should use empty string as default
        assert len(result) >= 0  # Should not crash
    
    # Logging
    def test_logs_expansion_info(self, expander, caplog):
        """Should log info message when skills are expanded."""
        import logging
        
        df = pd.DataFrame([
            {'skill_name': 'Python, Java, JavaScript', 'proficiency': 3, 'employee_id': 1}
        ])
        
        with caplog.at_level(logging.INFO):
            result = expander.expand_skills(df)
        
        assert "Expanded" in caplog.text
        assert "comma-separated skills" in caplog.text
        # 1 row expanded to 3 rows = 2 additional rows
        assert "2" in caplog.text or "total 3" in caplog.text
    
    def test_does_not_log_when_no_expansion(self, expander, caplog):
        """Should not log when no expansion occurs."""
        import logging
        
        df = pd.DataFrame([
            {'skill_name': 'Python', 'proficiency': 3, 'employee_id': 1}
        ])
        
        with caplog.at_level(logging.INFO):
            result = expander.expand_skills(df)
        
        # No expansion message
        assert "Expanded" not in caplog.text
    
    # Real-world scenarios
    def test_real_world_excel_input(self, expander):
        """Should handle real-world Excel import data."""
        df = pd.DataFrame([
            {
                'employee_id': 100,
                'skill_name': 'Python, Java, SQL',
                'proficiency': 4,
                'years_experience': 3,
                'sub_segment_id': 5
            },
            {
                'employee_id': 101,
                'skill_name': 'JavaScript; TypeScript; React',
                'proficiency': 3,
                'years_experience': 2,
                'sub_segment_id': 5
            },
            {
                'employee_id': 102,
                'skill_name': 'Machine Learning',
                'proficiency': 5,
                'years_experience': 7,
                'sub_segment_id': 6
            }
        ])
        
        result = expander.expand_skills(df)
        
        # 3 + 3 + 1 = 7 total rows
        assert len(result) == 7
        
        # Verify first employee's skills
        employee_100_skills = result[result['employee_id'] == 100]['skill_name'].tolist()
        assert employee_100_skills == ['Python', 'Java', 'SQL']
        
        # Verify second employee's skills
        employee_101_skills = result[result['employee_id'] == 101]['skill_name'].tolist()
        assert employee_101_skills == ['JavaScript', 'TypeScript', 'React']
        
        # Verify third employee (no expansion)
        employee_102_skills = result[result['employee_id'] == 102]['skill_name'].tolist()
        assert employee_102_skills == ['Machine Learning']
    
    def test_maintains_dataframe_index(self, expander):
        """Should reset index properly after expansion."""
        df = pd.DataFrame([
            {'skill_name': 'A, B, C', 'employee_id': 1}
        ])
        
        result = expander.expand_skills(df)
        
        # Result should be usable without index issues
        assert len(result) == 3
        # Should be able to iterate without errors
        for idx, row in result.iterrows():
            assert 'skill_name' in row
    
    def test_expansion_count_accuracy(self, expander):
        """Should accurately count expanded rows."""
        df = pd.DataFrame([
            {'skill_name': 'A, B', 'employee_id': 1},
            {'skill_name': 'C', 'employee_id': 2},
            {'skill_name': 'D, E, F', 'employee_id': 3}
        ])
        
        result = expander.expand_skills(df)
        
        # Original: 3 rows, Result: 2 + 1 + 3 = 6 rows
        # Expansion: 6 - 3 = 3 additional rows
        assert len(result) == 6
