"""
Skill embedding repository for vector similarity search.

Provides database access for skill embeddings with pgvector similarity search.
"""
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.skill_embedding import SkillEmbedding

logger = logging.getLogger(__name__)


class SkillEmbeddingRepository:
    """Repository for skill embedding vector similarity search."""
    
    def __init__(self, db: Session):
        """
        Initialize skill embedding repository.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_skill_and_model(
        self,
        skill_id: int,
        model_name: str
    ) -> Optional[SkillEmbedding]:
        """
        Get embedding for a specific skill and model.
        
        Args:
            skill_id: Skill ID
            model_name: Model name
            
        Returns:
            SkillEmbedding if found, None otherwise
        """
        try:
            embedding = self.db.query(SkillEmbedding).filter(
                SkillEmbedding.skill_id == skill_id,
                SkillEmbedding.model_name == model_name
            ).first()
            return embedding
        except Exception as e:
            logger.error(f"Failed to get embedding for skill_id={skill_id}, model={model_name}: {e}")
            raise
    
    def upsert(
        self,
        skill_id: int,
        model_name: str,
        embedding: List[float],
        embedding_version: str,
        updated_at: datetime = None
    ) -> SkillEmbedding:
        """
        Insert or update skill embedding.
        
        Args:
            skill_id: Skill ID
            model_name: Model name
            embedding: Embedding vector
            embedding_version: Version string
            updated_at: Update timestamp (defaults to now)
            
        Returns:
            Created or updated SkillEmbedding
        """
        try:
            if updated_at is None:
                updated_at = datetime.utcnow()
            
            # Check if exists
            existing = self.get_by_skill_and_model(skill_id, model_name)
            
            if existing:
                # Update existing
                existing.embedding = embedding
                existing.embedding_version = embedding_version
                existing.updated_at = updated_at
                self.db.flush()
                logger.debug(
                    f"Embedding updated: skill_id={skill_id}, model={model_name}, "
                    f"version={embedding_version}"
                )
                return existing
            else:
                # Insert new
                new_embedding = SkillEmbedding(
                    skill_id=skill_id,
                    model_name=model_name,
                    embedding=embedding,
                    embedding_version=embedding_version,
                    updated_at=updated_at
                )
                self.db.add(new_embedding)
                self.db.flush()
                logger.debug(
                    f"Embedding inserted: skill_id={skill_id}, model={model_name}, "
                    f"version={embedding_version}"
                )
                return new_embedding
                
        except Exception as e:
            logger.error(
                f"Failed to upsert embedding for skill_id={skill_id}, model={model_name}: {e}"
            )
            raise
    
    def find_top_k(
        self,
        query_vector: List[float],
        k: int = 5,
        model_name: str = None
    ) -> List[Tuple[int, float]]:
        """
        Find top K most similar skills using cosine similarity.
        
        Args:
            query_vector: Query embedding vector
            k: Number of top matches to return
            model_name: Optional filter by model name
            
        Returns:
            List of tuples (skill_id, similarity_score) ordered by similarity (highest first)
            Similarity score is cosine similarity in range [0, 1] where 1 is most similar
            
        Note:
            pgvector's <=> operator returns cosine distance (0 = identical, 2 = opposite)
            We convert to similarity: similarity = 1 - (distance / 2)
        """
        try:
            # Build query using pgvector cosine distance operator
            # <=> is cosine distance operator (0 = identical, 2 = opposite)
            query_str = """
                SELECT 
                    skill_id,
                    1 - (embedding <=> :query_vector::vector) / 2 AS similarity
                FROM skill_embeddings
            """
            
            params = {"query_vector": str(query_vector)}
            
            # Add model filter if specified
            if model_name:
                query_str += " WHERE model_name = :model_name"
                params["model_name"] = model_name
            
            # Order by similarity (highest first) and limit
            query_str += " ORDER BY embedding <=> :query_vector::vector LIMIT :k"
            params["k"] = k
            
            result = self.db.execute(text(query_str), params)
            matches = [(row[0], float(row[1])) for row in result]
            
            logger.debug(f"Found {len(matches)} embedding matches (top-{k})")
            if matches:
                logger.debug(f"Top match: skill_id={matches[0][0]}, similarity={matches[0][1]:.4f}")
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {e}")
            raise
    
    def get_embedding_count(self) -> int:
        """
        Get total count of skill embeddings in database.
        
        Returns:
            Total number of skill embeddings
        """
        try:
            count = self.db.query(SkillEmbedding).count()
            return count
        except Exception as e:
            logger.error(f"Failed to get embedding count: {e}")
            raise
    
    def has_embedding(self, skill_id: int) -> bool:
        """
        Check if a skill has an embedding.
        
        Args:
            skill_id: Skill ID to check
            
        Returns:
            True if skill has embedding, False otherwise
        """
        try:
            exists = self.db.query(SkillEmbedding).filter(
                SkillEmbedding.skill_id == skill_id
            ).first() is not None
            return exists
        except Exception as e:
            logger.error(f"Failed to check embedding existence for skill_id={skill_id}: {e}")
            raise
