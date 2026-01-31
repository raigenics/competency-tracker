"""
Import service for the Competency Tracking System.
Handles Excel data import with hierarchical master data processing and PostgreSQL compatibility.
"""
import logging
import pandas as pd
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
            'hierarchical_validations': []
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
                '%Y/%m/%d',      # 2011/02/02
                '%d-%b-%y',      # 1-Sep-25
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
            
            # Step 7: Import employee skills
            self._import_employee_skills(skills_df, zid_to_employee_id_mapping, import_timestamp)
            
            # Step 7: Ensure all changes are flushed and committed
            self.db.flush()
            self.db.commit()
            
            logger.info("Excel import completed successfully with PostgreSQL")
            
            return {
                'status': 'success',
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
        
        for category_name, subcategory_name in mappings:
            category = self.db.query(SkillCategory).filter(
                SkillCategory.category_name == category_name
            ).first()
            
            if not category:
                raise ImportServiceError(f"Category '{category_name}' not found for subcategory '{subcategory_name}'")
            
            existing_subcategory = self.db.query(SkillSubcategory).filter(
                SkillSubcategory.subcategory_name == subcategory_name,
                SkillSubcategory.category_id == category.category_id
            ).first()
            
            if not existing_subcategory:
                new_subcategory = SkillSubcategory(
                    subcategory_name=subcategory_name,
                    category_id=category.category_id
                )
                self.db.add(new_subcategory)
                self.import_stats['new_skill_subcategories'].append(subcategory_name)
                logger.info(f"Added new subcategory: {subcategory_name} under category: {category_name}")

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
            
            subcategory = self.db.query(SkillSubcategory).filter(
                SkillSubcategory.category_id == category.category_id,  # ← Added to fix collision bug
                SkillSubcategory.subcategory_name == subcategory_name
            ).first()
            
            if not subcategory:
                raise ImportServiceError(f"Subcategory '{subcategory_name}' not found under category '{category_name}' for skill '{skill_name}'")
            
            existing_skill = self.db.query(Skill).filter(
                Skill.skill_name == skill_name,
                Skill.subcategory_id == subcategory.subcategory_id
            ).first()
            
            if not existing_skill:
                new_skill = Skill(
                    skill_name=skill_name,
                    category_id=subcategory.category_id,
                    subcategory_id=subcategory.subcategory_id
                )
                self.db.add(new_skill)
                self.import_stats['new_skills'].append(skill_name)
                logger.info(f"Added new skill: {skill_name} under subcategory: {subcategory_name} (category: {category_name})")

    def _import_employees(self, employees_df: pd.DataFrame, import_timestamp: datetime) -> Dict[str, int]:
        """Import employees and return mapping of ZIDs to database employee IDs."""
        logger.info(f"Importing {len(employees_df)} employees")
        
        zid_to_employee_id_mapping = {}
        
        for _, row in employees_df.iterrows():
            zid = str(row['zid'])
            
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
            # Note: created_at is set explicitly to import_timestamp to ensure all records
            # imported in a single batch have the same creation time
            employee = Employee(
                zid=zid,
                full_name=row['full_name'],
                sub_segment_id=sub_segment.sub_segment_id,
                project_id=project.project_id,
                team_id=team.team_id,
                role_id=role.role_id if role else None,
                start_date_of_working=start_date,
                email=email,
                created_at=import_timestamp  # Explicit timestamp for import tracking
            )
            
            self.db.add(employee)
            self.db.flush()  # Get the auto-generated ID
            
            zid_to_employee_id_mapping[zid] = employee.employee_id
        
        self.import_stats['employees_imported'] = len(employees_df)
        logger.info(f"Imported {len(employees_df)} employees successfully")
        
        return zid_to_employee_id_mapping

    def _import_employee_skills(self, skills_df: pd.DataFrame, zid_to_employee_id_mapping: Dict[str, int], import_timestamp: datetime):
        """Import employee skills using the ZID to employee ID mapping with history tracking."""
        logger.info(f"Importing {len(skills_df)} employee skill records")
        
        # Initialize history service for bulk tracking
        history_service = SkillHistoryService(self.db)
        skill_records = []  # Collect all skills for bulk history tracking
        
        for _, row in skills_df.iterrows():
            zid = str(row['zid'])
            db_employee_id = zid_to_employee_id_mapping.get(zid)
            
            if not db_employee_id:
                raise ImportServiceError(f"Employee ZID mapping not found: {zid}")
            
            # Get skill ID - skill should exist from hierarchical processing
            skill = self.db.query(Skill).filter(
                Skill.skill_name == row['skill_name']
            ).first()
            
            if not skill:
                raise ImportServiceError(f"Skill not found: {row['skill_name']}")
            
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
            
            # Sanitize numeric fields - convert pandas NaN to None for PostgreSQL INTEGER compatibility
            years_experience = row.get('years_experience')
            if pd.isna(years_experience):
                years_experience = None
            else:
                try:
                    years_experience = int(years_experience)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid years_experience value '{years_experience}' for employee {zid}, setting to None")
                    years_experience = None
            
            interest_level = row.get('interest_level')
            if pd.isna(interest_level):
                interest_level = None
            else:
                try:
                    interest_level = int(interest_level)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid interest_level value '{interest_level}' for employee {zid}, setting to None")
                    interest_level = None
              # Create employee skill with explicit created_at timestamp
            # Note: created_at is set explicitly to import_timestamp to ensure all records
            # imported in a single batch have the same creation time
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
                created_at=import_timestamp  # Explicit timestamp for import tracking
            )
            
            self.db.add(employee_skill)
            self.db.flush()  # Get the ID for history tracking
            skill_records.append(employee_skill)
        
        # Bulk history tracking for all imported skills
        logger.info("Recording skill import history...")
        history_service.bulk_import_with_history(
            skill_records=skill_records,
            change_source=ChangeSource.IMPORT,
            changed_by="system",
            change_reason="Excel bulk import"
        )
        
        self.import_stats['skills_imported'] = len(skills_df)
        logger.info(f"Imported {len(skills_df)} employee skill records with history tracking")
