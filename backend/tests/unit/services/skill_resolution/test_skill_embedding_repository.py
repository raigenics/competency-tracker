"""
Unit tests for SkillEmbeddingRepository.

Tests vector similarity search with pgvector.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.skill_resolution.skill_embedding_repository import SkillEmbeddingRepository
from app.models.skill_embedding import SkillEmbedding


class TestSkillEmbeddingRepository:
    """Test suite for SkillEmbeddingRepository."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance."""
        return SkillEmbeddingRepository(db=mock_db)
    
    # ===== Test: find_top_k =====
    
    def test_find_top_k_returns_matches(self, repository, mock_db):
        """Should return top K matches ordered by similarity."""
        # Arrange
        query_vector = [0.1] * 1536
        
        # Mock database query result
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            (101, 0.95),
            (102, 0.88),
            (103, 0.75),
            (104, 0.60),
            (105, 0.45)
        ]))
        
        mock_db.execute.return_value = mock_result
        
        # Act
        matches = repository.find_top_k(query_vector, k=5)
        
        # Assert
        assert len(matches) == 5
        assert matches[0] == (101, 0.95)
        assert matches[1] == (102, 0.88)
        assert matches[4] == (105, 0.45)
        
        # Verify query was executed
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert 'similarity' in call_args[0][0].text.lower()
        assert call_args[1]['k'] == 5
    
    def test_find_top_k_with_model_filter(self, repository, mock_db):
        """Should filter by model_name when provided."""
        # Arrange
        query_vector = [0.2] * 1536
        
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            (201, 0.90),
            (202, 0.85)
        ]))
        
        mock_db.execute.return_value = mock_result
        
        # Act
        matches = repository.find_top_k(query_vector, k=3, model_name="text-embedding-3-small")
        
        # Assert
        assert len(matches) == 2
        
        # Verify model_name was included in query
        call_args = mock_db.execute.call_args
        assert call_args[1]['model_name'] == "text-embedding-3-small"
        assert 'model_name' in call_args[0][0].text
    
    def test_find_top_k_empty_results(self, repository, mock_db):
        """Should return empty list when no matches found."""
        # Arrange
        query_vector = [0.3] * 1536
        
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        
        mock_db.execute.return_value = mock_result
        
        # Act
        matches = repository.find_top_k(query_vector, k=5)
        
        # Assert
        assert matches == []
    
    def test_find_top_k_respects_limit(self, repository, mock_db):
        """Should limit results to k matches."""
        # Arrange
        query_vector = [0.4] * 1536
        
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            (301, 0.95),
            (302, 0.90),
            (303, 0.85)
        ]))
        
        mock_db.execute.return_value = mock_result
        
        # Act
        matches = repository.find_top_k(query_vector, k=3)
        
        # Assert
        assert len(matches) == 3
        
        # Verify LIMIT clause
        call_args = mock_db.execute.call_args
        assert call_args[1]['k'] == 3
    
    def test_find_top_k_converts_similarity_to_float(self, repository, mock_db):
        """Should convert similarity scores to float."""
        # Arrange
        query_vector = [0.5] * 1536
        
        # Mock result with Decimal values (common from PostgreSQL)
        from decimal import Decimal
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            (401, Decimal('0.9234')),
            (402, Decimal('0.8567'))
        ]))
        
        mock_db.execute.return_value = mock_result
        
        # Act
        matches = repository.find_top_k(query_vector, k=2)
        
        # Assert
        assert isinstance(matches[0][1], float)
        assert isinstance(matches[1][1], float)
        assert matches[0][1] == pytest.approx(0.9234, abs=0.0001)
        assert matches[1][1] == pytest.approx(0.8567, abs=0.0001)
    
    def test_find_top_k_database_exception(self, repository, mock_db):
        """Should raise exception when database query fails."""
        # Arrange
        query_vector = [0.6] * 1536
        mock_db.execute.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            repository.find_top_k(query_vector, k=5)
    
    # ===== Test: get_embedding_count =====
    
    def test_get_embedding_count_returns_count(self, repository, mock_db):
        """Should return total count of embeddings."""
        # Arrange
        mock_query = Mock()
        mock_query.count.return_value = 1234
        mock_db.query.return_value = mock_query
        
        # Act
        count = repository.get_embedding_count()
        
        # Assert
        assert count == 1234
        mock_db.query.assert_called_once_with(SkillEmbedding)
    
    def test_get_embedding_count_zero(self, repository, mock_db):
        """Should return 0 when no embeddings exist."""
        # Arrange
        mock_query = Mock()
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query
        
        # Act
        count = repository.get_embedding_count()
        
        # Assert
        assert count == 0
    
    def test_get_embedding_count_exception(self, repository, mock_db):
        """Should raise exception when count query fails."""
        # Arrange
        mock_db.query.side_effect = Exception("Query error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Query error"):
            repository.get_embedding_count()
    
    # ===== Test: has_embedding =====
    
    def test_has_embedding_returns_true(self, repository, mock_db):
        """Should return True when embedding exists."""
        # Arrange
        mock_embedding = Mock(spec=SkillEmbedding)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_embedding
        mock_db.query.return_value = mock_query
        
        # Act
        exists = repository.has_embedding(skill_id=123)
        
        # Assert
        assert exists is True
        mock_db.query.assert_called_once_with(SkillEmbedding)
    
    def test_has_embedding_returns_false(self, repository, mock_db):
        """Should return False when embedding does not exist."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act
        exists = repository.has_embedding(skill_id=999)
        
        # Assert
        assert exists is False
    
    def test_has_embedding_exception(self, repository, mock_db):
        """Should raise exception when query fails."""
        # Arrange
        mock_db.query.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            repository.has_embedding(skill_id=456)
    
    # ===== Test: get_by_skill_and_model =====
    
    def test_get_by_skill_and_model_returns_embedding(self, repository, mock_db):
        """Should return embedding when found."""
        # Arrange
        mock_embedding = Mock(spec=SkillEmbedding)
        mock_embedding.skill_id = 1
        mock_embedding.model_name = "test-model"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_embedding
        mock_db.query.return_value = mock_query
        
        # Act
        result = repository.get_by_skill_and_model(1, "test-model")
        
        # Assert
        assert result == mock_embedding
        mock_db.query.assert_called_once_with(SkillEmbedding)
    
    def test_get_by_skill_and_model_returns_none(self, repository, mock_db):
        """Should return None when embedding not found."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act
        result = repository.get_by_skill_and_model(999, "test-model")
        
        # Assert
        assert result is None
    
    # ===== Test: upsert - Insert New =====
    
    def test_upsert_inserts_new_embedding(self, repository, mock_db):
        """Should insert new embedding when none exists."""
        # Arrange
        from datetime import datetime
        embedding_vector = [0.1] * 1536
        updated_at = datetime(2026, 2, 5, 12, 0, 0)
        
        # Mock get_by_skill_and_model to return None (no existing)
        with patch.object(repository, 'get_by_skill_and_model', return_value=None):
            # Act
            result = repository.upsert(
                skill_id=1,
                model_name="test-model",
                embedding=embedding_vector,
                embedding_version="v1:abc123",
                updated_at=updated_at
            )
        
        # Assert
        # Should add new embedding to session
        mock_db.add.assert_called_once()
        added_embedding = mock_db.add.call_args[0][0]
        
        assert added_embedding.skill_id == 1
        assert added_embedding.model_name == "test-model"
        assert added_embedding.embedding == embedding_vector
        assert added_embedding.embedding_version == "v1:abc123"
        assert added_embedding.updated_at == updated_at
        
        # Should flush
        mock_db.flush.assert_called_once()
    
    # ===== Test: upsert - Update Existing =====
    
    def test_upsert_updates_existing_embedding(self, repository, mock_db):
        """Should update existing embedding."""
        # Arrange
        from datetime import datetime
        embedding_vector = [0.2] * 1536
        updated_at = datetime(2026, 2, 5, 12, 0, 0)
        
        # Mock existing embedding
        existing = Mock(spec=SkillEmbedding)
        existing.skill_id = 1
        existing.model_name = "test-model"
        existing.embedding = [0.1] * 1536
        existing.embedding_version = "v1:old"
        
        with patch.object(repository, 'get_by_skill_and_model', return_value=existing):
            # Act
            result = repository.upsert(
                skill_id=1,
                model_name="test-model",
                embedding=embedding_vector,
                embedding_version="v1:new",
                updated_at=updated_at
            )
        
        # Assert
        # Should update existing embedding
        assert existing.embedding == embedding_vector
        assert existing.embedding_version == "v1:new"
        assert existing.updated_at == updated_at
        
        # Should NOT add new
        mock_db.add.assert_not_called()
        
        # Should flush
        mock_db.flush.assert_called_once()
    
    # ===== Test: upsert - Default Timestamp =====
    
    def test_upsert_uses_default_timestamp(self, repository, mock_db):
        """Should use current time when updated_at not provided."""
        # Arrange
        embedding_vector = [0.1] * 1536
        
        with patch.object(repository, 'get_by_skill_and_model', return_value=None):
            # Act
            with patch('app.services.skill_resolution.skill_embedding_repository.datetime') as mock_datetime:
                from datetime import datetime
                mock_now = datetime(2026, 2, 5, 12, 30, 0)
                mock_datetime.utcnow.return_value = mock_now
                
                result = repository.upsert(
                    skill_id=1,
                    model_name="test-model",
                    embedding=embedding_vector,
                    embedding_version="v1"
                )
        
        # Assert
        added_embedding = mock_db.add.call_args[0][0]
        assert added_embedding.updated_at == mock_now
