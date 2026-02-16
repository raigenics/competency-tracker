"""
Unit tests for SkillResolver.

Target: backend/app/services/imports/employee_import/skill_resolver.py
Coverage: Skill resolution logic (exact match → alias match → unresolved).

Test Strategy:
- Mock SQLAlchemy Session and query behavior
- Test resolution priority: exact > alias > None
- Verify stats tracking for each resolution path
- Test name normalization integration
- No actual database access (pure unit tests)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.imports.employee_import.skill_resolver import SkillResolver
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias


class TestSkillResolverInit:
    """Test SkillResolver initialization."""
    
    def test_initializes_with_db_and_stats(self):
        """Should initialize with database session and stats dict."""
        db = Mock()
        stats = {'skills_resolved_exact': 0}
        
        resolver = SkillResolver(db, stats)
        
        assert resolver.db is db
        assert resolver.stats is stats
        assert resolver.normalize_name is None
    
    def test_sets_name_normalizer(self):
        """Should allow injecting name normalizer function."""
        db = Mock()
        stats = {}
        normalizer_func = lambda x: x.lower().strip()
        
        resolver = SkillResolver(db, stats)
        resolver.set_name_normalizer(normalizer_func)
        
        assert resolver.normalize_name is normalizer_func


class TestResolveSkillExactMatch:
    """Test exact match resolution path."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def stats(self):
        """Create stats dict for tracking."""
        return {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
    
    @pytest.fixture
    def resolver(self, mock_db, stats):
        """Create SkillResolver instance."""
        resolver = SkillResolver(mock_db, stats)
        # Use default normalization (lower + strip)
        return resolver
    
    def test_resolves_exact_match_case_insensitive(self, resolver, mock_db, stats):
        """Should resolve skill via exact match (case-insensitive)."""
        # Setup mock skill
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 42
        mock_skill.skill_name = "python"
        
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        # Execute
        result = resolver.resolve_skill("Python")
        
        # Verify - returns (skill_id, resolution_method, confidence)
        assert result == (42, "exact", None)
        assert stats['skills_resolved_exact'] == 1
        assert stats['skills_resolved_alias'] == 0
        assert stats['skills_unresolved'] == 0
        mock_db.query.assert_called_once_with(Skill)
    
    def test_resolves_exact_match_with_whitespace(self, resolver, mock_db, stats):
        """Should resolve exact match after trimming whitespace."""
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 99
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        result = resolver.resolve_skill("  Java  ")
        
        assert result == (99, "exact", None)
        assert stats['skills_resolved_exact'] == 1
    
    def test_exact_match_increments_stats(self, resolver, mock_db, stats):
        """Should increment exact match stats counter."""
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 10
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        resolver.resolve_skill("SQL")
        resolver.resolve_skill("JavaScript")
        
        assert stats['skills_resolved_exact'] == 2
    
    def test_exact_match_logs_debug_message(self, resolver, mock_db, caplog):
        """Should log debug message for exact match."""
        import logging
        
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 7
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        with caplog.at_level(logging.DEBUG):
            resolver.resolve_skill("Python")
        
        assert "exact match" in caplog.text
        assert "skill_id=7" in caplog.text


class TestResolveSkillAliasMatch:
    """Test alias match resolution path."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def stats(self):
        """Create stats dict for tracking."""
        return {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
    
    @pytest.fixture
    def resolver(self, mock_db, stats):
        """Create SkillResolver instance."""
        return SkillResolver(mock_db, stats)
    
    def test_resolves_alias_match_when_no_exact_match(self, resolver, mock_db, stats):
        """Should resolve via alias when no exact match found."""
        # Setup: exact match returns None
        mock_exact_query = Mock()
        mock_exact_query.filter.return_value.first.return_value = None
        
        # Setup: alias match returns result
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 55
        mock_alias_query = Mock()
        mock_alias_query.filter.return_value.first.return_value = mock_alias
        
        # Mock db.query to return different results based on model type
        def query_side_effect(model):
            if model == Skill:
                return mock_exact_query
            elif model == SkillAlias:
                return mock_alias_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Execute
        result = resolver.resolve_skill("JS")
        
        # Verify - returns (skill_id, resolution_method, confidence)
        assert result == (55, "alias", None)
        assert stats['skills_resolved_exact'] == 0
        assert stats['skills_resolved_alias'] == 1
        assert stats['skills_unresolved'] == 0
    
    def test_alias_match_case_insensitive(self, resolver, mock_db, stats):
        """Should match aliases case-insensitively."""
        mock_exact_query = Mock()
        mock_exact_query.filter.return_value.first.return_value = None
        
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 33
        mock_alias_query = Mock()
        mock_alias_query.filter.return_value.first.return_value = mock_alias
        
        def query_side_effect(model):
            return mock_exact_query if model == Skill else mock_alias_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = resolver.resolve_skill("JAVASCRIPT")
        
        assert result == (33, "alias", None)
        assert stats['skills_resolved_alias'] == 1
    
    def test_alias_match_increments_stats(self, resolver, mock_db, stats):
        """Should increment alias match stats counter."""
        mock_exact_query = Mock()
        mock_exact_query.filter.return_value.first.return_value = None
        
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 20
        mock_alias_query = Mock()
        mock_alias_query.filter.return_value.first.return_value = mock_alias
        
        def query_side_effect(model):
            return mock_exact_query if model == Skill else mock_alias_query
        
        mock_db.query.side_effect = query_side_effect
        
        resolver.resolve_skill("JS")
        resolver.resolve_skill("TS")
        
        assert stats['skills_resolved_alias'] == 2
    
    def test_alias_match_logs_debug_message(self, resolver, mock_db, caplog):
        """Should log debug message for alias match."""
        import logging
        
        mock_exact_query = Mock()
        mock_exact_query.filter.return_value.first.return_value = None
        
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 88
        mock_alias_query = Mock()
        mock_alias_query.filter.return_value.first.return_value = mock_alias
        
        def query_side_effect(model):
            return mock_exact_query if model == Skill else mock_alias_query
        
        mock_db.query.side_effect = query_side_effect
        
        with caplog.at_level(logging.DEBUG):
            resolver.resolve_skill("JS")
        
        assert "alias match" in caplog.text
        assert "skill_id=88" in caplog.text


class TestResolveSkillUnresolved:
    """Test unresolved skill path."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def stats(self):
        """Create stats dict for tracking."""
        return {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
    
    @pytest.fixture
    def resolver(self, mock_db, stats):
        """Create SkillResolver instance."""
        return SkillResolver(mock_db, stats)
    
    def test_returns_none_when_unresolved(self, resolver, mock_db, stats):
        """Should return None when skill cannot be resolved."""
        # Both exact and alias queries return None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = resolver.resolve_skill("UnknownSkill")
        
        assert result == (None, None, None)
        assert stats['skills_unresolved'] == 1
    
    def test_tracks_unresolved_skill_name(self, resolver, mock_db, stats):
        """Should add unresolved skill name to stats."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        resolver.resolve_skill("FakeSkill")
        
        assert "FakeSkill" in stats['unresolved_skill_names']
    
    def test_does_not_duplicate_unresolved_names(self, resolver, mock_db, stats):
        """Should not duplicate unresolved skill names in list."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        resolver.resolve_skill("DuplicateSkill")
        resolver.resolve_skill("DuplicateSkill")
        resolver.resolve_skill("DuplicateSkill")
        
        assert stats['unresolved_skill_names'].count("DuplicateSkill") == 1
        assert stats['skills_unresolved'] == 3  # Counter still increments
    
    def test_logs_warning_for_unresolved(self, resolver, mock_db, caplog):
        """Should log warning message for unresolved skill."""
        import logging
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with caplog.at_level(logging.WARNING):
            resolver.resolve_skill("UnknownSkill")
        
        assert "Could not resolve skill" in caplog.text
        assert "UnknownSkill" in caplog.text


class TestResolveSkillWithNormalizer:
    """Test skill resolution with custom name normalizer."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def stats(self):
        """Create stats dict for tracking."""
        return {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
    
    def test_uses_injected_normalizer(self, mock_db, stats):
        """Should use injected normalizer function."""
        resolver = SkillResolver(mock_db, stats)
        
        # Custom normalizer that adds prefix
        custom_normalizer = Mock(return_value="normalized_python")
        resolver.set_name_normalizer(custom_normalizer)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        resolver.resolve_skill("Python")
        
        # Verify custom normalizer was called
        custom_normalizer.assert_called_once_with("Python")
    
    def test_falls_back_to_default_normalization_when_none(self, mock_db, stats):
        """Should use default normalization when normalizer not set."""
        resolver = SkillResolver(mock_db, stats)
        # normalize_name is None by default
        
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 1
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_skill
        mock_db.query.return_value = mock_query
        
        result = resolver.resolve_skill("  PYTHON  ")
        
        # Should still resolve using default lower+strip
        assert result == (1, "exact", None)


class TestResolveSkillResolutionPriority:
    """Test resolution priority order."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def stats(self):
        """Create stats dict for tracking."""
        return {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
    
    def test_exact_match_takes_priority_over_alias(self, mock_db, stats):
        """Should prefer exact match even if alias exists."""
        resolver = SkillResolver(mock_db, stats)
        
        # Setup: both exact and alias would match
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 100
        mock_exact_query = Mock()
        mock_exact_query.filter.return_value.first.return_value = mock_skill
        
        mock_alias = Mock(spec=SkillAlias)
        mock_alias.skill_id = 200  # Different ID
        mock_alias_query = Mock()
        mock_alias_query.filter.return_value.first.return_value = mock_alias
        
        def query_side_effect(model):
            return mock_exact_query if model == Skill else mock_alias_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = resolver.resolve_skill("Python")
        
        # Should return exact match ID, not alias ID
        assert result == (100, "exact", None)
        assert stats['skills_resolved_exact'] == 1
        assert stats['skills_resolved_alias'] == 0


class TestResolveSkillMultipleResolutions:
    """Test multiple skill resolutions in sequence."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()
    
    @pytest.fixture
    def stats(self):
        """Create stats dict for tracking."""
        return {
            'skills_resolved_exact': 0,
            'skills_resolved_alias': 0,
            'skills_unresolved': 0,
            'unresolved_skill_names': []
        }
    
    def test_resolves_multiple_skills_with_different_paths(self, mock_db, stats):
        """Should handle multiple resolutions using different paths."""
        resolver = SkillResolver(mock_db, stats)
        
        # Skill 1: exact match
        mock_skill1 = Mock(spec=Skill)
        mock_skill1.skill_id = 1
        
        # Skill 2: alias match (exact returns None)
        mock_alias2 = Mock(spec=SkillAlias)
        mock_alias2.skill_id = 2
        
        # Skill 3: unresolved (both return None)
        
        call_count = [0]
        
        def query_side_effect(model):
            call_count[0] += 1
            query = Mock()
            
            # First call (Python - exact match)
            if call_count[0] == 1:
                query.filter.return_value.first.return_value = mock_skill1
            # Second call (JS - no exact)
            elif call_count[0] == 2:
                query.filter.return_value.first.return_value = None
            # Third call (JS - alias match)
            elif call_count[0] == 3:
                query.filter.return_value.first.return_value = mock_alias2
            # Fourth and fifth calls (Unknown - unresolved)
            else:
                query.filter.return_value.first.return_value = None
            
            return query
        
        mock_db.query.side_effect = query_side_effect
        
        # Execute
        result1 = resolver.resolve_skill("Python")
        result2 = resolver.resolve_skill("JS")
        result3 = resolver.resolve_skill("UnknownSkill")
        
        # Verify - returns (skill_id, resolution_method, confidence)
        assert result1 == (1, "exact", None)
        assert result2 == (2, "alias", None)
        assert result3 == (None, None, None)
        
        assert stats['skills_resolved_exact'] == 1
        assert stats['skills_resolved_alias'] == 1
        assert stats['skills_unresolved'] == 1
        assert len(stats['unresolved_skill_names']) == 1
