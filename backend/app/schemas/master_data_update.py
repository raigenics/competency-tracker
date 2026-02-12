"""
Pydantic schemas for Master Data update (PATCH) operations.

Each entity has:
- UpdateRequest: Input DTO with optional fields for partial updates
- UpdateResponse: Output DTO returning updated entity state
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CategoryUpdateRequest(BaseModel):
    """Request schema for updating a category."""
    category_name: Optional[str] = Field(
        default=None,
        description="New category name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('category_name')
    @classmethod
    def validate_category_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('category_name cannot be empty')
        return v


class CategoryUpdateResponse(BaseModel):
    """Response schema for updated category."""
    id: int = Field(description="Category ID")
    name: str = Field(description="Category name")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    
    class Config:
        from_attributes = True


class SubcategoryUpdateRequest(BaseModel):
    """Request schema for updating a subcategory."""
    subcategory_name: Optional[str] = Field(
        default=None,
        description="New subcategory name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('subcategory_name')
    @classmethod
    def validate_subcategory_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('subcategory_name cannot be empty')
        return v


class SubcategoryUpdateResponse(BaseModel):
    """Response schema for updated subcategory."""
    id: int = Field(description="Subcategory ID")
    name: str = Field(description="Subcategory name")
    category_id: int = Field(description="Parent category ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    
    class Config:
        from_attributes = True


class SkillUpdateRequest(BaseModel):
    """Request schema for updating a skill."""
    skill_name: Optional[str] = Field(
        default=None,
        description="New skill name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('skill_name')
    @classmethod
    def validate_skill_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('skill_name cannot be empty')
        return v


class SkillUpdateResponse(BaseModel):
    """Response schema for updated skill."""
    id: int = Field(description="Skill ID")
    name: str = Field(description="Skill name")
    subcategory_id: int = Field(description="Parent subcategory ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    
    class Config:
        from_attributes = True


class AliasUpdateRequest(BaseModel):
    """Request schema for updating a skill alias."""
    alias_text: Optional[str] = Field(
        default=None,
        description="New alias text (will be trimmed)",
        min_length=1,
        max_length=255
    )
    # Optional fields for future extensibility
    source: Optional[str] = Field(
        default=None,
        description="Source of the alias",
        max_length=50
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Confidence score for the alias",
        ge=0.0,
        le=1.0
    )
    
    @field_validator('alias_text')
    @classmethod
    def validate_alias_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('alias_text cannot be empty')
        return v


class AliasUpdateResponse(BaseModel):
    """Response schema for updated skill alias."""
    id: int = Field(description="Alias ID")
    alias_text: str = Field(description="Alias text")
    skill_id: int = Field(description="Associated skill ID")
    source: str = Field(description="Source of the alias")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    
    class Config:
        from_attributes = True


# =============================================================================
# Alias CREATE schemas
# =============================================================================

class AliasCreateRequest(BaseModel):
    """Request schema for creating a new skill alias."""
    alias_text: str = Field(
        description="Alias text (will be trimmed)",
        min_length=1,
        max_length=255
    )
    source: str = Field(
        default="manual",
        description="Source of the alias (e.g., 'manual', 'import')",
        max_length=50
    )
    confidence_score: Optional[float] = Field(
        default=1.0,
        description="Confidence score for the alias",
        ge=0.0,
        le=1.0
    )
    
    @field_validator('alias_text')
    @classmethod
    def validate_alias_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('alias_text cannot be empty')
        return v


class AliasCreateResponse(BaseModel):
    """Response schema for created skill alias."""
    id: int = Field(description="Alias ID")
    alias_text: str = Field(description="Alias text")
    skill_id: int = Field(description="Associated skill ID")
    source: str = Field(description="Source of the alias")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")
    message: str = Field(default="Alias created successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# Category CREATE schemas
# =============================================================================

class CategoryCreateRequest(BaseModel):
    """Request schema for creating a new category."""
    category_name: str = Field(
        description="Category name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('category_name')
    @classmethod
    def validate_category_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('category_name cannot be empty')
        return v


class CategoryCreateResponse(BaseModel):
    """Response schema for created category."""
    id: int = Field(description="Category ID")
    name: str = Field(description="Category name")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    message: str = Field(default="Category created successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# Subcategory CREATE schemas
# =============================================================================

class SubcategoryCreateRequest(BaseModel):
    """Request schema for creating a new subcategory."""
    subcategory_name: str = Field(
        description="Subcategory name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    
    @field_validator('subcategory_name')
    @classmethod
    def validate_subcategory_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('subcategory_name cannot be empty')
        return v


class SubcategoryCreateResponse(BaseModel):
    """Response schema for created subcategory."""
    id: int = Field(description="Subcategory ID")
    name: str = Field(description="Subcategory name")
    category_id: int = Field(description="Parent category ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    message: str = Field(default="Subcategory created successfully", description="Success message")
    
    class Config:
        from_attributes = True


# =============================================================================
# Skill CREATE schemas
# =============================================================================

class SkillCreateRequest(BaseModel):
    """Request schema for creating a new skill with optional aliases."""
    skill_name: str = Field(
        description="Skill name (will be trimmed)",
        min_length=1,
        max_length=255
    )
    alias_text: Optional[str] = Field(
        default=None,
        description="Optional comma-separated alias texts for the skill (e.g., 'alias1, alias2')",
        max_length=1000
    )
    
    @field_validator('skill_name')
    @classmethod
    def validate_skill_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('skill_name cannot be empty')
        return v
    
    @field_validator('alias_text')
    @classmethod
    def validate_alias_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None  # Treat empty string as no alias
        return v


class SkillCreateResponse(BaseModel):
    """Response schema for created skill."""
    id: int = Field(description="Skill ID")
    name: str = Field(description="Skill name")
    subcategory_id: int = Field(description="Parent subcategory ID")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    aliases: list[AliasCreateResponse] = Field(default_factory=list, description="Created aliases if provided")
    message: str = Field(default="Skill created successfully", description="Success message")
    
    class Config:
        from_attributes = True