"""
Import Job Tracker - Thread-safe in-memory storage for import progress.

Single Responsibility: Track import job status and progress for UI polling.
"""
import logging
import uuid
from typing import Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class ImportJobStatus:
    """Status of an import job."""
    job_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    message: str
    total_rows: int = 0
    processed_rows: int = 0
    percent_complete: int = 0
    
    # Detailed counters
    employees_total: int = 0
    employees_processed: int = 0
    skills_total: int = 0
    skills_processed: int = 0
    
    # Results (populated on completion)
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'message': self.message,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'percent_complete': self.percent_complete,
            'employees_total': self.employees_total,
            'employees_processed': self.employees_processed,
            'skills_total': self.skills_total,
            'skills_processed': self.skills_processed,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class ImportJobTracker:
    """
    Thread-safe in-memory tracker for import jobs.
    
    NOTE: This is a simple in-memory solution. For production with multiple
    workers, consider Redis or database-backed job tracking.
    """
    
    def __init__(self, max_jobs: int = 100):
        """
        Initialize job tracker.
        
        Args:
            max_jobs: Maximum number of jobs to keep in memory (LRU eviction)
        """
        self._jobs: Dict[str, ImportJobStatus] = {}
        self._lock = Lock()
        self._max_jobs = max_jobs
    
    def create_job(self, total_rows: int = 0) -> str:
        """
        Create a new import job and return job_id.
        
        Args:
            total_rows: Total number of rows to process (if known)
            
        Returns:
            job_id: Unique identifier for this import job
        """
        job_id = str(uuid.uuid4())
        
        with self._lock:
            # LRU eviction if we exceed max_jobs
            if len(self._jobs) >= self._max_jobs:
                oldest_job_id = min(self._jobs.keys(), 
                                   key=lambda k: self._jobs[k].created_at)
                del self._jobs[oldest_job_id]
                logger.debug(f"Evicted oldest job {oldest_job_id} (LRU)")
            
            self._jobs[job_id] = ImportJobStatus(
                job_id=job_id,
                status='pending',
                message='Import job created',
                total_rows=total_rows
            )
        
        logger.info(f"Created import job {job_id}")
        return job_id
    
    def update_progress(self, job_id: str, processed_rows: int, 
                       total_rows: Optional[int] = None,
                       message: Optional[str] = None,
                       employees_processed: int = 0,
                       skills_processed: int = 0) -> None:
        """
        Update job progress.
        
        Args:
            job_id: Job identifier
            processed_rows: Number of rows processed so far
            total_rows: Total rows (if changed from initial estimate)
            message: Status message
            employees_processed: Number of employees processed
            skills_processed: Number of skills processed
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found for progress update")
                return
            
            job.processed_rows = processed_rows
            if total_rows is not None:
                job.total_rows = total_rows
            
            # Calculate percentage (safe division)
            if job.total_rows > 0:
                job.percent_complete = min(100, int((processed_rows / job.total_rows) * 100))
            else:
                job.percent_complete = 0
            
            job.employees_processed = employees_processed
            job.skills_processed = skills_processed
            
            if message:
                job.message = message
            
            job.status = 'processing'
            job.updated_at = datetime.now(timezone.utc)
        
        logger.debug(f"Job {job_id}: {job.percent_complete}% ({processed_rows}/{job.total_rows})")
    
    def complete_job(self, job_id: str, result: Dict, 
                    success: bool = True, error: Optional[str] = None) -> None:
        """
        Mark job as completed.
        
        Args:
            job_id: Job identifier
            result: Import result dictionary
            success: Whether import succeeded
            error: Error message if failed
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found for completion")
                return
            
            job.status = 'completed' if success else 'failed'
            job.result = result
            job.error = error
            job.percent_complete = 100 if success else job.percent_complete
            job.message = 'Import completed successfully' if success else f'Import failed: {error}'
            job.updated_at = datetime.now(timezone.utc)
            job.completed_at = datetime.now(timezone.utc)
        
        logger.info(f"Job {job_id} completed with status: {job.status}")
    
    def get_status(self, job_id: str) -> Optional[ImportJobStatus]:
        """
        Get current status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            ImportJobStatus or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)
    
    def fail_job(self, job_id: str, error: str) -> None:
        """
        Mark job as failed.
        
        Args:
            job_id: Job identifier
            error: Error message
        """
        self.complete_job(job_id, {}, success=False, error=error)


# Global singleton instance
_tracker = ImportJobTracker()


def get_job_tracker() -> ImportJobTracker:
    """Get the global job tracker instance."""
    return _tracker
