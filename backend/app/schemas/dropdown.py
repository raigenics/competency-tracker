"""
Schemas for dropdown data responses.
"""
from typing import List, Optional
from pydantic import BaseModel


class DropdownItem(BaseModel):
    """Base schema for dropdown items."""
    id: int
    name: str

    class Config:
        from_attributes = True


class SegmentDropdown(DropdownItem):
    """Schema for segment dropdown items."""
    pass


class SubSegmentDropdown(DropdownItem):
    """Schema for sub-segment dropdown items."""
    pass


class ProjectDropdown(DropdownItem):
    """Schema for project dropdown items."""
    pass


class TeamDropdown(DropdownItem):
    """Schema for team dropdown items."""
    pass


class RoleDropdown(BaseModel):
    """Schema for role dropdown items (uses role_id, role_name, role_alias, role_description)."""
    role_id: int
    role_name: str
    role_alias: Optional[str] = None
    role_description: Optional[str] = None

    class Config:
        from_attributes = True


class SegmentListResponse(BaseModel):
    """Response schema for segments list."""
    segments: List[SegmentDropdown]


class SubSegmentListResponse(BaseModel):
    """Response schema for sub-segments list."""
    sub_segments: List[SubSegmentDropdown]


class ProjectListResponse(BaseModel):
    """Response schema for projects list."""
    projects: List[ProjectDropdown]


class TeamListResponse(BaseModel):
    """Response schema for teams list."""
    teams: List[TeamDropdown]


class ProficiencyLevelDropdown(BaseModel):
    """Schema for proficiency level dropdown items."""
    proficiency_level_id: int
    level_name: str
    level_description: Optional[str] = None
    # Frontend-compatible value (e.g., 'NOVICE', 'ADVANCED_BEGINNER')
    value: str

    class Config:
        from_attributes = True


class ProficiencyLevelListResponse(BaseModel):
    """Response schema for proficiency levels list."""
    proficiency_levels: List[ProficiencyLevelDropdown]
