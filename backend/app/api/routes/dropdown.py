"""
API routes for dropdown data.
"""
import time
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.dropdown_service import DropdownService
from app.schemas.dropdown import (
    SegmentListResponse,
    SubSegmentListResponse,
    ProjectListResponse, 
    TeamListResponse,
    SegmentDropdown,
    SubSegmentDropdown,
    ProjectDropdown,
    TeamDropdown
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dropdown", tags=["dropdown"])


@router.get("/segments", response_model=SegmentListResponse)
def get_segments(db: Session = Depends(get_db)):
    """
    Get all segments for dropdown.
    
    Returns:
        List of segments ordered alphabetically by name
    """
    start_time = time.time()
    try:
        segments = DropdownService.get_segments(db)
        query_time = time.time() - start_time
        dropdown_items = [
            SegmentDropdown(id=s.segment_id, name=s.segment_name)
            for s in segments
        ]
        total_time = time.time() - start_time
        logger.info(f"[PERF] GET /dropdown/segments | query={query_time*1000:.1f}ms | total={total_time*1000:.1f}ms | count={len(dropdown_items)}")
        return SegmentListResponse(segments=dropdown_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch segments: {str(e)}")


@router.get("/segments/{segment_id}/sub-segments", response_model=SubSegmentListResponse)
def get_sub_segments_by_segment(segment_id: int, db: Session = Depends(get_db)):
    """
    Get all sub-segments for a specific segment.
    
    Args:
        segment_id: ID of the segment
        
    Returns:
        List of sub-segments for the segment ordered alphabetically by name
        
    Raises:
        HTTPException: If segment_id is invalid
    """
    start_time = time.time()
    try:
        sub_segments = DropdownService.get_sub_segments_by_segment(db, segment_id)
        query_time = time.time() - start_time
        dropdown_items = [
            SubSegmentDropdown(id=ss.sub_segment_id, name=ss.sub_segment_name)
            for ss in sub_segments
        ]
        total_time = time.time() - start_time
        logger.info(f"[PERF] GET /dropdown/segments/{segment_id}/sub-segments | query={query_time*1000:.1f}ms | total={total_time*1000:.1f}ms | count={len(dropdown_items)}")
        return SubSegmentListResponse(sub_segments=dropdown_items)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sub-segments: {str(e)}")


@router.get("/sub-segments", response_model=SubSegmentListResponse)
def get_sub_segments(db: Session = Depends(get_db)):
    """
    Get all sub-segments for dropdown.
    
    Returns:
        List of sub-segments ordered alphabetically by name
    """
    start_time = time.time()
    try:
        sub_segments = DropdownService.get_sub_segments(db)
        query_time = time.time() - start_time
        dropdown_items = [
            SubSegmentDropdown(id=ss.sub_segment_id, name=ss.sub_segment_name)
            for ss in sub_segments
        ]
        total_time = time.time() - start_time
        logger.info(f"[PERF] GET /dropdown/sub-segments | query={query_time*1000:.1f}ms | total={total_time*1000:.1f}ms | count={len(dropdown_items)}")
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
    start_time = time.time()
    try:
        projects = DropdownService.get_projects_by_sub_segment(db, sub_segment_id)
        query_time = time.time() - start_time
        dropdown_items = [
            ProjectDropdown(id=p.project_id, name=p.project_name)
            for p in projects
        ]
        total_time = time.time() - start_time
        logger.info(f"[PERF] GET /dropdown/projects?sub_segment_id={sub_segment_id} | query={query_time*1000:.1f}ms | total={total_time*1000:.1f}ms | count={len(dropdown_items)}")
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
    start_time = time.time()
    try:
        teams = DropdownService.get_teams_by_project(db, project_id)
        query_time = time.time() - start_time
        dropdown_items = [
            TeamDropdown(id=t.team_id, name=t.team_name)
            for t in teams
        ]
        total_time = time.time() - start_time
        logger.info(f"[PERF] GET /dropdown/teams?project_id={project_id} | query={query_time*1000:.1f}ms | total={total_time*1000:.1f}ms | count={len(dropdown_items)}")
        return TeamListResponse(teams=dropdown_items)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")
