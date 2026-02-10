"""
Employee-related Pydantic schemas.
"""
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, validator
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


class EmployeeCreateRequest(BaseModel):
    """Request schema for creating a new employee via API."""
    zid: str = Field(..., min_length=1, max_length=50, description="Employee ZID (business identifier)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name of the employee")
    email: str = Field(..., max_length=255, description="Employee email address (required)")
    team_id: int = Field(..., description="ID of the team the employee belongs to")
    role_id: int = Field(..., description="Role ID from roles table (required)")
    start_date_of_working: Optional[date] = Field(None, description="Start date of employment")
    allocation_pct: Optional[int] = Field(None, ge=0, le=100, description="Project allocation percentage (0-100)")


class EmployeeCreateResponse(BaseModel):
    """Response schema for created employee."""
    employee_id: int = Field(description="Created employee ID")
    zid: str = Field(description="Employee ZID")
    full_name: str = Field(description="Full name of the employee")
    email: Optional[str] = Field(None, description="Employee email")
    team_id: int = Field(description="Team ID")
    team_name: str = Field(description="Team name")
    project_name: str = Field(description="Project name")
    sub_segment_name: str = Field(description="Sub-segment name")
    role_name: Optional[str] = Field(None, description="Role name")
    start_date_of_working: Optional[date] = Field(None, description="Start date")
    message: str = Field(default="Employee created successfully")
    
    class Config:
        from_attributes = True


class EmployeeUpdateRequest(BaseModel):
    """Request schema for updating an existing employee via API."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name of the employee")
    email: Optional[str] = Field(None, max_length=255, description="Employee email address")
    team_id: Optional[int] = Field(None, description="ID of the team the employee belongs to")
    role_id: Optional[int] = Field(None, description="Role ID from roles table")
    start_date_of_working: Optional[date] = Field(None, description="Start date of employment")
    allocation_pct: Optional[int] = Field(None, ge=0, le=100, description="Project allocation percentage (0-100)")


class OrganizationInfo(BaseModel):
    """Organization information for employee."""
    sub_segment: str = Field(description="Sub-segment name")
    project: str = Field(description="Project name")
    team: str = Field(description="Team name")
    # IDs for Edit form preselection (added for stale-while-revalidate optimization)
    segment_id: Optional[int] = Field(None, description="Segment ID")
    sub_segment_id: Optional[int] = Field(None, description="Sub-segment ID")
    project_id: Optional[int] = Field(None, description="Project ID")
    team_id: Optional[int] = Field(None, description="Team ID")


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


class SkillInfo(BaseModel):
    """Skill information for talent results."""
    name: str = Field(description="Skill name")
    proficiency: int = Field(description="Proficiency level (1-5)")


class TalentResultItem(BaseModel):
    """Single talent result item for table display."""
    id: int = Field(description="Employee ID")
    name: str = Field(description="Employee name")
    subSegment: str = Field(description="Sub-segment name")
    team: str = Field(description="Team name")
    role: str = Field(description="Role name")
    skills: List[SkillInfo] = Field(description="List of top skills")


class EmployeesByIdsRequest(BaseModel):
    """Request schema for fetching employees by IDs."""
    employee_ids: List[int] = Field(description="List of employee IDs to fetch")


class EmployeesByIdsResponse(BaseModel):
    """Response schema for employees by IDs."""
    results: List[TalentResultItem] = Field(description="List of employees with skills")


class EmployeeSuggestion(BaseModel):
    """Employee suggestion for autocomplete."""
    employee_id: int = Field(description="Employee ID")
    zid: str = Field(description="Employee ZID")
    full_name: str = Field(description="Full name of the employee")
    sub_segment: Optional[str] = Field(None, description="Sub-segment name")
    project: Optional[str] = Field(None, description="Project name")
    team: Optional[str] = Field(None, description="Team name")
    
    class Config:
        from_attributes = True


# ==========================================
# Employee Skills Bulk Save Schemas
# ==========================================

class EmployeeSkillItem(BaseModel):
    """Single skill item for bulk save."""
    skill_id: int = Field(description="Skill ID from approved skills list")
    proficiency: str = Field(
        description="Proficiency level name (NOVICE, ADVANCED_BEGINNER, COMPETENT, PROFICIENT, EXPERT)"
    )
    years_experience: Optional[float] = Field(
        default=None, ge=0, le=50,
        description="Years of experience with this skill"
    )
    last_used_month: Optional[str] = Field(
        default=None, pattern=r"^(0[1-9]|1[0-2])$",
        description="Last used month (01-12)"
    )
    last_used_year: Optional[str] = Field(
        default=None, pattern=r"^\d{2,4}$",
        description="Last used year (YY or YYYY)"
    )
    started_from: Optional[date] = Field(
        default=None, description="Date started learning this skill (YYYY-MM-DD)"
    )
    certification: Optional[str] = Field(
        default=None, max_length=500,
        description="Certification details (optional)"
    )
    
    class Config:
        from_attributes = True


class EmployeeSkillsBulkSaveRequest(BaseModel):
    """Request schema for bulk saving employee skills."""
    skills: List[EmployeeSkillItem] = Field(
        description="List of skills to save for the employee"
    )
    
    @validator('skills')
    def check_no_duplicate_skills(cls, v):
        skill_ids = [s.skill_id for s in v]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Duplicate skill_id found in the skills list")
        return v


class EmployeeSkillsBulkSaveResponse(BaseModel):
    """Response schema for bulk saving employee skills."""
    message: str = Field(description="Success message")
    employee_id: int = Field(description="Employee ID")
    skills_saved: int = Field(description="Number of skills saved")
    skills_deleted: int = Field(description="Number of previous skills deleted")


class EmployeeValidateUniqueResponse(BaseModel):
    """Response schema for ZID/email uniqueness validation."""
    zid_exists: bool = Field(description="True if ZID already exists in database")
    email_exists: bool = Field(description="True if email already exists in database")


# ==========================================
# Edit Bootstrap Endpoint Schemas
# ==========================================

class EditBootstrapEmployee(BaseModel):
    """Employee data for edit-bootstrap endpoint."""
    employee_id: int = Field(description="Employee ID")
    zid: str = Field(description="Employee ZID (business identifier)")
    full_name: str = Field(description="Full name of the employee")
    email: Optional[str] = Field(None, description="Employee email address")
    role_id: Optional[int] = Field(None, description="Role ID from roles table")
    team_id: int = Field(description="Team ID (required)")
    project_id: Optional[int] = Field(None, description="Project ID (derived via team)")
    sub_segment_id: Optional[int] = Field(None, description="Sub-segment ID (derived via team->project)")
    segment_id: Optional[int] = Field(None, description="Segment ID (derived via team->project->sub_segment)")
    start_date_of_working: Optional[date] = Field(None, description="Start date of employment")
    allocation: Optional[int] = Field(None, ge=0, le=100, description="Current project allocation percentage")


class EditBootstrapSegment(BaseModel):
    """Segment dropdown option for edit-bootstrap."""
    segment_id: int = Field(description="Segment ID")
    segment_name: str = Field(description="Segment name")


class EditBootstrapSubSegment(BaseModel):
    """Sub-segment dropdown option for edit-bootstrap."""
    sub_segment_id: int = Field(description="Sub-segment ID")
    sub_segment_name: str = Field(description="Sub-segment name")
    segment_id: int = Field(description="Parent segment ID")


class EditBootstrapProject(BaseModel):
    """Project dropdown option for edit-bootstrap."""
    project_id: int = Field(description="Project ID")
    project_name: str = Field(description="Project name")
    sub_segment_id: int = Field(description="Parent sub-segment ID")


class EditBootstrapTeam(BaseModel):
    """Team dropdown option for edit-bootstrap."""
    team_id: int = Field(description="Team ID")
    team_name: str = Field(description="Team name")
    project_id: int = Field(description="Parent project ID")


class EditBootstrapRole(BaseModel):
    """Role dropdown option for edit-bootstrap."""
    role_id: int = Field(description="Role ID")
    role_name: str = Field(description="Role name")


class EditBootstrapOptions(BaseModel):
    """All dropdown options for edit-bootstrap."""
    segments: List[EditBootstrapSegment] = Field(description="All segments")
    sub_segments: List[EditBootstrapSubSegment] = Field(description="All sub-segments with parent IDs")
    projects: List[EditBootstrapProject] = Field(description="All projects with parent IDs")
    teams: List[EditBootstrapTeam] = Field(description="All teams with parent IDs")
    roles: List[EditBootstrapRole] = Field(description="All roles")


class EditBootstrapSkill(BaseModel):
    """Skill data for edit-bootstrap endpoint."""
    emp_skill_id: int = Field(description="Employee skill ID (for UPDATE operations)")
    skill_id: int = Field(description="Skill ID")
    skill_name: str = Field(description="Skill name")
    proficiency_level_id: Optional[int] = Field(None, description="Proficiency level ID for dropdown preselection")
    proficiency_level_name: Optional[str] = Field(None, description="Proficiency level name for display")


class EditBootstrapMeta(BaseModel):
    """Metadata for edit-bootstrap response."""
    generated_at: str = Field(description="ISO timestamp when response was generated")


class EditBootstrapResponse(BaseModel):
    """
    Response schema for GET /employees/{employee_id}/edit-bootstrap.
    
    Returns all data needed to render the Edit Employee form in ONE call:
    - Employee data with org hierarchy IDs
    - All dropdown options (segments, sub-segments, projects, teams, roles)
    - Employee skills with proficiency IDs
    """
    employee: EditBootstrapEmployee = Field(description="Employee data")
    options: EditBootstrapOptions = Field(description="All dropdown options")
    skills: List[EditBootstrapSkill] = Field(description="Employee skills")
    meta: EditBootstrapMeta = Field(description="Response metadata")
