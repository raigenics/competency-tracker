"""
Skill resolution logic for employee import.

Single Responsibility: Resolve skill names to skill IDs using DB master data.
"""
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias

logger = logging.getLogger(__name__)


class SkillResolver:
    """Resolves skill names to skill IDs using database master data."""
    
    def __init__(self, db: Session, stats: Dict):
        self.db = db
        self.stats = stats
        self.normalize_name = None  # Will be injected
    
    def set_name_normalizer(self, normalizer_func):
        """Inject name normalization function."""
        self.normalize_name = normalizer_func
    
    def resolve_skill(self, skill_name: str) -> Optional[int]:
        """
        Resolve skill name to skill_id using DB master data.
        
        Resolution strategy:
            1. Exact match on skills.skill_name (case-insensitive)
            2. Alias match on skill_aliases.alias_text (case-insensitive)
            3. Return None (unresolved)
        
        Args:
            skill_name: Raw skill name from Excel
            
        Returns:
            skill_id if resolved, None otherwise
        """
        skill_name_normalized = self.normalize_name(skill_name) if self.normalize_name else skill_name.lower().strip()
        
        # Step 1: Exact match on skills.skill_name
        skill = self.db.query(Skill).filter(
            func.lower(func.trim(Skill.skill_name)) == skill_name_normalized
        ).first()
        
        if skill:
            logger.debug(f"✓ Resolved '{skill_name}' via exact match → skill_id={skill.skill_id}")
            self.stats['skills_resolved_exact'] += 1
            return skill.skill_id
        
        # Step 2: Alias match on skill_aliases.alias_text
        alias = self.db.query(SkillAlias).filter(
            func.lower(func.trim(SkillAlias.alias_text)) == skill_name_normalized
        ).first()
        
        if alias:
            logger.debug(f"✓ Resolved '{skill_name}' via alias match → skill_id={alias.skill_id}")
            self.stats['skills_resolved_alias'] += 1
            return alias.skill_id
        
        # Step 3: Unresolved
        logger.warning(f"✗ Could not resolve skill: '{skill_name}'")
        self.stats['skills_unresolved'] += 1
        if skill_name not in self.stats['unresolved_skill_names']:
            self.stats['unresolved_skill_names'].append(skill_name)
        return None
