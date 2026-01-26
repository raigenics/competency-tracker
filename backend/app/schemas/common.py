"""
Common Pydantic schemas for pagination and shared response structures.
"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Parameters for pagination."""
    page: int = Field(default=1, ge=1, description="Page number starting from 1")
    size: int = Field(default=50, ge=1, le=1000, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T] = Field(description="List of items for the current page")
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page") 
    pages: int = Field(description="Total number of pages")
    
    @classmethod
    def create(cls, items: List[T], total: int, pagination: PaginationParams):
        """Create a paginated response."""
        pages = (total + pagination.size - 1) // pagination.size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )


class StatusResponse(BaseModel):
    """Standard status response model."""
    status: str = Field(description="Status of the operation")
    message: Optional[str] = Field(default=None, description="Optional message")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error type or code")
    message: str = Field(description="Human-readable error message")
    details: Optional[dict] = Field(default=None, description="Additional error details")
