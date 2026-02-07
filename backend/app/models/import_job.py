"""
Import Job model - tracks progress and status of bulk import operations.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class ImportJob(Base):
    """
    Import Job model for tracking bulk import operations.
    
    This table persists the status and progress of import jobs to survive
    server restarts and enable multi-worker deployments.
    """
    
    __tablename__ = "import_jobs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Business identifier (UUID string)
    job_id = Column(String(36), unique=True, nullable=False, index=True)
    
    # Job status: 'pending', 'processing', 'completed', 'failed'
    status = Column(String(20), nullable=False, index=True, default='pending')
    
    # Progress tracking
    message = Column(String(500), nullable=True)
    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    percent_complete = Column(Integer, nullable=False, default=0)
    
    # Detailed counters for employees and skills
    employees_total = Column(Integer, nullable=False, default=0)
    employees_processed = Column(Integer, nullable=False, default=0)
    skills_total = Column(Integer, nullable=False, default=0)
    skills_processed = Column(Integer, nullable=False, default=0)
    
    # Result data (JSON) - populated on completion
    # Example: {"employees_imported": 100, "skills_imported": 500, "warnings": [...]}
    result = Column(JSON, nullable=True)
    
    # Error information (if status='failed')
    error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(), default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ImportJob(id={self.id}, job_id='{self.job_id}', status='{self.status}', progress={self.percent_complete}%)>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
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
