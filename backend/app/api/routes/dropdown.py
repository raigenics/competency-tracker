"""
API routes for dropdown data.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.dropdown_service import DropdownService
from app.schemas.dropdown import (
    SubSegmentListResponse,
    ProjectListResponse, 
    TeamListResponse,
    SubSegmentDropdown,
    ProjectDropdown,
    TeamDropdown
)

router = APIRouter(prefix="/dropdown", tags=["dropdown"])


@router.get("/sub-segments", response_model=SubSegmentListResponse)
def get_sub_segments(db: Session = Depends(get_db)):
    """
    Get all sub-segments for dropdown.
    
    Returns:
        List of sub-segments ordered alphabetically by name
    """
    try:
        sub_segments = DropdownService.get_sub_segments(db)
        dropdown_items = [
            SubSegmentDropdown(id=ss.sub_segment_id, name=ss.sub_segment_name)
            for ss in sub_segments
        ]
        return SubSegmentListResponse(sub_segments=dropdown_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sub-segments: {str(e)}")


@router.get("/projects", response_model=ProjectListResponse)
def get_projects(sub_segment_id: int, db: Session = Depends(get_db)):
    """
    Get all projects for a specific sub-segment.
    
    Args:
        sub_segment_id: ID of the sub-segment
        
    Returns:
        List of projects for the sub-segment ordered alphabetically by name
        
    Raises:
        HTTPException: If sub_segment_id is invalid
    """
    try:
        projects = DropdownService.get_projects_by_sub_segment(db, sub_segment_id)
        dropdown_items = [
            ProjectDropdown(id=p.project_id, name=p.project_name)
            for p in projects
        ]
        return ProjectListResponse(projects=dropdown_items)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@router.get("/teams", response_model=TeamListResponse)
def get_teams(project_id: int, db: Session = Depends(get_db)):
    """
    Get all teams for a specific project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        List of teams for the project ordered alphabetically by name
        
    Raises:
        HTTPException: If project_id is invalid
    """
    try:
        teams = DropdownService.get_teams_by_project(db, project_id)
        dropdown_items = [
            TeamDropdown(id=t.team_id, name=t.team_name)
            for t in teams
        ]
        return TeamListResponse(teams=dropdown_items)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")
