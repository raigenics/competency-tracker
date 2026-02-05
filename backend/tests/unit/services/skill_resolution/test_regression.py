"""
Regression tests for skill resolution.

Ensures that existing exact and alias matching behavior is NOT broken
by the addition of embedding-based matching.
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.skill_resolution.skill_resolver_service import SkillResolverService
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias


class TestSkillResolutionRegression:
    """
    Regression tests to verify existing functionality is preserved.
    
    These tests ensure that:
    1. Exact matching works exactly as before
    2. Alias matching works exactly as before
    3. Resolution order is preserved (exact -> alias -> embedding)
    4. Confidence scores for exact/alias remain unchanged
    """
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def resolver(self, mock_db):
        """Create resolver without embedding (legacy mode)."""
        return SkillResolverService(db=mock_db, enable_embedding=False)
    
    # ===== Regression: Exact Match =====
    
    def test_exact_match_unchanged_behavior(self, resolver, mock_db):
        """
        REGRESSION: Exact match should work exactly as in original implementation.
        
        Original behavior:
        - Case-insensitive match on skill_name
        - Returns skill_id
        - Confidence = 1.0
        """
        # Arrange
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 42
        mock_skill.skill_name = "Python"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        # Act
        result = resolver.resolve("python")
        
        # Assert - verify exact same behavior as before
        assert result.resolved_skill_id == 42
        assert result.resolution_method == "exact"
        assert result.resolution_confidence == 1.0
        assert result.is_resolved() is True
    
    def test_exact_match_multiple_variations(self, resolver, mock_db):
        """
        REGRESSION: Test exact match with various text variations.
        
        All these should resolve to the same skill as before.
        """
        test_cases = [
            ("Python", 100, "Python"),
            ("JavaScript", 200, "JavaScript"),
            ("SQL", 300, "SQL"),
            ("Machine Learning", 400, "Machine Learning"),
        ]
        
        for normalized_text, expected_id, skill_name in test_cases:
            # Arrange
            mock_skill = Mock(spec=Skill)
            mock_skill.skill_id = expected_id
            mock_skill.skill_name = skill_name
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_skill
            mock_db.query.return_value = mock_query
            
            # Act
            result = resolver.resolve(normalized_text.lower())
            
            # Assert
            assert result.resolved_skill_id == expected_id
            assert result.resolution_method == "exact"
            assert result.resolution_confidence == 1.0
    
    # ===== Regression: Alias Match =====
    
    def test_alias_match_unchanged_behavior(self, resolver, mock_db):
        """
        REGRESSION: Alias match should work exactly as in original implementation.
        
        Original behavior:
        - Falls back to alias when exact fails
        - Case-insensitive match on alias_text
        - Returns skill_id from alias
        - Confidence = 1.0
        """
        # Arrange
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 99
        mock_alias.alias_text = "js"
        
        def query_side_effect(model):
            mock_query = Mock()
            if model == Skill:
                # No exact match
                mock_query.filter.return_value.first.return_value = None
            elif model == SkillAlias:
                # Alias match found
                mock_query.filter.return_value.first.return_value = mock_alias
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = resolver.resolve("js")
        
        # Assert - verify exact same behavior as before
        assert result.resolved_skill_id == 99
        assert result.resolution_method == "alias"
        assert result.resolution_confidence == 1.0
        assert result.is_resolved() is True
    
    def test_alias_match_multiple_variations(self, resolver, mock_db):
        """
        REGRESSION: Test alias match with various common aliases.
        """
        test_cases = [
            ("js", 200, "JavaScript"),
            ("ts", 250, "TypeScript"),
            ("ml", 400, "Machine Learning"),
            ("ai", 450, "Artificial Intelligence"),
        ]
        
        for alias_text, expected_id, _ in test_cases:
            # Arrange
            mock_alias = Mock(spec=SkillAlias)
            mock_alias.skill_id = expected_id
            mock_alias.alias_text = alias_text
            
            def query_side_effect(model):
                mock_query = Mock()
                if model == Skill:
                    mock_query.filter.return_value.first.return_value = None
                elif model == SkillAlias:
                    mock_query.filter.return_value.first.return_value = mock_alias
                return mock_query
            
            mock_db.query.side_effect = query_side_effect
            
            # Act
            result = resolver.resolve(alias_text)
            
            # Assert
            assert result.resolved_skill_id == expected_id
            assert result.resolution_method == "alias"
            assert result.resolution_confidence == 1.0
    
    # ===== Regression: Resolution Order =====
    
    def test_exact_takes_precedence_over_alias(self, resolver, mock_db):
        """
        REGRESSION: Exact match should take precedence over alias match.
        
        If a text matches both exact skill name AND an alias,
        exact match should win.
        """
        # Arrange
        text = "python"
        
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 111
        mock_skill.skill_name = "Python"
        
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 999  # Different skill
        mock_alias.alias_text = "python"
        
        def query_side_effect(model):
            mock_query = Mock()
            if model == Skill:
                # Exact match found
                mock_query.filter.return_value.first.return_value = mock_skill
            elif model == SkillAlias:
                # Alias also exists (but should not be used)
                mock_query.filter.return_value.first.return_value = mock_alias
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = resolver.resolve(text)
        
        # Assert - should use exact match, not alias
        assert result.resolved_skill_id == 111  # NOT 999
        assert result.resolution_method == "exact"
        
        # Verify alias query was NOT called (early exit after exact match)
        # Only one query should have been made (for Skill)
        assert mock_db.query.call_count == 1
        mock_db.query.assert_called_with(Skill)
    
    # ===== Regression: Unresolved Behavior =====
    
    def test_unresolved_unchanged_behavior(self, resolver, mock_db):
        """
        REGRESSION: Unresolved skills should behave exactly as before.
        
        Original behavior:
        - When no exact or alias match, return None
        - Method = "unresolved"
        - Confidence = None
        """
        # Arrange
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Act
        result = resolver.resolve("unknown skill")
        
        # Assert - verify exact same behavior as before
        assert result.resolved_skill_id is None
        assert result.resolution_method == "unresolved"
        assert result.resolution_confidence is None
        assert result.is_resolved() is False
    
    # ===== Regression: Database Writes =====
    
    def test_no_database_writes_during_resolution(self, resolver, mock_db):
        """
        REGRESSION: Resolution should NOT write to database.
        
        Original implementation only reads from DB.
        New implementation should preserve this.
        """
        # Arrange
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 42
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        # Act
        resolver.resolve("python")
        
        # Assert - verify no write operations
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.flush.assert_not_called()
        mock_db.delete.assert_not_called()
    
    # ===== Regression: Output Format =====
    
    def test_resolution_result_format_unchanged(self, resolver, mock_db):
        """
        REGRESSION: ResolutionResult should have same structure as before.
        
        Original fields:
        - resolved_skill_id
        - resolution_method
        - resolution_confidence
        """
        # Arrange
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 123
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        # Act
        result = resolver.resolve("test")
        
        # Assert - verify result has expected fields
        assert hasattr(result, 'resolved_skill_id')
        assert hasattr(result, 'resolution_method')
        assert hasattr(result, 'resolution_confidence')
        assert hasattr(result, 'is_resolved')
        
        # Verify field types
        assert isinstance(result.resolved_skill_id, (int, type(None)))
        assert isinstance(result.resolution_method, str)
        assert isinstance(result.resolution_confidence, (float, type(None)))
