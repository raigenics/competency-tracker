"""
Schemas for Master Skills Import API endpoint.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ImportSummaryCount(BaseModel):
    """Summary counts for a single entity type."""
    inserted: int = Field(default=0, description="Number of new records inserted")
    existing: int = Field(default=0, description="Number of records that already existed")
    conflicts: int = Field(default=0, description="Number of conflicts detected")


class ImportSummary(BaseModel):
    """Overall import summary statistics."""
    rows_total: int = Field(description="Total rows in the Excel file")
    rows_processed: int = Field(description="Number of rows processed")
    categories: ImportSummaryCount
    subcategories: ImportSummaryCount
    skills: ImportSummaryCount
    aliases: ImportSummaryCount


class EmbeddingStatus(BaseModel):
    """Status of embedding generation during import."""
    enabled: bool = Field(description="Whether embedding service is available")
    attempted: bool = Field(description="Whether embedding generation was attempted")
    succeeded_count: int = Field(default=0, description="Number of embeddings successfully created/updated")
    skipped_count: int = Field(default=0, description="Number of embeddings skipped (already up-to-date)")
    failed_count: int = Field(default=0, description="Number of embeddings that failed to generate")
    reason: Optional[str] = Field(None, description="Reason if embeddings were not attempted or service disabled")


class ImportError(BaseModel):
    """Details of a single import error or conflict."""
    row_number: Optional[int] = Field(None, description="1-based row number in Excel file (None for embedding errors)")
    category: Optional[str] = Field(None, description="Category from the row")
    subcategory: Optional[str] = Field(None, description="Subcategory from the row")
    skill_name: Optional[str] = Field(None, description="Skill name from the row")
    alias: Optional[str] = Field(None, description="Specific alias that caused conflict")
    error_type: str = Field(
        description="Error type: VALIDATION_ERROR, SKILL_SUBCATEGORY_CONFLICT, ALIAS_CONFLICT, DUPLICATE_IN_FILE, EMBEDDING_GENERATION_FAILED"
    )
    message: str = Field(description="Human-readable error message")
    existing: Optional[Dict[str, Any]] = Field(None, description="Existing record details if applicable")
    attempted: Optional[Dict[str, Any]] = Field(None, description="Attempted values if applicable")


class MasterImportResponse(BaseModel):
    """Response model for master skills import endpoint."""
    status: str = Field(
        description="Import status: success, partial_success, or failed"
    )
    summary: ImportSummary
    errors: List[ImportError] = Field(default_factory=list)
    embedding_status: Optional[EmbeddingStatus] = Field(None, description="Status of embedding generation")
