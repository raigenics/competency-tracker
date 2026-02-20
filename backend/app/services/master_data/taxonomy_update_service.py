"""
Service functions for updating Skill Taxonomy entities.

Implements SRP with separate functions for each entity type.
Each function handles:
- Entity retrieval
- Input validation
- Uniqueness checking (case-insensitive)
- Database update
- Audit logging hooks (TODO)

Pattern:
- Thin service layer: validation + orchestration
- Direct SQLAlchemy queries (no separate repository layer as per existing codebase pattern)
"""
import logging
from typing import Optional, Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.employee_skill import EmployeeSkill
from app.schemas.master_data_update import (
    CategoryUpdateResponse,
    SubcategoryUpdateResponse,
    SkillUpdateResponse,
    AliasUpdateResponse,
    AliasCreateResponse,
    CategoryCreateResponse,
    SubcategoryCreateResponse,
    SkillCreateResponse,
)
from .exceptions import NotFoundError, ConflictError, EmbeddingError
from .validators import validate_required_name

logger = logging.getLogger(__name__)


# =============================================================================
# EMBEDDING HELPER
# =============================================================================

def _update_skill_embedding(db: Session, skill: Skill) -> None:
    """
    Generate and upsert embedding for a skill.
    
    Called after skill creation or modification (name/aliases changed).
    Uses the skill_embedding_service to generate embedding from skill_name + aliases
    and upserts into skill_embeddings table.
    
    Args:
        db: Database session
        skill: Skill object with relationships (aliases) loaded
        
    Raises:
        EmbeddingError: If embedding generation or persistence fails
    """
    try:
        from app.services.skill_resolution.embedding_provider import create_embedding_provider
        from app.services.skill_resolution.skill_embedding_service import SkillEmbeddingService
        
        provider = create_embedding_provider()
        embedding_service = SkillEmbeddingService(
            db=db,
            embedding_provider=provider
        )
        
        # Ensure aliases relationship is loaded for embedding text generation
        # The skill should already have aliases loaded after flush
        success = embedding_service.ensure_embedding_for_skill(skill)
        
        if not success:
            raise EmbeddingError(
                f"Failed to generate embedding for skill '{skill.skill_name}' (id={skill.skill_id})"
            )
        
        logger.info(f"Embedding updated for skill_id={skill.skill_id}, skill_name='{skill.skill_name}'")
        
    except ImportError as e:
        # Embedding service not available - raise error for admin workflows
        raise EmbeddingError(f"Embedding service unavailable: {e}")
    except EmbeddingError:
        raise
    except Exception as e:
        raise EmbeddingError(f"Embedding generation failed: {type(e).__name__}: {e}")


# =============================================================================
# CATEGORY CREATE
# =============================================================================

def create_category(
    db: Session,
    category_name: str,
    actor: Optional[str] = None
) -> CategoryCreateResponse:
    """
    Create a new skill category.
    
    Args:
        db: Database session
        category_name: Name for the new category (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        CategoryCreateResponse with created category data
        
    Raises:
        ConflictError: If name already exists (case-insensitive)
        ValidationError: If name is invalid
    """
    logger.info(f"Creating category '{category_name}' by {actor}")
    
    # Validate input
    validated_name = validate_required_name("category_name", category_name)
    
    # Check for duplicate name (case-insensitive), excluding soft-deleted
    existing = db.query(SkillCategory).filter(
        func.lower(SkillCategory.category_name) == validated_name.lower(),
        SkillCategory.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ConflictError("Category", "name", validated_name)
    
    # Create new category
    new_category = SkillCategory(
        category_name=validated_name,
        created_by=actor or "system"
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    logger.info(f"Category created with id {new_category.category_id}: '{validated_name}'")
    
    return CategoryCreateResponse(
        id=new_category.category_id,
        name=new_category.category_name,
        created_at=new_category.created_at,
        created_by=new_category.created_by,
        message="Category created successfully"
    )


# =============================================================================
# SUBCATEGORY CREATE
# =============================================================================

def create_subcategory(
    db: Session,
    category_id: int,
    subcategory_name: str,
    actor: Optional[str] = None
) -> SubcategoryCreateResponse:
    """
    Create a new subcategory under a category.
    
    Args:
        db: Database session
        category_id: ID of the parent category
        subcategory_name: Name for the new subcategory (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SubcategoryCreateResponse with created subcategory data
        
    Raises:
        NotFoundError: If parent category not found
        ConflictError: If name already exists within the category (case-insensitive)
        ValidationError: If name is invalid
    """
    logger.info(f"Creating subcategory '{subcategory_name}' under category {category_id} by {actor}")
    
    # Validate input
    validated_name = validate_required_name("subcategory_name", subcategory_name)
    
    # Check parent category exists and is not soft-deleted
    parent_category = db.query(SkillCategory).filter(
        SkillCategory.category_id == category_id,
        SkillCategory.deleted_at.is_(None)
    ).first()
    
    if not parent_category:
        raise NotFoundError("Category", category_id)
    
    # Check for duplicate name within same category (case-insensitive), excluding soft-deleted
    existing = db.query(SkillSubcategory).filter(
        SkillSubcategory.category_id == category_id,
        func.lower(SkillSubcategory.subcategory_name) == validated_name.lower(),
        SkillSubcategory.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ConflictError(
            "Subcategory", 
            "name", 
            validated_name, 
            scope=f"category '{parent_category.category_name}'"
        )
    
    # Create new subcategory
    new_subcategory = SkillSubcategory(
        subcategory_name=validated_name,
        category_id=category_id,
        created_by=actor or "system"
    )
    
    db.add(new_subcategory)
    db.commit()
    db.refresh(new_subcategory)
    
    logger.info(f"Subcategory created with id {new_subcategory.subcategory_id}: '{validated_name}'")
    
    return SubcategoryCreateResponse(
        id=new_subcategory.subcategory_id,
        name=new_subcategory.subcategory_name,
        category_id=new_subcategory.category_id,
        created_at=new_subcategory.created_at,
        created_by=new_subcategory.created_by,
        message="Subcategory created successfully"
    )


# =============================================================================
# SKILL CREATE
# =============================================================================

def create_skill(
    db: Session,
    subcategory_id: int,
    skill_name: str,
    alias_text: Optional[str] = None,
    actor: Optional[str] = None
) -> SkillCreateResponse:
    """
    Create a new skill under a subcategory, optionally with aliases.
    
    Args:
        db: Database session
        subcategory_id: ID of the parent subcategory
        skill_name: Name for the new skill (will be validated)
        alias_text: Optional comma-separated alias texts (e.g., "alias1, alias2")
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SkillCreateResponse with created skill data and aliases
        
    Raises:
        NotFoundError: If parent subcategory not found
        ConflictError: If skill name already exists within the subcategory (case-insensitive)
        ConflictError: If any alias_text already exists globally
        ValidationError: If name is invalid
    """
    logger.info(f"Creating skill '{skill_name}' under subcategory {subcategory_id} by {actor}")
    
    # Validate input
    validated_name = validate_required_name("skill_name", skill_name)
    
    # Check parent subcategory exists and is not soft-deleted
    parent_subcategory = db.query(SkillSubcategory).filter(
        SkillSubcategory.subcategory_id == subcategory_id,
        SkillSubcategory.deleted_at.is_(None)
    ).first()
    
    if not parent_subcategory:
        raise NotFoundError("Subcategory", subcategory_id)
    
    # Check for duplicate skill name within same subcategory (case-insensitive), excluding soft-deleted
    existing_skill = db.query(Skill).filter(
        Skill.subcategory_id == subcategory_id,
        func.lower(Skill.skill_name) == validated_name.lower(),
        Skill.deleted_at.is_(None)
    ).first()
    
    if existing_skill:
        raise ConflictError(
            "Skill", 
            "name", 
            validated_name, 
            scope=f"subcategory '{parent_subcategory.subcategory_name}'"
        )
    
    # Parse comma-separated aliases into list
    alias_list = []
    if alias_text:
        alias_list = [a.strip() for a in alias_text.split(',') if a.strip()]
    
    # Check all aliases don't already exist globally
    for alias in alias_list:
        existing_alias = db.query(SkillAlias).filter(
            func.lower(SkillAlias.alias_text) == alias.lower()
        ).first()
        
        if existing_alias:
            raise ConflictError("Alias", "text", alias)
    
    # Create new skill
    new_skill = Skill(
        skill_name=validated_name,
        subcategory_id=subcategory_id,
        created_by=actor or "system"
    )
    
    db.add(new_skill)
    db.flush()  # Get the skill_id before creating aliases
    
    # Create aliases if provided
    created_aliases = []
    for alias in alias_list:
        new_alias = SkillAlias(
            alias_text=alias,
            skill_id=new_skill.skill_id,
            source="manual",
            confidence_score=1.0
        )
        db.add(new_alias)
        db.flush()
        
        created_aliases.append(AliasCreateResponse(
            id=new_alias.alias_id,
            alias_text=new_alias.alias_text,
            skill_id=new_alias.skill_id,
            source=new_alias.source,
            confidence_score=new_alias.confidence_score,
            message="Alias created successfully"
        ))
    
    db.commit()
    db.refresh(new_skill)
    
    # Generate and persist embedding for the new skill
    _update_skill_embedding(db, new_skill)
    
    logger.info(f"Skill created with id {new_skill.skill_id}: '{validated_name}'" + 
                (f" with {len(created_aliases)} alias(es)" if created_aliases else ""))
    
    return SkillCreateResponse(
        id=new_skill.skill_id,
        name=new_skill.skill_name,
        subcategory_id=new_skill.subcategory_id,
        created_at=new_skill.created_at,
        created_by=new_skill.created_by,
        aliases=created_aliases,
        message="Skill created successfully"
    )


# =============================================================================
# CATEGORY UPDATE
# =============================================================================

def update_category_name(
    db: Session,
    category_id: int,
    new_name: str,
    actor: Optional[str] = None
) -> CategoryUpdateResponse:
    """
    Update the name of a skill category.
    
    Args:
        db: Database session
        category_id: ID of the category to update
        new_name: New category name (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        CategoryUpdateResponse with updated category data
        
    Raises:
        NotFoundError: If category not found
        ConflictError: If name already exists (case-insensitive)
        ValidationError: If name is invalid
    """
    logger.info(f"Updating category {category_id} name to '{new_name}' by {actor}")
    
    # Validate input
    validated_name = validate_required_name("category_name", new_name)
    
    # Fetch category
    category = db.query(SkillCategory).filter(
        SkillCategory.category_id == category_id
    ).first()
    
    if not category:
        raise NotFoundError("Category", category_id)
    
    # Check if name unchanged (case-insensitive)
    if category.category_name.lower() == validated_name.lower():
        # No change needed, return current state
        return _category_to_response(category)
    
    # Check uniqueness (case-insensitive)
    existing = db.query(SkillCategory).filter(
        func.lower(SkillCategory.category_name) == validated_name.lower(),
        SkillCategory.category_id != category_id
    ).first()
    
    if existing:
        raise ConflictError("Category", "category_name", validated_name)
    
    # Update
    category.category_name = validated_name
    
    # TODO: Audit logging - write to audit_log table when implemented
    # audit_log.write(entity_type="category", entity_id=category_id, 
    #                 action="update", actor=actor, changes={"category_name": validated_name})
    
    db.commit()
    db.refresh(category)
    
    logger.info(f"Category {category_id} name updated successfully")
    return _category_to_response(category)


def _category_to_response(category: SkillCategory) -> CategoryUpdateResponse:
    """Convert Category model to response DTO."""
    return CategoryUpdateResponse(
        id=category.category_id,
        name=category.category_name,
        created_at=category.created_at,
        created_by=category.created_by
    )


# =============================================================================
# SUBCATEGORY UPDATE
# =============================================================================

def update_subcategory_name(
    db: Session,
    subcategory_id: int,
    new_name: str,
    actor: Optional[str] = None
) -> SubcategoryUpdateResponse:
    """
    Update the name of a skill subcategory.
    
    Args:
        db: Database session
        subcategory_id: ID of the subcategory to update
        new_name: New subcategory name (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SubcategoryUpdateResponse with updated subcategory data
        
    Raises:
        NotFoundError: If subcategory not found
        ConflictError: If name already exists within the same category (case-insensitive)
        ValidationError: If name is invalid
    """
    logger.info(f"Updating subcategory {subcategory_id} name to '{new_name}' by {actor}")
    
    # Validate input
    validated_name = validate_required_name("subcategory_name", new_name)
    
    # Fetch subcategory
    subcategory = db.query(SkillSubcategory).filter(
        SkillSubcategory.subcategory_id == subcategory_id
    ).first()
    
    if not subcategory:
        raise NotFoundError("Subcategory", subcategory_id)
    
    # Check if name unchanged (case-insensitive)
    if subcategory.subcategory_name.lower() == validated_name.lower():
        # No change needed, return current state
        return _subcategory_to_response(subcategory)
    
    # Check uniqueness within same category (case-insensitive)
    existing = db.query(SkillSubcategory).filter(
        func.lower(SkillSubcategory.subcategory_name) == validated_name.lower(),
        SkillSubcategory.category_id == subcategory.category_id,
        SkillSubcategory.subcategory_id != subcategory_id
    ).first()
    
    if existing:
        raise ConflictError(
            "Subcategory", 
            "subcategory_name", 
            validated_name,
            scope=f"category {subcategory.category_id}"
        )
    
    # Update
    subcategory.subcategory_name = validated_name
    
    # TODO: Audit logging
    
    db.commit()
    db.refresh(subcategory)
    
    logger.info(f"Subcategory {subcategory_id} name updated successfully")
    return _subcategory_to_response(subcategory)


def _subcategory_to_response(subcategory: SkillSubcategory) -> SubcategoryUpdateResponse:
    """Convert Subcategory model to response DTO."""
    return SubcategoryUpdateResponse(
        id=subcategory.subcategory_id,
        name=subcategory.subcategory_name,
        category_id=subcategory.category_id,
        created_at=subcategory.created_at,
        created_by=subcategory.created_by
    )


# =============================================================================
# SKILL UPDATE
# =============================================================================

def update_skill_name(
    db: Session,
    skill_id: int,
    new_name: str,
    actor: Optional[str] = None
) -> SkillUpdateResponse:
    """
    Update the name of a skill.
    
    Args:
        db: Database session
        skill_id: ID of the skill to update
        new_name: New skill name (will be validated)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        SkillUpdateResponse with updated skill data
        
    Raises:
        NotFoundError: If skill not found
        ConflictError: If name already exists within the same subcategory (case-insensitive)
        ValidationError: If name is invalid
    """
    logger.info(f"Updating skill {skill_id} name to '{new_name}' by {actor}")
    
    # Validate input
    validated_name = validate_required_name("skill_name", new_name)
    
    # Fetch skill
    skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
    
    if not skill:
        raise NotFoundError("Skill", skill_id)
    
    # Check if name unchanged (case-insensitive)
    if skill.skill_name.lower() == validated_name.lower():
        # No change needed, return current state
        return _skill_to_response(skill)
    
    # Check uniqueness within same subcategory (case-insensitive)
    existing = db.query(Skill).filter(
        func.lower(Skill.skill_name) == validated_name.lower(),
        Skill.subcategory_id == skill.subcategory_id,
        Skill.skill_id != skill_id
    ).first()
    
    if existing:
        raise ConflictError(
            "Skill", 
            "skill_name", 
            validated_name,
            scope=f"subcategory {skill.subcategory_id}"
        )
    
    # Update
    skill.skill_name = validated_name
    
    # TODO: Audit logging
    
    db.commit()
    db.refresh(skill)
    
    # Regenerate embedding since skill name changed
    _update_skill_embedding(db, skill)
    
    logger.info(f"Skill {skill_id} name updated successfully")
    return _skill_to_response(skill)


def _skill_to_response(skill: Skill) -> SkillUpdateResponse:
    """Convert Skill model to response DTO."""
    return SkillUpdateResponse(
        id=skill.skill_id,
        name=skill.skill_name,
        subcategory_id=skill.subcategory_id,
        created_at=skill.created_at,
        created_by=skill.created_by
    )


# =============================================================================
# ALIAS UPDATE
# =============================================================================

def update_alias(
    db: Session,
    alias_id: int,
    alias_text: Optional[str] = None,
    source: Optional[str] = None,
    confidence_score: Optional[float] = None,
    actor: Optional[str] = None
) -> AliasUpdateResponse:
    """
    Update a skill alias.
    
    Args:
        db: Database session
        alias_id: ID of the alias to update
        alias_text: New alias text (optional, will be validated if provided)
        source: New source (optional)
        confidence_score: New confidence score (optional)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        AliasUpdateResponse with updated alias data
        
    Raises:
        NotFoundError: If alias not found
        ConflictError: If alias_text already exists for the same skill (case-insensitive)
        ValidationError: If alias_text is invalid
    """
    logger.info(f"Updating alias {alias_id} by {actor}")
    
    # Fetch alias
    alias = db.query(SkillAlias).filter(SkillAlias.alias_id == alias_id).first()
    
    if not alias:
        raise NotFoundError("Alias", alias_id)
    
    # Track if any changes were made
    changes_made = False
    alias_text_changed = False
    
    # Update alias_text if provided
    if alias_text is not None:
        validated_text = validate_required_name("alias_text", alias_text)
        
        # Check if text unchanged (case-insensitive)
        if alias.alias_text.lower() != validated_text.lower():
            # Check uniqueness within same skill (case-insensitive)
            existing = db.query(SkillAlias).filter(
                func.lower(SkillAlias.alias_text) == validated_text.lower(),
                SkillAlias.skill_id == alias.skill_id,
                SkillAlias.alias_id != alias_id
            ).first()
            
            if existing:
                raise ConflictError(
                    "Alias", 
                    "alias_text", 
                    validated_text,
                    scope=f"skill {alias.skill_id}"
                )
            
            alias.alias_text = validated_text
            changes_made = True
            alias_text_changed = True
    
    # Update source if provided
    if source is not None:
        alias.source = source.strip() if source else alias.source
        changes_made = True
    
    # Update confidence_score if provided
    if confidence_score is not None:
        alias.confidence_score = confidence_score
        changes_made = True
    
    if changes_made:
        # TODO: Audit logging
        db.commit()
        db.refresh(alias)
        
        # Regenerate embedding if alias text changed
        if alias_text_changed:
            skill = db.query(Skill).filter(Skill.skill_id == alias.skill_id).first()
            if skill:
                _update_skill_embedding(db, skill)
        
        logger.info(f"Alias {alias_id} updated successfully")
    
    return _alias_to_response(alias)


def _alias_to_response(alias: SkillAlias) -> AliasUpdateResponse:
    """Convert Alias model to response DTO."""
    return AliasUpdateResponse(
        id=alias.alias_id,
        alias_text=alias.alias_text,
        skill_id=alias.skill_id,
        source=alias.source,
        confidence_score=alias.confidence_score,
        created_at=alias.created_at
    )


# =============================================================================
# ALIAS CREATE
# =============================================================================

def create_alias(
    db: Session,
    skill_id: int,
    alias_text: str,
    source: str = "manual",
    confidence_score: Optional[float] = 1.0,
    actor: Optional[str] = None
) -> AliasCreateResponse:
    """
    Create a new alias for a skill.
    
    Args:
        db: Database session
        skill_id: ID of the skill to add alias to
        alias_text: Alias text (will be validated)
        source: Source of the alias (default: "manual")
        confidence_score: Confidence score (default: 1.0)
        actor: Username of the user performing the action (for audit)
        
    Returns:
        AliasCreateResponse with created alias data
        
    Raises:
        NotFoundError: If skill not found
        ConflictError: If alias_text already exists for this skill (case-insensitive)
        ValidationError: If alias_text is invalid
    """
    logger.info(f"Creating alias for skill {skill_id} by {actor}")
    
    # Validate alias_text
    validated_text = validate_required_name("alias_text", alias_text)
    
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
    if not skill:
        raise NotFoundError("Skill", skill_id)
    
    # Check uniqueness within skill (case-insensitive)
    existing = db.query(SkillAlias).filter(
        func.lower(SkillAlias.alias_text) == validated_text.lower(),
        SkillAlias.skill_id == skill_id
    ).first()
    
    if existing:
        raise ConflictError(
            "Alias", 
            "alias_text", 
            validated_text,
            scope=f"skill {skill_id}"
        )
    
    # Create new alias
    new_alias = SkillAlias(
        alias_text=validated_text,
        skill_id=skill_id,
        source=source,
        confidence_score=confidence_score
    )
    
    db.add(new_alias)
    db.commit()
    db.refresh(new_alias)
    
    # Regenerate embedding since aliases changed
    _update_skill_embedding(db, skill)
    
    logger.info(f"Alias {new_alias.alias_id} created successfully")
    
    return AliasCreateResponse(
        id=new_alias.alias_id,
        alias_text=new_alias.alias_text,
        skill_id=new_alias.skill_id,
        source=new_alias.source,
        confidence_score=new_alias.confidence_score,
        message="Alias created successfully"
    )


# =============================================================================
# ALIAS DELETE
# =============================================================================

def delete_alias(
    db: Session,
    alias_id: int,
    actor: Optional[str] = None
) -> dict:
    """
    Delete a skill alias.
    
    Args:
        db: Database session
        alias_id: ID of the alias to delete
        actor: Username of the user performing the action (for audit)
        
    Returns:
        dict with deletion confirmation
        
    Raises:
        NotFoundError: If alias not found
    """
    logger.info(f"Deleting alias {alias_id} by {actor}")
    
    # Fetch alias
    alias = db.query(SkillAlias).filter(SkillAlias.alias_id == alias_id).first()
    
    if not alias:
        raise NotFoundError("Alias", alias_id)
    
    alias_text = alias.alias_text
    skill_id = alias.skill_id
    
    # Fetch skill before deleting alias (for embedding update)
    skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
    
    db.delete(alias)
    db.commit()
    
    # Regenerate embedding since aliases changed
    if skill:
        _update_skill_embedding(db, skill)
    
    logger.info(f"Alias {alias_id} ('{alias_text}') deleted successfully")
    
    return {
        "id": alias_id,
        "alias_text": alias_text,
        "skill_id": skill_id,
        "message": "Alias deleted successfully"
    }


# =============================================================================
# CATEGORY SOFT DELETE
# =============================================================================

def soft_delete_category(
    db: Session,
    category_id: int,
    actor: Optional[str] = None
) -> dict:
    """
    Soft delete a skill category (set deleted_at and deleted_by).
    
    Args:
        db: Database session
        category_id: ID of the category to delete
        actor: Username of the user performing the action
        
    Returns:
        dict with deletion confirmation
        
    Raises:
        NotFoundError: If category not found or already deleted
        ConflictError: If category has subcategories (must delete children first)
    """
    logger.info(f"Soft-deleting category {category_id} by {actor}")
    
    # Fetch category (only non-deleted)
    category = db.query(SkillCategory).filter(
        SkillCategory.category_id == category_id,
        SkillCategory.deleted_at.is_(None)
    ).first()
    
    if not category:
        raise NotFoundError("Category", category_id)
    
    # Check for child subcategories (only non-deleted)
    child_count = db.query(SkillSubcategory).filter(
        SkillSubcategory.category_id == category_id,
        SkillSubcategory.deleted_at.is_(None)
    ).count()
    
    if child_count > 0:
        raise ConflictError(
            "Category",
            "subcategories",
            f"{child_count} subcategories",
            scope=f"category {category_id}"
        )
    
    # Perform soft delete
    category.deleted_at = func.now()
    category.deleted_by = actor or "system"
    
    db.commit()
    db.refresh(category)
    
    logger.info(f"Category {category_id} ('{category.category_name}') soft-deleted successfully")
    
    return {
        "id": category_id,
        "name": category.category_name,
        "deleted_at": str(category.deleted_at),
        "deleted_by": category.deleted_by,
        "message": "Category deleted successfully"
    }


# =============================================================================
# SUBCATEGORY SOFT DELETE
# =============================================================================

def soft_delete_subcategory(
    db: Session,
    subcategory_id: int,
    actor: Optional[str] = None
) -> dict:
    """
    Soft delete a skill subcategory (set deleted_at and deleted_by).
    
    Args:
        db: Database session
        subcategory_id: ID of the subcategory to delete
        actor: Username of the user performing the action
        
    Returns:
        dict with deletion confirmation
        
    Raises:
        NotFoundError: If subcategory not found or already deleted
        ConflictError: If subcategory has skills (must delete children first)
    """
    logger.info(f"Soft-deleting subcategory {subcategory_id} by {actor}")
    
    # Fetch subcategory (only non-deleted)
    subcategory = db.query(SkillSubcategory).filter(
        SkillSubcategory.subcategory_id == subcategory_id,
        SkillSubcategory.deleted_at.is_(None)
    ).first()
    
    if not subcategory:
        raise NotFoundError("Subcategory", subcategory_id)
    
    # Check for child skills (only non-deleted)
    child_count = db.query(Skill).filter(
        Skill.subcategory_id == subcategory_id,
        Skill.deleted_at.is_(None)
    ).count()
    
    if child_count > 0:
        raise ConflictError(
            "Subcategory",
            "skills",
            f"{child_count} skills",
            scope=f"subcategory {subcategory_id}"
        )
    
    # Perform soft delete
    subcategory.deleted_at = func.now()
    subcategory.deleted_by = actor or "system"
    
    db.commit()
    db.refresh(subcategory)
    
    logger.info(f"Subcategory {subcategory_id} ('{subcategory.subcategory_name}') soft-deleted successfully")
    
    return {
        "id": subcategory_id,
        "name": subcategory.subcategory_name,
        "category_id": subcategory.category_id,
        "deleted_at": str(subcategory.deleted_at),
        "deleted_by": subcategory.deleted_by,
        "message": "Subcategory deleted successfully"
    }


# =============================================================================
# SKILL DEPENDENCY CHECK
# =============================================================================

def check_skill_dependencies(db: Session, skill_id: int) -> Dict[str, int]:
    """
    Check if a skill has any dependencies (employee skills assigned).
    Only counts active employee skill records (where skill has not been soft-deleted
    from the employee's profile).
    
    Args:
        db: Database session
        skill_id: ID of the skill to check
        
    Returns:
        Dict with dependency counts, e.g. {"employee_skills": 5}
    """
    employee_skill_count = db.query(func.count(EmployeeSkill.employee_id))\
        .filter(EmployeeSkill.skill_id == skill_id)\
        .scalar() or 0
    
    dependencies = {}
    if employee_skill_count > 0:
        dependencies["employee_skills"] = employee_skill_count
    
    return dependencies


def check_skills_dependencies_bulk(db: Session, skill_ids: List[int]) -> List[Dict]:
    """
    Check if multiple skills have any dependencies (employee skills assigned).
    Uses a single efficient query with GROUP BY.
    
    Args:
        db: Database session
        skill_ids: List of skill IDs to check
        
    Returns:
        List of blocked skills with counts, e.g. [{"skill_id": 1, "employee_skills": 5}]
    """
    if not skill_ids:
        return []
    
    # Single query to get employee skill counts per skill_id
    results = db.query(
        EmployeeSkill.skill_id,
        func.count(EmployeeSkill.employee_id).label('employee_skill_count')
    )\
        .filter(EmployeeSkill.skill_id.in_(skill_ids))\
        .group_by(EmployeeSkill.skill_id)\
        .all()
    
    blocked = []
    for skill_id, employee_skill_count in results:
        if employee_skill_count > 0:
            blocked.append({
                "skill_id": skill_id,
                "employee_skills": employee_skill_count
            })
    
    return blocked


# =============================================================================
# SKILL SOFT DELETE
# =============================================================================

def soft_delete_skill(
    db: Session,
    skill_id: int,
    actor: Optional[str] = None
) -> dict:
    """
    Soft delete a skill (set deleted_at and deleted_by).
    
    Args:
        db: Database session
        skill_id: ID of the skill to delete
        actor: Username of the user performing the action
        
    Returns:
        dict with deletion confirmation
        
    Raises:
        NotFoundError: If skill not found or already deleted
    """
    logger.info(f"Soft-deleting skill {skill_id} by {actor}")
    
    # Fetch skill (only non-deleted)
    skill = db.query(Skill).filter(
        Skill.skill_id == skill_id,
        Skill.deleted_at.is_(None)
    ).first()
    
    if not skill:
        raise NotFoundError("Skill", skill_id)
    
    # Perform soft delete
    skill.deleted_at = func.now()
    skill.deleted_by = actor or "system"
    
    db.commit()
    db.refresh(skill)
    
    logger.info(f"Skill {skill_id} ('{skill.skill_name}') soft-deleted successfully")
    
    return {
        "id": skill_id,
        "name": skill.skill_name,
        "subcategory_id": skill.subcategory_id,
        "deleted_at": str(skill.deleted_at),
        "deleted_by": skill.deleted_by,
        "message": "Skill deleted successfully"
    }
