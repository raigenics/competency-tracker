"""
Skill resolution services for matching raw skill inputs to master skills.

This package provides a 3-layer skill resolution system:
1. Exact match on skill names
2. Alias match on skill aliases
3. Embedding-based semantic similarity matching
"""

from .skill_embedding_service import SkillEmbeddingService, EmbeddingResult

__all__ = ['SkillEmbeddingService', 'EmbeddingResult']
