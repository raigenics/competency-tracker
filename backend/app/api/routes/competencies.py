"""
API routes for competency analysis and matrix operations.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc

from app.db.session import get_db
from app.models import (
    Employee, EmployeeSkill, Skill, SkillCategory, SkillSubcategory,
    ProficiencyLevel, SubSegment, Project, Team
)
from app.schemas.competency import (
    EmployeeCompetencyProfile, CompetencyMatrixResponse, SkillDemandResponse,
    CompetencyInsights, CompetencySearchFilters, EmployeeSkillResponse,
    ProficiencyLevelResponse
)
from app.schemas.common import PaginationParams
from app.services.skill_history_service import SkillHistoryService
from app.models.skill_history import ChangeSource, ChangeAction, EmployeeSkillHistory
from app.schemas.skill_history import (
    SkillHistoryResponse, SkillUpdateRequest, SkillCreateRequest,
    SkillHistoryListResponse, SkillProgressionResponse, ProficiencyChangeResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/competencies", tags=["competencies"])


@router.get("/employee/{employee_id}/profile", response_model=EmployeeCompetencyProfile)
async def get_employee_competency_profile(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete competency profile for an employee.
    """
    logger.info(f"Fetching competency profile for employee ID: {employee_id}")
    
    try:
        employee = db.query(Employee).options(
            joinedload(Employee.sub_segment),
            joinedload(Employee.project),
            joinedload(Employee.team),
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill).joinedload(Skill.category),
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.proficiency_level)
        ).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found"
            )
          # Build skills list
        skills = []
        competency_summary = {"Beginner": 0, "Intermediate": 0, "Advanced": 0, "Expert": 0}
        
        for emp_skill in employee.employee_skills:
            skill_data = EmployeeSkillResponse(
                emp_skill_id=emp_skill.emp_skill_id,
                employee_id=emp_skill.employee_id,
                employee_name=employee.full_name,
                skill_id=emp_skill.skill_id,
                skill_name=emp_skill.skill.skill_name,
                category=emp_skill.skill.category.category_name if emp_skill.skill.category else None,
                proficiency=ProficiencyLevelResponse(
                    proficiency_level_id=emp_skill.proficiency_level.proficiency_level_id,
                    level_name=emp_skill.proficiency_level.level_name,
                    level_description=emp_skill.proficiency_level.level_description
                ),
                years_experience=emp_skill.years_experience,
                last_used=emp_skill.last_used,
                interest_level=emp_skill.interest_level,
                last_updated=emp_skill.last_updated,
                certification=emp_skill.certification
            )
            skills.append(skill_data)
            
            # Update competency summary
            level_name = emp_skill.proficiency_level.level_name
            if level_name in competency_summary:
                competency_summary[level_name] += 1
        
        # Get top skills (Advanced/Expert with high experience or interest)
        top_skills = []
        for emp_skill in employee.employee_skills:
            if emp_skill.proficiency_level.level_name in ["Advanced", "Expert"]:
                top_skills.append({
                    "skill_name": emp_skill.skill.skill_name,
                    "proficiency": emp_skill.proficiency_level.level_name,
                    "years_experience": emp_skill.years_experience or 0,
                    "interest_level": emp_skill.interest_level or 0
                })
        
        # Sort by proficiency level and experience
        proficiency_order = {"Expert": 4, "Advanced": 3, "Intermediate": 2, "Beginner": 1}
        top_skills.sort(
            key=lambda x: (proficiency_order.get(x["proficiency"], 0), x["years_experience"]),
            reverse=True
        )
        
        return EmployeeCompetencyProfile(
            employee_id=employee.employee_id,
            employee_name=employee.full_name,
            role=employee.role,
            organization={
                "sub_segment": employee.sub_segment.sub_segment_name,
                "project": employee.project.project_name,
                "team": employee.team.team_name
            },
            skills=skills,
            competency_summary=competency_summary,
            top_skills=top_skills[:10]  # Top 10 skills
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching competency profile for employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching competency profile"
        )


@router.get("/matrix", response_model=CompetencyMatrixResponse)
async def get_competency_matrix(
    sub_segment: Optional[str] = Query(None, description="Filter by sub-segment"),
    project: Optional[str] = Query(None, description="Filter by project"),
    team: Optional[str] = Query(None, description="Filter by team"),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills to focus on"),
    db: Session = Depends(get_db)
):
    """
    Generate competency matrix for a team, project, or sub-segment.
    """
    logger.info("Generating competency matrix")
    
    try:
        # Build employee query with filters
        query = db.query(Employee).options(
            joinedload(Employee.sub_segment),
            joinedload(Employee.project),
            joinedload(Employee.team),
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill),
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.proficiency_level)
        )
        
        scope = {}
        matrix_name = "Organization Competency Matrix"
        
        if sub_segment:
            query = query.join(SubSegment).filter(SubSegment.sub_segment_name.ilike(f"%{sub_segment}%"))
            scope["sub_segment"] = sub_segment
            matrix_name = f"{sub_segment} Competency Matrix"
        
        if project:
            query = query.join(Project).filter(Project.project_name.ilike(f"%{project}%"))
            scope["project"] = project
            matrix_name = f"{project} Competency Matrix"
        
        if team:
            query = query.join(Team).filter(Team.team_name.ilike(f"%{team}%"))
            scope["team"] = team
            matrix_name = f"{team} Competency Matrix"
        
        employees = query.all()
        
        if not employees:
            # Return empty matrix instead of 404 for empty state
            return CompetencyMatrixResponse(
                matrix_name=matrix_name,
                scope=scope,
                employees=[],
                skill_coverage={},
                gap_analysis=[],
                recommendations=[]
            )
        
        # Build employee profiles
        employee_profiles = []
        all_skills = set()
        
        for employee in employees:
            # Get skills for this employee
            emp_skills = []
            competency_summary = {"Beginner": 0, "Intermediate": 0, "Advanced": 0, "Expert": 0}
            
            for emp_skill in employee.employee_skills:
                # Filter by specific skills if requested
                if skills:
                    skill_list = [s.strip() for s in skills.split(',')]
                    if emp_skill.skill.skill_name not in skill_list:
                        continue
                
                all_skills.add(emp_skill.skill.skill_name)
                
                skill_data = EmployeeSkillResponse(
                    emp_skill_id=emp_skill.emp_skill_id,
                    employee_id=emp_skill.employee_id,
                    employee_name=employee.full_name,
                    skill_id=emp_skill.skill_id,
                    skill_name=emp_skill.skill.skill_name,
                    proficiency=ProficiencyLevelResponse(
                        proficiency_level_id=emp_skill.proficiency_level.proficiency_level_id,
                        level_name=emp_skill.proficiency_level.level_name,
                        level_description=emp_skill.proficiency_level.level_description                    ),
                    years_experience=emp_skill.years_experience,
                    last_used=emp_skill.last_used,
                    interest_level=emp_skill.interest_level,
                    last_updated=emp_skill.last_updated
                )
                emp_skills.append(skill_data)
                
                level_name = emp_skill.proficiency_level.level_name
                if level_name in competency_summary:
                    competency_summary[level_name] += 1
            
            # Get top skills
            top_skills = []
            for emp_skill in employee.employee_skills:
                if emp_skill.proficiency_level.level_name in ["Advanced", "Expert"]:
                    top_skills.append({
                        "skill_name": emp_skill.skill.skill_name,
                        "proficiency": emp_skill.proficiency_level.level_name,
                        "years_experience": emp_skill.years_experience or 0,
                        "interest_level": emp_skill.interest_level or 0
                    })
            
            proficiency_order = {"Expert": 4, "Advanced": 3, "Intermediate": 2, "Beginner": 1}
            top_skills.sort(
                key=lambda x: (proficiency_order.get(x["proficiency"], 0), x["years_experience"]),
                reverse=True
            )
            
            profile = EmployeeCompetencyProfile(
                employee_id=employee.employee_id,
                employee_name=employee.full_name,
                role=employee.role,
                organization={
                    "sub_segment": employee.sub_segment.sub_segment_name,
                    "project": employee.project.project_name,
                    "team": employee.team.team_name
                },
                skills=emp_skills,
                competency_summary=competency_summary,
                top_skills=top_skills[:5]  # Top 5 skills per employee
            )
            employee_profiles.append(profile)
        
        # Calculate skill coverage across the team/organization
        skill_coverage = {}
        for skill_name in all_skills:
            skill_coverage[skill_name] = {"Beginner": 0, "Intermediate": 0, "Advanced": 0, "Expert": 0}
            
            for profile in employee_profiles:
                for skill in profile.skills:
                    if skill.skill_name == skill_name:
                        level_name = skill.proficiency.level_name
                        skill_coverage[skill_name][level_name] += 1
        
        # Simple gap analysis - identify skills with low coverage
        gap_analysis = []
        recommendations = []
        
        for skill_name, coverage in skill_coverage.items():
            total_employees = sum(coverage.values())
            expert_ratio = coverage["Expert"] / total_employees if total_employees > 0 else 0
            advanced_ratio = (coverage["Advanced"] + coverage["Expert"]) / total_employees if total_employees > 0 else 0
            
            if expert_ratio < 0.1:  # Less than 10% experts
                gap_analysis.append({
                    "skill_name": skill_name,
                    "required_proficiency": "Expert",
                    "current_proficiency": "Intermediate" if advanced_ratio > 0.3 else "Beginner",
                    "gap_severity": "High" if expert_ratio == 0 else "Medium",
                    "recommended_action": "Skill development program or expert hiring"
                })
        
        if len(gap_analysis) > 0:
            recommendations.append("Focus on developing expert-level competencies in identified gap areas")
        
        if len(employee_profiles) > 10:
            recommendations.append("Consider cross-training programs to improve skill distribution")
        
        return CompetencyMatrixResponse(
            matrix_name=matrix_name,
            scope=scope,
            employees=employee_profiles,
            skill_coverage=skill_coverage,
            gap_analysis=gap_analysis[:10],  # Top 10 gaps
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating competency matrix: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating competency matrix"
        )


@router.get("/insights", response_model=CompetencyInsights)
async def get_competency_insights(db: Session = Depends(get_db)):
    """
    Get high-level competency insights and trends.
    """
    logger.info("Fetching competency insights")
    
    try:
        # Total counts
        total_skills = db.query(func.count(Skill.skill_id.distinct())).scalar()
        total_assessments = db.query(func.count(EmployeeSkill.emp_skill_id)).scalar()
        
        # Identify skill gaps (skills with low expert coverage)
        skill_gaps = []
        expert_level_id = db.query(ProficiencyLevel.proficiency_level_id).filter(
            ProficiencyLevel.level_name == "Expert"
        ).scalar()
        
        if expert_level_id:
            skills_with_low_experts = db.query(
                Skill.skill_name,
                func.count(EmployeeSkill.emp_skill_id).label('expert_count')
            ).join(EmployeeSkill).filter(
                EmployeeSkill.proficiency_level_id == expert_level_id
            ).group_by(Skill.skill_name).having(
                func.count(EmployeeSkill.emp_skill_id) < 2
            ).all()
            
            skill_gaps = [skill_name for skill_name, count in skills_with_low_experts]
        
        # Strongest skills (most experts)
        strongest_skills = [
            skill_name for skill_name, count in
            db.query(Skill.skill_name, func.count(EmployeeSkill.emp_skill_id))
            .join(EmployeeSkill)
            .filter(EmployeeSkill.proficiency_level_id == expert_level_id)
            .group_by(Skill.skill_name)
            .order_by(desc(func.count(EmployeeSkill.emp_skill_id)))
            .limit(10)
            .all()
        ]
        
        # Emerging skills (high interest but lower experience)
        emerging_skills = []
        high_interest_skills = db.query(
            Skill.skill_name,
            func.avg(EmployeeSkill.interest_level).label('avg_interest'),
            func.avg(EmployeeSkill.years_experience).label('avg_experience')
        ).join(EmployeeSkill).filter(
            EmployeeSkill.interest_level.isnot(None),
            EmployeeSkill.years_experience.isnot(None)
        ).group_by(Skill.skill_name).having(
            func.avg(EmployeeSkill.interest_level) > 4.0
        ).order_by(desc(func.avg(EmployeeSkill.interest_level))).all()
        
        for skill_name, avg_interest, avg_experience in high_interest_skills[:10]:
            if avg_experience < 3:  # Low experience but high interest
                emerging_skills.append(skill_name)
        
        # Generate recommendations
        recommendations = []
        if len(skill_gaps) > 5:
            recommendations.append(f"Address {len(skill_gaps)} skill gaps through training or recruitment")
        
        if len(emerging_skills) > 0:
            recommendations.append(f"Invest in {len(emerging_skills)} emerging skills with high interest")
        
        if total_assessments > 0:
            avg_skills_per_employee = total_assessments / db.query(func.count(Employee.employee_id.distinct())).scalar()
            if avg_skills_per_employee < 5:
                recommendations.append("Encourage broader skill development across the organization")
        
        return CompetencyInsights(
            total_skills=total_skills,
            total_assessments=total_assessments,
            skill_gaps=skill_gaps[:10],
            strongest_skills=strongest_skills[:10],
            emerging_skills=emerging_skills[:10],
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error fetching competency insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching competency insights"
        )


@router.get("/search", response_model=List[EmployeeSkillResponse])
async def search_competencies(
    filters: CompetencySearchFilters = Depends(),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    Search for employee competencies with advanced filtering.
    """
    logger.info("Searching competencies with filters")
    
    try:
        # Build complex query
        query = db.query(EmployeeSkill).options(
            joinedload(EmployeeSkill.employee).joinedload(Employee.sub_segment),
            joinedload(EmployeeSkill.employee).joinedload(Employee.project),
            joinedload(EmployeeSkill.employee).joinedload(Employee.team),
            joinedload(EmployeeSkill.skill).joinedload(Skill.category),
            joinedload(EmployeeSkill.skill).joinedload(Skill.subcategory),
            joinedload(EmployeeSkill.proficiency_level)
        )
        
        # Apply filters
        if filters.skill_names:
            query = query.join(Skill).filter(Skill.skill_name.in_(filters.skill_names))
        
        if filters.categories:
            query = query.join(Skill).join(SkillCategory).filter(
                SkillCategory.category_name.in_(filters.categories)
            )
        
        if filters.subcategories:
            query = query.join(Skill).join(SkillSubcategory).filter(
                SkillSubcategory.subcategory_name.in_(filters.subcategories)
            )
        
        if filters.proficiency_levels:
            query = query.join(ProficiencyLevel).filter(
                ProficiencyLevel.level_name.in_(filters.proficiency_levels)
            )
        
        if filters.min_experience is not None:
            query = query.filter(
                EmployeeSkill.years_experience >= filters.min_experience
            )
        
        if filters.min_interest is not None:
            query = query.filter(
                EmployeeSkill.interest_level >= filters.min_interest
            )
        
        if filters.sub_segments:
            query = query.join(Employee).join(SubSegment).filter(
                SubSegment.sub_segment_name.in_(filters.sub_segments)
            )
        
        if filters.projects:
            query = query.join(Employee).join(Project).filter(
                Project.project_name.in_(filters.projects)
            )
        
        if filters.teams:
            query = query.join(Employee).join(Team).filter(
                Team.team_name.in_(filters.teams)
            )
        
        # Apply pagination
        results = query.offset(pagination.offset).limit(pagination.size).all()
        
        # Build response
        response_items = []
        for emp_skill in results:
            skill_data = EmployeeSkillResponse(
                emp_skill_id=emp_skill.emp_skill_id,
                employee_id=emp_skill.employee_id,
                employee_name=emp_skill.employee.full_name,
                skill_id=emp_skill.skill_id,
                skill_name=emp_skill.skill.skill_name,
                proficiency=ProficiencyLevelResponse(
                    proficiency_level_id=emp_skill.proficiency_level.proficiency_level_id,
                    level_name=emp_skill.proficiency_level.level_name,
                    level_description=emp_skill.proficiency_level.level_description                ),
                years_experience=emp_skill.years_experience,
                last_used=emp_skill.last_used,
                interest_level=emp_skill.interest_level,
                last_updated=emp_skill.last_updated
            )
            response_items.append(skill_data)
        
        return response_items
        
    except Exception as e:
        logger.error(f"Error searching competencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching competencies"
        )


# ==================== SKILL HISTORY TRACKING ENDPOINTS ====================

@router.put("/employee-skill/{emp_skill_id}")
async def update_employee_skill(
    emp_skill_id: int,
    request: SkillUpdateRequest,
    changed_by: Optional[str] = Query(None, description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Update an employee skill with history tracking.
    """
    logger.info(f"Updating employee skill {emp_skill_id}")
    
    try:
        history_service = SkillHistoryService(db)
        
        updated_skill, history_record = history_service.update_skill_with_history(
            emp_skill_id=emp_skill_id,
            proficiency_level_id=request.proficiency_level_id,
            years_experience=request.years_experience,
            certification=request.certification,
            change_source=ChangeSource.UI,
            changed_by=changed_by,
            change_reason=request.change_reason
        )
        
        db.commit()
        
        return {
            "message": "Employee skill updated successfully",
            "emp_skill_id": updated_skill.emp_skill_id,
            "history_id": history_record.history_id,
            "updated_fields": {
                k: v for k, v in request.dict(exclude_unset=True).items() 
                if v is not None
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating employee skill: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating employee skill"
        )


@router.post("/employee-skill")
async def create_employee_skill(
    request: SkillCreateRequest,
    changed_by: Optional[str] = Query(None, description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Create a new employee skill with history tracking.
    """
    logger.info(f"Creating new skill for employee {request.employee_id}")
    
    try:
        # Check if skill already exists for this employee
        existing = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == request.employee_id,
            EmployeeSkill.skill_id == request.skill_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee already has this skill. Use PUT to update."
            )
        
        history_service = SkillHistoryService(db)
        
        new_skill, history_record = history_service.create_skill_with_history(
            employee_id=request.employee_id,
            skill_id=request.skill_id,
            proficiency_level_id=request.proficiency_level_id,
            years_experience=request.years_experience,
            certification=request.certification,
            change_source=ChangeSource.UI,
            changed_by=changed_by,
            change_reason=request.change_reason
        )
        
        db.commit()
        
        return {
            "message": "Employee skill created successfully",
            "emp_skill_id": new_skill.emp_skill_id,
            "history_id": history_record.history_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating employee skill: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating employee skill"
        )


@router.get("/employee/{employee_id}/skill-history", response_model=SkillHistoryListResponse)
async def get_employee_skill_history(
    employee_id: int,
    pagination: PaginationParams = Depends(),
    skill_id: Optional[int] = Query(None, description="Filter by specific skill"),
    db: Session = Depends(get_db)
):
    """
    Get skill change history for an employee.
    """
    logger.info(f"Fetching skill history for employee {employee_id}")
    
    try:
        # Build query with joins for readable names
        query = db.query(EmployeeSkillHistory).options(
            joinedload(EmployeeSkillHistory.employee),
            joinedload(EmployeeSkillHistory.skill),
            joinedload(EmployeeSkillHistory.old_proficiency),
            joinedload(EmployeeSkillHistory.new_proficiency)
        ).filter(EmployeeSkillHistory.employee_id == employee_id)
        
        if skill_id:
            query = query.filter(EmployeeSkillHistory.skill_id == skill_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        history_records = query.order_by(
            EmployeeSkillHistory.changed_at.desc()
        ).offset(pagination.offset).limit(pagination.size).all()
        
        # Build response items
        response_items = []
        for record in history_records:
            item = SkillHistoryResponse(
                history_id=record.history_id,
                employee_id=record.employee_id,
                employee_name=record.employee.full_name if record.employee else None,
                skill_id=record.skill_id,
                skill_name=record.skill.skill_name if record.skill else None,
                emp_skill_id=record.emp_skill_id,
                action=record.action,
                changed_at=record.changed_at,
                change_source=record.change_source,
                changed_by=record.changed_by,
                change_reason=record.change_reason,
                batch_id=record.batch_id,
                old_proficiency_level_id=record.old_proficiency_level_id,
                old_proficiency_name=record.old_proficiency.level_name if record.old_proficiency else None,
                old_years_experience=record.old_years_experience,
                old_certification=record.old_certification,
                new_proficiency_level_id=record.new_proficiency_level_id,
                new_proficiency_name=record.new_proficiency.level_name if record.new_proficiency else None,
                new_years_experience=record.new_years_experience,
                new_certification=record.new_certification
            )
            response_items.append(item)
        
        return SkillHistoryListResponse.create(response_items, total, pagination)
        
    except Exception as e:
        logger.error(f"Error fetching skill history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill history"
        )


@router.get("/skill/{skill_id}/progression", response_model=List[SkillProgressionResponse])
async def get_skill_progression(
    skill_id: int,
    employee_id: Optional[int] = Query(None, description="Filter by specific employee"),
    db: Session = Depends(get_db)
):
    """
    Get skill progression over time for employees.
    Shows how proficiency has changed.
    """
    logger.info(f"Fetching skill progression for skill {skill_id}")
    
    try:
        # Query proficiency changes (using the simplified table)
        from app.models.skill_history import ProficiencyChangeHistory
        
        query = db.query(ProficiencyChangeHistory).options(
            joinedload(ProficiencyChangeHistory.employee),
            joinedload(ProficiencyChangeHistory.skill),
            joinedload(ProficiencyChangeHistory.from_proficiency),
            joinedload(ProficiencyChangeHistory.to_proficiency)
        ).filter(ProficiencyChangeHistory.skill_id == skill_id)
        
        if employee_id:
            query = query.filter(ProficiencyChangeHistory.employee_id == employee_id)
        
        changes = query.order_by(
            ProficiencyChangeHistory.employee_id,
            ProficiencyChangeHistory.changed_at
        ).all()
        
        # Group by employee
        employee_progressions = {}
        for change in changes:
            emp_id = change.employee_id
            if emp_id not in employee_progressions:
                employee_progressions[emp_id] = {
                    "employee_name": change.employee.full_name,
                    "skill_name": change.skill.skill_name,
                    "changes": []
                }
            
            change_response = ProficiencyChangeResponse(
                change_id=change.change_id,
                employee_id=change.employee_id,
                employee_name=change.employee.full_name,
                skill_id=change.skill_id,
                skill_name=change.skill.skill_name,
                from_proficiency_id=change.from_proficiency_id,
                from_proficiency_name=change.from_proficiency.level_name if change.from_proficiency else "New",
                to_proficiency_id=change.to_proficiency_id,
                to_proficiency_name=change.to_proficiency.level_name,
                changed_at=change.changed_at,
                change_source=change.change_source,
                changed_by=change.changed_by,
                change_reason=change.change_reason,
                batch_id=change.batch_id
            )
            employee_progressions[emp_id]["changes"].append(change_response)
        
        # Build response
        response = []
        for emp_id, data in employee_progressions.items():
            if not data["changes"]:
                continue
                
            # Determine trend (simple: compare first and last)
            changes_list = data["changes"]
            if len(changes_list) == 1:
                trend = "stable"
            else:
                # Simple proficiency level comparison
                first_level = changes_list[0].from_proficiency_id or 0
                last_level = changes_list[-1].to_proficiency_id
                if last_level > first_level:
                    trend = "improving"
                elif last_level < first_level:
                    trend = "declining"
                else:
                    trend = "stable"
            
            progression = SkillProgressionResponse(
                employee_id=emp_id,
                employee_name=data["employee_name"],
                skill_id=skill_id,
                skill_name=data["skill_name"],
                progression=changes_list,
                current_proficiency=changes_list[-1].to_proficiency_name,
                progression_trend=trend
            )
            response.append(progression)
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching skill progression: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching skill progression"
        )
