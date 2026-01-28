"""
API routes for Capability Finder (Advanced Query) feature.
Provides endpoints for typeahead/autocomplete data.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.capability_finder_service import CapabilityFinderService
from app.schemas.capability_finder import (
    SkillListResponse, 
    RoleListResponse, 
    SearchRequest, 
    SearchResponse
)

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


@router.post("/search", response_model=SearchResponse)
def search_matching_talent(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for employees matching specified criteria.
    
    Filters:
    - Required Skills (multi-select with AND logic - must have ALL)
    - Sub-segment (optional)
    - Team (optional)
    - Role (optional)
    - Min Proficiency Level (0-5, applies to required skills)
    - Min Years of Experience (applies to required skills)
    
    Returns:
        List of matching employees with top 3 skills
    """
    try:
        results = CapabilityFinderService.search_matching_talent(
            db=db,
            skills=request.skills,
            sub_segment_id=request.sub_segment_id,
            team_id=request.team_id,
            role=request.role,
            min_proficiency=request.min_proficiency,
            min_experience_years=request.min_experience_years
        )
        
        return SearchResponse(
            results=results,
            count=len(results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search matching talent: {str(e)}"
        )
