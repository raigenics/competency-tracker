"""
FastAPI routes for Excel import functionality.
"""
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.import_service import ImportService, ImportServiceError
from app.db.session import get_db

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/import", tags=["import"])


@router.post("/excel", response_model=Dict[str, Any])
async def import_excel_file(
    file: UploadFile = File(..., description="Excel file containing employee and skills data"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Import employee and skills data from Excel file.
    
    Expected Excel format:
    - Sheet 1: employees (employee_id, first_name, last_name, sub_segment, project, team, role)
    - Sheet 2: skills (employee_id, skill_name, category, subcategory, proficiency_level, 
               years_experience, last_used_year, interest_level)
    
    Returns:
        Dict with import statistics and status
    
    Raises:
        HTTPException: If file validation or import fails
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
    
    temp_file_path = None
    
    try:
        # Save uploaded file to temporary location
        temp_file_path = await _save_upload_file(file)
        logger.info(f"Saved uploaded file to: {temp_file_path}")
          # Process the import
        import_service = ImportService(db_session=db)
        result = import_service.import_excel(temp_file_path)
        
        logger.info(f"Import completed successfully: {result}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except ImportServiceError as e:
        logger.error(f"Import service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during import"
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {str(e)}")


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
