"""
API routes for employee data management and queries.

Thin controller pattern - all business logic delegated to services.
Each endpoint maps to one service module with zero cross-dependencies.

RBAC Integration:
- RBAC context extracted from headers via get_rbac_context dependency
- Scope filtering applied by list_service based on user's role/scope
- Temporary: Uses X-RBAC-* headers until JWT auth is implemented
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.employee import (
    EmployeeListResponse, 
    EmployeesByIdsRequest, EmployeesByIdsResponse,
    EmployeeSuggestion,
    EmployeeCreateRequest, EmployeeCreateResponse,
    EmployeeUpdateRequest,
    EmployeeSkillsBulkSaveRequest, EmployeeSkillsBulkSaveResponse,
    EmployeeValidateUniqueResponse,
    EditBootstrapResponse,
    EmployeeDeleteResponse
)
from app.schemas.common import PaginationParams
from app.security.rbac_policy import get_rbac_context, RbacContext

# Service layer imports - isolated business logic
from app.services.employee_profile import suggest_service
from app.services.employee_profile import list_service
from app.services.employee_profile import profile_service
from app.services.employee_profile import by_ids_service
from app.services.employee_profile import create_service
from app.services.employee_profile import employee_skills_service
from app.services.employee_profile import validation_service
from app.services.employee_profile import delete_service
from app.services.employee_profile import edit_bootstrap_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/suggest", response_model=List[EmployeeSuggestion])
async def suggest_employees(
    q: str = Query(..., min_length=2, description="Search query for employee name or ZID"),
    limit: int = Query(8, ge=1, le=20, description="Maximum number of suggestions to return"),
    db: Session = Depends(get_db)
):
    """
    Get employee suggestions for autocomplete.
    
    - **q**: Search query (minimum 2 characters) - searches both name and ZID
    - **limit**: Maximum number of results (1-20, default 8)
    """
    logger.info(f"Fetching employee suggestions for query: '{q}' with limit: {limit}")
    
    try:
        suggestions = suggest_service.get_employee_suggestions(db, q, limit)
        logger.info(f"Returning {len(suggestions)} suggestions for query: '{q}'")
        return suggestions
        
    except Exception as e:
        logger.error(f"Error fetching employee suggestions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employee suggestions"
        )


@router.get("/validate-unique", response_model=EmployeeValidateUniqueResponse)
async def validate_unique(
    zid: Optional[str] = Query(None, description="ZID to check for uniqueness"),
    email: Optional[str] = Query(None, description="Email to check for uniqueness"),
    exclude_employee_id: Optional[int] = Query(None, description="Employee ID to exclude from check (for edit mode)"),
    db: Session = Depends(get_db)
):
    """
    Validate ZID and email uniqueness for employee creation/editing.
    
    - **zid**: ZID to check - returns zid_exists=true if already in use
    - **email**: Email to check - returns email_exists=true if already in use
    - **exclude_employee_id**: When editing, pass the current employee's ID to exclude 
                               their own ZID/email from triggering the uniqueness error
    
    Returns:
        - zid_exists: true if ZID is already used by another employee
        - email_exists: true if email is already used by another employee
    """
    logger.info(f"Validating uniqueness: zid={zid}, email={email}, exclude_id={exclude_employee_id}")
    
    result = validation_service.validate_unique(
        db=db,
        zid=zid,
        email=email,
        exclude_employee_id=exclude_employee_id
    )
    
    return EmployeeValidateUniqueResponse(**result)


@router.get("", response_model=EmployeeListResponse)
async def get_employees(
    pagination: PaginationParams = Depends(),
    sub_segment_id: Optional[int] = Query(None, description="Filter by sub-segment ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    search: Optional[str] = Query(None, description="Search by name or ZID"),
    db: Session = Depends(get_db),
    rbac_context: RbacContext = Depends(get_rbac_context)
):
    """
    Get a paginated list of employees with optional filters.
    
    RBAC: Results are filtered based on user's role and organizational scope.
    - SUPER_ADMIN: Sees all employees
    - SEGMENT_HEAD: Sees employees in their segment
    - SUBSEGMENT_HEAD: Sees employees in their sub-segment
    - PROJECT_MANAGER: Sees employees in their project
    - TEAM_LEAD/TEAM_MEMBER: Sees employees in their team
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 10)
    - **sub_segment_id**: Filter by sub-segment ID
    - **project_id**: Filter by project ID
    - **team_id**: Filter by team ID
    - **role_id**: Filter by role ID
    - **search**: Search by employee name or ZID
    """
    logger.info(f"Fetching employees with filters: sub_segment_id={sub_segment_id}, project_id={project_id}, team_id={team_id}, role_id={role_id}, search={search}, page={pagination.page}, size={pagination.size}, role={rbac_context.role}")
    
    try:
        return list_service.get_employees_paginated(
            db=db,
            pagination=pagination,
            sub_segment_id=sub_segment_id,
            project_id=project_id,
            team_id=team_id,
            role_id=role_id,
            search=search,
            rbac_context=rbac_context
        )
        
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employees"
        )


@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific employee including their skills.
    """
    logger.info(f"Fetching employee details for ID: {employee_id}")
    
    try:
        return profile_service.get_employee_profile(db, employee_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee {employee_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching employee details"
        )


@router.get("/{employee_id}/edit-bootstrap", response_model=EditBootstrapResponse)
async def get_edit_bootstrap(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all data needed to render the Edit Employee form in ONE call.
    
    Eliminates frontend waterfall calls by returning:
    - Employee data with org hierarchy IDs
    - All dropdown options (segments, sub-segments, projects, teams, roles)
    - Employee skills with proficiency IDs
    
    This endpoint is optimized for Edit mode - use standard GET /{employee_id}
    for read-only views.
    """
    logger.info(f"[EDIT-BOOTSTRAP] Fetching edit-bootstrap for employee_id={employee_id}")
    
    try:
        return edit_bootstrap_service.get_edit_bootstrap(db, employee_id)
        
    except ValueError as e:
        logger.warning(f"[EDIT-BOOTSTRAP] Employee not found: {employee_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[EDIT-BOOTSTRAP] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching edit bootstrap data"
        )


@router.post("/by-ids", response_model=EmployeesByIdsResponse)
async def get_employees_by_ids(
    request: EmployeesByIdsRequest,
    db: Session = Depends(get_db)
):
    """
    Fetch employees by a list of employee IDs.
    Returns employee data formatted for TalentResultsTable component.
    
    Args:
        request: Contains list of employee_ids
        
    Returns:
        List of employees with top skills, formatted for frontend table
    """
    logger.info(f"Fetching {len(request.employee_ids)} employees by IDs")
    
    try:
        response = by_ids_service.get_employees_by_ids(db, request.employee_ids)
        logger.info(f"Returning {len(response.results)} employees")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching employees by IDs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employees: {str(e)}"
        )


@router.post("/", response_model=EmployeeCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    request: EmployeeCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new employee record.
    
    This endpoint creates an employee with basic details only.
    Skills should be added separately via the competencies endpoints.
    
    Args:
        request: Employee creation data including:
            - zid: Unique employee identifier (required)
            - full_name: Employee's full name (required)
            - team_id: ID of the team (required)
            - email: Employee email (required)
            - role_id: Role ID from roles table (required)
            - start_date_of_working: Employment start date (optional)
    
    Returns:
        Created employee details with organization info
        
    Raises:
        404: If team_id is invalid
        409: If ZID already exists
        422: If required fields are missing/invalid or role_id is invalid
    """
    logger.info(f"Creating employee with ZID: {request.zid}")
    
    # Service handles validation and creation
    employee = create_service.create_employee(
        db=db,
        zid=request.zid,
        full_name=request.full_name,
        team_id=request.team_id,
        role_id=request.role_id,
        email=request.email,
        start_date_of_working=request.start_date_of_working,
        allocation_pct=request.allocation_pct
    )
    
    # Build response with organization info
    return EmployeeCreateResponse(
        employee_id=employee.employee_id,
        zid=employee.zid,
        full_name=employee.full_name,
        email=employee.email,
        team_id=employee.team_id,
        team_name=employee.team.team_name if employee.team else "",
        project_name=employee.project.project_name if employee.project else "",
        sub_segment_name=employee.sub_segment.sub_segment_name if employee.sub_segment else "",
        role_name=employee.role.role_name if employee.role else None,
        start_date_of_working=employee.start_date_of_working,
        message="Employee created successfully"
    )


@router.put("/{employee_id}", response_model=EmployeeCreateResponse)
async def update_employee(
    employee_id: int,
    request: EmployeeUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing employee record.
    
    This endpoint updates employee details. Only provided fields are updated.
    
    Args:
        employee_id: ID of the employee to update
        request: Employee update data (all fields optional):
            - full_name: Employee's full name
            - team_id: ID of the team
            - email: Employee email
            - role_id: Role ID from roles table
            - start_date_of_working: Employment start date
    
    Returns:
        Updated employee details with organization info
        
    Raises:
        404: If employee_id or team_id is invalid
        422: If role_id is invalid
    """
    logger.info(f"Updating employee with ID: {employee_id}")
    
    # Service handles validation and update
    employee = create_service.update_employee(
        db=db,
        employee_id=employee_id,
        full_name=request.full_name,
        team_id=request.team_id,
        email=request.email,
        role_id=request.role_id,
        start_date_of_working=request.start_date_of_working,
        allocation_pct=request.allocation_pct
    )

   
    # Build response with organization info
    return EmployeeCreateResponse(
        employee_id=employee.employee_id,
        zid=employee.zid,
        full_name=employee.full_name,
        email=employee.email,
        team_id=employee.team_id,
        team_name=employee.team.team_name if employee.team else "",
        project_name=employee.project.project_name if employee.project else "",
        sub_segment_name=employee.sub_segment.sub_segment_name if employee.sub_segment else "",
        role_name=employee.role.role_name if employee.role else None,
        start_date_of_working=employee.start_date_of_working,
        message="Employee updated successfully"
    )


@router.post(
    "/{employee_id}/skills",
    response_model=EmployeeSkillsBulkSaveResponse,
    summary="Save employee skills (replace all)",
    description="Atomically replaces all skills for an employee. Existing skills are soft-deleted and new ones are created."
)
def save_employee_skills(
    employee_id: int,
    request: EmployeeSkillsBulkSaveRequest,
    db: Session = Depends(get_db)
):
    """
    Save employee skills using replace-all strategy.
    
    - Validates employee exists
    - Validates all skill_ids exist
    - Soft-deletes existing skills
    - Creates new skill records
    - All operations are atomic (transaction)
    """
    skills_saved, skills_deleted = employee_skills_service.save_employee_skills(db, employee_id, request.skills)
    return EmployeeSkillsBulkSaveResponse(
        message="Skills saved successfully",
        employee_id=employee_id,
        skills_saved=skills_saved,
        skills_deleted=skills_deleted
    )


@router.delete(
    "/{employee_id}",
    response_model=EmployeeDeleteResponse,
    summary="Soft-delete an employee",
    description="Soft-deletes an employee by setting deleted_at timestamp. The employee record is retained but excluded from queries."
)
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft-delete an employee.
    
    This endpoint performs a soft delete by setting the deleted_at timestamp.
    The employee record is retained in the database but will be excluded 
    from all employee queries.
    
    Args:
        employee_id: ID of the employee to delete
        
    Returns:
        Confirmation message with deleted employee ID
        
    Raises:
        404: If employee not found
        400: If employee is already deleted
    """
    logger.info(f"Soft-deleting employee with ID: {employee_id}")
    
    employee = delete_service.soft_delete_employee(db, employee_id)
    
    return EmployeeDeleteResponse(
        message=f"Employee '{employee.full_name}' has been deleted successfully",
        employee_id=employee_id
    )
