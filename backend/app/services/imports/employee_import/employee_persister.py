"""
Employee database persistence for employee import.

Single Responsibility: Insert employee records to database.
"""
import logging
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Employee, SubSegment, Project, Team, Role
from .allocation_writer import parse_allocation_pct, upsert_active_project_allocation
from .master_data_validator import MasterDataValidator

logger = logging.getLogger(__name__)


class EmployeePersister:
    """Handles employee database operations."""
    
    def __init__(self, db: Session, stats: Dict, date_parser, field_sanitizer, progress_callback=None):
        self.db = db
        self.stats = stats
        self.date_parser = date_parser
        self.field_sanitizer = field_sanitizer
        self.progress_callback = progress_callback  # Optional callback for progress reporting
        # Master data validator for per-row validation
        self.master_data_validator = MasterDataValidator(db)
    
    @staticmethod
    def _is_empty(value) -> bool:
        """
        Check if a value is considered empty (None, empty string, or whitespace-only).
        
        Args:
            value: Value to check
            
        Returns:
            True if value is empty, False otherwise
        """
        import pandas as pd
        
        if value is None:
            return True
        if pd.isna(value):
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        return False
    
    def import_employees(self, employees_df: pd.DataFrame, import_timestamp: datetime) -> Dict[str, int]:
        """
        Import employees with upsert logic (update if exists, insert if new).
        Each employee is committed independently so failures don't affect others.
        
        UPSERT LOGIC:
        - Query Employee by zid
        - If NOT found: Create new Employee
        - If FOUND: Update only non-empty fields from Excel
        
        Args:
            employees_df: DataFrame with employee data
            import_timestamp: Import timestamp
            
        Returns:
            Dict mapping ZID to employee_id
        """
        logger.info(f"Upserting {len(employees_df)} employees (per-employee transactions)")

        zid_to_employee_id_mapping = {}
        successful_imports = 0
        employees_created = 0
        employees_updated = 0
        failed_employees = []
          # Threshold-based progress tracking for employees (20% → 50% range)
        total_employees = len(employees_df)
        progress_step = max(1, total_employees // 10)  # Update every ~10% of employees
        next_threshold = progress_step

        for row_idx, row in employees_df.iterrows():
            row_number = row_idx + 2  # Excel row number (accounting for header)
            zid = str(row.get('zid', ''))
            full_name = str(row.get('full_name', ''))

            try:
                # ----------------------------------------------------------
                # MASTER DATA VALIDATION (before any DB operations)
                # ----------------------------------------------------------
                sub_segment_name = row.get('sub_segment', '')
                project_name = row.get('project', '')
                team_name = row.get('team', '')
                role_name = row.get('role', '')
                
                validation_result = self.master_data_validator.validate_row(
                    sub_segment_name=sub_segment_name,
                    project_name=project_name,
                    team_name=team_name,
                    role_name=role_name if role_name else None,
                    zid=zid,
                    row_number=row_number
                )
                
                if not validation_result.is_valid:
                    # Record validation failure and skip this row
                    logger.warning(
                        f"Validation failed for row {row_number} (ZID: {zid}): "
                        f"{validation_result.error_message}"
                    )
                    failed_employee = {
                        'sheet': 'Employee',
                        'excel_row_number': row_number,
                        'row_number': row_number,
                        'sub_segment': sub_segment_name if sub_segment_name else None,
                        'zid': zid if zid else None,
                        'full_name': full_name if full_name else None,
                        'employee_name': full_name if full_name else None,
                        'skill_name': None,
                        'error_code': validation_result.error_code,
                        'message': validation_result.error_message
                    }
                    failed_employees.append(failed_employee)
                    self.stats['failed_rows'].append(failed_employee)
                    continue  # Skip to next row
                
                # ----------------------------------------------------------
                # EMPLOYEE UPSERT (validation passed)
                # ----------------------------------------------------------
                
                # Check if employee exists
                existing_employee = self.db.query(Employee).filter(Employee.zid == zid).first()
                
                if existing_employee:
                    # UPDATE: Update existing employee with non-empty fields only
                    employee_id = self._update_existing_employee(existing_employee, row, zid, import_timestamp)
                    employees_updated += 1
                    logger.debug(f"Updated employee {zid} (ID: {employee_id})")
                else:
                    # INSERT: Create new employee
                    employee_id = self._import_single_employee(row, zid, full_name, import_timestamp)
                    employees_created += 1
                    logger.debug(f"Created employee {zid} (ID: {employee_id})")
                
                # Handle project allocation if provided
                self._handle_project_allocation(row, employee_id, zid)
                
                # Commit this employee immediately (per-employee transaction)
                self.db.commit()
                
                zid_to_employee_id_mapping[zid] = employee_id
                successful_imports += 1
                
                # Report progress when crossing threshold
                if self.progress_callback and successful_imports >= next_threshold:
                    # Map employee progress to 20% → 50% range (30% total)
                    employee_progress_percent = (successful_imports / total_employees) * 30
                    overall_progress = 20 + employee_progress_percent
                    
                    self.progress_callback(
                        message=f"Importing employees... ({successful_imports}/{total_employees})",
                        percent=int(overall_progress),
                        total_rows=100,
                        employees_processed=successful_imports
                    )
                    
                    # Advance to next threshold
                    next_threshold += progress_step

            except Exception as e:
                # Log the error and continue with next row
                error_message = str(e)
                logger.warning(f"Failed to import employee at row {row_number} (ZID: {zid}, Name: {full_name}): {error_message}")
                
                # Determine error code
                error_code = self._determine_error_code(error_message)

                # Track failed employee
                failed_employee = {
                    'sheet': 'Employee',
                    'excel_row_number': row_number,
                    'row_number': row_number,  # Legacy field
                    'sub_segment': sub_segment_name if sub_segment_name else None,
                    'zid': zid if zid else None,
                    'full_name': full_name if full_name else None,
                    'employee_name': full_name if full_name else None,  # For consistency
                    'skill_name': None,  # Not applicable for employee rows
                    'error_code': error_code,
                    'message': error_message
                }
                failed_employees.append(failed_employee)
                self.stats['failed_rows'].append(failed_employee)

                # Rollback ONLY this employee (won't affect previous commits)
                self.db.rollback()
                continue
        
        # Always send final employee progress update
        if self.progress_callback and successful_imports > 0:
            self.progress_callback(
                message=f"Imported {successful_imports}/{total_employees} employees",
                percent=50,
                total_rows=100,
                employees_processed=successful_imports
            )

        self.stats['employees_imported'] = successful_imports
        self.stats['employees_created'] = employees_created
        self.stats['employees_updated'] = employees_updated
        self.stats['failed_employees'] = failed_employees
        logger.info(f"Upserted {successful_imports} of {len(employees_df)} employees "
                   f"(created: {employees_created}, updated: {employees_updated}, failed: {len(failed_employees)})")

        return zid_to_employee_id_mapping
    
    def _update_existing_employee(self, existing_employee: Employee, row, zid: str, import_timestamp: datetime) -> int:
        """
        Update an existing employee with non-empty fields from Excel.
        
        RULE: Never overwrite existing DB values with empty/null Excel values.
        
        Args:
            existing_employee: Existing Employee object from database
            row: DataFrame row with new data
            zid: Employee ZID
            import_timestamp: Import timestamp
            
        Returns:
            employee_id of the updated employee
        """
        # Update full_name if provided
        if not self._is_empty(row.get('full_name')):
            existing_employee.full_name = row['full_name']
        
        # Update team (NORMALIZED: team_id is the only org FK)
        # If team changes, project/sub_segment are derived via team relationships
        if not self._is_empty(row.get('team')):
            # Need project context for team lookup
            if not self._is_empty(row.get('project')) and not self._is_empty(row.get('sub_segment')):
                sub_segment = self.db.query(SubSegment).filter(
                    SubSegment.sub_segment_name == row['sub_segment']
                ).first()
                if sub_segment:
                    project = self.db.query(Project).filter(
                        Project.project_name == row['project'],
                        Project.sub_segment_id == sub_segment.sub_segment_id
                    ).first()
                    if project:
                        team = self.db.query(Team).filter(
                            Team.team_name == row['team'],
                            Team.project_id == project.project_id
                        ).first()
                        if team:
                            existing_employee.team_id = team.team_id
        
        # Update role if provided
        if not self._is_empty(row.get('role')):
            role = self.db.query(Role).filter(Role.role_name == row['role']).first()
            if role:
                existing_employee.role_id = role.role_id
        
        # Update start_date_of_working if provided
        if not self._is_empty(row.get('start_date_of_working')):
            start_date = self.date_parser.parse_date_safely(
                row.get('start_date_of_working'), 
                'start_date_of_working', 
                zid
            )
            if start_date:
                existing_employee.start_date_of_working = start_date
        
        # Update email if provided
        if not self._is_empty(row.get('email')):
            email_raw = row.get('email') or row.get('Email')
            if email_raw and not pd.isna(email_raw):
                email = str(email_raw).strip()
                if email:
                    existing_employee.email = email
        
        self.db.add(existing_employee)
        self.db.flush()  # Ensure ID is available
        
        return existing_employee.employee_id
    
    def _import_single_employee(self, row, zid: str, full_name: str, import_timestamp: datetime) -> int:
        """
        Import a single employee record.
        
        NORMALIZED: Only team_id is stored on Employee.
        project/sub_segment are derived via team -> project -> sub_segment.
        """
        # Get foreign key IDs - master data should exist from hierarchical processing
        # Normalize input for case-insensitive matching
        sub_segment_input = str(row['sub_segment']).strip().lower() if row.get('sub_segment') else ""
        project_input = str(row['project']).strip().lower() if row.get('project') else ""
        team_input = str(row['team']).strip().lower() if row.get('team') else ""
        
        sub_segment = self.db.query(SubSegment).filter(
            func.lower(func.trim(SubSegment.sub_segment_name)) == sub_segment_input
        ).first()

        if not sub_segment:
            from app.services.import_service import ImportServiceError
            raise ImportServiceError(f"Sub-segment not found: {row['sub_segment']}")

        project = self.db.query(Project).filter(
            func.lower(func.trim(Project.project_name)) == project_input,
            Project.sub_segment_id == sub_segment.sub_segment_id
        ).first()

        if not project:
            from app.services.import_service import ImportServiceError
            raise ImportServiceError(f"Project not found: {row['project']} under sub-segment: {row['sub_segment']}")

        # Debug logging for team lookup
        logger.debug(f"Team lookup: input='{row.get('team')}' normalized='{team_input}' project_id={project.project_id}")
        
        # Get top 5 teams under this project for debugging
        teams_in_project = self.db.query(Team).filter(Team.project_id == project.project_id).limit(5).all()
        logger.debug(f"Teams under project {project.project_id}: {[t.team_name for t in teams_in_project]}")
        
        team = self.db.query(Team).filter(
            func.lower(func.trim(Team.team_name)) == team_input,
            Team.project_id == project.project_id
        ).first()

        if not team:
            from app.services.import_service import ImportServiceError
            raise ImportServiceError(f"Team not found: {row['team']} under project: {row['project']}")

        # Lookup role by name (optional)
        role = None
        if row.get('role'):
            role = self.db.query(Role).filter(Role.role_name == row['role']).first()

        # Convert start_date_of_working using safe parsing
        start_date = self.date_parser.parse_date_safely(
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

        # Create employee (NORMALIZED: only team_id, not project_id/sub_segment_id)
        employee = Employee(
            zid=zid,
            full_name=full_name,
            team_id=team.team_id,
            role_id=role.role_id if role else None,
            start_date_of_working=start_date,
            email=email,
            created_at=import_timestamp
        )

        self.db.add(employee)
        self.db.flush()  # Get the auto-generated ID
        
        return employee.employee_id
    
    def _determine_error_code(self, error_message: str) -> str:
        """Determine error code based on error message."""
        error_message_lower = error_message.lower()
        
        if "not found" in error_message_lower:
            return "MISSING_REFERENCE"
        elif "duplicate" in error_message_lower:
            return "DUPLICATE_ENTRY"
        elif "constraint" in error_message_lower:
            return "CONSTRAINT_VIOLATION"
        else:
            return "IMPORT_ERROR"

    def _handle_project_allocation(self, row, employee_id: int, zid: str) -> Optional[int]:
        """
        Handle project allocation for an employee during import.
        
        If "Project Allocation %" column is present and valid:
        - Resolve project_id from employee's team
        - Upsert allocation into employee_project_allocations
        
        Args:
            row: DataFrame row with employee data
            employee_id: ID of the employee just created/updated
            zid: Employee ZID for logging
            
        Returns:
            allocation_id if created/updated, None otherwise
        """
        # Check if allocation column exists and has value
        raw_allocation = row.get('project_allocation_pct')
        allocation_pct = parse_allocation_pct(raw_allocation)
        
        if allocation_pct is None:
            return None  # No allocation to process
        
        # Resolve project_id via employee's team
        employee = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee or not employee.team:
            logger.warning(
                f"Allocation% provided for employee {zid} but team not resolved; "
                f"skipping allocation row"
            )
            return None
        
        project_id = employee.team.project_id
        if not project_id:
            logger.warning(
                f"Allocation% provided for employee {zid} but project not resolved; "
                f"skipping allocation row"
            )
            return None
        
        # Determine start_date: prefer employee's start_date_of_working, fallback to today
        start_date = employee.start_date_of_working
        
        try:
            allocation_id = upsert_active_project_allocation(
                db=self.db,
                employee_id=employee_id,
                project_id=project_id,
                allocation_pct=allocation_pct,
                start_date=start_date,
                allocation_type='BILLABLE'
            )
            logger.debug(f"Upserted allocation for employee {zid}: {allocation_pct}% on project {project_id}")
            return allocation_id
        except Exception as e:
            logger.warning(f"Failed to upsert allocation for employee {zid}: {e}")
            # Don't fail the employee import for allocation errors
            return None