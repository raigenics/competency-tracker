"""
Unit tests for unresolved_skills_service.

Tests cover:
- get_unresolved_skills returns unresolved rows when include_suggestions=false
- get_unresolved_skills returns 200 even if suggestions fail (no 500 error)
- _get_embedding_suggestions rollback prevents cascading transaction errors
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.exc import OperationalError

from app.services.imports.unresolved_skills_service import (
    get_unresolved_skills,
    _get_suggestions,
    _get_embedding_suggestions,
    ImportJobNotFoundError
)
from app.models.import_job import ImportJob
from app.models.raw_skill_input import RawSkillInput
from app.models.employee import Employee


class TestGetUnresolvedSkillsWithoutSuggestions:
    """Test include_suggestions=false returns 200 with unresolved rows."""
    
    def test_returns_unresolved_skills_without_suggestions(self):
        """Should return unresolved skills with empty suggestions when include_suggestions=false."""
        # Arrange
        mock_db = MagicMock()
        
        # Mock ImportJob exists
        mock_job = MagicMock(spec=ImportJob)
        mock_job.job_id = "test-job-123"
        
        # Mock RawSkillInput records
        mock_raw_skill1 = MagicMock(spec=RawSkillInput)
        mock_raw_skill1.raw_skill_id = 1
        mock_raw_skill1.raw_text = "Python"
        mock_raw_skill1.normalized_text = "python"
        mock_raw_skill1.employee_id = None
        
        mock_raw_skill2 = MagicMock(spec=RawSkillInput)
        mock_raw_skill2.raw_skill_id = 2
        mock_raw_skill2.raw_text = "JavaScript"
        mock_raw_skill2.normalized_text = "javascript"
        mock_raw_skill2.employee_id = None
        
        # Set up query responses
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_raw_skill1, mock_raw_skill2
        ]
        
        # Act
        result = get_unresolved_skills(
            db=mock_db,
            import_run_id="test-job-123",
            include_suggestions=False,
            max_suggestions=5
        )
        
        # Assert
        assert result.import_run_id == "test-job-123"
        assert result.total_count == 2
        assert len(result.unresolved_skills) == 2
        assert result.unresolved_skills[0].raw_text == "Python"
        assert result.unresolved_skills[0].suggestions == []
        assert result.unresolved_skills[1].raw_text == "JavaScript"
        assert result.unresolved_skills[1].suggestions == []
    
    def test_does_not_call_suggestions_when_disabled(self):
        """Should not call _get_suggestions when include_suggestions=false."""
        # Arrange
        mock_db = MagicMock()
        mock_job = MagicMock()
        mock_raw_skill = MagicMock()
        mock_raw_skill.raw_skill_id = 1
        mock_raw_skill.raw_text = "Test"
        mock_raw_skill.normalized_text = "test"
        mock_raw_skill.employee_id = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_raw_skill]
        
        with patch('app.services.imports.unresolved_skills_service._get_suggestions') as mock_get_suggestions:
            # Act
            get_unresolved_skills(
                db=mock_db,
                import_run_id="test-job",
                include_suggestions=False,
                max_suggestions=5
            )
            
            # Assert
            mock_get_suggestions.assert_not_called()


class TestGetUnresolvedSkillsSuggestionFailure:
    """Test include_suggestions=true returns 200 even if suggestions fail."""
    
    def test_returns_empty_suggestions_when_suggestion_fails(self):
        """Should return 200 with empty suggestions when _get_suggestions raises exception."""
        # Arrange
        mock_db = MagicMock()
        mock_job = MagicMock()
        mock_raw_skill = MagicMock()
        mock_raw_skill.raw_skill_id = 1
        mock_raw_skill.raw_text = "Test Skill"
        mock_raw_skill.normalized_text = "test skill"
        mock_raw_skill.employee_id = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_raw_skill]
        
        with patch('app.services.imports.unresolved_skills_service._get_suggestions') as mock_get_suggestions:
            mock_get_suggestions.side_effect = Exception("Database error")
            
            # Act - should not raise exception
            result = get_unresolved_skills(
                db=mock_db,
                import_run_id="test-job",
                include_suggestions=True,
                max_suggestions=5
            )
            
            # Assert - still returns 200 with empty suggestions
            assert result.total_count == 1
            assert result.unresolved_skills[0].suggestions == []
    
    def test_returns_partial_suggestions_when_embedding_fails(self):
        """Should return exact/alias matches even if embedding search fails."""
        # Arrange
        mock_db = MagicMock()
        
        # Mock no exact/alias matches, embedding fails
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = []
        
        with patch('app.services.imports.unresolved_skills_service._get_embedding_suggestions') as mock_embed:
            mock_embed.side_effect = Exception("Embedding service error")
            
            # Act - should not raise
            suggestions = _get_suggestions(mock_db, "test skill", max_suggestions=5)
            
            # Assert - returns empty list, no exception propagated  
            assert suggestions == []


class TestEmbeddingSuggestionsRollback:
    """Test _get_embedding_suggestions rollback prevents cascading transaction errors."""
    
    def test_rollback_on_embedding_query_failure(self):
        """Should rollback transaction when embedding query fails."""
        # Arrange
        mock_db = MagicMock()
        
        # Mock embedding provider to work
        mock_provider = MagicMock()
        mock_provider.embed.return_value = [0.1, 0.2, 0.3]  # dummy embedding
        
        # Mock execute to fail with table not found
        mock_db.execute.side_effect = OperationalError("", "", "relation does not exist")
        
        with patch('app.services.skill_resolution.embedding_provider.create_embedding_provider', 
                   return_value=mock_provider):
            # Act
            suggestions = _get_embedding_suggestions(mock_db, "test", max_results=5)
            
            # Assert - rollback was called to clear failed transaction
            mock_db.rollback.assert_called_once()
            # Returns empty list, no exception raised
            assert suggestions == []
    
    def test_returns_empty_when_embedding_not_available(self):
        """Should return empty list when embedding provider not configured."""
        # Arrange
        mock_db = MagicMock()
        
        with patch('app.services.skill_resolution.embedding_provider.create_embedding_provider', 
                   side_effect=Exception("Embedding service not configured")):
            # Act
            suggestions = _get_embedding_suggestions(mock_db, "test", max_results=5)
            
            # Assert - returns empty list gracefully
            assert suggestions == []


class TestGetUnresolvedSkillsJobNotFound:
    """Test ImportJobNotFoundError is raised for missing jobs."""
    
    def test_raises_error_for_missing_job(self):
        """Should raise ImportJobNotFoundError when job doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ImportJobNotFoundError) as exc_info:
            get_unresolved_skills(
                db=mock_db,
                import_run_id="nonexistent-job",
                include_suggestions=False,
                max_suggestions=5
            )
        
        assert "nonexistent-job" in str(exc_info.value)


# ============================================================================
# TEST: get_single_skill_suggestions (new endpoint)
# ============================================================================

from app.services.imports.unresolved_skills_service import (
    get_single_skill_suggestions,
    RawSkillNotFoundError
)


class TestGetSingleSkillSuggestions:
    """Test get_single_skill_suggestions fetches suggestions for ONE skill only."""
    
    def test_returns_suggestions_for_single_skill(self):
        """Should return suggestions for the specific raw_skill_id."""
        # Arrange
        mock_db = MagicMock()
        
        # Mock ImportJob exists
        mock_job = MagicMock()
        mock_job.job_id = "job-123"
        
        # Mock RawSkillInput record
        mock_raw_skill = MagicMock()
        mock_raw_skill.raw_skill_id = 42
        mock_raw_skill.raw_text = "Python Dev"
        mock_raw_skill.normalized_text = "python dev"
        mock_raw_skill.employee_id = None
        
        # Mock query chain
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,      # First call: ImportJob query
            mock_raw_skill # Second call: RawSkillInput query
        ]
        
        with patch('app.services.imports.unresolved_skills_service._get_suggestions') as mock_suggestions:
            mock_suggestions.return_value = []
            
            # Act
            result = get_single_skill_suggestions(
                db=mock_db,
                import_run_id="job-123",
                raw_skill_id=42,
                max_suggestions=10,
                include_embeddings=True
            )
        
        # Assert
        assert result.raw_skill_id == 42
        assert result.raw_text == "Python Dev"
        assert result.normalized_text == "python dev"
        mock_suggestions.assert_called_once_with(
            mock_db, "python dev", 10, include_embeddings=True
        )
    
    def test_raises_not_found_for_missing_job(self):
        """Should raise ImportJobNotFoundError if job doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ImportJobNotFoundError):
            get_single_skill_suggestions(
                db=mock_db,
                import_run_id="bad-job",
                raw_skill_id=1
            )
    
    def test_raises_not_found_for_missing_raw_skill(self):
        """Should raise RawSkillNotFoundError if raw_skill_id doesn't exist."""
        # Arrange
        mock_db = MagicMock()
        mock_job = MagicMock()
        
        # First query returns job, second returns None (no raw_skill)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job,  # Job exists
            None       # Raw skill not found
        ]
        
        # Act & Assert
        with pytest.raises(RawSkillNotFoundError):
            get_single_skill_suggestions(
                db=mock_db,
                import_run_id="job-123",
                raw_skill_id=999
            )
    
    def test_only_calls_suggestions_once(self):
        """Should call _get_suggestions exactly once (not for all skills)."""
        # Arrange
        mock_db = MagicMock()
        mock_job = MagicMock()
        mock_raw_skill = MagicMock()
        mock_raw_skill.raw_skill_id = 1
        mock_raw_skill.raw_text = "Test"
        mock_raw_skill.normalized_text = "test"
        mock_raw_skill.employee_id = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job, mock_raw_skill
        ]
        
        with patch('app.services.imports.unresolved_skills_service._get_suggestions') as mock_suggestions:
            mock_suggestions.return_value = []
            
            # Act
            get_single_skill_suggestions(
                db=mock_db,
                import_run_id="job-123",
                raw_skill_id=1
            )
        
        # Assert - called exactly once, not multiple times
        assert mock_suggestions.call_count == 1
    
    def test_passes_include_embeddings_false(self):
        """Should pass include_embeddings=false to skip embedding lookups."""
        # Arrange
        mock_db = MagicMock()
        mock_job = MagicMock()
        mock_raw_skill = MagicMock()
        mock_raw_skill.raw_skill_id = 1
        mock_raw_skill.raw_text = "Test"
        mock_raw_skill.normalized_text = "test"
        mock_raw_skill.employee_id = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_job, mock_raw_skill
        ]
        
        with patch('app.services.imports.unresolved_skills_service._get_suggestions') as mock_suggestions:
            mock_suggestions.return_value = []
            
            # Act
            get_single_skill_suggestions(
                db=mock_db,
                import_run_id="job-123",
                raw_skill_id=1,
                include_embeddings=False
            )
        
        # Assert
        _, kwargs = mock_suggestions.call_args
        assert kwargs.get('include_embeddings') is False