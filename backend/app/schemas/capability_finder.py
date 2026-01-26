"""
Schemas for Capability Finder (Advanced Query) API.
"""
from typing import List
from pydantic import BaseModel


class SkillListResponse(BaseModel):
    """Response schema for skills list."""
    skills: List[str]


class RoleListResponse(BaseModel):
    """Response schema for roles list."""
    roles: List[str]
