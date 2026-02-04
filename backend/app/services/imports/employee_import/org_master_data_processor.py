"""
Organizational master data processing for employee import.

Single Responsibility: Process SubSegment, Project, Team, and Role master data.
"""
import logging
from typing import Set, Dict, Tuple
from sqlalchemy.orm import Session
import pandas as pd

from app.models import SubSegment, Project, Team, Role

logger = logging.getLogger(__name__)


class OrgMasterDataProcessor:
    """Processes organizational master data from Employee sheet."""
    
    def __init__(self, db: Session, stats: Dict):
        self.db = db
        self.stats = stats
    
    def process_all(self, master_data: Dict[str, Set]):
        """
        Process all org master data (SubSegment/Project/Team/Role only).

        NOTE: Does NOT process skill categories/subcategories/skills.
        Those are resolved from existing DB master data during skill import.
        
        CRITICAL: Must commit org master data BEFORE employee import starts.
        """
        logger.info("Processing org master data (SubSegment/Project/Team/Role only)...")
        
        # Log summary
        self._log_master_data_summary(master_data)
        
        # Step 1: Process top-level org entities
        self._process_sub_segments(master_data['sub_segments'])
        self._process_roles(master_data['roles'])
        self.db.flush()  # Ensure parent entities exist

        # Step 2: Process second-level org entities with parent validation
        self._process_projects_with_validation(master_data['projects'], master_data['sub_segment_project_mappings'])
        self.db.flush()  # Ensure projects exist
        
        # Step 3: Process third-level org entities with hierarchical validation
        self._process_teams_with_validation(master_data['teams'], master_data['project_team_mappings'])
        self.db.flush()  # Ensure all org master data is flushed to session
        
        # CRITICAL FIX: Commit org master data NOW before employee import
        self.db.commit()
        logger.info("Committed org master data (SubSegment/Project/Team/Role)")
        logger.info("Org master data processing completed (skills will be resolved from DB)")
    
    def _log_master_data_summary(self, master_data: Dict[str, Set]):
        """Log summary of master data to process."""
        logger.info(f"Master data summary:")
        logger.info(f"  Sub-segments: {len(master_data.get('sub_segments', set()))}")
        logger.info(f"  Projects: {len(master_data.get('sub_segment_project_mappings', set()))}")
        logger.info(f"  Teams: {len(master_data.get('project_team_mappings', set()))}")
        logger.info(f"  Roles: {len(master_data.get('roles', set()))}")
        
        if master_data.get('project_team_mappings'):
            logger.debug(f"Team mappings to create: {sorted(master_data['project_team_mappings'])}")
    
    def _process_sub_segments(self, sub_segments: Set[str]):
        """Process Sub-Segment master data."""
        for sub_segment_name in sub_segments:
            if not sub_segment_name or pd.isna(sub_segment_name):
                continue

            existing = self.db.query(SubSegment).filter(
                SubSegment.sub_segment_name == sub_segment_name
            ).first()
            
            if not existing:
                new_sub_segment = SubSegment(sub_segment_name=sub_segment_name)
                self.db.add(new_sub_segment)
                self.stats['new_sub_segments'].append(sub_segment_name)
                logger.info(f"Added new sub-segment: {sub_segment_name}")

    def _process_roles(self, roles: Set[str]):
        """Process Role master data."""
        for role_name in roles:
            if not role_name or pd.isna(role_name):
                continue

            existing = self.db.query(Role).filter(
                Role.role_name == role_name
            ).first()

            if not existing:
                new_role = Role(role_name=role_name)
                self.db.add(new_role)
                self.stats['new_roles'].append(role_name)
                logger.info(f"Added new role: {role_name}")

    def _process_projects_with_validation(self, projects: Set[str], mappings: Set[Tuple[str, str]]):
        """Process Projects with Sub-Segment validation."""
        logger.info("Processing projects with sub-segment validation...")

        for sub_segment_name, project_name in mappings:
            sub_segment = self.db.query(SubSegment).filter(
                SubSegment.sub_segment_name == sub_segment_name
            ).first()

            if not sub_segment:
                from app.services.import_service import ImportServiceError
                raise ImportServiceError(f"Sub-Segment '{sub_segment_name}' not found for project '{project_name}'")

            existing_project = self.db.query(Project).filter(
                Project.project_name == project_name,
                Project.sub_segment_id == sub_segment.sub_segment_id
            ).first()

            if not existing_project:
                new_project = Project(
                    project_name=project_name,
                    sub_segment_id=sub_segment.sub_segment_id
                )
                self.db.add(new_project)
                self.stats['new_projects'].append(project_name)
                logger.info(f"Added new project: {project_name} under sub-segment: {sub_segment_name}")

    def _process_teams_with_validation(self, teams: Set[str], mappings: Set[Tuple[str, str]]):
        """Process Teams with Project validation."""
        logger.info("Processing teams with project validation...")

        for project_name, team_name in mappings:
            project = self.db.query(Project).filter(
                Project.project_name == project_name
            ).first()

            if not project:
                from app.services.import_service import ImportServiceError
                raise ImportServiceError(f"Project '{project_name}' not found for team '{team_name}'")

            existing_team = self.db.query(Team).filter(
                Team.team_name == team_name,
                Team.project_id == project.project_id
            ).first()

            if not existing_team:
                new_team = Team(
                    team_name=team_name,
                    project_id=project.project_id
                )
                self.db.add(new_team)
                self.stats['new_teams'].append(team_name)
                logger.info(f"Added new team: {team_name} under project: {project_name}")
