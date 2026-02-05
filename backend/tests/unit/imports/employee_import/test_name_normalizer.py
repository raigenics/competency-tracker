"""
Unit tests for NameNormalizer.

Target: backend/app/services/imports/employee_import/name_normalizer.py
Coverage: Name normalization for case-insensitive comparison and database constraints.

Test Strategy:
- Pure function testing (no mocks needed)
- Verify whitespace handling (leading, trailing, internal)
- Verify case normalization
- Verify special characters and edge cases
- Matches database constraints: lower(trim(name))
"""
import pytest
from backend.app.services.imports.employee_import.name_normalizer import NameNormalizer


class TestNormalizeName:
    """Test NameNormalizer.normalize_name() method."""
    
    @pytest.fixture
    def normalizer(self):
        """Create NameNormalizer instance."""
        return NameNormalizer()
    
    # Basic normalization
    def test_normalizes_simple_name(self, normalizer):
        """Should convert simple name to lowercase."""
        result = normalizer.normalize_name("Python")
        assert result == "python"
    
    def test_normalizes_mixed_case(self, normalizer):
        """Should normalize mixed case names."""
        result = normalizer.normalize_name("JavaScript")
        assert result == "javascript"
    
    def test_normalizes_all_caps(self, normalizer):
        """Should normalize all caps names."""
        result = normalizer.normalize_name("SQL")
        assert result == "sql"
    
    # Whitespace handling
    def test_strips_leading_whitespace(self, normalizer):
        """Should remove leading whitespace."""
        result = normalizer.normalize_name("  Java")
        assert result == "java"
    
    def test_strips_trailing_whitespace(self, normalizer):
        """Should remove trailing whitespace."""
        result = normalizer.normalize_name("Java  ")
        assert result == "java"
    
    def test_strips_both_leading_and_trailing_whitespace(self, normalizer):
        """Should remove both leading and trailing whitespace."""
        result = normalizer.normalize_name("  Java  ")
        assert result == "java"
    
    def test_collapses_multiple_internal_spaces(self, normalizer):
        """Should collapse multiple spaces to single space."""
        result = normalizer.normalize_name("Machine    Learning")
        assert result == "machine learning"
    
    def test_collapses_mixed_internal_spaces(self, normalizer):
        """Should collapse various internal whitespace."""
        result = normalizer.normalize_name("Data   Science  AI")
        assert result == "data science ai"
    
    def test_handles_tabs_and_newlines(self, normalizer):
        """Should collapse tabs and newlines to single space."""
        result = normalizer.normalize_name("Cloud\t\nComputing")
        assert result == "cloud computing"
    
    def test_strips_and_collapses_combined(self, normalizer):
        """Should handle both stripping and collapsing together."""
        result = normalizer.normalize_name("  Web   Development  ")
        assert result == "web development"
    
    # Empty and None handling
    def test_returns_empty_string_for_none(self, normalizer):
        """Should return empty string for None input."""
        result = normalizer.normalize_name(None)
        assert result == ""
    
    def test_returns_empty_string_for_empty_string(self, normalizer):
        """Should return empty string for empty input."""
        result = normalizer.normalize_name("")
        assert result == ""
    
    def test_returns_empty_string_for_whitespace_only(self, normalizer):
        """Should return empty string for whitespace-only input."""
        result = normalizer.normalize_name("   ")
        assert result == ""
    
    def test_returns_empty_string_for_tabs_only(self, normalizer):
        """Should return empty string for tabs/newlines only."""
        result = normalizer.normalize_name("\t\n\r")
        assert result == ""
    
    # Special characters and numbers
    def test_preserves_special_characters(self, normalizer):
        """Should preserve special characters while normalizing."""
        result = normalizer.normalize_name("C++")
        assert result == "c++"
    
    def test_preserves_hyphens(self, normalizer):
        """Should preserve hyphens in compound names."""
        result = normalizer.normalize_name("DevOps-Engineer")
        assert result == "devops-engineer"
    
    def test_preserves_dots(self, normalizer):
        """Should preserve dots in names."""
        result = normalizer.normalize_name(".NET")
        assert result == ".net"
    
    def test_preserves_numbers(self, normalizer):
        """Should preserve numbers in names."""
        result = normalizer.normalize_name("Angular 15")
        assert result == "angular 15"
    
    def test_preserves_underscores(self, normalizer):
        """Should preserve underscores."""
        result = normalizer.normalize_name("Machine_Learning")
        assert result == "machine_learning"
    
    def test_preserves_slashes(self, normalizer):
        """Should preserve slashes."""
        result = normalizer.normalize_name("CI/CD")
        assert result == "ci/cd"
    
    # Database constraint matching
    def test_matches_database_constraint_simple(self, normalizer):
        """Should match database unique constraint: lower(trim(name))."""
        # Simulating database constraint behavior
        db_name = "Python"
        normalized = normalizer.normalize_name(db_name)
        assert normalized == db_name.strip().lower()
    
    def test_matches_database_constraint_with_spaces(self, normalizer):
        """Should match database constraint with internal spaces."""
        db_name = "  Machine   Learning  "
        # Database would do: lower(trim(name)) but won't collapse spaces
        # Our normalizer goes further by collapsing spaces
        normalized = normalizer.normalize_name(db_name)
        assert normalized == "machine learning"
    
    # Real-world examples
    def test_normalizes_skill_name_example(self, normalizer):
        """Should normalize real skill name from Excel."""
        result = normalizer.normalize_name("  Python Programming  ")
        assert result == "python programming"
    
    def test_normalizes_department_name_example(self, normalizer):
        """Should normalize department name."""
        result = normalizer.normalize_name("  Software   Development  ")
        assert result == "software development"
    
    def test_normalizes_location_name_example(self, normalizer):
        """Should normalize location name."""
        result = normalizer.normalize_name("  New  York  ")
        assert result == "new york"
    
    # Unicode and international characters
    def test_handles_unicode_characters(self, normalizer):
        """Should handle Unicode characters."""
        result = normalizer.normalize_name("Zürich")
        assert result == "zürich"
    
    def test_handles_accented_characters(self, normalizer):
        """Should handle accented characters."""
        result = normalizer.normalize_name("Français")
        assert result == "français"
    
    def test_handles_cyrillic_characters(self, normalizer):
        """Should handle Cyrillic characters."""
        result = normalizer.normalize_name("Москва")
        assert result == "москва"
    
    # Consistency tests
    def test_idempotent_normalization(self, normalizer):
        """Should produce same result when normalized twice."""
        name = "  Python   Programming  "
        first = normalizer.normalize_name(name)
        second = normalizer.normalize_name(first)
        assert first == second
    
    def test_case_insensitive_comparison_enabled(self, normalizer):
        """Should enable case-insensitive comparison."""
        name1 = normalizer.normalize_name("PYTHON")
        name2 = normalizer.normalize_name("python")
        name3 = normalizer.normalize_name("Python")
        assert name1 == name2 == name3
    
    def test_whitespace_insensitive_comparison_enabled(self, normalizer):
        """Should enable whitespace-insensitive comparison."""
        name1 = normalizer.normalize_name("Machine Learning")
        name2 = normalizer.normalize_name("  Machine   Learning  ")
        name3 = normalizer.normalize_name("machine learning")
        assert name1 == name2 == name3
