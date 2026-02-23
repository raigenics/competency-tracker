"""
Skill Proficiency Breakdown Service - GET /skills/{skill_id}/proficiency-breakdown

Handles proficiency distribution, average, and median calculations for a specific skill.
Zero dependencies on other services.

Returns:
    - counts: Dict of proficiency level names to employee counts
    - avg: Average proficiency value (1-5) rounded to 1 decimal
    - median: Median proficiency value (1-5)
    - total: Total employees with proficiency data
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import EmployeeSkill, ProficiencyLevel
from app.schemas.skill import SkillProficiencyBreakdownResponse

logger = logging.getLogger(__name__)

# Canonical proficiency level names (matches UI requirements)
PROFICIENCY_LEVELS = ["Novice", "Adv. Beginner", "Competent", "Proficient", "Expert"]

# Mapping from DB level names to canonical names (handles variations)
LEVEL_NAME_MAPPING = {
    "Beginner": "Novice",
    "Novice": "Novice",
    "Advanced Beginner": "Adv. Beginner",
    "Adv Beginner": "Adv. Beginner",
    "Adv. Beginner": "Adv. Beginner",
    "Competent": "Competent",
    "Proficient": "Proficient",
    "Expert": "Expert"
}


def get_skill_proficiency_breakdown(db: Session, skill_id: int) -> SkillProficiencyBreakdownResponse:
    """
    Get proficiency breakdown for a specific skill.
    
    Args:
        db: Database session
        skill_id: The skill ID to fetch proficiency data for
    
    Returns:
        SkillProficiencyBreakdownResponse with counts, avg, median, total
    """
    logger.info(f"Fetching proficiency breakdown for skill_id: {skill_id}")
    
    # Query proficiency data
    raw_counts = _query_proficiency_counts(db, skill_id)
    proficiency_ids = _query_proficiency_ids(db, skill_id)
    
    # Normalize counts to canonical level names
    counts = _normalize_counts(raw_counts)
    
    # Calculate statistics
    total = sum(counts.values())
    avg = _calculate_average(proficiency_ids) if proficiency_ids else None
    median = _calculate_median(proficiency_ids) if proficiency_ids else None
    
    # Build response
    response = SkillProficiencyBreakdownResponse(
        counts=counts,
        avg=avg,
        median=median,
        total=total
    )
    
    logger.info(f"Proficiency breakdown for skill {skill_id}: "
                f"total={total}, avg={avg}, median={median}")
    return response


# === DATABASE QUERIES (Repository layer) ===

def _query_proficiency_counts(db: Session, skill_id: int) -> Dict[str, int]:
    """
    Query proficiency level distribution for a skill.
    Returns dict of {level_name: count}.
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        Dict mapping level names to counts
    """
    results = db.query(
        ProficiencyLevel.level_name,
        func.count(EmployeeSkill.emp_skill_id)
    ).join(
        EmployeeSkill, EmployeeSkill.proficiency_level_id == ProficiencyLevel.proficiency_level_id
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None)
    ).group_by(
        ProficiencyLevel.level_name
    ).all()
    
    return dict(results)


def _query_proficiency_ids(db: Session, skill_id: int) -> List[int]:
    """
    Query all proficiency_level_ids for a skill (for avg/median calculation).
    
    Args:
        db: Database session
        skill_id: The skill ID
    
    Returns:
        List of proficiency_level_id values (1-5)
    """
    results = db.query(
        EmployeeSkill.proficiency_level_id
    ).filter(
        EmployeeSkill.skill_id == skill_id,
        EmployeeSkill.deleted_at.is_(None),
        EmployeeSkill.proficiency_level_id.isnot(None)
    ).all()
    
    return [r[0] for r in results]


# === BUSINESS LOGIC (Pure functions) ===

def _normalize_counts(raw_counts: Dict[str, int]) -> Dict[str, int]:
    """
    Normalize raw DB level names to canonical level names.
    Ensures all 5 levels are present in output.
    
    Args:
        raw_counts: Dict from DB query {db_level_name: count}
    
    Returns:
        Dict with canonical level names {canonical_name: count}
    """
    # Initialize all levels to 0
    normalized = {level: 0 for level in PROFICIENCY_LEVELS}
    
    # Map raw counts to canonical names
    for db_name, count in raw_counts.items():
        canonical_name = LEVEL_NAME_MAPPING.get(db_name, db_name)
        if canonical_name in normalized:
            normalized[canonical_name] = count
    
    return normalized


def _calculate_average(proficiency_ids: List[int]) -> Optional[float]:
    """
    Calculate average proficiency level.
    
    Args:
        proficiency_ids: List of proficiency_level_id values (1-5)
    
    Returns:
        Average rounded to 1 decimal place, or None if empty
    """
    if not proficiency_ids:
        return None
    
    avg = sum(proficiency_ids) / len(proficiency_ids)
    return round(avg, 1)


def _calculate_median(proficiency_ids: List[int]) -> Optional[int]:
    """
    Calculate median proficiency level.
    Handles both odd and even counts correctly.
    
    Args:
        proficiency_ids: List of proficiency_level_id values (1-5)
    
    Returns:
        Median value (integer 1-5), or None if empty
    """
    if not proficiency_ids:
        return None
    
    sorted_ids = sorted(proficiency_ids)
    n = len(sorted_ids)
    
    if n % 2 == 1:
        # Odd count: return middle element
        return sorted_ids[n // 2]
    else:
        # Even count: average of two middle elements, rounded
        mid1 = sorted_ids[n // 2 - 1]
        mid2 = sorted_ids[n // 2]
        return round((mid1 + mid2) / 2)
