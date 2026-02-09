"""
Models package - all database models for the Competency Tracking System.

Import order is important for foreign key dependencies:
1. Master/Dimension tables (no dependencies)
2. Master tables with dependencies 
3. Fact tables (depend on master tables)
"""

# Master/Dimension tables (no dependencies)
from app.models.segment import Segment
from app.models.sub_segment import SubSegment
from app.models.category import SkillCategory
from app.models.proficiency import ProficiencyLevel
from app.models.role import Role

# Master tables with dependencies
from app.models.project import Project
from app.models.team import Team
from app.models.subcategory import SkillSubcategory
from app.models.skill import Skill

# Fact tables (volatile - wiped and replaced on import)
from app.models.employee import Employee
from app.models.employee_skill import EmployeeSkill

# Allocation tables (future staffing and availability)
from app.models.employee_project_allocation import EmployeeProjectAllocation

# History/Audit tables (permanent - track changes over time)
from app.models.skill_history import EmployeeSkillHistory, ProficiencyChangeHistory, ChangeAction, ChangeSource

# Skill normalization and tracking tables
from app.models.raw_skill_input import RawSkillInput
from app.models.skill_alias import SkillAlias

# Skill embeddings for semantic search
from app.models.skill_embedding import SkillEmbedding

# Import job tracking
from app.models.import_job import ImportJob

# RBAC (Role-Based Access Control) - Authentication and Authorization
from app.models.auth import (
    User,
    UserEmployeeLink,
    AuthRole,
    AuthPermission,
    AuthRolePermission,
    AuthScopeType,
    AuthUserScopeRole,
    AuthAuditLog,
)

__all__ = [
    # Master/Dimension tables
    "Segment",
    "SubSegment",
    "SkillCategory", 
    "ProficiencyLevel",
    "Role",
    
    # Master tables with dependencies
    "Project",
    "Team",
    "SkillSubcategory",
    "Skill",
    
    # Fact tables
    "Employee",
    "EmployeeSkill",
    
    # History/Audit tables
    "EmployeeSkillHistory",
    "ProficiencyChangeHistory", 
    "ChangeAction",
    "ChangeSource",
    
    # Skill normalization and tracking tables
    "RawSkillInput",
    "SkillAlias",
    
    # Skill embeddings
    "SkillEmbedding",
    
    # Import job tracking
    "ImportJob",
    
    # RBAC (Role-Based Access Control)
    "User",
    "UserEmployeeLink",
    "AuthRole",
    "AuthPermission",
    "AuthRolePermission",
    "AuthScopeType",
    "AuthUserScopeRole",
    "AuthAuditLog",
]
