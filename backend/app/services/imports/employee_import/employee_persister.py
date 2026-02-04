"""
Employee database persistence for employee import.

Single Responsibility: Insert employee records to database.
"""
import logging
from typing import Dict
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models import Employee, SubSegment, Project, Team, Role

logger = logging.getLogger(__name__)


class EmployeePersister:
    """Handles employee database operations."""
    
    def __init__(self, db: Session, stats: Dict, date_parser, field_sanitizer):
        self.db = db
        self.stats = stats
        self.date_parser = date_parser
        self.field_sanitizer = field_sanitizer
    
    def import_employees(self, employees_df: pd.DataFrame, import_timestamp: datetime) -> Dict[str, int]:
        """
        Import employees with per-employee transaction scope for partial success.
        Each employee is committed independently so failures don't affect others.
        
        Args:
            employees_df: DataFrame with employee data
            import_timestamp: Import timestamp
            
        Returns:
            Dict mapping ZID to employee_id
        """
        logger.info(f"Importing {len(employees_df)} employees (per-employee transactions)")

        zid_to_employee_id_mapping = {}
        successful_imports = 0
        failed_employees = []

        for row_idx, row in employees_df.iterrows():
            row_number = row_idx + 2  # Excel row number (accounting for header)
            zid = str(row.get('zid', ''))
            full_name = str(row.get('full_name', ''))

            try:
                employee_id = self._import_single_employee(row, zid, full_name, import_timestamp)
                
                # Commit this employee immediately (per-employee transaction)
                self.db.commit()
                
                zid_to_employee_id_mapping[zid] = employee_id
                successful_imports += 1
                logger.debug(f"Committed employee {zid} (ID: {employee_id})")

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

        self.stats['employees_imported'] = successful_imports
        self.stats['failed_employees'] = failed_employees
        logger.info(f"Imported {successful_imports} of {len(employees_df)} employees (failed: {len(failed_employees)})")

        return zid_to_employee_id_mapping
    
    def _import_single_employee(self, row, zid: str, full_name: str, import_timestamp: datetime) -> int:
        """Import a single employee record."""
        # Get foreign key IDs - master data should exist from hierarchical processing
        sub_segment = self.db.query(SubSegment).filter(
            SubSegment.sub_segment_name == row['sub_segment']
        ).first()

        if not sub_segment:
            from app.services.import_service import ImportServiceError
            raise ImportServiceError(f"Sub-segment not found: {row['sub_segment']}")

        project = self.db.query(Project).filter(
            Project.project_name == row['project'],
            Project.sub_segment_id == sub_segment.sub_segment_id
        ).first()

        if not project:
            from app.services.import_service import ImportServiceError
            raise ImportServiceError(f"Project not found: {row['project']} under sub-segment: {row['sub_segment']}")

        team = self.db.query(Team).filter(
            Team.team_name == row['team'],
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
