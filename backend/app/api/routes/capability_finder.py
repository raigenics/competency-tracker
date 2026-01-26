"""
API routes for Capability Finder (Advanced Query) feature.
Provides endpoints for typeahead/autocomplete data.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.capability_finder_service import CapabilityFinderService
from app.schemas.capability_finder import SkillListResponse, RoleListResponse

router = APIRouter(prefix="/capability-finder", tags=["capability-finder"])


@router.get("/skills", response_model=SkillListResponse)
def get_all_skills(db: Session = Depends(get_db)):
    """
    Get all distinct skill names for typeahead/autocomplete.
    
    Returns:
        List of all distinct skill names sorted alphabetically (A-Z)
    """
    try:
        skills = CapabilityFinderService.get_all_skills(db)
        return SkillListResponse(skills=skills)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch skills: {str(e)}"
        )


@router.get("/roles", response_model=RoleListResponse)
def get_all_roles(db: Session = Depends(get_db)):
    """
    Get all distinct role names for typeahead/autocomplete.
    
    Returns:
        List of all distinct role names sorted alphabetically (A-Z)
    """
    try:
        roles = CapabilityFinderService.get_all_roles(db)
        return RoleListResponse(roles=roles)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch roles: {str(e)}"
        )
