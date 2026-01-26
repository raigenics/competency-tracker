"""
Pydantic schemas for skill history tracking.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.skill_history import ChangeAction, ChangeSource


class SkillHistoryResponse(BaseModel):
    """Response model for skill history records."""
    history_id: int
    employee_id: int
    employee_name: Optional[str] = None
    skill_id: int
    skill_name: Optional[str] = None
    emp_skill_id: Optional[int] = None
    
    action: ChangeAction
    changed_at: datetime
    change_source: ChangeSource
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    batch_id: Optional[str] = None
    
    # Before state (None for INSERT)
    old_proficiency_level_id: Optional[int] = None
    old_proficiency_name: Optional[str] = None
    old_years_experience: Optional[int] = None
    old_certification: Optional[str] = None
    
    # After state (None for DELETE)
    new_proficiency_level_id: Optional[int] = None
    new_proficiency_name: Optional[str] = None
    new_years_experience: Optional[int] = None
    new_certification: Optional[str] = None

    class Config:
        from_attributes = True


class ProficiencyChangeResponse(BaseModel):
    """Response model for simplified proficiency changes."""
    change_id: int
    employee_id: int
    employee_name: Optional[str] = None
    skill_id: int
    skill_name: Optional[str] = None
    
    from_proficiency_id: Optional[int] = None
    from_proficiency_name: Optional[str] = None
    to_proficiency_id: int
    to_proficiency_name: Optional[str] = None
    
    changed_at: datetime
    change_source: ChangeSource
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    batch_id: Optional[str] = None

    class Config:
        from_attributes = True


class SkillUpdateRequest(BaseModel):
    """Request model for updating employee skills."""
    proficiency_level_id: Optional[int] = None
    years_experience: Optional[int] = None
    certification: Optional[str] = None
    change_reason: Optional[str] = None


class SkillCreateRequest(BaseModel):
    """Request model for creating new employee skills."""
    employee_id: int
    skill_id: int
    proficiency_level_id: int
    years_experience: Optional[int] = None
    certification: Optional[str] = None
    change_reason: Optional[str] = None


class SkillHistoryListResponse(BaseModel):
    """Response model for paginated skill history."""
    items: List[SkillHistoryResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(cls, items: List[SkillHistoryResponse], total: int, pagination):
        """Create a paginated response."""
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            has_next=pagination.offset + len(items) < total,
            has_previous=pagination.page > 1
        )


class SkillProgressionResponse(BaseModel):
    """Response showing skill progression over time."""
    employee_id: int
    employee_name: str
    skill_id: int
    skill_name: str
    progression: List[ProficiencyChangeResponse]
    current_proficiency: str
    progression_trend: str  # "improving", "declining", "stable"

    class Config:
        from_attributes = True
