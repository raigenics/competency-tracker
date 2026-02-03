"""
Skill-related Pydantic schemas.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import PaginatedResponse


class SkillBase(BaseModel):
    """Base skill schema with common fields."""
    skill_name: str = Field(min_length=1, max_length=200, description="Name of the skill")


class SkillCreate(SkillBase):
    """Schema for creating a new skill."""
    category_name: str = Field(description="Name of the skill category")
    subcategory_name: Optional[str] = Field(default=None, description="Name of the skill subcategory")


class CategoryInfo(BaseModel):
    """Category information for skills."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    subcategory_id: Optional[int] = Field(default=None, description="Subcategory ID")
    subcategory_name: Optional[str] = Field(default=None, description="Subcategory name")


class SkillResponse(SkillBase):
    """Response schema for skill data."""
    skill_id: int = Field(description="Skill ID")
    category: CategoryInfo = Field(description="Category information")
    employee_count: int = Field(description="Number of employees with this skill")
    
    class Config:
        from_attributes = True


class SkillListResponse(PaginatedResponse[SkillResponse]):
    """Paginated response for skill list."""
    pass


class SkillDetailResponse(SkillResponse):
    """Detailed skill response with employee proficiency distribution."""
    proficiency_distribution: dict = Field(description="Distribution of employees by proficiency level")
    avg_years_experience: Optional[float] = Field(description="Average years of experience")
    avg_interest_level: Optional[float] = Field(description="Average interest level")


class SkillStatsResponse(BaseModel):
    """Skill statistics response."""
    total_skills: int = Field(description="Total number of skills")
    by_category: dict = Field(description="Skill count by category")
    by_subcategory: dict = Field(description="Skill count by subcategory")
    most_popular_skills: List[dict] = Field(description="Most popular skills by employee count")
    

class CategoryResponse(BaseModel):
    """Response schema for skill categories."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    skill_count: int = Field(description="Number of skills in this category")
    subcategory_count: int = Field(description="Number of subcategories in this category")
    
    class Config:
        from_attributes = True


class SubcategoryResponse(BaseModel):
    """Response schema for skill subcategories."""
    subcategory_id: int = Field(description="Subcategory ID")
    subcategory_name: str = Field(description="Subcategory name")
    category_name: str = Field(description="Parent category name")
    skill_count: int = Field(description="Number of skills in this subcategory")
    
    class Config:
        from_attributes = True


class SkillSummaryResponse(BaseModel):
    """Response schema for skill summary statistics."""
    skill_id: int = Field(description="Skill ID")
    skill_name: str = Field(description="Skill name")
    employee_count: int = Field(description="Number of distinct employees with this skill")
    employee_ids: List[int] = Field(default_factory=list, description="List of employee IDs with this skill")
    avg_experience_years: float = Field(description="Average years of experience for this skill")
    certified_count: int = Field(description="Number of certified employees (backward compatibility)")
    certified_employee_count: int = Field(description="Number of distinct certified employees")
    
    class Config:
        from_attributes = True


class TaxonomySkillItem(BaseModel):
    """Skill item in taxonomy tree."""
    skill_id: int = Field(description="Skill ID from database")
    skill_name: str = Field(description="Skill name")
    
    class Config:
        from_attributes = True


class TaxonomySubcategoryItem(BaseModel):
    """Subcategory item in taxonomy tree."""
    subcategory_id: int = Field(description="Subcategory ID from database")
    subcategory_name: str = Field(description="Subcategory name")
    skills: List[TaxonomySkillItem] = Field(default_factory=list, description="Skills in this subcategory")
    
    class Config:
        from_attributes = True


class TaxonomyCategoryItem(BaseModel):
    """Category item in taxonomy tree."""
    category_id: int = Field(description="Category ID from database")
    category_name: str = Field(description="Category name")
    subcategories: List[TaxonomySubcategoryItem] = Field(default_factory=list, description="Subcategories in this category")
    
    class Config:
        from_attributes = True


class TaxonomyTreeResponse(BaseModel):
    """Complete taxonomy tree response."""
    categories: List[TaxonomyCategoryItem] = Field(description="All categories with nested subcategories and skills")
    
    class Config:
        from_attributes = True


# === Lazy-loading Taxonomy Schemas ===

class CategorySummaryItem(BaseModel):
    """Lightweight category summary for initial load."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    subcategory_count: int = Field(description="Number of subcategories")
    skill_count: int = Field(description="Total number of skills in category")
    
    class Config:
        from_attributes = True


class CategoriesResponse(BaseModel):
    """Response for categories list endpoint."""
    categories: List[CategorySummaryItem] = Field(description="List of categories with counts")
    
    class Config:
        from_attributes = True


class SubcategorySummaryItem(BaseModel):
    """Lightweight subcategory summary for on-demand load."""
    subcategory_id: int = Field(description="Subcategory ID")
    subcategory_name: str = Field(description="Subcategory name")
    skill_count: int = Field(description="Number of skills in subcategory")
    
    class Config:
        from_attributes = True


class SubcategoriesResponse(BaseModel):
    """Response for subcategories list endpoint."""
    category_id: int = Field(description="Parent category ID")
    category_name: str = Field(description="Parent category name")
    subcategories: List[SubcategorySummaryItem] = Field(description="List of subcategories with skill counts")
    
    class Config:
        from_attributes = True


class SkillsResponse(BaseModel):
    """Response for skills list endpoint."""
    subcategory_id: int = Field(description="Parent subcategory ID")
    subcategory_name: str = Field(description="Parent subcategory name")
    category_id: int = Field(description="Parent category ID")
    category_name: str = Field(description="Parent category name")
    skills: List[TaxonomySkillItem] = Field(description="List of skills in subcategory")
    
    class Config:
        from_attributes = True


# === Capability Overview Search Schemas ===

class SkillSearchResultItem(BaseModel):
    """Single skill search result with full hierarchy path."""
    skill_id: int = Field(description="Skill ID")
    skill_name: str = Field(description="Skill name")
    category_id: int = Field(description="Parent category ID")
    category_name: str = Field(description="Parent category name")
    subcategory_id: int = Field(description="Parent subcategory ID")
    subcategory_name: str = Field(description="Parent subcategory name")
    
    class Config:
        from_attributes = True


class SkillSearchResponse(BaseModel):
    """Response for skill search endpoint."""
    results: List[SkillSearchResultItem] = Field(description="List of matching skills with hierarchy")
    count: int = Field(description="Number of results")
    
    class Config:
        from_attributes = True
