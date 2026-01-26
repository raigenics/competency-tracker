"""
Import-related Pydantic schemas for Excel import operations.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ImportStats(BaseModel):
    """Statistics from an import operation."""
    employees_imported: int = Field(description="Number of employees imported")
    skills_imported: int = Field(description="Number of skill records imported")
    new_categories: List[str] = Field(description="New skill categories added")
    new_subcategories: List[str] = Field(description="New skill subcategories added")
    new_skills_added: List[str] = Field(description="New skills added")
    new_projects: List[str] = Field(description="New projects added")
    new_teams: List[str] = Field(description="New teams added")
    new_sub_segments: List[str] = Field(description="New sub-segments added")


class ImportResponse(BaseModel):
    """Response model for import operations."""
    status: str = Field(description="Import status (success/failed)")
    message: Optional[str] = Field(default=None, description="Optional message")
    stats: Optional[ImportStats] = Field(default=None, description="Import statistics")
    

class ImportError(BaseModel):
    """Error details for import failures."""
    error_type: str = Field(description="Type of import error")
    message: str = Field(description="Error message")
    line_number: Optional[int] = Field(default=None, description="Line number where error occurred")
    column_name: Optional[str] = Field(default=None, description="Column name related to error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ImportValidationResponse(BaseModel):
    """Response for import file validation."""
    is_valid: bool = Field(description="Whether the file is valid for import")
    errors: List[ImportError] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    preview: Optional[Dict[str, Any]] = Field(default=None, description="Preview of the data to be imported")
