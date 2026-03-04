"""
Unit tests for SkillResolverService.

Tests the 3-layer skill resolution strategy:
1. Exact match
2. Alias match
3. Embedding-based semantic similarity
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.skill_resolution.skill_resolver_service import (
    SkillResolverService,
    ResolutionResult
)
from app.services.skill_resolution.embedding_provider import FakeEmbeddingProvider
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias


class TestSkillResolverService:
    """Test suite for SkillResolverService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def fake_embedding_provider(self):
        """Create fake embedding provider for testing."""
        return FakeEmbeddingProvider(dimension=1536, deterministic=True)
    
    @pytest.fixture
    def resolver_without_embedding(self, mock_db):
        """Create resolver without embedding support."""
        return SkillResolverService(db=mock_db, enable_embedding=False)
    
    @pytest.fixture
    def resolver_with_embedding(self, mock_db, fake_embedding_provider):
        """Create resolver with embedding support."""
        return SkillResolverService(
            db=mock_db,
            embedding_provider=fake_embedding_provider,
            enable_embedding=True
        )
    
    # ===== Test: Exact Match =====
    
    def test_exact_match_found(self, resolver_without_embedding, mock_db):
        """Should resolve via exact match and NOT call alias or embedding."""
        # Arrange
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 123
        mock_skill.skill_name = "Python"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        # Act
        result = resolver_without_embedding.resolve("python")
        
        # Assert
        assert result.resolved_skill_id == 123
        assert result.resolution_method == "exact"
        assert result.resolution_confidence == 1.0
        assert result.is_resolved() is True
        
        # Verify exact match query was called
        mock_db.query.assert_called_once_with(Skill)
    
    def test_exact_match_case_insensitive(self, resolver_without_embedding, mock_db):
        """Exact match should be case-insensitive."""
        # Arrange
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 456
        mock_skill.skill_name = "JavaScript"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        # Act
        result = resolver_without_embedding.resolve("javascript")
        
        # Assert
        assert result.resolved_skill_id == 456
        assert result.resolution_method == "exact"
        assert result.resolution_confidence == 1.0
    
    # ===== Test: Alias Match =====
    
    def test_alias_match_when_exact_fails(self, resolver_without_embedding, mock_db):
        """Should resolve via alias when exact match fails."""
        # Arrange
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 789
        mock_alias.alias_text = "js"
        
        # Setup query mock to return None for Skill, then alias for SkillAlias
        def query_side_effect(model):
            mock_query = Mock()
            if model == Skill:
                mock_query.filter.return_value.first.return_value = None
            elif model == SkillAlias:
                mock_query.filter.return_value.first.return_value = mock_alias
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = resolver_without_embedding.resolve("js")
        
        # Assert
        assert result.resolved_skill_id == 789
        assert result.resolution_method == "alias"
        assert result.resolution_confidence == 1.0
        assert result.is_resolved() is True
        
        # Verify both queries were called
        assert mock_db.query.call_count == 2
    
    def test_alias_match_case_insensitive(self, resolver_without_embedding, mock_db):
        """Alias match should be case-insensitive."""
        # Arrange
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 999
        
        def query_side_effect(model):
            mock_query = Mock()
            if model == Skill:
                mock_query.filter.return_value.first.return_value = None
            elif model == SkillAlias:
                mock_query.filter.return_value.first.return_value = mock_alias
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = resolver_without_embedding.resolve("typescript")
        
        # Assert
        assert result.resolved_skill_id == 999
        assert result.resolution_method == "alias"
    
    # ===== Test: Embedding Match - NOT called when exact/alias succeeds =====
    
    def test_embedding_not_called_on_exact_match(self, resolver_with_embedding, mock_db):
        """Embedding provider should NOT be called when exact match succeeds."""
        # Arrange
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 111
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        # Spy on embedding provider
        with patch.object(resolver_with_embedding.embedding_provider, 'embed') as mock_embed:
            # Act
            result = resolver_with_embedding.resolve("python")
            
            # Assert
            assert result.resolved_skill_id == 111
            assert result.resolution_method == "exact"
            mock_embed.assert_not_called()
    
    def test_embedding_not_called_on_alias_match(self, resolver_with_embedding, mock_db):
        """Embedding provider should NOT be called when alias match succeeds."""
        # Arrange
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 222
        
        def query_side_effect(model):
            mock_query = Mock()
            if model == Skill:
                mock_query.filter.return_value.first.return_value = None
            elif model == SkillAlias:
                mock_query.filter.return_value.first.return_value = mock_alias
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Spy on embedding provider
        with patch.object(resolver_with_embedding.embedding_provider, 'embed') as mock_embed:
            # Act
            result = resolver_with_embedding.resolve("js")
            
            # Assert
            assert result.resolved_skill_id == 222
            assert result.resolution_method == "alias"
            mock_embed.assert_not_called()
    
    # ===== Test: Embedding Match - High Similarity (>= 0.88) =====
    
    def test_embedding_high_similarity_auto_accept(self, resolver_with_embedding, mock_db):
        """High similarity (>= 0.88) should auto-accept with resolved_skill_id set."""
        # Arrange: No exact or alias match
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Mock embedding repository to return high similarity
        with patch.object(resolver_with_embedding.embedding_repo, 'find_top_k') as mock_find:
            mock_find.return_value = [
                (555, 0.92),  # High similarity
                (556, 0.75),
                (557, 0.60)
            ]
            
            # Act
            result = resolver_with_embedding.resolve("machine learning")
            
            # Assert
            assert result.resolved_skill_id == 555
            assert result.resolution_method == "embedding"
            assert result.resolution_confidence == 0.92
            assert result.is_resolved() is True
    
    def test_embedding_threshold_exact_088(self, resolver_with_embedding, mock_db):
        """Similarity exactly at 0.88 should auto-accept."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(resolver_with_embedding.embedding_repo, 'find_top_k') as mock_find:
            mock_find.return_value = [(333, 0.88)]
            
            # Act
            result = resolver_with_embedding.resolve("data science")
            
            # Assert
            assert result.resolved_skill_id == 333
            assert result.resolution_method == "embedding"
            assert result.resolution_confidence == 0.88
    
    # ===== Test: Embedding Match - Medium Similarity (0.80-0.88) =====
    
    def test_embedding_medium_similarity_review(self, resolver_with_embedding, mock_db):
        """Medium similarity (0.80-0.88) should mark for review, NOT auto-resolve."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(resolver_with_embedding.embedding_repo, 'find_top_k') as mock_find:
            mock_find.return_value = [(444, 0.85)]
            
            # Act
            result = resolver_with_embedding.resolve("deep learning")
            
            # Assert
            assert result.resolved_skill_id is None  # NOT resolved
            assert result.resolution_method == "review"
            assert result.resolution_confidence == 0.85
            assert result.is_resolved() is False
    
    def test_embedding_threshold_exact_080(self, resolver_with_embedding, mock_db):
        """Similarity exactly at 0.80 should mark for review."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(resolver_with_embedding.embedding_repo, 'find_top_k') as mock_find:
            mock_find.return_value = [(666, 0.80)]
            
            # Act
            result = resolver_with_embedding.resolve("neural networks")
            
            # Assert
            assert result.resolved_skill_id is None
            assert result.resolution_method == "review"
            assert result.resolution_confidence == 0.80
    
    # ===== Test: Embedding Match - Low Similarity (< 0.80) =====
    
    def test_embedding_low_similarity_unresolved(self, resolver_with_embedding, mock_db):
        """Low similarity (< 0.80) should remain unresolved."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(resolver_with_embedding.embedding_repo, 'find_top_k') as mock_find:
            mock_find.return_value = [(777, 0.65)]
            
            # Act
            result = resolver_with_embedding.resolve("quantum computing")
            
            # Assert
            assert result.resolved_skill_id is None
            assert result.resolution_method == "unresolved"
            # Low similarity results fall through to the generic "unresolved" handler
            # which doesn't preserve the similarity score (by design)
            assert result.resolution_confidence is None
            assert result.is_resolved() is False
    
    # ===== Test: Unresolved (all layers fail) =====
    
    def test_unresolved_when_all_layers_fail(self, resolver_without_embedding, mock_db):
        """Should return unresolved when exact and alias both fail."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = resolver_without_embedding.resolve("unknown skill")
        
        # Assert
        assert result.resolved_skill_id is None
        assert result.resolution_method == "unresolved"
        assert result.resolution_confidence is None
        assert result.is_resolved() is False
    
    def test_unresolved_when_no_embedding_matches(self, resolver_with_embedding, mock_db):
        """Should return unresolved when embedding repo returns empty list."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        with patch.object(resolver_with_embedding.embedding_repo, 'find_top_k') as mock_find:
            mock_find.return_value = []  # No matches
            
            # Act
            result = resolver_with_embedding.resolve("completely unknown")
            
            # Assert
            assert result.resolved_skill_id is None
            assert result.resolution_method == "unresolved"
            assert result.resolution_confidence is None
    
    # ===== Test: Embedding Provider Failure Handling =====
    
    def test_embedding_provider_exception_graceful_fallback(self, resolver_with_embedding, mock_db):
        """Should handle embedding provider exceptions gracefully without failing import."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Make embedding provider raise exception
        with patch.object(resolver_with_embedding.embedding_provider, 'embed') as mock_embed:
            mock_embed.side_effect = Exception("API Error")
            
            # Act
            result = resolver_with_embedding.resolve("test skill")
            
            # Assert - should fall back to unresolved, NOT raise exception
            assert result.resolved_skill_id is None
            assert result.resolution_method == "unresolved"
            assert result.resolution_confidence is None
    
    def test_embedding_repo_exception_graceful_fallback(self, resolver_with_embedding, mock_db):
        """Should handle embedding repository exceptions gracefully."""
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Make repository raise exception
        with patch.object(resolver_with_embedding.embedding_repo, 'find_top_k') as mock_find:
            mock_find.side_effect = Exception("Database Error")
            
            # Act
            result = resolver_with_embedding.resolve("test skill")
            
            # Assert
            assert result.resolved_skill_id is None
            assert result.resolution_method == "unresolved"
            assert result.resolution_confidence is None
    
    # ===== Test: ResolutionResult Helper =====
    
    def test_resolution_result_is_resolved_true(self):
        """is_resolved() should return True when skill_id is set."""
        result = ResolutionResult(
            resolved_skill_id=123,
            resolution_method="exact",
            resolution_confidence=1.0
        )
        assert result.is_resolved() is True
    
    def test_resolution_result_is_resolved_false(self):
        """is_resolved() should return False when skill_id is None."""
        result = ResolutionResult(
            resolved_skill_id=None,
            resolution_method="review",
            resolution_confidence=0.85
        )
        assert result.is_resolved() is False
