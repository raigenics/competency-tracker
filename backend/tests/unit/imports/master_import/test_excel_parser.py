"""
Unit tests for ExcelParser (Master Import).

Target: backend/app/services/imports/master_import/excel_parser.py
Coverage: Excel file parsing and validation for master skills import.

Test Strategy:
- Mock pandas Excel reading (no real files)
- Test column validation (case-insensitive matching)
- Test row parsing and normalization
- Test alias parsing (comma-separated)
- Test error handling and validation
- Test MasterSkillRow dataclass creation
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from app.services.imports.master_import.excel_parser import ExcelParser, MasterSkillRow


class TestExcelParserInit:
    """Test ExcelParser initialization."""
    
    def test_initializes_with_empty_errors(self):
        """Should initialize with empty errors list."""
        parser = ExcelParser()
        
        assert parser.errors == []
        assert parser.EXPECTED_COLUMNS == ["category", "subcategory", "skill name", "alias"]


class TestReadExcelFile:
    """Test _read_excel_file method."""
    
    @pytest.fixture
    def parser(self):
        """Create ExcelParser instance."""
        return ExcelParser()
    
    def _create_workbook_mock(self, rows_data):
        """Helper to create a mock workbook with given rows data."""
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = iter(rows_data)
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        return mock_wb
    
    def test_reads_excel_file_successfully(self, parser):
        """Should read Excel file into DataFrame."""
        # Rows data: first row is header, subsequent rows are data
        rows_data = [
            ('Category', 'SubCategory', 'Skill Name', 'Alias'),
            ('Programming', 'Languages', 'Python', 'py'),
        ]
        
        mock_wb = self._create_workbook_mock(rows_data)
        
        with patch('app.services.imports.master_import.excel_parser.load_workbook', return_value=mock_wb):
            result = parser._read_excel_file(b'fake_content')
        
        assert len(result) == 1
        assert 'Category' in result.columns
    
    def test_logs_column_information(self, parser, caplog):
        """Should log detected columns."""
        import logging
        
        rows_data = [
            ('Category', 'SubCategory', 'Skill Name', 'Alias'),
        ]
        
        mock_wb = self._create_workbook_mock(rows_data)
        
        with patch('app.services.imports.master_import.excel_parser.load_workbook', return_value=mock_wb):
            with caplog.at_level(logging.INFO):
                parser._read_excel_file(b'content')
        
        assert "Excel loaded" in caplog.text
        assert "Detected Excel columns" in caplog.text
    
    def test_raises_on_excel_parsing_error(self, parser):
        """Should raise ValueError when Excel parsing fails."""
        with patch('app.services.imports.master_import.excel_parser.load_workbook', side_effect=Exception("Invalid Excel")):
            with pytest.raises(ValueError, match="Failed to parse Excel file"):
                parser._read_excel_file(b'bad_content')


class TestValidateColumns:
    """Test _validate_columns method."""
    
    @pytest.fixture
    def parser(self):
        """Create ExcelParser instance."""
        return ExcelParser()
    
    def test_validates_exact_column_names(self, parser):
        """Should validate columns with exact case-sensitive names."""
        df = pd.DataFrame(columns=['category', 'subcategory', 'skill name', 'alias'])
        
        column_map = parser._validate_columns(df)
        
        assert column_map == {
            'category': 'category',
            'subcategory': 'subcategory',
            'skill name': 'skill name',
            'alias': 'alias'
        }
    
    def test_validates_case_insensitive_columns(self, parser):
        """Should match columns case-insensitively."""
        df = pd.DataFrame(columns=['Category', 'SubCategory', 'Skill Name', 'Alias'])
        
        column_map = parser._validate_columns(df)
        
        assert column_map == {
            'category': 'Category',
            'subcategory': 'SubCategory',
            'skill name': 'Skill Name',
            'alias': 'Alias'
        }
    
    def test_validates_mixed_case_columns(self, parser):
        """Should handle mixed case column names."""
        df = pd.DataFrame(columns=['CATEGORY', 'SubCategory', 'Skill name', 'ALIAS'])
        
        column_map = parser._validate_columns(df)
        
        assert column_map['category'] == 'CATEGORY'
        assert column_map['subcategory'] == 'SubCategory'
        assert column_map['skill name'] == 'Skill name'
        assert column_map['alias'] == 'ALIAS'
    
    def test_handles_extra_columns(self, parser):
        """Should allow extra columns beyond required ones."""
        df = pd.DataFrame(columns=['Category', 'SubCategory', 'Skill Name', 'Alias', 'Extra1', 'Extra2'])
        
        column_map = parser._validate_columns(df)
        
        # Should map required columns and ignore extra ones
        assert len(column_map) == 4
        assert 'category' in column_map
    
    def test_raises_on_missing_columns(self, parser):
        """Should raise ValueError when required columns are missing."""
        df = pd.DataFrame(columns=['Category', 'SubCategory'])  # Missing Skill Name and Alias
        
        with pytest.raises(ValueError, match="must have at least 4 columns"):
            parser._validate_columns(df)
    
    def test_raises_on_too_few_columns(self, parser):
        """Should raise ValueError when less than 4 columns."""
        df = pd.DataFrame(columns=['Category', 'SubCategory'])
        
        with pytest.raises(ValueError, match="must have at least 4 columns"):
            parser._validate_columns(df)
    
    def test_error_message_lists_available_columns(self, parser):
        """Should list available columns in error message."""
        df = pd.DataFrame(columns=['Category', 'SubCategory'])
        
        with pytest.raises(ValueError, match="Category, SubCategory"):
            parser._validate_columns(df)
    
    def test_logs_successful_mapping(self, parser, caplog):
        """Should log successful column mapping."""
        import logging
        
        df = pd.DataFrame(columns=['Category', 'SubCategory', 'Skill Name', 'Alias'])
        
        with caplog.at_level(logging.INFO):
            parser._validate_columns(df)
        
        assert "Column mapping successful" in caplog.text


class TestParseAliases:
    """Test _parse_aliases method."""
    
    @pytest.fixture
    def parser(self):
        """Create ExcelParser instance."""
        return ExcelParser()
    
    def test_parses_single_alias(self, parser):
        """Should parse single alias."""
        result = parser._parse_aliases("py")
        assert result == ["py"]
    
    def test_parses_multiple_aliases(self, parser):
        """Should parse comma-separated aliases."""
        result = parser._parse_aliases("py, python3, python")
        assert result == ["py", "python3", "python"]
    
    def test_strips_whitespace_from_aliases(self, parser):
        """Should strip whitespace from each alias."""
        result = parser._parse_aliases("  py  ,  python3  ")
        assert result == ["py", "python3"]
    
    def test_returns_empty_for_no_aliases(self, parser):
        """Should return empty list for empty alias text."""
        assert parser._parse_aliases("") == []
        assert parser._parse_aliases("nan") == []
        assert parser._parse_aliases("None") == []
    
    def test_removes_empty_aliases(self, parser):
        """Should remove empty strings after splitting."""
        result = parser._parse_aliases("py, , python, ")
        assert result == ["py", "python"]


# NOTE: TestIsEmptyRow and TestValidateRowFields removed
# These methods were inlined into _parse_single_row during refactoring


class TestParseSingleRow:
    """Test _parse_single_row method."""
    
    @pytest.fixture
    def parser(self):
        """Create ExcelParser instance."""
        return ExcelParser()
    
    @pytest.fixture
    def column_map(self):
        """Create column mapping."""
        return {
            'category': 'Category',
            'subcategory': 'SubCategory',
            'skill name': 'Skill Name',
            'alias': 'Alias'
        }
    
    @pytest.fixture
    def normalize_key(self):
        """Create mock normalize_key function."""
        return lambda x: x.lower().strip()
    
    def test_parses_valid_row(self, parser, column_map, normalize_key):
        """Should parse valid row into MasterSkillRow."""
        row = pd.Series({
            'Category': 'Programming',
            'SubCategory': 'Languages',
            'Skill Name': 'Python',
            'Alias': 'py, python3'
        })
        
        result = parser._parse_single_row(row, 2, column_map, normalize_key)
        
        assert isinstance(result, MasterSkillRow)
        assert result.row_number == 2
        assert result.category == 'Programming'
        assert result.subcategory == 'Languages'
        assert result.skill_name == 'Python'
        assert result.aliases == ['py', 'python3']
    
    def test_creates_normalized_fields(self, parser, column_map, normalize_key):
        """Should create normalized versions of fields."""
        row = pd.Series({
            'Category': '  PROGRAMMING  ',
            'SubCategory': 'Languages',
            'Skill Name': 'Python',
            'Alias': 'PY, Python3'
        })
        
        result = parser._parse_single_row(row, 2, column_map, normalize_key)
        
        assert result.category_norm == 'programming'
        assert result.subcategory_norm == 'languages'
        assert result.skill_name_norm == 'python'
        assert result.aliases_norm == ['py', 'python3']
    
    def test_skips_empty_row(self, parser, column_map, normalize_key):
        """Should return None for empty row."""
        row = pd.Series({
            'Category': '',
            'SubCategory': 'nan',
            'Skill Name': 'None',
            'Alias': ''
        })
        
        result = parser._parse_single_row(row, 2, column_map, normalize_key)
        
        assert result is None
    
    def test_skips_invalid_row(self, parser, column_map, normalize_key):
        """Should return None for row with missing required fields."""
        row = pd.Series({
            'Category': 'Programming',
            'SubCategory': '',
            'Skill Name': 'Python',
            'Alias': ''
        })
        
        result = parser._parse_single_row(row, 2, column_map, normalize_key)
        
        assert result is None
        assert len(parser.errors) == 1
    
    def test_handles_row_without_aliases(self, parser, column_map, normalize_key):
        """Should handle row with no aliases."""
        row = pd.Series({
            'Category': 'Programming',
            'SubCategory': 'Languages',
            'Skill Name': 'Python',
            'Alias': ''
        })
        
        result = parser._parse_single_row(row, 2, column_map, normalize_key)
        
        assert result.aliases == []
        assert result.aliases_norm == []


class TestParseRows:
    """Test _parse_rows method."""
    
    @pytest.fixture
    def parser(self):
        """Create ExcelParser instance."""
        return ExcelParser()
    
    @pytest.fixture
    def column_map(self):
        """Create column mapping."""
        return {
            'category': 'Category',
            'subcategory': 'SubCategory',
            'skill name': 'Skill Name',
            'alias': 'Alias'
        }
    
    @pytest.fixture
    def normalize_key(self):
        """Create mock normalize_key function."""
        return lambda x: x.lower().strip()
    
    def test_parses_multiple_rows(self, parser, column_map, normalize_key):
        """Should parse multiple valid rows."""
        df = pd.DataFrame([
            {'Category': 'Prog', 'SubCategory': 'Lang', 'Skill Name': 'Python', 'Alias': 'py'},
            {'Category': 'Prog', 'SubCategory': 'Lang', 'Skill Name': 'Java', 'Alias': 'jv'}
        ])
        
        result = parser._parse_rows(df, column_map, normalize_key)
        
        assert len(result) == 2
        assert result[0].skill_name == 'Python'
        assert result[1].skill_name == 'Java'
    
    def test_skips_empty_rows(self, parser, column_map, normalize_key):
        """Should skip empty rows."""
        df = pd.DataFrame([
            {'Category': 'Prog', 'SubCategory': 'Lang', 'Skill Name': 'Python', 'Alias': ''},
            {'Category': '', 'SubCategory': '', 'Skill Name': '', 'Alias': ''},  # Empty
            {'Category': 'Prog', 'SubCategory': 'Lang', 'Skill Name': 'Java', 'Alias': ''}
        ])
        
        result = parser._parse_rows(df, column_map, normalize_key)
        
        assert len(result) == 2
    
    def test_tracks_errors_for_invalid_rows(self, parser, column_map, normalize_key):
        """Should track errors for invalid rows."""
        df = pd.DataFrame([
            {'Category': 'Prog', 'SubCategory': '', 'Skill Name': 'Python', 'Alias': ''},  # Invalid
            {'Category': 'Prog', 'SubCategory': 'Lang', 'Skill Name': 'Java', 'Alias': ''}
        ])
        
        result = parser._parse_rows(df, column_map, normalize_key)
        
        assert len(result) == 1
        assert len(parser.errors) == 1
    
    def test_continues_on_row_exception(self, parser, column_map, normalize_key, caplog):
        """Should continue parsing even if a row raises exception."""
        import logging
        
        df = pd.DataFrame([
            {'Category': 'Prog', 'SubCategory': 'Lang', 'Skill Name': 'Python', 'Alias': ''}
        ])
        
        # Mock _parse_single_row to raise exception for first row
        with patch.object(parser, '_parse_single_row', side_effect=Exception("Test error")):
            with caplog.at_level(logging.WARNING):
                result = parser._parse_rows(df, column_map, normalize_key)
        
        # Should track error and continue
        assert len(parser.errors) == 1
        assert parser.errors[0]['error_type'] == 'VALIDATION_ERROR'
        assert "Error parsing row" in caplog.text


class TestParseExcel:
    """Test parse_excel main method."""
    
    @pytest.fixture
    def parser(self):
        """Create ExcelParser instance."""
        return ExcelParser()
    
    def _create_workbook_mock(self, rows_data):
        """Helper to create a mock workbook with given rows data."""
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = iter(rows_data)
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        return mock_wb
    
    def test_parses_valid_excel_file(self, parser):
        """Should parse valid Excel file end-to-end."""
        rows_data = [
            ('Category', 'SubCategory', 'Skill Name', 'Alias'),
            ('Programming', 'Languages', 'Python', 'py'),
            ('Programming', 'Languages', 'Java', 'jv, java8'),
        ]
        
        mock_wb = self._create_workbook_mock(rows_data)
        
        with patch('app.services.imports.master_import.excel_parser.load_workbook', return_value=mock_wb):
            with patch('app.utils.normalization.normalize_key', lambda x: x.lower().strip()):
                result = parser.parse_excel(b'fake_content')
        
        assert len(result) == 2
        assert result[0].skill_name == 'Python'
        assert result[1].aliases == ['jv', 'java8']
    
    def test_resets_errors_on_new_parse(self, parser):
        """Should reset errors list for each new parse."""
        parser.errors = [{'old': 'error'}]
        
        rows_data = [
            ('Category', 'SubCategory', 'Skill Name', 'Alias'),
            ('Prog', 'Lang', 'Python', ''),
        ]
        
        mock_wb = self._create_workbook_mock(rows_data)
        
        with patch('app.services.imports.master_import.excel_parser.load_workbook', return_value=mock_wb):
            with patch('app.utils.normalization.normalize_key', lambda x: x.lower()):
                parser.parse_excel(b'content')
        
        # Old errors should be cleared
        assert not any(e.get('old') == 'error' for e in parser.errors)
    
    def test_logs_parsing_summary(self, parser, caplog):
        """Should log summary of parsing results."""
        import logging
        
        rows_data = [
            ('Category', 'SubCategory', 'Skill Name', 'Alias'),
            ('Prog', 'Lang', 'Python', ''),
        ]
        
        mock_wb = self._create_workbook_mock(rows_data)
        
        with patch('app.services.imports.master_import.excel_parser.load_workbook', return_value=mock_wb):
            with patch('app.utils.normalization.normalize_key', lambda x: x.lower()):
                with caplog.at_level(logging.INFO):
                    parser.parse_excel(b'content')
        
        assert "Parsing complete" in caplog.text
        assert "valid rows" in caplog.text


class TestMasterSkillRowDataclass:
    """Test MasterSkillRow dataclass."""
    
    def test_creates_master_skill_row(self):
        """Should create MasterSkillRow with all fields."""
        row = MasterSkillRow(
            row_number=2,
            category="Programming",
            subcategory="Languages",
            skill_name="Python",
            aliases=["py", "python3"],
            category_norm="programming",
            subcategory_norm="languages",
            skill_name_norm="python",
            aliases_norm=["py", "python3"]
        )
        
        assert row.row_number == 2
        assert row.category == "Programming"
        assert row.skill_name == "Python"
        assert len(row.aliases) == 2
        assert row.skill_name_norm == "python"
