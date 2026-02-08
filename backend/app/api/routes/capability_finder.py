"""
API routes for Capability Finder (Advanced Query) feature.
Provides endpoints for typeahead/autocomplete data.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.session import get_db
from app.services.capability_finder_service import CapabilityFinderService
from app.schemas.capability_finder import (
    SkillListResponse,
    SkillSuggestionsResponse,
    RoleListResponse, 
    SearchRequest, 
    SearchResponse,
    ExportRequest
)

router = APIRouter(prefix="/capability-finder", tags=["capability-finder"])
logger = logging.getLogger(__name__)


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


@router.get("/skills/suggestions", response_model=SkillSuggestionsResponse)
def get_skill_suggestions(query: str = None, db: Session = Depends(get_db)):
    """
    Get enhanced skill suggestions with employee availability metadata.
    
    Returns master skills with flags indicating whether employees have each skill.
    Skills with employees appear first (selectable), master-only skills appear after (disabled).
    
    Query parameters:
        query (str, optional): Filter skills by name (case-insensitive partial match)
    
    Returns:
        List of skill suggestions with metadata:
        - skill_id: Unique skill identifier
        - skill_name: Skill name
        - is_employee_available: Whether any employees have this skill
        - is_selectable: Whether this skill can be selected for search
    """
    try:
        suggestions = CapabilityFinderService.get_skill_suggestions(db, query)
        return SkillSuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch skill suggestions: {str(e)}"
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
    except ValueError as e:
        # Client validation errors (e.g., invalid IDs, bad parameters)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search matching talent: {str(e)}"
        )


@router.post("/export")
async def export_matching_talent(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export matching talent to Excel file.
    
    Request body:
    - mode: "all" (export all search results) or "selected" (export only selected employees)
    - filters: Search filters (same as search endpoint)
    - selected_employee_ids: List of employee IDs (required if mode="selected")
    
    Returns:
        Excel file (.xlsx) with employee data and consolidated skills
    """
    try:
        logger.info(f"Export request received - mode: {request.mode}, selected_count: {len(request.selected_employee_ids)}")
        
        # Validate request
        if request.mode == "selected" and not request.selected_employee_ids:
            raise HTTPException(
                status_code=400,
                detail="selected_employee_ids cannot be empty when mode is 'selected'"
            )
        
        # Generate Excel file
        excel_file = CapabilityFinderService.export_matching_talent_to_excel(
            db=db,
            mode=request.mode,
            skills=request.filters.skills,
            sub_segment_id=request.filters.sub_segment_id,
            team_id=request.filters.team_id,
            role=request.filters.role,
            min_proficiency=request.filters.min_proficiency,
            min_experience_years=request.filters.min_experience_years,
            selected_employee_ids=request.selected_employee_ids
        )
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"capability_finder_matching_talent_{timestamp}.xlsx"
        
        logger.info(f"Export completed successfully - filename: {filename}")
        
        # Return as streaming response
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        logger.warning(f"Export validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export matching talent: {str(e)}"
        )
