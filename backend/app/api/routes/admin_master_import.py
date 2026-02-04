"""
Admin Master Skills Import API endpoint.
POST /admin/skills/master-import
"""
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.master_import import MasterImportResponse
from app.services.master_import_parser import MasterImportParser
from app.services.master_import_service import MasterImportService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/admin/skills/master-import",
    response_model=MasterImportResponse,
    summary="Master Skills Import",
    description="""
    Import skills from Excel file with conflict detection and reporting.
    
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
    
    **Response Status:**
    - `success`: All rows imported without conflicts
    - `partial_success`: Some rows imported, some conflicts detected
    - `failed`: No rows imported due to conflicts/errors
    """,
    tags=["Admin"]
)
async def master_skills_import(
    file: UploadFile = File(..., description="Excel file (.xlsx or .xls)"),
    db: Session = Depends(get_db)
):
    """
    Import master skills from Excel file.
    
    Args:
        file: Excel file upload
        db: Database session
        
    Returns:
        MasterImportResponse with status, summary, and errors
        
    Raises:
        HTTPException: If file is invalid or parsing fails
    """
    # Log received file details for debugging
    logger.info(f"Received file upload: filename='{file.filename}', content_type='{file.content_type}'")
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        error_detail = f"Invalid file type. Please upload an Excel file (.xlsx or .xls). Received: {file.filename}"
        logger.warning(f"Rejecting file: {error_detail}")
        raise HTTPException(
            status_code=400,
            detail=error_detail
        )
    
    # Read file content
    try:
        file_content = await file.read()
        logger.info(f"File read successfully: {len(file_content)} bytes")
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {type(e).__name__}: {str(e)}"
        )
      # Parse Excel file
    parser = MasterImportParser()
    try:
        rows = parser.parse_excel(file_content)
        logger.info(f"Excel parsed successfully: {len(rows)} valid rows, {len(parser.errors)} validation errors")
    except ValueError as e:
        # Known validation error - return 400 with clear details
        logger.warning(f"Excel validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Excel validation failed",
                "message": str(e),
                "type": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        # Unexpected parsing error - log and return 500
        logger.error(f"Unexpected error parsing Excel: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error parsing Excel file: {type(e).__name__}: {str(e)}"
        )
      # Check for parsing errors
    if parser.errors:
        # Return validation errors without processing
        logger.warning(f"Returning {len(parser.errors)} row validation errors without processing")
        from app.schemas.master_import import ImportSummary, ImportSummaryCount, ImportError
        
        summary = ImportSummary(
            rows_total=len(rows) + len(parser.errors),
            rows_processed=0,
            categories=ImportSummaryCount(),
            subcategories=ImportSummaryCount(),
            skills=ImportSummaryCount(),
            aliases=ImportSummaryCount()
        )
        
        errors = [ImportError(**err) for err in parser.errors]
        
        # Return as successful response with errors (not HTTP 400)
        return MasterImportResponse(
            status="failed",
            summary=summary,
            errors=errors
        )
      # No rows to process
    if not rows:
        logger.info("No valid rows to process after parsing")
        from app.schemas.master_import import ImportSummary, ImportSummaryCount
        
        summary = ImportSummary(
            rows_total=0,
            rows_processed=0,
            categories=ImportSummaryCount(),
            subcategories=ImportSummaryCount(),
            skills=ImportSummaryCount(),
            aliases=ImportSummaryCount()
        )
        
        return MasterImportResponse(
            status="success",
            summary=summary,
            errors=[]
        )
    
    # Process import
    logger.info(f"Starting import processing for {len(rows)} rows")
    service = MasterImportService(db)
    try:
        result = service.process_import(rows)
        logger.info(f"Import completed: status={result.status}, processed={result.summary.rows_processed}")
        return result
    except ValueError as e:
        # Known business logic error (e.g., validation failure) - return 400
        logger.warning(f"Import validation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Import validation failed",
                "message": str(e),
                "type": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        # Unexpected error - log with full traceback and return 500
        logger.error(
            f"Unexpected error during import processing: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Import processing failed: {type(e).__name__}: {str(e)}"
        )
