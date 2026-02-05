"""
Skill resolver service - 3-layer skill resolution.

Resolves raw skill text to skill IDs using:
1. Exact match
2. Alias match  
3. Embedding-based semantic similarity
"""
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.services.skill_resolution.embedding_provider import EmbeddingProvider
from app.services.skill_resolution.skill_embedding_repository import SkillEmbeddingRepository

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    """Result of skill resolution."""
    resolved_skill_id: Optional[int]
    resolution_method: str  # "exact", "alias", "embedding", "review", "unresolved"
    resolution_confidence: Optional[float]
    
    def is_resolved(self) -> bool:
        """Check if skill was successfully resolved."""
        return self.resolved_skill_id is not None


class SkillResolverService:
    """
    Service for resolving raw skill text to skill IDs.
    
    Implements 3-layer resolution strategy:
    1. Exact match on skills.skill_name (case-insensitive)
    2. Alias match on skill_aliases.alias_text (case-insensitive)
    3. Embedding match using semantic similarity
       - similarity >= 0.88: auto-accept
       - 0.80 <= similarity < 0.88: mark for review
       - similarity < 0.80: unresolved
    """
    
    # Similarity thresholds
    THRESHOLD_AUTO_ACCEPT = 0.88
    THRESHOLD_REVIEW = 0.80
    
    def __init__(
        self,
        db: Session,
        embedding_provider: Optional[EmbeddingProvider] = None,
        enable_embedding: bool = True
    ):
        """
        Initialize skill resolver service.
        
        Args:
            db: SQLAlchemy database session
            embedding_provider: Optional embedding provider (if None, embedding layer is disabled)
            enable_embedding: Whether to enable embedding-based resolution
        """
        self.db = db
        self.embedding_provider = embedding_provider
        self.enable_embedding = enable_embedding and embedding_provider is not None
        self.embedding_repo = SkillEmbeddingRepository(db) if self.enable_embedding else None
        
        if not self.enable_embedding:
            logger.info("Skill resolver initialized WITHOUT embedding support (exact + alias only)")
        else:
            logger.info("Skill resolver initialized WITH embedding support (3-layer resolution)")
    
    def resolve(self, normalized_text: str) -> ResolutionResult:
        """
        Resolve normalized skill text to skill ID.
        
        Args:
            normalized_text: Normalized skill text (lowercased, trimmed)
            
        Returns:
            ResolutionResult with resolved skill ID and metadata
        """
        # Layer 1: Exact match
        result = self._try_exact_match(normalized_text)
        if result.is_resolved():
            return result
        
        # Layer 2: Alias match
        result = self._try_alias_match(normalized_text)
        if result.is_resolved():
            return result
        
        # Layer 3: Embedding match (if enabled)
        if self.enable_embedding:
            try:
                result = self._try_embedding_match(normalized_text)
                if result.resolved_skill_id is not None or result.resolution_method == "review":
                    return result
            except Exception as e:
                # Log error but don't fail the import
                logger.error(f"Embedding match failed for '{normalized_text}': {e}")
                # Fall through to unresolved
        
        # No match found
        return ResolutionResult(
            resolved_skill_id=None,
            resolution_method="unresolved",
            resolution_confidence=None
        )
    
    def _try_exact_match(self, normalized_text: str) -> ResolutionResult:
        """Try exact match on skills.skill_name."""
        skill = self.db.query(Skill).filter(
            func.lower(func.trim(Skill.skill_name)) == normalized_text
        ).first()
        
        if skill:
            logger.debug(f"✓ Resolved '{normalized_text}' via EXACT match → skill_id={skill.skill_id}")
            return ResolutionResult(
                resolved_skill_id=skill.skill_id,
                resolution_method="exact",
                resolution_confidence=1.0
            )
        
        return ResolutionResult(
            resolved_skill_id=None,
            resolution_method="unresolved",
            resolution_confidence=None
        )
    
    def _try_alias_match(self, normalized_text: str) -> ResolutionResult:
        """Try alias match on skill_aliases.alias_text."""
        alias = self.db.query(SkillAlias).filter(
            func.lower(func.trim(SkillAlias.alias_text)) == normalized_text
        ).first()
        
        if alias:
            logger.debug(f"✓ Resolved '{normalized_text}' via ALIAS match → skill_id={alias.skill_id}")
            return ResolutionResult(
                resolved_skill_id=alias.skill_id,
                resolution_method="alias",
                resolution_confidence=1.0
            )
        
        return ResolutionResult(
            resolved_skill_id=None,
            resolution_method="unresolved",
            resolution_confidence=None
        )
    
    def _try_embedding_match(self, normalized_text: str) -> ResolutionResult:
        """
        Try embedding-based semantic similarity match.
        
        Args:
            normalized_text: Normalized skill text
            
        Returns:
            ResolutionResult with embedding match or review status
        """
        # Generate embedding for input text
        query_embedding = self.embedding_provider.embed(normalized_text)
        
        # Find top-5 most similar skills
        matches = self.embedding_repo.find_top_k(query_embedding, k=5)
        
        if not matches:
            logger.debug(f"✗ No embedding matches found for '{normalized_text}'")
            return ResolutionResult(
                resolved_skill_id=None,
                resolution_method="unresolved",
                resolution_confidence=None
            )
        
        # Get best match
        best_skill_id, best_similarity = matches[0]
        
        # Apply thresholds
        if best_similarity >= self.THRESHOLD_AUTO_ACCEPT:
            # Auto-accept: high confidence match
            logger.info(
                f"✓ Resolved '{normalized_text}' via EMBEDDING match "
                f"→ skill_id={best_skill_id}, similarity={best_similarity:.4f}"
            )
            return ResolutionResult(
                resolved_skill_id=best_skill_id,
                resolution_method="embedding",
                resolution_confidence=best_similarity
            )
        
        elif best_similarity >= self.THRESHOLD_REVIEW:
            # Review: medium confidence - needs manual verification
            logger.info(
                f"⚠ '{normalized_text}' marked for REVIEW "
                f"→ skill_id={best_skill_id}, similarity={best_similarity:.4f}"
            )
            return ResolutionResult(
                resolved_skill_id=None,  # Do NOT auto-resolve
                resolution_method="review",
                resolution_confidence=best_similarity
            )
        
        else:
            # Low confidence: treat as unresolved
            logger.debug(
                f"✗ Low similarity for '{normalized_text}': "
                f"best={best_similarity:.4f} < threshold={self.THRESHOLD_REVIEW}"
            )
            return ResolutionResult(
                resolved_skill_id=None,
                resolution_method="unresolved",
                resolution_confidence=best_similarity
            )
