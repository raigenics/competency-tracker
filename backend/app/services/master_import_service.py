"""
Service for Master Skills Import with conflict detection and upsert operations.
"""
import logging
from typing import List, Dict, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.schemas.master_import import (
    ImportSummary,
    ImportSummaryCount,
    ImportError,
    MasterImportResponse
)
from app.services.master_import_parser import MasterSkillRow
from app.utils.normalization import normalize_key

logger = logging.getLogger(__name__)


class MasterImportService:
    """Service for processing master skills imports with conflict detection."""
    
    def __init__(self, db: Session):
        self.db = db
        self.errors: List[ImportError] = []
        
        # Caches for conflict detection
        self.categories_cache: Dict[str, int] = {}  # norm_name -> category_id
        self.subcategories_cache: Dict[Tuple[str, str], int] = {}  # (category_norm, subcat_norm) -> subcat_id
        self.skills_cache: Dict[str, Dict] = {}  # skill_norm -> {skill_id, subcategory_id, ...}
        self.aliases_cache: Dict[str, Dict] = {}  # alias_norm -> {alias_id, skill_id, ...}
        
        # Track what happened during import
        self.stats = {
            'categories': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'subcategories': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'skills': {'inserted': 0, 'existing': 0, 'conflicts': 0},
            'aliases': {'inserted': 0, 'existing': 0, 'conflicts': 0},
        }
        
    def load_caches(self):
        """Load existing data into memory caches for fast conflict detection."""
        # Load categories
        categories = self.db.query(SkillCategory).all()
        for cat in categories:
            self.categories_cache[normalize_key(cat.category_name)] = cat.category_id
          # Load subcategories
        subcategories = self.db.query(SkillSubcategory).all()
        for subcat in subcategories:
            cat_name = self.db.query(SkillCategory.category_name)\
                .filter(SkillCategory.category_id == subcat.category_id)\
                .scalar()
            key = (normalize_key(cat_name), normalize_key(subcat.subcategory_name))
            self.subcategories_cache[key] = subcat.subcategory_id
        
        # Load skills
        skills = self.db.query(Skill).all()
        for skill in skills:
            skill_norm = normalize_key(skill.skill_name)
            self.skills_cache[skill_norm] = {
                'skill_id': skill.skill_id,
                'skill_name': skill.skill_name,
                'subcategory_id': skill.subcategory_id
            }
        
        # Load aliases
        aliases = self.db.query(SkillAlias).all()
        for alias in aliases:
            alias_norm = normalize_key(alias.alias_text)
            self.aliases_cache[alias_norm] = {
                'alias_id': alias.alias_id,
                'alias_text': alias.alias_text,
                'skill_id': alias.skill_id
            }
    
    def detect_file_duplicates(self, rows: List[MasterSkillRow]) -> Set[int]:
        """
        Detect duplicate skills within the file itself.
        Returns set of row_numbers to skip.
        """
        seen_skills: Dict[str, int] = {}  # skill_norm -> first row_number
        skip_rows: Set[int] = set()
        
        for row in rows:
            if row.skill_name_norm in seen_skills:
                self.errors.append(ImportError(
                    row_number=row.row_number,
                    category=row.category,
                    subcategory=row.subcategory,
                    skill_name=row.skill_name,
                    error_type="DUPLICATE_IN_FILE",
                    message=f"Duplicate skill in file. First occurrence at row {seen_skills[row.skill_name_norm]}"
                ))
                skip_rows.add(row.row_number)
                self.stats['skills']['conflicts'] += 1
            else:
                seen_skills[row.skill_name_norm] = row.row_number
        
        return skip_rows
    
    def upsert_category(self, category_name: str, category_norm: str) -> int:
        """
        Insert or get existing category.
        Returns category_id.
        """
        if category_norm in self.categories_cache:
            self.stats['categories']['existing'] += 1
            return self.categories_cache[category_norm]
        
        # Insert new category
        new_category = SkillCategory(category_name=category_name)
        self.db.add(new_category)
        self.db.flush()
        
        self.categories_cache[category_norm] = new_category.category_id
        self.stats['categories']['inserted'] += 1
        return new_category.category_id
    
    def upsert_subcategory(self, subcategory_name: str, subcategory_norm: str, 
                          category_id: int, category_norm: str) -> int:
        """
        Insert or get existing subcategory.
        Returns subcategory_id.
        """
        key = (category_norm, subcategory_norm)
        
        if key in self.subcategories_cache:
            self.stats['subcategories']['existing'] += 1
            return self.subcategories_cache[key]
          # Insert new subcategory
        new_subcat = SkillSubcategory(
            subcategory_name=subcategory_name,
            category_id=category_id
        )
        self.db.add(new_subcat)
        self.db.flush()
        
        self.subcategories_cache[key] = new_subcat.subcategory_id
        self.stats['subcategories']['inserted'] += 1
        return new_subcat.subcategory_id
    
    def upsert_skill(self, row: MasterSkillRow, subcategory_id: int) -> Tuple[bool, int]:
        """
        Insert or validate existing skill.
        Returns (success, skill_id).
        
        CONFLICT: If skill exists under different subcategory.
        """
        if row.skill_name_norm in self.skills_cache:
            existing = self.skills_cache[row.skill_name_norm]
            
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
        
        self.skills_cache[row.skill_name_norm] = {
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
            if alias_norm in self.aliases_cache:
                existing = self.aliases_cache[alias_norm]
                
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
            
            self.aliases_cache[alias_norm] = {
                'alias_id': new_alias.alias_id,
                'alias_text': new_alias.alias_text,
                'skill_id': new_alias.skill_id
            }
            self.stats['aliases']['inserted'] += 1
        
        return all_success
    
    def process_import(self, rows: List[MasterSkillRow]) -> MasterImportResponse:
        """
        Process master skills import with conflict detection.
        
        Returns:
            MasterImportResponse with status, summary, and errors
        """
        logger.info(f"Starting import processing for {len(rows)} rows")
        
        # Load existing data
        self.load_caches()
        logger.info(
            f"Loaded caches: {len(self.categories_cache)} categories, "
            f"{len(self.subcategories_cache)} subcategories, "
            f"{len(self.skills_cache)} skills, "
            f"{len(self.aliases_cache)} aliases"
        )
        
        # Detect duplicates within the file
        skip_rows = self.detect_file_duplicates(rows)
        if skip_rows:
            logger.warning(f"Detected {len(skip_rows)} duplicate rows in file")
        
        rows_processed = 0
        
        for row in rows:
            # Skip duplicate rows
            if row.row_number in skip_rows:
                continue
            
            try:
                # 1. Upsert Category
                category_id = self.upsert_category(row.category, row.category_norm)
                
                # 2. Upsert SubCategory
                subcategory_id = self.upsert_subcategory(
                    row.subcategory, row.subcategory_norm, 
                    category_id, row.category_norm
                )
                
                # 3. Upsert Skill (with conflict detection)
                skill_success, skill_id = self.upsert_skill(row, subcategory_id)
                  # 4. Upsert Aliases (only if skill was successful)
                if skill_success and row.aliases:
                    self.upsert_aliases(row, skill_id)
                
                rows_processed += 1
                
            except Exception as e:
                # Log unexpected errors with full traceback
                logger.error(
                    f"Unexpected error processing row {row.row_number}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                self.errors.append(ImportError(
                    row_number=row.row_number,
                    category=row.category,
                    subcategory=row.subcategory,
                    skill_name=row.skill_name,
                    error_type="UNEXPECTED_ERROR",
                    message=f"{type(e).__name__}: {str(e)}"
                ))
          # Commit transaction
        self.db.commit()
        logger.info(f"Import committed: {rows_processed} rows processed")
        
        # Build response
        summary = ImportSummary(
            rows_total=len(rows),
            rows_processed=rows_processed,
            categories=ImportSummaryCount(**self.stats['categories']),
            subcategories=ImportSummaryCount(**self.stats['subcategories']),
            skills=ImportSummaryCount(**self.stats['skills']),
            aliases=ImportSummaryCount(**self.stats['aliases'])
        )
        
        # Determine overall status
        total_conflicts = (
            self.stats['skills']['conflicts'] + 
            self.stats['aliases']['conflicts']
        )
        
        if total_conflicts > 0 and rows_processed == 0:
            status = "failed"
        elif total_conflicts > 0:
            status = "partial_success"
        else:
            status = "success"
        
        logger.info(
            f"Import complete: status={status}, errors={len(self.errors)}, "
            f"conflicts={total_conflicts}"
        )
        
        return MasterImportResponse(
            status=status,
            summary=summary,
            errors=self.errors
        )
