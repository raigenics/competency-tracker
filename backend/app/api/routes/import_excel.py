"""
FastAPI routes for Excel import functionality.
"""
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.import_service import ImportService, ImportServiceError
from app.services.import_job_service import ImportJobService
from app.db.session import get_db

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/import", tags=["import"])

# Thread pool for background import processing
executor = ThreadPoolExecutor(max_workers=2)


@router.post("/excel", response_model=Dict[str, Any])
async def import_excel_file(
    file: UploadFile = File(..., description="Excel file containing employee and skills data"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import employee and skills data from Excel file with progress tracking.
    
    Returns immediately with a job_id. Use GET /import/status/{job_id} to poll progress.
    
    Expected Excel format:
    - Sheet 1: employees (employee_id, first_name, last_name, sub_segment, project, team, role)
    - Sheet 2: skills (employee_id, skill_name, category, subcategory, proficiency_level, 
               years_experience, last_used_year, interest_level)
    
    Returns:
        Dict with job_id for polling status
    
    Raises:
        HTTPException: If file validation fails
    """
    logger.info(f"Received Excel import request for file: {file.filename}")
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    # Validate file size (limit to 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file.size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        )
      # Save uploaded file to temporary location
    try:
        temp_file_path = await _save_upload_file(file)
        logger.info(f"Saved uploaded file to: {temp_file_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Create import job in database
    try:
        job_service = ImportJobService(db)
        job_id = job_service.create_job(
            job_type="employee_import",
            message="Import starting..."
        )
        logger.info(f"✅ Created DB-backed import job {job_id} for file: {file.filename}")
    except Exception as e:
        logger.error(f"❌ Failed to create import job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create import job: {str(e)}"
        )
    
    # Start async import in background
    asyncio.create_task(_process_import_async(job_id, temp_file_path))
    
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "job_id": job_id,
            "status": "pending",
            "message": "Import job created. Poll /import/status/{job_id} for progress."
        }
    )


async def _process_import_async(job_id: str, file_path: str):
    """Process import in background thread with DB-backed progress tracking."""
    def _run_import():
        db = None
        import_service = None
        job_service = None
        try:
            logger.info(f"🔵 Starting background import for job {job_id}")
            logger.info(f"🔵 Creating new database session for background thread...")
            
            # Create NEW database session for background thread
            from app.db.session import SessionLocal
            db = SessionLocal()
            
            logger.info(f"🔵 Database session created successfully")
            
            # Create job service for progress updates
            job_service = ImportJobService(db)
            
            # Create import service with job_id
            logger.info(f"🔵 Creating ImportService for file: {file_path}")
            import_service = ImportService(db_session=db, job_id=job_id)
            
            logger.info(f"🔵 Starting Excel import...")
            result = import_service.import_excel(file_path)
            
            logger.info(f"🔵 Import completed, updating job status...")
            
            # Mark job as complete in database
            job_service.complete_job(job_id, result)
            
            logger.info(f"✅ Import job {job_id} completed successfully")
            
        except Exception as e:
            # Mark job as failed in database
            logger.error(f"❌ Import job {job_id} failed: {type(e).__name__}", exc_info=True)
            
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            if job_service:
                job_service.fail_job(job_id, error_msg)
            else:
                # Fallback: create new session to update job status
                try:
                    from app.db.session import SessionLocal
                    fallback_db = SessionLocal()
                    fallback_service = ImportJobService(fallback_db)
                    fallback_service.fail_job(job_id, error_msg)
                    fallback_db.close()
                except Exception as fallback_err:
                    logger.error(f"❌ Failed to update job status on error: {fallback_err}")
            
            logger.error(f"❌ Job {job_id} marked as failed with error: {error_msg}")
            
        finally:
            # Close database session
            if db:
                try:
                    db.close()
                    logger.info(f"🔵 Database session closed for job {job_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to close database session: {str(e)}")
            
            # Clean up temporary file
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.info(f"🧹 Cleaned up temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clean up temporary file {file_path}: {str(e)}")
      # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _run_import)


async def _save_upload_file(upload_file: UploadFile) -> str:
    """
    Save uploaded file to a temporary location.
    
    Args:
        upload_file: The uploaded file
        
    Returns:
        str: Path to the saved temporary file
        
    Raises:
        Exception: If file saving fails
    """
    try:
        # Create temporary file
        suffix = Path(upload_file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            
            # Read and write file contents
            content = await upload_file.read()
            temp_file.write(content)
            temp_file.flush()
            
        logger.info(f"Saved {len(content)} bytes to temporary file: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise Exception(f"Failed to save uploaded file: {str(e)}")


@router.get("/status/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get the current status of an import job from database.
    
    Args:
        job_id: The job identifier returned from POST /import/excel
        db: Database session
        
    Returns:
        Dict with job status, progress, and results
        
    Raises:
        HTTPException: If job not found
    """
    job_service = ImportJobService(db)
    job_status = job_service.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {job_id} not found"
        )
    
    # Ensure backward compatibility with frontend
    # Frontend expects 'percent_complete' field
    if 'percent_complete' not in job_status:
        job_status['percent_complete'] = job_status.get('percent', 0)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=job_status
    )


@router.get("/status")
async def get_import_status() -> Dict[str, str]:
    """
    Get the current status of the import service.
    
    Returns:
        Dict with service status information
    """
    return {
        "service": "import_service",
        "status": "ready",
        "version": "1.0.0",
        "supported_formats": ["xlsx", "xls"]
    }
