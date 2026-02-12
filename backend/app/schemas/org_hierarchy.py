"""
Pydantic schemas for Org Hierarchy API responses.

Hierarchy: Segment → SubSegment → Project → Team
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TeamNode(BaseModel):
    """Team node in the org hierarchy."""
    team_id: int = Field(description="Team ID")
    team_name: str = Field(description="Team name")

    class Config:
        from_attributes = True


class ProjectNode(BaseModel):
    """Project node in the org hierarchy."""
    project_id: int = Field(description="Project ID")
    project_name: str = Field(description="Project name")
    teams: List[TeamNode] = Field(default_factory=list, description="Teams in this project")

    class Config:
        from_attributes = True


class SubSegmentNode(BaseModel):
    """Sub-segment node in the org hierarchy."""
    sub_segment_id: int = Field(description="Sub-segment ID")
    sub_segment_name: str = Field(description="Sub-segment name")
    projects: List[ProjectNode] = Field(default_factory=list, description="Projects in this sub-segment")

    class Config:
        from_attributes = True


class SegmentNode(BaseModel):
    """Segment node (root) in the org hierarchy."""
    segment_id: int = Field(description="Segment ID")
    segment_name: str = Field(description="Segment name")
    sub_segments: List[SubSegmentNode] = Field(default_factory=list, description="Sub-segments in this segment")

    class Config:
        from_attributes = True


class OrgHierarchyResponse(BaseModel):
    """Response schema for the full org hierarchy."""
    segments: List[SegmentNode] = Field(description="List of segments with nested hierarchy")
    total_segments: int = Field(description="Total number of segments")
    total_sub_segments: int = Field(description="Total number of sub-segments")
    total_projects: int = Field(description="Total number of projects")
    total_teams: int = Field(description="Total number of teams")

    class Config:
        from_attributes = True


# =============================================================================
# Segment CREATE schemas
# =============================================================================

class SegmentCreateRequest(BaseModel):
    """Request schema for creating a new segment."""
    name: str = Field(
        description="Segment name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class SegmentCreateResponse(BaseModel):
    """Response schema for created segment."""
    segment_id: int = Field(description="Segment ID")
    segment_name: str = Field(description="Segment name")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    message: str = Field(default="Segment created successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# SubSegment CREATE schemas
# =============================================================================

class SubSegmentCreateRequest(BaseModel):
    """Request schema for creating a new sub-segment."""
    segment_id: int = Field(
        description="Parent segment ID",
        ge=1
    )
    name: str = Field(
        description="Sub-segment name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class SubSegmentCreateResponse(BaseModel):
    """Response schema for created sub-segment."""
    sub_segment_id: int = Field(description="Sub-segment ID")
    sub_segment_name: str = Field(description="Sub-segment name")
    segment_id: int = Field(description="Parent segment ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    message: str = Field(default="Sub-segment created successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# Segment UPDATE schemas
# =============================================================================

class SegmentUpdateRequest(BaseModel):
    """Request schema for updating a segment."""
    name: str = Field(
        description="New segment name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class SegmentUpdateResponse(BaseModel):
    """Response schema for updated segment."""
    segment_id: int = Field(description="Segment ID")
    segment_name: str = Field(description="Updated segment name")
    message: str = Field(default="Segment updated successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# SubSegment UPDATE schemas
# =============================================================================

class SubSegmentUpdateRequest(BaseModel):
    """Request schema for updating a sub-segment."""
    name: str = Field(
        description="New sub-segment name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class SubSegmentUpdateResponse(BaseModel):
    """Response schema for updated sub-segment."""
    sub_segment_id: int = Field(description="Sub-segment ID")
    sub_segment_name: str = Field(description="Updated sub-segment name")
    segment_id: int = Field(description="Parent segment ID")
    message: str = Field(default="Sub-segment updated successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# DELETE schemas (dependency conflict response)
# =============================================================================

class DependencyConflictResponse(BaseModel):
    """
    Response schema when deletion fails due to existing dependencies.
    Used for 409 Conflict responses.
    """
    message: str = Field(
        description="Error message explaining why deletion failed"
    )
    dependencies: dict = Field(
        description="Dictionary of dependency counts by type"
    )


# =============================================================================
# Project CREATE schemas
# =============================================================================

class ProjectCreateRequest(BaseModel):
    """Request schema for creating a new project."""
    sub_segment_id: int = Field(
        description="Parent sub-segment ID",
        ge=1
    )
    name: str = Field(
        description="Project name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    description: Optional[str] = Field(
        default=None,
        description="Project description (optional)",
        max_length=1000
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class ProjectCreateResponse(BaseModel):
    """Response schema for created project."""
    project_id: int = Field(description="Project ID")
    project_name: str = Field(description="Project name")
    sub_segment_id: int = Field(description="Parent sub-segment ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    message: str = Field(default="Project created successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# Team CREATE schemas
# =============================================================================

class TeamCreateRequest(BaseModel):
    """Request schema for creating a new team."""
    project_id: int = Field(
        description="Parent project ID",
        ge=1
    )
    name: str = Field(
        description="Team name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    description: Optional[str] = Field(
        default=None,
        description="Team description (optional)",
        max_length=1000
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class TeamCreateResponse(BaseModel):
    """Response schema for created team."""
    team_id: int = Field(description="Team ID")
    team_name: str = Field(description="Team name")
    project_id: int = Field(description="Parent project ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    message: str = Field(default="Team created successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# Project UPDATE schemas
# =============================================================================

class ProjectUpdateRequest(BaseModel):
    """Request schema for updating a project."""
    name: str = Field(
        description="New project name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class ProjectUpdateResponse(BaseModel):
    """Response schema for updated project."""
    project_id: int = Field(description="Project ID")
    project_name: str = Field(description="Updated project name")
    sub_segment_id: int = Field(description="Parent sub-segment ID")
    message: str = Field(default="Project updated successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# Team UPDATE schemas
# =============================================================================

class TeamUpdateRequest(BaseModel):
    """Request schema for updating a team."""
    name: str = Field(
        description="New team name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('name cannot be empty')
        return v


class TeamUpdateResponse(BaseModel):
    """Response schema for updated team."""
    team_id: int = Field(description="Team ID")
    team_name: str = Field(description="Updated team name")
    project_id: int = Field(description="Parent project ID")
    message: str = Field(default="Team updated successfully", description="Success message")
    
    class Config:
        from_attributes = True
