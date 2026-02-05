"""
Skill Embedding model - stores vector embeddings for skills.

This table stores vector embeddings for semantic search and similarity matching.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base


class SkillEmbedding(Base):
    """
    Skill embedding model for semantic search.
    
    Stores vector embeddings generated from skill names and descriptions
    to enable semantic similarity search and skill matching.
    """
    
    __tablename__ = "skill_embeddings"
    
    # Primary key and foreign key
    skill_id = Column(
        Integer, 
        ForeignKey("skills.skill_id", ondelete="CASCADE"), 
        primary_key=True, 
        index=True
    )
    
    # Model metadata
    model_name = Column(Text, nullable=False)
    
    # Vector embedding (1536 dimensions for OpenAI text-embedding-ada-002)
    embedding = Column(Vector(1536), nullable=False)
    
    # Version tracking
    embedding_version = Column(Text, nullable=True)
    
    # Timestamp
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    skill = relationship("Skill", backref="embedding")
    
    def __repr__(self):
        return f"<SkillEmbedding(skill_id={self.skill_id}, model='{self.model_name}', version='{self.embedding_version}')>"
