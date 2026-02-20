"""
Skill resolution logic for employee import.

Single Responsibility: Resolve skill names to skill IDs using DB master data.

Resolution Strategy:
    1. Token validation (reject garbage tokens like ")", "4", "6")
    2. Exact match on skills.skill_name (case-insensitive)
    3. Alias match on skill_aliases.alias_text (case-insensitive)
    4. Embedding match (with confidence thresholds):
       - Auto-accept: similarity ≥ 0.88
       - Review: 0.80 ≤ similarity < 0.88 (logged for manual review)
       - Reject: similarity < 0.80 (unresolved)
"""
import logging
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator
from app.utils.normalization import normalize_skill_name

logger = logging.getLogger(__name__)


class SkillResolver:
    """Resolves skill names to skill IDs using database master data."""
    
    # Embedding similarity thresholds
    EMBEDDING_AUTO_ACCEPT_THRESHOLD = 0.88  # ≥ 0.88: Auto-accept
    EMBEDDING_REVIEW_THRESHOLD = 0.80       # ≥ 0.80, < 0.88: Needs review
    # < 0.80: Rejected (unresolved)
    
    def __init__(self, db: Session, stats: Dict):
        self.db = db
        self.stats = stats
        self.normalize_name = None  # Will be injected
        self.token_validator = SkillTokenValidator()
        
        # Normalized lookup cache for bilateral plural matching
        # Built lazily on first use
        self._skill_lookup: Optional[Dict[str, int]] = None
        self._alias_lookup: Optional[Dict[str, int]] = None
        
        # Initialize embedding provider (optional - graceful degradation)
        self.embedding_provider = None
        self.embedding_enabled = False
        try:
            from app.services.skill_resolution.embedding_provider import create_embedding_provider
            self.embedding_provider = create_embedding_provider()
            self.embedding_enabled = True
            logger.info("Skill resolution: Embedding-based matching enabled")
        except Exception as e:
            logger.warning(f"Skill resolution: Embedding matching disabled: {type(e).__name__}: {str(e)}")
    
    def _build_lookup_cache(self):
        """
        Build normalized lookup cache for skills and aliases.
        
        Uses normalize_skill_name() for bilateral plural handling:
        - "RESTful APIs" in input matches "RESTful API" in DB
        - "RESTful API" in input matches "RESTful APIs" in DB
        
        Cache is built once per resolver instance.
        """
        if self._skill_lookup is not None:
            return  # Already built
        
        self._skill_lookup = {}
        self._alias_lookup = {}
        
        # Build skill lookup: normalized_name -> skill_id
        for skill in self.db.query(Skill).all():
            normalized = normalize_skill_name(skill.skill_name)
            if normalized and normalized not in self._skill_lookup:
                self._skill_lookup[normalized] = skill.skill_id
        
        # Build alias lookup: normalized_alias -> skill_id
        for alias in self.db.query(SkillAlias).all():
            normalized = normalize_skill_name(alias.alias_text)
            if normalized and normalized not in self._alias_lookup:
                self._alias_lookup[normalized] = alias.skill_id
        
        logger.debug(f"Built skill lookup cache: {len(self._skill_lookup)} skills, {len(self._alias_lookup)} aliases")
    
    def set_name_normalizer(self, normalizer_func):
        """Inject name normalization function."""
        self.normalize_name = normalizer_func    
    def resolve_skill(self, skill_name: str) -> Tuple[Optional[int], Optional[str], Optional[float]]:
        """
        Resolve skill name to skill_id using DB master data.
        
        Resolution strategy:
            1. Token validation (reject garbage like ")", "4", "6")
            2. Exact match on skills.skill_name (case-insensitive)
            3. Alias match on skill_aliases.alias_text (case-insensitive)
            4. Embedding match with thresholds:
               - ≥ 0.88: Auto-accept (set resolved_skill_id)
               - 0.80-0.88: Review needed (NO resolved_skill_id, mark for review)
               - < 0.80: Unresolved
        
        Args:
            skill_name: Raw skill name from Excel
            
        Returns:
            Tuple of (skill_id, resolution_method, confidence):
            - skill_id: Resolved skill ID (None if unresolved or needs review)
            - resolution_method: 'exact', 'alias', 'embedding', 'needs_review', or None
            - confidence: Similarity score (0.0-1.0) for embedding matches, None otherwise
            
        Examples:
            ("Python", "exact", None) - exact match
            (42, "alias", None) - alias match
            (99, "embedding", 0.92) - high-confidence embedding match (auto-accepted)
            (None, "needs_review", 0.85) - embedding match needs review (not auto-accepted)
            (None, None, None) - unresolved
        """
        # Step 1: Token validation
        cleaned_token = self.token_validator.clean_and_validate(skill_name)
        if cleaned_token is None:
            logger.debug(f"Token rejected: '{skill_name}' (invalid token)")
            self.stats['skills_unresolved'] += 1
            if skill_name not in self.stats['unresolved_skill_names']:
                self.stats['unresolved_skill_names'].append(skill_name)
            return None, None, None
        
        # Build lookup cache on first use (enables bilateral plural matching)
        self._build_lookup_cache()
        
        # Normalize input with plural handling (e.g., "APIs" -> "api")
        skill_name_normalized = normalize_skill_name(cleaned_token)
        
        # Step 2: Exact match on skills.skill_name (via normalized lookup)
        if skill_name_normalized in self._skill_lookup:
            skill_id = self._skill_lookup[skill_name_normalized]
            logger.debug(f"✓ Resolved '{skill_name}' via exact match → skill_id={skill_id}")
            self.stats['skills_resolved_exact'] += 1
            return skill_id, "exact", None
        
        # Step 3: Alias match on skill_aliases.alias_text (via normalized lookup)
        if skill_name_normalized in self._alias_lookup:
            skill_id = self._alias_lookup[skill_name_normalized]
            logger.debug(f"✓ Resolved '{skill_name}' via alias match → skill_id={skill_id}")
            self.stats['skills_resolved_alias'] += 1
            return skill_id, "alias", None
        
        # Step 4: Embedding match (if enabled)
        if self.embedding_enabled and self.embedding_provider:
            skill_id, confidence = self._try_embedding_match(skill_name_normalized)
            
            if skill_id and confidence:
                if confidence >= self.EMBEDDING_AUTO_ACCEPT_THRESHOLD:
                    # Auto-accept high-confidence matches
                    logger.debug(f"✓ Resolved '{skill_name}' via embedding (auto-accept) → skill_id={skill_id}, confidence={confidence:.4f}")
                    self.stats.setdefault('skills_resolved_embedding', 0)
                    self.stats['skills_resolved_embedding'] += 1
                    return skill_id, "embedding", confidence
                elif confidence >= self.EMBEDDING_REVIEW_THRESHOLD:
                    # Medium-confidence: needs manual review
                    logger.debug(f"⚠ '{skill_name}' embedding match needs review → skill_id={skill_id}, confidence={confidence:.4f}")
                    self.stats.setdefault('skills_needs_review', 0)
                    self.stats['skills_needs_review'] += 1
                    # Return None for skill_id (not auto-accepted), but include method and confidence
                    return None, "needs_review", confidence
                # else: confidence < 0.80, fall through to unresolved
        
        # Step 5: Unresolved
        logger.warning(f"✗ Could not resolve skill: '{skill_name}'")
        self.stats['skills_unresolved'] += 1
        if skill_name not in self.stats['unresolved_skill_names']:
            self.stats['unresolved_skill_names'].append(skill_name)
        return None, None, None
    
    def _try_embedding_match(self, skill_name_normalized: str) -> Tuple[Optional[int], Optional[float]]:
        """
        Try to match skill using embedding similarity.
        
        Args:
            skill_name_normalized: Normalized skill name
            
        Returns:
            Tuple of (skill_id, confidence) or (None, None) if no match
        """
        try:
            from app.services.skill_resolution.skill_embedding_repository import SkillEmbeddingRepository
            
            # Generate embedding for input skill
            input_embedding = self.embedding_provider.embed(skill_name_normalized)
            
            # Find best match using cosine similarity
            embedding_repo = SkillEmbeddingRepository(self.db)
            best_match = embedding_repo.find_most_similar(
                embedding=input_embedding,
                model_name="text-embedding-3-small",
                limit=1,
                min_similarity=self.EMBEDDING_REVIEW_THRESHOLD  # Only consider ≥ 0.80
            )
            
            if best_match:
                skill_id, similarity = best_match[0]
                return skill_id, similarity
            
            return None, None
            
        except Exception as e:
            logger.debug(f"Embedding match failed for '{skill_name_normalized}': {type(e).__name__}: {str(e)}")
            return None, None
