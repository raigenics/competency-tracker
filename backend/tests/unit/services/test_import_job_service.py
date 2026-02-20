"""
Unit tests for ImportJobService.

Tests the database-backed progress tracking service for bulk imports.

Coverage targets:
- Job creation
- Job updates (with throttling)
- Job completion/failure
- Status retrieval
- Throttling logic
- Error handling
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError

from app.services.import_job_service import ImportJobService, JobStatusDBError
from app.models.import_job import ImportJob


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock()
    db.query.return_value = db
    db.filter_by.return_value = db
    db.filter.return_value = db
    db.first.return_value = None
    return db


@pytest.fixture
def mock_job():
    """Create a mock ImportJob object."""
    job = MagicMock(spec=ImportJob)
    job.job_id = "test-job-123"
    job.status = "pending"
    job.percent_complete = 0
    job.message = "Starting..."
    job.employees_processed = 0
    job.skills_processed = 0
    job.created_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    job.completed_at = None
    job.error = None
    job.result = None
    job.to_dict.return_value = {
        "job_id": "test-job-123",
        "status": "pending",
        "percent_complete": 0,
        "message": "Starting..."
    }
    return job


@pytest.fixture
def service(mock_db):
    """Create ImportJobService with mock db."""
    return ImportJobService(mock_db)


# ============================================================================
# TEST: create_job
# ============================================================================

class TestCreateJob:
    """Test create_job() method."""
    
    def test_creates_job_with_uuid(self, service, mock_db):
        """Should create job and return UUID job_id."""
        # Act
        job_id = service.create_job()
        
        # Assert
        assert job_id is not None
        assert len(job_id) == 36  # UUID format
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_creates_job_with_pending_status(self, service, mock_db):
        """Should create job with 'pending' status."""
        # Act
        service.create_job()
        
        # Assert
        call_args = mock_db.add.call_args
        job = call_args[0][0]
        assert job.status == 'pending'
        assert job.percent_complete == 0
    
    def test_creates_job_with_custom_message(self, service, mock_db):
        """Should create job with custom message."""
        # Act
        service.create_job(message="Custom initialization message")
        
        # Assert
        call_args = mock_db.add.call_args
        job = call_args[0][0]
        assert job.message == "Custom initialization message"
    
    def test_creates_job_with_job_type(self, service, mock_db):
        """Should create job for tracking purposes."""
        # Act
        job_id = service.create_job(job_type="master_import")
        
        # Assert
        assert job_id is not None
        mock_db.commit.assert_called_once()
    
    def test_handles_db_error_on_create(self, service, mock_db):
        """Should rollback and raise on database error."""
        # Arrange
        mock_db.commit.side_effect = SQLAlchemyError("Connection failed")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            service.create_job()
        
        mock_db.rollback.assert_called_once()
    
    def test_initializes_throttling_state(self, service, mock_db):
        """Should initialize throttling state for new job."""
        # Act
        job_id = service.create_job()
        
        # Assert
        assert job_id in service._last_update_time
        assert job_id in service._last_percent
        assert job_id in service._last_status


# ============================================================================
# TEST: update_job
# ============================================================================

class TestUpdateJob:
    """Test update_job() method."""
    
    def test_updates_job_status(self, service, mock_db, mock_job):
        """Should update job status in database."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        result = service.update_job("test-job-123", status="processing", force_update=True)
        
        # Assert
        assert result is True
        assert mock_job.status == "processing"
        mock_db.commit.assert_called()
    
    def test_updates_percent_complete(self, service, mock_db, mock_job):
        """Should update percent_complete."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        result = service.update_job("test-job-123", percent=50, force_update=True)
        
        # Assert
        assert result is True
        assert mock_job.percent_complete == 50
    
    def test_clamps_percent_to_valid_range(self, service, mock_db, mock_job):
        """Should clamp percent to 0-100 range."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        service.update_job("test-job-123", percent=150, force_update=True)
        
        # Assert
        assert mock_job.percent_complete == 100  # Clamped to 100
    
    def test_clamps_negative_percent_to_zero(self, service, mock_db, mock_job):
        """Should clamp negative percent to 0."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        service.update_job("test-job-123", percent=-10, force_update=True)
        
        # Assert
        assert mock_job.percent_complete == 0
    
    def test_updates_message(self, service, mock_db, mock_job):
        """Should update progress message."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        service.update_job("test-job-123", message="Processing row 100...", force_update=True)
        
        # Assert
        assert mock_job.message == "Processing row 100..."
    
    def test_updates_employee_and_skill_counts(self, service, mock_db, mock_job):
        """Should update employees_processed and skills_processed."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        service.update_job("test-job-123", employees_processed=50, skills_processed=200, force_update=True)
        
        # Assert
        assert mock_job.employees_processed == 50
        assert mock_job.skills_processed == 200
    
    def test_returns_false_for_unknown_job(self, service, mock_db):
        """Should return False when job not found."""
        # Arrange
        mock_db.first.return_value = None
        
        # Act
        result = service.update_job("unknown-job", status="processing", force_update=True)
        
        # Assert
        assert result is False
    
    def test_handles_db_error_on_update(self, service, mock_db, mock_job):
        """Should rollback and return False on database error."""
        # Arrange
        mock_db.first.return_value = mock_job
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        # Act
        result = service.update_job("test-job-123", percent=50, force_update=True)
        
        # Assert
        assert result is False
        mock_db.rollback.assert_called()


# ============================================================================
# TEST: Throttling Logic
# ============================================================================

class TestThrottling:
    """Test update throttling behavior."""
    
    def test_allows_update_on_status_change(self, service, mock_db, mock_job):
        """Should allow update when status changes."""
        # Arrange
        mock_db.first.return_value = mock_job
        service._last_status["test-job-123"] = "pending"
        service._last_update_time["test-job-123"] = datetime.now(timezone.utc)
        service._last_percent["test-job-123"] = 10
        
        # Act - status changes from pending to processing
        result = service.update_job("test-job-123", status="processing")
        
        # Assert
        assert result is True
    
    def test_allows_update_on_boundary_crossing(self, service, mock_db, mock_job):
        """Should allow update when percent crosses 10% boundary."""
        # Arrange
        mock_db.first.return_value = mock_job
        service._last_status["test-job-123"] = "processing"
        service._last_update_time["test-job-123"] = datetime.now(timezone.utc)
        service._last_percent["test-job-123"] = 8  # Below 10%
        
        # Act - crossing 10% boundary
        result = service.update_job("test-job-123", percent=15)
        
        # Assert
        assert result is True
    
    def test_throttles_frequent_updates(self, service, mock_db, mock_job):
        """Should throttle updates that are too frequent."""
        # Arrange
        mock_db.first.return_value = mock_job
        service._last_status["test-job-123"] = "processing"
        service._last_update_time["test-job-123"] = datetime.now(timezone.utc)
        service._last_percent["test-job-123"] = 45
        
        # Act - small percent change, same status, just updated
        result = service.update_job("test-job-123", percent=46)  # Doesn't cross boundary
        
        # Assert
        assert result is False  # Throttled
    
    def test_allows_update_after_interval(self, service, mock_db, mock_job):
        """Should allow update after MIN_UPDATE_INTERVAL_SECONDS."""
        # Arrange
        mock_db.first.return_value = mock_job
        service._last_status["test-job-123"] = "processing"
        old_time = datetime.now(timezone.utc) - timedelta(seconds=10)  # 10 seconds ago
        service._last_update_time["test-job-123"] = old_time
        service._last_percent["test-job-123"] = 45
        
        # Act
        result = service.update_job("test-job-123", percent=46)
        
        # Assert
        assert result is True
    
    def test_force_update_bypasses_throttle(self, service, mock_db, mock_job):
        """Should bypass throttling when force_update=True."""
        # Arrange
        mock_db.first.return_value = mock_job
        service._last_status["test-job-123"] = "processing"
        service._last_update_time["test-job-123"] = datetime.now(timezone.utc)
        service._last_percent["test-job-123"] = 45
        
        # Act
        result = service.update_job("test-job-123", percent=46, force_update=True)
        
        # Assert
        assert result is True


# ============================================================================
# TEST: complete_job
# ============================================================================

class TestCompleteJob:
    """Test complete_job() method."""
    
    def test_marks_job_completed(self, service, mock_db, mock_job):
        """Should mark job as completed with 100%."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        result = service.complete_job("test-job-123")
        
        # Assert
        assert result is True
        assert mock_job.status == 'completed'
        assert mock_job.percent_complete == 100
    
    def test_sets_completion_timestamp(self, service, mock_db, mock_job):
        """Should set completed_at timestamp."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        service.complete_job("test-job-123")
        
        # Assert
        assert mock_job.completed_at is not None
    
    def test_stores_result_data(self, service, mock_db, mock_job):
        """Should store result dictionary."""
        # Arrange
        mock_db.first.return_value = mock_job
        result_data = {
            "employees_imported": 100,
            "skills_imported": 500,
            "failed_rows": []
        }
        
        # Act
        service.complete_job("test-job-123", result=result_data)
        
        # Assert
        assert mock_job.result == result_data
        assert mock_job.employees_processed == 100
        assert mock_job.skills_processed == 500
    
    def test_returns_false_for_unknown_job(self, service, mock_db):
        """Should return False when job not found."""
        # Arrange
        mock_db.first.return_value = None
        
        # Act
        result = service.complete_job("unknown-job")
        
        # Assert
        assert result is False
    
    def test_handles_db_error_on_complete(self, service, mock_db, mock_job):
        """Should rollback on database error."""
        # Arrange
        mock_db.first.return_value = mock_job
        mock_db.commit.side_effect = SQLAlchemyError("Commit failed")
        
        # Act
        result = service.complete_job("test-job-123")
        
        # Assert
        assert result is False
        mock_db.rollback.assert_called()


# ============================================================================
# TEST: fail_job
# ============================================================================

class TestFailJob:
    """Test fail_job() method."""
    
    def test_marks_job_failed(self, service, mock_db, mock_job):
        """Should mark job as failed."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        result = service.fail_job("test-job-123", error="Parse error in row 50")
        
        # Assert
        assert result is True
        assert mock_job.status == 'failed'
    
    def test_stores_error_message(self, service, mock_db, mock_job):
        """Should store error message."""
        # Arrange
        mock_db.first.return_value = mock_job
        error_msg = "ValueError: Invalid date format in row 10"
        
        # Act
        service.fail_job("test-job-123", error=error_msg)
        
        # Assert
        assert mock_job.error == error_msg
    
    def test_sets_completion_timestamp_on_failure(self, service, mock_db, mock_job):
        """Should set completed_at even on failure."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        service.fail_job("test-job-123", error="Some error")
        
        # Assert
        assert mock_job.completed_at is not None
    
    def test_returns_false_for_unknown_job(self, service, mock_db):
        """Should return False when job not found."""
        # Arrange
        mock_db.first.return_value = None
        
        # Act
        result = service.fail_job("unknown-job", error="Error")
        
        # Assert
        assert result is False


# ============================================================================
# TEST: get_job_status
# ============================================================================

class TestGetJobStatus:
    """Test get_job_status() method."""
    
    def test_returns_job_status_dict(self, service, mock_db, mock_job):
        """Should return job status as dictionary."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Act
        result = service.get_job_status("test-job-123")
        
        # Assert
        assert result is not None
        assert result["job_id"] == "test-job-123"
        assert result["status"] == "pending"
    
    def test_returns_none_for_unknown_job(self, service, mock_db):
        """Should return None when job not found."""
        # Arrange
        mock_db.first.return_value = None
        
        # Act
        result = service.get_job_status("unknown-job")
        
        # Assert
        assert result is None
    
    def test_raises_exception_on_db_error(self, service, mock_db):
        """Should raise JobStatusDBError on database error."""
        # Arrange
        mock_db.query.side_effect = SQLAlchemyError("Database unavailable")
        
        # Act & Assert
        with pytest.raises(JobStatusDBError):
            service.get_job_status("test-job-123")


# ============================================================================
# TEST: _should_update (Throttling Logic)
# ============================================================================

class TestShouldUpdate:
    """Test _should_update() internal method."""
    
    def test_returns_true_for_first_update(self, service):
        """Should return True for first update of a job."""
        # Act
        result = service._should_update("new-job", status="processing", percent=None)
        
        # Assert
        assert result is True
    
    def test_returns_true_when_status_changes(self, service):
        """Should return True when status actually changes."""
        # Arrange
        service._last_status["job-1"] = "pending"
        service._last_update_time["job-1"] = datetime.now(timezone.utc)
        service._last_percent["job-1"] = 0
        
        # Act
        result = service._should_update("job-1", status="processing", percent=10)
        
        # Assert
        assert result is True
    
    def test_returns_false_when_same_status_and_no_boundary(self, service):
        """Should return False when status same and no boundary crossed."""
        # Arrange
        service._last_status["job-1"] = "processing"
        service._last_update_time["job-1"] = datetime.now(timezone.utc)
        service._last_percent["job-1"] = 55
        
        # Act - same status, percent within same 10% band
        result = service._should_update("job-1", status=None, percent=57)
        
        # Assert
        assert result is False


# ============================================================================
# TEST: cleanup_old_jobs
# ============================================================================

class TestCleanupOldJobs:
    """Test cleanup_old_jobs() method."""
    
    def test_deletes_old_completed_jobs(self, service, mock_db):
        """Should delete old completed/failed jobs."""
        # Arrange
        mock_db.delete.return_value = 5
        
        # Act
        deleted = service.cleanup_old_jobs(days_old=7)
        
        # Assert
        assert deleted == 5
        mock_db.commit.assert_called()
    
    def test_returns_zero_on_db_error(self, service, mock_db):
        """Should return 0 on database error."""
        # Arrange
        mock_db.delete.side_effect = SQLAlchemyError("Delete failed")
        
        # Act
        deleted = service.cleanup_old_jobs()
        
        # Assert
        assert deleted == 0
        mock_db.rollback.assert_called()


# ============================================================================
# TEST: Integration Scenarios
# ============================================================================

class TestJobLifecycle:
    """Test complete job lifecycle scenarios."""
    
    def test_full_successful_import_lifecycle(self, service, mock_db, mock_job):
        """Test complete lifecycle: create -> updates -> complete."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Create job
        job_id = service.create_job(message="Starting import")
        
        # Update progress
        service.update_job(job_id, status="processing", percent=25, force_update=True)
        service.update_job(job_id, percent=50, force_update=True)
        service.update_job(job_id, percent=75, force_update=True)
        
        # Complete
        result = service.complete_job(job_id, result={"employees_imported": 100})
        
        # Assert
        assert result is True
        assert mock_job.status == 'completed'
    
    def test_full_failed_import_lifecycle(self, service, mock_db, mock_job):
        """Test lifecycle: create -> updates -> fail."""
        # Arrange
        mock_db.first.return_value = mock_job
        
        # Create job
        job_id = service.create_job()
        
        # Update progress
        service.update_job(job_id, status="processing", force_update=True)
        
        # Fail
        result = service.fail_job(job_id, error="Parse error")
        
        # Assert
        assert result is True
        assert mock_job.status == 'failed'
