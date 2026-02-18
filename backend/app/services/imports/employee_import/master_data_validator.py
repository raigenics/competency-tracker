"""
Master data validation for employee import.

Single Responsibility: Validate that required master data exists before importing employee rows.
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
import pandas as pd

from app.models import Segment, SubSegment, Project, Team, Role

logger = logging.getLogger(__name__)


@dataclass
class MasterDataValidationResult:
    """Result of master data validation for a single row."""
    is_valid: bool
    sub_segment_id: Optional[int] = None
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    role_id: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class MasterDataValidator:
    """
    Validates that required master data exists before importing employee rows.
    
    Validates:
    - Sub-Segment exists
    - Project exists AND belongs to the Sub-Segment
    - Team exists AND belongs to the Project
    - Role exists (if provided) - matches role_name OR any alias token
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Cache for performance (lookup by normalized name)
        self._sub_segment_cache: Dict[str, Optional[SubSegment]] = {}
        self._project_cache: Dict[Tuple[str, int], Optional[Project]] = {}  # (project_name, sub_segment_id)
        self._team_cache: Dict[Tuple[str, int], Optional[Team]] = {}  # (team_name, project_id)
        # Role lookup: normalized_token -> Role (preloaded for performance)
        self._role_lookup: Dict[str, Role] = {}
        self._roles_loaded = False
    
    @staticmethod
    def _normalize_string(value) -> str:
        """
        Normalize a string value: trim whitespace, collapse multiple spaces.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized string, or empty string if None/NaN
        """
        if value is None or pd.isna(value):
            return ""
        return " ".join(str(value).strip().split())
    
    def validate_row(
        self, 
        sub_segment_name: str, 
        project_name: str, 
        team_name: str, 
        role_name: Optional[str] = None,
        zid: str = "",
        row_number: int = 0
    ) -> MasterDataValidationResult:
        """
        Validate that all required master data exists for an employee row.
        
        Args:
            sub_segment_name: Sub-Segment name from Excel
            project_name: Project name from Excel
            team_name: Team name from Excel
            role_name: Role/Designation name from Excel (optional)
            zid: Employee ZID for error message
            row_number: Excel row number for error message
            
        Returns:
            MasterDataValidationResult with validation status and IDs if valid
        """
        # Normalize input strings
        sub_segment_name = self._normalize_string(sub_segment_name)
        project_name = self._normalize_string(project_name)
        team_name = self._normalize_string(team_name)
        role_name = self._normalize_string(role_name) if role_name else None
        
        # Validate Sub-Segment exists
        sub_segment = self._get_sub_segment(sub_segment_name)
        if not sub_segment:
            return MasterDataValidationResult(
                is_valid=False,
                error_code="MISSING_SUB_SEGMENT",
                error_message=f"Sub-Segment '{sub_segment_name}' not found in master data"
            )
        
        # Validate Project exists AND belongs to Sub-Segment
        project = self._get_project(project_name, sub_segment.sub_segment_id)
        if not project:
            return MasterDataValidationResult(
                is_valid=False,
                error_code="MISSING_PROJECT",
                error_message=f"Project '{project_name}' not found under Sub-Segment '{sub_segment_name}'"
            )
        
        # Validate Team exists AND belongs to Project
        team = self._get_team(team_name, project.project_id)
        if not team:
            return MasterDataValidationResult(
                is_valid=False,
                error_code="MISSING_TEAM",
                error_message=f"Team '{team_name}' not found under Project '{project_name}'"
            )
        
        # Validate Role exists (if provided)
        role_id = None
        if role_name:
            role = self._get_role(role_name)
            if not role:
                return MasterDataValidationResult(
                    is_valid=False,
                    error_code="MISSING_ROLE",
                    error_message=f"Role/Designation '{role_name}' not found in master data"
                )
            role_id = role.role_id
        
        # All validations passed
        return MasterDataValidationResult(
            is_valid=True,
            sub_segment_id=sub_segment.sub_segment_id,
            project_id=project.project_id,
            team_id=team.team_id,
            role_id=role_id
        )
    
    def _get_sub_segment(self, name: str) -> Optional[SubSegment]:
        """Get SubSegment by name with caching."""
        if name in self._sub_segment_cache:
            return self._sub_segment_cache[name]
        
        sub_segment = self.db.query(SubSegment).filter(
            SubSegment.sub_segment_name == name
        ).first()
        
        self._sub_segment_cache[name] = sub_segment
        return sub_segment
    
    def _get_project(self, name: str, sub_segment_id: int) -> Optional[Project]:
        """Get Project by name AND sub_segment_id with caching."""
        cache_key = (name, sub_segment_id)
        if cache_key in self._project_cache:
            return self._project_cache[cache_key]
        
        project = self.db.query(Project).filter(
            Project.project_name == name,
            Project.sub_segment_id == sub_segment_id
        ).first()
        
        self._project_cache[cache_key] = project
        return project
    
    def _get_team(self, name: str, project_id: int) -> Optional[Team]:
        """Get Team by name AND project_id with caching."""
        cache_key = (name, project_id)
        if cache_key in self._team_cache:
            return self._team_cache[cache_key]
        
        team = self.db.query(Team).filter(
            Team.team_name == name,
            Team.project_id == project_id
        ).first()
        
        self._team_cache[cache_key] = team
        return team
    
    def _load_roles(self) -> None:
        """
        Preload all active roles and build normalized lookup dict.
        
        Maps normalized tokens (role_name + alias tokens) to Role objects.
        This allows O(1) lookup for role resolution during import.
        """
        if self._roles_loaded:
            return
        
        # Fetch all active roles (soft-delete filter)
        roles = self.db.query(Role).filter(Role.deleted_at.is_(None)).all()
        
        for role in roles:
            # Add role_name (normalized, case-insensitive key)
            role_name_key = self._normalize_string(role.role_name).lower()
            if role_name_key:
                self._role_lookup[role_name_key] = role
            
            # Add alias tokens (comma-separated)
            if role.role_alias:
                for alias_token in role.role_alias.split(','):
                    alias_key = self._normalize_string(alias_token).lower()
                    if alias_key:
                        # First match wins (don't overwrite existing)
                        if alias_key not in self._role_lookup:
                            self._role_lookup[alias_key] = role
        
        self._roles_loaded = True
    
    def _get_role(self, name: str) -> Optional[Role]:
        """
        Get Role by name or alias with preloaded lookup.
        
        Matches against:
        1. role_name (case-insensitive)
        2. Any alias token in role_alias (comma-separated, case-insensitive)
        
        Only active roles (deleted_at IS NULL) are considered.
        """
        # Ensure roles are loaded
        self._load_roles()
        
        # Normalize and lookup
        normalized_key = self._normalize_string(name).lower()
        return self._role_lookup.get(normalized_key)
    
    def clear_cache(self):
        """Clear all caches."""
        self._sub_segment_cache.clear()
        self._project_cache.clear()
        self._team_cache.clear()
        self._role_lookup.clear()
        self._roles_loaded = False
