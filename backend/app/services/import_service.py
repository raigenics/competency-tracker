"""
Import service for the Competency Tracking System.
Handles Excel data import with hierarchical master data processing and PostgreSQL compatibility.
"""
import logging
import pandas as pd
import uuid
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
            'new_skill_categories': [],
            'new_skill_subcategories': [],
            'new_skills': [],
            'new_roles': [],
            'hierarchical_validations': [],
            'failed_rows': []
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
                except ValueError:
                    pass
                    
                logger.warning(f"Could not parse {field_name} '{date_str}' for record {record_id}")
                return None
                
        except Exception as e:
            logger.warning(f"Date conversion error for {field_name} '{date_str}' in record {record_id}: {e}")
            return None

    @staticmethod
    def _normalize_name(name: str) -> str:
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
    
    @staticmethod
    def _normalize_subcategory_name(name: str) -> str:
        """
        Normalize subcategory name for case-insensitive comparison.
        Wrapper for _normalize_name() for backward compatibility.
        
        Args:
            name: Raw subcategory name from Excel
            
        Returns:
            Normalized name (trimmed, collapsed spaces, lowercased)
        """
        return ImportService._normalize_name(name)

    def import_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Import Excel file data with hierarchical master data processing.
        Enhanced for PostgreSQL compatibility.
        
        Args:
            file_path (str): Path to the Excel file
            
        Returns:
            Dict with import statistics
            
        Raises:
            ImportServiceError: If import fails
        """
        logger.info(f"Starting Excel import with PostgreSQL compatibility from: {file_path}")
        
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
        
        try:            # Step 1: Read and validate Excel data
            employees_df, skills_df = self._read_and_validate_excel(file_path)
            
            # Step 2: Generate import timestamp (UTC timezone-aware) for created_at fields
            import_timestamp = datetime.now(timezone.utc)
            logger.info(f"Import timestamp: {import_timestamp.isoformat()}")
            
            # Step 3: Scan Excel data for all master data (Step 1 of 2-step approach)
            master_data = get_master_data_for_scanning(employees_df, skills_df)
            
            # Step 4: Clear fact tables (employees and employee_skills)
            self._clear_fact_tables()
            
            # Step 5: Process hierarchical master data (Step 2 of 2-step approach)
            self._process_hierarchical_master_data(master_data)
              # Step 6: Import employees with proper ZID handling
            zid_to_employee_id_mapping = self._import_employees(employees_df, import_timestamp)
            
            # Step 7: Import employee skills (stores expanded count in import_stats)
            expanded_skill_count = self._import_employee_skills(skills_df, zid_to_employee_id_mapping, import_timestamp)
              # Step 7: Ensure all changes are flushed and committed
            self.db.flush()
            self.db.commit()
            
            logger.info("Excel import completed successfully with PostgreSQL")
            
            # Determine status based on failures
            total_employee_rows = len(employees_df)
            total_skill_rows_original = len(skills_df)
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
                'skill_original_total': total_skill_rows_original,
                'skill_imported': skill_imported,
                'skill_failed': failed_skill_count,
                # Legacy fields for backward compatibility
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

    def _read_and_validate_excel(self, file_path: str) -> tuple:
        """Read and validate Excel file data."""
        logger.info("Reading and validating Excel data")
        
        try:
            employees_df, skills_df = read_excel(file_path)
            
            # Additional business validations
            self._validate_business_rules(employees_df, skills_df)
            
            return employees_df, skills_df
            
        except ExcelReaderError as e:
            raise ImportServiceError(f"Excel validation failed: {str(e)}")

    def _validate_business_rules(self, employees_df: pd.DataFrame, skills_df: pd.DataFrame):
        """Validate business rules between employees and skills data."""
        logger.info("Validating business rules")
        
        # Check that all ZIDs in skills exist in employees
        employee_zids = set(employees_df['zid'].astype(str).unique())
        skill_employee_zids = set(skills_df['zid'].astype(str).unique())
        
        missing_employees = skill_employee_zids - employee_zids
        if missing_employees:
            raise ImportServiceError(
                f"Skills data contains ZIDs not found in employees data: {missing_employees}"
            )
        
        # Check for duplicate ZIDs
        duplicate_employees = employees_df[employees_df.duplicated(['zid'], keep=False)]
        if not duplicate_employees.empty:
            raise ImportServiceError(f"Duplicate ZIDs found: {duplicate_employees['zid'].tolist()}")
        
        # Validate proficiency levels exist (Dreyfus Model)
        expected_proficiency = ['Novice', 'Advanced Beginner', 'Competent', 'Proficient', 'Expert']
        invalid_proficiency = skills_df[~skills_df['proficiency'].isin(expected_proficiency)]
        if not invalid_proficiency.empty:
            invalid_values = invalid_proficiency['proficiency'].unique()
            raise ImportServiceError(f"Invalid proficiency levels found: {invalid_values}. Valid levels are: {expected_proficiency}")

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

    def _process_hierarchical_master_data(self, master_data: Dict[str, Set]):
        """Process hierarchical master data with proper validation."""
        logger.info("Processing hierarchical master data...")
        
        # Step 1: Process top-level entities
        self._process_sub_segments(master_data['sub_segments'])
        self._process_skill_categories(master_data['skill_categories'])
        self._process_roles(master_data['roles'])
        self.db.flush()  # Ensure parent entities exist
        
        # Step 2: Process second-level entities with parent validation
        self._process_projects_with_validation(master_data['projects'], master_data['sub_segment_project_mappings'])
        self._process_skill_subcategories_with_validation(
            master_data['skill_subcategories'], 
            master_data['category_subcategory_mappings']
        )
        self.db.flush()  # Ensure second-level entities exist
          # Step 3: Process third-level entities with hierarchical validation
        self._process_teams_with_validation(master_data['teams'], master_data['project_team_mappings'])
        self._process_skills_with_validation(
            master_data['skills'], 
            master_data['subcategory_skill_mappings']
        )
        self.db.flush()  # Ensure all master data is committed to session
        
        logger.info("Hierarchical master data processing completed")

    def _process_sub_segments(self, sub_segments: Set[str]):
        """Process Sub-Segment master data."""
        for sub_segment_name in sub_segments:
            if not sub_segment_name or pd.isna(sub_segment_name):
                continue
            
            existing = self.db.query(SubSegment).filter(
                SubSegment.sub_segment_name == sub_segment_name
            ).first()
            
            if not existing:
                new_sub_segment = SubSegment(sub_segment_name=sub_segment_name)
                self.db.add(new_sub_segment)
                self.import_stats['new_sub_segments'].append(sub_segment_name)
                logger.info(f"Added new sub-segment: {sub_segment_name}")

    def _process_skill_categories(self, categories: Set[str]):
        """Process Skill Category master data."""
        for category_name in categories:
            if not category_name or pd.isna(category_name):
                continue
            
            existing = self.db.query(SkillCategory).filter(
                SkillCategory.category_name == category_name
            ).first()
            
            if not existing:
                new_category = SkillCategory(category_name=category_name)
                self.db.add(new_category)
                self.import_stats['new_skill_categories'].append(category_name)
                logger.info(f"Added new skill category: {category_name}")

    def _process_roles(self, roles: Set[str]):
        """Process Role master data."""
        for role_name in roles:
            if not role_name or pd.isna(role_name):
                continue
            
            existing = self.db.query(Role).filter(
                Role.role_name == role_name
            ).first()
            
            if not existing:
                new_role = Role(role_name=role_name)
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
                    sub_segment_id=sub_segment.sub_segment_id
                )
                self.db.add(new_project)
                self.import_stats['new_projects'].append(project_name)
                logger.info(f"Added new project: {project_name} under sub-segment: {sub_segment_name}")

    def _process_skill_subcategories_with_validation(self, subcategories: Set[str], mappings: Set[Tuple[str, str]]):
        """Process Skill Subcategories with Category validation."""
        logger.info("Processing subcategories with category validation...")
        
        # Track seen subcategories to deduplicate case/space variants
        seen_subcategories = {}  # (category_id, normalized_name) -> display_name
        
        for category_name, subcategory_name in mappings:
            category = self.db.query(SkillCategory).filter(
                SkillCategory.category_name == category_name
            ).first()
            
            if not category:
                raise ImportServiceError(f"Category '{category_name}' not found for subcategory '{subcategory_name}'")
            
            # Normalize for deduplication
            subcategory_normalized = self._normalize_subcategory_name(subcategory_name)
            dedupe_key = (category.category_id, subcategory_normalized)
            
            # Skip if we've already seen this normalized subcategory
            if dedupe_key in seen_subcategories:
                logger.debug(f"Skipping duplicate subcategory '{subcategory_name}' (normalized form already seen as '{seen_subcategories[dedupe_key]}')")
                continue
            
            seen_subcategories[dedupe_key] = subcategory_name.strip()
              # Use case-insensitive query to check database
            from sqlalchemy import func
            existing_subcategory = self.db.query(SkillSubcategory).filter(
                func.lower(func.trim(SkillSubcategory.subcategory_name)) == subcategory_normalized,
                SkillSubcategory.category_id == category.category_id
            ).first()
            
            if not existing_subcategory:
                new_subcategory = SkillSubcategory(
                    subcategory_name=subcategory_name.strip(),
                    category_id=category.category_id
                )
                self.db.add(new_subcategory)
                self.import_stats['new_skill_subcategories'].append(subcategory_name.strip())
                logger.info(f"Added new subcategory: {subcategory_name.strip()} under category: {category_name}")

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
                    project_id=project.project_id
                )
                self.db.add(new_team)
                self.import_stats['new_teams'].append(team_name)
                logger.info(f"Added new team: {team_name} under project: {project_name}")

    def _process_skills_with_validation(self, skills: Set[str], mappings: Set[Tuple[str, str, str]]):
        """
        Process Skills with Subcategory validation.
        
        Args:
            skills: Set of skill names
            mappings: Set of (category_name, subcategory_name, skill_name) triplets
                     Category is included to prevent subcategory name collisions across different categories
        """
        logger.info("Processing skills with subcategory validation...")
        
        # Track seen skills to deduplicate case/space variants
        seen_skills = {}  # (subcategory_id, normalized_skill_name) -> display_name
        
        for category_name, subcategory_name, skill_name in mappings:            
            # Normalize names            
            category_name = category_name.strip() if category_name else category_name
            subcategory_name = subcategory_name.strip() if subcategory_name else subcategory_name
            skill_name = skill_name.strip() if skill_name else skill_name
            
            # Lookup subcategory using BOTH category_id and subcategory_name to prevent collisions
            # (e.g., "Frameworks" can exist under both "Web Development" and "Desktop Development")
            category = self.db.query(SkillCategory).filter(
                SkillCategory.category_name == category_name
            ).first()
            
            if not category:
                raise ImportServiceError(f"Category '{category_name}' not found for subcategory '{subcategory_name}'")
            
            # Normalize subcategory name for case-insensitive lookup
            subcategory_normalized = self._normalize_subcategory_name(subcategory_name)
              # Use case-insensitive query to find subcategory
            from sqlalchemy import func
            subcategory = self.db.query(SkillSubcategory).filter(
                SkillSubcategory.category_id == category.category_id,  # ← Added to fix collision bug
                func.lower(func.trim(SkillSubcategory.subcategory_name)) == subcategory_normalized
            ).first()
            
            if not subcategory:
                raise ImportServiceError(f"Subcategory '{subcategory_name}' not found under category '{category_name}' for skill '{skill_name}'")
            
            # Normalize skill name for deduplication
            skill_normalized = self._normalize_name(skill_name)
            dedupe_key = (subcategory.subcategory_id, skill_normalized)
            
            # Skip if we've already seen this normalized skill
            if dedupe_key in seen_skills:
                logger.debug(f"Skipping duplicate skill '{skill_name}' (normalized form already seen as '{seen_skills[dedupe_key]}')")
                continue
            
            seen_skills[dedupe_key] = skill_name
            
            # Use case-insensitive query to check database
            existing_skill = self.db.query(Skill).filter(
                func.lower(func.trim(Skill.skill_name)) == skill_normalized,
                Skill.subcategory_id == subcategory.subcategory_id
            ).first()
            
            if not existing_skill:
                new_skill = Skill(
                    skill_name=skill_name,
                    subcategory_id=subcategory.subcategory_id
                )
                self.db.add(new_skill)
                self.import_stats['new_skills'].append(skill_name)
                logger.info(f"Added new skill: {skill_name} under subcategory: {subcategory_name} (category: {category_name})")
    
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
    
    def _import_employee_skills(self, skills_df: pd.DataFrame, zid_to_employee_id_mapping: Dict[str, int], import_timestamp: datetime) -> int:
        """Import employee skills with per-employee transaction batches.
        Skills are grouped by employee and committed together to ensure atomicity.
        Handles comma-separated skills in a single cell by splitting them.
        
        Returns:
            Number of expanded skill rows (after comma splitting)
        """
        logger.info(f"Importing {len(skills_df)} employee skill records (per-employee batches)")
        
        # Expand comma-separated skills BEFORE processing
        expanded_skills_df = self._expand_comma_separated_skills(skills_df)
        expanded_count = len(expanded_skills_df)
        logger.info(f"Expanded to {expanded_count} individual skill entries after splitting comma-separated values")
          # Create a ZID to employee name mapping for error reporting
        zid_to_name_mapping = {}
        for zid, emp_id in zid_to_employee_id_mapping.items():
            employee = self.db.query(Employee).filter(Employee.employee_id == emp_id).first()
            if employee:
                zid_to_name_mapping[zid] = employee.full_name
        
        # Initialize history service
        history_service = SkillHistoryService(self.db)
        successful_skill_imports = 0
        
        # Group skills by ZID for per-employee processing
        skills_by_zid = {}
        for row_idx, row in expanded_skills_df.iterrows():
            zid = str(row.get('zid', ''))
            excel_row = row_idx + 2  # Excel row number (1-based + header)
            if zid not in skills_by_zid:
                skills_by_zid[zid] = []
            skills_by_zid[zid].append((excel_row, row))  # (excel_row_number, row_data)
        
        # Process each employee's skills as a batch
        for zid, skill_rows in skills_by_zid.items():
            db_employee_id = zid_to_employee_id_mapping.get(zid)
            employee_name = zid_to_name_mapping.get(zid, None)
            
            if not db_employee_id:
                # Employee was not imported (failed earlier), skip all their skills
                logger.warning(f"Skipping {len(skill_rows)} skills for ZID {zid}: Employee was not imported")
                for excel_row, row in skill_rows:
                    self.import_stats['failed_rows'].append({
                        'sheet': 'Employee_Skills',
                        'excel_row_number': excel_row,
                        'row_number': excel_row,  # Legacy field
                        'zid': zid,
                        'employee_name': employee_name or row.get('employee_full_name'),
                        'skill_name': str(row.get('skill_name', '')),
                        'category': row.get('skill_category'),
                        'subcategory': row.get('skill_subcategory'),
                        'error_code': 'EMPLOYEE_NOT_IMPORTED',
                        'message': f'Employee ZID {zid} was not successfully imported'
                    })
                continue
            
            # Process all skills for this employee in one batch
            employee_skill_records = []
            
            for excel_row, row in skill_rows:
                skill_name = str(row.get('skill_name', ''))
                
                try:
                    # Get or create skill (defensive programming)
                    skill = self._get_or_create_skill(row)
                    
                    if not skill:
                        raise ImportServiceError(f"Could not resolve skill: {skill_name}")
                    
                    # Get proficiency level ID
                    proficiency = self.db.query(ProficiencyLevel).filter(
                        ProficiencyLevel.level_name == row['proficiency']
                    ).first()
                    
                    if not proficiency:
                        raise ImportServiceError(f"Proficiency level not found: {row['proficiency']}")
                    
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
                        skill_id=skill.skill_id,
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
                        'row_number': excel_row,  # Legacy field
                        'zid': zid,
                        'employee_name': employee_name or row.get('employee_full_name'),
                        'skill_name': skill_name,
                        'category': row.get('skill_category'),
                        'subcategory': row.get('skill_subcategory'),
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
                            change_reason="Excel bulk import",
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
                        'excel_row_number': None,  # Not tied to specific row
                        'row_number': None,
                        'zid': zid,
                        'employee_name': employee_name,
                        'skill_name': None,
                        'category': None,
                        'subcategory': None,
                        'error_code': 'BATCH_COMMIT_FAILED',
                        'message': f'Failed to commit skill batch for ZID {zid}: {error_message}'
                    })
                successful_skill_imports -= len(employee_skill_records)
                continue
        
        self.import_stats['skills_imported'] = successful_skill_imports
        logger.info(f"Imported {successful_skill_imports} of {expanded_count} employee skill records")
        
        return expanded_count  # Return expanded count for statistics
    
    def _expand_comma_separated_skills(self, skills_df: pd.DataFrame) -> pd.DataFrame:
        """
        Expand comma-separated skills in a single cell into multiple rows.
        
        Example:
            Input row: skill_name="Git, VSCode, Tmux"
            Output: 3 rows with skill_name="Git", "VSCode", "Tmux"
        
        All other fields (category, subcategory, proficiency, etc.) are duplicated for each split skill.
        
        Args:
            skills_df: Original skills DataFrame
            
        Returns:
            Expanded DataFrame with one row per individual skill
        """
        expanded_rows = []
        
        for idx, row in skills_df.iterrows():
            skill_name_raw = str(row.get('skill_name', '')).strip()
            
            # Check if skill_name contains comma (indicates multiple skills)
            if ',' in skill_name_raw:
                # Split by comma and process each skill
                individual_skills = [s.strip() for s in skill_name_raw.split(',')]
                
                # Filter out empty strings
                individual_skills = [s for s in individual_skills if s]
                
                logger.debug(f"Splitting skill '{skill_name_raw}' into {len(individual_skills)} individual skills")
                
                # Create a copy of the row for each individual skill
                for skill_name in individual_skills:
                    row_copy = row.copy()
                    row_copy['skill_name'] = skill_name
                    expanded_rows.append(row_copy)
            else:
                # Single skill - keep as is
                expanded_rows.append(row)
        
        # Create new DataFrame from expanded rows
        if expanded_rows:            return pd.DataFrame(expanded_rows).reset_index(drop=True)
        else:
            return skills_df
    
    def _get_or_create_skill(self, row: pd.Series) -> Optional[Skill]:
        """Get existing skill or create it if missing (defensive programming)."""
        skill_name = str(row.get('skill_name', ''))
        category_name = row.get('skill_category')
        subcategory_name = row.get('skill_subcategory')
        
        if not category_name or not subcategory_name:
            raise ImportServiceError(f"Cannot resolve skill '{skill_name}': Missing category or subcategory")
        
        # Get category
        category = self.db.query(SkillCategory).filter(
            SkillCategory.category_name == category_name
        ).first()
        
        if not category:
            # Create missing category
            category = SkillCategory(category_name=category_name)
            self.db.add(category)
            self.db.flush()
            self.import_stats['new_skill_categories'].append(category_name)
            logger.info(f"Created missing category: {category_name}")
        
        # Normalize subcategory name for case-insensitive lookup
        subcategory_normalized = self._normalize_subcategory_name(subcategory_name)
        
        # Get or create subcategory using case-insensitive query
        from sqlalchemy import func
        subcategory = self.db.query(SkillSubcategory).filter(
            SkillSubcategory.category_id == category.category_id,
            func.lower(func.trim(SkillSubcategory.subcategory_name)) == subcategory_normalized
        ).first()
        
        if not subcategory:
            subcategory = SkillSubcategory(
                subcategory_name=subcategory_name.strip(),
                category_id=category.category_id
            )
            self.db.add(subcategory)
            self.db.flush()
            self.import_stats['new_skill_subcategories'].append(subcategory_name.strip())
            logger.info(f"Created missing subcategory: {subcategory_name.strip()}")
        
        # Normalize skill name for case-insensitive lookup
        skill_normalized = self._normalize_name(skill_name)
        
        # Try to find existing skill using case-insensitive query
        skill = self.db.query(Skill).filter(
            func.lower(func.trim(Skill.skill_name)) == skill_normalized,
            Skill.subcategory_id == subcategory.subcategory_id
        ).first()
        
        if skill:
            return skill
        
        # Skill not found - create it
        logger.warning(f"Skill '{skill_name}' not found, creating it")
        skill = Skill(
            skill_name=skill_name.strip(),
            subcategory_id=subcategory.subcategory_id
        )
        self.db.add(skill)
        self.db.flush()
        self.import_stats['new_skills'].append(skill_name.strip())
        logger.info(f"Created missing skill: {skill_name.strip()}")
        
        return skill
    
    def _sanitize_integer_field(self, value: Any, field_name: str, zid: str) -> Optional[int]:
        """Sanitize integer fields - convert pandas NaN to None for PostgreSQL."""
        if pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid {field_name} value '{value}' for employee {zid}, setting to None")
            return None
