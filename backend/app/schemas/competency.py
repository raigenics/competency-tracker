"""
Competency-related Pydantic schemas for employee skills and proficiency.
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from app.schemas.role import RoleResponse


class ProficiencyLevelResponse(BaseModel):
    """Response schema for proficiency levels."""
    proficiency_level_id: int = Field(description="Proficiency level ID")
    level_name: str = Field(description="Proficiency level name")
    level_description: Optional[str] = Field(description="Proficiency level description")
    
    class Config:
        from_attributes = True


class EmployeeSkillBase(BaseModel):
    """Base employee skill schema."""
    years_experience: Optional[int] = Field(default=None, ge=0, description="Years of experience with the skill")
    last_used: Optional[date] = Field(default=None, description="Last date the skill was used")
    interest_level: Optional[int] = Field(default=None, ge=1, le=5, description="Interest level in the skill (1-5)")
    last_updated: Optional[datetime] = Field(default=None, description="When this skill record was last updated")


class EmployeeSkillCreate(EmployeeSkillBase):
    """Schema for creating employee skill records."""
    employee_id: int = Field(description="Employee ID")
    skill_id: int = Field(description="Skill ID")
    proficiency_level_id: int = Field(description="Proficiency level ID")


class EmployeeSkillResponse(EmployeeSkillBase):
    """Response schema for employee skill data."""
    emp_skill_id: int = Field(description="Employee skill record ID")
    employee_id: int = Field(description="Employee ID")
    employee_name: str = Field(description="Employee name")
    skill_id: int = Field(description="Skill ID")
    skill_name: str = Field(description="Skill name")
    category: Optional[str] = Field(default=None, description="Skill category name")
    proficiency: ProficiencyLevelResponse = Field(description="Proficiency level details")
    certification: Optional[str] = Field(default=None, description="Certification name or details")
    
    class Config:
        from_attributes = True


class CompetencyGapAnalysis(BaseModel):
    """Competency gap analysis result."""
    skill_name: str = Field(description="Skill name")
    required_proficiency: str = Field(description="Required proficiency level")
    current_proficiency: Optional[str] = Field(description="Current proficiency level")
    gap_severity: str = Field(description="Gap severity (Critical, High, Medium, Low)")
    recommended_action: str = Field(description="Recommended action")


class EmployeeCompetencyProfile(BaseModel):
    """Complete competency profile for an employee."""
    employee_id: int = Field(description="Employee ID")
    employee_name: str = Field(description="Employee name")
    role: Optional[RoleResponse] = Field(description="Employee role")
    start_date_of_working: Optional[date] = Field(None, description="Start date of employment")
    organization: Dict[str, str] = Field(description="Organization structure")
    skills: List[EmployeeSkillResponse] = Field(description="Employee skills")
    competency_summary: Dict[str, int] = Field(description="Competency summary by proficiency level")
    top_skills: List[Dict[str, Any]] = Field(description="Top skills by proficiency and experience")


class CompetencyMatrixResponse(BaseModel):
    """Competency matrix response for teams or organizations."""
    matrix_name: str = Field(description="Name of the competency matrix")
    scope: Dict[str, str] = Field(description="Scope of the matrix (team, project, etc.)")
    employees: List[EmployeeCompetencyProfile] = Field(description="Employee profiles")
    skill_coverage: Dict[str, Dict[str, int]] = Field(description="Skill coverage by proficiency level")
    gap_analysis: List[CompetencyGapAnalysis] = Field(description="Competency gap analysis")
    recommendations: List[str] = Field(description="Recommendations for skill development")


class SkillDemandResponse(BaseModel):
    """Response for skill demand analysis."""
    skill_name: str = Field(description="Skill name")
    total_employees: int = Field(description="Total employees with this skill")
    proficiency_breakdown: Dict[str, int] = Field(description="Breakdown by proficiency level")
    avg_experience: Optional[float] = Field(description="Average years of experience")
    avg_interest: Optional[float] = Field(description="Average interest level")
    trend: str = Field(description="Skill trend (Growing, Stable, Declining)")


class CompetencyInsights(BaseModel):
    """High-level competency insights."""
    total_skills: int = Field(description="Total unique skills")
    total_assessments: int = Field(description="Total skill assessments")
    skill_gaps: List[str] = Field(description="Identified skill gaps")
    strongest_skills: List[str] = Field(description="Organization's strongest skills")
    emerging_skills: List[str] = Field(description="Emerging skills gaining popularity")
    recommendations: List[str] = Field(description="Strategic recommendations")


class CompetencySearchFilters(BaseModel):
    """Filters for competency search."""
    skill_names: Optional[List[str]] = Field(default=None, description="Filter by skill names")
    categories: Optional[List[str]] = Field(default=None, description="Filter by categories")
    subcategories: Optional[List[str]] = Field(default=None, description="Filter by subcategories")
    proficiency_levels: Optional[List[str]] = Field(default=None, description="Filter by proficiency levels")
    min_experience: Optional[int] = Field(default=None, ge=0, description="Minimum years of experience")
    min_interest: Optional[int] = Field(default=None, ge=1, le=5, description="Minimum interest level")
    sub_segments: Optional[List[str]] = Field(default=None, description="Filter by sub-segments")
    projects: Optional[List[str]] = Field(default=None, description="Filter by projects")
    teams: Optional[List[str]] = Field(default=None, description="Filter by teams")
