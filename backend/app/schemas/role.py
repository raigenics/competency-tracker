"""
Role-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base role schema with common fields."""
    role_name: str = Field(..., max_length=100, description="Role/designation name")
    role_alias: Optional[str] = Field(default=None, description="Comma-separated alias names")
    role_description: Optional[str] = Field(default=None, max_length=500, description="Role description")


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    pass


class RoleResponse(RoleBase):
    """Response schema for role data."""
    role_id: int = Field(description="Role ID")
    
    class Config:
        from_attributes = True
