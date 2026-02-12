"""
Pydantic schemas for Master Data - Skill Taxonomy API.
Read-only hierarchical response: Categories -> SubCategories -> Skills
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TaxonomyAliasDTO(BaseModel):
    """Alias item for a skill."""
    id: int = Field(description="Alias ID")
    text: str = Field(description="Alias text")
    source: Optional[str] = Field(default=None, description="Source of the alias")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")

    class Config:
        from_attributes = True


class TaxonomySkillDTO(BaseModel):
    """Skill item in taxonomy hierarchy."""
    id: int = Field(description="Skill ID")
    name: str = Field(description="Skill name")
    description: Optional[str] = Field(default=None, description="Skill description")
    employee_count: int = Field(default=0, description="Number of employees with this skill")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    aliases: List[TaxonomyAliasDTO] = Field(default_factory=list, description="Skill aliases")

    class Config:
        from_attributes = True


class TaxonomySubCategoryDTO(BaseModel):
    """SubCategory item with nested skills."""
    id: int = Field(description="SubCategory ID")
    name: str = Field(description="SubCategory name")
    description: Optional[str] = Field(default=None, description="SubCategory description")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    skills: List[TaxonomySkillDTO] = Field(default_factory=list, description="Skills in this subcategory")

    class Config:
        from_attributes = True


class TaxonomyCategoryDTO(BaseModel):
    """Category item with nested subcategories."""
    id: int = Field(description="Category ID")
    name: str = Field(description="Category name")
    description: Optional[str] = Field(default=None, description="Category description")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator username")
    subcategories: List[TaxonomySubCategoryDTO] = Field(default_factory=list, description="Subcategories in this category")

    class Config:
        from_attributes = True


class SkillTaxonomyResponse(BaseModel):
    """Response schema for the full skill taxonomy hierarchy."""
    categories: List[TaxonomyCategoryDTO] = Field(description="List of categories with nested hierarchy")
    total_categories: int = Field(description="Total number of categories")
    total_subcategories: int = Field(description="Total number of subcategories")
    total_skills: int = Field(description="Total number of skills")

    class Config:
        from_attributes = True
