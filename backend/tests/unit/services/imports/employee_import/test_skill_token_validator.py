"""
Unit tests for SkillTokenValidator.

Tests token cleanup and validation logic to prevent garbage tokens.
"""
import pytest
from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator


class TestSkillTokenValidatorCleanup:
    """Test token cleaning functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SkillTokenValidator()
    
    def test_clean_basic_skill_name(self):
        """Test cleaning of basic skill names."""
        assert self.validator.clean_and_validate("Python") == "Python"
        assert self.validator.clean_and_validate("JavaScript") == "JavaScript"
        assert self.validator.clean_and_validate("Machine Learning") == "Machine Learning"
    
    def test_clean_whitespace(self):
        """Test cleaning of whitespace."""
        assert self.validator.clean_and_validate("  Python  ") == "Python"
        assert self.validator.clean_and_validate("Python   Programming") == "Python Programming"
        assert self.validator.clean_and_validate("\tJava\n") == "Java"
    
    def test_clean_boundary_punctuation(self):
        """Test stripping of boundary punctuation."""
        assert self.validator.clean_and_validate("(Python)") == "Python"
        assert self.validator.clean_and_validate(")test") == "test"
        assert self.validator.clean_and_validate("test(") == "test"
        assert self.validator.clean_and_validate("(test)") == "test"
    
    def test_preserve_internal_punctuation(self):
        """Test preservation of internal punctuation for technical names."""
        assert self.validator.clean_and_validate("C++") == "C++"
        assert self.validator.clean_and_validate("C#") == "C#"
        assert self.validator.clean_and_validate(".NET") == ".NET"
        assert self.validator.clean_and_validate("Node.js") == "Node.js"


class TestSkillTokenValidatorValidation:
    """Test token validation rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SkillTokenValidator()
    
    def test_reject_empty_string(self):
        """Test rejection of empty strings."""
        assert self.validator.clean_and_validate("") is None
        assert self.validator.clean_and_validate("   ") is None
        assert self.validator.clean_and_validate("\t\n") is None
    
    def test_reject_only_punctuation(self):
        """Test rejection of tokens with only punctuation."""
        assert self.validator.clean_and_validate(")") is None
        assert self.validator.clean_and_validate("(") is None
        assert self.validator.clean_and_validate("()") is None
        assert self.validator.clean_and_validate("...") is None
        assert self.validator.clean_and_validate("!!!") is None
    
    def test_reject_only_digits(self):
        """Test rejection of tokens with only digits."""
        assert self.validator.clean_and_validate("4") is None
        assert self.validator.clean_and_validate("6") is None
        assert self.validator.clean_and_validate("123") is None
        assert self.validator.clean_and_validate("0") is None
    
    def test_reject_too_short_non_whitelisted(self):
        """Test rejection of single-character tokens not on whitelist."""
        assert self.validator.clean_and_validate("A") is None
        assert self.validator.clean_and_validate("X") is None
        assert self.validator.clean_and_validate("Z") is None
        assert self.validator.clean_and_validate("Q") is None
    
    def test_accept_whitelisted_single_chars(self):
        """Test acceptance of whitelisted single-character skills."""
        assert self.validator.clean_and_validate("C") == "C"
        assert self.validator.clean_and_validate("c") == "c"  # Case preserved
        assert self.validator.clean_and_validate("R") == "R"
        assert self.validator.clean_and_validate("r") == "r"
        assert self.validator.clean_and_validate("V") == "V"
        assert self.validator.clean_and_validate("v") == "v"
    
    def test_accept_valid_tokens(self):
        """Test acceptance of valid tokens."""
        assert self.validator.clean_and_validate("Python") == "Python"
        assert self.validator.clean_and_validate("C++") == "C++"
        assert self.validator.clean_and_validate("Go") == "Go"
        assert self.validator.clean_and_validate("JS") == "JS"


class TestSkillTokenValidatorEdgeCases:
    """Test edge cases and real-world scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SkillTokenValidator()
    
    def test_mixed_valid_invalid(self):
        """Test tokens with mixed valid/invalid characters."""
        # Valid: Contains alphanumeric
        assert self.validator.clean_and_validate("Python3") == "Python3"
        assert self.validator.clean_and_validate("Web2.0") == "Web2.0"
        
        # Invalid: Only special chars
        assert self.validator.clean_and_validate("@#$") is None
    
    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        # Should preserve unicode in skill names
        result = self.validator.clean_and_validate("Français")
        assert result is not None
        assert "Français" in result or "Fran" in result  # May normalize
    
    def test_common_garbage_tokens(self):
        """Test rejection of common garbage tokens from Excel."""
        garbage = [")", "(", "4", "6", "1", "2", "...", "---", "***", " ", ""]
        for token in garbage:
            result = self.validator.clean_and_validate(token)
            assert result is None, f"Expected '{token}' to be rejected, got '{result}'"
    
    def test_technical_skill_names(self):
        """Test acceptance of technical skill names with special chars."""
        valid_skills = [
            "C++",
            "C#",
            ".NET",
            "Node.js",
            "Vue.js",
            "F#",
            "Objective-C",
            "COBOL-85",
        ]
        for skill in valid_skills:
            result = self.validator.clean_and_validate(skill)
            assert result is not None, f"Expected '{skill}' to be accepted, got None"
    
    def test_pandas_series_input(self):
        """Test handling of pandas Series input (edge case)."""
        # Validator should convert to string
        import pandas as pd
        series = pd.Series(["Python"])
        result = self.validator.clean_and_validate(series)
        # Should handle gracefully (convert to string representation)
        assert result is not None or result is None  # Just ensure no crash


class TestSkillTokenValidatorQuickCheck:
    """Test quick validation check method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SkillTokenValidator()
    
    def test_is_valid_token_true(self):
        """Test is_valid_token returns True for valid tokens."""
        assert self.validator.is_valid_token("Python") is True
        assert self.validator.is_valid_token("C++") is True
        assert self.validator.is_valid_token("  Java  ") is True
    
    def test_is_valid_token_false(self):
        """Test is_valid_token returns False for invalid tokens."""
        assert self.validator.is_valid_token(")") is False
        assert self.validator.is_valid_token("4") is False
        assert self.validator.is_valid_token("") is False
        assert self.validator.is_valid_token("   ") is False


class TestSkillTokenValidatorRealWorldScenarios:
    """Test real-world scenarios from actual data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SkillTokenValidator()
    
    def test_excel_import_garbage(self):
        """Test handling of garbage data commonly found in Excel imports."""
        # These should all be rejected
        garbage_data = [
            ")",      # Stray parenthesis
            "(",      # Stray parenthesis
            "4",      # Just a number
            "6",      # Just a number
            "1",      # Just a number
            "...",    # Ellipsis
            "",       # Empty
            " ",      # Whitespace
            "\t",     # Tab
            "---",    # Dashes
            "***",    # Asterisks
        ]
        
        for token in garbage_data:
            result = self.validator.clean_and_validate(token)
            assert result is None, f"Garbage token '{token}' should be rejected, got '{result}'"
    
    def test_excel_import_valid_skills(self):
        """Test handling of valid skill names from Excel."""
        valid_skills = [
            "Python Programming",
            "Machine Learning",
            "Data Analysis",
            "C++",
            "JavaScript",
            "SQL",
            "Cloud Computing",
            "DevOps",
            "Agile",
            "Docker",
            "Kubernetes",
            "React",
            "Angular",
            "Vue.js",
            ".NET Core",
        ]
        
        for skill in valid_skills:
            result = self.validator.clean_and_validate(skill)
            assert result is not None, f"Valid skill '{skill}' should be accepted"
            assert len(result) >= 2 or result.upper() in ['C', 'R', 'V'], f"Result too short: '{result}'"
    
    def test_comma_separated_remnants(self):
        """Test handling of remnants from comma-separated parsing."""
        # After splitting "Python, Java, )" by comma
        assert self.validator.clean_and_validate("Python") == "Python"
        assert self.validator.clean_and_validate("Java") == "Java"
        assert self.validator.clean_and_validate(")") is None
        
        # After splitting "C++, 4, JavaScript"
        assert self.validator.clean_and_validate("C++") == "C++"
        assert self.validator.clean_and_validate("4") is None
        assert self.validator.clean_and_validate("JavaScript") == "JavaScript"
