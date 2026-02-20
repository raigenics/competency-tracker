"""
Custom exceptions for Master Data operations.

Provides clean exception types that are converted to HTTP responses at the router level.
"""


class MasterDataError(Exception):
    """Base exception for master data operations."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(MasterDataError):
    """Entity not found exception."""
    
    def __init__(self, entity_type: str, entity_id: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            message=f"{entity_type} with id {entity_id} not found",
            details={"entity_type": entity_type, "entity_id": entity_id}
        )


class ConflictError(MasterDataError):
    """Duplicate/conflict exception for uniqueness violations."""
    
    def __init__(self, entity_type: str, field: str, value: str, scope: str = None):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        self.scope = scope
        
        if scope:
            msg = f"{entity_type} with {field} '{value}' already exists in {scope}"
        else:
            msg = f"{entity_type} with {field} '{value}' already exists"
        
        super().__init__(
            message=msg,
            details={
                "entity_type": entity_type,
                "field": field,
                "value": value,
                "scope": scope
            }
        )


class ValidationError(MasterDataError):
    """Input validation exception."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(
            message=message,
            details={"field": field}
        )


class EmbeddingError(MasterDataError):
    """Embedding generation/persistence exception."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            details={"error_type": "embedding"}
        )
