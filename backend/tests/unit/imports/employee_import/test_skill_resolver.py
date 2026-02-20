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
        """Create mock database session with lookup cache support."""
        db = Mock()
        return db
    
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
    
    def _setup_lookup_mock(self, mock_db, skills=None, aliases=None):
        """
        Helper to setup mock for lookup cache.
        
        Args:
            mock_db: Mock database session
            skills: List of (skill_name, skill_id) tuples
            aliases: List of (alias_text, skill_id) tuples
        """
        skills = skills or []
        aliases = aliases or []
        
        # Create mock skill objects
        mock_skills = []
        for name, skill_id in skills:
            s = Mock(spec=Skill)
            s.skill_name = name
            s.skill_id = skill_id
            mock_skills.append(s)
        
        # Create mock alias objects
        mock_aliases = []
        for text, skill_id in aliases:
            a = Mock(spec=SkillAlias)
            a.alias_text = text
            a.skill_id = skill_id
            mock_aliases.append(a)
        
        # Mock query().all() to return appropriate lists
        def query_side_effect(model):
            query = Mock()
            if model == Skill:
                query.all.return_value = mock_skills
            elif model == SkillAlias:
                query.all.return_value = mock_aliases
            return query
        
        mock_db.query.side_effect = query_side_effect
    
    def test_resolves_exact_match_case_insensitive(self, resolver, mock_db, stats):
        """Should resolve skill via exact match (case-insensitive)."""
        self._setup_lookup_mock(mock_db, skills=[("Python", 42)])
        
        result = resolver.resolve_skill("python")
        
        assert result == (42, "exact", None)
        assert stats['skills_resolved_exact'] == 1
        assert stats['skills_resolved_alias'] == 0
        assert stats['skills_unresolved'] == 0
    
    def test_resolves_exact_match_with_whitespace(self, resolver, mock_db, stats):
        """Should resolve exact match after trimming whitespace."""
        self._setup_lookup_mock(mock_db, skills=[("Java", 99)])
        
        result = resolver.resolve_skill("  Java  ")
        
        assert result == (99, "exact", None)
        assert stats['skills_resolved_exact'] == 1
    
    def test_exact_match_increments_stats(self, resolver, mock_db, stats):
        """Should increment exact match stats counter."""
        self._setup_lookup_mock(mock_db, skills=[("SQL", 10), ("JavaScript", 11)])
        
        resolver.resolve_skill("SQL")
        resolver.resolve_skill("JavaScript")
        
        assert stats['skills_resolved_exact'] == 2
    
    def test_exact_match_logs_debug_message(self, resolver, mock_db, caplog):
        """Should log debug message for exact match."""
        import logging
        
        self._setup_lookup_mock(mock_db, skills=[("Python", 7)])
        
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
    
    def _setup_lookup_mock(self, mock_db, skills=None, aliases=None):
        """Helper to setup mock for lookup cache."""
        skills = skills or []
        aliases = aliases or []
        
        mock_skills = []
        for name, skill_id in skills:
            s = Mock(spec=Skill)
            s.skill_name = name
            s.skill_id = skill_id
            mock_skills.append(s)
        
        mock_aliases = []
        for text, skill_id in aliases:
            a = Mock(spec=SkillAlias)
            a.alias_text = text
            a.skill_id = skill_id
            mock_aliases.append(a)
        
        def query_side_effect(model):
            query = Mock()
            if model == Skill:
                query.all.return_value = mock_skills
            elif model == SkillAlias:
                query.all.return_value = mock_aliases
            return query
        
        mock_db.query.side_effect = query_side_effect
    
    def test_resolves_alias_match_when_no_exact_match(self, resolver, mock_db, stats):
        """Should resolve via alias when no exact match found."""
        self._setup_lookup_mock(mock_db, skills=[], aliases=[("JS", 55)])
        
        result = resolver.resolve_skill("JS")
        
        assert result == (55, "alias", None)
        assert stats['skills_resolved_exact'] == 0
        assert stats['skills_resolved_alias'] == 1
        assert stats['skills_unresolved'] == 0
    
    def test_alias_match_case_insensitive(self, resolver, mock_db, stats):
        """Should match aliases case-insensitively."""
        self._setup_lookup_mock(mock_db, skills=[], aliases=[("javascript", 33)])
        
        result = resolver.resolve_skill("JAVASCRIPT")
        
        assert result == (33, "alias", None)
        assert stats['skills_resolved_alias'] == 1
    
    def test_alias_match_increments_stats(self, resolver, mock_db, stats):
        """Should increment alias match stats counter."""
        self._setup_lookup_mock(mock_db, skills=[], aliases=[("JS", 20), ("TS", 21)])
        
        resolver.resolve_skill("JS")
        resolver.resolve_skill("TS")
        
        assert stats['skills_resolved_alias'] == 2
    
    def test_alias_match_logs_debug_message(self, resolver, mock_db, caplog):
        """Should log debug message for alias match."""
        import logging
        
        self._setup_lookup_mock(mock_db, skills=[], aliases=[("JS", 88)])
        
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
    
    def _setup_empty_lookup_mock(self, mock_db):
        """Helper to setup mock with empty lookups."""
        def query_side_effect(model):
            query = Mock()
            query.all.return_value = []
            return query
        mock_db.query.side_effect = query_side_effect
    
    def test_returns_none_when_unresolved(self, resolver, mock_db, stats):
        """Should return None when skill cannot be resolved."""
        self._setup_empty_lookup_mock(mock_db)
        
        result = resolver.resolve_skill("UnknownSkill")
        
        assert result == (None, None, None)
        assert stats['skills_unresolved'] == 1
    
    def test_tracks_unresolved_skill_name(self, resolver, mock_db, stats):
        """Should add unresolved skill name to stats."""
        self._setup_empty_lookup_mock(mock_db)
        
        resolver.resolve_skill("FakeSkill")
        
        assert "FakeSkill" in stats['unresolved_skill_names']
    
    def test_does_not_duplicate_unresolved_names(self, resolver, mock_db, stats):
        """Should not duplicate unresolved skill names in list."""
        self._setup_empty_lookup_mock(mock_db)
        
        resolver.resolve_skill("DuplicateSkill")
        resolver.resolve_skill("DuplicateSkill")
        resolver.resolve_skill("DuplicateSkill")
        
        assert stats['unresolved_skill_names'].count("DuplicateSkill") == 1
        assert stats['skills_unresolved'] == 3  # Counter still increments
    
    def test_logs_warning_for_unresolved(self, resolver, mock_db, caplog):
        """Should log warning message for unresolved skill."""
        import logging
        
        self._setup_empty_lookup_mock(mock_db)
        
        with caplog.at_level(logging.WARNING):
            resolver.resolve_skill("UnknownSkill")
        
        assert "Could not resolve skill" in caplog.text
        assert "UnknownSkill" in caplog.text


class TestResolveSkillWithNormalizer:
    """Test skill resolution with custom name normalizer (legacy - normalize_name is no longer used)."""
    
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
    
    def _setup_lookup_mock(self, mock_db, skills=None, aliases=None):
        """Helper to setup mock for lookup cache."""
        skills = skills or []
        aliases = aliases or []
        
        mock_skills = []
        for name, skill_id in skills:
            s = Mock(spec=Skill)
            s.skill_name = name
            s.skill_id = skill_id
            mock_skills.append(s)
        
        mock_aliases = []
        for text, skill_id in aliases:
            a = Mock(spec=SkillAlias)
            a.alias_text = text
            a.skill_id = skill_id
            mock_aliases.append(a)
        
        def query_side_effect(model):
            query = Mock()
            if model == Skill:
                query.all.return_value = mock_skills
            elif model == SkillAlias:
                query.all.return_value = mock_aliases
            return query
        
        mock_db.query.side_effect = query_side_effect
    
    def test_resolves_with_default_normalization(self, mock_db, stats):
        """Should resolve using normalize_skill_name function."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(mock_db, skills=[("Python", 1)])
        
        result = resolver.resolve_skill("  PYTHON  ")
        
        # Should resolve using normalize_skill_name
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
    
    def _setup_lookup_mock(self, mock_db, skills=None, aliases=None):
        """Helper to setup mock for lookup cache."""
        skills = skills or []
        aliases = aliases or []
        
        mock_skills = []
        for name, skill_id in skills:
            s = Mock(spec=Skill)
            s.skill_name = name
            s.skill_id = skill_id
            mock_skills.append(s)
        
        mock_aliases = []
        for text, skill_id in aliases:
            a = Mock(spec=SkillAlias)
            a.alias_text = text
            a.skill_id = skill_id
            mock_aliases.append(a)
        
        def query_side_effect(model):
            query = Mock()
            if model == Skill:
                query.all.return_value = mock_skills
            elif model == SkillAlias:
                query.all.return_value = mock_aliases
            return query
        
        mock_db.query.side_effect = query_side_effect
    
    def test_exact_match_takes_priority_over_alias(self, mock_db, stats):
        """Should prefer exact match even if alias exists with same normalized name."""
        resolver = SkillResolver(mock_db, stats)
        
        # Both skill and alias exist for "python" (normalized)
        self._setup_lookup_mock(
            mock_db,
            skills=[("Python", 100)],
            aliases=[("Python", 200)]  # Different ID
        )
        
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
    
    def _setup_lookup_mock(self, mock_db, skills=None, aliases=None):
        """Helper to setup mock for lookup cache."""
        skills = skills or []
        aliases = aliases or []
        
        mock_skills = []
        for name, skill_id in skills:
            s = Mock(spec=Skill)
            s.skill_name = name
            s.skill_id = skill_id
            mock_skills.append(s)
        
        mock_aliases = []
        for text, skill_id in aliases:
            a = Mock(spec=SkillAlias)
            a.alias_text = text
            a.skill_id = skill_id
            mock_aliases.append(a)
        
        def query_side_effect(model):
            query = Mock()
            if model == Skill:
                query.all.return_value = mock_skills
            elif model == SkillAlias:
                query.all.return_value = mock_aliases
            return query
        
        mock_db.query.side_effect = query_side_effect
    
    def test_resolves_multiple_skills_with_different_paths(self, mock_db, stats):
        """Should handle multiple resolutions using different paths."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(
            mock_db,
            skills=[("Python", 1)],
            aliases=[("JS", 2)]
        )
        
        result1 = resolver.resolve_skill("Python")
        result2 = resolver.resolve_skill("JS")
        result3 = resolver.resolve_skill("UnknownSkill")
        
        assert result1 == (1, "exact", None)
        assert result2 == (2, "alias", None)
        assert result3 == (None, None, None)
        
        assert stats['skills_resolved_exact'] == 1
        assert stats['skills_resolved_alias'] == 1
        assert stats['skills_unresolved'] == 1
        assert len(stats['unresolved_skill_names']) == 1


# ============================================================================
# TEST: Plural Normalization (NEW FEATURE)
# ============================================================================

class TestResolveSkillPluralNormalization:
    """Test plural normalization for skill resolution.
    
    This tests the bilateral matching behavior where:
    - "RESTful APIs" matches "RESTful API" alias
    - "RESTful API" matches "RESTful APIs" alias
    - "Web Services" matches "Web Service"
    - etc.
    """
    
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
    
    def _setup_lookup_mock(self, mock_db, skills=None, aliases=None):
        """Helper to setup mock for lookup cache."""
        skills = skills or []
        aliases = aliases or []
        
        mock_skills = []
        for name, skill_id in skills:
            s = Mock(spec=Skill)
            s.skill_name = name
            s.skill_id = skill_id
            mock_skills.append(s)
        
        mock_aliases = []
        for text, skill_id in aliases:
            a = Mock(spec=SkillAlias)
            a.alias_text = text
            a.skill_id = skill_id
            mock_aliases.append(a)
        
        def query_side_effect(model):
            query = Mock()
            if model == Skill:
                query.all.return_value = mock_skills
            elif model == SkillAlias:
                query.all.return_value = mock_aliases
            return query
        
        mock_db.query.side_effect = query_side_effect
    
    # ----- APIs <-> API matching -----
    
    def test_resolves_restful_apis_to_restful_api_alias(self, mock_db, stats):
        """Should resolve 'RESTful APIs' via 'RESTful API' alias."""
        resolver = SkillResolver(mock_db, stats)
        
        # Alias in DB is singular: "RESTful API"
        self._setup_lookup_mock(mock_db, skills=[], aliases=[("RESTful API", 42)])
        
        # Input is plural: "RESTful APIs"
        result = resolver.resolve_skill("RESTful APIs")
        
        assert result == (42, "alias", None)
        assert stats['skills_resolved_alias'] == 1
    
    def test_resolves_restful_api_to_restful_apis_alias(self, mock_db, stats):
        """Should resolve 'RESTful API' via 'RESTful APIs' alias (reverse)."""
        resolver = SkillResolver(mock_db, stats)
        
        # Alias in DB is plural: "RESTful APIs"
        self._setup_lookup_mock(mock_db, skills=[], aliases=[("RESTful APIs", 42)])
        
        # Input is singular: "RESTful API"
        result = resolver.resolve_skill("RESTful API")
        
        assert result == (42, "alias", None)
        assert stats['skills_resolved_alias'] == 1
    
    # ----- Services <-> Service matching -----
    
    def test_resolves_web_services_to_web_service(self, mock_db, stats):
        """Should resolve 'Web Services' via 'Web Service' skill."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(mock_db, skills=[("Web Service", 50)], aliases=[])
        
        result = resolver.resolve_skill("Web Services")
        
        assert result == (50, "exact", None)
        assert stats['skills_resolved_exact'] == 1
    
    def test_resolves_web_service_to_web_services(self, mock_db, stats):
        """Should resolve 'Web Service' via 'Web Services' skill (reverse)."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(mock_db, skills=[("Web Services", 50)], aliases=[])
        
        result = resolver.resolve_skill("Web Service")
        
        assert result == (50, "exact", None)
        assert stats['skills_resolved_exact'] == 1
    
    # ----- Frameworks <-> Framework matching -----
    
    def test_resolves_frameworks_to_framework(self, mock_db, stats):
        """Should resolve 'Frameworks' via 'Framework' skill."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(mock_db, skills=[("Framework", 60)], aliases=[])
        
        result = resolver.resolve_skill("Frameworks")
        
        assert result == (60, "exact", None)
    
    def test_resolves_framework_to_frameworks(self, mock_db, stats):
        """Should resolve 'Framework' via 'Frameworks' skill (reverse)."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(mock_db, skills=[("Frameworks", 60)], aliases=[])
        
        result = resolver.resolve_skill("Framework")
        
        assert result == (60, "exact", None)
    
    # ----- Safety: No naive 's' stripping -----
    
    def test_glass_does_not_become_glas(self, mock_db, stats):
        """Should NOT turn 'Glass' into 'Glas' (no naive 's' stripping)."""
        resolver = SkillResolver(mock_db, stats)
        
        # Skill is "Glas" (not "Glass")
        self._setup_lookup_mock(mock_db, skills=[("Glas", 70)], aliases=[])
        
        result = resolver.resolve_skill("Glass")
        
        # Should NOT match - "Glass" != "Glas"
        assert result == (None, None, None)
        assert stats['skills_unresolved'] == 1
    
    def test_unrelated_skill_still_unresolved(self, mock_db, stats):
        """Should not resolve unrelated skills."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(mock_db, skills=[("Python", 1)], aliases=[("JS", 2)])
        
        result = resolver.resolve_skill("Unknown Skill")
        
        assert result == (None, None, None)
        assert stats['skills_unresolved'] == 1
    
    def test_kubernetes_not_stripped(self, mock_db, stats):
        """Should NOT strip 's' from 'Kubernetes'."""
        resolver = SkillResolver(mock_db, stats)
        
        # Only "Kubernetes" exists (no "Kubernete")
        self._setup_lookup_mock(mock_db, skills=[("Kubernetes", 80)], aliases=[])
        
        result = resolver.resolve_skill("Kubernetes")
        
        assert result == (80, "exact", None)
    
    def test_aws_not_stripped(self, mock_db, stats):
        """Should NOT strip 's' from 'AWS'."""
        resolver = SkillResolver(mock_db, stats)
        
        self._setup_lookup_mock(mock_db, skills=[("AWS", 90)], aliases=[])
        
        result = resolver.resolve_skill("AWS")
        
        assert result == (90, "exact", None)
