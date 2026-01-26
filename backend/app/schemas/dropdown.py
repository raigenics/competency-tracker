"""
Schemas for dropdown data responses.
"""
from typing import List
from pydantic import BaseModel


class DropdownItem(BaseModel):
    """Base schema for dropdown items."""
    id: int
    name: str

    class Config:
        from_attributes = True


class SubSegmentDropdown(DropdownItem):
    """Schema for sub-segment dropdown items."""
    pass


class ProjectDropdown(DropdownItem):
    """Schema for project dropdown items."""
    pass


class TeamDropdown(DropdownItem):
    """Schema for team dropdown items."""
    pass


class SubSegmentListResponse(BaseModel):
    """Response schema for sub-segments list."""
    sub_segments: List[SubSegmentDropdown]


class ProjectListResponse(BaseModel):
    """Response schema for projects list."""
    projects: List[ProjectDropdown]


class TeamListResponse(BaseModel):
    """Response schema for teams list."""
    teams: List[TeamDropdown]
