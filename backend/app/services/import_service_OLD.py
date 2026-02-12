"""
Import service for the Competency Tracking System.
Handles Excel data import with hierarchical master data processing and PostgreSQL compatibility.
"""
import logging
import pandas as pd
import uuid
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models import (
    Employee, EmployeeSkill, SubSegment, Project, Team,
    SkillCategory, SkillSubcategory, Skill, ProficiencyLevel, Role
)
from app.models.skill_alias import SkillAlias
from app.models.raw_skill_input import RawSkillInput
from app.utils.excel_reader import read_excel, ExcelReaderError, get_master_data_for_scanning
from app.services.skill_history_service import SkillHistoryService
from app.models.skill_history import ChangeSource

logger = logging.getLogger(__name__)


class ImportServiceError(Exception):
    """Custom exception for import service errors."""
    pass


class ImportService:
    """Service class for handling Excel imports with PostgreSQL compatibility."""
    def __init__(self, db_session: Optional[Session] = None):
        self.db: Optional[Session] = db_session
        self.import_stats = {
            'employees_imported': 0,
            'skills_imported': 0,
            'new_sub_segments': [],
            'new_projects': [],
            'new_teams': [],
            'new_roles': [],
            'failed_rows': [],
            # Skill resolution stats (NEW)
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }

    def _parse_date_safely(self, date_str: str, field_name: str, record_id: str = "") -> Optional[date]:
        """
        Safely parse date strings with PostgreSQL compatibility.

        Args:
            date_str: Date string to parse
            field_name: Name of the field for logging
            record_id: ID of the record for logging

        Returns:
            Parsed date or None if parsing fails
        """
        if not date_str or str(date_str).lower() in ['nan', 'none', '']:
            return None

        try:
            # Clean the date string
            date_str = str(date_str).strip()

            # Common date formats to try
            date_formats = [
                '%Y-%m-%d',      # 2011-02-02 (ISO format - PostgreSQL preferred)
                '%d-%m-%Y',      # 02-02-2011
                '%m/%d/%Y',      # 02/02/2011
                '%d/%m/%Y',      # 02/02/2011
                '%Y/%m/%d',      # 2011/02/02                '%d-%b-%y',      # 1-Sep-25
                '%d-%B-%y',      # 1-September-25
                '%d-%b-%Y',      # 1-Sep-2025
                '%d-%B-%Y',      # 1-September-2025
                '%d-%m-%Y',      # 01-02-2025
            ]

            parsed_date = None
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, date_format).date()
                    break
                except ValueError:
                    continue

            if parsed_date:
                # Validate date range for PostgreSQL compatibility
                if parsed_date.year < 1000 or parsed_date.year > 9999:
                    logger.warning(f"Date year out of PostgreSQL range for {field_name} '{date_str}' in record {record_id}")
                    return None
                return parsed_date
            else:
                # Special case: try to extract year and create end-of-year date
                try:
                    year = int(date_str)
                    if 1900 <= year <= 2100:
                        return datetime(year, 12, 31).date()
                except ValueError:                pass

                logger.warning(f"Could not parse {field_name} '{date_str}' for record {record_id}")
                return None
        
        except Exception as e:
            logger.warning(f"Date conversion error for {field_name} '{date_str}' in record {record_id}: {e}")
            return None
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize any name for case-insensitive comparison.
        Matches database unique constraints: lower(trim(name))

        Args:
            name: Raw name from Excel

        Returns:
            Normalized name (trimmed, collapsed spaces, lowercased)
        """
        if not name:
            return ""
        # Strip leading/trailing spaces and collapse multiple internal spaces
        import re
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        # Return lowercased for comparison
        return name.lower()
    
    def _normalize_subcategory_name(self, name: str) -> str:
        """
        Normalize subcategory name for case-insensitive comparison.
        Wrapper for _normalize_name() for backward compatibility.
        
        Args:
            name: Raw subcategory name from Excel

        Returns:
            Normalized name (trimmed, collapsed spaces, lowercased)
        """
        return self._normalize_name(name)
    
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
        logger.info(f"Starting Excel import (NEW FORMAT - no category/subcategory in skills) from: {file_path}")

        # Use provided session or create new one
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
            employees_df, skills_df = read_excel(file_path)
            logger.info(f"Read {len(employees_df)} employees, {len(skills_df)} skills")
            logger.info(f"Employee columns: {list(employees_df.columns)}")
            logger.info(f"Skills columns: {list(skills_df.columns)}")

            # Step 2: Generate import timestamp (UTC timezone-aware)
            import_timestamp = datetime.now(timezone.utc)
            logger.info(f"Import timestamp: {import_timestamp.isoformat()}")

            # Step 3: Scan org master data from Employee sheet ONLY (no skill categories/subcategories)
            master_data = get_master_data_for_scanning(employees_df, skills_df)

            # Step 4: Clear fact tables (employees and employee_skills)
            self._clear_fact_tables()

            # Step 5: Process org master data (SubSegment/Project/Team/Role only - NO skill hierarchy)
            self._process_org_master_data(master_data)

            # Step 6: Import employees FIRST
            zid_to_employee_id_mapping = self._import_employees(employees_df, import_timestamp)

            # Step 7: Import employee skills with resolution (NEW METHOD)
            expanded_skill_count = self._import_employee_skills_with_resolution(
                skills_df, 
                zid_to_employee_id_mapping, 
                import_timestamp
            )

            # Step 8: Ensure all changes are flushed and committed
            self.db.flush()
            self.db.commit()

            logger.info("Excel import completed successfully")
            logger.info(f"Skill resolution stats: exact={self.import_stats['skills_resolved_exact']}, "
                        f"alias={self.import_stats['skills_resolved_alias']}, "
                        f"unresolved={self.import_stats['skills_unresolved']}")

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
                # Skill resolution stats (NEW)
                'skills_resolved_exact': self.import_stats['skills_resolved_exact'],
                'skills_resolved_alias': self.import_stats['skills_resolved_alias'],
                'skills_unresolved': self.import_stats['skills_unresolved'],
                'unresolved_skill_names': self.import_stats['unresolved_skill_names'],                # Legacy fields for backward compatibility
                'total_rows': total_employee_rows,
                'success_count': employee_imported,
                'failed_count': total_failed,
                **self.import_stats
            }

        except Exception as e:
            if self.db:
                self.db.rollback()
                logger.error("Transaction rolled back due to error")
            
            # Enhanced error reporting for PostgreSQL
            error_msg = f"Excel import failed: {str(e)}"
            if "duplicate key" in str(e).lower():
                error_msg += " (PostgreSQL constraint violation - check for duplicate data)"
            elif "foreign key" in str(e).lower():
                error_msg += " (PostgreSQL foreign key constraint - check data relationships)"
            elif "not null" in str(e).lower():
                error_msg += " (PostgreSQL NOT NULL constraint - check for missing required data)"
            elif "connection" in str(e).lower():
                error_msg += " (PostgreSQL connection issue - check database availability)"
            
            logger.error(error_msg)
            raise ImportServiceError(error_msg)
        
        finally:
            # Only close session if we created it
            if self.db and should_close_session:
                self.db.close()
    
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
    
    def _process_org_master_data(self, master_data: Dict[str, Set]):
        """
        Process org master data (SubSegment/Project/Team/Role) from Employee sheet.

        NOTE: NEW FORMAT - Does NOT process skill categories/subcategories/skills.
        Those are resolved from existing DB master data during skill import.
        
        CRITICAL: Must commit org master data BEFORE employee import starts.
        Reason: Employee import uses per-employee commits, which would commit
        partial org data. We need all org entities (SubSegment/Project/Team/Role)
        fully committed and visible before any employee is processed.
        """
        logger.info("Processing org master data (SubSegment/Project/Team/Role only)...")
        
        # DIAGNOSTIC: Log what we're about to process to help debug "Team not found" errors
        logger.info(f"Master data summary:")
        logger.info(f"  Sub-segments: {len(master_data.get('sub_segments', set()))}")
        logger.info(f"  Projects: {len(master_data.get('sub_segment_project_mappings', set()))}")
        logger.info(f"  Teams: {len(master_data.get('project_team_mappings', set()))}")
        logger.info(f"  Roles: {len(master_data.get('roles', set()))}")
        
        # Log team details for debugging
        if master_data.get('project_team_mappings'):
            logger.debug(f"Team mappings to create: {sorted(master_data['project_team_mappings'])}")

        # Step 1: Process top-level org entities
        self._process_sub_segments(master_data['sub_segments'])
        self._process_roles(master_data['roles'])
        self.db.flush()  # Ensure parent entities exist

        # Step 2: Process second-level org entities with parent validation
        self._process_projects_with_validation(master_data['projects'], master_data['sub_segment_project_mappings'])
        self.db.flush()  # Ensure projects exist
        
        # Step 3: Process third-level org entities with hierarchical validation
        self._process_teams_with_validation(master_data['teams'], master_data['project_team_mappings'])
        self.db.flush()  # Ensure all org master data is flushed to session
        
        # CRITICAL FIX: Commit org master data NOW before employee import
        # Reason: Per-employee commits in _import_employees() need all org entities
        # to be fully committed and queryable. Without this, teams created above
        # may not be visible when employee import queries for them.
        self.db.commit()
        logger.info("Committed org master data (SubSegment/Project/Team/Role)")

        logger.info("Org master data processing completed (skills will be resolved from DB)")
    
    def _process_sub_segments(self, sub_segments: Set[str]):
        """Process Sub-Segment master data."""
        for sub_segment_name in sub_segments:
            if not sub_segment_name or pd.isna(sub_segment_name):
                continue

            existing = self.db.query(SubSegment).filter(
                SubSegment.sub_segment_name == sub_segment_name
            ).first()
            
            if not existing:
                new_sub_segment = SubSegment(sub_segment_name=sub_segment_name, created_by="excel_import")
                self.db.add(new_sub_segment)
                self.import_stats['new_sub_segments'].append(sub_segment_name)
                logger.info(f"Added new sub-segment: {sub_segment_name}")

    def _process_roles(self, roles: Set[str]):
        """Process Role master data."""
        for role_name in roles:
            if not role_name or pd.isna(role_name):
                continue

            existing = self.db.query(Role).filter(
                Role.role_name == role_name
            ).first()

            if not existing:
                new_role = Role(role_name=role_name, created_by="excel_import")
                self.db.add(new_role)
                self.import_stats['new_roles'].append(role_name)
                logger.info(f"Added new role: {role_name}")

    def _process_projects_with_validation(self, projects: Set[str], mappings: Set[Tuple[str, str]]):
        """Process Projects with Sub-Segment validation."""
        logger.info("Processing projects with sub-segment validation...")

        for sub_segment_name, project_name in mappings:
            sub_segment = self.db.query(SubSegment).filter(
                SubSegment.sub_segment_name == sub_segment_name
            ).first()

            if not sub_segment:
                raise ImportServiceError(f"Sub-Segment '{sub_segment_name}' not found for project '{project_name}'")

            existing_project = self.db.query(Project).filter(
                Project.project_name == project_name,
                Project.sub_segment_id == sub_segment.sub_segment_id
            ).first()

            if not existing_project:
                new_project = Project(
                    project_name=project_name,
                    sub_segment_id=sub_segment.sub_segment_id,
                    created_by="excel_import"
                )
                self.db.add(new_project)
                self.import_stats['new_projects'].append(project_name)
                logger.info(f"Added new project: {project_name} under sub-segment: {sub_segment_name}")


    def _process_teams_with_validation(self, teams: Set[str], mappings: Set[Tuple[str, str]]):
        """Process Teams with Project validation."""
        logger.info("Processing teams with project validation...")

        for project_name, team_name in mappings:
            project = self.db.query(Project).filter(
                Project.project_name == project_name
            ).first()

            if not project:
                raise ImportServiceError(f"Project '{project_name}' not found for team '{team_name}'")

            existing_team = self.db.query(Team).filter(
                Team.team_name == team_name,
                Team.project_id == project.project_id
            ).first()

            if not existing_team:
                new_team = Team(
                    team_name=team_name,
                    project_id=project.project_id,
                    created_by="excel_import"
                )
                self.db.add(new_team)
                self.import_stats['new_teams'].append(team_name)
                logger.info(f"Added new team: {team_name} under project: {project_name}")

    def _resolve_skill(self, skill_name: str) -> Optional[int]:
        """
        Resolve skill name to skill_id using DB master data.
        
        Resolution strategy:
            1. Exact match on skills.skill_name (case-insensitive)
            2. Alias match on skill_aliases.alias_text (case-insensitive)
            3. Return None (unresolved)
        
        Args:
            skill_name: Raw skill name from Excel
            
        Returns:
            skill_id if resolved, None otherwise
        """
        from sqlalchemy import func
        
        skill_name_normalized = self._normalize_name(skill_name)
        
        # Step 1: Exact match on skills.skill_name
        skill = self.db.query(Skill).filter(
            func.lower(func.trim(Skill.skill_name)) == skill_name_normalized
        ).first()
        
        if skill:
            logger.debug(f"✓ Resolved '{skill_name}' via exact match → skill_id={skill.skill_id}")
            self.import_stats['skills_resolved_exact'] += 1
            return skill.skill_id
        
        # Step 2: Alias match on skill_aliases.alias_text
        alias = self.db.query(SkillAlias).filter(
            func.lower(func.trim(SkillAlias.alias_text)) == skill_name_normalized
        ).first()
        
        if alias:
            logger.debug(f"✓ Resolved '{skill_name}' via alias match → skill_id={alias.skill_id}")
            self.import_stats['skills_resolved_alias'] += 1
            return alias.skill_id
          # Step 3: Unresolved
        logger.warning(f"✗ Could not resolve skill: '{skill_name}'")
        self.import_stats['skills_unresolved'] += 1
        if skill_name not in self.import_stats['unresolved_skill_names']:
            self.import_stats['unresolved_skill_names'].append(skill_name)
        return None

    def _record_unresolved_skill(self, skill_name: str, employee_id: int,
                                  sub_segment_id: int, timestamp: datetime):
        """
        Log unresolved skill to raw_skill_inputs table for manual review.
        
        Args:
            skill_name: Unresolved skill name from Excel
            employee_id: Employee who has this skill
            sub_segment_id: Employee's sub-segment (for context)
            timestamp: Import timestamp
        """
        try:
            # FIX: Use correct field names for RawSkillInput model
            raw_input = RawSkillInput(
                raw_text=skill_name,  # Original text from Excel
                normalized_text=self._normalize_name(skill_name),  # Normalized version
                sub_segment_id=sub_segment_id,
                source_type="excel_import",  # Source identifier
                employee_id=employee_id,
                resolved_skill_id=None,  # Not resolved yet
                resolution_method=None,
                resolution_confidence=None,
                created_at=timestamp
            )
            self.db.add(raw_input)
            logger.info(f"📝 Logged unresolved skill '{skill_name}' to raw_skill_inputs")
            
            # Also log to text file for easy review
            self._log_unresolved_skill_to_file(skill_name, employee_id, sub_segment_id, timestamp)
            
        except Exception as e:
            logger.error(f"Failed to log unresolved skill '{skill_name}': {e}")

    def _log_unresolved_skill_to_file(self, skill_name: str, employee_id: int,
                                       sub_segment_id: int, timestamp: datetime):
        """
        Log unresolved skill to a text file in backend folder for easy review.
        
        Args:
            skill_name: Unresolved skill name from Excel
            employee_id: Employee who has this skill
            sub_segment_id: Employee's sub-segment (for context)
            timestamp: Import timestamp
        """
        try:
            # Get backend folder path (parent of app folder)
            backend_folder = Path(__file__).parent.parent.parent
            log_file = backend_folder / "unresolved_skills.txt"
            
            # Get employee info for better context
            employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
            employee_name = f"{employee.first_name} {employee.last_name}" if employee else f"ID:{employee_id}"
            employee_zid = employee.zid if employee else "Unknown"
            
            # Get sub-segment info
            sub_segment = self.db.query(SubSegment).filter(SubSegment.id == sub_segment_id).first()
            sub_segment_name = sub_segment.name if sub_segment else f"ID:{sub_segment_id}"
            
            # Format log entry
            log_entry = (
                f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"UNRESOLVED: \"{skill_name}\" | "
                f"Employee: {employee_name} ({employee_zid}) | "
                f"Sub-Segment: {sub_segment_name}\n"
            )
            
            # Append to file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            logger.debug(f"Logged unresolved skill to {log_file}")
            
        except Exception as e:
            # Don't fail the import if file logging fails
            logger.warning(f"Failed to log unresolved skill to file: {e}")

    def _import_employee_skills_with_resolution(self, skills_df: pd.DataFrame, 
                                                 zid_to_employee_id_mapping: Dict[str, int], 
                                                 import_timestamp: datetime) -> int:
        """
        Import employee skills with NEW FORMAT resolution logic.
        
        Resolution Flow:
            1. For each skill row, resolve skill_name via _resolve_skill()
            2. If resolved: Create EmployeeSkill + SkillHistory records
            3. If unresolved: Log to raw_skill_inputs table
        
        Transaction Strategy:
            - Skills grouped by employee (ZID)
            - Each employee's skills committed as a batch
            - Failures don't affect other employees
        
        Args:
            skills_df: DataFrame with columns: zid, skill_name, proficiency, interest_level, etc.
            zid_to_employee_id_mapping: Map of ZID → employee_id
            import_timestamp: Import timestamp (UTC timezone-aware)
            
        Returns:
            Total number of skill rows processed        """
        logger.info(f"Importing {len(skills_df)} employee skill records (NEW FORMAT with resolution)")
        
        # FIX: Expand comma-separated skills BEFORE processing (same as old importer)
        # Excel can have "PostgreSQL, SQL Server" -> split into 2 rows
        expanded_rows = []
        for idx, row in skills_df.iterrows():
            skill_name_raw = str(row.get('skill_name', '')).strip()
            
            # Split on comma or semicolon
            if ',' in skill_name_raw or ';' in skill_name_raw:
                # Split and clean each skill
                skill_names = [s.strip() for s in skill_name_raw.replace(';', ',').split(',')]
                skill_names = [s for s in skill_names if s]  # Remove empty
                
                # Create a row for each skill (copy all other columns)
                for skill_name in skill_names:
                    row_copy = row.copy()
                    row_copy['skill_name'] = skill_name
                    expanded_rows.append(row_copy)
            else:
                expanded_rows.append(row)
        
        # Replace original dataframe with expanded one
        if len(expanded_rows) > len(skills_df):
            skills_df = pd.DataFrame(expanded_rows)
            logger.info(f"📊 Expanded {len(expanded_rows) - len(skills_df)} comma-separated skills → total {len(skills_df)} skill rows")
        
        # Create ZID to employee name mapping for error reporting
        zid_to_name_mapping = {}
        zid_to_subsegment_mapping = {}
        for zid, emp_id in zid_to_employee_id_mapping.items():
            employee = self.db.query(Employee).filter(Employee.employee_id == emp_id).first()
            if employee:
                zid_to_name_mapping[zid] = employee.full_name
                zid_to_subsegment_mapping[zid] = employee.sub_segment_id
        
        # Initialize history service
        history_service = SkillHistoryService(self.db)
        successful_skill_imports = 0
        
        # Group skills by ZID for per-employee processing
        skills_by_zid = {}
        for row_idx, row in skills_df.iterrows():
            zid = str(row.get('zid', ''))
            excel_row = row_idx + 2  # Excel row number (1-based + header)
            if zid not in skills_by_zid:
                skills_by_zid[zid] = []
            skills_by_zid[zid].append((excel_row, row))
        
        # Process each employee's skills as a batch
        for zid, skill_rows in skills_by_zid.items():
            db_employee_id = zid_to_employee_id_mapping.get(zid)
            employee_name = zid_to_name_mapping.get(zid, None)
            sub_segment_id = zid_to_subsegment_mapping.get(zid, None)
            
            if not db_employee_id:
                # Employee was not imported (failed earlier), skip all their skills
                logger.warning(f"Skipping {len(skill_rows)} skills for ZID {zid}: Employee was not imported")
                for excel_row, row in skill_rows:
                    self.import_stats['failed_rows'].append({
                        'sheet': 'Employee_Skills',
                        'excel_row_number': excel_row,
                        'row_number': excel_row,
                        'zid': zid,
                        'employee_name': employee_name or str(row.get('employee_full_name', '')),
                        'skill_name': str(row.get('skill_name', '')),
                        'error_code': 'EMPLOYEE_NOT_IMPORTED',
                        'message': f'Employee ZID {zid} was not successfully imported'
                    })
                continue
              # Process all skills for this employee in one batch
            employee_skill_records = []
            
            for excel_row, row in skill_rows:
                # DEFENSIVE: Ensure skill_name is a clean string (not pandas Series or other type)
                skill_name_raw = row.get('skill_name', '')
                
                # Handle edge case where pandas might return a Series instead of scalar
                if isinstance(skill_name_raw, pd.Series):
                    skill_name = str(skill_name_raw.iloc[0]).strip() if len(skill_name_raw) > 0 else ''
                else:
                    skill_name = str(skill_name_raw).strip()
                
                if not skill_name:
                    logger.warning(f"Skipping empty skill name at Excel row {excel_row}")
                    continue
                
                try:
                    # NEW: Resolve skill via exact match → alias match → None
                    skill_id = self._resolve_skill(skill_name)
                    
                    if not skill_id:
                        # Unresolved skill - log to raw_skill_inputs
                        self._record_unresolved_skill(
                            skill_name=skill_name,
                            employee_id=db_employee_id,
                            sub_segment_id=sub_segment_id,
                            timestamp=import_timestamp
                        )
                        logger.warning(f"Skill '{skill_name}' unresolved for ZID {zid} - logged to raw_skill_inputs")
                        
                        # Track as failed row for reporting
                        self.import_stats['failed_rows'].append({
                            'sheet': 'Employee_Skills',
                            'excel_row_number': excel_row,
                            'row_number': excel_row,
                            'zid': zid,
                            'employee_name': employee_name,
                            'skill_name': skill_name,
                            'error_code': 'SKILL_NOT_RESOLVED',
                            'message': f'Skill "{skill_name}" not found in master data (logged to raw_skill_inputs)'
                        })
                        continue
                    
                    # Get proficiency level ID
                    proficiency_name = str(row.get('proficiency', '')).strip()
                    proficiency = self.db.query(ProficiencyLevel).filter(
                        ProficiencyLevel.level_name == proficiency_name
                    ).first()
                    
                    if not proficiency:
                        raise ImportServiceError(f"Proficiency level not found: {proficiency_name}")
                    
                    # Process date fields using safe parsing
                    last_used = self._parse_date_safely(
                        row.get('last_used'),
                        'last_used',
                        f"employee {zid}"
                    )
                    
                    started_learning_from = self._parse_date_safely(
                        row.get('started_learning_from'),
                        'started_learning_from',
                        f"employee {zid}"
                    )
                    
                    # Sanitize numeric fields
                    years_experience = self._sanitize_integer_field(row.get('years_experience'), 'years_experience', zid)
                    interest_level = self._sanitize_integer_field(row.get('interest_level'), 'interest_level', zid)
                    
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
                    
                    employee_skill_records.append(employee_skill)
                    successful_skill_imports += 1
                    
                except Exception as e:
                    # Log the error but don't fail the entire employee batch yet
                    error_message = str(e)
                    logger.warning(f"Failed to prepare skill at Excel row {excel_row} (ZID: {zid}, Skill: {skill_name}): {error_message}")
                    
                    # Determine error code
                    error_code = "SKILL_IMPORT_ERROR"
                    if "not found" in error_message.lower():
                        error_code = "MISSING_REFERENCE"
                    elif "proficiency" in error_message.lower():
                        error_code = "INVALID_PROFICIENCY"
                    elif "duplicate" in error_message.lower():
                        error_code = "DUPLICATE_SKILL"
                    elif "constraint" in error_message.lower():
                        error_code = "CONSTRAINT_VIOLATION"
                    
                    # Track failed skill row with full context
                    self.import_stats['failed_rows'].append({
                        'sheet': 'Employee_Skills',
                        'excel_row_number': excel_row,
                        'row_number': excel_row,
                        'zid': zid,
                        'employee_name': employee_name,
                        'skill_name': skill_name,
                        'error_code': error_code,
                        'message': error_message
                    })
                    continue
            
            # CRITICAL: Commit all skills for this employee as a batch
            try:
                if employee_skill_records:
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
                    
            except Exception as e:
                # If commit fails, rollback this employee's skills only
                error_message = str(e)
                logger.error(f"Failed to commit skills for employee ZID {zid}: {error_message}")
                self.db.rollback()
                
                # Mark all this employee's skills as failed
                for skill_record in employee_skill_records:
                    self.import_stats['failed_rows'].append({
                        'sheet': 'Employee_Skills',
                        'excel_row_number': None,
                        'row_number': None,
                        'zid': zid,                        'employee_name': employee_name,
                        'skill_name': None,
                        'error_code': 'BATCH_COMMIT_FAILED',
                        'message': f'Failed to commit skill batch for ZID {zid}: {error_message}'
                    })
                successful_skill_imports -= len(employee_skill_records)
                continue
        
        self.import_stats['skills_imported'] = successful_skill_imports
        
        # DEBUG: Log resolution stats
        logger.info(f"Imported {successful_skill_imports} of {len(skills_df)} employee skill records")
        logger.info(f"📊 Resolution stats: exact={self.import_stats['skills_resolved_exact']}, "
                   f"alias={self.import_stats['skills_resolved_alias']}, "
                   f"unresolved={self.import_stats['skills_unresolved']}")
        
        return len(skills_df)  # Return total rows processed

    def _import_employees(self, employees_df: pd.DataFrame, import_timestamp: datetime) -> Dict[str, int]:
        """Import employees with per-employee transaction scope for partial success.
        Each employee is committed independently so failures don't affect others."""
        logger.info(f"Importing {len(employees_df)} employees (per-employee transactions)")

        zid_to_employee_id_mapping = {}
        successful_imports = 0
        failed_employees = []

        for row_idx, row in employees_df.iterrows():
            row_number = row_idx + 2  # Excel row number (accounting for header)
            zid = str(row.get('zid', ''))
            full_name = str(row.get('full_name', ''))

            try:
                # Get foreign key IDs - master data should exist from hierarchical processing
                sub_segment = self.db.query(SubSegment).filter(
                    SubSegment.sub_segment_name == row['sub_segment']
                ).first()

                if not sub_segment:
                    raise ImportServiceError(f"Sub-segment not found: {row['sub_segment']}")

                project = self.db.query(Project).filter(
                    Project.project_name == row['project'],
                    Project.sub_segment_id == sub_segment.sub_segment_id
                ).first()

                if not project:
                    raise ImportServiceError(f"Project not found: {row['project']} under sub-segment: {row['sub_segment']}")

                team = self.db.query(Team).filter(
                    Team.team_name == row['team'],
                    Team.project_id == project.project_id
                ).first()

                if not team:
                    raise ImportServiceError(f"Team not found: {row['team']} under project: {row['project']}")

                # Lookup role by name (optional)
                role = None
                if row.get('role'):
                    role = self.db.query(Role).filter(Role.role_name == row['role']).first()

                # Convert start_date_of_working using safe parsing
                start_date = self._parse_date_safely(
                    row.get('start_date_of_working'), 
                    'start_date_of_working', 
                    zid
                )

                # Parse email column (case-insensitive, optional)
                email = None
                email_raw = row.get('email') or row.get('Email')
                if email_raw and not pd.isna(email_raw):
                    email = str(email_raw).strip()
                    if email == '':
                        email = None

                # Create employee with explicit created_at timestamp
                employee = Employee(
                    zid=zid,
                    full_name=full_name,
                    sub_segment_id=sub_segment.sub_segment_id,
                    project_id=project.project_id,
                    team_id=team.team_id,
                    role_id=role.role_id if role else None,
                    start_date_of_working=start_date,
                    email=email,
                    created_at=import_timestamp
                )

                self.db.add(employee)
                self.db.flush()  # Get the auto-generated ID

                # CRITICAL: Commit this employee immediately (per-employee transaction)
                self.db.commit()

                zid_to_employee_id_mapping[zid] = employee.employee_id
                successful_imports += 1
                logger.debug(f"Committed employee {zid} (ID: {employee.employee_id})")

            except Exception as e:
                # Log the error and continue with next row
                error_message = str(e)
                logger.warning(f"Failed to import employee at row {row_number} (ZID: {zid}, Name: {full_name}): {error_message}")
                    # Determine error code
                error_code = "IMPORT_ERROR"
                if "not found" in error_message.lower():
                    error_code = "MISSING_REFERENCE"
                elif "duplicate" in error_message.lower():
                    error_code = "DUPLICATE_ENTRY"
                elif "constraint" in error_message.lower():
                    error_code = "CONSTRAINT_VIOLATION"

                # Track failed employee
                failed_employee = {
                    'sheet': 'Employee',
                    'excel_row_number': row_number,
                    'row_number': row_number,  # Legacy field
                    'zid': zid if zid else None,
                    'full_name': full_name if full_name else None,
                    'employee_name': full_name if full_name else None,  # For consistency
                    'skill_name': None,  # Not applicable for employee rows
                    'error_code': error_code,
                    'message': error_message
                }
                failed_employees.append(failed_employee)
                self.import_stats['failed_rows'].append(failed_employee)

                # Rollback ONLY this employee (won't affect previous commits)
                self.db.rollback()
                continue

        self.import_stats['employees_imported'] = successful_imports
        self.import_stats['failed_employees'] = failed_employees
        logger.info(f"Imported {successful_imports} of {len(employees_df)} employees (failed: {len(failed_employees)})")

        return zid_to_employee_id_mapping



    def _sanitize_integer_field(self, value: Any, field_name: str, zid: str) -> Optional[int]:
        """Sanitize integer fields - convert pandas NaN to None for PostgreSQL."""
        if pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid {field_name} value '{value}' for employee {zid}, setting to None")
            return None
