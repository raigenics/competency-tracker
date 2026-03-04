"""
Unit tests for capability_finder/export_service.py

Tests for exporting matching talent to Excel with all skills consolidated.
"""
import pytest
from unittest.mock import MagicMock, Mock, patch
from io import BytesIO
from datetime import date
from app.services.capability_finder import export_service as service
from app.schemas.capability_finder import EmployeeSearchResult, SkillInfo


# ============================================================================
# TEST: export_matching_talent_to_excel (Main Entry Point)
# ============================================================================

class TestExportMatchingTalentToExcel:
    """Test the main export function."""
    
    def test_validates_export_request(self, mock_db):
        """Should validate request before processing."""
        # Arrange/Act/Assert
        with pytest.raises(ValueError):
            service.export_matching_talent_to_excel(
                mock_db,
                mode='selected',
                skills=['Python'],
                selected_employee_ids=[]  # Empty for selected mode = error
            )
    
    def test_returns_empty_workbook_when_no_employees(self, mock_db):
        """Should return empty workbook when no matching employees."""
        # Arrange
        with patch.object(service, '_determine_employee_ids_to_export', return_value=set()):
            with patch.object(service, '_create_empty_workbook', return_value=BytesIO(b'test')) as mock_empty:
                # Act
                result = service.export_matching_talent_to_excel(
                    mock_db,
                    mode='all',
                    skills=['Python']
                )
        
        # Assert
        mock_empty.assert_called_once()
    
    def test_exports_all_matching_employees_in_all_mode(self, mock_db, mock_employee):
        """Should export all matching employees in 'all' mode."""
        # Arrange
        employee = mock_employee(1, 'Z1001', 'John Doe')
        employee_ids = {1}
        
        with patch.object(service, '_determine_employee_ids_to_export', return_value=employee_ids):
            with patch.object(service, '_query_employees_with_relationships', return_value=[employee]):
                with patch.object(service, '_build_export_rows', return_value=[{'employee_name': 'John'}]):
                    with patch.object(service, '_create_excel_workbook', return_value=BytesIO(b'test')):
                        # Act
                        result = service.export_matching_talent_to_excel(
                            mock_db,
                            mode='all',
                            skills=['Python']
                        )
        
        # Assert
        assert isinstance(result, BytesIO)
    
    def test_exports_only_selected_employees_in_selected_mode(self, mock_db, mock_employee):
        """Should export only selected employees in 'selected' mode."""
        # Arrange
        employee = mock_employee(1, 'Z1001', 'Jane Doe')
        selected_ids = [1, 5, 10]
        
        with patch.object(service, '_determine_employee_ids_to_export', return_value=set(selected_ids)) as mock_determine:
            with patch.object(service, '_query_employees_with_relationships', return_value=[employee]):
                with patch.object(service, '_build_export_rows', return_value=[]):
                    with patch.object(service, '_create_excel_workbook', return_value=BytesIO(b'test')):
                        # Act
                        result = service.export_matching_talent_to_excel(
                            mock_db,
                            mode='selected',
                            skills=[],
                            selected_employee_ids=selected_ids
                        )
        
        # Assert
        mock_determine.assert_called_once()


# ============================================================================
# TEST: _validate_export_request (Validation)
# ============================================================================

class TestValidateExportRequest:
    """Test export request validation."""
    
    def test_raises_error_for_selected_mode_with_empty_ids(self):
        """Should raise ValueError when mode='selected' and IDs empty."""
        # Act/Assert
        with pytest.raises(ValueError, match="selected_employee_ids cannot be empty"):
            service._validate_export_request(mode='selected', selected_employee_ids=[])
    
    def test_raises_error_for_selected_mode_with_none_ids(self):
        """Should raise ValueError when mode='selected' and IDs is None."""
        # Act/Assert
        with pytest.raises(ValueError, match="selected_employee_ids cannot be empty"):
            service._validate_export_request(mode='selected', selected_employee_ids=None)
    
    def test_accepts_all_mode_with_empty_ids(self):
        """Should accept mode='all' with empty selected_employee_ids."""
        # Act - should not raise
        service._validate_export_request(mode='all', selected_employee_ids=[])
    
    def test_accepts_selected_mode_with_ids(self):
        """Should accept mode='selected' with valid IDs."""
        # Act - should not raise
        service._validate_export_request(mode='selected', selected_employee_ids=[1, 2, 3])


# ============================================================================
# TEST: _determine_employee_ids_to_export (ID Determination)
# ============================================================================

class TestDetermineEmployeeIdsToExport:
    """Test employee ID determination logic."""
    
    def test_returns_selected_ids_for_selected_mode(self, mock_db):
        """Should return selected IDs directly for 'selected' mode."""
        # Arrange
        selected_ids = [1, 5, 10, 15]
        
        # Act
        result = service._determine_employee_ids_to_export(
            mock_db,
            mode='selected',
            skills=[],
            sub_segment_id=None,
            team_id=None,
            role=None,
            min_proficiency=0,
            min_experience_years=0,
            selected_employee_ids=selected_ids
        )
        
        # Assert
        assert result == set(selected_ids)
    
    def test_searches_for_matching_employees_in_all_mode(self, mock_db):
        """Should search for matching employees in 'all' mode."""
        # Arrange
        search_results = [
            EmployeeSearchResult(
                employee_id=1,
                employee_name='Test',
                sub_segment='SS1',
                team='Team1',
                role='Dev',
                top_skills=[]
            )
        ]
        
        with patch.object(service, '_search_matching_talent_for_export', return_value=search_results):
            # Act
            result = service._determine_employee_ids_to_export(
                mock_db,
                mode='all',
                skills=['Python'],
                sub_segment_id=None,
                team_id=None,
                role=None,
                min_proficiency=0,
                min_experience_years=0,
                selected_employee_ids=[]
            )
        
        # Assert
        assert 1 in result
    
    def test_returns_empty_set_when_no_matches(self, mock_db):
        """Should return empty set when no employees match search."""
        # Arrange
        with patch.object(service, '_search_matching_talent_for_export', return_value=[]):
            # Act
            result = service._determine_employee_ids_to_export(
                mock_db,
                mode='all',
                skills=['NonExistent'],
                sub_segment_id=None,
                team_id=None,
                role=None,
                min_proficiency=0,
                min_experience_years=0,
                selected_employee_ids=[]
            )
        
        # Assert
        assert result == set()


# ============================================================================
# TEST: _query_employees_with_relationships (DB Query)
# ============================================================================

class TestQueryEmployeesWithRelationships:
    """Test employee query with relationships."""
    
    def test_queries_employees_by_ids(self, mock_db, mock_employee):
        """Should query employees by specified IDs."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_employee(1, 'Z001', 'John')]
        
        # Act
        result = service._query_employees_with_relationships(mock_db, {1, 2, 3})
        
        # Assert
        mock_query.filter.assert_called_once()
        assert len(result) == 1
    
    def test_eager_loads_relationships(self, mock_db):
        """Should eager load team, project, sub_segment, roles."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_employees_with_relationships(mock_db, {1})
        
        # Assert
        mock_query.options.assert_called_once()
    
    def test_returns_empty_list_when_no_matches(self, mock_db):
        """Should return empty list when no employees found."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        result = service._query_employees_with_relationships(mock_db, {999})
        
        # Assert
        assert result == []


# ============================================================================
# TEST: _build_export_rows (Row Building)
# ============================================================================

class TestBuildExportRows:
    """Test export row building."""
    
    def test_builds_row_for_each_employee(self, mock_db, mock_employee):
        """Should build export row for each employee."""
        # Arrange
        employees = [
            mock_employee(1, 'Z001', 'Alice'),
            mock_employee(2, 'Z002', 'Bob')
        ]
        
        with patch.object(service, '_query_employee_all_skills', return_value=[]):
            with patch.object(service, '_build_skills_text', return_value=''):
                with patch.object(service, '_build_export_row', side_effect=[{'name': 'Alice'}, {'name': 'Bob'}]):
                    # Act
                    result = service._build_export_rows(mock_db, employees)
        
        # Assert
        assert len(result) == 2
    
    def test_fetches_all_skills_for_each_employee(self, mock_db, mock_employee):
        """Should fetch all skills for each employee."""
        # Arrange
        employees = [mock_employee(1, 'Z001', 'Charlie')]
        
        with patch.object(service, '_query_employee_all_skills', return_value=[]) as mock_skills:
            with patch.object(service, '_build_skills_text', return_value=''):
                with patch.object(service, '_build_export_row', return_value={}):
                    # Act
                    service._build_export_rows(mock_db, employees)
        
        # Assert
        mock_skills.assert_called_once_with(mock_db, 1)


# ============================================================================
# TEST: _query_employee_all_skills (Skills Query)
# ============================================================================

class TestQueryEmployeeAllSkills:
    """Test employee skills query."""
    
    def test_queries_skills_for_employee(self, mock_db):
        """Should query all skills for specified employee."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_employee_all_skills(mock_db, employee_id=42)
        
        # Assert
        mock_query.filter.assert_called_once()
    
    def test_orders_by_proficiency_then_name(self, mock_db):
        """Should order skills by proficiency DESC, then name ASC."""
        # Arrange
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        # Act
        service._query_employee_all_skills(mock_db, employee_id=1)
        
        # Assert
        mock_query.order_by.assert_called_once()


# ============================================================================
# TEST: _build_skills_text (Pure Function)
# ============================================================================

class TestBuildSkillsText:
    """Test skills text building."""
    
    def test_returns_empty_string_for_empty_skills(self):
        """Should return empty string for empty skills list."""
        # Act
        result = service._build_skills_text([])
        
        # Assert
        assert result == ''
    
    def test_formats_single_skill(self):
        """Should format single skill correctly."""
        # Arrange
        mock_emp_skill = Mock()
        mock_emp_skill.years_experience = 5
        mock_emp_skill.last_used = None
        mock_emp_skill.certification = None
        
        mock_skill = Mock()
        mock_skill.skill_name = 'Python'
        
        mock_prof = Mock()
        mock_prof.level_name = 'Expert'
        
        skills = [(mock_emp_skill, mock_skill, mock_prof)]
        
        with patch.object(service, '_format_single_skill', return_value='Python (Expert, 5yrs)'):
            # Act
            result = service._build_skills_text(skills)
        
        # Assert
        assert 'Python' in result or result.endswith(';')
    
    def test_joins_multiple_skills_with_semicolon_newline(self):
        """Should join multiple skills with semicolon + newline."""
        # Arrange - mock multiple skills
        skills = [
            (Mock(), Mock(), Mock()),
            (Mock(), Mock(), Mock())
        ]
        
        with patch.object(service, '_format_single_skill', side_effect=['Skill1', 'Skill2']):
            # Act
            result = service._build_skills_text(skills)
        
        # Assert
        assert ';\n' in result


# ============================================================================
# TEST: _format_single_skill (Pure Function)
# ============================================================================

class TestFormatSingleSkill:
    """Test single skill formatting."""
    
    def test_includes_skill_name_and_proficiency(self):
        """Should include skill name and proficiency level."""
        # Arrange
        mock_emp_skill = Mock()
        mock_emp_skill.years_experience = 0
        mock_emp_skill.last_used = None
        mock_emp_skill.certification = None
        
        mock_skill = Mock()
        mock_skill.skill_name = 'Python'
        
        mock_prof = Mock()
        mock_prof.level_name = 'Expert'
        
        # Act
        result = service._format_single_skill(mock_emp_skill, mock_skill, mock_prof)
        
        # Assert
        assert 'Python' in result
        assert 'Expert' in result
    
    def test_includes_years_experience_when_present(self):
        """Should include years of experience when > 0."""
        # Arrange
        mock_emp_skill = Mock()
        mock_emp_skill.years_experience = 5
        mock_emp_skill.last_used = None
        mock_emp_skill.certification = None
        
        mock_skill = Mock()
        mock_skill.skill_name = 'Java'
        
        mock_prof = Mock()
        mock_prof.level_name = 'Proficient'
        
        # Act
        result = service._format_single_skill(mock_emp_skill, mock_skill, mock_prof)
        
        # Assert
        assert '5yrs' in result
    
    def test_excludes_years_when_zero(self):
        """Should not include years when experience is 0."""
        # Arrange
        mock_emp_skill = Mock()
        mock_emp_skill.years_experience = 0
        mock_emp_skill.last_used = None
        mock_emp_skill.certification = None
        
        mock_skill = Mock()
        mock_skill.skill_name = 'React'
        
        mock_prof = Mock()
        mock_prof.level_name = 'Novice'
        
        # Act
        result = service._format_single_skill(mock_emp_skill, mock_skill, mock_prof)
        
        # Assert
        assert 'yrs' not in result
    
    def test_includes_last_used_when_present(self):
        """Should include last used date when present."""
        # Arrange
        mock_emp_skill = Mock()
        mock_emp_skill.years_experience = 0
        mock_emp_skill.last_used = date(2024, 6, 15)
        mock_emp_skill.certification = None
        
        mock_skill = Mock()
        mock_skill.skill_name = 'Docker'
        
        mock_prof = Mock()
        mock_prof.level_name = 'Competent'
        
        # Act
        result = service._format_single_skill(mock_emp_skill, mock_skill, mock_prof)
        
        # Assert
        assert 'LastUsed: 2024-06' in result
    
    def test_includes_certification_when_present(self):
        """Should include certification when present."""
        # Arrange
        mock_emp_skill = Mock()
        mock_emp_skill.years_experience = 0
        mock_emp_skill.last_used = None
        mock_emp_skill.certification = 'AWS Solutions Architect'
        
        mock_skill = Mock()
        mock_skill.skill_name = 'AWS'
        
        mock_prof = Mock()
        mock_prof.level_name = 'Expert'
        
        # Act
        result = service._format_single_skill(mock_emp_skill, mock_skill, mock_prof)
        
        # Assert
        assert 'Certs: AWS Solutions Architect' in result
    
    def test_strips_numeric_prefix_from_proficiency(self):
        """Should strip numeric prefix from proficiency (e.g., '3 - Competent' -> 'Competent')."""
        # Arrange
        mock_emp_skill = Mock()
        mock_emp_skill.years_experience = 0
        mock_emp_skill.last_used = None
        mock_emp_skill.certification = None
        
        mock_skill = Mock()
        mock_skill.skill_name = 'Kubernetes'
        
        mock_prof = Mock()
        mock_prof.level_name = '3 - Competent'
        
        # Act
        result = service._format_single_skill(mock_emp_skill, mock_skill, mock_prof)
        
        # Assert
        assert 'Competent' in result
        assert '3 -' not in result


# ============================================================================
# TEST: _build_export_row (Pure Function)
# ============================================================================

class TestBuildExportRow:
    """Test export row building."""
    
    def test_builds_row_with_all_fields(self, mock_employee):
        """Should build row with all employee fields."""
        # Arrange
        employee = mock_employee(1, 'Z1234', 'Test User')
        employee.sub_segment = Mock(sub_segment_name='Engineering')
        employee.project = Mock(project_name='ProjectX')
        employee.team = Mock(team_name='TeamA')
        employee.role = Mock(role_name='Developer')
        
        # Act
        result = service._build_export_row(employee, 'Python (Expert);')
        
        # Assert
        assert result['employee_name'] == 'Test User'
        assert result['zid'] == 'Z1234'
        assert result['sub_segment'] == 'Engineering'
        assert result['project'] == 'ProjectX'
        assert result['team'] == 'TeamA'
        assert result['role'] == 'Developer'
        assert result['skills'] == 'Python (Expert);'
    
    def test_handles_missing_org_info(self, mock_employee):
        """Should handle missing organizational info gracefully."""
        # Arrange
        employee = mock_employee(1, 'Z9999', 'No Org')
        employee.sub_segment = None
        employee.project = None
        employee.team = None
        employee.role = None
        
        # Act
        result = service._build_export_row(employee, '')
        
        # Assert
        assert result['sub_segment'] == ''
        assert result['project'] == ''
        assert result['team'] == ''
        assert result['role'] == ''


# ============================================================================
# TEST: _create_empty_workbook (Excel Creation)
# ============================================================================

class TestCreateEmptyWorkbook:
    """Test empty workbook creation."""
    
    def test_returns_bytesio_object(self):
        """Should return BytesIO object."""
        # Act
        result = service._create_empty_workbook()
        
        # Assert
        assert isinstance(result, BytesIO)
    
    def test_creates_valid_excel_content(self):
        """Should create valid Excel content (not empty bytes)."""
        # Act
        result = service._create_empty_workbook()
        
        # Assert
        content = result.read()
        assert len(content) > 0
        # Excel files start with PK (zip signature)
        assert content[:2] == b'PK'


# ============================================================================
# TEST: _create_excel_workbook (Excel Creation)
# ============================================================================

class TestCreateExcelWorkbook:
    """Test Excel workbook creation with data."""
    
    def test_returns_bytesio_object(self):
        """Should return BytesIO object."""
        # Arrange
        rows = [{'employee_name': 'John', 'zid': 'Z001', 'sub_segment': 'SS1',
                 'project': 'P1', 'team': 'T1', 'role': 'Dev', 'skills': 'Python;'}]
        
        # Act
        result = service._create_excel_workbook(rows)
        
        # Assert
        assert isinstance(result, BytesIO)
    
    def test_creates_valid_excel_file(self):
        """Should create valid Excel file."""
        # Arrange
        rows = [{'employee_name': 'Jane', 'zid': 'Z002', 'sub_segment': 'SS2',
                 'project': 'P2', 'team': 'T2', 'role': 'QA', 'skills': 'Java;'}]
        
        # Act
        result = service._create_excel_workbook(rows)
        content = result.read()
        
        # Assert
        assert len(content) > 0
        assert content[:2] == b'PK'
    
    def test_handles_empty_rows(self):
        """Should handle empty rows list."""
        # Act
        result = service._create_excel_workbook([])
        
        # Assert
        assert isinstance(result, BytesIO)


# ============================================================================
# TEST: Helper Formatting Functions
# ============================================================================

class TestApplyHeaderFormatting:
    """Test header formatting."""
    
    def test_writes_headers_to_worksheet(self):
        """Should write headers to worksheet."""
        # Arrange
        mock_ws = MagicMock()
        headers = ['Name', 'ZID', 'Team']
        
        # Act
        service._apply_header_formatting(mock_ws, headers)
        
        # Assert
        assert mock_ws.cell.call_count == 3


class TestWriteDataRows:
    """Test data row writing."""
    
    def test_writes_all_fields_for_each_row(self):
        """Should write all fields for each row."""
        # Arrange
        mock_ws = MagicMock()
        rows = [{'employee_name': 'Test', 'zid': 'Z001', 'sub_segment': 'SS',
                 'project': 'P', 'team': 'T', 'role': 'R', 'skills': 'S'}]
        
        # Act
        service._write_data_rows(mock_ws, rows)
        
        # Assert
        assert mock_ws.cell.call_count == 7  # 7 columns


class TestSetColumnWidths:
    """Test column width setting."""
    
    def test_sets_width_for_all_columns(self):
        """Should set width for all columns."""
        # Arrange
        mock_ws = MagicMock()
        mock_ws.column_dimensions = {}
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            mock_ws.column_dimensions[col] = MagicMock()
        
        # Act
        service._set_column_widths(mock_ws)
        
        # Assert - G should have wider column
        assert mock_ws.column_dimensions['G'].width == 75
