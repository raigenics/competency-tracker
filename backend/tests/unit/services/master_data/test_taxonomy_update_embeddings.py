"""
Unit tests for embedding updates in manual Skill Taxonomy workflows.

Tests that embeddings are correctly generated and persisted when:
1. Add Skill - creates embedding for new skill
2. Edit Skill Name - regenerates embedding when name changes
3. Create Alias - regenerates embedding for parent skill
4. Update Alias (text) - regenerates embedding when alias_text changes
5. Delete Alias - regenerates embedding for parent skill
6. Update Alias (non-text fields) - does NOT regenerate embedding
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.master_data.taxonomy_update_service import (
    create_skill,
    update_skill_name,
    create_alias,
    update_alias,
    delete_alias,
    _update_skill_embedding,
)
from app.services.master_data.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    EmbeddingError,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_skill():
    """Factory to create mock Skill objects."""
    def _create(skill_id=1, skill_name="React", subcategory_id=1, **kwargs):
        skill = Mock()
        skill.skill_id = skill_id
        skill.skill_name = skill_name
        skill.subcategory_id = subcategory_id
        skill.created_at = kwargs.get('created_at', datetime(2024, 1, 1))
        skill.created_by = kwargs.get('created_by', 'admin')
        skill.aliases = kwargs.get('aliases', [])
        return skill
    return _create


@pytest.fixture
def mock_alias():
    """Factory to create mock Alias objects."""
    def _create(alias_id=1, alias_text="ReactJS", skill_id=1, **kwargs):
        alias = Mock()
        alias.alias_id = alias_id
        alias.alias_text = alias_text
        alias.skill_id = skill_id
        alias.source = kwargs.get('source', 'manual')
        alias.confidence_score = kwargs.get('confidence_score', 1.0)
        alias.created_at = kwargs.get('created_at', datetime(2024, 1, 1))
        return alias
    return _create


@pytest.fixture
def mock_subcategory():
    """Factory to create mock Subcategory objects."""
    def _create(subcategory_id=1, subcategory_name="Frontend", **kwargs):
        subcategory = Mock()
        subcategory.subcategory_id = subcategory_id
        subcategory.subcategory_name = subcategory_name
        subcategory.deleted_at = None
        return subcategory
    return _create


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    service = Mock()
    service.ensure_embedding_for_skill.return_value = True
    return service


# ============================================================================
# _update_skill_embedding TESTS
# ============================================================================

class TestUpdateSkillEmbedding:
    """Tests for the _update_skill_embedding helper function."""
    
    @patch('app.services.skill_resolution.skill_embedding_service.SkillEmbeddingService')
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_success_generates_embedding(self, mock_create_provider, mock_service_class, mock_db, mock_skill):
        """Should generate embedding for skill successfully."""
        # Arrange
        skill = mock_skill(skill_id=42, skill_name="Kubernetes")
        mock_provider = Mock()
        mock_create_provider.return_value = mock_provider
        
        mock_service = Mock()
        mock_service.ensure_embedding_for_skill.return_value = True
        mock_service_class.return_value = mock_service
        
        # Act
        _update_skill_embedding(mock_db, skill)
        
        # Assert
        mock_create_provider.assert_called_once()
        mock_service_class.assert_called_once_with(
            db=mock_db,
            embedding_provider=mock_provider
        )
        mock_service.ensure_embedding_for_skill.assert_called_once_with(skill)
    
    @patch('app.services.skill_resolution.skill_embedding_service.SkillEmbeddingService')
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_raises_embedding_error_on_failure(self, mock_create_provider, mock_service_class, mock_db, mock_skill):
        """Should raise EmbeddingError when embedding generation fails."""
        # Arrange
        skill = mock_skill(skill_id=42, skill_name="Kubernetes")
        mock_provider = Mock()
        mock_create_provider.return_value = mock_provider
        
        mock_service = Mock()
        mock_service.ensure_embedding_for_skill.return_value = False  # Failure
        mock_service_class.return_value = mock_service
        
        # Act & Assert
        with pytest.raises(EmbeddingError) as exc_info:
            _update_skill_embedding(mock_db, skill)
        
        assert "Failed to generate embedding" in str(exc_info.value.message)
        assert "Kubernetes" in str(exc_info.value.message)
    
    @patch('app.services.skill_resolution.embedding_provider.create_embedding_provider')
    def test_raises_embedding_error_on_provider_unavailable(self, mock_create_provider, mock_db, mock_skill):
        """Should raise EmbeddingError when embedding provider is unavailable."""
        # Arrange
        skill = mock_skill(skill_id=42, skill_name="Kubernetes")
        mock_create_provider.side_effect = Exception("API key not configured")
        
        # Act & Assert
        with pytest.raises(EmbeddingError) as exc_info:
            _update_skill_embedding(mock_db, skill)
        
        assert "Embedding generation failed" in str(exc_info.value.message)


# ============================================================================
# CREATE SKILL EMBEDDING TESTS
# ============================================================================

class TestCreateSkillEmbedding:
    """Tests that create_skill generates embeddings."""
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_create_skill_generates_embedding(self, mock_update_embedding, mock_db, mock_subcategory, mock_skill):
        """Should generate embedding when creating a new skill."""
        # Arrange
        subcategory = mock_subcategory(subcategory_id=10)
        new_skill = mock_skill(skill_id=99, skill_name="Docker", subcategory_id=10)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            subcategory,  # Find parent subcategory
            None,         # Check for duplicate skill name
        ]
        mock_db.flush = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda s: setattr(s, 'skill_id', 99))
        
        # We need to capture the skill object that gets added
        added_skills = []
        def capture_add(obj):
            if hasattr(obj, 'skill_name'):
                obj.skill_id = 99
                obj.created_at = datetime.now()
                obj.created_by = 'system'
                added_skills.append(obj)
        mock_db.add.side_effect = capture_add
        
        # Act
        result = create_skill(
            db=mock_db,
            subcategory_id=10,
            skill_name="Docker",
            alias_text=None,
            actor="admin"
        )
        
        # Assert
        mock_update_embedding.assert_called_once()
        # Verify the skill passed to embedding update
        call_args = mock_update_embedding.call_args[0]
        assert call_args[0] == mock_db
        # The second arg is the skill object
        skill_arg = call_args[1]
        assert skill_arg.skill_name == "Docker"
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_create_skill_with_aliases_generates_embedding(self, mock_update_embedding, mock_db, mock_subcategory, mock_skill):
        """Should generate embedding including aliases when creating skill with aliases."""
        # Arrange
        subcategory = mock_subcategory(subcategory_id=10)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            subcategory,  # Find parent subcategory
            None,         # Check for duplicate skill name
            None,         # Check alias 1 doesn't exist
            None,         # Check alias 2 doesn't exist
        ]
        mock_db.flush = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Simulate skill_id assignment on flush
        flush_count = [0]
        def mock_flush():
            flush_count[0] += 1
        mock_db.flush.side_effect = mock_flush
        
        added_objects = []
        def capture_add(obj):
            if hasattr(obj, 'skill_name'):
                obj.skill_id = 99
                obj.created_at = datetime.now()
                obj.created_by = 'system'
            elif hasattr(obj, 'alias_text'):
                obj.alias_id = len(added_objects) + 1
            added_objects.append(obj)
        mock_db.add.side_effect = capture_add
        
        # Act
        result = create_skill(
            db=mock_db,
            subcategory_id=10,
            skill_name="Kubernetes",
            alias_text="K8s, K8",
            actor="admin"
        )
        
        # Assert
        mock_update_embedding.assert_called_once()
        assert result.name == "Kubernetes"
        assert len(result.aliases) == 2


# ============================================================================
# UPDATE SKILL NAME EMBEDDING TESTS
# ============================================================================

class TestUpdateSkillNameEmbedding:
    """Tests that update_skill_name regenerates embeddings."""
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_update_skill_name_regenerates_embedding(self, mock_update_embedding, mock_db, mock_skill):
        """Should regenerate embedding when skill name changes."""
        # Arrange
        skill = mock_skill(skill_id=1, skill_name="React", subcategory_id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            skill,   # Find skill
            None     # Check for duplicate name
        ]
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = update_skill_name(mock_db, 1, "React.js", actor="admin")
        
        # Assert
        mock_update_embedding.assert_called_once()
        call_args = mock_update_embedding.call_args[0]
        assert call_args[0] == mock_db
        assert call_args[1] == skill
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_no_embedding_update_when_name_unchanged(self, mock_update_embedding, mock_db, mock_skill):
        """Should NOT regenerate embedding when name is unchanged (case-insensitive)."""
        # Arrange
        skill = mock_skill(skill_id=1, skill_name="React", subcategory_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = skill
        
        # Act - same name, different case
        result = update_skill_name(mock_db, 1, "react", actor="admin")
        
        # Assert
        mock_update_embedding.assert_not_called()


# ============================================================================
# CREATE ALIAS EMBEDDING TESTS
# ============================================================================

class TestCreateAliasEmbedding:
    """Tests that create_alias regenerates embeddings."""
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_create_alias_regenerates_embedding(self, mock_update_embedding, mock_db, mock_skill):
        """Should regenerate embedding when alias is added."""
        # Arrange
        skill = mock_skill(skill_id=5, skill_name="Python")
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            skill,  # Find skill
            None    # Check alias doesn't exist
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda a: setattr(a, 'alias_id', 100))
        
        # Make add capture the alias and set alias_id
        def mock_add(obj):
            if hasattr(obj, 'alias_text'):
                obj.alias_id = 100
        mock_db.add.side_effect = mock_add
        
        # Act
        result = create_alias(mock_db, skill_id=5, alias_text="Py")
        
        # Assert
        mock_update_embedding.assert_called_once()
        call_args = mock_update_embedding.call_args[0]
        assert call_args[0] == mock_db
        assert call_args[1] == skill


# ============================================================================
# UPDATE ALIAS EMBEDDING TESTS
# ============================================================================

class TestUpdateAliasEmbedding:
    """Tests that update_alias regenerates embeddings only when alias_text changes."""
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_update_alias_text_regenerates_embedding(self, mock_update_embedding, mock_db, mock_alias, mock_skill):
        """Should regenerate embedding when alias_text changes."""
        # Arrange
        alias = mock_alias(alias_id=1, alias_text="ReactJS", skill_id=5)
        skill = mock_skill(skill_id=5, skill_name="React")
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            alias,  # Find alias
            None,   # Check for duplicate alias text
            skill   # Find skill for embedding update
        ]
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = update_alias(mock_db, 1, alias_text="React JS Updated")
        
        # Assert
        mock_update_embedding.assert_called_once()
        call_args = mock_update_embedding.call_args[0]
        assert call_args[0] == mock_db
        assert call_args[1] == skill
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_update_alias_source_does_not_regenerate_embedding(self, mock_update_embedding, mock_db, mock_alias):
        """Should NOT regenerate embedding when only source changes."""
        # Arrange
        alias = mock_alias(alias_id=1, alias_text="ReactJS", skill_id=5, source="manual")
        mock_db.query.return_value.filter.return_value.first.return_value = alias
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = update_alias(mock_db, 1, source="import")
        
        # Assert
        mock_update_embedding.assert_not_called()
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_update_alias_confidence_does_not_regenerate_embedding(self, mock_update_embedding, mock_db, mock_alias):
        """Should NOT regenerate embedding when only confidence_score changes."""
        # Arrange
        alias = mock_alias(alias_id=1, alias_text="ReactJS", skill_id=5, confidence_score=0.5)
        mock_db.query.return_value.filter.return_value.first.return_value = alias
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = update_alias(mock_db, 1, confidence_score=0.9)
        
        # Assert
        mock_update_embedding.assert_not_called()
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_no_embedding_update_when_alias_text_unchanged(self, mock_update_embedding, mock_db, mock_alias):
        """Should NOT regenerate embedding when alias_text is unchanged (case-insensitive)."""
        # Arrange
        alias = mock_alias(alias_id=1, alias_text="ReactJS", skill_id=5)
        mock_db.query.return_value.filter.return_value.first.return_value = alias
        
        # Act - same text, different case
        result = update_alias(mock_db, 1, alias_text="reactjs")
        
        # Assert - no commit means no changes
        mock_update_embedding.assert_not_called()


# ============================================================================
# DELETE ALIAS EMBEDDING TESTS
# ============================================================================

class TestDeleteAliasEmbedding:
    """Tests that delete_alias regenerates embeddings."""
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_delete_alias_regenerates_embedding(self, mock_update_embedding, mock_db, mock_alias, mock_skill):
        """Should regenerate embedding when alias is deleted."""
        # Arrange
        alias = mock_alias(alias_id=1, alias_text="ReactJS", skill_id=5)
        skill = mock_skill(skill_id=5, skill_name="React")
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            alias,  # Find alias
            skill   # Find skill for embedding update
        ]
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        # Act
        result = delete_alias(mock_db, 1)
        
        # Assert
        mock_update_embedding.assert_called_once()
        call_args = mock_update_embedding.call_args[0]
        assert call_args[0] == mock_db
        assert call_args[1] == skill


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestEmbeddingErrorHandling:
    """Tests that embedding errors are properly raised."""
    
    @patch('app.services.master_data.taxonomy_update_service._update_skill_embedding')
    def test_create_skill_propagates_embedding_error(self, mock_update_embedding, mock_db, mock_subcategory):
        """Should propagate EmbeddingError when embedding fails during skill creation."""
        # Arrange
        subcategory = mock_subcategory(subcategory_id=10)
        mock_update_embedding.side_effect = EmbeddingError("API unavailable")
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            subcategory,  # Find parent subcategory
            None,         # Check for duplicate skill name
        ]
        mock_db.flush = Mock()
        mock_db.add = Mock(side_effect=lambda obj: setattr(obj, 'skill_id', 99) if hasattr(obj, 'skill_name') else None)
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda s: [setattr(s, 'created_at', datetime.now()), setattr(s, 'created_by', 'admin')])
        
        # Act & Assert
        with pytest.raises(EmbeddingError) as exc_info:
            create_skill(
                db=mock_db,
                subcategory_id=10,
                skill_name="Docker",
                actor="admin"
            )
        
        assert "API unavailable" in str(exc_info.value.message)
