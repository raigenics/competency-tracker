"""
API routes for Master Data management.

Currently implements:
- READ endpoints for the Skill Taxonomy hierarchy
- CREATE (POST) endpoints for aliases
- UPDATE (PATCH) endpoints for taxonomy entities (category, subcategory, skill, alias)
- DELETE endpoints for aliases
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.master_data_taxonomy import SkillTaxonomyResponse
from app.schemas.master_data_update import (
    CategoryUpdateRequest,
    CategoryUpdateResponse,
    SubcategoryUpdateRequest,
    SubcategoryUpdateResponse,
    SkillUpdateRequest,
    SkillUpdateResponse,
    AliasUpdateRequest,
    AliasUpdateResponse,
    AliasCreateRequest,
    AliasCreateResponse,
    CategoryCreateRequest,
    CategoryCreateResponse,
    SubcategoryCreateRequest,
    SubcategoryCreateResponse,
    SkillCreateRequest,
    SkillCreateResponse,
)
from app.services.master_data import skill_taxonomy_service
from app.services.master_data import taxonomy_update_service
from app.services.master_data.exceptions import NotFoundError, ConflictError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/master-data", tags=["master-data"])


@router.get("/skill-taxonomy", response_model=SkillTaxonomyResponse)
async def get_skill_taxonomy(
    q: Optional[str] = Query(
        None,
        description="Optional search term to filter skills by name",
        min_length=1,
        max_length=100
    ),
    db: Session = Depends(get_db)
):
    """
    Get the complete skill taxonomy hierarchy.
    
    Returns nested structure: Categories -> SubCategories -> Skills
    
    Each skill includes:
    - Basic info (id, name, description)
    - Employee count (number of employees with this skill)
    - Audit fields (created_at, created_by)
    
    Query Parameters:
    - q: Optional search term to filter skills by name (case-insensitive)
    
    Returns:
    - categories: List of categories with nested subcategories and skills
    - total_categories: Count of categories in response
    - total_subcategories: Count of subcategories in response  
    - total_skills: Count of skills in response
    """
    logger.info(f"GET /master-data/skill-taxonomy (search={q})")
    
    try:
        return skill_taxonomy_service.get_skill_taxonomy(db, search_query=q)
    except Exception as e:
        logger.error(f"Error fetching skill taxonomy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill taxonomy"
        )


# =============================================================================
# HELPER: Exception to HTTP conversion
# =============================================================================

def _handle_master_data_error(e: Exception) -> HTTPException:
    """Convert service exceptions to appropriate HTTP responses."""
    if isinstance(e, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    elif isinstance(e, ConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    elif isinstance(e, ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    else:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# =============================================================================
# POST ENDPOINTS - Create Category
# =============================================================================

@router.post(
    "/skill-taxonomy/categories",
    response_model=CategoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Category name already exists"},
        422: {"description": "Validation error"},
    }
)
async def create_category(
    request: CategoryCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new skill category.
    
    Args:
    - **category_name**: Name for the category (must be unique, case-insensitive)
    """
    logger.info(f"POST /master-data/skill-taxonomy/categories")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return taxonomy_update_service.create_category(
            db=db,
            category_name=request.category_name,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# POST ENDPOINTS - Create Subcategory
# =============================================================================

@router.post(
    "/skill-taxonomy/categories/{category_id}/subcategories",
    response_model=SubcategoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Category not found"},
        409: {"description": "Subcategory name already exists in category"},
        422: {"description": "Validation error"},
    }
)
async def create_subcategory(
    category_id: int = Path(..., description="Category ID to add subcategory to", ge=1),
    request: SubcategoryCreateRequest = None,
    db: Session = Depends(get_db)
):
    """
    Create a new subcategory under a category.
    
    Args:
    - **category_id**: Parent category ID
    - **subcategory_name**: Name for the subcategory (must be unique within category, case-insensitive)
    """
    logger.info(f"POST /master-data/skill-taxonomy/categories/{category_id}/subcategories")
    
    actor = "system"  # Placeholder - get from auth context
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request body is required"
        )
    
    try:
        return taxonomy_update_service.create_subcategory(
            db=db,
            category_id=category_id,
            subcategory_name=request.subcategory_name,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# POST ENDPOINTS - Create Skill
# =============================================================================

@router.post(
    "/skill-taxonomy/subcategories/{subcategory_id}/skills",
    response_model=SkillCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Subcategory not found"},
        409: {"description": "Skill name already exists in subcategory or alias already exists"},
        422: {"description": "Validation error"},
    }
)
async def create_skill(
    subcategory_id: int = Path(..., description="Subcategory ID to add skill to", ge=1),
    request: SkillCreateRequest = None,
    db: Session = Depends(get_db)
):
    """
    Create a new skill under a subcategory, optionally with aliases.
    
    Args:
    - **subcategory_id**: Parent subcategory ID
    - **skill_name**: Name for the skill (must be unique within subcategory, case-insensitive)
    - **alias_text**: Optional comma-separated aliases (e.g., "alias1, alias2"). Each must be globally unique.
    """
    logger.info(f"POST /master-data/skill-taxonomy/subcategories/{subcategory_id}/skills")
    
    actor = "system"  # Placeholder - get from auth context
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request body is required"
        )
    
    try:
        return taxonomy_update_service.create_skill(
            db=db,
            subcategory_id=subcategory_id,
            skill_name=request.skill_name,
            alias_text=request.alias_text,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# PATCH ENDPOINTS - Category
# =============================================================================

@router.patch(
    "/skill-taxonomy/categories/{category_id}",
    response_model=CategoryUpdateResponse,
    responses={
        404: {"description": "Category not found"},
        409: {"description": "Category name already exists"},
        422: {"description": "Invalid input"},
    }
)
async def update_category(
    category_id: int = Path(..., description="Category ID to update", ge=1),
    request: CategoryUpdateRequest = None,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency when RBAC is fully implemented
    # current_user: RbacContext = Depends(get_rbac_context)
):
    """
    Update a skill category's name.
    
    Requires Project Manager or Admin role.
    
    - **category_name**: New name for the category (must be unique, case-insensitive)
    """
    logger.info(f"PATCH /master-data/skill-taxonomy/categories/{category_id}")
    
    # TODO: Get actor from current_user when auth is implemented
    actor = "system"  # Placeholder
    
    if not request or request.category_name is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="category_name is required"
        )
    
    try:
        return taxonomy_update_service.update_category_name(
            db=db,
            category_id=category_id,
            new_name=request.category_name,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# PATCH ENDPOINTS - Subcategory
# =============================================================================

@router.patch(
    "/skill-taxonomy/subcategories/{subcategory_id}",
    response_model=SubcategoryUpdateResponse,
    responses={
        404: {"description": "Subcategory not found"},
        409: {"description": "Subcategory name already exists in category"},
        422: {"description": "Invalid input"},
    }
)
async def update_subcategory(
    subcategory_id: int = Path(..., description="Subcategory ID to update", ge=1),
    request: SubcategoryUpdateRequest = None,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency when RBAC is fully implemented
):
    """
    Update a skill subcategory's name.
    
    Requires Project Manager or Admin role.
    
    - **subcategory_name**: New name for the subcategory (must be unique within its category, case-insensitive)
    """
    logger.info(f"PATCH /master-data/skill-taxonomy/subcategories/{subcategory_id}")
    
    actor = "system"  # Placeholder
    
    if not request or request.subcategory_name is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="subcategory_name is required"
        )
    
    try:
        return taxonomy_update_service.update_subcategory_name(
            db=db,
            subcategory_id=subcategory_id,
            new_name=request.subcategory_name,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# PATCH ENDPOINTS - Skill
# =============================================================================

@router.patch(
    "/skill-taxonomy/skills/{skill_id}",
    response_model=SkillUpdateResponse,
    responses={
        404: {"description": "Skill not found"},
        409: {"description": "Skill name already exists in subcategory"},
        422: {"description": "Invalid input"},
    }
)
async def update_skill(
    skill_id: int = Path(..., description="Skill ID to update", ge=1),
    request: SkillUpdateRequest = None,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency when RBAC is fully implemented
):
    """
    Update a skill's name.
    
    Requires Project Manager or Admin role.
    
    - **skill_name**: New name for the skill (must be unique within its subcategory, case-insensitive)
    """
    logger.info(f"PATCH /master-data/skill-taxonomy/skills/{skill_id}")
    
    actor = "system"  # Placeholder
    
    if not request or request.skill_name is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="skill_name is required"
        )
    
    try:
        return taxonomy_update_service.update_skill_name(
            db=db,
            skill_id=skill_id,
            new_name=request.skill_name,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# PATCH ENDPOINTS - Alias
# =============================================================================

@router.patch(
    "/skill-taxonomy/aliases/{alias_id}",
    response_model=AliasUpdateResponse,
    responses={
        404: {"description": "Alias not found"},
        409: {"description": "Alias text already exists for skill"},
        422: {"description": "Invalid input"},
    }
)
async def update_alias(
    alias_id: int = Path(..., description="Alias ID to update", ge=1),
    request: AliasUpdateRequest = None,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency when RBAC is fully implemented
):
    """
    Update a skill alias.
    
    Requires Project Manager or Admin role.
    
    - **alias_text**: New alias text (must be unique within its skill, case-insensitive)
    - **source**: Optional new source identifier
    - **confidence_score**: Optional new confidence score (0.0-1.0)
    """
    logger.info(f"PATCH /master-data/skill-taxonomy/aliases/{alias_id}")
    
    actor = "system"  # Placeholder
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request body is required"
        )
    
    # At least one field must be provided
    if request.alias_text is None and request.source is None and request.confidence_score is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field (alias_text, source, or confidence_score) must be provided"
        )
    
    try:
        return taxonomy_update_service.update_alias(
            db=db,
            alias_id=alias_id,
            alias_text=request.alias_text,
            source=request.source,
            confidence_score=request.confidence_score,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# POST ENDPOINTS - Create Alias
# =============================================================================

@router.post(
    "/skill-taxonomy/skills/{skill_id}/aliases",
    response_model=AliasCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Skill not found"},
        409: {"description": "Alias text already exists for skill"},
        422: {"description": "Validation error"},
    }
)
async def create_alias(
    skill_id: int = Path(..., description="Skill ID to add alias to", ge=1),
    request: AliasCreateRequest = None,
    db: Session = Depends(get_db)
):
    """
    Create a new alias for a skill.
    
    Args:
    - **skill_id**: Skill ID to add alias to
    - **alias_text**: Alias text (must be unique within the skill, case-insensitive)
    - **source**: Source of the alias (default: "manual")
    - **confidence_score**: Confidence score (default: 1.0)
    """
    logger.info(f"POST /master-data/skill-taxonomy/skills/{skill_id}/aliases")
    
    actor = "system"  # Placeholder
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request body is required"
        )
    
    try:
        return taxonomy_update_service.create_alias(
            db=db,
            skill_id=skill_id,
            alias_text=request.alias_text,
            source=request.source,
            confidence_score=request.confidence_score,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# DELETE ENDPOINTS - Delete Alias
# =============================================================================

@router.delete(
    "/skill-taxonomy/aliases/{alias_id}",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Alias not found"},
    }
)
async def delete_alias(
    alias_id: int = Path(..., description="Alias ID to delete", ge=1),
    db: Session = Depends(get_db)
):
    """
    Delete a skill alias.
    
    Args:
    - **alias_id**: Alias ID to delete
    """
    logger.info(f"DELETE /master-data/skill-taxonomy/aliases/{alias_id}")
    
    actor = "system"  # Placeholder
    
    try:
        return taxonomy_update_service.delete_alias(
            db=db,
            alias_id=alias_id,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# DELETE ENDPOINTS - Soft Delete Category
# =============================================================================

@router.delete(
    "/skill-taxonomy/categories/{category_id}",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Category not found"},
        409: {"description": "Category has subcategories - delete them first"},
    }
)
async def delete_category(
    category_id: int = Path(..., description="Category ID to delete", ge=1),
    db: Session = Depends(get_db)
):
    """
    Soft delete a skill category.
    
    Category must not have any subcategories. Delete all subcategories first.
    
    Args:
    - **category_id**: Category ID to delete
    """
    logger.info(f"DELETE /master-data/skill-taxonomy/categories/{category_id}")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return taxonomy_update_service.soft_delete_category(
            db=db,
            category_id=category_id,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# DELETE ENDPOINTS - Soft Delete Subcategory
# =============================================================================

@router.delete(
    "/skill-taxonomy/subcategories/{subcategory_id}",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Subcategory not found"},
        409: {"description": "Subcategory has skills - delete them first"},
    }
)
async def delete_subcategory(
    subcategory_id: int = Path(..., description="Subcategory ID to delete", ge=1),
    db: Session = Depends(get_db)
):
    """
    Soft delete a skill subcategory.
    
    Subcategory must not have any skills. Delete all skills first.
    
    Args:
    - **subcategory_id**: Subcategory ID to delete
    """
    logger.info(f"DELETE /master-data/skill-taxonomy/subcategories/{subcategory_id}")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        return taxonomy_update_service.soft_delete_subcategory(
            db=db,
            subcategory_id=subcategory_id,
            actor=actor
        )
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)


# =============================================================================
# DELETE ENDPOINTS - Soft Delete Skill
# =============================================================================

@router.delete(
    "/skill-taxonomy/skills/{skill_id}",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Skill not found"},
        409: {"description": "Skill has dependencies (employees have this skill)"},
    }
)
async def delete_skill(
    skill_id: int = Path(..., description="Skill ID to delete", ge=1),
    db: Session = Depends(get_db)
):
    """
    Soft delete a skill.
    
    Args:
    - **skill_id**: Skill ID to delete
    
    Raises:
        404: If skill not found or already deleted
        409: If skill has dependencies (employees have this skill)
    """
    logger.info(f"DELETE /master-data/skill-taxonomy/skills/{skill_id}")
    
    actor = "system"  # Placeholder - get from auth context
    
    try:
        # Check for dependencies first
        dependencies = taxonomy_update_service.check_skill_dependencies(db, skill_id)
        if dependencies:
            logger.warning(f"Skill {skill_id} has dependencies: {dependencies}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "This item has dependencies and cannot be deleted.",
                    "dependencies": dependencies
                }
            )
        
        return taxonomy_update_service.soft_delete_skill(
            db=db,
            skill_id=skill_id,
            actor=actor
        )
    except HTTPException:
        raise
    except (NotFoundError, ConflictError, ValidationError) as e:
        raise _handle_master_data_error(e)
    except Exception as e:
        raise _handle_master_data_error(e)
