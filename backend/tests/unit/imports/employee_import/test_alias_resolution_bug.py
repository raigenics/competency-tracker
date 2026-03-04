"""
Test for alias resolution bug: mapped skills not resolving on re-import.

Bug description:
- User maps unresolved skill "Azure Kubernetes Service (AKS)" to a target skill
- Alias created with alias_text = "azure kubernetes service (aks)"
- On re-import, skill "Azure Kubernetes Service (AKS)" still marked as UNRESOLVED

This test reproduces the bug to verify the fix.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.imports.employee_import.skill_resolver import SkillResolver
from app.services.imports.employee_import.name_normalizer import NameNormalizer
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.utils.normalization import normalize_skill_name


class TestAliasResolutionBug:
    """
    Test that aliases created via "Map Unresolved Skill" flow
    are properly resolved on subsequent imports.
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
    
    def test_old_normalization_causes_mismatch(self):
        """
        Demonstrate the bug: NameNormalizer keeps closing parenthesis,
        but token validator strips it. This causes lookup mismatch.
        """
        from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator
        
        raw_text = "Azure Kubernetes Service (AKS)"
        
        # OLD behavior: NameNormalizer (used before the fix)
        name_normalizer = NameNormalizer()
        old_alias_text = name_normalizer.normalize_name(raw_text)
        
        # Resolver normalization: token_validator -> normalize_skill_name
        token_validator = SkillTokenValidator()
        cleaned = token_validator.clean_and_validate(raw_text)
        resolver_lookup_key = normalize_skill_name(cleaned)
        
        # The OLD alias text, when normalized for cache, gives wrong key
        old_cache_key = normalize_skill_name(old_alias_text)
        
        print(f"Raw: {raw_text!r}")
        print(f"OLD alias_text: {old_alias_text!r}")
        print(f"OLD cache key: {old_cache_key!r}")
        print(f"Resolver lookup key: {resolver_lookup_key!r}")
        
        # These DON'T match - this is the bug!
        assert old_cache_key != resolver_lookup_key, "Bug no longer exists - test needs update"
    
    def test_alias_text_normalization_consistency(self):
        """
        Verify that the NEW canonical normalization produces consistent keys.
        
        After the fix, both alias storage and resolver lookup use:
        token_validator.clean_and_validate() -> normalize_skill_name()
        """
        from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator
        
        # The input skill name from Excel
        raw_skill_name = "Azure Kubernetes Service (AKS)"
        
        # How alias_text is stored AFTER THE FIX
        token_validator = SkillTokenValidator()
        cleaned = token_validator.clean_and_validate(raw_skill_name)
        stored_alias_text = normalize_skill_name(cleaned)
        
        # How resolver normalizes alias_text when building cache
        cache_key_from_stored = normalize_skill_name(stored_alias_text)
        
        # How resolver normalizes input when looking up
        cleaned_input = token_validator.clean_and_validate(raw_skill_name)
        input_normalized = normalize_skill_name(cleaned_input)
        
        print(f"Raw input: {raw_skill_name!r}")
        print(f"Stored alias_text (NEW): {stored_alias_text!r}")
        print(f"Cache key from stored alias: {cache_key_from_stored!r}")
        print(f"Input normalized for lookup: {input_normalized!r}")
        
        # These MUST be equal for the alias to be found
        assert cache_key_from_stored == input_normalized, (
            f"Normalization mismatch! "
            f"Cache key: {cache_key_from_stored!r} != Input: {input_normalized!r}"
        )
    
    def test_resolve_skill_finds_manually_mapped_alias(self, mock_db, stats):
        """
        Test that a skill resolver correctly resolves a skill
        that was previously mapped via the UI flow.
        
        Flow being tested:
        1. During import: "Azure Kubernetes Service (AKS)" is unresolved
        2. User maps it to skill_id=42 via UI
        3. Alias created with canonical alias_text (after fix)
        4. On next import: same skill should resolve via alias
        """
        from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator
        
        # Setup: Target skill exists
        target_skill = Mock(spec=Skill)
        target_skill.skill_id = 42
        target_skill.skill_name = "Azure Kubernetes Services"
        
        # Setup: How alias is stored AFTER THE FIX
        # The fix applies: token_validator.clean_and_validate() -> normalize_skill_name()
        raw_text = "Azure Kubernetes Service (AKS)"
        token_validator = SkillTokenValidator()
        cleaned_token = token_validator.clean_and_validate(raw_text)
        canonical_alias_text = normalize_skill_name(cleaned_token)
        
        alias = Mock(spec=SkillAlias)
        alias.alias_text = canonical_alias_text  # "azure kubernetes service (aks" (note: no closing paren)
        alias.skill_id = 42
        
        # Mock DB queries to return our skill and alias
        def mock_query(model):
            mock_q = Mock()
            if model == Skill:
                mock_q.all.return_value = [target_skill]
            elif model == SkillAlias:
                mock_q.all.return_value = [alias]
            return mock_q
        
        mock_db.query.side_effect = mock_query
        
        # Create resolver with embedding disabled
        with patch('app.services.skill_resolution.embedding_provider.create_embedding_provider', side_effect=Exception("disabled")):
            resolver = SkillResolver(mock_db, stats)
        
        # Debug: check what's in the cache
        resolver._build_lookup_cache()
        print(f"Skill lookup cache: {resolver._skill_lookup}")
        print(f"Alias lookup cache: {resolver._alias_lookup}")
        print(f"Canonical alias text: {canonical_alias_text!r}")
        
        # Act: Try to resolve the EXACT same input that was originally unresolved
        skill_id, resolution_method, confidence = resolver.resolve_skill("Azure Kubernetes Service (AKS)")
        
        # Assert: Should resolve via alias
        assert skill_id == 42, f"Expected skill_id=42, got {skill_id}"
        assert resolution_method == "alias", f"Expected method='alias', got {resolution_method}"
        assert stats['skills_resolved_alias'] == 1
    
    def test_resolve_skill_finds_alias_with_different_case(self, mock_db, stats):
        """
        Test that alias resolution is case-insensitive.
        """
        from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator
        
        # Setup
        target_skill = Mock(spec=Skill)
        target_skill.skill_id = 42
        target_skill.skill_name = "Azure Kubernetes Services"
        
        # Use the new canonical normalization
        raw_text = "azure kubernetes service (aks)"
        token_validator = SkillTokenValidator()
        cleaned_token = token_validator.clean_and_validate(raw_text)
        canonical_alias_text = normalize_skill_name(cleaned_token)
        
        alias = Mock(spec=SkillAlias)
        alias.alias_text = canonical_alias_text
        alias.skill_id = 42
        
        def mock_query(model):
            mock_q = Mock()
            if model == Skill:
                mock_q.all.return_value = [target_skill]
            elif model == SkillAlias:
                mock_q.all.return_value = [alias]
            return mock_q
        
        mock_db.query.side_effect = mock_query
        
        with patch('app.services.skill_resolution.embedding_provider.create_embedding_provider', side_effect=Exception("disabled")):
            resolver = SkillResolver(mock_db, stats)
        
        # Act: Input with DIFFERENT case
        skill_id, resolution_method, confidence = resolver.resolve_skill("AZURE KUBERNETES SERVICE (AKS)")
        
        # Assert
        assert skill_id == 42
        assert resolution_method == "alias"


class TestNormalizationFunctionComparison:
    """
    Direct comparison of normalization functions to identify mismatches.
    """
    
    @pytest.mark.parametrize("input_text,expected_match", [
        ("Azure Kubernetes Service (AKS)", True),
        ("azure kubernetes service (aks)", True),
        ("RESTful APIs", True),  # Tests plural handling
        ("  Python  ", True),  # Tests whitespace
        ("Machine Learning / AI", True),  # Tests slash handling
    ])
    def test_normalization_produces_matching_keys(self, input_text, expected_match):
        """
        Test that the normalization used to store alias and 
        the normalization used to lookup produce matching keys.
        """
        name_normalizer = NameNormalizer()
        
        # Step 1: How alias_text is stored (via NameNormalizer)
        stored = name_normalizer.normalize_name(input_text)
        
        # Step 2: How it's normalized when building cache
        cache_key = normalize_skill_name(stored)
        
        # Step 3: How input is normalized for lookup
        lookup_key = normalize_skill_name(input_text)
        
        if expected_match:
            assert cache_key == lookup_key, (
                f"Keys don't match!\n"
                f"  Input: {input_text!r}\n"
                f"  Stored: {stored!r}\n"
                f"  Cache key: {cache_key!r}\n"
                f"  Lookup key: {lookup_key!r}"
            )
