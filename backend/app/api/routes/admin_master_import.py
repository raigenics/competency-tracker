"""
Admin Master Skills Import API endpoint.
POST /admin/skills/master-import (async with job tracking)
"""
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.schemas.master_import import MasterImportResponse
from app.services.master_import_parser import MasterImportParser
from app.services.master_import_service import MasterImportService
from app.services.import_job_service import ImportJobService

router = APIRouter()
logger = logging.getLogger(__name__)

# Thread pool for background import processing
_master_import_executor = ThreadPoolExecutor(max_workers=2)


@router.post(
    "/admin/skills/master-import",
    summary="Master Skills Import (Async)",
    description="""
    Import skills from Excel file with conflict detection and reporting.
    
    **Returns immediately with job_id** - use GET /api/import/status/{job_id} to poll progress.
    
    **Excel Format:**
    - Column 1: Category (required)
    - Column 2: SubCategory (required)
    - Column 3: Skill Name (required)
    - Column 4: Alias (optional, comma-separated)
    
    **Behavior:**
    - Upserts data into: skill_categories, skill_subcategories, skills, skill_aliases
    - Does NOT write to raw_skill_inputs table
    - Idempotent: re-importing same data is safe
    
    **Conflict Detection:**
    - SKILL_SUBCATEGORY_CONFLICT: Skill exists under different subcategory
    - ALIAS_CONFLICT: Alias already assigned to different skill
    - DUPLICATE_IN_FILE: Same skill appears multiple times in file
    """,
    tags=["Admin"]
)
async def master_skills_import(
    file: UploadFile = File(..., description="Excel file (.xlsx or .xls)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import master skills from Excel file (async with job tracking).
    
    Returns immediately with job_id. Poll /api/import/status/{job_id} for progress.
    """
    logger.info(f"Received file upload: filename='{file.filename}', content_type='{file.content_type}'")
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        error_detail = f"Invalid file type. Please upload an Excel file (.xlsx or .xls). Received: {file.filename}"
        logger.warning(f"Rejecting file: {error_detail}")
        raise HTTPException(
            status_code=400,
            detail=error_detail
        )
    
    # Read file content immediately (before returning)
    try:
        file_content = await file.read()
        logger.info(f"File read successfully: {len(file_content)} bytes")
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {type(e).__name__}: {str(e)}"
        )
    
    # Create import job in database
    try:
        job_service = ImportJobService(db)
        job_id = job_service.create_job(
            job_type="master_skills_import",
            message="Starting import..."
        )
        logger.info(f"✅ Created master import job {job_id}")
    except Exception as e:
        logger.error(f"❌ Failed to create import job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create import job: {str(e)}"
        )
    
    # Start async import in background
    asyncio.create_task(_process_master_import_async(job_id, file_content))
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "pending",
            "message": "Import job created. Poll /api/import/status/{job_id} for progress."
        }
    )


async def _process_master_import_async(job_id: str, file_content: bytes):
    """Process master import in background thread with DB-backed progress tracking."""
    
    def _run_import():
        db = None
        progress_db = None  # Separate session for progress updates
        job_service = None
        job_start_time = time.time()
        
        try:
            logger.info(f"[IMPORT] ====== JOB {job_id} STARTED ======")
            logger.info(f"[IMPORT] Job {job_id} | File size: {len(file_content)} bytes")
            
            # Create NEW database session for background thread (main import)
            db = SessionLocal()
            
            # Create SEPARATE session for progress updates (commits independently)
            progress_db = SessionLocal()
            job_service = ImportJobService(progress_db)
            
            # Update: Parsing
            job_service.update_job(
                job_id,
                status='processing',
                percent=5,
                message='Parsing Excel file...',
                force_update=True
            )
            
            # Parse Excel file
            parser = MasterImportParser()
            parse_start = time.time()
            try:
                rows = parser.parse_excel(file_content)
                logger.info(f"[IMPORT] Job {job_id} | Excel parsed in {time.time() - parse_start:.2f}s | {len(rows)} valid rows, {len(parser.errors)} errors")
            except ValueError as e:
                logger.error(f"[IMPORT] Job {job_id} FAILED | Excel validation error after {time.time() - job_start_time:.2f}s")
                job_service.fail_job(job_id, f"Excel validation failed: {str(e)}")
                return
            except Exception as e:
                logger.error(f"[IMPORT] Job {job_id} FAILED | Unexpected parsing error after {time.time() - job_start_time:.2f}s")
                job_service.fail_job(job_id, f"Unexpected parsing error: {type(e).__name__}: {str(e)}")
                return
            
            # Check for parsing errors
            if parser.errors:
                job_service.fail_job(
                    job_id, 
                    f"File contains {len(parser.errors)} validation error(s). Please fix and retry."
                )
                return
            
            # No rows to process
            if not rows:
                job_service.complete_job(job_id, {
                    "status": "success",
                    "message": "No valid rows to process",
                    "rows_total": 0,
                    "rows_processed": 0
                })
                return
            
            # Update: Processing
            job_service.update_job(
                job_id,
                percent=10,
                message=f'Processing {len(rows)} rows...',
                total_count=len(rows),
                force_update=True
            )
            
            # Create progress callback that uses separate session
            def progress_callback(percent: int, message: str):
                """Update job progress using separate DB session."""
                try:
                    logger.info(f"[JOB UPDATE] job_id={job_id} | percent={percent}% | message='{message}' | elapsed={time.time() - job_start_time:.2f}s")
                    job_service.update_job(
                        job_id,
                        percent=percent,
                        message=message,
                        force_update=False  # Let throttling handle it
                    )
                except Exception as e:
                    # Don't let progress update failures break the import
                    logger.warning(f"[JOB UPDATE] FAILED job_id={job_id} | error={e}")
            
            # Process import with progress callback
            service = MasterImportService(db)
            process_start = time.time()
            try:
                result = service.process_import(rows, progress_callback=progress_callback)
                logger.info(f"[IMPORT] Job {job_id} | Import service completed in {time.time() - process_start:.2f}s | status={result.status}, processed={result.summary.rows_processed}")
            except ValueError as e:
                db.rollback()
                logger.error(f"[IMPORT] Job {job_id} FAILED | Validation error after {time.time() - job_start_time:.2f}s")
                job_service.fail_job(job_id, f"Import validation failed: {str(e)}")
                return
            except Exception as e:
                db.rollback()
                logger.exception(f"[IMPORT] Job {job_id} FAILED after {time.time() - job_start_time:.2f}s | {type(e).__name__}: {str(e)}")
                job_service.fail_job(job_id, f"Import processing failed: {type(e).__name__}: {str(e)}")
                return
            
            # Build result dictionary
            import_result = {
                "status": result.status,
                "summary": {
                    "rows_total": result.summary.rows_total,
                    "rows_processed": result.summary.rows_processed,
                    "categories": {
                        "inserted": result.summary.categories.inserted,
                        "existing": result.summary.categories.existing,
                        "conflicts": result.summary.categories.conflicts
                    },
                    "subcategories": {
                        "inserted": result.summary.subcategories.inserted,
                        "existing": result.summary.subcategories.existing,
                        "conflicts": result.summary.subcategories.conflicts
                    },
                    "skills": {
                        "inserted": result.summary.skills.inserted,
                        "existing": result.summary.skills.existing,
                        "conflicts": result.summary.skills.conflicts
                    },
                    "aliases": {
                        "inserted": result.summary.aliases.inserted,
                        "existing": result.summary.aliases.existing,
                        "conflicts": result.summary.aliases.conflicts
                    }
                },
                "errors_count": len(result.errors) if result.errors else 0
            }
            
            # Mark job as complete
            job_service.complete_job(job_id, import_result)
            logger.info(f"[IMPORT] ====== JOB {job_id} COMPLETED ======")
            logger.info(f"[IMPORT] Job {job_id} | Total time: {time.time() - job_start_time:.2f}s")
            
        except Exception as e:
            logger.exception(f"[IMPORT] Job {job_id} FAILED after {time.time() - job_start_time:.2f}s | {type(e).__name__}: {str(e)}")
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            if job_service:
                job_service.fail_job(job_id, error_msg)
            else:
                try:
                    fallback_db = SessionLocal()
                    fallback_service = ImportJobService(fallback_db)
                    fallback_service.fail_job(job_id, error_msg)
                    fallback_db.close()
                except Exception as fallback_err:
                    logger.error(f"❌ Failed to update job status on error: {fallback_err}")
            
        finally:
            # Close main import session
            if db:
                try:
                    db.close()
                    logger.info(f"🔵 Main database session closed for job {job_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to close main database session: {str(e)}")
            
            # Close progress tracking session
            if progress_db:
                try:
                    progress_db.close()
                    logger.info(f"🔵 Progress database session closed for job {job_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to close progress database session: {str(e)}")
    
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_master_import_executor, _run_import)
