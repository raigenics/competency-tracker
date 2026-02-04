"""
Data upsert operations for master import.

Single Responsibility: Insert or update data entities.
"""
import logging
from typing import Tuple
from sqlalchemy.orm import Session

from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from .excel_parser import MasterSkillRow
from .data_cache import DataCache
from app.schemas.master_import import ImportError

logger = logging.getLogger(__name__)


class DataUpserter:
    """Handles upsert operations for categories, subcategories, skills, and aliases."""
    
    def __init__(self, db: Session, cache: DataCache):
        self.db = db
        self.cache = cache
        self.errors = []
        
        # Track stats
        self.stats = {
            'categories': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'subcategories': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'skills': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'aliases': {'inserted': 0, 'existing': 0, 'conflicts': 0},
        }
    
    def upsert_category(self, category_name: str, category_norm: str) -> int:
        """
        Insert or get existing category.
        Returns category_id.
        """
        if category_norm in self.cache.categories:
            self.stats['categories']['existing'] += 1
            return self.cache.categories[category_norm]
        
        # Insert new category
        new_category = SkillCategory(category_name=category_name)
        self.db.add(new_category)
        self.db.flush()
        
        self.cache.categories[category_norm] = new_category.category_id
        self.stats['categories']['inserted'] += 1
        return new_category.category_id
    
    def upsert_subcategory(self, subcategory_name: str, subcategory_norm: str, 
                          category_id: int, category_norm: str) -> int:
        """
        Insert or get existing subcategory.
        Returns subcategory_id.
        """
        key = (category_norm, subcategory_norm)
        
        if key in self.cache.subcategories:
            self.stats['subcategories']['existing'] += 1
            return self.cache.subcategories[key]
        
        # Insert new subcategory
        new_subcat = SkillSubcategory(
            subcategory_name=subcategory_name,
            category_id=category_id
        )
        self.db.add(new_subcat)
        self.db.flush()
        
        self.cache.subcategories[key] = new_subcat.subcategory_id
        self.stats['subcategories']['inserted'] += 1
        return new_subcat.subcategory_id
    
    def upsert_skill(self, row: MasterSkillRow, subcategory_id: int) -> Tuple[bool, int]:
        """
        Insert or validate existing skill.
        Returns (success, skill_id).
        
        CONFLICT: If skill exists under different subcategory.
        """
        if row.skill_name_norm in self.cache.skills:
            existing = self.cache.skills[row.skill_name_norm]
            
            # Check for subcategory conflict
            if existing['subcategory_id'] != subcategory_id:
                self.errors.append(ImportError(
                    row_number=row.row_number,
                    category=row.category,
                    subcategory=row.subcategory,
                    skill_name=row.skill_name,
                    error_type="SKILL_SUBCATEGORY_CONFLICT",
                    message=f"Skill already exists under different subcategory",
                    existing={
                        'skill_id': existing['skill_id'],
                        'skill_name': existing['skill_name'],
                        'subcategory_id': existing['subcategory_id']
                    },
                    attempted={
                        'skill_name': row.skill_name,
                        'subcategory_id': subcategory_id
                    }
                ))
                self.stats['skills']['conflicts'] += 1
                return (False, existing['skill_id'])
            
            self.stats['skills']['existing'] += 1
            return (True, existing['skill_id'])
        
        # Insert new skill
        new_skill = Skill(
            skill_name=row.skill_name,
            subcategory_id=subcategory_id
        )
        self.db.add(new_skill)
        self.db.flush()
        
        self.cache.skills[row.skill_name_norm] = {
            'skill_id': new_skill.skill_id,
            'skill_name': new_skill.skill_name,
            'subcategory_id': new_skill.subcategory_id
        }
        self.stats['skills']['inserted'] += 1
        return (True, new_skill.skill_id)
    
    def upsert_aliases(self, row: MasterSkillRow, skill_id: int) -> bool:
        """
        Insert or validate aliases for a skill.
        Returns True if all aliases processed successfully.
        
        CONFLICT: If alias exists for different skill.
        """
        all_success = True
        
        for alias, alias_norm in zip(row.aliases, row.aliases_norm):
            if alias_norm in self.cache.aliases:
                existing = self.cache.aliases[alias_norm]
                
                # Check if alias points to different skill
                if existing['skill_id'] != skill_id:
                    self.errors.append(ImportError(
                        row_number=row.row_number,
                        category=row.category,
                        subcategory=row.subcategory,
                        skill_name=row.skill_name,
                        alias=alias,
                        error_type="ALIAS_CONFLICT",
                        message=f"Alias '{alias}' already exists for different skill",
                        existing={
                            'alias_id': existing['alias_id'],
                            'alias_text': existing['alias_text'],
                            'skill_id': existing['skill_id']
                        },
                        attempted={
                            'alias_text': alias,
                            'skill_id': skill_id
                        }
                    ))
                    self.stats['aliases']['conflicts'] += 1
                    all_success = False
                    continue
                
                # Same skill - OK
                self.stats['aliases']['existing'] += 1
                continue
            
            # Insert new alias
            new_alias = SkillAlias(
                alias_text=alias,
                skill_id=skill_id,
                source='master_import',  # Required field
                confidence_score=1.0  # Master import = high confidence
            )
            self.db.add(new_alias)
            self.db.flush()
            
            self.cache.aliases[alias_norm] = {
                'alias_id': new_alias.alias_id,
                'alias_text': new_alias.alias_text,
                'skill_id': new_alias.skill_id
            }
            self.stats['aliases']['inserted'] += 1
        
        return all_success
