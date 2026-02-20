"""
Search service for Capability Finder.

Handles searching for employees matching specified skill and organizational criteria.

PHASE 1 HYBRID SEARCH:
- STRICT match: AND logic - employee must have ALL specified skills
- PARTIAL fallback: OR logic - if strict returns empty, fallback to employees with ≥1 skill
- Case-insensitive skill + role matching
- Skill alias resolution via skill_aliases table
- Soft-delete filtering for Employee, EmployeeSkill, Skill, Role
- Both team_id AND sub_segment_id filters can apply together
- Subquery-first pattern to avoid early join explosion
- Deterministic ordering
- selectinload for N+1 prevention

API contracts preserved (new fields are additive only)

TODO (Phase 2): Embeddings-based semantic search when skill_embeddings table is populated
"""
from typing import List, Optional, Set, Tuple, Dict, Any
import re
from sqlalchemy.orm import Session, selectinload, Query
from sqlalchemy import distinct, func, and_, or_, desc, asc

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.role import Role
from app.models.employee import Employee
from app.models.employee_skill import EmployeeSkill
from app.models.team import Team
from app.models.project import Project
from app.schemas.capability_finder import EmployeeSearchResult, SkillInfo


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Optional confidence threshold for skill aliases.
# Set to None to include all aliases regardless of confidence.
# Set to a float (e.g., 0.8) to only include aliases with confidence >= threshold.
ALIAS_CONFIDENCE_THRESHOLD: Optional[float] = None


# =============================================================================
# PUBLIC API
# =============================================================================

def search_matching_talent(
    db: Session,
    skills: List[str],
    sub_segment_id: Optional[int] = None,
    team_id: Optional[int] = None,
    role: Optional[str] = None,
    min_proficiency: int = 0,
    min_experience_years: int = 0
) -> List[EmployeeSearchResult]:
    """
    Search for employees matching specified criteria using HYBRID search strategy.
    
    HYBRID SEARCH STRATEGY:
    1. STRICT match (AND logic): Return employees who have ALL specified skills
    2. PARTIAL fallback (OR logic): If strict returns empty, return employees with ≥1 skill
    
    Features:
    - Case-insensitive skill matching ("react" matches "React")
    - Alias expansion ("ReactJS" resolves to canonical "React" skill)
    - Soft-delete filtering (excludes deleted employees/skills/employee_skills/roles)
    - Both team_id and sub_segment_id can apply together
    - Case-insensitive role matching
    - Deterministic ordering (matched_skill_count DESC for partial, name ASC, id ASC)
    
    Args:
        db: Database session
        skills: List of required skill names (AND logic first, OR fallback)
        sub_segment_id: Optional sub-segment filter
        team_id: Optional team filter
        role: Optional role name filter (case-insensitive)
        min_proficiency: Minimum proficiency level (0-5, applies to required skills)
        min_experience_years: Minimum years of experience (applies to required skills)
        
    Returns:
        List of matching employees with their top 3 skills and match metadata
        
    Example:
        >>> results = search_matching_talent(
        ...     db=db,
        ...     skills=['react', 'AWS'],
        ...     min_proficiency=3,
        ...     team_id=5
        ... )
        >>> # STRICT: Returns employees who have BOTH React AND AWS
        >>> # PARTIAL: If none found, returns employees with React OR AWS
    """
    # Normalize skill terms and resolve to canonical skill IDs
    normalized_terms = _normalize_skill_terms(skills) if skills else []
    canonical_skill_ids = _resolve_canonical_skill_ids(db, normalized_terms) if normalized_terms else set()
    
    # If skills were requested but none resolved, return empty result immediately
    if skills and len(skills) > 0 and not canonical_skill_ids:
        return []
    
    # Normalize role for case-insensitive matching
    normalized_role = role.strip().lower() if role else None
    
    # STEP 1: Try STRICT match (AND logic - all skills required)
    if canonical_skill_ids:
        strict_results = _query_strict_match(
            db=db,
            canonical_skill_ids=canonical_skill_ids,
            sub_segment_id=sub_segment_id,
            team_id=team_id,
            normalized_role=normalized_role,
            min_proficiency=min_proficiency,
            min_experience_years=min_experience_years
        )
        
        if strict_results:
            # Build results with STRICT match type
            return _build_results(
                db=db,
                employees=strict_results,
                match_type="STRICT",
                matched_skill_count=len(canonical_skill_ids)
            )
        
        # STEP 2: PARTIAL fallback (OR logic - at least 1 skill)
        partial_results = _query_partial_match(
            db=db,
            canonical_skill_ids=canonical_skill_ids,
            sub_segment_id=sub_segment_id,
            team_id=team_id,
            normalized_role=normalized_role,
            min_proficiency=min_proficiency,
            min_experience_years=min_experience_years
        )
        
        return partial_results
    
    # No skills specified - org-only search (return all matching org filters)
    employees = _query_org_only(
        db=db,
        sub_segment_id=sub_segment_id,
        team_id=team_id,
        normalized_role=normalized_role
    )
    
    return _build_results(
        db=db,
        employees=employees,
        match_type=None,
        matched_skill_count=None
    )


# =============================================================================
# SKILL NORMALIZATION AND RESOLUTION
# =============================================================================

def _normalize_skill_terms(skill_terms: List[str]) -> List[str]:
    """
    Normalize incoming skill search terms for consistent matching.
    
    Normalization rules:
    - Strip leading/trailing whitespace
    - Collapse multiple internal spaces to single space
    - Convert to lowercase for case-insensitive matching
    
    Args:
        skill_terms: Raw skill terms from user input
        
    Returns:
        List of normalized, lowercase skill terms
        
    Example:
        >>> _normalize_skill_terms(["  React JS ", "AWS ", "  docker"])
        ['react js', 'aws', 'docker']
    """
    normalized = []
    for term in skill_terms:
        if term is None:
            continue
        # Strip whitespace and collapse multiple spaces
        cleaned = re.sub(r'\s+', ' ', term.strip())
        if cleaned:
            normalized.append(cleaned.lower())
    return normalized


def _resolve_canonical_skill_ids(
    db: Session, 
    normalized_terms: List[str]
) -> Set[int]:
    """
    Resolve normalized skill terms to canonical skill IDs.
    
    Resolution strategy:
    1. Match against skills.skill_name (case-insensitive)
    2. Match against skill_aliases.alias_text (case-insensitive)
    3. Union results and return unique skill_ids
    
    CRITICAL: Multiple aliases/terms may map to the same canonical skill_id.
    The returned set contains unique skill IDs only, which is critical
    for correct AND logic (count of distinct required skills).
    
    Example: ["react", "reactjs"] both mapping to skill_id=42 → returns {42}
             Required skill count = 1, not 2
    
    Args:
        db: Database session
        normalized_terms: Lowercase, cleaned skill terms
        
    Returns:
        Set of unique canonical skill_ids
    """
    if not normalized_terms:
        return set()
    
    skill_ids: Set[int] = set()
    
    # 1. Match from skills table (case-insensitive, excluding soft-deleted)
    skill_matches = db.query(Skill.skill_id).filter(
        func.lower(Skill.skill_name).in_(normalized_terms),
        Skill.deleted_at.is_(None)
    ).all()
    skill_ids.update(s[0] for s in skill_matches)
    
    # 2. Match from skill_aliases table (case-insensitive)
    alias_query = db.query(SkillAlias.skill_id).filter(
        func.lower(SkillAlias.alias_text).in_(normalized_terms)
    )
    
    # Apply confidence threshold if configured
    if ALIAS_CONFIDENCE_THRESHOLD is not None:
        alias_query = alias_query.filter(
            or_(
                SkillAlias.confidence_score.is_(None),
                SkillAlias.confidence_score >= ALIAS_CONFIDENCE_THRESHOLD
            )
        )
    
    # Join to Skill to ensure the canonical skill is not deleted
    alias_query = alias_query.join(
        Skill, SkillAlias.skill_id == Skill.skill_id
    ).filter(Skill.deleted_at.is_(None))
    
    alias_matches = alias_query.all()
    skill_ids.update(s[0] for s in alias_matches)
    
    return skill_ids


# =============================================================================
# STRICT MATCH QUERY (AND LOGIC)
# =============================================================================

def _query_strict_match(
    db: Session,
    canonical_skill_ids: Set[int],
    sub_segment_id: Optional[int],
    team_id: Optional[int],
    normalized_role: Optional[str],
    min_proficiency: int,
    min_experience_years: int
) -> List[Employee]:
    """
    Query employees who have ALL required skills (STRICT AND logic).
    
    Uses subquery-first pattern:
    1. Build subquery to find employee_ids with ALL skills
    2. Load Employee objects via IN(subquery)
    3. Use selectinload for relationships to avoid N+1
    
    Args:
        db: Database session
        canonical_skill_ids: Set of required skill IDs (must have ALL)
        sub_segment_id: Optional sub-segment filter
        team_id: Optional team filter
        normalized_role: Optional role name (lowercase)
        min_proficiency: Minimum proficiency level
        min_experience_years: Minimum years of experience
        
    Returns:
        List of Employee objects matching ALL skills, ordered by name, id
    """
    required_count = len(canonical_skill_ids)
    
    # Subquery: employees who have ALL required skills
    skill_match_subquery = db.query(
        EmployeeSkill.employee_id
    ).filter(
        EmployeeSkill.deleted_at.is_(None),
        EmployeeSkill.skill_id.in_(canonical_skill_ids),
        EmployeeSkill.proficiency_level_id >= min_proficiency,
        EmployeeSkill.years_experience >= min_experience_years
    ).group_by(
        EmployeeSkill.employee_id
    ).having(
        func.count(distinct(EmployeeSkill.skill_id)) == required_count
    ).subquery()
    
    # Build employee query with org/role filters
    employee_query = _build_employee_query_with_filters(
        db=db,
        employee_id_subquery=skill_match_subquery,
        sub_segment_id=sub_segment_id,
        team_id=team_id,
        normalized_role=normalized_role
    )
    
    # Deterministic ordering: name ASC, id ASC
    employees = employee_query.order_by(
        Employee.full_name.asc(),
        Employee.employee_id.asc()
    ).all()
    
    return employees


# =============================================================================
# PARTIAL MATCH QUERY (OR LOGIC FALLBACK)
# =============================================================================

def _query_partial_match(
    db: Session,
    canonical_skill_ids: Set[int],
    sub_segment_id: Optional[int],
    team_id: Optional[int],
    normalized_role: Optional[str],
    min_proficiency: int,
    min_experience_years: int
) -> List[EmployeeSearchResult]:
    """
    Query employees who have at least ONE required skill (PARTIAL OR logic).
    
    Used as fallback when STRICT match returns empty.
    Orders by matched_skill_count DESC for relevance.
    
    Args:
        db: Database session
        canonical_skill_ids: Set of required skill IDs (must have ≥1)
        sub_segment_id: Optional sub-segment filter
        team_id: Optional team filter
        normalized_role: Optional role name (lowercase)
        min_proficiency: Minimum proficiency level
        min_experience_years: Minimum years of experience
        
    Returns:
        List of EmployeeSearchResult with match metadata, ordered by relevance
    """
    # Subquery: employees with ≥1 skill and their match count
    skill_match_query = db.query(
        EmployeeSkill.employee_id,
        func.count(distinct(EmployeeSkill.skill_id)).label('matched_count')
    ).filter(
        EmployeeSkill.deleted_at.is_(None),
        EmployeeSkill.skill_id.in_(canonical_skill_ids),
        EmployeeSkill.proficiency_level_id >= min_proficiency,
        EmployeeSkill.years_experience >= min_experience_years
    ).group_by(
        EmployeeSkill.employee_id
    ).having(
        func.count(distinct(EmployeeSkill.skill_id)) >= 1
    ).subquery()
    
    # Build employee query with org/role filters and matched_count
    employee_query = db.query(
        Employee,
        skill_match_query.c.matched_count
    ).join(
        skill_match_query,
        Employee.employee_id == skill_match_query.c.employee_id
    ).filter(
        Employee.deleted_at.is_(None)
    ).options(
        selectinload(Employee.team),
        selectinload(Employee.role)
    )
    
    # Apply org filters (BOTH can apply together)
    if team_id is not None:
        employee_query = employee_query.filter(Employee.team_id == team_id)
    
    if sub_segment_id is not None:
        employee_query = employee_query.join(
            Team, Employee.team_id == Team.team_id
        ).join(
            Project, Team.project_id == Project.project_id
        ).filter(Project.sub_segment_id == sub_segment_id)
    
    # Apply role filter (case-insensitive) with soft-delete check
    if normalized_role is not None:
        employee_query = employee_query.join(
            Role, Employee.role_id == Role.role_id
        ).filter(
            func.lower(Role.role_name) == normalized_role,
            Role.deleted_at.is_(None)
        )
    
    # Order by: matched_count DESC, name ASC, id ASC
    results = employee_query.order_by(
        desc(skill_match_query.c.matched_count),
        Employee.full_name.asc(),
        Employee.employee_id.asc()
    ).all()
    
    # Build results with PARTIAL match type and individual matched_count
    employee_results = []
    for employee, matched_count in results:
        top_skills = _query_employee_top_skills(db, employee.employee_id)
        employee_result = _build_employee_result(
            employee=employee,
            top_skills=top_skills,
            match_type="PARTIAL",
            matched_skill_count=matched_count
        )
        employee_results.append(employee_result)
    
    return employee_results


# =============================================================================
# ORG-ONLY QUERY (NO SKILLS FILTER)
# =============================================================================

def _query_org_only(
    db: Session,
    sub_segment_id: Optional[int],
    team_id: Optional[int],
    normalized_role: Optional[str]
) -> List[Employee]:
    """
    Query employees with org/role filters only (no skill requirement).
    
    Used when skills list is empty.
    
    Args:
        db: Database session
        sub_segment_id: Optional sub-segment filter
        team_id: Optional team filter
        normalized_role: Optional role name (lowercase)
        
    Returns:
        List of Employee objects ordered by name, id
    """
    employee_query = db.query(Employee).filter(
        Employee.deleted_at.is_(None)
    ).options(
        selectinload(Employee.team),
        selectinload(Employee.role)
    )
    
    # Apply org filters (BOTH can apply together)
    if team_id is not None:
        employee_query = employee_query.filter(Employee.team_id == team_id)
    
    if sub_segment_id is not None:
        employee_query = employee_query.join(
            Team, Employee.team_id == Team.team_id
        ).join(
            Project, Team.project_id == Project.project_id
        ).filter(Project.sub_segment_id == sub_segment_id)
    
    # Apply role filter (case-insensitive) with soft-delete check
    if normalized_role is not None:
        employee_query = employee_query.join(
            Role, Employee.role_id == Role.role_id
        ).filter(
            func.lower(Role.role_name) == normalized_role,
            Role.deleted_at.is_(None)
        )
    
    return employee_query.order_by(
        Employee.full_name.asc(),
        Employee.employee_id.asc()
    ).all()


# =============================================================================
# SHARED QUERY HELPERS
# =============================================================================

def _build_employee_query_with_filters(
    db: Session,
    employee_id_subquery,
    sub_segment_id: Optional[int],
    team_id: Optional[int],
    normalized_role: Optional[str]
) -> Query:
    """
    Build Employee query with org/role filters applied.
    
    Uses selectinload for relationships to avoid N+1 queries.
    
    Args:
        db: Database session
        employee_id_subquery: Subquery returning employee_id column
        sub_segment_id: Optional sub-segment filter
        team_id: Optional team filter
        normalized_role: Optional role name (lowercase)
        
    Returns:
        SQLAlchemy Query object (not executed yet)
    """
    employee_query = db.query(Employee).filter(
        Employee.employee_id.in_(db.query(employee_id_subquery.c.employee_id)),
        Employee.deleted_at.is_(None)
    ).options(
        selectinload(Employee.team),
        selectinload(Employee.role)
    )
    
    # Apply org filters (BOTH can apply together)
    if team_id is not None:
        employee_query = employee_query.filter(Employee.team_id == team_id)
    
    if sub_segment_id is not None:
        employee_query = employee_query.join(
            Team, Employee.team_id == Team.team_id
        ).join(
            Project, Team.project_id == Project.project_id
        ).filter(Project.sub_segment_id == sub_segment_id)
    
    # Apply role filter (case-insensitive) with soft-delete check
    if normalized_role is not None:
        employee_query = employee_query.join(
            Role, Employee.role_id == Role.role_id
        ).filter(
            func.lower(Role.role_name) == normalized_role,
            Role.deleted_at.is_(None)
        )
    
    return employee_query


def _build_results(
    db: Session,
    employees: List[Employee],
    match_type: Optional[str],
    matched_skill_count: Optional[int]
) -> List[EmployeeSearchResult]:
    """
    Build EmployeeSearchResult list from Employee objects.
    
    Args:
        db: Database session
        employees: List of Employee objects
        match_type: "STRICT", "PARTIAL", or None
        matched_skill_count: Number of matched skills (same for all if STRICT)
        
    Returns:
        List of EmployeeSearchResult objects
    """
    results = []
    for employee in employees:
        top_skills = _query_employee_top_skills(db, employee.employee_id)
        employee_result = _build_employee_result(
            employee=employee,
            top_skills=top_skills,
            match_type=match_type,
            matched_skill_count=matched_skill_count
        )
        results.append(employee_result)
    return results


# =============================================================================
# TOP SKILLS QUERY
# =============================================================================

def _query_employee_top_skills(db: Session, employee_id: int) -> List[tuple]:
    """
    Query top 3 skills for an employee.
    
    Skills are ordered by:
    1. Proficiency level (DESC)
    2. Last used date (DESC)
    3. Skill name (ASC)
    
    Excludes:
    - Soft-deleted EmployeeSkill records (deleted_at IS NOT NULL)
    - Soft-deleted Skill records (deleted_at IS NOT NULL)
    
    Args:
        db: Database session
        employee_id: Employee ID
        
    Returns:
        List of tuples (skill_name, proficiency_level_id)
    """
    top_skills_query = db.query(
        Skill.skill_name,
        EmployeeSkill.proficiency_level_id
    ).join(
        EmployeeSkill, EmployeeSkill.skill_id == Skill.skill_id
    ).filter(
        EmployeeSkill.employee_id == employee_id,
        EmployeeSkill.deleted_at.is_(None),
        Skill.deleted_at.is_(None)
    ).order_by(
        EmployeeSkill.proficiency_level_id.desc(),
        EmployeeSkill.last_used.desc(),
        Skill.skill_name.asc()
    ).limit(3).all()
    
    return top_skills_query


# =============================================================================
# RESULT BUILDING
# =============================================================================

def _build_employee_result(
    employee: Employee,
    top_skills: List[tuple],
    match_type: Optional[str] = None,
    matched_skill_count: Optional[int] = None
) -> EmployeeSearchResult:
    """
    Build EmployeeSearchResult from employee and top skills data.
    
    Pure transformation helper - no DB access, no side effects.
    
    Args:
        employee: Employee model instance
        top_skills: List of tuples (skill_name, proficiency_level_id)
        match_type: "STRICT", "PARTIAL", or None
        matched_skill_count: Number of matched skills
        
    Returns:
        EmployeeSearchResult schema object
    """
    # Transform top skills to SkillInfo objects
    skills_info = [
        SkillInfo(name=skill_name, proficiency=proficiency)
        for skill_name, proficiency in top_skills
    ]
    
    # Extract organization info
    sub_segment_name = employee.sub_segment.sub_segment_name if employee.sub_segment else ""
    team_name = employee.team.team_name if employee.team else ""
    role_name = employee.role.role_name if employee.role else ""
    
    # Build result object
    return EmployeeSearchResult(
        employee_id=employee.employee_id,
        employee_name=employee.full_name,
        sub_segment=sub_segment_name,
        team=team_name,
        role=role_name,
        top_skills=skills_info,
        match_type=match_type,
        matched_skill_count=matched_skill_count
    )


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================

def _query_skill_ids(db: Session, skill_names: List[str]) -> List[int]:
    """
    Query skill IDs for given skill names (case-insensitive, with aliases).
    
    DEPRECATED: Use _resolve_canonical_skill_ids instead.
    Kept for backward compatibility with existing tests.
    
    Args:
        db: Database session
        skill_names: List of skill names
        
    Returns:
        List of skill IDs
    """
    normalized = _normalize_skill_terms(skill_names)
    skill_ids = _resolve_canonical_skill_ids(db, normalized)
    return list(skill_ids)


def _query_matching_employees(
    db: Session,
    skills: List[str],
    sub_segment_id: Optional[int],
    team_id: Optional[int],
    role: Optional[str],
    min_proficiency: int,
    min_experience_years: int
) -> List[Employee]:
    """
    Query employees matching all specified filters.
    
    DEPRECATED: Legacy function kept for backward compatibility.
    New code should use search_matching_talent() which implements
    hybrid STRICT/PARTIAL matching.
    
    This function only returns STRICT matches (AND logic).
    """
    normalized_terms = _normalize_skill_terms(skills) if skills else []
    canonical_skill_ids = _resolve_canonical_skill_ids(db, normalized_terms) if normalized_terms else set()
    normalized_role = role.strip().lower() if role else None
    
    if skills and len(skills) > 0 and not canonical_skill_ids:
        return []
    
    if canonical_skill_ids:
        return _query_strict_match(
            db=db,
            canonical_skill_ids=canonical_skill_ids,
            sub_segment_id=sub_segment_id,
            team_id=team_id,
            normalized_role=normalized_role,
            min_proficiency=min_proficiency,
            min_experience_years=min_experience_years
        )
    
    return _query_org_only(
        db=db,
        sub_segment_id=sub_segment_id,
        team_id=team_id,
        normalized_role=normalized_role
    )
