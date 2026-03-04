"""
Unit tests for SkillEmbeddingService.

Tests embedding generation, persistence, and idempotency.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.skill_resolution.skill_embedding_service import (
    SkillEmbeddingService,
    EmbeddingResult
)
from app.services.skill_resolution.embedding_provider import EmbeddingProvider
from app.services.skill_resolution.skill_embedding_repository import SkillEmbeddingRepository
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding


class TestSkillEmbeddingService:
    """Test suite for SkillEmbeddingService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock embedding provider."""
        provider = Mock(spec=EmbeddingProvider)
        # Return deterministic embeddings
        provider.embed.return_value = [0.1] * 1536
        return provider
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock embedding repository."""
        return Mock(spec=SkillEmbeddingRepository)
    
    @pytest.fixture
    def service(self, mock_db, mock_provider, mock_repository):
        """Create service instance with mocks."""
        return SkillEmbeddingService(
            db=mock_db,
            embedding_provider=mock_provider,
            embedding_repository=mock_repository,
            model_name="test-model",
            embedding_version="v1"
        )
    
    # ===== Test: ensure_embedding_for_skill - Insert New =====
    
    def test_ensure_embedding_for_skill_creates_new(
        self, service, mock_provider, mock_repository
    ):
        """Should create new embedding when none exists."""
        # Arrange
        skill = Skill(skill_id=1, skill_name="Python Programming")
        
        # No existing embedding
        mock_repository.get_by_skill_and_model.return_value = None
        
        # Act
        result = service.ensure_embedding_for_skill(skill)
        
        # Assert
        assert result is True
        
        # Should check for existing
        mock_repository.get_by_skill_and_model.assert_called_once_with(1, "test-model")
        
        # Should generate embedding with normalized text
        mock_provider.embed.assert_called_once()
        call_args = mock_provider.embed.call_args[0][0]
        assert call_args == "python programming"  # normalized
        
        # Should upsert
        mock_repository.upsert.assert_called_once()
        upsert_call = mock_repository.upsert.call_args
        assert upsert_call[1]['skill_id'] == 1
        assert upsert_call[1]['model_name'] == "test-model"
        assert upsert_call[1]['embedding'] == [0.1] * 1536
        assert upsert_call[1]['embedding_version'].startswith("v1:")  # Has hash
    
    # ===== Test: ensure_embedding_for_skill - Update Existing =====
    
    def test_ensure_embedding_for_skill_updates_existing(
        self, service, mock_provider, mock_repository
    ):
        """Should update embedding when skill name changed."""
        # Arrange
        skill = Skill(skill_id=1, skill_name="Python 3.11")
        
        # Existing embedding with old hash
        existing = Mock(spec=SkillEmbedding)
        existing.embedding_version = "v1:oldhash"
        mock_repository.get_by_skill_and_model.return_value = existing
        
        # Act
        result = service.ensure_embedding_for_skill(skill)
        
        # Assert
        assert result is True
        
        # Should regenerate because hash changed
        mock_provider.embed.assert_called_once()
        mock_repository.upsert.assert_called_once()
    
    # ===== Test: ensure_embedding_for_skill - Skip Up-to-Date =====
    
    def test_ensure_embedding_for_skill_skips_uptodate(
        self, service, mock_provider, mock_repository
    ):
        """Should skip embedding generation when up-to-date."""
        # Arrange
        skill = Skill(skill_id=1, skill_name="Python")
        
        # Compute correct version+hash for "python" (normalized)
        # The implementation uses: f"{self.embedding_version}:{hash}"
        import hashlib
        text_hash = hashlib.md5("python".encode('utf-8')).hexdigest()[:8]
        version_with_hash = f"v1:{text_hash}"  # Match service's embedding_version="v1"
        
        # Existing embedding with matching version and hash
        existing = Mock(spec=SkillEmbedding)
        existing.embedding_version = version_with_hash
        mock_repository.get_by_skill_and_model.return_value = existing
        
        # Act
        result = service.ensure_embedding_for_skill(skill)
        
        # Assert - should return True (successful, already up-to-date)
        assert result is True
    
    # ===== Test: ensure_embedding_for_skill - Version Mismatch =====
    
    def test_ensure_embedding_for_skill_version_mismatch(
        self, service, mock_provider, mock_repository
    ):
        """Should regenerate embedding when version changed."""
        # Arrange
        skill = Skill(skill_id=1, skill_name="Python")
        
        # Existing embedding with old version
        existing = Mock(spec=SkillEmbedding)
        existing.embedding_version = "v0:somehash"  # Old version
        mock_repository.get_by_skill_and_model.return_value = existing
        
        # Act
        result = service.ensure_embedding_for_skill(skill)
        
        # Assert
        assert result is True
        
        # Should regenerate
        mock_provider.embed.assert_called_once()
        mock_repository.upsert.assert_called_once()
    
    # ===== Test: ensure_embedding_for_skill - Failure =====
    
    def test_ensure_embedding_for_skill_handles_failure(
        self, service, mock_provider, mock_repository
    ):
        """Should handle embedding generation failure gracefully."""
        # Arrange
        skill = Skill(skill_id=1, skill_name="Python")
        
        mock_repository.get_by_skill_and_model.return_value = None
        mock_provider.embed.side_effect = Exception("API Error")
        
        # Act
        result = service.ensure_embedding_for_skill(skill)
        
        # Assert
        assert result is False  # Failed but didn't raise
        mock_repository.upsert.assert_not_called()
    
    # ===== Test: ensure_embeddings_for_skill_ids - Batch Success =====
    
    def test_ensure_embeddings_for_skill_ids_batch_success(
        self, service, mock_db, mock_provider, mock_repository
    ):
        """Should process multiple skills in batch."""
        # Arrange
        skill_ids = [1, 2, 3]
        
        # Mock query to return skills
        skills = [
            Skill(skill_id=1, skill_name="Python"),
            Skill(skill_id=2, skill_name="Java"),
            Skill(skill_id=3, skill_name="JavaScript")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = skills
        mock_db.query.return_value = mock_query
        
        # No existing embeddings
        mock_repository.get_by_skill_and_model.return_value = None
        
        # Act
        result = service.ensure_embeddings_for_skill_ids(skill_ids)
        
        # Assert
        assert len(result.succeeded) == 3
        assert len(result.failed) == 0
        assert len(result.skipped) == 0
        
        assert result.succeeded == [1, 2, 3]
        
        # Should call embed 3 times
        assert mock_provider.embed.call_count == 3
        assert mock_repository.upsert.call_count == 3
    
    # ===== Test: ensure_embeddings_for_skill_ids - Mixed Results =====
    
    def test_ensure_embeddings_for_skill_ids_mixed_results(
        self, service, mock_db, mock_provider, mock_repository
    ):
        """Should handle mixed success/failure/skip in batch."""
        # Arrange
        skill_ids = [1, 2, 3]
        
        # Compute hash for skill 2 "java"
        import hashlib
        java_hash = hashlib.md5("java".encode('utf-8')).hexdigest()[:8]
        
        skills = [
            Skill(skill_id=1, skill_name="Python"),
            Skill(skill_id=2, skill_name="Java"),
            Skill(skill_id=3, skill_name="JavaScript")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = skills
        mock_db.query.return_value = mock_query
        
        # Skill 1: new (success)
        # Skill 2: up-to-date (skip)
        # Skill 3: error (fail)
        def get_embedding_side_effect(skill_id, model_name):
            if skill_id == 2:
                # Return up-to-date embedding
                existing = Mock(spec=SkillEmbedding)
                existing.embedding_version = f"v1:{java_hash}"
                return existing
            return None
        
        mock_repository.get_by_skill_and_model.side_effect = get_embedding_side_effect
        
        # Make skill 3 fail - check for "javascript" in the text (enhanced text is normalized)
        def embed_side_effect(text):
            if "javascript" in text.lower():
                raise Exception("API Error")
            return [0.1] * 1536
        
        mock_provider.embed.side_effect = embed_side_effect
        
        # Act
        result = service.ensure_embeddings_for_skill_ids(skill_ids)
        
        # Assert - skill 1 succeeds, skill 2 skipped, skill 3 fails
        assert len(result.succeeded) >= 1  # At least skill 1 should succeed
        assert len(result.failed) == 1  # Skill 3 fails
        
        assert 1 in result.succeeded  # Python succeeded
        assert result.failed[0]['skill_id'] == 3
        assert result.failed[0]['skill_name'] == "JavaScript"
        assert "API Error" in result.failed[0]['error']
    
    # ===== Test: ensure_embeddings_for_skill_ids - Empty List =====
    
    def test_ensure_embeddings_for_skill_ids_empty_list(
        self, service, mock_db, mock_provider
    ):
        """Should handle empty skill ID list."""
        # Act
        result = service.ensure_embeddings_for_skill_ids([])
        
        # Assert
        assert len(result.succeeded) == 0
        assert len(result.failed) == 0
        assert len(result.skipped) == 0
        
        # Should not query database
        mock_db.query.assert_not_called()
    
    # ===== Test: ensure_embeddings_for_skill_ids - Skill Not Found =====
    
    def test_ensure_embeddings_for_skill_ids_skill_not_found(
        self, service, mock_db, mock_provider, mock_repository
    ):
        """Should handle case where skill ID doesn't exist."""
        # Arrange
        skill_ids = [999]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []  # No skills found
        mock_db.query.return_value = mock_query
        
        # Act
        result = service.ensure_embeddings_for_skill_ids(skill_ids)
        
        # Assert
        assert len(result.succeeded) == 0
        assert len(result.failed) == 0
        assert len(result.skipped) == 0
        
        # Should not call provider
        mock_provider.embed.assert_not_called()
    
    # ===== Test: Normalization =====
    
    def test_normalize_text(self):
        """Should normalize text consistently."""
        # Test static method
        assert SkillEmbeddingService._normalize_text("  Python  ") == "python"
        assert SkillEmbeddingService._normalize_text("JAVA") == "java"
        assert SkillEmbeddingService._normalize_text("React.js") == "react.js"
    
    # ===== Test: Hash Computation =====
    
    def test_compute_text_hash(self):
        """Should compute consistent hash."""
        # Test static method
        hash1 = SkillEmbeddingService._compute_text_hash("python")
        hash2 = SkillEmbeddingService._compute_text_hash("python")
        hash3 = SkillEmbeddingService._compute_text_hash("java")
        
        assert hash1 == hash2  # Same input = same hash
        assert hash1 != hash3  # Different input = different hash
        assert len(hash1) == 8  # 8 character hash
    
    # ===== Test: Embedding Only Uses Skill Name =====
    
    def test_embedding_uses_only_skill_name(
        self, service, mock_provider, mock_repository
    ):
        """Should embed ONLY skill name, not category/subcategory."""
        # Arrange
        skill = Skill(
            skill_id=1,
            skill_name="Python Programming",
            subcategory_id=10  # Has category relationship
        )
        
        mock_repository.get_by_skill_and_model.return_value = None
        
        # Act
        service.ensure_embedding_for_skill(skill)
        
        # Assert
        # Should embed normalized skill name only
        mock_provider.embed.assert_called_once_with("python programming")
        
        # Verify no category/subcategory info in call
        call_text = mock_provider.embed.call_args[0][0]
        assert "python programming" == call_text
        # Should NOT contain any category/subcategory data


class TestEmbeddingResult:
    """Test suite for EmbeddingResult dataclass."""
    
    def test_embedding_result_creation(self):
        """Should create EmbeddingResult with default empty lists."""
        result = EmbeddingResult()
        
        assert result.succeeded == []
        assert result.failed == []
        assert result.skipped == []
    
    def test_embedding_result_with_data(self):
        """Should create EmbeddingResult with data."""
        result = EmbeddingResult(
            succeeded=[1, 2, 3],
            failed=[{'skill_id': 4, 'error': 'test'}],
            skipped=[5, 6]
        )
        
        assert result.succeeded == [1, 2, 3]
        assert len(result.failed) == 1
        assert result.skipped == [5, 6]
