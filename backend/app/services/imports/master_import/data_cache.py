"""
Data cache for master import conflict detection.

Single Responsibility: Load and maintain in-memory cache of existing data.
"""
import logging
from typing import Dict, Set, Tuple
from sqlalchemy.orm import Session

from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.utils.normalization import normalize_key

logger = logging.getLogger(__name__)


class DataCache:
    """Cache for existing data to enable fast conflict detection."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Caches for conflict detection
        self.categories: Dict[str, int] = {}  # norm_name -> category_id
        self.subcategories: Dict[Tuple[str, str], int] = {}  # (category_norm, subcat_norm) -> subcat_id
        self.skills: Dict[str, Dict] = {}  # skill_norm -> {skill_id, subcategory_id, ...}
        self.aliases: Dict[str, Dict] = {}  # alias_norm -> {alias_id, skill_id, ...}
    
    def load_all(self):
        """Load all existing data into memory caches."""
        self._load_categories()
        self._load_subcategories()
        self._load_skills()
        self._load_aliases()
        
        logger.info(
            f"Loaded caches: {len(self.categories)} categories, "
            f"{len(self.subcategories)} subcategories, "
            f"{len(self.skills)} skills, "
            f"{len(self.aliases)} aliases"
        )
    
    def _load_categories(self):
        """Load categories into cache."""
        categories = self.db.query(SkillCategory).all()
        for cat in categories:
            self.categories[normalize_key(cat.category_name)] = cat.category_id
    
    def _load_subcategories(self):
        """Load subcategories into cache."""
        subcategories = self.db.query(SkillSubcategory).all()
        for subcat in subcategories:
            cat_name = self.db.query(SkillCategory.category_name)\
                .filter(SkillCategory.category_id == subcat.category_id)\
                .scalar()
            key = (normalize_key(cat_name), normalize_key(subcat.subcategory_name))
            self.subcategories[key] = subcat.subcategory_id
    
    def _load_skills(self):
        """Load skills into cache."""
        skills = self.db.query(Skill).all()
        for skill in skills:
            skill_norm = normalize_key(skill.skill_name)
            self.skills[skill_norm] = {
                'skill_id': skill.skill_id,
                'skill_name': skill.skill_name,
                'subcategory_id': skill.subcategory_id
            }
    
    def _load_aliases(self):
        """Load aliases into cache."""
        aliases = self.db.query(SkillAlias).all()
        for alias in aliases:
            alias_norm = normalize_key(alias.alias_text)
            self.aliases[alias_norm] = {
                'alias_id': alias.alias_id,
                'alias_text': alias.alias_text,
                'skill_id': alias.skill_id
            }
