"""
Unit tests for employee_import/field_sanitizer.py

Tests integer field sanitization with pandas NaN handling.
"""
import pytest
import pandas as pd
import numpy as np
from app.services.imports.employee_import.field_sanitizer import FieldSanitizer


# ============================================================================
# TEST: sanitize_integer_field
# ============================================================================

class TestSanitizeIntegerField:
    """Test integer field sanitization."""
    
    def test_returns_integer_for_valid_int(self):
        """Should return integer for valid int value."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(42, "test_field", "Z1001")
        
        # Assert
        assert result == 42
        assert isinstance(result, int)
    
    def test_returns_integer_for_float_that_is_whole_number(self):
        """Should convert float like 5.0 to integer 5."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(5.0, "test_field", "Z1001")
        
        # Assert
        assert result == 5
        assert isinstance(result, int)
    
    def test_returns_none_for_pandas_nan(self):
        """Should return None for pandas NaN (for PostgreSQL NULL)."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(pd.NA, "test_field", "Z1001")
        
        # Assert
        assert result is None
    
    def test_returns_none_for_numpy_nan(self):
        """Should return None for numpy NaN."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(np.nan, "test_field", "Z1001")
        
        # Assert
        assert result is None
    
    def test_returns_none_for_python_none(self):
        """Should return None for None value."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(None, "test_field", "Z1001")
        
        # Assert
        assert result is None
    
    def test_returns_none_for_empty_string(self):
        """Should return None for empty string."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field("", "test_field", "Z1001")
        
        # Assert
        assert result is None
    
    def test_returns_none_for_non_numeric_string(self):
        """Should return None for non-numeric string."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field("not-a-number", "test_field", "Z1001")
        
        # Assert
        assert result is None
    
    def test_converts_string_number_to_int(self):
        """Should convert string representation of number to int."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field("123", "test_field", "Z1001")
        
        # Assert
        assert result == 123
        assert isinstance(result, int)
    
    def test_handles_negative_integers(self):
        """Should handle negative integers."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(-10, "test_field", "Z1001")
        
        # Assert
        assert result == -10
    
    def test_handles_zero(self):
        """Should handle zero value."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(0, "test_field", "Z1001")
        
        # Assert
        assert result == 0
    
    def test_truncates_float_with_decimal_part(self):
        """Should truncate float with decimal part."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(5.7, "test_field", "Z1001")
        
        # Assert
        assert result == 5  # Truncated, not rounded
    
    def test_logs_warning_for_invalid_value(self, caplog):
        """Should log warning when value cannot be converted."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        with caplog.at_level("WARNING"):
            result = sanitizer.sanitize_integer_field("invalid", "proficiency", "Z1001")
        
        # Assert
        assert result is None
        assert "Invalid proficiency value" in caplog.text
        assert "Z1001" in caplog.text
    
    def test_includes_field_name_in_warning(self, caplog):
        """Should include field name in warning message."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        with caplog.at_level("WARNING"):
            sanitizer.sanitize_integer_field("bad", "years_experience", "Z9999")
        
        # Assert
        assert "years_experience" in caplog.text
    
    def test_handles_very_large_integers(self):
        """Should handle very large integers."""
        # Arrange
        sanitizer = FieldSanitizer()
        
        # Act
        result = sanitizer.sanitize_integer_field(2147483647, "test_field", "Z1001")
        
        # Assert
        assert result == 2147483647
