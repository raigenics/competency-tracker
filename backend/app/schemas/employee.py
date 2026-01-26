"""
Employee-related Pydantic schemas.
"""
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from datetime import date
from app.schemas.common import PaginatedResponse
from app.schemas.role import RoleResponse

if TYPE_CHECKING:
    from app.schemas.competency import EmployeeSkillResponse


class EmployeeBase(BaseModel):
    """Base employee schema with common fields."""
    zid: str = Field(..., description="Employee ZID (business identifier)")
    full_name: str = Field(..., description="Full name of the employee")
    role: Optional[RoleResponse] = Field(default=None, description="Employee role")
    start_date_of_working: Optional[date] = Field(None, description="Start date of employment")


class EmployeeCreate(BaseModel):
    """Schema for creating a new employee."""
    zid: str = Field(..., description="Employee ZID (business identifier)")
    full_name: str = Field(..., description="Full name of the employee")
    role_name: Optional[str] = Field(default=None, max_length=100, description="Employee role name")
    start_date_of_working: Optional[date] = Field(None, description="Start date of employment")
    sub_segment_name: str = Field(description="Name of the sub-segment")
    project_name: str = Field(description="Name of the project")
    team_name: str = Field(description="Name of the team")


class OrganizationInfo(BaseModel):
    """Organization information for employee."""
    sub_segment: str = Field(description="Sub-segment name")
    project: str = Field(description="Project name")
    team: str = Field(description="Team name")


class EmployeeResponse(EmployeeBase):
    """Response schema for employee data."""
    employee_id: int = Field(description="Employee ID")
    organization: OrganizationInfo = Field(description="Organization structure")
    skills_count: int = Field(description="Number of skills for this employee")
    
    class Config:
        from_attributes = True


class EmployeeListResponse(PaginatedResponse[EmployeeResponse]):
    """Paginated response for employee list."""
    pass


# Define EmployeeDetailResponse without the circular import - we'll handle this separately
class EmployeeDetailResponse(EmployeeResponse):
    """Detailed employee response with skills."""
    pass  # We'll update this dynamically after all schemas are loaded


class EmployeeStatsResponse(BaseModel):
    """Employee statistics response."""
    total_employees: int = Field(description="Total number of employees")
    by_sub_segment: dict = Field(description="Employee count by sub-segment")
    by_project: dict = Field(description="Employee count by project")
    by_team: dict = Field(description="Employee count by team")
    avg_skills_per_employee: float = Field(description="Average number of skills per employee")
