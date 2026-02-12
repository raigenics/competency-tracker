"""
Import Job Service - Database-backed progress tracking for bulk imports.

Single Responsibility: Persist import job progress to database for reliable tracking.
Replaces in-memory job tracker to support Azure App Service multi-worker deployments.
"""
import logging
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.import_job import ImportJob

logger = logging.getLogger(__name__)


class JobStatusDBError(Exception):
    """Raised when a transient database error occurs fetching job status.
    
    This should NOT be treated as 'job not found' - the job may exist but
    the database is temporarily unavailable.
    """
    pass


class ImportJobService:
    """
    Service for managing import job progress in database.
    
    Features:
    - Persistent storage (survives restarts)
    - Multi-worker safe
    - Throttled updates (avoid DB spam)
    - Phase-based progress tracking
    """
    
    # Throttling: minimum seconds between DB updates
    MIN_UPDATE_INTERVAL_SECONDS = 5
      # Progress boundaries for forced updates (even if throttle not reached)
    PROGRESS_BOUNDARIES = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    
    def __init__(self, db_session: Session):
        """
        Initialize import job service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self._last_update_time = {}  # job_id -> last update timestamp (for throttling)
        self._last_percent = {}  # job_id -> last percent reported (for boundary detection)
        self._last_status = {}  # job_id -> last status reported (for status change detection)
    
    def create_job(self, job_type: str = "employee_import", message: str = "Import starting...") -> str:
        """
        Create a new import job in database.
        
        Args:
            job_type: Type of import (for logging/debugging)
            message: Initial progress message
            
        Returns:
            job_id: UUID string for this import job
        """
        job_id = str(uuid.uuid4())
        
        try:
            job = ImportJob(
                job_id=job_id,
                status='pending',
                message=message,
                total_rows=0,
                processed_rows=0,
                percent_complete=0,
                employees_total=0,
                employees_processed=0,
                skills_total=0,
                skills_processed=0
            )
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
              # Initialize throttling state
            self._last_update_time[job_id] = datetime.now(timezone.utc)
            self._last_percent[job_id] = 0
            self._last_status[job_id] = 'pending'
            
            logger.info(f"✅ Created import job {job_id} with status 'pending'")
            return job_id
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create import job: {str(e)}")
            raise
    
    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        percent: Optional[int] = None,
        message: Optional[str] = None,
        processed_count: Optional[int] = None,
        total_count: Optional[int] = None,
        employees_processed: Optional[int] = None,
        skills_processed: Optional[int] = None,
        force_update: bool = False
    ) -> bool:
        """
        Update import job progress with intelligent throttling.
        
        Throttling Logic:
        - Update if: at least MIN_UPDATE_INTERVAL_SECONDS passed since last update
        - OR: percent crossed a 10% boundary (0, 10, 20, ..., 100)
        - OR: status changed
        - OR: force_update=True
        
        Args:
            job_id: Job identifier
            status: New status ('pending', 'processing', 'completed', 'failed')
            percent: Progress percentage (0-100)
            message: Progress message
            processed_count: Number of rows processed
            total_count: Total rows to process
            employees_processed: Employees imported count
            skills_processed: Skills imported count
            force_update: Force update regardless of throttling
            
        Returns:
            True if DB was updated, False if throttled
        """
        # Check if we should throttle this update
        if not force_update and not self._should_update(job_id, status, percent):
            logger.debug(f"⏸️ Throttled update for job {job_id} (percent={percent})")
            return False
        
        try:
            # Fetch current job
            job = self.db.query(ImportJob).filter_by(job_id=job_id).first()
            if not job:
                logger.warning(f"⚠️ Job {job_id} not found in database")
                return False
            
            # Update fields if provided
            if status is not None:
                job.status = status
            if percent is not None:
                job.percent_complete = min(100, max(0, percent))  # Clamp 0-100
            if message is not None:
                job.message = message
            if processed_count is not None:
                job.processed_rows = processed_count
            if total_count is not None:
                job.total_rows = total_count
            if employees_processed is not None:
                job.employees_processed = employees_processed
            if skills_processed is not None:
                job.skills_processed = skills_processed
              # Update timestamp
            job.updated_at = datetime.now(timezone.utc)
            
            # Commit to database
            self.db.commit()
            self.db.refresh(job)
            
            # Update throttling state
            self._last_update_time[job_id] = job.updated_at
            if percent is not None:
                self._last_percent[job_id] = percent
            if status is not None:
                self._last_status[job_id] = status
            
            logger.info(f"[JOB DB] Committed job {job_id}: status={status or job.status}, "
                       f"percent={percent or job.percent_complete}%, message='{message or job.message}'")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"❌ Failed to update job {job_id}: {str(e)}")
            return False
    
    def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark job as completed with final result.
        
        Args:
            job_id: Job identifier
            result: Import result dictionary (statistics, counts, etc.)
            
        Returns:
            True if updated successfully
        """
        try:
            job = self.db.query(ImportJob).filter_by(job_id=job_id).first()
            if not job:
                logger.warning(f"⚠️ Job {job_id} not found")
                return False
            
            job.status = 'completed'
            job.percent_complete = 100
            job.message = 'Import completed successfully'
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = job.completed_at
            
            if result:
                job.result = result
                # Extract counts from result if available
                if 'employees_imported' in result:
                    job.employees_processed = result['employees_imported']
                if 'skills_imported' in result:
                    job.skills_processed = result['skills_imported']
            
            self.db.commit()
            self.db.refresh(job)
            
            logger.info(f"✅ Completed job {job_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"❌ Failed to complete job {job_id}: {str(e)}")
            return False
    
    def fail_job(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed with error message.
        
        Args:
            job_id: Job identifier
            error: Error message/traceback
            
        Returns:
            True if updated successfully
        """
        try:
            job = self.db.query(ImportJob).filter_by(job_id=job_id).first()
            if not job:
                logger.warning(f"⚠️ Job {job_id} not found")
                return False
            
            job.status = 'failed'
            job.message = 'Import failed'
            job.error = error
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = job.completed_at
            
            self.db.commit()
            self.db.refresh(job)
            
            logger.error(f"❌ Failed job {job_id}: {error}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"❌ Failed to mark job {job_id} as failed: {str(e)}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current job status from database.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary or None if job does not exist
            
        Raises:
            JobStatusDBError: If a transient database error occurs (NOT 'not found')
        """
        try:
            job = self.db.query(ImportJob).filter_by(job_id=job_id).first()
            if not job:
                return None
            
            return job.to_dict()
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error getting job status for {job_id}: {str(e)}")
            # Raise specific exception so endpoint can return 503 instead of 404
            raise JobStatusDBError(f"Database temporarily unavailable: {type(e).__name__}")
    
    def _should_update(self, job_id: str, status: Optional[str], percent: Optional[int]) -> bool:
        """
        Determine if job should be updated based on throttling rules.
        
        Returns:
            True if update should proceed, False if throttled
        """
        now = datetime.now(timezone.utc)
        
        # Rule 1: Always update if status actually changed
        if status is not None and job_id in self._last_status:
            if status != self._last_status[job_id]:
                logger.debug(f"📌 Status changed from '{self._last_status[job_id]}' to '{status}'")
                return True
        elif status is not None:
            # First status update for this job
            return True
        
        # Rule 2: Check time-based throttling
        if job_id in self._last_update_time:
            elapsed = (now - self._last_update_time[job_id]).total_seconds()
            if elapsed >= self.MIN_UPDATE_INTERVAL_SECONDS:
                return True
        else:
            # First update for this job
            return True
        
        # Rule 3: Check if percent crossed a 10% boundary
        if percent is not None and job_id in self._last_percent:
            last_percent = self._last_percent[job_id]
            
            # Find which boundary was crossed
            for boundary in self.PROGRESS_BOUNDARIES:
                if last_percent < boundary <= percent:
                    logger.debug(f"📈 Percent crossed boundary {boundary}% (was {last_percent}%, now {percent}%)")
                    return True
        
        # Throttle this update
        return False
    
    def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """
        Delete completed/failed jobs older than specified days.
        
        Args:
            days_old: Delete jobs older than this many days
            
        Returns:
            Number of jobs deleted
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            deleted = self.db.query(ImportJob).filter(
                ImportJob.completed_at < cutoff_date,
                ImportJob.status.in_(['completed', 'failed'])
            ).delete()
            
            self.db.commit()
            
            if deleted > 0:
                logger.info(f"🗑️ Cleaned up {deleted} old import jobs (older than {days_old} days)")
            
            return deleted
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"❌ Failed to cleanup old jobs: {str(e)}")
            return 0


# Missing import
from datetime import timedelta
