"""
Service for Master Skills Import with conflict detection and upsert operations.

Single Responsibility: Orchestrate the master import process.
"""
import logging
import os
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
          # Initialize embedding service (optional - graceful degradation if not available)
        self.embedding_service = None
        self.embedding_enabled = False
        self.embedding_unavailable_reason = None
        try:
            from app.services.skill_resolution.embedding_provider import create_embedding_provider
            from app.services.skill_resolution.skill_embedding_service import SkillEmbeddingService
            
            provider = create_embedding_provider()
            self.embedding_service = SkillEmbeddingService(
                db=db,
                embedding_provider=provider
            )
            self.embedding_enabled = True
            logger.info("Master import: Embedding service initialized and enabled")
        except Exception as e:
            self.embedding_unavailable_reason = f"{type(e).__name__}: {str(e)}"
            logger.warning(f"Master import: Embedding service not available: {self.embedding_unavailable_reason}. Imports will continue without embeddings.")
    
    def process_import(self, rows: List[MasterSkillRow]) -> MasterImportResponse:
        """
        Process master skills import with conflict detection.
        
        Returns:
            MasterImportResponse with status, summary, and errors
        """
        logger.info(f"Starting import processing for {len(rows)} rows")
        logger.info(f"Embedding service status: enabled={self.embedding_enabled}")
        
        # Load existing data
        self.cache.load_all()
        
        # Detect duplicates within the file
        skip_rows = self.conflict_detector.detect_file_duplicates(rows)
        
        # Process each row
        rows_processed, skill_ids_processed = self._process_rows(rows, skip_rows)
        
        # Flush to ensure all skill_ids are available in database
        if skill_ids_processed:
            self.db.flush()
            logger.info(f"Flushed {len(skill_ids_processed)} skill IDs to database before embedding generation")
        
        # Generate embeddings for all processed skills (batch operation)
        embedding_result = None
        embedding_attempted = False
        if self.embedding_enabled and skill_ids_processed:
            try:
                embedding_attempted = True
                logger.info(f"Attempting to generate embeddings for {len(skill_ids_processed)} skills")
                embedding_result = self.embedding_service.ensure_embeddings_for_skill_ids(skill_ids_processed)
                logger.info(
                    f"Embedding generation complete: succeeded={len(embedding_result.succeeded)}, "
                    f"skipped={len(embedding_result.skipped)}, failed={len(embedding_result.failed)}"
                )
            except Exception as e:
                logger.error(f"Embedding generation failed with exception: {e}", exc_info=True)
                # Create a failed result
                from app.services.skill_resolution.skill_embedding_service import EmbeddingResult
                embedding_result = EmbeddingResult(
                    succeeded=[],
                    failed=[{'skill_id': sid, 'skill_name': 'unknown', 'error': str(e)} for sid in skill_ids_processed],
                    skipped=[]
                )
        elif not self.embedding_enabled:
            logger.info(f"Embedding generation not attempted: service disabled ({self.embedding_unavailable_reason})")
        elif not skill_ids_processed:
            logger.info("Embedding generation not attempted: no skills processed")
        
        # Commit transaction (includes skills, aliases, and embeddings)
        self.db.commit()
        logger.info(f"Import committed: {rows_processed} rows processed")
          # Build and return response
        return self._build_response(rows, rows_processed, embedding_result, embedding_attempted)
    
    def _process_rows(self, rows: List[MasterSkillRow], skip_rows: set) -> tuple:
        """Process all rows and return (count of successfully processed rows, list of skill_ids)."""
        rows_processed = 0
        skill_ids_processed = []
        
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
                
                # Track skill_id for embedding generation
                # Include ALL skill_ids that are present (new, existing, even conflicted)
                # because embeddings should be ensured for all skills in the system
                if skill_id:
                    skill_ids_processed.append(skill_id)
                
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
        return rows_processed, skill_ids_processed
    
    def _build_response(self, rows: List[MasterSkillRow], rows_processed: int, embedding_result, embedding_attempted: bool) -> MasterImportResponse:
        """Build the import response with summary and status."""
        # Combine errors from conflict detector and upserter
        all_errors = self.conflict_detector.errors + self.upserter.errors
        
        # Add embedding failures as separate errors (not blocking)
        if embedding_result and embedding_result.failed:
            from app.schemas.master_import import ImportError
            for failure in embedding_result.failed:
                all_errors.append(ImportError(
                    row_number=None,  # Not row-specific
                    skill_name=failure.get('skill_name'),
                    error_type="EMBEDDING_GENERATION_FAILED",
                    message=f"Embedding generation failed: {failure.get('error')}"
                ))
        
        # Build embedding status
        from app.schemas.master_import import EmbeddingStatus
        if self.embedding_enabled:
            if embedding_attempted and embedding_result:
                embedding_status = EmbeddingStatus(
                    enabled=True,
                    attempted=True,
                    succeeded_count=len(embedding_result.succeeded),
                    skipped_count=len(embedding_result.skipped),
                    failed_count=len(embedding_result.failed),
                    reason=None
                )
            elif not embedding_attempted:
                embedding_status = EmbeddingStatus(
                    enabled=True,
                    attempted=False,
                    succeeded_count=0,
                    skipped_count=0,
                    failed_count=0,
                    reason="No skills processed"
                )
            else:
                embedding_status = EmbeddingStatus(
                    enabled=True,
                    attempted=False,
                    succeeded_count=0,
                    skipped_count=0,
                    failed_count=0,
                    reason="Embedding generation failed to start"
                )
        else:
            embedding_status = EmbeddingStatus(
                enabled=False,
                attempted=False,
                succeeded_count=0,
                skipped_count=0,
                failed_count=0,
                reason=f"Embedding service not available: {self.embedding_unavailable_reason}"
            )
        
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
        
        # Log embedding stats
        logger.info(
            f"Embedding status: enabled={embedding_status.enabled}, attempted={embedding_status.attempted}, "
            f"succeeded={embedding_status.succeeded_count}, skipped={embedding_status.skipped_count}, "
            f"failed={embedding_status.failed_count}"
        )
        
        logger.info(
            f"Import complete: status={status}, errors={len(all_errors)}, "
            f"conflicts={total_conflicts}"
        )
        
        return MasterImportResponse(
            status=status,
            summary=summary,
            errors=all_errors,
            embedding_status=embedding_status
        )
