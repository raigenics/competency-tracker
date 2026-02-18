"""
Employee Import Orchestrator - Main service for employee Excel imports.

Single Responsibility: Coordinate the employee import process.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models import Employee, EmployeeSkill
from app.utils.excel_reader import read_excel, get_master_data_for_scanning

from .date_parser import DateParser
from .name_normalizer import NameNormalizer
from .field_sanitizer import FieldSanitizer
from .org_master_data_processor import OrgMasterDataProcessor
from .skill_resolver import SkillResolver
from .unresolved_skill_logger import UnresolvedSkillLogger
from .employee_persister import EmployeePersister
from .skill_expander import SkillExpander
from .skill_persister import SkillPersister

logger = logging.getLogger(__name__)

# Import DB-backed job service (not in-memory tracker)
from app.services.import_job_service import ImportJobService


class ImportServiceError(Exception):
    """Custom exception for import service errors."""
    pass


class EmployeeImportOrchestrator:
    """Orchestrates the employee import process."""
    
    def __init__(self, db_session: Optional[Session] = None, job_id: Optional[str] = None):
        self.db: Optional[Session] = db_session
        self.job_id = job_id  # Optional job_id for DB-backed progress tracking
        # Use DB-backed job service for progress tracking (not in-memory tracker)
        self.job_service = ImportJobService(db_session) if job_id and db_session else None
        self.import_stats = {
            'employees_imported': 0,
            'skills_imported': 0,
            'new_sub_segments': [],
            'new_projects': [],
            'new_teams': [],
            'new_roles': [],
            'failed_rows': [],
            # Skill resolution stats
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
        
        # Initialize components
        self.date_parser = DateParser()
        self.name_normalizer = NameNormalizer()
        self.field_sanitizer = FieldSanitizer()
    
    def import_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Import Excel file data with NEW FORMAT.

        CHANGES FROM LEGACY:
        - Employee_Skills sheet NO LONGER has Category/Subcategory columns
        - Skills resolved via exact match → alias match → unresolved (logged to raw_skill_inputs)
        - Category/Subcategory derived from DB relationship: Skill → SkillSubcategory → SkillCategory
        - Org master data (SubSegment/Project/Team) still scanned and created from Employee sheet

        Import Flow:
            1. Read & normalize Excel (employees_df, skills_df)
            2. Scan & seed org master data (SubSegment/Project/Team/Role)
            3. Import employees → build zid_to_employee_id mapping
            4. Import skills with resolution (exact/alias/unresolved)
            5. Commit transaction

        Args:
            file_path (str): Path to the Excel file

        Returns:
            Dict with import statistics including resolution metrics

        Raises:
            ImportServiceError: If import fails
        """
        logger.info(f"Starting Excel import (NEW FORMAT - no category/subcategory in skills) from: {file_path}")        # Use provided session or create new one
        if self.db is None:
            self.db = SessionLocal()
            should_close_session = True
        else:
            should_close_session = False

        # Validate PostgreSQL connection before starting
        try:
            self.db.execute(text("SELECT 1"))
            logger.info("PostgreSQL connection validated successfully")
        except Exception as e:
            error_msg = f"PostgreSQL connection failed: {str(e)}"
            logger.error(error_msg)
            if should_close_session:
                self.db.close()
            raise ImportServiceError(error_msg)

        try:
            # Step 1: Read Excel data
            logger.info("Reading Excel data")
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, status='processing', percent=5, message="Reading Excel file..."
                )
            
            employees_df, skills_df = read_excel(file_path)
            logger.info(f"Read {len(employees_df)} employees, {len(skills_df)} skills")
            logger.info(f"Employee columns: {list(employees_df.columns)}")
            logger.info(f"Skills columns: {list(skills_df.columns)}")
            
            # Calculate total rows for progress tracking
            total_rows = len(employees_df) + len(skills_df)
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, percent=10,
                    message=f"Processing {len(employees_df)} employees and {len(skills_df)} skills...",
                    total_count=total_rows
                )

            # Step 2: Generate import timestamp (UTC timezone-aware)
            import_timestamp = datetime.now(timezone.utc)
            logger.info(f"Import timestamp: {import_timestamp.isoformat()}")

            # Step 3: Scan org master data from Employee sheet ONLY
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, percent=15, message="Scanning organization master data..."
                )
            master_data = get_master_data_for_scanning(employees_df, skills_df)

            # Step 4: Clear fact tables (employees and employee_skills)
            # NOTE: Skipped for upsert logic - we now update existing records
            # self._clear_fact_tables()

            # Step 5: Process org master data (SubSegment/Project/Team/Role only)
            # NOTE: create_missing=False means we do NOT create missing master data.
            # Instead, per-row validation in EmployeePersister will fail rows with 
            # missing SubSegment/Project/Team/Role references.
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, percent=20, message="Validating organization structure..."
                )
            org_processor = OrgMasterDataProcessor(self.db, self.import_stats, create_missing=False)
            org_processor.process_all(master_data)

            # Step 6: Import employees FIRST
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, percent=30, message="Importing employees (upsert mode)..."
                )
            employee_persister = EmployeePersister(
                self.db, self.import_stats, 
                self.date_parser, self.field_sanitizer
            )
            zid_to_employee_id_mapping = employee_persister.import_employees(
                employees_df, import_timestamp
            )
            
            # Update progress after employees imported
            if self.job_service and self.job_id:
                employees_processed = self.import_stats.get('employees_imported', 0)
                self.job_service.update_job(
                    self.job_id, percent=50,
                    message=f"Imported {employees_processed} employees",
                    employees_processed=employees_processed
                )

            # Step 7: Expand comma-separated skills
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, percent=55, message="Expanding comma-separated skills..."
                )
            skill_expander = SkillExpander()
            skills_df = skill_expander.expand_skills(skills_df)

            # Step 8: Import employee skills with resolution
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, percent=60,
                    message=f"Importing {len(skills_df)} skills with resolution..."
                )
            skill_resolver = SkillResolver(self.db, self.import_stats)
            skill_resolver.set_name_normalizer(self.name_normalizer.normalize_name)
            
            unresolved_logger = UnresolvedSkillLogger(self.db)
            unresolved_logger.set_name_normalizer(self.name_normalizer.normalize_name)
            
            skill_persister = SkillPersister(
                self.db, self.import_stats,
                self.date_parser, self.field_sanitizer,
                skill_resolver, unresolved_logger
            )
            expanded_skill_count = skill_persister.import_employee_skills(
                skills_df, zid_to_employee_id_mapping, import_timestamp
            )
            
            # Update progress after skills imported
            if self.job_service and self.job_id:
                skills_processed = self.import_stats.get('skills_imported', 0)
                self.job_service.update_job(
                    self.job_id, percent=90,
                    message=f"Imported {skills_processed} skills",
                    skills_processed=skills_processed
                )

            # Step 9: Ensure all changes are flushed and committed
            if self.job_service and self.job_id:
                self.job_service.update_job(
                    self.job_id, percent=95, message="Committing changes to database..."
                )
            self.db.flush()
            self.db.commit()

            logger.info("Excel import completed successfully")
            logger.info(f"Skill resolution stats: exact={self.import_stats['skills_resolved_exact']}, "
                        f"alias={self.import_stats['skills_resolved_alias']}, "
                        f"unresolved={self.import_stats['skills_unresolved']}")

            # Build response
            response = self._build_response(employees_df, expanded_skill_count)
            
            # Mark job as completed in DB
            if self.job_service and self.job_id:
                self.job_service.complete_job(self.job_id, result=response)
            
            return response

        except Exception as e:
            if self.db:
                self.db.rollback()
                logger.error("Transaction rolled back due to error")
            
            # Enhanced error reporting for PostgreSQL
            error_msg = self._format_error_message(str(e))
            logger.error(error_msg)
            
            # Mark job as failed in DB
            if self.job_service and self.job_id:
                self.job_service.fail_job(self.job_id, error_msg)
            
            raise ImportServiceError(error_msg)
        
        finally:
            # Only close session if we created it
            if self.db and should_close_session:
                self.db.close
    
    def _clear_fact_tables(self):
        """Clear volatile fact tables (employees and employee_skills)."""
        logger.info("Clearing fact tables (employees, employee_skills)")
        
        try:
            # Delete in correct order (children first)
            deleted_skills = self.db.query(EmployeeSkill).delete()
            logger.info(f"Deleted {deleted_skills} employee skill records")
            
            deleted_employees = self.db.query(Employee).delete()
            logger.info(f"Deleted {deleted_employees} employee records")
        except SQLAlchemyError as e:
            raise ImportServiceError(f"Failed to clear fact tables: {str(e)}")
    
    def _build_response(self, employees_df, expanded_skill_count: int) -> Dict[str, Any]:
        """Build the import response dictionary."""
        # Determine status based on failures
        total_employee_rows = len(employees_df)
        total_skill_rows_expanded = expanded_skill_count

        employee_imported = self.import_stats['employees_imported']
        skill_imported = self.import_stats['skills_imported']

        # Count failed employees vs failed skills
        failed_employee_count = len([r for r in self.import_stats['failed_rows'] if r.get('sheet') == 'Employee'])
        failed_skill_count = len([r for r in self.import_stats['failed_rows'] if r.get('sheet') == 'Employee_Skills'])
        total_failed = len(self.import_stats['failed_rows'])

        status = 'success' if total_failed == 0 else 'completed_with_errors'

        return {
            'status': status,
            'employee_total': total_employee_rows,
            'employee_imported': employee_imported,
            'employee_failed': failed_employee_count,
            'skill_total': total_skill_rows_expanded,
            'skill_imported': skill_imported,
            'skill_failed': failed_skill_count,
            # Skill resolution stats
            'skills_resolved_exact': self.import_stats['skills_resolved_exact'],
            'skills_resolved_alias': self.import_stats['skills_resolved_alias'],
            'skills_unresolved': self.import_stats['skills_unresolved'],
            'unresolved_skill_names': self.import_stats['unresolved_skill_names'],
            # Legacy fields for backward compatibility
            'total_rows': total_employee_rows,
            'success_count': employee_imported,
            'failed_count': total_failed,
            **self.import_stats
        }
    
    def _format_error_message(self, error: str) -> str:
        """Format error message with PostgreSQL-specific hints."""
        error_msg = f"Excel import failed: {error}"
        error_lower = error.lower()
        
        if "duplicate key" in error_lower:
            error_msg += " (PostgreSQL constraint violation - check for duplicate data)"
        elif "foreign key" in error_lower:
            error_msg += " (PostgreSQL foreign key constraint - check data relationships)"
        elif "not null" in error_lower:
            error_msg += " (PostgreSQL NOT NULL constraint - check for missing required data)"
        elif "connection" in error_lower:
            error_msg += " (PostgreSQL connection issue - check database availability)"
        
        return error_msg
