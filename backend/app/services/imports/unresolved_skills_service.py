"""
Service for resolving unmatched skills from Employee Bulk Import.

Provides:
- GET endpoint: List unresolved skills for an import run with suggestions
- POST endpoint: Map raw skill to existing skill and create alias
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.raw_skill_input import RawSkillInput
from app.models.import_job import ImportJob
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.models.employee import Employee
from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator
from app.utils.normalization import normalize_skill_name


logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class SkillSuggestion(BaseModel):
    """A suggested skill match for an unresolved skill."""
    skill_id: int
    skill_name: str
    category: str
    subcategory: str
    match_type: str = Field(description="'exact', 'alias', or 'embedding'")
    confidence: float = Field(ge=0.0, le=1.0, description="Match confidence (0.0-1.0)")


class UnresolvedSkillItem(BaseModel):
    """An unresolved skill from an import run."""
    raw_skill_id: int
    raw_text: str
    normalized_text: str
    employee_name: Optional[str] = None
    employee_zid: Optional[str] = None
    suggestions: List[SkillSuggestion] = []


class UnresolvedSkillsResponse(BaseModel):
    """Response for GET unresolved skills endpoint."""
    import_run_id: str
    total_count: int
    unresolved_skills: List[UnresolvedSkillItem]


class ResolveSkillRequest(BaseModel):
    """Request body for POST resolve endpoint."""
    raw_skill_id: int = Field(description="ID of the raw_skill_input to resolve")
    target_skill_id: int = Field(description="ID of the master skill to map to")


class ResolveSkillResponse(BaseModel):
    """Response for POST resolve endpoint."""
    raw_skill_id: int
    resolved_skill_id: int
    alias_created: bool
    alias_text: str
    message: str


class SingleSkillSuggestionsResponse(BaseModel):
    """Response for GET single skill suggestions endpoint."""
    raw_skill_id: int
    raw_text: str
    normalized_text: str
    employee_name: Optional[str] = None
    employee_zid: Optional[str] = None
    suggestions: List[SkillSuggestion] = []


# =============================================================================
# EXCEPTIONS
# =============================================================================

class UnresolvedSkillError(Exception):
    """Base exception for unresolved skill operations."""
    pass


class ImportJobNotFoundError(UnresolvedSkillError):
    """Import job not found."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Import job '{job_id}' not found")


class RawSkillNotFoundError(UnresolvedSkillError):
    """Raw skill input not found."""
    def __init__(self, raw_skill_id: int):
        self.raw_skill_id = raw_skill_id
        super().__init__(f"Raw skill input {raw_skill_id} not found")


class SkillNotFoundError(UnresolvedSkillError):
    """Target skill not found."""
    def __init__(self, skill_id: int):
        self.skill_id = skill_id
        super().__init__(f"Skill {skill_id} not found")


class AlreadyResolvedError(UnresolvedSkillError):
    """Raw skill is already resolved."""
    def __init__(self, raw_skill_id: int):
        self.raw_skill_id = raw_skill_id
        super().__init__(f"Raw skill input {raw_skill_id} is already resolved")


class AliasAlreadyExistsError(UnresolvedSkillError):
    """Alias already maps to a different skill."""
    def __init__(self, alias_text: str, existing_skill_id: int, existing_skill_name: str):
        self.alias_text = alias_text
        self.existing_skill_id = existing_skill_id
        self.existing_skill_name = existing_skill_name
        super().__init__(
            f"Alias '{alias_text}' already exists for skill '{existing_skill_name}' (ID: {existing_skill_id})"
        )


# =============================================================================
# GET SINGLE SKILL SUGGESTIONS
# =============================================================================

def get_single_skill_suggestions(
    db: Session,
    import_run_id: str,
    raw_skill_id: int,
    max_suggestions: int = 10,
    include_embeddings: bool = True
) -> SingleSkillSuggestionsResponse:
    """
    Get suggestions for a SINGLE unresolved skill by raw_skill_id.
    
    This is optimized for the modal use case - fetches suggestions for
    only one skill instead of all unresolved skills.
    
    Args:
        db: Database session
        import_run_id: The import job UUID
        raw_skill_id: ID of the specific raw_skill_input
        max_suggestions: Maximum number of suggestions (default: 10)
        include_embeddings: Whether to include embedding-based suggestions (default: True)
        
    Returns:
        SingleSkillSuggestionsResponse with suggestions for this one skill
        
    Raises:
        ImportJobNotFoundError: If import job not found
        RawSkillNotFoundError: If raw skill input not found
    """
    logger.info(f"Getting suggestions for raw_skill_id={raw_skill_id} in job {import_run_id}")
    
    # Verify import job exists
    job = db.query(ImportJob).filter(ImportJob.job_id == import_run_id).first()
    if not job:
        raise ImportJobNotFoundError(import_run_id)
    
    # Get the specific raw_skill_input
    raw_skill = db.query(RawSkillInput).filter(
        RawSkillInput.raw_skill_id == raw_skill_id,
        RawSkillInput.job_id == import_run_id
    ).first()
    
    if not raw_skill:
        raise RawSkillNotFoundError(raw_skill_id)
    
    # Get employee info
    employee_name = None
    employee_zid = None
    if raw_skill.employee_id:
        employee = db.query(Employee).filter(
            Employee.employee_id == raw_skill.employee_id
        ).first()
        if employee:
            employee_name = employee.full_name
            employee_zid = employee.zid
    
    # Get suggestions (using existing logic)
    suggestions = []
    try:
        suggestions = _get_suggestions(
            db, 
            raw_skill.normalized_text, 
            max_suggestions,
            include_embeddings=include_embeddings
        )
    except Exception as e:
        logger.warning(f"Failed to get suggestions for raw_skill_id={raw_skill_id}: {e}")
        suggestions = []
    
    return SingleSkillSuggestionsResponse(
        raw_skill_id=raw_skill.raw_skill_id,
        raw_text=raw_skill.raw_text,
        normalized_text=raw_skill.normalized_text,
        employee_name=employee_name,
        employee_zid=employee_zid,
        suggestions=suggestions
    )


# =============================================================================
# GET UNRESOLVED SKILLS
# =============================================================================

def get_unresolved_skills(
    db: Session,
    import_run_id: str,
    include_suggestions: bool = True,
    max_suggestions: int = 5
) -> UnresolvedSkillsResponse:
    """
    Get all unresolved skills for an import run with optional suggestions.
    
    Args:
        db: Database session
        import_run_id: The import job UUID
        include_suggestions: Whether to include skill suggestions
        max_suggestions: Maximum number of suggestions per skill
        
    Returns:
        UnresolvedSkillsResponse with all unresolved skills and suggestions
        
    Raises:
        ImportJobNotFoundError: If import job not found
    """
    logger.info(f"Getting unresolved skills for import run: {import_run_id}")
    
    # Verify import job exists
    job = db.query(ImportJob).filter(ImportJob.job_id == import_run_id).first()
    if not job:
        raise ImportJobNotFoundError(import_run_id)
    
    # Get all UNRESOLVED raw_skill_inputs for this job
    raw_skills = db.query(RawSkillInput).filter(
        RawSkillInput.job_id == import_run_id,
        RawSkillInput.status == "UNRESOLVED"
    ).all()
    
    logger.info(f"Found {len(raw_skills)} unresolved skills for job {import_run_id}")
    
    # Build response items
    items = []
    for raw_skill in raw_skills:
        # Get employee info
        employee_name = None
        employee_zid = None
        if raw_skill.employee_id:
            employee = db.query(Employee).filter(
                Employee.employee_id == raw_skill.employee_id
            ).first()
            if employee:
                employee_name = employee.full_name
                employee_zid = employee.zid
        
        # Get suggestions (fail-safe - return empty suggestions on error)
        suggestions = []
        if include_suggestions:
            try:
                suggestions = _get_suggestions(
                    db, raw_skill.normalized_text, max_suggestions
                )
            except Exception as e:
                # Suggestions are optional - log and continue with empty list
                logger.warning(f"Failed to get suggestions for '{raw_skill.raw_text}': {e}")
                suggestions = []
        
        items.append(UnresolvedSkillItem(
            raw_skill_id=raw_skill.raw_skill_id,
            raw_text=raw_skill.raw_text,
            normalized_text=raw_skill.normalized_text,
            employee_name=employee_name,
            employee_zid=employee_zid,
            suggestions=suggestions
        ))
    
    return UnresolvedSkillsResponse(
        import_run_id=import_run_id,
        total_count=len(items),
        unresolved_skills=items
    )


def _get_suggestions(
    db: Session,
    normalized_text: str,
    max_suggestions: int = 5,
    include_embeddings: bool = True
) -> List[SkillSuggestion]:
    """
    Get skill suggestions for an unresolved skill text.
    
    Priority:
    1. Exact name match (highest confidence)
    2. Alias match
    3. Embedding similarity (if available and include_embeddings=True)
    
    Args:
        db: Database session
        normalized_text: Normalized skill text to match
        max_suggestions: Maximum number of suggestions to return
        include_embeddings: Whether to include embedding-based suggestions (default: True)
        
    Returns:
        List of SkillSuggestion ordered by confidence
    """
    suggestions = []
    seen_skill_ids = set()
    
    # 1. Try exact name match (normalized)
    exact_match = db.query(Skill).join(
        SkillSubcategory, Skill.subcategory_id == SkillSubcategory.subcategory_id
    ).join(
        SkillCategory, SkillSubcategory.category_id == SkillCategory.category_id
    ).filter(
        func.lower(func.trim(Skill.skill_name)) == normalized_text.lower()
    ).first()
    
    if exact_match:
        suggestions.append(SkillSuggestion(
            skill_id=exact_match.skill_id,
            skill_name=exact_match.skill_name,
            category=exact_match.subcategory.category.category_name,
            subcategory=exact_match.subcategory.subcategory_name,
            match_type="exact",
            confidence=1.0
        ))
        seen_skill_ids.add(exact_match.skill_id)
    
    # 2. Try alias match
    alias_matches = db.query(SkillAlias).join(
        Skill, SkillAlias.skill_id == Skill.skill_id
    ).join(
        SkillSubcategory, Skill.subcategory_id == SkillSubcategory.subcategory_id
    ).join(
        SkillCategory, SkillSubcategory.category_id == SkillCategory.category_id
    ).filter(
        func.lower(func.trim(SkillAlias.alias_text)) == normalized_text.lower()
    ).all()
    
    for alias in alias_matches:
        if alias.skill_id not in seen_skill_ids:
            skill = alias.skill
            suggestions.append(SkillSuggestion(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name,
                category=skill.subcategory.category.category_name,
                subcategory=skill.subcategory.subcategory_name,
                match_type="alias",
                confidence=alias.confidence_score or 0.95
            ))
            seen_skill_ids.add(skill.skill_id)
    
    # 3. Try embedding similarity (if pgvector available and enabled)
    # Only do embedding search if we don't have enough suggestions
    if include_embeddings and len(suggestions) < max_suggestions:
        try:
            embedding_suggestions = _get_embedding_suggestions(
                db, normalized_text, 
                max_results=max_suggestions - len(suggestions),
                exclude_skill_ids=seen_skill_ids
            )
            suggestions.extend(embedding_suggestions)
        except Exception as e:
            # Embedding search is optional - log and continue
            logger.debug(f"Embedding search not available: {e}")
    
    # Sort by confidence and limit
    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    return suggestions[:max_suggestions]


def _get_embedding_suggestions(
    db: Session,
    text: str,
    max_results: int = 5,
    exclude_skill_ids: set = None,
    min_similarity: float = 0.5
) -> List[SkillSuggestion]:
    """
    Get skill suggestions using pgvector embedding similarity.
    
    This is an optional feature that gracefully fails if:
    - pgvector extension not installed
    - skill_embeddings table doesn't exist
    - Embedding service not configured
    
    Args:
        db: Database session
        text: Text to find similar skills for
        max_results: Maximum results to return
        exclude_skill_ids: Skill IDs to exclude from results
        min_similarity: Minimum similarity threshold
        
    Returns:
        List of SkillSuggestion with embedding match type
    """
    exclude_skill_ids = exclude_skill_ids or set()
    suggestions = []
    
    try:
        # Import embedding provider - this may not be available or configured
        from app.services.skill_resolution.embedding_provider import create_embedding_provider
        
        # Get embedding for the input text
        provider = create_embedding_provider()
        query_embedding = provider.embed(text)
        
        if query_embedding is None or len(query_embedding) == 0:
            logger.debug("Could not generate embedding for text")
            return []
    except Exception as e:
        logger.debug(f"Embedding generation not available: {e}")
        return suggestions
    
    # Search for similar embeddings using pgvector
    # Using cosine distance: 1 - similarity
    try:
        from sqlalchemy import text as sql_text
        
        # Build exclusion clause
        exclude_clause = ""
        if exclude_skill_ids:
            exclude_list = ",".join(str(sid) for sid in exclude_skill_ids)
            exclude_clause = f"AND se.skill_id NOT IN ({exclude_list})"
        
        query = sql_text(f"""
            SELECT 
                se.skill_id,
                s.skill_name,
                c.category_name,
                sc.subcategory_name,
                1 - (se.embedding <=> :query_embedding) as similarity
            FROM skill_embeddings se
            JOIN skills s ON se.skill_id = s.skill_id
            JOIN skill_subcategories sc ON s.subcategory_id = sc.subcategory_id
            JOIN skill_categories c ON sc.category_id = c.category_id
            WHERE 1 - (se.embedding <=> :query_embedding) >= :min_similarity
            {exclude_clause}
            ORDER BY similarity DESC
            LIMIT :max_results
        """)
        
        results = db.execute(query, {
            "query_embedding": str(list(query_embedding)),
            "min_similarity": min_similarity,
            "max_results": max_results
        }).fetchall()
        
        for row in results:
            suggestions.append(SkillSuggestion(
                skill_id=row.skill_id,
                skill_name=row.skill_name,
                category=row.category_name,
                subcategory=row.subcategory_name,
                match_type="embedding",
                confidence=round(row.similarity, 4)
            ))
            
    except Exception as e:
        # Rollback to clear failed transaction state and prevent cascading errors
        db.rollback()
        logger.debug(f"Embedding query failed: {e}")
    
    return suggestions


# =============================================================================
# RESOLVE SKILL
# =============================================================================

def resolve_skill(
    db: Session,
    import_run_id: str,
    raw_skill_id: int,
    target_skill_id: int,
    resolved_by: str = None
) -> ResolveSkillResponse:
    """
    Map an unresolved skill to an existing master skill and create alias.
    
    Args:
        db: Database session
        import_run_id: The import job UUID
        raw_skill_id: ID of the raw_skill_input to resolve
        target_skill_id: ID of the master skill to map to
        resolved_by: Username of the user performing the resolution
        
    Returns:
        ResolveSkillResponse with resolution details
        
    Raises:
        ImportJobNotFoundError: If import job not found
        RawSkillNotFoundError: If raw skill input not found
        SkillNotFoundError: If target skill not found
        AlreadyResolvedError: If raw skill is already resolved
        AliasAlreadyExistsError: If alias already maps to a different skill
    """
    logger.info(f"Resolving skill {raw_skill_id} -> {target_skill_id} by {resolved_by}")
    
    # Verify import job exists
    job = db.query(ImportJob).filter(ImportJob.job_id == import_run_id).first()
    if not job:
        raise ImportJobNotFoundError(import_run_id)
    
    # Get the raw skill input
    raw_skill = db.query(RawSkillInput).filter(
        RawSkillInput.raw_skill_id == raw_skill_id,
        RawSkillInput.job_id == import_run_id
    ).first()
    
    if not raw_skill:
        raise RawSkillNotFoundError(raw_skill_id)
    
    # Check if already resolved
    if raw_skill.status == "RESOLVED":
        raise AlreadyResolvedError(raw_skill_id)
    
    # Verify target skill exists
    target_skill = db.query(Skill).filter(Skill.skill_id == target_skill_id).first()
    if not target_skill:
        raise SkillNotFoundError(target_skill_id)
    
    # Compute canonical alias text using the same normalization as SkillResolver
    # This ensures the alias will be found when resolver builds its lookup cache
    # Flow: raw_text -> token_validator.clean_and_validate() -> normalize_skill_name()
    token_validator = SkillTokenValidator()
    cleaned_token = token_validator.clean_and_validate(raw_skill.raw_text)
    if cleaned_token:
        canonical_alias_text = normalize_skill_name(cleaned_token)
    else:
        # Fallback to original normalized_text if token validation fails
        canonical_alias_text = normalize_skill_name(raw_skill.normalized_text)
    
    # Check if alias already exists for a DIFFERENT skill
    existing_alias = db.query(SkillAlias).filter(
        func.lower(SkillAlias.alias_text) == canonical_alias_text.lower()
    ).first()
    
    if existing_alias and existing_alias.skill_id != target_skill_id:
        # Alias exists but maps to different skill - conflict
        existing_skill = db.query(Skill).filter(
            Skill.skill_id == existing_alias.skill_id
        ).first()
        raise AliasAlreadyExistsError(
            raw_skill.normalized_text,
            existing_alias.skill_id,
            existing_skill.skill_name if existing_skill else "Unknown"
        )
    
    alias_created = False
    
    # Create alias if it doesn't exist (for this skill or any other)
    if not existing_alias:
        new_alias = SkillAlias(
            alias_text=canonical_alias_text,
            skill_id=target_skill_id,
            source="import_resolution",
            confidence_score=1.0
        )
        db.add(new_alias)
        alias_created = True
        logger.info(f"Created alias '{canonical_alias_text}' -> skill {target_skill_id}")
    else:
        logger.info(f"Alias '{canonical_alias_text}' already exists for skill {target_skill_id}")
    
    # Update raw_skill_input record
    raw_skill.status = "RESOLVED"
    raw_skill.resolved_skill_id = target_skill_id
    raw_skill.resolution_method = "manual_mapping"
    raw_skill.resolution_confidence = 1.0
    raw_skill.resolved_by = resolved_by
    raw_skill.resolved_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Successfully resolved skill {raw_skill_id} to {target_skill_id}")
    
    return ResolveSkillResponse(
        raw_skill_id=raw_skill_id,
        resolved_skill_id=target_skill_id,
        alias_created=alias_created,
        alias_text=canonical_alias_text,
        message=f"Skill '{raw_skill.raw_text}' mapped to '{target_skill.skill_name}'" + 
                (" and alias created" if alias_created else "")
    )
