"""
Schemas for dashboard API responses.
"""
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class EmployeeScopeResponse(BaseModel):
    """Schema for employee scope count response."""
    employee_count: int = Field(..., description="Number of employees in scope")
    scope_level: Literal["ORGANIZATION", "SUB_SEGMENT", "PROJECT", "TEAM"] = Field(..., description="Current scope level")
    scope_label: str = Field(..., description="Human-readable scope label")
    filters: "EmployeeScopeFilters" = Field(..., description="Applied filters")

    class Config:
        from_attributes = True


class EmployeeScopeFilters(BaseModel):
    """Schema for employee scope filters."""
    sub_segment_id: Optional[int] = Field(None, description="Sub-segment filter ID")
    project_id: Optional[int] = Field(None, description="Project filter ID") 
    team_id: Optional[int] = Field(None, description="Team filter ID")

    class Config:
        from_attributes = True


class TopSkillItem(BaseModel):
    """Schema for individual top skill item."""
    skill_id: int = Field(..., description="Skill ID")
    skill_name: str = Field(..., description="Skill name")
    total_employees: int = Field(..., description="Total distinct employees with this skill")
    expert_count: int = Field(..., description="Number of employees at Expert level")
    proficient_count: int = Field(..., description="Number of employees at Proficient level")
    intermediate_beginner_count: int = Field(..., description="Number of employees at Competent/Advanced Beginner/Novice levels")
    expert_pct: int = Field(..., description="Percentage of employees at Expert level (rounded)")
    proficient_pct: int = Field(..., description="Percentage of employees at Proficient level (rounded)")
    intermediate_beginner_pct: int = Field(..., description="Percentage of employees at other levels (rounded)")

    class Config:
        from_attributes = True


class TopSkillsScope(BaseModel):
    """Schema for top skills scope information."""
    sub_segment_id: Optional[int] = Field(None, description="Sub-segment filter ID")
    project_id: Optional[int] = Field(None, description="Project filter ID")
    team_id: Optional[int] = Field(None, description="Team filter ID")
    scope_level: Literal["ORGANIZATION", "SUB_SEGMENT", "PROJECT", "TEAM"] = Field(..., description="Current scope level")
    employee_count: int = Field(..., description="Total employees in scope")

    class Config:
        from_attributes = True


class TopSkillsResponse(BaseModel):
    """Schema for top skills API response."""
    scope: TopSkillsScope = Field(..., description="Scope information")
    limit: int = Field(..., description="Requested limit")
    returned: int = Field(..., description="Actual number of skills returned")
    items: List[TopSkillItem] = Field(..., description="List of top skills")

    class Config:
        from_attributes = True


class SkillMomentumScope(BaseModel):
    """Schema for skill momentum scope information."""
    sub_segment_id: Optional[int] = Field(None, description="Sub-segment filter ID")
    project_id: Optional[int] = Field(None, description="Project filter ID")
    team_id: Optional[int] = Field(None, description="Team filter ID")
    employee_count: int = Field(..., description="Total employees in scope")

    class Config:
        from_attributes = True


class SkillMomentumBuckets(BaseModel):
    """Schema for skill momentum bucket counts."""
    updated_last_1_month: int = Field(..., description="Employees with updates in last 1 month")
    updated_last_3_months: int = Field(..., description="Employees with updates in last 3 months (but not 1 month)")
    updated_last_6_months: int = Field(..., description="Employees with updates in last 6 months (but not 3 months)")
    not_updated_gt_6_months: int = Field(..., description="Employees with no updates in > 6 months or no updates")

    class Config:
        from_attributes = True


class SkillMomentumResponse(BaseModel):
    """Schema for skill momentum API response."""
    scope: SkillMomentumScope = Field(..., description="Scope information")
    as_of: str = Field(..., description="Date of calculation (YYYY-MM-DD)")
    buckets: SkillMomentumBuckets = Field(..., description="Employee counts by momentum bucket")

    class Config:
        from_attributes = True


class OrgSkillCoverageItem(BaseModel):
    """Schema for individual organization skill coverage item."""
    sub_segment_name: str = Field(..., description="Sub-segment name")
    total_employees: int = Field(..., description="Total distinct employees in sub-segment")
    frontend_dev: int = Field(..., description="Frontend developers count")
    backend_dev: int = Field(..., description="Backend developers count")
    full_stack: int = Field(..., description="Full stack developers count")
    cloud_eng: int = Field(..., description="Cloud engineers count")
    devops: int = Field(..., description="DevOps engineers count")
    certified_pct: int = Field(..., description="Percentage of certified employees (rounded)")

    class Config:
        from_attributes = True


class OrgSkillCoverageTotals(BaseModel):
    """Schema for organization-wide totals."""
    total_employees: int = Field(..., description="Total employees organization-wide")
    frontend_dev: int = Field(..., description="Total frontend developers")
    backend_dev: int = Field(..., description="Total backend developers")
    full_stack: int = Field(..., description="Total full stack developers")
    cloud_eng: int = Field(..., description="Total cloud engineers")
    devops: int = Field(..., description="Total DevOps engineers")
    certified_pct: int = Field(..., description="Overall certified percentage")

    class Config:
        from_attributes = True


class OrgSkillCoverageResponse(BaseModel):
    """Schema for organization skill coverage API response."""
    sub_segments: List[OrgSkillCoverageItem] = Field(..., description="Sub-segment coverage data")
    organization_total: OrgSkillCoverageTotals = Field(..., description="Organization-wide totals")
    as_of: str = Field(..., description="Date of calculation (YYYY-MM-DD)")

    class Config:
        from_attributes = True