"""
Unit tests for SkillPersister.

Target: backend/app/services/imports/employee_import/skill_persister.py
Coverage: Employee skill database persistence with resolution logic.

Test Strategy:
- Mock all dependencies (db, resolver, logger, history service)
- Test skill resolution flow (exact → alias → unresolved)
- Test batch processing per employee
- Test error handling and rollback scenarios
- Test stats tracking
- No actual database access
"""
import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, date
from app.services.imports.employee_import.skill_persister import SkillPersister
from app.models import Employee, EmployeeSkill, ProficiencyLevel
from app.models.skill_history import ChangeSource


class TestSkillPersisterInit:
    """Test SkillPersister initialization."""
    
    def test_initializes_with_dependencies(self):
        """Should initialize with all required dependencies."""
        mock_db = Mock()
        stats = {}
        date_parser = Mock()
        field_sanitizer = Mock()
        skill_resolver = Mock()
        unresolved_logger = Mock()
        
        persister = SkillPersister(
            mock_db, stats, date_parser, field_sanitizer,
            skill_resolver, unresolved_logger
        )
        
        assert persister.db is mock_db
        assert persister.stats is stats
        assert persister.date_parser is date_parser
        assert persister.field_sanitizer is field_sanitizer
        assert persister.skill_resolver is skill_resolver
        assert persister.unresolved_logger is unresolved_logger


class TestCreateEmployeeMappings:
    """Test _create_employee_mappings method."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance."""
        mock_db = Mock()
        stats = {}
        return SkillPersister(mock_db, stats, Mock(), Mock(), Mock(), Mock())
    
    def test_creates_name_and_subsegment_mappings(self, persister):
        """Should create mappings from ZID to employee name and sub-segment."""
        # Mock employees
        emp1 = Mock(spec=Employee)
        emp1.full_name = "John Doe"
        emp1.sub_segment_id = 5
        
        emp2 = Mock(spec=Employee)
        emp2.full_name = "Jane Smith"
        emp2.sub_segment_id = 7
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [emp1, emp2]
        persister.db.query.return_value = mock_query
        
        zid_to_emp_id = {"Z1001": 1, "Z1002": 2}
        
        name_mapping, subsegment_mapping = persister._create_employee_mappings(zid_to_emp_id)
        
        assert name_mapping == {"Z1001": "John Doe", "Z1002": "Jane Smith"}
        assert subsegment_mapping == {"Z1001": 5, "Z1002": 7}
    
    def test_handles_missing_employee(self, persister):
        """Should handle case when employee not found in DB."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        persister.db.query.return_value = mock_query
        
        zid_to_emp_id = {"Z9999": 999}
        
        name_mapping, subsegment_mapping = persister._create_employee_mappings(zid_to_emp_id)
        
        # Should not include missing employee
        assert "Z9999" not in name_mapping
        assert "Z9999" not in subsegment_mapping


class TestGroupSkillsByZid:
    """Test _group_skills_by_zid method."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance."""
        return SkillPersister(Mock(), {}, Mock(), Mock(), Mock(), Mock())
    
    def test_groups_skills_by_zid(self, persister):
        """Should group skills by employee ZID."""
        df = pd.DataFrame([
            {'zid': 'Z1001', 'skill_name': 'Python'},
            {'zid': 'Z1001', 'skill_name': 'Java'},
            {'zid': 'Z1002', 'skill_name': 'SQL'}
        ])
        
        result = persister._group_skills_by_zid(df)
        
        assert 'Z1001' in result
        assert 'Z1002' in result
        assert len(result['Z1001']) == 2
        assert len(result['Z1002']) == 1
    
    def test_includes_excel_row_numbers(self, persister):
        """Should include Excel row numbers (1-based + header)."""
        df = pd.DataFrame([
            {'zid': 'Z1001', 'skill_name': 'Python'}
        ])
        
        result = persister._group_skills_by_zid(df)
        
        # Row 0 in DataFrame = Excel row 2 (1-based + header)
        excel_row, row_data = result['Z1001'][0]
        assert excel_row == 2


class TestProcessSingleSkillResolved:
    """Test _process_single_skill method - resolved skill path."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance with mocked dependencies."""
        mock_db = Mock()
        stats = {'failed_rows': []}
        date_parser = Mock()
        field_sanitizer = Mock()
        skill_resolver = Mock()
        unresolved_logger = Mock()
        
        return SkillPersister(
            mock_db, stats, date_parser, field_sanitizer,
            skill_resolver, unresolved_logger
        )
    
    def test_creates_employee_skill_for_resolved_skill(self, persister):
        """Should create EmployeeSkill record when skill is resolved."""
        # Setup mocks - resolve_skill returns (skill_id, resolution_method, confidence)
        persister.skill_resolver.resolve_skill.return_value = (42, "exact", None)
        
        mock_proficiency = Mock(spec=ProficiencyLevel)
        mock_proficiency.proficiency_level_id = 3
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_proficiency
        persister.db.query.return_value = mock_query
        
        persister.date_parser.parse_date_safely.return_value = date(2023, 1, 1)
        persister.field_sanitizer.sanitize_integer_field.return_value = 5
        
        row = pd.Series({
            'skill_name': 'Python',
            'proficiency': 'Expert',
            'years_experience': 5,
            'interest_level': 4,
            'last_used': '2023-01-01',
            'started_learning_from': '2020-01-01',
            'certification': 'AWS Certified',
            'comment': 'Great skill'
        })
        
        result = persister._process_single_skill(
            row, excel_row=2, zid='Z1001', employee_name='John Doe',
            db_employee_id=1, sub_segment_id=5, 
            import_timestamp=datetime(2025, 1, 1)
        )
        
        # Verify EmployeeSkill was created
        assert result is not None
        assert isinstance(result, EmployeeSkill)
        persister.db.add.assert_called_once()
        persister.db.flush.assert_called_once()
    
    def test_resolves_skill_name(self, persister):
        """Should call skill resolver with skill name."""
        persister.skill_resolver.resolve_skill.return_value = (42, "exact", None)
        
        mock_proficiency = Mock(spec=ProficiencyLevel)
        mock_proficiency.proficiency_level_id = 3
        persister.db.query.return_value.filter.return_value.first.return_value = mock_proficiency
        
        persister.date_parser.parse_date_safely.return_value = None
        persister.field_sanitizer.sanitize_integer_field.return_value = None
        
        row = pd.Series({'skill_name': 'Python', 'proficiency': 'Expert'})
        
        persister._process_single_skill(
            row, 2, 'Z1001', 'John', 1, 5, datetime(2025, 1, 1)
        )
        
        persister.skill_resolver.resolve_skill.assert_called_once_with('Python')


class TestProcessSingleSkillUnresolved:
    """Test _process_single_skill method - unresolved skill path."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance."""
        mock_db = Mock()
        stats = {'failed_rows': []}
        return SkillPersister(mock_db, stats, Mock(), Mock(), Mock(), Mock())
    
    def test_logs_unresolved_skill(self, persister):
        """Should log to raw_skill_inputs when skill cannot be resolved."""
        persister.skill_resolver.resolve_skill.return_value = (None, None, None)  # Unresolved
        
        row = pd.Series({'skill_name': 'UnknownSkill', 'proficiency': 'Expert'})
        timestamp = datetime(2025, 1, 1)
        
        result = persister._process_single_skill(
            row, 2, 'Z1001', 'John', 1, 5, timestamp
        )
        
        # Should call unresolved logger
        persister.unresolved_logger.record_unresolved_skill.assert_called_once_with(
            skill_name='UnknownSkill',
            employee_id=1,
            sub_segment_id=5,
            timestamp=timestamp
        )
        
        # Should return None (skill not imported)
        assert result is None
    
    def test_tracks_unresolved_in_failed_rows(self, persister):
        """Should add unresolved skill to failed_rows stats."""
        persister.skill_resolver.resolve_skill.return_value = (None, None, None)
        
        row = pd.Series({'skill_name': 'UnknownSkill', 'proficiency': 'Expert'})
        
        persister._process_single_skill(
            row, 2, 'Z1001', 'John Doe', 1, 5, datetime(2025, 1, 1)
        )
        
        assert len(persister.stats['failed_rows']) == 1
        failed = persister.stats['failed_rows'][0]
        assert failed['error_code'] == 'SKILL_NOT_RESOLVED'
        assert failed['skill_name'] == 'UnknownSkill'
        assert failed['zid'] == 'Z1001'


class TestProcessSingleSkillErrors:
    """Test _process_single_skill method - error handling."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance."""
        mock_db = Mock()
        stats = {'failed_rows': []}
        return SkillPersister(mock_db, stats, Mock(), Mock(), Mock(), Mock())
    
    def test_handles_empty_skill_name(self, persister):
        """Should skip skills with empty names."""
        row = pd.Series({'skill_name': '', 'proficiency': 'Expert'})
        
        result = persister._process_single_skill(
            row, 2, 'Z1001', 'John', 1, 5, datetime(2025, 1, 1)
        )
        
        assert result is None
        # Should not call resolver for empty skill
        persister.skill_resolver.resolve_skill.assert_not_called()
    
    def test_handles_pandas_series_skill_name(self, persister):
        """Should handle edge case where skill_name is a pandas Series."""
        persister.skill_resolver.resolve_skill.return_value = (42, "exact", None)
        mock_proficiency = Mock(spec=ProficiencyLevel, proficiency_level_id=3)
        persister.db.query.return_value.filter.return_value.first.return_value = mock_proficiency
        persister.date_parser.parse_date_safely.return_value = None
        persister.field_sanitizer.sanitize_integer_field.return_value = None
        
        # Create a Series as skill_name (edge case)
        skill_name_series = pd.Series(['Python'])
        row = pd.Series({'skill_name': skill_name_series, 'proficiency': 'Expert'})
        
        result = persister._process_single_skill(
            row, 2, 'Z1001', 'John', 1, 5, datetime(2025, 1, 1)
        )
        
        # Should extract first element and resolve
        persister.skill_resolver.resolve_skill.assert_called_once_with('Python')
    
    def test_catches_and_logs_exceptions(self, persister, caplog):
        """Should catch exceptions and track as failed row."""
        import logging
        
        persister.skill_resolver.resolve_skill.side_effect = Exception("DB Error")
        
        row = pd.Series({'skill_name': 'Python', 'proficiency': 'Expert'})
        
        with caplog.at_level(logging.WARNING):
            result = persister._process_single_skill(
                row, 2, 'Z1001', 'John Doe', 1, 5, datetime(2025, 1, 1)
            )
        
        assert result is None
        assert len(persister.stats['failed_rows']) == 1
        assert "Failed to prepare skill" in caplog.text
    
    def test_determines_error_codes(self, persister):
        """Should determine appropriate error codes from exception messages."""
        persister.skill_resolver.resolve_skill.return_value = (42, "exact", None)
        # "not found" is matched first in _determine_skill_error_code, so use MISSING_REFERENCE
        persister.db.query.side_effect = Exception("Proficiency level not found: Invalid")
        
        row = pd.Series({'skill_name': 'Python', 'proficiency': 'Invalid'})
        
        persister._process_single_skill(
            row, 2, 'Z1001', 'John', 1, 5, datetime(2025, 1, 1)
        )
        
        failed = persister.stats['failed_rows'][0]
        assert failed['error_code'] == 'MISSING_REFERENCE'


class TestCommitEmployeeSkills:
    """Test _commit_employee_skills method."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance."""
        mock_db = Mock()
        stats = {'failed_rows': []}
        return SkillPersister(mock_db, stats, Mock(), Mock(), Mock(), Mock())
    
    @pytest.fixture
    def mock_history_service(self):
        """Create mock history service."""
        return Mock()
    
    def test_commits_skills_and_history_together(self, persister, mock_history_service):
        """Should commit employee skills and history in same transaction."""
        skill1 = Mock(spec=EmployeeSkill, employee_id=1, skill_id=10)
        skill2 = Mock(spec=EmployeeSkill, employee_id=1, skill_id=11)
        
        result = persister._commit_employee_skills(
            [skill1, skill2], 'Z1001', 'John Doe', 
            mock_history_service, datetime(2025, 1, 1)
        )
        
        # Should record history for both skills
        assert mock_history_service.record_skill_change.call_count == 2
        
        # Should commit
        persister.db.commit.assert_called_once()
        
        # Should return count
        assert result == 2
    
    def test_uses_same_batch_id_for_employee(self, persister, mock_history_service):
        """Should use same batch_id for all skills of one employee."""
        skill1 = Mock(spec=EmployeeSkill, employee_id=1, skill_id=10)
        skill2 = Mock(spec=EmployeeSkill, employee_id=1, skill_id=11)
        
        persister._commit_employee_skills(
            [skill1, skill2], 'Z1001', 'John', mock_history_service, datetime(2025, 1, 1)
        )
        
        # Get batch_ids from both calls
        call1_batch = mock_history_service.record_skill_change.call_args_list[0][1]['batch_id']
        call2_batch = mock_history_service.record_skill_change.call_args_list[1][1]['batch_id']
        
        # Should be same batch_id
        assert call1_batch == call2_batch
    
    def test_returns_zero_for_empty_list(self, persister, mock_history_service):
        """Should return 0 when no skills to commit."""
        result = persister._commit_employee_skills(
            [], 'Z1001', 'John', mock_history_service, datetime(2025, 1, 1)
        )
        
        assert result == 0
        persister.db.commit.assert_not_called()
    
    def test_rolls_back_on_commit_failure(self, persister, mock_history_service, caplog):
        """Should rollback when commit fails."""
        import logging
        
        skill1 = Mock(spec=EmployeeSkill, employee_id=1, skill_id=10)
        persister.db.commit.side_effect = Exception("Commit failed")
        
        with caplog.at_level(logging.ERROR):
            result = persister._commit_employee_skills(
                [skill1], 'Z1001', 'John Doe', mock_history_service, datetime(2025, 1, 1)
            )
        
        # Should rollback
        persister.db.rollback.assert_called_once()
        
        # Should return 0
        assert result == 0
        
        # Should log error
        assert "Failed to commit skills" in caplog.text
        
        # Should track as failed
        assert len(persister.stats['failed_rows']) == 1
        assert persister.stats['failed_rows'][0]['error_code'] == 'BATCH_COMMIT_FAILED'


class TestProcessEmployeeSkills:
    """Test _process_employee_skills method."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance."""
        mock_db = Mock()
        stats = {'failed_rows': []}
        return SkillPersister(mock_db, stats, Mock(), Mock(), Mock(), Mock())
    
    def test_skips_skills_for_missing_employee(self, persister, caplog):
        """Should skip all skills when employee not imported."""
        import logging
        
        skill_rows = [
            (2, pd.Series({'skill_name': 'Python'})),
            (3, pd.Series({'skill_name': 'Java'}))
        ]
        
        # Employee not in mapping
        with caplog.at_level(logging.WARNING):
            result = persister._process_employee_skills(
                'Z9999', skill_rows, {}, {}, {},
                Mock(), datetime(2025, 1, 1)
            )
        
        assert result == 0
        assert "Employee was not imported" in caplog.text
        assert len(persister.stats['failed_rows']) == 2


class TestMarkSkillsAsFailed:
    """Test _mark_skills_as_failed method."""
    
    def test_marks_all_skills_as_failed(self):
        """Should add all skills to failed_rows."""
        persister = SkillPersister(Mock(), {'failed_rows': []}, Mock(), Mock(), Mock(), Mock())
        
        skill_rows = [
            (2, pd.Series({'skill_name': 'Python', 'employee_full_name': 'John'})),
            (3, pd.Series({'skill_name': 'Java', 'employee_full_name': 'John'}))
        ]
        
        persister._mark_skills_as_failed(skill_rows, 'Z1001', 'John Doe', 'TEST_ERROR')
        
        assert len(persister.stats['failed_rows']) == 2
        assert all(f['error_code'] == 'TEST_ERROR' for f in persister.stats['failed_rows'])


class TestDetermineSkillErrorCode:
    """Test _determine_skill_error_code method."""
    
    @pytest.fixture
    def persister(self):
        """Create SkillPersister instance."""
        return SkillPersister(Mock(), {}, Mock(), Mock(), Mock(), Mock())
    
    def test_identifies_missing_reference(self, persister):
        """Should identify 'not found' errors."""
        code = persister._determine_skill_error_code("Proficiency level not found: Expert")
        assert code == "MISSING_REFERENCE"
    
    def test_identifies_proficiency_error(self, persister):
        """Should identify proficiency errors."""
        code = persister._determine_skill_error_code("Invalid proficiency value")
        assert code == "INVALID_PROFICIENCY"
    
    def test_identifies_duplicate_error(self, persister):
        """Should identify duplicate errors."""
        code = persister._determine_skill_error_code("Duplicate entry for key")
        assert code == "DUPLICATE_SKILL"
    
    def test_identifies_constraint_violation(self, persister):
        """Should identify constraint violations."""
        code = persister._determine_skill_error_code("Foreign key constraint failed")
        assert code == "CONSTRAINT_VIOLATION"
    
    def test_defaults_to_generic_error(self, persister):
        """Should default to generic error code."""
        code = persister._determine_skill_error_code("Unknown error occurred")
        assert code == "SKILL_IMPORT_ERROR"
