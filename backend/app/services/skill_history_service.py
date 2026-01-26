"""
Service for tracking employee skill changes and history.
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models.employee_skill import EmployeeSkill
from app.models.skill_history import EmployeeSkillHistory, ChangeAction, ChangeSource
from app.db.session import SessionLocal


class SkillHistoryService:
    """Service for managing employee skill change history."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_skill_change(
        self,
        employee_id: int,
        skill_id: int,
        old_skill_record: Optional[EmployeeSkill],
        new_skill_record: EmployeeSkill,
        change_source: ChangeSource = ChangeSource.UI,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None,
        batch_id: Optional[str] = None
    ) -> EmployeeSkillHistory:
        """
        Record a skill change in the history table.
        
        Args:
            employee_id: ID of the employee
            skill_id: ID of the skill
            old_skill_record: Previous state (None for new skills)
            new_skill_record: New/updated state (None for deletions)
            change_source: Source of the change
            changed_by: Who made the change (optional)
            change_reason: Reason for change (optional)
            batch_id: Batch identifier for grouped changes
            
        Returns:
            The created history record
        """
        
        # Determine action type
        if old_skill_record is None:
            action = ChangeAction.INSERT
        elif new_skill_record is None:
            action = ChangeAction.DELETE
        else:
            action = ChangeAction.UPDATE
        
        # Create history record
        history_record = EmployeeSkillHistory(
            employee_id=employee_id,
            skill_id=skill_id,
            emp_skill_id=new_skill_record.emp_skill_id if new_skill_record else None,
            action=action,
            change_source=change_source,
            changed_by=changed_by,
            change_reason=change_reason,
            batch_id=batch_id,
            
            # Old state
            old_proficiency_level_id=old_skill_record.proficiency_level_id if old_skill_record else None,
            old_years_experience=old_skill_record.years_experience if old_skill_record else None,
            old_last_used=old_skill_record.last_used if old_skill_record else None,
            old_certification=old_skill_record.certification if old_skill_record else None,
            
            # New state  
            new_proficiency_level_id=new_skill_record.proficiency_level_id if new_skill_record else None,
            new_years_experience=new_skill_record.years_experience if new_skill_record else None,
            new_last_used=new_skill_record.last_used if new_skill_record else None,
            new_certification=new_skill_record.certification if new_skill_record else None,
        )
        
        self.db.add(history_record)
        self.db.flush()  # Get the ID
        
        return history_record
    
    def update_skill_with_history(
        self,
        emp_skill_id: int,
        proficiency_level_id: Optional[int] = None,
        years_experience: Optional[int] = None,
        last_used: Optional[datetime] = None,
        certification: Optional[str] = None,
        change_source: ChangeSource = ChangeSource.UI,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> tuple[EmployeeSkill, EmployeeSkillHistory]:
        """
        Update an employee skill and record the change in history.
        
        This is the main method you'll call from your API routes.
        
        Returns:
            Tuple of (updated_skill_record, history_record)
        """
        
        # Get current state
        old_record = self.db.query(EmployeeSkill).filter(
            EmployeeSkill.emp_skill_id == emp_skill_id
        ).first()
        
        if not old_record:
            raise ValueError(f"Employee skill record {emp_skill_id} not found")
        
        # Create a copy of old state for history
        old_state = EmployeeSkill(
            proficiency_level_id=old_record.proficiency_level_id,
            years_experience=old_record.years_experience,
            last_used=old_record.last_used,
            certification=old_record.certification
        )
        
        # Apply updates
        if proficiency_level_id is not None:
            old_record.proficiency_level_id = proficiency_level_id
        if years_experience is not None:
            old_record.years_experience = years_experience
        if last_used is not None:
            old_record.last_used = last_used
        if certification is not None:
            old_record.certification = certification
            
        # Update the last_updated timestamp
        old_record.last_updated = datetime.utcnow()
        
        # Record the change in history
        history_record = self.record_skill_change(
            employee_id=old_record.employee_id,
            skill_id=old_record.skill_id,
            old_skill_record=old_state,
            new_skill_record=old_record,
            change_source=change_source,
            changed_by=changed_by,
            change_reason=change_reason
        )
        
        return old_record, history_record
    
    def create_skill_with_history(
        self,
        employee_id: int,
        skill_id: int,
        proficiency_level_id: int,
        years_experience: Optional[int] = None,
        last_used: Optional[datetime] = None,
        certification: Optional[str] = None,
        change_source: ChangeSource = ChangeSource.UI,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> tuple[EmployeeSkill, EmployeeSkillHistory]:
        """
        Create a new employee skill and record it in history.
        
        Returns:
            Tuple of (new_skill_record, history_record)
        """
        
        # Create new skill record
        new_skill = EmployeeSkill(
            employee_id=employee_id,
            skill_id=skill_id,
            proficiency_level_id=proficiency_level_id,
            years_experience=years_experience,
            last_used=last_used,
            certification=certification
        )
        
        self.db.add(new_skill)
        self.db.flush()  # Get the ID
        
        # Record in history
        history_record = self.record_skill_change(
            employee_id=employee_id,
            skill_id=skill_id,
            old_skill_record=None,  # No previous state
            new_skill_record=new_skill,
            change_source=change_source,
            changed_by=changed_by,
            change_reason=change_reason
        )
        
        return new_skill, history_record
    
    def bulk_import_with_history(
        self,
        skill_records: list[EmployeeSkill],
        change_source: ChangeSource = ChangeSource.IMPORT,
        changed_by: Optional[str] = None,
        change_reason: str = "Bulk Excel import"
    ):
        """
        Handle bulk import operations with history tracking.
        
        This method should be integrated into your existing import service.
        """
        
        batch_id = str(uuid.uuid4())[:8]  # Short unique ID for this import batch
        
        for skill_record in skill_records:
            # For imports, we typically don't have "old" state since we clear the table
            # So everything is an INSERT operation
            self.record_skill_change(
                employee_id=skill_record.employee_id,
                skill_id=skill_record.skill_id,
                old_skill_record=None,
                new_skill_record=skill_record,
                change_source=change_source,
                changed_by=changed_by,
                change_reason=change_reason,
                batch_id=batch_id
            )
    
    def get_skill_history(
        self,
        employee_id: Optional[int] = None,
        skill_id: Optional[int] = None,
        limit: int = 100
    ) -> list[EmployeeSkillHistory]:
        """Get skill change history with optional filtering."""
        
        query = self.db.query(EmployeeSkillHistory)
        
        if employee_id:
            query = query.filter(EmployeeSkillHistory.employee_id == employee_id)
        if skill_id:
            query = query.filter(EmployeeSkillHistory.skill_id == skill_id)
            
        return query.order_by(EmployeeSkillHistory.changed_at.desc()).limit(limit).all()


# Example usage in your API routes:
def update_employee_skill_api_example():
    """Example of how to use this in your API routes."""
    
    db = SessionLocal()
    history_service = SkillHistoryService(db)
    
    try:
        # Update a skill with history tracking
        updated_skill, history_record = history_service.update_skill_with_history(
            emp_skill_id=123,
            proficiency_level_id=4,  # Changed from level 3 to 4
            change_source=ChangeSource.UI,
            changed_by="user123",
            change_reason="Annual review - demonstrated advanced capabilities"
        )
        
        db.commit()
        
        return {
            "message": "Skill updated successfully",
            "skill": updated_skill,
            "history_id": history_record.history_id
        }
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
