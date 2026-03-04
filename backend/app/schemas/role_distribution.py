"""
Schemas for Dashboard Role Distribution API.

Defines request/response contracts for the role distribution endpoint.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS / CONSTANTS
# =============================================================================

ContextLevelType = Literal["SEGMENT", "SUB_SEGMENT", "PROJECT", "TEAM"]
BreakdownLabelType = Literal["Sub-Segment", "Project", "Team"]


# =============================================================================
# NESTED SCHEMAS
# =============================================================================

class RoleCount(BaseModel):
    """Schema for individual role count within a breakdown row."""
    role_id: int = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    employee_count: int = Field(..., ge=0, description="Number of employees with this role")

    class Config:
        from_attributes = True


class RoleDistributionScope(BaseModel):
    """Schema for scope information showing current filter context."""
    segment_id: int = Field(..., description="Segment ID (always present)")
    segment_name: str = Field(..., description="Segment name")
    sub_segment_id: Optional[int] = Field(None, description="Sub-segment ID if filtered")
    sub_segment_name: Optional[str] = Field(None, description="Sub-segment name if filtered")
    project_id: Optional[int] = Field(None, description="Project ID if filtered")
    project_name: Optional[str] = Field(None, description="Project name if filtered")
    team_id: Optional[int] = Field(None, description="Team ID if filtered")
    team_name: Optional[str] = Field(None, description="Team name if filtered")

    class Config:
        from_attributes = True


class RoleDistributionRow(BaseModel):
    """Schema for a single breakdown row in the role distribution table."""
    breakdown_id: int = Field(..., description="ID of the breakdown entity (sub_segment/project/team)")
    breakdown_name: str = Field(..., description="Name of the breakdown entity")
    total_employees: int = Field(..., ge=0, description="Total employee count for this breakdown")
    top_roles: List[RoleCount] = Field(
        default_factory=list, 
        description="Top N roles by employee count (for inline chips)"
    )
    all_roles: List[RoleCount] = Field(
        default_factory=list, 
        description="All roles up to max_roles (for expanded panel)"
    )
    more_roles_count: int = Field(
        ..., 
        ge=0, 
        description="Number of additional roles beyond top_n (for '+X more' indicator)"
    )

    class Config:
        from_attributes = True


# =============================================================================
# RESPONSE SCHEMA
# =============================================================================

class RoleDistributionResponse(BaseModel):
    """
    Response schema for GET /api/dashboard/role-distribution.
    
    Contains all data needed to render the Role Distribution dashboard section:
    - Dynamic title/subtitle based on context level
    - Breakdown rows with role counts and expandable details
    """
    context_level: ContextLevelType = Field(
        ..., 
        description="Current context level based on filters"
    )
    title: str = Field(
        ..., 
        description="Dynamic title for the section (e.g., 'Role Distribution by Segment DTS')"
    )
    subtitle: str = Field(
        ..., 
        description="Dynamic subtitle for the section (e.g., 'Employee count by role across Sub-Segments')"
    )
    breakdown_label: BreakdownLabelType = Field(
        ..., 
        description="Label for the first table column (Sub-Segment/Project/Team)"
    )
    scope: RoleDistributionScope = Field(
        ..., 
        description="Current scope/filter context"
    )
    rows: List[RoleDistributionRow] = Field(
        default_factory=list, 
        description="Breakdown rows for the table"
    )

    class Config:
        from_attributes = True


# =============================================================================
# ERROR RESPONSE
# =============================================================================

class RoleDistributionError(BaseModel):
    """Schema for error responses."""
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for client handling")

    class Config:
        from_attributes = True
