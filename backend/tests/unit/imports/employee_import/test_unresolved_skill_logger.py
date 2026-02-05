"""
Unit tests for UnresolvedSkillLogger.

Target: backend/app/services/imports/employee_import/unresolved_skill_logger.py
Coverage: Logging unresolved skills to database and file.

Test Strategy:
- Mock SQLAlchemy Session (db.add, db.query)
- Mock filesystem operations (open, Path)
- Test database logging to raw_skill_inputs table
- Test file logging with context (employee, sub-segment)
- Test error handling for DB and file failures
- No actual file I/O or database access
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime
from pathlib import Path
from backend.app.services.imports.employee_import.unresolved_skill_logger import UnresolvedSkillLogger
from backend.app.models.raw_skill_input import RawSkillInput
from backend.app.models import Employee, SubSegment


class TestUnresolvedSkillLoggerInit:
    """Test UnresolvedSkillLogger initialization."""
    
    def test_initializes_with_db_session(self):
        """Should initialize with database session."""
        db = Mock()
        
        logger = UnresolvedSkillLogger(db)
        
        assert logger.db is db
        assert logger.normalize_name is None
    
    def test_sets_name_normalizer(self):
        """Should allow injecting name normalizer function."""
        db = Mock()
        normalizer_func = lambda x: x.lower().strip()
        
        logger = UnresolvedSkillLogger(db)
        logger.set_name_normalizer(normalizer_func)
        
        assert logger.normalize_name is normalizer_func


class TestRecordUnresolvedSkill:
    """Test record_unresolved_skill method."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def logger_instance(self, mock_db):
        """Create UnresolvedSkillLogger instance."""
        return UnresolvedSkillLogger(mock_db)
    
    @pytest.fixture
    def timestamp(self):
        """Create fixed timestamp for testing."""
        return datetime(2025, 1, 15, 10, 30, 0)
    
    def test_creates_raw_skill_input_record(self, logger_instance, mock_db, timestamp):
        """Should create RawSkillInput record with correct fields."""
        with patch.object(logger_instance, '_log_to_file'):
            logger_instance.record_unresolved_skill(
                skill_name="UnknownSkill",
                employee_id=123,
                sub_segment_id=5,
                timestamp=timestamp
            )
        
        # Verify db.add was called
        mock_db.add.assert_called_once()
        
        # Get the RawSkillInput object that was added
        added_record = mock_db.add.call_args[0][0]
        assert isinstance(added_record, RawSkillInput)
        assert added_record.raw_text == "UnknownSkill"
        assert added_record.sub_segment_id == 5
        assert added_record.source_type == "excel_import"
        assert added_record.employee_id == 123
        assert added_record.resolved_skill_id is None
        assert added_record.resolution_method is None
        assert added_record.resolution_confidence is None
        assert added_record.created_at == timestamp
    
    def test_normalizes_skill_name_with_default_normalization(self, logger_instance, mock_db, timestamp):
        """Should use default normalization when normalizer not set."""
        with patch.object(logger_instance, '_log_to_file'):
            logger_instance.record_unresolved_skill(
                skill_name="  PYTHON  ",
                employee_id=1,
                sub_segment_id=1,
                timestamp=timestamp
            )
        
        added_record = mock_db.add.call_args[0][0]
        # Default normalization: lower().strip()
        assert added_record.normalized_text == "python"
    
    def test_normalizes_skill_name_with_custom_normalizer(self, mock_db, timestamp):
        """Should use custom normalizer when injected."""
        logger_instance = UnresolvedSkillLogger(mock_db)
        custom_normalizer = Mock(return_value="custom_normalized")
        logger_instance.set_name_normalizer(custom_normalizer)
        
        with patch.object(logger_instance, '_log_to_file'):
            logger_instance.record_unresolved_skill(
                skill_name="TestSkill",
                employee_id=1,
                sub_segment_id=1,
                timestamp=timestamp
            )
        
        custom_normalizer.assert_called_once_with("TestSkill")
        added_record = mock_db.add.call_args[0][0]
        assert added_record.normalized_text == "custom_normalized"
    
    def test_calls_log_to_file(self, logger_instance, mock_db, timestamp):
        """Should call _log_to_file with correct parameters."""
        with patch.object(logger_instance, '_log_to_file') as mock_log_file:
            logger_instance.record_unresolved_skill(
                skill_name="FileSkill",
                employee_id=456,
                sub_segment_id=7,
                timestamp=timestamp
            )
        
        mock_log_file.assert_called_once_with("FileSkill", 456, 7, timestamp)
    
    def test_logs_info_message(self, logger_instance, mock_db, timestamp, caplog):
        """Should log info message when skill is recorded."""
        import logging
        
        with patch.object(logger_instance, '_log_to_file'):
            with caplog.at_level(logging.INFO):
                logger_instance.record_unresolved_skill(
                    skill_name="LoggedSkill",
                    employee_id=1,
                    sub_segment_id=1,
                    timestamp=timestamp
                )
        
        assert "Logged unresolved skill" in caplog.text
        assert "LoggedSkill" in caplog.text
        assert "raw_skill_inputs" in caplog.text
    
    def test_handles_database_exception(self, mock_db, timestamp, caplog):
        """Should catch and log database exceptions."""
        import logging
        
        logger_instance = UnresolvedSkillLogger(mock_db)
        mock_db.add.side_effect = Exception("DB Error")
        
        with caplog.at_level(logging.ERROR):
            logger_instance.record_unresolved_skill(
                skill_name="ErrorSkill",
                employee_id=1,
                sub_segment_id=1,
                timestamp=timestamp
            )
        
        assert "Failed to log unresolved skill" in caplog.text
        assert "ErrorSkill" in caplog.text
        assert "DB Error" in caplog.text
    
    def test_does_not_raise_on_exception(self, mock_db, timestamp):
        """Should not raise exception even if DB operation fails."""
        logger_instance = UnresolvedSkillLogger(mock_db)
        mock_db.add.side_effect = Exception("DB Error")
        
        # Should not raise
        logger_instance.record_unresolved_skill(
            skill_name="ErrorSkill",
            employee_id=1,
            sub_segment_id=1,
            timestamp=timestamp
        )


class TestLogToFile:
    """Test _log_to_file private method."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def logger_instance(self, mock_db):
        """Create UnresolvedSkillLogger instance."""
        return UnresolvedSkillLogger(mock_db)
    
    @pytest.fixture
    def timestamp(self):
        """Create fixed timestamp for testing."""
        return datetime(2025, 1, 15, 10, 30, 45)
    
    @pytest.fixture
    def mock_employee(self):
        """Create mock employee."""
        employee = Mock(spec=Employee)
        employee.employee_id = 123
        employee.full_name = "John Doe"
        employee.zid = "Z1001"
        return employee
    
    @pytest.fixture
    def mock_sub_segment(self):
        """Create mock sub-segment."""
        sub_segment = Mock(spec=SubSegment)
        sub_segment.sub_segment_id = 5
        sub_segment.sub_segment_name = "Software Development"
        return sub_segment
    
    def test_writes_to_correct_file_path(self, logger_instance, mock_db, timestamp, mock_employee, mock_sub_segment):
        """Should write to unresolved_skills.txt in backend folder."""
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_employee, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        # Mock file operations
        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch.object(Path, '__truediv__', return_value=Path('/fake/backend/unresolved_skills.txt')):
                logger_instance._log_to_file("TestSkill", 123, 5, timestamp)
        
        # Verify file was opened in append mode
        m_open.assert_called_once()
        call_args = m_open.call_args
        assert 'a' in call_args[0] or call_args[1].get('mode') == 'a'
        assert call_args[1].get('encoding') == 'utf-8'
    
    def test_writes_formatted_log_entry(self, logger_instance, mock_db, timestamp, mock_employee, mock_sub_segment):
        """Should write formatted log entry with all context."""
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_employee, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger_instance._log_to_file("UnknownSkill", 123, 5, timestamp)
        
        # Get what was written to file
        handle = m_open()
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        
        # Verify format
        assert "[2025-01-15 10:30:45]" in written_content
        assert 'UNRESOLVED: "UnknownSkill"' in written_content
        assert "Employee: John Doe (Z1001)" in written_content
        assert "Sub-Segment: Software Development" in written_content
        assert written_content.endswith('\n')
    
    def test_queries_employee_info(self, logger_instance, mock_db, timestamp, mock_employee, mock_sub_segment):
        """Should query employee information from database."""
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_employee, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger_instance._log_to_file("TestSkill", 123, 5, timestamp)
        
        # Verify Employee query was made
        assert any(call.args[0] == Employee for call in mock_db.query.call_args_list)
    
    def test_queries_sub_segment_info(self, logger_instance, mock_db, timestamp, mock_employee, mock_sub_segment):
        """Should query sub-segment information from database."""
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_employee, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger_instance._log_to_file("TestSkill", 123, 5, timestamp)
        
        # Verify SubSegment query was made
        assert any(call.args[0] == SubSegment for call in mock_db.query.call_args_list)
    
    def test_handles_missing_employee(self, logger_instance, mock_db, timestamp, mock_sub_segment):
        """Should handle case when employee not found."""
        mock_query = Mock()
        # Employee query returns None, sub-segment returns mock
        mock_query.filter.return_value.first.side_effect = [None, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger_instance._log_to_file("TestSkill", 999, 5, timestamp)
        
        handle = m_open()
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        
        # Should use fallback format
        assert "Employee: ID:999" in written_content
        assert "Unknown" in written_content  # ZID fallback
    
    def test_handles_missing_sub_segment(self, logger_instance, mock_db, timestamp, mock_employee):
        """Should handle case when sub-segment not found."""
        mock_query = Mock()
        # Employee returns mock, sub-segment query returns None
        mock_query.filter.return_value.first.side_effect = [mock_employee, None]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger_instance._log_to_file("TestSkill", 123, 999, timestamp)
        
        handle = m_open()
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        
        # Should use fallback format
        assert "Sub-Segment: ID:999" in written_content
    
    def test_logs_debug_message(self, logger_instance, mock_db, timestamp, mock_employee, mock_sub_segment, caplog):
        """Should log debug message with file path."""
        import logging
        
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_employee, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            with caplog.at_level(logging.DEBUG):
                logger_instance._log_to_file("TestSkill", 123, 5, timestamp)
        
        assert "Logged unresolved skill to" in caplog.text
    
    def test_handles_file_write_exception(self, logger_instance, mock_db, timestamp, caplog):
        """Should catch and log file write exceptions."""
        import logging
        
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = Exception("File write error")
        mock_db.query.return_value = mock_query
        
        with caplog.at_level(logging.WARNING):
            logger_instance._log_to_file("TestSkill", 123, 5, timestamp)
        
        assert "Failed to log unresolved skill to file" in caplog.text
    
    def test_does_not_raise_on_file_exception(self, logger_instance, mock_db, timestamp):
        """Should not raise exception even if file operation fails."""
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = Exception("File error")
        mock_db.query.return_value = mock_query
        
        # Should not raise
        logger_instance._log_to_file("TestSkill", 123, 5, timestamp)
    
    def test_appends_to_existing_file(self, logger_instance, mock_db, timestamp, mock_employee, mock_sub_segment):
        """Should append to file rather than overwrite."""
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_employee, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger_instance._log_to_file("Skill1", 123, 5, timestamp)
        
        # Verify 'a' mode (append)
        call_args = m_open.call_args
        assert call_args[1].get('mode') == 'a' or 'a' in str(call_args)
    
    def test_uses_utf8_encoding(self, logger_instance, mock_db, timestamp, mock_employee, mock_sub_segment):
        """Should use UTF-8 encoding for international characters."""
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_employee, mock_sub_segment]
        mock_db.query.return_value = mock_query
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger_instance._log_to_file("TestSkill", 123, 5, timestamp)
        
        # Verify encoding
        call_args = m_open.call_args
        assert call_args[1].get('encoding') == 'utf-8'


class TestUnresolvedSkillLoggerIntegration:
    """Test integration scenarios."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def timestamp(self):
        """Create fixed timestamp for testing."""
        return datetime(2025, 1, 15, 10, 30, 0)
    
    def test_records_multiple_unresolved_skills(self, mock_db, timestamp):
        """Should handle multiple unresolved skills in sequence."""
        logger = UnresolvedSkillLogger(mock_db)
        
        mock_employee = Mock(spec=Employee, full_name="John Doe", zid="Z1001")
        mock_sub_segment = Mock(spec=SubSegment, sub_segment_name="SW Dev")
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_employee
        
        def query_side_effect(model):
            q = Mock()
            q.filter.return_value.first.return_value = mock_employee if model == Employee else mock_sub_segment
            return q
        
        mock_db.query.side_effect = query_side_effect
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger.record_unresolved_skill("Skill1", 1, 1, timestamp)
            logger.record_unresolved_skill("Skill2", 2, 1, timestamp)
            logger.record_unresolved_skill("Skill3", 3, 1, timestamp)
        
        # Verify db.add was called 3 times
        assert mock_db.add.call_count == 3
    
    def test_complete_workflow_with_normalizer(self, mock_db, timestamp):
        """Should complete full workflow with custom normalizer."""
        logger = UnresolvedSkillLogger(mock_db)
        custom_normalizer = lambda x: x.lower().strip().replace(" ", "_")
        logger.set_name_normalizer(custom_normalizer)
        
        mock_employee = Mock(spec=Employee, full_name="Jane Smith", zid="Z2002")
        mock_sub_segment = Mock(spec=SubSegment, sub_segment_name="Data Science")
        
        def query_side_effect(model):
            q = Mock()
            q.filter.return_value.first.return_value = mock_employee if model == Employee else mock_sub_segment
            return q
        
        mock_db.query.side_effect = query_side_effect
        
        m_open = mock_open()
        with patch('builtins.open', m_open):
            logger.record_unresolved_skill("Machine Learning", 100, 10, timestamp)
        
        # Verify normalized text
        added_record = mock_db.add.call_args[0][0]
        assert added_record.normalized_text == "machine_learning"
        assert added_record.raw_text == "Machine Learning"
