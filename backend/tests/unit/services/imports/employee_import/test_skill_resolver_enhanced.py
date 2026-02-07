"""
Unit tests for SkillResolver with embedding-based resolution.

Tests resolution precedence and threshold logic.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.imports.employee_import.skill_resolver import SkillResolver


class TestSkillResolverPrecedence:
    """Test resolution precedence: token validation → exact → alias → embedding."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
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
        # Mock query to never be called
        self.mock_db.query = Mock(side_effect=Exception("Should not query for invalid tokens"))
        
        # Test garbage tokens
        skill_id, method, confidence = self.resolver.resolve_skill(")")
        assert skill_id is None
        assert method is None
        assert confidence is None
        assert self.stats['skills_unresolved'] == 1
    
    def test_exact_match_takes_precedence(self):
        """Test that exact match is tried before alias."""
        # Mock exact match found
        mock_skill = Mock()
        mock_skill.skill_id = 42
        mock_skill.skill_name = "Python"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        self.mock_db.query.return_value = mock_query
        
        skill_id, method, confidence = self.resolver.resolve_skill("Python")
        
        assert skill_id == 42
        assert method == "exact"
        assert confidence is None
        assert self.stats['skills_resolved_exact'] == 1
    
    def test_alias_match_after_exact_fails(self):
        """Test that alias match is tried after exact match fails."""
        # Mock: exact match fails, alias match succeeds
        mock_alias = Mock()
        mock_alias.skill_id = 99
        
        call_count = [0]
        def mock_query_side_effect(*args):
            call_count[0] += 1
            mock_q = Mock()
            if call_count[0] == 1:
                # First call: exact match (returns None)
                mock_q.filter.return_value.first.return_value = None
            else:
                # Second call: alias match (returns alias)
                mock_q.filter.return_value.first.return_value = mock_alias
            return mock_q
        
        self.mock_db.query.side_effect = mock_query_side_effect
        
        skill_id, method, confidence = self.resolver.resolve_skill("py")
        
        assert skill_id == 99
        assert method == "alias"
        assert confidence is None
        assert self.stats['skills_resolved_alias'] == 1


class TestSkillResolverEmbeddingThresholds:
    """Test embedding similarity thresholds."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
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
        # Mock: no exact/alias match
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # Mock embedding match with high confidence
        with patch.object(self.resolver, '_try_embedding_match', return_value=(123, 0.92)):
            skill_id, method, confidence = self.resolver.resolve_skill("Python Programming")
            
            assert skill_id == 123
            assert method == "embedding"
            assert confidence == 0.92
            assert self.stats['skills_resolved_embedding'] == 1
    
    def test_needs_review_medium_confidence(self):
        """Test needs_review for 0.80 ≤ similarity < 0.88."""
        # Mock: no exact/alias match
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # Mock embedding match with medium confidence
        with patch.object(self.resolver, '_try_embedding_match', return_value=(456, 0.83)):
            skill_id, method, confidence = self.resolver.resolve_skill("ML Programming")
            
            assert skill_id is None  # NOT auto-accepted
            assert method == "needs_review"
            assert confidence == 0.83
            assert self.stats['skills_needs_review'] == 1
    
    def test_reject_low_confidence(self):
        """Test rejection for similarity < 0.80."""
        # Mock: no exact/alias match
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # Mock embedding match with low confidence (should be filtered by repository)
        with patch.object(self.resolver, '_try_embedding_match', return_value=(None, None)):
            skill_id, method, confidence = self.resolver.resolve_skill("Unknown Skill")
            
            assert skill_id is None
            assert method is None
            assert confidence is None
            assert self.stats['skills_unresolved'] == 1
    
    def test_threshold_boundary_0_88(self):
        """Test exact boundary at 0.88 (auto-accept threshold)."""
        # Mock: no exact/alias match
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
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
        # Mock: no exact/alias match
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
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
        self.mock_db = Mock()
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
        # Mock: no exact/alias match
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
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
        self.mock_db = Mock()
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
        # Mock: exact match
        mock_skill = Mock()
        mock_skill.skill_id = 1
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        self.mock_db.query.return_value = mock_query
        
        self.resolver.resolve_skill("Exact Match")
        assert self.stats['skills_resolved_exact'] == 1
        
        # Mock: alias match
        self.stats = {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_resolved_embedding': 0,
            'skills_needs_review': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
        self.resolver.stats = self.stats
        
        mock_alias = Mock()
        mock_alias.skill_id = 2
        
        call_count = [0]
        def mock_query_side_effect(*args):
            call_count[0] += 1
            mock_q = Mock()
            if call_count[0] == 1:
                mock_q.filter.return_value.first.return_value = None
            else:
                mock_q.filter.return_value.first.return_value = mock_alias
            return mock_q
        
        self.mock_db.query.side_effect = mock_query_side_effect
        self.resolver.resolve_skill("Alias Match")
        assert self.stats['skills_resolved_alias'] == 1
    
    def test_unresolved_names_tracked(self):
        """Test that unresolved skill names are tracked."""
        # Mock: no match
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with patch.object(self.resolver, '_try_embedding_match', return_value=(None, None)):
            self.resolver.resolve_skill("Unknown 1")
            self.resolver.resolve_skill("Unknown 2")
            self.resolver.resolve_skill("Unknown 1")  # Duplicate
            
            assert self.stats['skills_unresolved'] == 3
            assert len(self.stats['unresolved_skill_names']) == 2  # No duplicates in list
            assert "Unknown 1" in self.stats['unresolved_skill_names']
            assert "Unknown 2" in self.stats['unresolved_skill_names']
