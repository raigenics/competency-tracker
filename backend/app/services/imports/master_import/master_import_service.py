"""
Service for Master Skills Import with conflict detection and upsert operations.

Single Responsibility: Orchestrate the master import process.
"""
import logging
from typing import List
from sqlalchemy.orm import Session

from app.schemas.master_import import (
    ImportSummary,
    ImportSummaryCount,
    MasterImportResponse
)
from .excel_parser import MasterSkillRow
from .data_cache import DataCache
from .conflict_detector import ConflictDetector
from .data_upsert import DataUpserter

logger = logging.getLogger(__name__)


class MasterImportService:
    """Service for processing master skills imports with conflict detection."""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = DataCache(db)
        self.conflict_detector = ConflictDetector()
        self.upserter = DataUpserter(db, self.cache)
    
    def process_import(self, rows: List[MasterSkillRow]) -> MasterImportResponse:
        """
        Process master skills import with conflict detection.
        
        Returns:
            MasterImportResponse with status, summary, and errors
        """
        logger.info(f"Starting import processing for {len(rows)} rows")
        
        # Load existing data
        self.cache.load_all()
        
        # Detect duplicates within the file
        skip_rows = self.conflict_detector.detect_file_duplicates(rows)
        
        # Process each row
        rows_processed = self._process_rows(rows, skip_rows)
        
        # Commit transaction
        self.db.commit()
        logger.info(f"Import committed: {rows_processed} rows processed")
        
        # Build and return response
        return self._build_response(rows, rows_processed)
    
    def _process_rows(self, rows: List[MasterSkillRow], skip_rows: set) -> int:
        """Process all rows and return count of successfully processed rows."""
        rows_processed = 0
        
        for row in rows:
            # Skip duplicate rows
            if row.row_number in skip_rows:
                continue
            
            try:
                # 1. Upsert Category
                category_id = self.upserter.upsert_category(row.category, row.category_norm)
                
                # 2. Upsert SubCategory
                subcategory_id = self.upserter.upsert_subcategory(
                    row.subcategory, row.subcategory_norm, 
                    category_id, row.category_norm
                )
                
                # 3. Upsert Skill (with conflict detection)
                skill_success, skill_id = self.upserter.upsert_skill(row, subcategory_id)
                
                # 4. Upsert Aliases (only if skill was successful)
                if skill_success and row.aliases:
                    self.upserter.upsert_aliases(row, skill_id)
                
                rows_processed += 1
                
            except Exception as e:
                # Log unexpected errors with full traceback
                logger.error(
                    f"Unexpected error processing row {row.row_number}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                from app.schemas.master_import import ImportError
                self.upserter.errors.append(ImportError(
                    row_number=row.row_number,
                    category=row.category,
                    subcategory=row.subcategory,
                    skill_name=row.skill_name,
                    error_type="UNEXPECTED_ERROR",
                    message=f"{type(e).__name__}: {str(e)}"
                ))
        
        return rows_processed
    
    def _build_response(self, rows: List[MasterSkillRow], rows_processed: int) -> MasterImportResponse:
        """Build the import response with summary and status."""
        # Combine errors from conflict detector and upserter
        all_errors = self.conflict_detector.errors + self.upserter.errors
        
        # Build summary
        summary = ImportSummary(
            rows_total=len(rows),
            rows_processed=rows_processed,
            categories=ImportSummaryCount(**self.upserter.stats['categories']),
            subcategories=ImportSummaryCount(**self.upserter.stats['subcategories']),
            skills=ImportSummaryCount(**self.upserter.stats['skills']),
            aliases=ImportSummaryCount(**self.upserter.stats['aliases'])
        )
        
        # Determine overall status
        total_conflicts = (
            self.upserter.stats['skills']['conflicts'] + 
            self.upserter.stats['aliases']['conflicts']
        )
        
        if total_conflicts > 0 and rows_processed == 0:
            status = "failed"
        elif total_conflicts > 0:
            status = "partial_success"
        else:
            status = "success"
        
        logger.info(
            f"Import complete: status={status}, errors={len(all_errors)}, "
            f"conflicts={total_conflicts}"
        )
        
        return MasterImportResponse(
            status=status,
            summary=summary,
            errors=all_errors
        )
