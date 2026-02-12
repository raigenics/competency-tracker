"""
Organizational master data processing for employee import.

Single Responsibility: Process SubSegment, Project, Team, and Role master data.
"""
import logging
from typing import Set, Dict, Tuple
from sqlalchemy.orm import Session
import pandas as pd

from app.models import Segment, SubSegment, Project, Team, Role

logger = logging.getLogger(__name__)


class OrgMasterDataProcessor:
    """Processes organizational master data from Employee sheet."""
    
    def __init__(self, db: Session, stats: Dict):
        self.db = db
        self.stats = stats
    
    def process_all(self, master_data: Dict[str, Set]):
        """
        Process all org master data (Segment/SubSegment/Project/Team/Role).

        NOTE: Does NOT process skill categories/subcategories/skills.
        Those are resolved from existing DB master data during skill import.
        
        CRITICAL: Must commit org master data BEFORE employee import starts.
        """
        logger.info("Processing org master data (Segment/SubSegment/Project/Team/Role)...")
        
        # Log summary
        self._log_master_data_summary(master_data)
        
        # Step 0: Process segments (top of hierarchy)
        self._process_segments(master_data.get('segments', set()))
        self.db.flush()  # Ensure segments exist
        
        # Step 1: Process sub-segments with segment linkage
        self._process_sub_segments_with_segment_mapping(
            master_data['sub_segments'],
            master_data.get('segment_subsegment_mappings', set())
        )
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
        logger.info("Committed org master data (Segment/SubSegment/Project/Team/Role)")
        logger.info("Org master data processing completed (skills will be resolved from DB)")
    
    def _log_master_data_summary(self, master_data: Dict[str, Set]):
        """Log summary of master data to process."""
        logger.info(f"Master data summary:")
        logger.info(f"  Segments: {len(master_data.get('segments', set()))}")
        logger.info(f"  Sub-segments: {len(master_data.get('sub_segments', set()))}")
        logger.info(f"  Projects: {len(master_data.get('sub_segment_project_mappings', set()))}")
        logger.info(f"  Teams: {len(master_data.get('project_team_mappings', set()))}")
        logger.info(f"  Roles: {len(master_data.get('roles', set()))}")
        
        if master_data.get('project_team_mappings'):
            logger.debug(f"Team mappings to create: {sorted(master_data['project_team_mappings'])}")
    
    def _process_segments(self, segments: Set[str]):
        """Process Segment master data (top-level org units)."""
        
        for segment_name in segments:
            if not segment_name or pd.isna(segment_name):
                continue
            
            # Clean segment name (remove whitespace)
            segment_name_clean = str(segment_name).strip()
            if not segment_name_clean:
                continue

            existing = self.db.query(Segment).filter(
                Segment.segment_name == segment_name_clean
            ).first()
            
            if not existing:
                new_segment = Segment(segment_name=segment_name_clean, created_by="employee_import")
                self.db.add(new_segment)
                self.stats.setdefault('new_segments', []).append(segment_name_clean)
                logger.info(f"Added new segment: {segment_name_clean}")
    
    def _process_sub_segments_with_segment_mapping(
        self, 
        sub_segments: Set[str], 
        segment_subsegment_mappings: Set[Tuple[str, str]]
    ):
        """
        Process Sub-Segment master data with Segment linkage.
        
        If a sub_segment has a segment mapping, link it.
        Otherwise, leave segment_id as NULL.
        """
        # Build segment mapping dict for quick lookup
        subseg_to_segment = {}
        for segment_name, subseg_name in segment_subsegment_mappings:
            subseg_to_segment[subseg_name] = segment_name
        
        for sub_segment_name in sub_segments:
            if not sub_segment_name or pd.isna(sub_segment_name):
                continue

            existing = self.db.query(SubSegment).filter(
                SubSegment.sub_segment_name == sub_segment_name
            ).first()
            
            # Determine which segment to link to (only if explicitly mapped in Excel)
            segment = None
            segment_name = subseg_to_segment.get(sub_segment_name)
            if segment_name:
                # Find the segment
                segment_name_clean = str(segment_name).strip()
                segment = self.db.query(Segment).filter(
                    Segment.segment_name == segment_name_clean
                ).first()
                
                if not segment:
                    logger.warning(
                        f"Segment '{segment_name_clean}' not found for sub-segment '{sub_segment_name}'. "
                        f"Sub-segment will be created without segment link."
                    )
            
            if not existing:
                # Create new sub_segment with segment link (or NULL if no mapping)
                new_sub_segment = SubSegment(
                    sub_segment_name=sub_segment_name,
                    segment_id=segment.segment_id if segment else None,
                    created_by="employee_import"
                )
                self.db.add(new_sub_segment)
                self.stats.setdefault('new_sub_segments', []).append(sub_segment_name)
                if segment:
                    logger.info(
                        f"Added new sub-segment: {sub_segment_name} "
                        f"(linked to segment: {segment.segment_name})"
                    )
                else:
                    logger.info(f"Added new sub-segment: {sub_segment_name} (no segment link)")
            else:
                # Update existing sub_segment to link to segment if mapping exists
                if segment and existing.segment_id is None:
                    existing.segment_id = segment.segment_id
                    logger.info(
                        f"Updated existing sub-segment '{sub_segment_name}' "
                        f"to link to segment: {segment.segment_name}"
                    )
                elif segment and existing.segment_id != segment.segment_id:
                    # Sub-segment already linked to different segment
                    # Keep existing link (don't override)
                    logger.debug(
                        f"Sub-segment '{sub_segment_name}' already linked to segment_id={existing.segment_id}, "
                        f"skipping re-link to {segment.segment_name}"
                    )

    def _process_roles(self, roles: Set[str]):
        """Process Role master data."""
        
        for role_name in roles:
            if not role_name or pd.isna(role_name):
                continue

            existing = self.db.query(Role).filter(
                Role.role_name == role_name
            ).first()
            
            if not existing:
                new_role = Role(role_name=role_name, created_by="employee_import")
                self.db.add(new_role)
                self.stats.setdefault('new_roles', []).append(role_name)
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
                    sub_segment_id=sub_segment.sub_segment_id,
                    created_by="employee_import"
                )
                self.db.add(new_project)
                self.stats.setdefault('new_projects', []).append(project_name)
                logger.info(f"Added new project: {project_name} under sub-segment: {sub_segment_name}")

    def _process_teams_with_validation(self, teams: Set[str], mappings: Set[Tuple[str, str, str]]):
        """
        Process Teams with Project validation.
        
        FIX: mappings now contains (sub_segment, project, team) triples to handle duplicate project names.
        """
        logger.info("Processing teams with project validation...")

        for sub_segment_name, project_name, team_name in mappings:
            # FIX: Lookup sub_segment first to resolve project correctly
            sub_segment = self.db.query(SubSegment).filter(
                SubSegment.sub_segment_name == sub_segment_name
            ).first()
            
            if not sub_segment:
                from app.services.import_service import ImportServiceError
                raise ImportServiceError(f"Sub-Segment '{sub_segment_name}' not found for team '{team_name}'")
            
            # FIX: Lookup project using BOTH project_name AND sub_segment_id
            project = self.db.query(Project).filter(
                Project.project_name == project_name,
                Project.sub_segment_id == sub_segment.sub_segment_id
            ).first()

            if not project:
                from app.services.import_service import ImportServiceError
                raise ImportServiceError(f"Project '{project_name}' not found under sub-segment '{sub_segment_name}' for team '{team_name}'")

            existing_team = self.db.query(Team).filter(
                Team.team_name == team_name,
                Team.project_id == project.project_id
            ).first()

            if not existing_team:
                new_team = Team(
                    team_name=team_name,
                    project_id=project.project_id,
                    created_by="employee_import"
                )
                self.db.add(new_team)
                self.stats.setdefault('new_teams', []).append(team_name)
                logger.info(f"Added new team: {team_name} under project: {project_name} (sub-segment: {sub_segment_name}, project_id: {project.project_id})")
