"""
Unit tests for SkillResolver with embedding-based resolution.

Tests resolution precedence and threshold logic.
"""
import pytest
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch
from app.services.imports.employee_import.skill_resolver import SkillResolver


def create_mock_db(skills=None, aliases=None):
    """Create a mock DB with proper query().all() behavior for lookup cache."""
    mock_db = Mock()
    skills = skills or []
    aliases = aliases or []
    
    def query_side_effect(model):
        mock_query = Mock()
        model_name = model.__name__ if hasattr(model, '__name__') else str(model)
        if model_name == 'Skill':
            mock_query.all.return_value = skills
        elif model_name == 'SkillAlias':
            mock_query.all.return_value = aliases
        else:
            mock_query.all.return_value = []
        # Support filter().first() chains (not used by current code but kept for safety)
        mock_query.filter.return_value.first.return_value = None
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    return mock_db


class TestSkillResolverPrecedence:
    """Test resolution precedence: token validation → exact → alias → embedding."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = create_mock_db()
        self.stats = {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_resolved_embedding': 0,
            'skills_needs_review': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
    
    def test_reject_invalid_token(self):
        """Test that invalid tokens are rejected before resolution."""
        # Invalid tokens are rejected before cache build, so no queries made
        skill_id, method, confidence = self.resolver.resolve_skill(")")
        assert skill_id is None
        assert method is None
        assert confidence is None
        assert self.stats['skills_unresolved'] == 1
    
    def test_exact_match_takes_precedence(self):
        """Test that exact match is tried before alias."""
        # Create mock skill in lookup cache
        mock_skill = SimpleNamespace(skill_id=42, skill_name="Python")
        self.mock_db = create_mock_db(skills=[mock_skill])
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
        
        skill_id, method, confidence = self.resolver.resolve_skill("Python")
        
        assert skill_id == 42
        assert method == "exact"
        assert confidence is None
        assert self.stats['skills_resolved_exact'] == 1
    
    def test_alias_match_after_exact_fails(self):
        """Test that alias match is tried after exact match fails."""
        # Create mock alias in lookup cache (no matching skill for "py")
        mock_alias = SimpleNamespace(alias_text="py", skill_id=99)
        self.mock_db = create_mock_db(skills=[], aliases=[mock_alias])
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
        
        skill_id, method, confidence = self.resolver.resolve_skill("py")
        
        assert skill_id == 99
        assert method == "alias"
        assert confidence is None
        assert self.stats['skills_resolved_alias'] == 1


class TestSkillResolverEmbeddingThresholds:
    """Test embedding similarity thresholds."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = create_mock_db()
        self.stats = {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_resolved_embedding': 0,
            'skills_needs_review': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
        
        # Enable embedding (mock provider)
        self.resolver.embedding_enabled = True
        self.resolver.embedding_provider = Mock()
    
    def test_auto_accept_high_confidence(self):
        """Test auto-accept for similarity ≥ 0.88."""
        # No exact/alias match (empty lookup cache)
        
        # Mock embedding match with high confidence
        with patch.object(self.resolver, '_try_embedding_match', return_value=(123, 0.92)):
            skill_id, method, confidence = self.resolver.resolve_skill("Python Programming")
            
            assert skill_id == 123
            assert method == "embedding"
            assert confidence == 0.92
            assert self.stats['skills_resolved_embedding'] == 1
    
    def test_needs_review_medium_confidence(self):
        """Test needs_review for 0.80 ≤ similarity < 0.88."""
        # No exact/alias match (empty lookup cache)
        
        # Mock embedding match with medium confidence
        with patch.object(self.resolver, '_try_embedding_match', return_value=(456, 0.83)):
            skill_id, method, confidence = self.resolver.resolve_skill("ML Programming")
            
            assert skill_id is None  # NOT auto-accepted
            assert method == "needs_review"
            assert confidence == 0.83
            assert self.stats['skills_needs_review'] == 1
    
    def test_reject_low_confidence(self):
        """Test rejection for similarity < 0.80."""
        # No exact/alias match (empty lookup cache)
        
        # Mock embedding match with low confidence (should be filtered by repository)
        with patch.object(self.resolver, '_try_embedding_match', return_value=(None, None)):
            skill_id, method, confidence = self.resolver.resolve_skill("Unknown Skill")
            
            assert skill_id is None
            assert method is None
            assert confidence is None
            assert self.stats['skills_unresolved'] == 1
    
    def test_threshold_boundary_0_88(self):
        """Test exact boundary at 0.88 (auto-accept threshold)."""
        # No exact/alias match (empty lookup cache)
        
        # Test exactly 0.88 - should auto-accept
        with patch.object(self.resolver, '_try_embedding_match', return_value=(100, 0.88)):
            skill_id, method, confidence = self.resolver.resolve_skill("Test Skill")
            assert skill_id == 100
            assert method == "embedding"
            assert self.stats['skills_resolved_embedding'] == 1
        
        # Reset stats
        self.stats['skills_resolved_embedding'] = 0
        self.stats['skills_needs_review'] = 0
        
        # Test 0.8799 - should need review
        with patch.object(self.resolver, '_try_embedding_match', return_value=(101, 0.8799)):
            skill_id, method, confidence = self.resolver.resolve_skill("Test Skill 2")
            assert skill_id is None  # Not auto-accepted
            assert method == "needs_review"
            assert self.stats['skills_needs_review'] == 1
    
    def test_threshold_boundary_0_80(self):
        """Test exact boundary at 0.80 (review threshold)."""
        # No exact/alias match (empty lookup cache)
        
        # Test exactly 0.80 - should need review
        with patch.object(self.resolver, '_try_embedding_match', return_value=(200, 0.80)):
            skill_id, method, confidence = self.resolver.resolve_skill("Boundary Test")
            assert skill_id is None  # Not auto-accepted
            assert method == "needs_review"
            assert self.stats['skills_needs_review'] == 1


class TestSkillResolverEmbeddingDisabled:
    """Test behavior when embedding is disabled."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = create_mock_db()
        self.stats = {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
        
        # Ensure embedding is disabled
        self.resolver.embedding_enabled = False
        self.resolver.embedding_provider = None
    
    def test_fallback_to_unresolved_when_embedding_disabled(self):
        """Test that skills are unresolved when embedding is disabled and no exact/alias match."""
        # No exact/alias match (empty lookup cache)
        
        skill_id, method, confidence = self.resolver.resolve_skill("Unknown Skill")
        
        assert skill_id is None
        assert method is None
        assert confidence is None
        assert self.stats['skills_unresolved'] == 1
        assert "Unknown Skill" in self.stats['unresolved_skill_names']


class TestSkillResolverStatsTracking:
    """Test that stats are tracked correctly."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = create_mock_db()
        self.stats = {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_resolved_embedding': 0,
            'skills_needs_review': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
        self.resolver.embedding_enabled = True
        self.resolver.embedding_provider = Mock()
    
    def test_stats_increment_correctly(self):
        """Test that stats increment for each resolution method."""
        # Set up mock with "Exact Match" skill
        mock_skill = SimpleNamespace(skill_id=1, skill_name="Exact Match")
        self.mock_db = create_mock_db(skills=[mock_skill])
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
        
        self.resolver.resolve_skill("Exact Match")
        assert self.stats['skills_resolved_exact'] == 1
        
        # Test alias match with a new resolver
        self.stats = {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_resolved_embedding': 0,
            'skills_needs_review': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
        mock_alias = SimpleNamespace(alias_text="Alias Match", skill_id=2)
        self.mock_db = create_mock_db(skills=[], aliases=[mock_alias])
        self.resolver = SkillResolver(self.mock_db, self.stats)
        self.resolver.set_name_normalizer(lambda x: x.lower().strip())
        
        self.resolver.resolve_skill("Alias Match")
        assert self.stats['skills_resolved_alias'] == 1
    
    def test_unresolved_names_tracked(self):
        """Test that unresolved skill names are tracked."""
        # Empty lookup cache (no exact/alias match possible)
        
        with patch.object(self.resolver, '_try_embedding_match', return_value=(None, None)):
            self.resolver.resolve_skill("Unknown 1")
            self.resolver.resolve_skill("Unknown 2")
            self.resolver.resolve_skill("Unknown 1")  # Duplicate
            
            assert self.stats['skills_unresolved'] == 3
            assert len(self.stats['unresolved_skill_names']) == 2  # No duplicates in list
            assert "Unknown 1" in self.stats['unresolved_skill_names']
            assert "Unknown 2" in self.stats['unresolved_skill_names']
