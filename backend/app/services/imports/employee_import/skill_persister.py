"""
Employee skill database persistence for employee import.

Single Responsibility: Insert employee skill records to database.
"""
import logging
import uuid
from typing import Dict
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models import Employee, EmployeeSkill, ProficiencyLevel
from app.services.skill_history_service import SkillHistoryService
from app.models.skill_history import ChangeSource

logger = logging.getLogger(__name__)


class SkillPersister:
    """Handles employee skill database operations."""
    
    def __init__(self, db: Session, stats: Dict, date_parser, field_sanitizer, 
                 skill_resolver, unresolved_logger, progress_callback=None):
        self.db = db
        self.stats = stats
        self.date_parser = date_parser
        self.field_sanitizer = field_sanitizer
        self.skill_resolver = skill_resolver
        self.unresolved_logger = unresolved_logger
        self.progress_callback = progress_callback  # Optional callback for progress reporting
    
    def import_employee_skills(self, skills_df: pd.DataFrame, 
                              zid_to_employee_id_mapping: Dict[str, int],
                              import_timestamp: datetime) -> int:
        """
        Import employee skills with resolution logic.
        
        Resolution Flow:
            1. For each skill row, resolve skill_name via skill_resolver
            2. If resolved: Create EmployeeSkill + SkillHistory records
            3. If unresolved: Log to raw_skill_inputs table
        
        Transaction Strategy:
            - Skills grouped by employee (ZID)
            - Each employee's skills committed as a batch
            - Failures don't affect other employees
        
        Args:
            skills_df: DataFrame with skill data
            zid_to_employee_id_mapping: Map of ZID → employee_id
            import_timestamp: Import timestamp
            
        Returns:
            Total number of skill rows processed
        """
        logger.info(f"Importing {len(skills_df)} employee skill records (with resolution)")
        
        # Create ZID to employee name/subsegment mapping for error reporting
        zid_to_name_mapping, zid_to_subsegment_mapping = self._create_employee_mappings(zid_to_employee_id_mapping)
        
        # Initialize history service
        history_service = SkillHistoryService(self.db)
        successful_skill_imports = 0        # Group skills by ZID for per-employee processing
        skills_by_zid = self._group_skills_by_zid(skills_df)
        
        # Threshold-based progress tracking (replaces buggy modulo logic)
        # Progress range: 50% → 85% (35% total for skills phase)
        total_skills = len(skills_df)
        
        # Define progress reporting interval and threshold
        progress_interval = max(1, total_skills // 10)  # Update every ~10% of skills
        next_report_at = progress_interval  # First threshold
        
        # Process each employee's skills as a batch
        processed_count = 0
        for zid, skill_rows in skills_by_zid.items():
            employee_skill_count = self._process_employee_skills(
                zid, skill_rows, zid_to_employee_id_mapping,
                zid_to_name_mapping, zid_to_subsegment_mapping,
                history_service, import_timestamp
            )
            successful_skill_imports += employee_skill_count
            processed_count += len(skill_rows)
            
            # Report progress when crossing threshold (NOT modulo!)
            # This guarantees updates even if processed_count jumps by batches
            if self.progress_callback:
                while processed_count >= next_report_at and next_report_at <= total_skills:
                    # Calculate progress from 50% to 85% (35% range for skills)
                    skill_progress_percent = (next_report_at / total_skills) * 35
                    overall_progress = 50 + skill_progress_percent
                    
                    logger.debug(f"🔔 Progress threshold reached: {next_report_at}/{total_skills} skills → {int(overall_progress)}%")
                    
                    self.progress_callback(
                        message=f"Importing skills... ({processed_count}/{total_skills})",
                        percent=int(overall_progress),
                        total_rows=100,
                        skills_processed=successful_skill_imports
                    )
                    
                    # Advance to next threshold
                    next_report_at += progress_interval
        
        # CRITICAL: Always send final progress update at 85%
        # This prevents the last visible update being stuck around ~81%
        if self.progress_callback and processed_count > 0:
            logger.debug(f"🏁 Final skill progress: {processed_count}/{total_skills} skills → 85%")
            self.progress_callback(
                message=f"Imported {successful_skill_imports}/{total_skills} skills",
                percent=85,
                total_rows=100,
                skills_processed=successful_skill_imports
            )
        
        self.stats['skills_imported'] = successful_skill_imports
        
        # Log resolution stats
        logger.info(f"Imported {successful_skill_imports} of {len(skills_df)} employee skill records")
        logger.info(f"📊 Resolution stats: exact={self.stats['skills_resolved_exact']}, "
                   f"alias={self.stats['skills_resolved_alias']}, "
                   f"unresolved={self.stats['skills_unresolved']}")
        
        return len(skills_df)  # Return total rows processed
    
    def _create_employee_mappings(self, zid_to_employee_id_mapping: Dict[str, int]) -> tuple:
        """Create ZID to employee name and subsegment mappings."""
        zid_to_name_mapping = {}
        zid_to_subsegment_mapping = {}
        
        for zid, emp_id in zid_to_employee_id_mapping.items():
            employee = self.db.query(Employee).filter(Employee.employee_id == emp_id).first()
            if employee:
                zid_to_name_mapping[zid] = employee.full_name
                zid_to_subsegment_mapping[zid] = employee.sub_segment_id
        
        return zid_to_name_mapping, zid_to_subsegment_mapping
    
    def _group_skills_by_zid(self, skills_df: pd.DataFrame) -> Dict:
        """Group skills by ZID for per-employee processing."""
        skills_by_zid = {}
        for row_idx, row in skills_df.iterrows():
            zid = str(row.get('zid', ''))
            excel_row = row_idx + 2  # Excel row number (1-based + header)
            if zid not in skills_by_zid:
                skills_by_zid[zid] = []
            skills_by_zid[zid].append((excel_row, row))
        return skills_by_zid
    
    def _process_employee_skills(self, zid: str, skill_rows: list,
                                 zid_to_employee_id_mapping: Dict,
                                 zid_to_name_mapping: Dict,
                                 zid_to_subsegment_mapping: Dict,
                                 history_service,
                                 import_timestamp: datetime) -> int:
        """Process all skills for a single employee."""
        db_employee_id = zid_to_employee_id_mapping.get(zid)
        employee_name = zid_to_name_mapping.get(zid, None)
        sub_segment_id = zid_to_subsegment_mapping.get(zid, None)
        
        if not db_employee_id:
            # Employee was not imported (failed earlier), skip all their skills
            logger.warning(f"Skipping {len(skill_rows)} skills for ZID {zid}: Employee was not imported")
            self._mark_skills_as_failed(skill_rows, zid, employee_name, "EMPLOYEE_NOT_IMPORTED")
            return 0
        
        # Process all skills for this employee in one batch
        employee_skill_records = []
        
        for excel_row, row in skill_rows:
            skill_record = self._process_single_skill(
                row, excel_row, zid, employee_name, 
                db_employee_id, sub_segment_id, import_timestamp
            )
            if skill_record:
                employee_skill_records.append(skill_record)
        
        # Commit all skills for this employee as a batch
        return self._commit_employee_skills(
            employee_skill_records, zid, employee_name,
            history_service, import_timestamp
        )
    
    def _process_single_skill(self, row, excel_row: int, zid: str, employee_name: str,
                             db_employee_id: int, sub_segment_id: int, 
                             import_timestamp: datetime):
        """Process a single skill record."""
        # DEFENSIVE: Ensure skill_name is a clean string
        skill_name_raw = row.get('skill_name', '')
        
        # Handle edge case where pandas might return a Series
        if isinstance(skill_name_raw, pd.Series):
            skill_name = str(skill_name_raw.iloc[0]).strip() if len(skill_name_raw) > 0 else ''
        else:
            skill_name = str(skill_name_raw).strip()        
        if not skill_name:
            logger.warning(f"Skipping empty skill name at Excel row {excel_row}")
            return None
        
        try:
            # Resolve skill via exact match → alias match → embedding match → None
            skill_id, resolution_method, resolution_confidence = self.skill_resolver.resolve_skill(skill_name)
            
            if not skill_id:
                # Check if it's a "needs review" case
                if resolution_method == "needs_review" and resolution_confidence:
                    # Log to raw_skill_inputs with resolution info for manual review
                    self.unresolved_logger.record_unresolved_skill(
                        skill_name=skill_name,
                        employee_id=db_employee_id,
                        sub_segment_id=sub_segment_id,
                        timestamp=import_timestamp,
                        resolution_method=resolution_method,
                        resolution_confidence=resolution_confidence
                    )
                    logger.warning(f"Skill '{skill_name}' needs review (similarity={resolution_confidence:.4f}) for ZID {zid} - logged to raw_skill_inputs")
                else:
                    # Truly unresolved skill - log to raw_skill_inputs
                    self.unresolved_logger.record_unresolved_skill(
                        skill_name=skill_name,
                        employee_id=db_employee_id,
                        sub_segment_id=sub_segment_id,
                        timestamp=import_timestamp
                    )
                    logger.warning(f"Skill '{skill_name}' unresolved for ZID {zid} - logged to raw_skill_inputs")
                
                # Track as failed row for reporting
                self.stats['failed_rows'].append({
                    'sheet': 'Employee_Skills',
                    'excel_row_number': excel_row,
                    'row_number': excel_row,
                    'zid': zid,
                    'employee_name': employee_name,
                    'skill_name': skill_name,
                    'error_code': 'SKILL_NEEDS_REVIEW' if resolution_method == "needs_review" else 'SKILL_NOT_RESOLVED',
                    'message': f'Skill "{skill_name}" {"needs manual review" if resolution_method == "needs_review" else "not found in master data"} (logged to raw_skill_inputs)'
                })
                return None
            
            # Get proficiency level ID
            proficiency_name = str(row.get('proficiency', '')).strip()
            proficiency = self.db.query(ProficiencyLevel).filter(
                ProficiencyLevel.level_name == proficiency_name
            ).first()
            
            if not proficiency:
                from app.services.import_service import ImportServiceError
                raise ImportServiceError(f"Proficiency level not found: {proficiency_name}")
            
            # Process date fields using safe parsing
            last_used = self.date_parser.parse_date_safely(
                row.get('last_used'),
                'last_used',
                f"employee {zid}"
            )
            
            started_learning_from = self.date_parser.parse_date_safely(
                row.get('started_learning_from'),
                'started_learning_from',
                f"employee {zid}"
            )
            
            # Sanitize numeric fields
            years_experience = self.field_sanitizer.sanitize_integer_field(row.get('years_experience'), 'years_experience', zid)
            interest_level = self.field_sanitizer.sanitize_integer_field(row.get('interest_level'), 'interest_level', zid)
            
            # Create employee skill
            employee_skill = EmployeeSkill(
                employee_id=db_employee_id,
                skill_id=skill_id,
                proficiency_level_id=proficiency.proficiency_level_id,
                years_experience=years_experience,
                last_used=last_used,
                started_learning_from=started_learning_from,
                certification=row.get('certification'),
                comment=row.get('comment'),
                interest_level=interest_level,
                created_at=import_timestamp
            )
            
            self.db.add(employee_skill)
            self.db.flush()  # Get emp_skill_id
            
            return employee_skill
            
        except Exception as e:
            # Log the error but don't fail the entire employee batch yet
            error_message = str(e)
            logger.warning(f"Failed to prepare skill at Excel row {excel_row} (ZID: {zid}, Skill: {skill_name}): {error_message}")
            
            # Determine error code
            error_code = self._determine_skill_error_code(error_message)
            
            # Track failed skill row with full context
            self.stats['failed_rows'].append({
                'sheet': 'Employee_Skills',
                'excel_row_number': excel_row,
                'row_number': excel_row,
                'zid': zid,
                'employee_name': employee_name,
                'skill_name': skill_name,
                'error_code': error_code,
                'message': error_message
            })
            return None
    
    def _commit_employee_skills(self, employee_skill_records: list, zid: str, 
                               employee_name: str, history_service, 
                               import_timestamp: datetime) -> int:
        """Commit all skills for an employee as a batch."""
        if not employee_skill_records:
            return 0
        
        try:
            # Add history tracking BEFORE commit (so it's in same transaction)
            batch_id = str(uuid.uuid4())[:8]
            for skill_record in employee_skill_records:
                history_service.record_skill_change(
                    employee_id=skill_record.employee_id,
                    skill_id=skill_record.skill_id,
                    old_skill_record=None,
                    new_skill_record=skill_record,
                    change_source=ChangeSource.IMPORT,
                    changed_by="system",
                    change_reason="Excel bulk import (NEW FORMAT)",
                    batch_id=batch_id
                )
            
            # Commit employee's skills + history together
            self.db.commit()
            logger.debug(f"Committed {len(employee_skill_records)} skills for employee ZID {zid}")
            return len(employee_skill_records)
            
        except Exception as e:
            # If commit fails, rollback this employee's skills only
            error_message = str(e)
            logger.error(f"Failed to commit skills for employee ZID {zid}: {error_message}")
            self.db.rollback()
            
            # Mark all this employee's skills as failed
            for skill_record in employee_skill_records:
                self.stats['failed_rows'].append({
                    'sheet': 'Employee_Skills',
                    'excel_row_number': None,
                    'row_number': None,
                    'zid': zid,
                    'employee_name': employee_name,
                    'skill_name': None,
                    'error_code': 'BATCH_COMMIT_FAILED',
                    'message': f'Failed to commit skill batch for ZID {zid}: {error_message}'
                })
            return 0
    
    def _mark_skills_as_failed(self, skill_rows: list, zid: str, employee_name: str, error_code: str):
        """Mark all skills for an employee as failed."""
        for excel_row, row in skill_rows:
            self.stats['failed_rows'].append({
                'sheet': 'Employee_Skills',
                'excel_row_number': excel_row,
                'row_number': excel_row,
                'zid': zid,
                'employee_name': employee_name or str(row.get('employee_full_name', '')),
                'skill_name': str(row.get('skill_name', '')),
                'error_code': error_code,
                'message': f'Employee ZID {zid} was not successfully imported'
            })
    
    def _determine_skill_error_code(self, error_message: str) -> str:
        """Determine error code based on error message."""
        error_message_lower = error_message.lower()
        
        if "not found" in error_message_lower:
            return "MISSING_REFERENCE"
        elif "proficiency" in error_message_lower:
            return "INVALID_PROFICIENCY"
        elif "duplicate" in error_message_lower:
            return "DUPLICATE_SKILL"
        elif "constraint" in error_message_lower:
            return "CONSTRAINT_VIOLATION"
        else:
            return "SKILL_IMPORT_ERROR"
