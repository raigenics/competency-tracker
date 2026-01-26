"""
Pydantic schemas package for the Competency Tracking System.
Contains request and response models for the API.
"""

from app.schemas.employee import (
    EmployeeBase, EmployeeCreate, EmployeeResponse, EmployeeListResponse
)
from app.schemas.role import (
    RoleBase, RoleCreate, RoleResponse
)
from app.schemas.skill import (
    SkillBase, SkillCreate, SkillResponse, SkillListResponse
)
from app.schemas.competency import (
    EmployeeSkillBase, EmployeeSkillCreate, EmployeeSkillResponse,
    CompetencyMatrixResponse
)
from app.schemas.import_schema import (
    ImportResponse, ImportStats, ImportError
)
from app.schemas.common import (
    PaginationParams, PaginatedResponse
)

__all__ = [
    # Employee schemas
    "EmployeeBase", "EmployeeCreate", "EmployeeResponse", "EmployeeListResponse",
    
    # Role schemas
    "RoleBase", "RoleCreate", "RoleResponse",
    
    # Skill schemas  
    "SkillBase", "SkillCreate", "SkillResponse", "SkillListResponse",
    
    # Competency schemas
    "EmployeeSkillBase", "EmployeeSkillCreate", "EmployeeSkillResponse", 
    "CompetencyMatrixResponse",
    
    # Import schemas
    "ImportResponse", "ImportStats", "ImportError",
    
    # Common schemas
    "PaginationParams", "PaginatedResponse",
]
