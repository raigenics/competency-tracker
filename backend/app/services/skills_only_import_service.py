"""
Skills-only import service for resolving skills via normalization and aliases.
Handles Excel files with pre-seeded master data (no Category/SubCategory columns).
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timezone
from dataclasses import dataclass
from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.raw_skill_input import RawSkillInput
from app.models.employee_skill import EmployeeSkill
from app.models.employee import Employee
from app.models.proficiency import ProficiencyLevel
from app.models.sub_segment import SubSegment
from app.utils.normalization import normalize_skill_text

logger = logging.getLogger(__name__)


@dataclass
class SkillOccurrence:
    """Represents a single skill occurrence in the import file."""
    employee_id: int
    raw_text: str
    normalized_text: str
    sub_segment_id: Optional[int]
    proficiency: Optional[str] = None
    years_experience: Optional[float] = None
    last_used_year: Optional[int] = None
    interest_level: Optional[str] = None


@dataclass
class ResolutionResult:
    """Result of skill resolution."""
    normalized_text: str
    resolved_skill_id: Optional[int]
    resolution_method: str  # EXACT, ALIAS, UNRESOLVED
    resolution_confidence: Optional[float]
    skill_name: Optional[str] = None  # For reporting


class SkillsOnlyImportService:
    """
    Service for importing skills-only Excel files with intelligent resolution.
    
    Resolution Strategy:
    1. EXACT match against normalized canonical skills
    2. ALIAS match against skill_aliases table
    3. Mark as UNRESOLVED if no match found
    
    Does NOT create new canonical skills.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.stats = {
            'employees_processed': 0,
            'skills_total': 0,
            'resolved_exact': 0,
            'resolved_alias': 0,
            'unresolved': 0,
            'raw_skill_inputs_inserted': 0,
            'employee_skills_upserted': 0
        }
        self.errors: List[Dict[str, Any]] = []
        
        # Cache for performance
        self.canonical_skills_map: Dict[str, Tuple[int, str]] = {}  # norm_text -> (skill_id, skill_name)
        self.alias_map: Dict[str, Tuple[int, str]] = {}  # norm_alias -> (skill_id, skill_name)
        self.proficiency_map: Dict[str, int] = {}  # normalized level_name -> proficiency_level_id
        self.default_proficiency_id: Optional[int] = None
        
    def import_skills_only(
        self, 
        employees_df: pd.DataFrame, 
        skills_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Import skills from Excel file using pre-seeded master data."""
        logger.info("Starting skills-only import with resolution")
        
        try:
            # Load canonical skills and aliases into cache
            self._load_canonical_skills()
            self._load_skill_aliases()
            self._load_proficiency_levels()
            
            # Parse skill occurrences from Excel
            skill_occurrences = self._parse_skill_occurrences(employees_df, skills_df)
            self.stats['skills_total'] = len(skill_occurrences)
            
            # Batch insert into raw_skill_inputs
            raw_skill_id_map = self._batch_insert_raw_skills(skill_occurrences)
            
            # Resolve skills in batch
            resolution_results = self._batch_resolve_skills(skill_occurrences)
            
            # Update raw_skill_inputs with resolution results
            self._update_raw_skills_with_resolution(raw_skill_id_map, resolution_results)
            
            # Insert/upsert into employee_skills for resolved skills
            self._upsert_employee_skills(skill_occurrences, resolution_results)
            
            # Generate unresolved grouped report
            unresolved_grouped = self._group_unresolved_skills(skill_occurrences, resolution_results)
            
            # Commit transaction
            self.db.commit()
            logger.info("Skills-only import completed successfully")
            
            # Determine status
            if self.stats['unresolved'] == 0 and len(self.errors) == 0:
                status = 'success'
            elif self.stats['resolved_exact'] + self.stats['resolved_alias'] > 0:
                status = 'partial_success'
            else:
                status = 'failed'
            
            return {
                'status': status,
                'summary': {
                    'employees_processed': self.stats['employees_processed'],
                    'skills_total': self.stats['skills_total'],
                    'resolved_exact': self.stats['resolved_exact'],
                    'resolved_alias': self.stats['resolved_alias'],
                    'unresolved': self.stats['unresolved']
                },
                'unresolved_grouped': unresolved_grouped,
                'errors': self.errors
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Skills-only import failed: {str(e)}", exc_info=True)
            raise
    
    def _load_canonical_skills(self):
        """Load all canonical skills into memory for fast matching."""
        logger.info("Loading canonical skills into cache")
        
        skills = self.db.query(Skill).all()
        
        for skill in skills:
            norm_text = normalize_skill_text(skill.skill_name)
            self.canonical_skills_map[norm_text] = (skill.skill_id, skill.skill_name)
        
        logger.info(f"Loaded {len(self.canonical_skills_map)} canonical skills")
    
    def _load_skill_aliases(self):
        """Load all skill aliases into memory for fast matching."""
        logger.info("Loading skill aliases into cache")
        
        aliases = self.db.query(SkillAlias).all()
        
        for alias in aliases:
            norm_alias = normalize_skill_text(alias.alias_text)
            
            # Get the canonical skill name for this alias
            skill = self.db.query(Skill).filter(Skill.skill_id == alias.skill_id).first()
            skill_name = skill.skill_name if skill else "Unknown"
            
            self.alias_map[norm_alias] = (alias.skill_id, skill_name)
        
        logger.info(f"Loaded {len(self.alias_map)} skill aliases")
    
    def _load_proficiency_levels(self):
        """Load proficiency levels into memory for mapping text to IDs."""
        logger.info("Loading proficiency levels into cache")
        
        proficiencies = self.db.query(ProficiencyLevel).order_by(ProficiencyLevel.proficiency_level_id).all()
        
        if not proficiencies:
            logger.warning("No proficiency levels found in database")
            return
        
        # Map normalized level names to IDs
        for prof in proficiencies:
            norm_name = prof.level_name.strip().lower()
            self.proficiency_map[norm_name] = prof.proficiency_level_id
        
        # Set default to first proficiency level
        self.default_proficiency_id = proficiencies[0].proficiency_level_id
        
        logger.info(f"Loaded {len(self.proficiency_map)} proficiency levels, default ID: {self.default_proficiency_id}")
    
    def _map_proficiency_text_to_id(self, proficiency_text: Optional[str]) -> int:
        """Map proficiency text to proficiency_level_id."""
        if not proficiency_text or not proficiency_text.strip():
            return self.default_proficiency_id or 1
        
        norm_text = proficiency_text.strip().lower()
        
        # Direct match
        if norm_text in self.proficiency_map:
            return self.proficiency_map[norm_text]
        
        # Partial match (e.g., "expert" matches "Expert Level")
        for key, prof_id in self.proficiency_map.items():
            if norm_text in key or key in norm_text:
                return prof_id
        
        # Default fallback
        logger.warning(f"Proficiency text '{proficiency_text}' not mapped, using default")
        return self.default_proficiency_id or 1
    
    def _parse_skill_occurrences(
        self, 
        employees_df: pd.DataFrame, 
        skills_df: pd.DataFrame
    ) -> List[SkillOccurrence]:
        """Parse skill occurrences from Excel data."""
        logger.info("Parsing skill occurrences from Excel")
        
        skill_occurrences = []
        employee_zids = set()
        
        # Build employee lookup: ZID -> (employee_id, sub_segment_id)
        employee_lookup = {}
        for _, emp_row in employees_df.iterrows():
            zid = str(emp_row['zid']).strip()
            
            # Use data from Excel file directly (employees may not be in DB yet)
            employee_id = emp_row.get('employee_id')
            sub_segment_id = emp_row.get('sub_segment_id')
            
            if zid and employee_id:
                employee_lookup[zid] = (employee_id, sub_segment_id)
                logger.debug(f"Added employee {zid} to lookup: employee_id={employee_id}, sub_segment_id={sub_segment_id}")
        
        logger.info(f"Built employee lookup for {len(employee_lookup)} employees")
        
        # Parse skills
        for idx, skill_row in skills_df.iterrows():
            try:
                zid = str(skill_row['zid']).strip()
                # Support both 'skill' and 'skill_name' columns
                raw_text = str(skill_row.get('skill', skill_row.get('skill_name', ''))).strip()
                
                # Skip empty skills
                if not raw_text or raw_text.lower() in ['nan', 'none', '']:
                    continue
                
                # Check if employee exists
                if zid not in employee_lookup:
                    self.errors.append({
                        'type': 'VALIDATION_ERROR',
                        'message': f'Employee ZID {zid} not found in employee data',
                        'context': {'row': idx + 2, 'zid': zid}
                    })
                    continue
                
                employee_id, sub_segment_id = employee_lookup[zid]
                employee_zids.add(zid)
                
                # Normalize skill text
                normalized_text = normalize_skill_text(raw_text)
                
                # Parse optional fields
                proficiency = self._parse_optional_str(skill_row.get('proficiency'))
                years_exp = self._parse_optional_float(skill_row.get('years_experience'))
                last_used = self._parse_optional_int(skill_row.get('last_used'))
                interest = self._parse_optional_str(skill_row.get('interest_level'))
                
                skill_occurrences.append(SkillOccurrence(
                    employee_id=employee_id,
                    raw_text=raw_text,
                    normalized_text=normalized_text,
                    sub_segment_id=sub_segment_id,
                    proficiency=proficiency,
                    years_experience=years_exp,
                    last_used_year=last_used,
                    interest_level=interest
                ))
                
            except Exception as e:
                self.errors.append({
                    'type': 'PARSING_ERROR',
                    'message': f'Error parsing skill row: {str(e)}',
                    'context': {'row': idx + 2}
                })
                logger.error(f"Error parsing skill row {idx + 2}: {e}")
        
        self.stats['employees_processed'] = len(employee_zids)
        logger.info(f"Parsed {len(skill_occurrences)} skill occurrences from {len(employee_zids)} employees")
        
        return skill_occurrences
    
    def _parse_optional_str(self, value: Any) -> Optional[str]:
        """Parse optional string field."""
        if pd.isna(value) or value is None or str(value).strip().lower() in ['nan', 'none', '']:
            return None
        return str(value).strip()
    
    def _parse_optional_float(self, value: Any) -> Optional[float]:
        """Parse optional float field."""
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_optional_int(self, value: Any) -> Optional[int]:
        """Parse optional integer field."""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(value))  # Handle "2024.0" strings
        except (ValueError, TypeError):
            return None
    
    def _batch_insert_raw_skills(
        self,
        skill_occurrences: List[SkillOccurrence]
    ) -> Dict[str, int]:
        """Batch insert into raw_skill_inputs table."""
        logger.info(f"Batch inserting {len(skill_occurrences)} raw skill inputs")
        
        raw_skill_id_map = {}
        
        for occ in skill_occurrences:
            raw_skill = RawSkillInput(
                raw_text=occ.raw_text,
                normalized_text=occ.normalized_text,
                sub_segment_id=occ.sub_segment_id,
                source_type='excel_skills_only',
                employee_id=occ.employee_id
            )
            self.db.add(raw_skill)
            self.db.flush()  # Get the ID
            
            # Map normalized text to raw_skill_input_id
            key = f"{occ.employee_id}_{occ.normalized_text}"
            raw_skill_id_map[key] = raw_skill.raw_skill_id
        
        self.stats['raw_skill_inputs_inserted'] = len(skill_occurrences)
        logger.info(f"Inserted {len(skill_occurrences)} raw skill inputs")
        
        return raw_skill_id_map
    
    def _batch_resolve_skills(
        self,
        skill_occurrences: List[SkillOccurrence]
    ) -> Dict[str, ResolutionResult]:
        """Batch resolve skills using EXACT and ALIAS matching."""
        logger.info("Batch resolving skills")
        
        resolution_results = {}
        unique_normalized_texts = set(occ.normalized_text for occ in skill_occurrences)
        
        for norm_text in unique_normalized_texts:
            # Try EXACT match first
            if norm_text in self.canonical_skills_map:
                skill_id, skill_name = self.canonical_skills_map[norm_text]
                resolution_results[norm_text] = ResolutionResult(
                    normalized_text=norm_text,
                    resolved_skill_id=skill_id,
                    resolution_method='EXACT',
                    resolution_confidence=1.00,
                    skill_name=skill_name
                )
                self.stats['resolved_exact'] += 1
                continue
            
            # Try ALIAS match
            if norm_text in self.alias_map:
                skill_id, skill_name = self.alias_map[norm_text]
                resolution_results[norm_text] = ResolutionResult(
                    normalized_text=norm_text,
                    resolved_skill_id=skill_id,
                    resolution_method='ALIAS',
                    resolution_confidence=0.98,
                    skill_name=skill_name
                )
                self.stats['resolved_alias'] += 1
                continue
            
            # Mark as UNRESOLVED
            resolution_results[norm_text] = ResolutionResult(
                normalized_text=norm_text,
                resolved_skill_id=None,
                resolution_method='UNRESOLVED',
                resolution_confidence=None,
                skill_name=None
            )
            self.stats['unresolved'] += 1
        
        logger.info(f"Resolution complete: {self.stats['resolved_exact']} EXACT, "
                   f"{self.stats['resolved_alias']} ALIAS, {self.stats['unresolved']} UNRESOLVED")
        
        return resolution_results
    
    def _update_raw_skills_with_resolution(
        self,
        raw_skill_id_map: Dict[str, int],
        resolution_results: Dict[str, ResolutionResult]
    ) -> None:
        """Update raw_skill_inputs with resolution results."""
        logger.info("Updating raw_skill_inputs with resolution results")
        
        for norm_text, result in resolution_results.items():
            raw_skills = self.db.query(RawSkillInput).filter(
                RawSkillInput.normalized_text == norm_text
            ).all()
            
            for raw_skill in raw_skills:
                raw_skill.resolved_skill_id = result.resolved_skill_id
                raw_skill.resolution_method = result.resolution_method
                raw_skill.resolution_confidence = result.resolution_confidence
                
                # Log unresolved skills to file
                if result.resolution_method == 'UNRESOLVED':
                    self._log_unresolved_skill_to_file(
                        raw_skill.raw_text,
                        raw_skill.employee_id,
                        raw_skill.sub_segment_id,
                        raw_skill.created_at
                    )
        
        logger.info("Raw skill inputs updated with resolution results")

    def _log_unresolved_skill_to_file(self, skill_name: str, employee_id: int,
                                       sub_segment_id: Optional[int], timestamp: datetime):
        """
        Log unresolved skill to a text file in backend folder for easy review.
        
        Args:
            skill_name: Unresolved skill name from Excel
            employee_id: Employee who has this skill
            sub_segment_id: Employee's sub-segment (for context)
            timestamp: Import timestamp
        """
        try:
            # Get backend folder path (parent of app folder)
            backend_folder = Path(__file__).parent.parent.parent
            log_file = backend_folder / "unresolved_skills.txt"
            
            # Get employee info for better context
            employee = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
            employee_name = f"{employee.first_name} {employee.last_name}" if employee else f"ID:{employee_id}"
            employee_zid = employee.zid if employee else "Unknown"
            
            # Get sub-segment info
            sub_segment_name = "N/A"
            if sub_segment_id:
                sub_segment = self.db.query(SubSegment).filter(SubSegment.sub_segment_id == sub_segment_id).first()
                sub_segment_name = sub_segment.name if sub_segment else f"ID:{sub_segment_id}"
            
            # Format log entry
            log_entry = (
                f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"UNRESOLVED: \"{skill_name}\" | "
                f"Employee: {employee_name} ({employee_zid}) | "
                f"Sub-Segment: {sub_segment_name}\n"
            )
            
            # Append to file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            logger.debug(f"Logged unresolved skill to {log_file}")
            
        except Exception as e:
            # Don't fail the import if file logging fails
            logger.warning(f"Failed to log unresolved skill to file: {e}")
    
    def _upsert_employee_skills(
        self,
        skill_occurrences: List[SkillOccurrence],
        resolution_results: Dict[str, ResolutionResult]
    ) -> None:
        """Upsert into employee_skills table (only for resolved skills)."""
        logger.info("Upserting employee skills")
        
        upserted_count = 0
        
        for occ in skill_occurrences:
            result = resolution_results.get(occ.normalized_text)
            
            # Skip unresolved skills
            if not result or not result.resolved_skill_id:
                continue
            
            # Check if employee_skill already exists
            existing = self.db.query(EmployeeSkill).filter(
                and_(
                    EmployeeSkill.employee_id == occ.employee_id,
                    EmployeeSkill.skill_id == result.resolved_skill_id                )
            ).first()
            
            if existing:
                # Update existing record
                if occ.proficiency:
                    existing.proficiency_level_id = self._map_proficiency_text_to_id(occ.proficiency)
                existing.years_experience = occ.years_experience
                if occ.last_used_year:
                    existing.last_used = datetime(occ.last_used_year, 1, 1).date()
            else:
                # Insert new record with proficiency mapping
                proficiency_id = self._map_proficiency_text_to_id(occ.proficiency)
                
                emp_skill = EmployeeSkill(
                    employee_id=occ.employee_id,
                    skill_id=result.resolved_skill_id,
                    proficiency_level_id=proficiency_id,
                    years_experience=occ.years_experience,
                    last_used=datetime(occ.last_used_year, 1, 1).date() if occ.last_used_year else None
                )
                self.db.add(emp_skill)
            
            upserted_count += 1
        
        self.stats['employee_skills_upserted'] = upserted_count
        logger.info(f"Upserted {upserted_count} employee skills")
    
    def _group_unresolved_skills(
        self,
        skill_occurrences: List[SkillOccurrence],
        resolution_results: Dict[str, ResolutionResult]
    ) -> List[Dict[str, Any]]:
        """Group unresolved skills by sub_segment_id for reporting."""
        logger.info("Grouping unresolved skills by sub-segment")
        
        grouped = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'employees': set(), 'raw_texts': set()}))
        
        for occ in skill_occurrences:
            result = resolution_results.get(occ.normalized_text)
            
            # Only include unresolved skills
            if result and result.resolution_method == 'UNRESOLVED':
                sub_seg_id = occ.sub_segment_id or 0
                norm_text = occ.normalized_text
                
                grouped[sub_seg_id][norm_text]['count'] += 1
                grouped[sub_seg_id][norm_text]['raw_texts'].add(occ.raw_text)
                
                # Add employee info
                emp = self.db.query(Employee).filter(Employee.employee_id == occ.employee_id).first()
                if emp:
                    grouped[sub_seg_id][norm_text]['employees'].add(emp.zid)
        
        # Convert to list format
        result = []
        for sub_seg_id in sorted(grouped.keys()):
            items = []
            for norm_text in sorted(grouped[sub_seg_id].keys()):
                data = grouped[sub_seg_id][norm_text]
                sample_employees = sorted(list(data['employees']))[:5]
                
                items.append({
                    'normalized_text': norm_text,
                    'raw_text': ', '.join(sorted(data['raw_texts'])),
                    'count': data['count'],
                    'sample_employees': sample_employees
                })
            
            result.append({
                'sub_segment_id': sub_seg_id,
                'items': items
            })
        
        logger.info(f"Grouped unresolved skills into {len(result)} sub-segments")
        
        return result
