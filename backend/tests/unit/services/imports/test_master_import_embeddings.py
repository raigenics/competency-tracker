"""
Integration tests for master import with embedding generation.

Tests that embeddings are created during master skill import.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.imports.master_import.master_import_service import MasterImportService
from app.services.imports.master_import.excel_parser import MasterSkillRow
from app.models.skill import Skill


class TestMasterImportWithEmbeddings:
    """Integration tests for master import with embedding generation."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock(spec=Session)
        # Mock query for skill fetching
        db.query.return_value.filter.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def sample_rows(self):
        """Create sample master skill rows."""
        return [
            MasterSkillRow(
                row_number=2,
                category="Backend",
                subcategory="Programming Languages",
                skill_name="Python",
                aliases=["Py", "Python3"],
                category_norm="backend",
                subcategory_norm="programminglanguages",
                skill_name_norm="python",
                aliases_norm=["py", "python3"]
            ),
            MasterSkillRow(
                row_number=3,
                category="Backend",
                subcategory="Programming Languages",
                skill_name="Java",
                aliases=["J8", "Java SE"],
                category_norm="backend",
                subcategory_norm="programminglanguages",
                skill_name_norm="java",
                aliases_norm=["j8", "javase"]
            )
        ]
    
    # ===== Test: Embeddings Generated on Import =====
    
    @patch('app.services.skill_resolution.skill_embedding_service.SkillEmbeddingService')
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_master_import_generates_embeddings(
        self, mock_provider_factory, mock_service_class, mock_db, sample_rows
    ):
        """Should generate embeddings for all imported skills."""
        # Arrange
        mock_provider = Mock()
        mock_provider_factory.return_value = mock_provider
        
        mock_embedding_service = Mock()
        mock_embedding_result = Mock()
        mock_embedding_result.succeeded = [1, 2]
        mock_embedding_result.failed = []
        mock_embedding_result.skipped = []
        mock_embedding_service.ensure_embeddings_for_skill_ids.return_value = mock_embedding_result
        mock_service_class.return_value = mock_embedding_service
        
        service = MasterImportService(db=mock_db)
        
        # Mock the data cache and upserter to track skill IDs
        with patch.object(service.cache, 'load_all'):
            with patch.object(service.conflict_detector, 'detect_file_duplicates', return_value=set()):
                with patch.object(service.upserter, 'upsert_category', return_value=1):
                    with patch.object(service.upserter, 'upsert_subcategory', return_value=1):
                        with patch.object(service.upserter, 'upsert_skill', side_effect=[(True, 1), (True, 2)]):
                            with patch.object(service.upserter, 'upsert_aliases', return_value=True):
                                # Act
                                response = service.process_import(sample_rows)
        
        # Assert
        # Should initialize embedding service
        mock_provider_factory.assert_called_once()
        mock_service_class.assert_called_once()
        
        # Should call ensure_embeddings_for_skill_ids with skill IDs
        mock_embedding_service.ensure_embeddings_for_skill_ids.assert_called_once()
        skill_ids_arg = mock_embedding_service.ensure_embeddings_for_skill_ids.call_args[0][0]
        assert set(skill_ids_arg) == {1, 2}
        
        # Should commit (at least once)
        assert mock_db.commit.called
    
    # ===== Test: Embedding Failures Don't Break Import =====
    
    @patch('app.services.skill_resolution.skill_embedding_service.SkillEmbeddingService')
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_master_import_continues_on_embedding_failure(
        self, mock_provider_factory, mock_service_class, mock_db, sample_rows
    ):
        """Should continue import even if embedding generation fails."""
        # Arrange
        mock_provider = Mock()
        mock_provider_factory.return_value = mock_provider
        
        mock_embedding_service = Mock()
        mock_embedding_result = Mock()
        mock_embedding_result.succeeded = [1]
        mock_embedding_result.failed = [
            {'skill_id': 2, 'skill_name': 'Java', 'error': 'API Error'}
        ]
        mock_embedding_result.skipped = []
        mock_embedding_service.ensure_embeddings_for_skill_ids.return_value = mock_embedding_result
        mock_service_class.return_value = mock_embedding_service
        
        service = MasterImportService(db=mock_db)
        
        # Mock the flow
        with patch.object(service.cache, 'load_all'):
            with patch.object(service.conflict_detector, 'detect_file_duplicates', return_value=set()):
                with patch.object(service.upserter, 'upsert_category', return_value=1):
                    with patch.object(service.upserter, 'upsert_subcategory', return_value=1):
                        with patch.object(service.upserter, 'upsert_skill', side_effect=[(True, 1), (True, 2)]):
                            with patch.object(service.upserter, 'upsert_aliases', return_value=True):
                                # Act
                                response = service.process_import(sample_rows)
        
        # Assert
        # Should still commit (skills were inserted successfully)
        assert mock_db.commit.called
        
        # Should include embedding failure in errors
        assert response.status == "success"  # Overall import succeeded
        
        # Check for embedding failure in errors
        embedding_errors = [e for e in response.errors if e.error_type == "EMBEDDING_GENERATION_FAILED"]
        assert len(embedding_errors) == 1
        assert embedding_errors[0].skill_name == "Java"
        assert "API Error" in embedding_errors[0].message
    
    # ===== Test: Import Without Embedding Provider =====
    
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_master_import_gracefully_degrades_without_provider(
        self, mock_provider_factory, mock_db, sample_rows
    ):
        """Should continue import even if embedding provider not available."""
        # Arrange
        # Make provider creation fail
        mock_provider_factory.side_effect = Exception("API key not configured")
        
        service = MasterImportService(db=mock_db)
        
        # Assert embedding service not initialized
        assert service.embedding_enabled is False
        assert service.embedding_service is None
        
        # Mock the flow
        with patch.object(service.cache, 'load_all'):
            with patch.object(service.conflict_detector, 'detect_file_duplicates', return_value=set()):
                with patch.object(service.upserter, 'upsert_category', return_value=1):
                    with patch.object(service.upserter, 'upsert_subcategory', return_value=1):
                        with patch.object(service.upserter, 'upsert_skill', side_effect=[(True, 1), (True, 2)]):
                            with patch.object(service.upserter, 'upsert_aliases', return_value=True):
                                # Act
                                response = service.process_import(sample_rows)
        
        # Assert
        # Should still succeed
        assert response.status == "success"
        assert mock_db.commit.called
        
        # No embedding errors
        embedding_errors = [e for e in response.errors if e.error_type == "EMBEDDING_GENERATION_FAILED"]
        assert len(embedding_errors) == 0
    
    # ===== Test: Empty Skill List =====
    
    @patch('app.services.skill_resolution.skill_embedding_service.SkillEmbeddingService')
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_master_import_handles_empty_skill_list(
        self, mock_provider_factory, mock_service_class, mock_db
    ):
        """Should handle import with no skills gracefully."""
        # Arrange
        mock_provider = Mock()
        mock_provider_factory.return_value = mock_provider
        
        mock_embedding_service = Mock()
        mock_service_class.return_value = mock_embedding_service
        
        service = MasterImportService(db=mock_db)
        
        with patch.object(service.cache, 'load_all'):
            with patch.object(service.conflict_detector, 'detect_file_duplicates', return_value=set()):
                # Act
                response = service.process_import([])
        
        # Assert
        # Should NOT call embedding service (no skills)
        mock_embedding_service.ensure_embeddings_for_skill_ids.assert_not_called()
        
        assert mock_db.commit.called
    
    # ===== Test: Embedding Service Receives Correct Skill IDs =====
    
    @patch('app.services.skill_resolution.skill_embedding_service.SkillEmbeddingService')
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_embedding_service_receives_all_skill_ids(
        self, mock_provider_factory, mock_service_class, mock_db, sample_rows
    ):
        """Should pass all processed skill IDs to embedding service."""
        # Arrange
        mock_provider = Mock()
        mock_provider_factory.return_value = mock_provider
        
        mock_embedding_service = Mock()
        mock_embedding_result = Mock()
        mock_embedding_result.succeeded = [10, 20]
        mock_embedding_result.failed = []
        mock_embedding_result.skipped = []
        mock_embedding_service.ensure_embeddings_for_skill_ids.return_value = mock_embedding_result
        mock_service_class.return_value = mock_embedding_service
        
        service = MasterImportService(db=mock_db)
        
        with patch.object(service.cache, 'load_all'):
            with patch.object(service.conflict_detector, 'detect_file_duplicates', return_value=set()):
                with patch.object(service.upserter, 'upsert_category', return_value=1):
                    with patch.object(service.upserter, 'upsert_subcategory', return_value=1):
                        # Return specific skill IDs
                        with patch.object(service.upserter, 'upsert_skill', side_effect=[(True, 10), (True, 20)]):
                            with patch.object(service.upserter, 'upsert_aliases', return_value=True):
                                # Act
                                response = service.process_import(sample_rows)
        
        # Assert
        call_args = mock_embedding_service.ensure_embeddings_for_skill_ids.call_args[0][0]
        assert call_args == [10, 20]
