"""
Schemas for Capability Finder (Advanced Query) API.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SkillListResponse(BaseModel):
    """Response schema for skills list."""
    skills: List[str]


class RoleListResponse(BaseModel):
    """Response schema for roles list."""
    roles: List[str]


class SearchRequest(BaseModel):
    """Request schema for talent search."""
    skills: List[str] = Field(default_factory=list, description="List of required skill names (AND logic)")
    sub_segment_id: Optional[int] = Field(None, description="Sub-segment ID filter")
    team_id: Optional[int] = Field(None, description="Team ID filter")
    role: Optional[str] = Field(None, description="Role name filter")
    min_proficiency: int = Field(0, ge=0, le=5, description="Minimum proficiency level (0-5)")
    min_experience_years: int = Field(0, ge=0, description="Minimum years of experience")


class SkillInfo(BaseModel):
    """Skill information for an employee."""
    name: str
    proficiency: int


class EmployeeSearchResult(BaseModel):
    """Single employee search result."""
    employee_id: int
    employee_name: str
    sub_segment: str
    team: str
    role: str
    top_skills: List[SkillInfo]


class SearchResponse(BaseModel):
    """Response schema for talent search."""
    results: List[EmployeeSearchResult]
    count: int


class ExportRequest(BaseModel):
    """Request schema for export matching talent."""
    mode: str = Field(..., description="Export mode: 'all' or 'selected'")
    filters: SearchRequest = Field(..., description="Search filters to apply")
    selected_employee_ids: List[int] = Field(default_factory=list, description="Employee IDs for mode='selected'")
