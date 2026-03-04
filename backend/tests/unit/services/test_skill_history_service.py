"""
Unit tests for SkillHistoryService.

Target: backend/app/services/skill_history_service.py
Coverage: Tests record_skill_change() accepts both ORM objects and dict snapshots.

Test Strategy:
- Mock database session
- Test dict snapshot input (batch import UPDATE path)
- Test ORM object input (manual update path)
- Test None input (INSERT path)
- Verify correct field extraction in all cases
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime

from app.services.skill_history_service import SkillHistoryService, _get_field
from app.models.employee_skill import EmployeeSkill
from app.models.skill_history import ChangeAction, ChangeSource


class TestGetFieldHelper:
    """Test _get_field helper function."""
    
    def test_returns_none_for_none_object(self):
        """Should return None when object is None."""
        assert _get_field(None, 'proficiency_level_id') is None
        assert _get_field(None, 'years_experience') is None
    
    def test_returns_value_from_dict(self):
        """Should return value using key lookup for dict."""
        old_record = {
            'proficiency_level_id': 3,
            'years_experience': 5,
            'last_used': date(2024, 6, 15),
            'certification': 'AWS Solutions Architect'
        }
        
        assert _get_field(old_record, 'proficiency_level_id') == 3
        assert _get_field(old_record, 'years_experience') == 5
        assert _get_field(old_record, 'last_used') == date(2024, 6, 15)
        assert _get_field(old_record, 'certification') == 'AWS Solutions Architect'
    
    def test_returns_none_for_missing_dict_key(self):
        """Should return None for missing key in dict."""
        old_record = {'proficiency_level_id': 3}
        
        assert _get_field(old_record, 'missing_field') is None
    
    def test_returns_value_from_orm_object(self):
        """Should return value using attribute access for ORM object."""
        orm_record = Mock(spec=EmployeeSkill)
        orm_record.proficiency_level_id = 4
        orm_record.years_experience = 7
        orm_record.last_used = date(2025, 1, 1)
        orm_record.certification = 'Azure Expert'
        
        assert _get_field(orm_record, 'proficiency_level_id') == 4
        assert _get_field(orm_record, 'years_experience') == 7
        assert _get_field(orm_record, 'last_used') == date(2025, 1, 1)
        assert _get_field(orm_record, 'certification') == 'Azure Expert'
    
    def test_returns_none_for_missing_orm_attribute(self):
        """Should return None for missing attribute on ORM object."""
        orm_record = Mock(spec=[])  # No attributes
        
        assert _get_field(orm_record, 'missing_field') is None


class TestRecordSkillChangeWithDictSnapshot:
    """Test record_skill_change() with dict snapshot (batch import UPDATE path)."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.add = Mock()
        db.flush = Mock()
        return db
    
    @pytest.fixture
    def history_service(self, mock_db):
        """Create SkillHistoryService instance."""
        return SkillHistoryService(mock_db)
    
    @pytest.fixture
    def new_skill_record(self):
        """Create mock new skill record (ORM object)."""
        record = Mock(spec=EmployeeSkill)
        record.emp_skill_id = 100
        record.proficiency_level_id = 5
        record.years_experience = 10
        record.last_used = date(2025, 2, 1)
        record.certification = 'New Certification'
        return record
    
    def test_accepts_dict_snapshot_without_crash(self, history_service, new_skill_record):
        """Should accept dict snapshot for old_skill_record without AttributeError."""
        old_record_dict = {
            'proficiency_level_id': 2,
            'years_experience': 5,
            'last_used': date(2024, 1, 1),
            'certification': 'Old Certification'
        }
        
        # This should NOT raise AttributeError
        result = history_service.record_skill_change(
            employee_id=1,
            skill_id=42,
            old_skill_record=old_record_dict,
            new_skill_record=new_skill_record,
            change_source=ChangeSource.IMPORT,
            changed_by='batch_import',
            batch_id='batch-123'
        )
        
        # Should return history record
        assert result is not None
        history_service.db.add.assert_called_once()
        history_service.db.flush.assert_called_once()
    
    def test_extracts_correct_old_values_from_dict(self, history_service, new_skill_record, mock_db):
        """Should correctly extract old values from dict snapshot."""
        old_record_dict = {
            'proficiency_level_id': 3,
            'years_experience': 7,
            'last_used': date(2024, 6, 15),
            'certification': 'AWS Certified'
        }
        
        history_service.record_skill_change(
            employee_id=1,
            skill_id=42,
            old_skill_record=old_record_dict,
            new_skill_record=new_skill_record,
            change_source=ChangeSource.IMPORT
        )
        
        # Get the EmployeeSkillHistory object that was added
        add_call = mock_db.add.call_args
        history_record = add_call[0][0]
        
        # Verify old values were extracted correctly from dict
        assert history_record.old_proficiency_level_id == 3
        assert history_record.old_years_experience == 7
        assert history_record.old_last_used == date(2024, 6, 15)
        assert history_record.old_certification == 'AWS Certified'
    
    def test_determines_update_action_with_dict(self, history_service, new_skill_record, mock_db):
        """Should determine UPDATE action when old_skill_record dict is provided."""
        old_record_dict = {'proficiency_level_id': 2}
        
        history_service.record_skill_change(
            employee_id=1,
            skill_id=42,
            old_skill_record=old_record_dict,
            new_skill_record=new_skill_record
        )
        
        history_record = mock_db.add.call_args[0][0]
        assert history_record.action == ChangeAction.UPDATE


class TestRecordSkillChangeWithOrmObject:
    """Test record_skill_change() with ORM object (manual update path)."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.add = Mock()
        db.flush = Mock()
        return db
    
    @pytest.fixture
    def history_service(self, mock_db):
        """Create SkillHistoryService instance."""
        return SkillHistoryService(mock_db)
    
    @pytest.fixture
    def old_skill_orm(self):
        """Create mock old skill record (ORM object)."""
        record = Mock(spec=EmployeeSkill)
        record.proficiency_level_id = 2
        record.years_experience = 4
        record.last_used = date(2023, 12, 1)
        record.certification = 'Existing Cert'
        return record
    
    @pytest.fixture
    def new_skill_record(self):
        """Create mock new skill record (ORM object)."""
        record = Mock(spec=EmployeeSkill)
        record.emp_skill_id = 200
        record.proficiency_level_id = 4
        record.years_experience = 8
        record.last_used = date(2025, 1, 15)
        record.certification = 'Updated Cert'
        return record
    
    def test_accepts_orm_object_for_manual_update(self, history_service, old_skill_orm, new_skill_record):
        """Should accept ORM object for old_skill_record (backward compatibility)."""
        # This must continue to work for manual update paths
        result = history_service.record_skill_change(
            employee_id=1,
            skill_id=50,
            old_skill_record=old_skill_orm,
            new_skill_record=new_skill_record,
            change_source=ChangeSource.UI,
            changed_by='user@example.com'
        )
        
        assert result is not None
        history_service.db.add.assert_called_once()
    
    def test_extracts_correct_old_values_from_orm(self, history_service, old_skill_orm, new_skill_record, mock_db):
        """Should correctly extract old values from ORM object."""
        history_service.record_skill_change(
            employee_id=1,
            skill_id=50,
            old_skill_record=old_skill_orm,
            new_skill_record=new_skill_record
        )
        
        history_record = mock_db.add.call_args[0][0]
        
        # Verify old values were extracted correctly from ORM
        assert history_record.old_proficiency_level_id == 2
        assert history_record.old_years_experience == 4
        assert history_record.old_last_used == date(2023, 12, 1)
        assert history_record.old_certification == 'Existing Cert'


class TestRecordSkillChangeWithNone:
    """Test record_skill_change() with None (INSERT path)."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.add = Mock()
        db.flush = Mock()
        return db
    
    @pytest.fixture
    def history_service(self, mock_db):
        """Create SkillHistoryService instance."""
        return SkillHistoryService(mock_db)
    
    @pytest.fixture
    def new_skill_record(self):
        """Create mock new skill record (ORM object)."""
        record = Mock(spec=EmployeeSkill)
        record.emp_skill_id = 300
        record.proficiency_level_id = 3
        record.years_experience = 2
        record.last_used = date(2025, 2, 10)
        record.certification = None
        return record
    
    def test_handles_none_old_record_for_insert(self, history_service, new_skill_record):
        """Should handle None old_skill_record for INSERT operations."""
        result = history_service.record_skill_change(
            employee_id=5,
            skill_id=100,
            old_skill_record=None,
            new_skill_record=new_skill_record,
            change_source=ChangeSource.IMPORT,
            batch_id='batch-456'
        )
        
        assert result is not None
        history_service.db.add.assert_called_once()
    
    def test_sets_null_old_values_for_insert(self, history_service, new_skill_record, mock_db):
        """Should set all old_* fields to None for INSERT."""
        history_service.record_skill_change(
            employee_id=5,
            skill_id=100,
            old_skill_record=None,
            new_skill_record=new_skill_record
        )
        
        history_record = mock_db.add.call_args[0][0]
        
        assert history_record.old_proficiency_level_id is None
        assert history_record.old_years_experience is None
        assert history_record.old_last_used is None
        assert history_record.old_certification is None
    
    def test_determines_insert_action(self, history_service, new_skill_record, mock_db):
        """Should determine INSERT action when old_skill_record is None."""
        history_service.record_skill_change(
            employee_id=5,
            skill_id=100,
            old_skill_record=None,
            new_skill_record=new_skill_record
        )
        
        history_record = mock_db.add.call_args[0][0]
        assert history_record.action == ChangeAction.INSERT
