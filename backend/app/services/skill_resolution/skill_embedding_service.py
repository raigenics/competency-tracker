"""
Skill Embedding Service - manages persistence of skill embeddings.

Ensures embeddings are created/updated when skills are added/modified.
Single Responsibility: Orchestrate embedding generation and persistence.
"""
import logging
import hashlib
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from dataclasses import dataclass, field

from app.models.skill import Skill
from app.services.skill_resolution.embedding_provider import EmbeddingProvider
from app.services.skill_resolution.skill_embedding_repository import SkillEmbeddingRepository

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation operation."""
    succeeded: List[int] = field(default_factory=list)  # skill_ids that succeeded
    failed: List[Dict[str, Any]] = field(default_factory=list)  # {skill_id, skill_name, error}
    skipped: List[int] = field(default_factory=list)  # skill_ids that were up-to-date


class SkillEmbeddingService:
    """Service for managing skill embeddings."""
    
    def __init__(
        self,
        db: Session,
        embedding_provider: EmbeddingProvider,
        embedding_repository: SkillEmbeddingRepository = None,
        model_name: str = "text-embedding-3-small",
        embedding_version: str = "v1"
    ):
        """
        Initialize skill embedding service.
        
        Args:
            db: Database session
            embedding_provider: Provider for generating embeddings
            embedding_repository: Repository for DB operations (auto-created if None)
            model_name: Model name to use for embeddings
            embedding_version: Version string for embeddings
        """
        self.db = db
        self.embedding_provider = embedding_provider
        self.embedding_repository = embedding_repository or SkillEmbeddingRepository(db)
        self.model_name = model_name
        self.embedding_version = embedding_version
    
    def ensure_embeddings_for_skill_ids(
        self,
        skill_ids: List[int]
    ) -> EmbeddingResult:
        """
        Ensure embeddings exist for given skill IDs (batch operation).
        
        Only generates embeddings for skills that need them:
        - No existing embedding
        - Embedding version/model mismatch
        - Skill name changed (detected via hash comparison)
        
        Args:
            skill_ids: List of skill IDs to process
            
        Returns:
            EmbeddingResult with succeeded, failed, and skipped skill IDs
        """
        result = EmbeddingResult()
        
        if not skill_ids:
            logger.debug("No skill IDs provided for embedding generation")
            return result
        
        logger.info(f"Ensuring embeddings for {len(skill_ids)} skills")
        
        # Fetch all skills in one query
        skills = self.db.query(Skill).filter(Skill.skill_id.in_(skill_ids)).all()
        skill_map = {skill.skill_id: skill for skill in skills}
        
        # Process each skill
        for skill_id in skill_ids:
            skill = skill_map.get(skill_id)
            if not skill:
                logger.warning(f"Skill ID {skill_id} not found in database")
                continue
            
            try:
                # Check if embedding needed
                if self._is_embedding_up_to_date(skill):
                    logger.debug(f"Embedding skipped (up-to-date): skill_id={skill_id}, skill_name='{skill.skill_name}'")
                    result.skipped.append(skill_id)
                    continue
                
                # Generate and save embedding
                success = self._generate_and_save_embedding(skill)
                if success:
                    logger.info(f"Embedding upserted: skill_id={skill_id}, skill_name='{skill.skill_name}', model={self.model_name}, version={self.embedding_version}")
                    result.succeeded.append(skill_id)
                else:
                    # Should not happen as exceptions are caught below
                    result.failed.append({
                        'skill_id': skill_id,
                        'skill_name': skill.skill_name,
                        'error': 'Unknown error'
                    })
                    
            except Exception as e:
                # Log warning but continue processing
                logger.warning(
                    f"Embedding failed: skill_id={skill_id}, skill_name='{skill.skill_name}', "
                    f"error={type(e).__name__}: {str(e)}"
                )
                result.failed.append({
                    'skill_id': skill_id,
                    'skill_name': skill.skill_name,
                    'error': f"{type(e).__name__}: {str(e)}"
                })
        
        logger.info(
            f"Embedding batch complete: succeeded={len(result.succeeded)}, "
            f"skipped={len(result.skipped)}, failed={len(result.failed)}"
        )
        
        return result
    
    def ensure_embedding_for_skill(self, skill: Skill) -> bool:
        """
        Ensure embedding exists for a single skill.
        
        Args:
            skill: Skill object (must have skill_id and skill_name)
            
        Returns:
            True if successful, False if failed
        """
        try:
            # Check if embedding needed
            if self._is_embedding_up_to_date(skill):
                logger.debug(f"Embedding skipped (up-to-date): skill_id={skill.skill_id}, skill_name='{skill.skill_name}'")
                return True
            
            # Generate and save embedding
            success = self._generate_and_save_embedding(skill)
            if success:
                logger.info(f"Embedding upserted: skill_id={skill.skill_id}, skill_name='{skill.skill_name}', model={self.model_name}, version={self.embedding_version}")
            return success
            
        except Exception as e:
            logger.warning(
                f"Embedding failed: skill_id={skill.skill_id}, skill_name='{skill.skill_name}', "
                f"error={type(e).__name__}: {str(e)}"
            )
            return False
    
    def _is_embedding_up_to_date(self, skill: Skill) -> bool:
        """
        Check if embedding is up-to-date for a skill.
        
        Returns True if:
        - Embedding exists
        - Model name matches
        - Version matches
        - Skill name hash matches (skill not changed)
        """
        try:
            existing = self.embedding_repository.get_by_skill_and_model(
                skill.skill_id,
                self.model_name
            )
            
            if not existing:
                return False
            
            # Check version
            if existing.embedding_version != self.embedding_version:
                return False
            
            # Check if skill name changed (using hash comparison)
            # We use a simple hash of normalized skill name to detect changes
            normalized_name = self._normalize_text(skill.skill_name)
            current_hash = self._compute_text_hash(normalized_name)
            
            # Store hash in embedding_version as "v1:hash" format for tracking
            # This allows us to detect if skill_name changed
            version_with_hash = f"{self.embedding_version}:{current_hash}"
            
            # If version doesn't include hash, assume it might be outdated
            if ':' not in existing.embedding_version:
                return False
            
            # Compare hashes
            if existing.embedding_version != version_with_hash:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking embedding status for skill_id={skill.skill_id}: {e}")
            # If we can't check, assume it needs update to be safe
            return False
    
    def _generate_and_save_embedding(self, skill: Skill) -> bool:
        """
        Generate embedding for skill and save to database.
        
        Args:
            skill: Skill object
            
        Returns:
            True if successful
            
        Raises:
            Exception if embedding generation or save fails
        """
        # Generate enhanced embedding text (includes aliases, category, subcategory)
        embedding_text = self._generate_enhanced_embedding_text(skill)
        
        # Normalize for consistency
        normalized_text = self._normalize_text(embedding_text)
        
        # Generate embedding using enhanced text
        embedding_vector = self.embedding_provider.embed(normalized_text)
        
        # Compute hash for change detection (use skill name only for backwards compatibility)
        text_hash = self._compute_text_hash(self._normalize_text(skill.skill_name))
        version_with_hash = f"{self.embedding_version}:{text_hash}"
        
        # Upsert to database
        self.embedding_repository.upsert(
            skill_id=skill.skill_id,
            model_name=self.model_name,
            embedding=embedding_vector,
            embedding_version=version_with_hash,
            updated_at=datetime.utcnow()
        )
        
        return True
    
    def _generate_enhanced_embedding_text(self, skill: Skill) -> str:
        """
        Generate enhanced embedding text for a skill.
        
        Format: "skill_name | aliases: alias1, alias2 | category: cat_name | subcategory: subcat_name"
        
        This provides richer context for embedding generation, improving match quality.
        
        Args:
            skill: Skill object with relationships loaded
            
        Returns:
            Enhanced text string for embedding
        """
        parts = [skill.skill_name]
        
        # Add aliases if available
        try:
            if hasattr(skill, 'aliases') and skill.aliases:
                alias_texts = [alias.alias_text for alias in skill.aliases if alias.alias_text]
                if alias_texts:
                    parts.append(f"aliases: {', '.join(alias_texts)}")
        except Exception as e:
            logger.debug(f"Could not load aliases for skill_id={skill.skill_id}: {e}")
        
        # Add category and subcategory if available
        try:
            if hasattr(skill, 'subcategory') and skill.subcategory:
                subcategory = skill.subcategory
                parts.append(f"subcategory: {subcategory.subcategory_name}")
                
                if hasattr(subcategory, 'category') and subcategory.category:
                    category = subcategory.category
                    parts.append(f"category: {category.category_name}")
        except Exception as e:
            logger.debug(f"Could not load category/subcategory for skill_id={skill.skill_id}: {e}")
        
        # Join parts with separator
        enhanced_text = " | ".join(parts)
        return enhanced_text
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text for consistent embedding generation.
        
        Same normalization used in skill matching.
        """
        return text.strip().lower()
    
    @staticmethod
    def _compute_text_hash(text: str) -> str:
        """
        Compute hash of text for change detection.
        
        Uses MD5 for speed (not security-critical).
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
