"""
Service for Master Skills Import with conflict detection and upsert operations.

Single Responsibility: Orchestrate the master import process.
"""
import logging
import os
import time
from typing import List, Optional, Callable
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

# Progress callback type: (percent: int, message: str) -> None
ProgressCallback = Callable[[int, str], None]

# Batch size for commits and progress updates
# Commits happen every COMMIT_BATCH_SIZE rows to distribute DB work evenly
COMMIT_BATCH_SIZE = 300


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
    
    def process_import(self, rows: List[MasterSkillRow], progress_callback: Optional[ProgressCallback] = None) -> MasterImportResponse:
        """
        Process master skills import with conflict detection.
        
        Args:
            rows: List of parsed rows to import
            progress_callback: Optional callback for progress updates (percent, message).
                              This should use a SEPARATE DB session to commit progress
                              independently of the main import transaction.
        
        Returns:
            MasterImportResponse with status, summary, and errors
        """
        import_start_time = time.time()
        logger.info(f"[IMPORT] ====== IMPORT STARTED ======")
        logger.info(f"[IMPORT] Total rows to process: {len(rows)}")
        logger.info(f"[IMPORT] Embedding service enabled: {self.embedding_enabled}")
        logger.info(f"[IMPORT] Commit batch size: {COMMIT_BATCH_SIZE}")
        
        # Load existing data
        if progress_callback:
            progress_callback(12, "Loading existing data...")
        cache_start = time.time()
        self.cache.load_all()
        logger.info(f"[IMPORT] Cache loaded in {time.time() - cache_start:.2f}s")
        
        # Detect duplicates within the file
        if progress_callback:
            progress_callback(15, "Checking for duplicates...")
        dup_start = time.time()
        skip_rows = self.conflict_detector.detect_file_duplicates(rows)
        logger.info(f"[IMPORT] Duplicate detection completed in {time.time() - dup_start:.2f}s | Skipping {len(skip_rows)} rows")
        
        # Process each row (10-85% progress range)
        logger.info(f"[IMPORT] Starting row processing at {time.time() - import_start_time:.2f}s elapsed")
        rows_processed, skill_ids_processed = self._process_rows(rows, skip_rows, progress_callback, import_start_time)
        
        # Commit any remaining rows from the final partial batch
        if skill_ids_processed:
            if progress_callback:
                progress_callback(88, "Committing final batch...")
            final_commit_start = time.time()
            logger.info(f"[IMPORT] Final batch commit starting at {time.time() - import_start_time:.2f}s elapsed")
            self.db.commit()
            logger.info(f"[IMPORT] Final batch commit finished in {time.time() - final_commit_start:.2f}s | Total skill IDs: {len(skill_ids_processed)}")
        
        # Generate embeddings for all processed skills (batch operation)
        embedding_result = None
        embedding_attempted = False
        if self.embedding_enabled and skill_ids_processed:
            try:
                embedding_attempted = True
                if progress_callback:
                    progress_callback(90, f"Generating embeddings for {len(skill_ids_processed)} skills...")
                embed_start = time.time()
                logger.info(f"[IMPORT] Embedding generation starting at {time.time() - import_start_time:.2f}s elapsed")
                # Pass progress callback for smooth updates during embedding generation (90% → 95%)
                embedding_result = self.embedding_service.ensure_embeddings_for_skill_ids(
                    skill_ids_processed,
                    progress_callback=progress_callback,
                    progress_start=90,
                    progress_end=95
                )
                logger.info(
                    f"[IMPORT] Embedding generation completed in {time.time() - embed_start:.2f}s | "
                    f"succeeded={len(embedding_result.succeeded)}, "
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
        
        # Commit embeddings (rows already committed in batches during _process_rows)
        if progress_callback:
            progress_callback(95, "Finalizing...")
        finalize_commit_start = time.time()
        logger.info(f"[IMPORT] Finalize commit starting at {time.time() - import_start_time:.2f}s elapsed")
        self.db.commit()  # Commit any embedding changes
        logger.info(f"[IMPORT] Finalize commit finished in {time.time() - finalize_commit_start:.2f}s")
        logger.info(f"[IMPORT] ====== IMPORT COMPLETED ======")
        logger.info(f"[IMPORT] Total time: {time.time() - import_start_time:.2f}s | Rows processed: {rows_processed}")
          # Build and return response
        return self._build_response(rows, rows_processed, embedding_result, embedding_attempted)
    
    def _process_rows(self, rows: List[MasterSkillRow], skip_rows: set, progress_callback: Optional[ProgressCallback] = None, import_start_time: float = None) -> tuple:
        """Process all rows with batch commits and return (count of successfully processed rows, list of skill_ids).
        
        Progress is reported in the 15-85% range during row processing.
        Commits happen every COMMIT_BATCH_SIZE rows to distribute DB work evenly.
        Progress is updated AFTER each commit to reflect real database state.
        """
        if import_start_time is None:
            import_start_time = time.time()
            
        rows_processed = 0
        rows_in_current_batch = 0
        committed_count = 0
        batch_number = 0
        skill_ids_processed = []
        total_rows = len(rows)
        
        # Progress range: 15% to 85% during row processing
        PROGRESS_START = 15
        PROGRESS_END = 85
        PROGRESS_RANGE = PROGRESS_END - PROGRESS_START
        
        for idx, row in enumerate(rows):
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
                rows_in_current_batch += 1
                
                # Commit batch and update progress AFTER commit
                if rows_in_current_batch >= COMMIT_BATCH_SIZE:
                    batch_commit_start = time.time()
                    logger.info(f"[IMPORT] Batch {batch_number + 1} commit starting at {time.time() - import_start_time:.2f}s elapsed | rows_in_batch={rows_in_current_batch}")
                    self.db.commit()  # Distribute DB work across batches
                    batch_commit_duration = time.time() - batch_commit_start
                    batch_number += 1
                    committed_count += rows_in_current_batch
                    rows_in_current_batch = 0
                    
                    # Update progress AFTER commit (reflects real DB state)
                    if progress_callback:
                        percent = PROGRESS_START + int((committed_count / total_rows) * PROGRESS_RANGE)
                        progress_callback(percent, f"Committed batch {batch_number} ({committed_count} / {total_rows} rows)")
                        logger.info(f"[IMPORT] Progress update: {percent}% | Committed {committed_count}/{total_rows} | Batch commit took {batch_commit_duration:.2f}s | Total elapsed {time.time() - import_start_time:.2f}s")
                    else:
                        logger.info(f"[IMPORT] Batch {batch_number} committed in {batch_commit_duration:.2f}s | {committed_count}/{total_rows} rows | Total elapsed {time.time() - import_start_time:.2f}s")
                
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
        
        # Note: Final partial batch is committed in process_import() after this method returns
        # This ensures embedding generation has all skill_ids available
        if progress_callback:
            progress_callback(PROGRESS_END, f"Row processing complete: {rows_processed} / {total_rows}")
        
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
