"""
Unit tests for normalization utilities.

Target: backend/app/utils/normalization.py
Coverage: normalize_designation function for role matching.
"""
import pytest
from app.utils.normalization import normalize_designation, normalize_key, normalize_skill_name


# ============================================================================
# TEST: normalize_designation
# ============================================================================

class TestNormalizeDesignation:
    """Test normalize_designation function for role/designation matching."""
    
    def test_returns_empty_string_for_none(self):
        """Should return empty string when input is None."""
        assert normalize_designation(None) == ""
    
    def test_returns_empty_string_for_empty(self):
        """Should return empty string when input is empty."""
        assert normalize_designation("") == ""
    
    def test_lowercases_input(self):
        """Should convert to lowercase."""
        assert normalize_designation("ENGINEER") == "engineer"
        assert normalize_designation("Scrum Master") == "scrum master"
    
    def test_strips_leading_trailing_whitespace(self):
        """Should strip leading and trailing whitespace."""
        assert normalize_designation("  Engineer  ") == "engineer"
        assert normalize_designation("\t\nScrum Master\t\n") == "scrum master"
    
    def test_collapses_multiple_spaces(self):
        """Should collapse multiple internal spaces to single space."""
        assert normalize_designation("Senior   Software   Engineer") == "senior software engineer"
        assert normalize_designation("Scrum    Master") == "scrum master"
    
    def test_normalizes_space_after_slash(self):
        """Should remove space AFTER slash (BUG FIX: Scrum Master/ TL case)."""
        assert normalize_designation("Scrum Master/ TL") == "scrum master/tl"
        assert normalize_designation("Tech Lead/ Manager") == "tech lead/manager"
    
    def test_normalizes_space_before_slash(self):
        """Should remove space BEFORE slash."""
        assert normalize_designation("Scrum Master /TL") == "scrum master/tl"
        assert normalize_designation("Dev /QA") == "dev/qa"
    
    def test_normalizes_spaces_both_sides_of_slash(self):
        """Should remove spaces on BOTH sides of slash."""
        assert normalize_designation("Scrum Master / TL") == "scrum master/tl"
        assert normalize_designation("Developer / Tester") == "developer/tester"
    
    def test_handles_multiple_slashes(self):
        """Should normalize spaces around multiple slashes."""
        assert normalize_designation("Dev / QA / Support") == "dev/qa/support"
        assert normalize_designation("A/ B /C / D") == "a/b/c/d"
    
    def test_preserves_slash_without_spaces(self):
        """Should preserve slash when no surrounding spaces."""
        assert normalize_designation("Scrum Master/TL") == "scrum master/tl"
        assert normalize_designation("Dev/QA") == "dev/qa"
    
    def test_combined_normalization(self):
        """Should handle combination of all normalization rules."""
        # Multiple spaces + slash normalization + case
        assert normalize_designation("  SCRUM   MASTER /  TL  ") == "scrum master/tl"
        # Leading/trailing + internal + slash
        assert normalize_designation("  Senior   Engineer / Lead  ") == "senior engineer/lead"


class TestNormalizeDesignationEdgeCases:
    """Test edge cases for normalize_designation."""
    
    def test_handles_non_string_input(self):
        """Should convert non-string input to string."""
        # Integer
        assert normalize_designation(123) == "123"
        # Float
        assert normalize_designation(3.14) == "3.14"
    
    def test_handles_only_slash(self):
        """Should handle input that is only a slash."""
        assert normalize_designation("/") == "/"
    
    def test_handles_only_spaces_around_slash(self):
        """Should handle input that is only spaces around slash."""
        assert normalize_designation(" / ") == "/"
    
    def test_handles_unicode_spaces(self):
        """Should handle various whitespace characters."""
        # Non-breaking space
        assert normalize_designation("Scrum\xa0Master") == "scrum master"
    
    def test_slash_at_start_or_end(self):
        """Should handle slash at start or end of designation."""
        assert normalize_designation("/Engineer") == "/engineer"
        assert normalize_designation("Engineer/") == "engineer/"
        assert normalize_designation("/ Engineer /") == "/engineer/"


# ============================================================================
# TEST: normalize_skill_name (Plural handling for skill resolution)
# ============================================================================

class TestNormalizeSkillName:
    """Test normalize_skill_name function for skill resolution with plural handling."""
    
    # ----- Basic normalization (inherited from normalize_key behavior) -----
    
    def test_returns_empty_string_for_none(self):
        """Should return empty string when input is None."""
        assert normalize_skill_name(None) == ""
    
    def test_returns_empty_string_for_empty(self):
        """Should return empty string when input is empty."""
        assert normalize_skill_name("") == ""
        assert normalize_skill_name("   ") == ""
    
    def test_lowercases_input(self):
        """Should convert to lowercase."""
        assert normalize_skill_name("Python") == "python"
        assert normalize_skill_name("JAVASCRIPT") == "javascript"
    
    def test_strips_whitespace(self):
        """Should strip leading and trailing whitespace."""
        assert normalize_skill_name("  Python  ") == "python"
    
    def test_collapses_multiple_spaces(self):
        """Should collapse multiple internal spaces to single space."""
        assert normalize_skill_name("Machine   Learning") == "machine learning"
    
    # ----- Slash normalization -----
    
    def test_normalizes_slash_spacing(self):
        """Should remove spaces around slashes."""
        assert normalize_skill_name("CI / CD") == "ci/cd"
        assert normalize_skill_name("CI/ CD") == "ci/cd"
        assert normalize_skill_name("CI /CD") == "ci/cd"
    
    # ----- PLURAL NORMALIZATION (core feature) -----
    
    def test_normalizes_apis_to_api(self):
        """Should normalize 'APIs' to 'API' (case-insensitive)."""
        assert normalize_skill_name("RESTful APIs") == "restful api"
        assert normalize_skill_name("RESTful API") == "restful api"
        assert normalize_skill_name("Web APIs") == "web api"
        assert normalize_skill_name("APIS") == "api"
    
    def test_normalizes_services_to_service(self):
        """Should normalize 'Services' to 'Service' (case-insensitive)."""
        assert normalize_skill_name("Web Services") == "web service"
        assert normalize_skill_name("Web Service") == "web service"
        assert normalize_skill_name("SERVICES") == "service"
        # Note: "Microservices" is treated as a single compound word,
        # not "Micro Services", so it is NOT normalized
        assert normalize_skill_name("Microservices") == "microservices"
    
    def test_normalizes_frameworks_to_framework(self):
        """Should normalize 'Frameworks' to 'Framework' (case-insensitive)."""
        assert normalize_skill_name("Frameworks") == "framework"
        assert normalize_skill_name("Framework") == "framework"
        assert normalize_skill_name("Web Frameworks") == "web framework"
        assert normalize_skill_name("FRAMEWORKS") == "framework"
    
    # ----- Safety: Does NOT strip 's' naively -----
    
    def test_does_not_strip_glass_to_glas(self):
        """Should NOT turn 'Glass' into 'Glas' (no naive 's' stripping)."""
        assert normalize_skill_name("Glass") == "glass"
        assert normalize_skill_name("Glasses") == "glasses"  # Not in rule set
    
    def test_does_not_strip_analytics_to_analytic(self):
        """Should NOT modify words not in the explicit rule set."""
        assert normalize_skill_name("Analytics") == "analytics"
        assert normalize_skill_name("Data Analytics") == "data analytics"
    
    def test_does_not_strip_kubernetes_to_kubernete(self):
        """Should NOT strip trailing 's' from 'Kubernetes'."""
        assert normalize_skill_name("Kubernetes") == "kubernetes"
    
    def test_does_not_strip_aws_to_aw(self):
        """Should NOT strip trailing 's' from acronyms like 'AWS'."""
        assert normalize_skill_name("AWS") == "aws"
    
    def test_does_not_strip_jenkins_to_jenkin(self):
        """Should NOT strip trailing 's' from 'Jenkins'."""
        assert normalize_skill_name("Jenkins") == "jenkins"
    
    # ----- Bilateral matching scenarios -----
    
    def test_apis_matches_api_bidirectional(self):
        """Both 'APIs' and 'API' should normalize to same value."""
        assert normalize_skill_name("RESTful APIs") == normalize_skill_name("RESTful API")
    
    def test_services_matches_service_bidirectional(self):
        """Both 'Services' and 'Service' should normalize to same value."""
        assert normalize_skill_name("Web Services") == normalize_skill_name("Web Service")
    
    def test_frameworks_matches_framework_bidirectional(self):
        """Both 'Frameworks' and 'Framework' should normalize to same value."""
        assert normalize_skill_name("Frameworks") == normalize_skill_name("Framework")


class TestNormalizeSkillNameEdgeCases:
    """Test edge cases for normalize_skill_name."""
    
    def test_handles_plural_as_standalone_word(self):
        """Should normalize standalone plural words."""
        assert normalize_skill_name("APIs") == "api"
        assert normalize_skill_name("Services") == "service"
    
    def test_handles_plural_in_middle_of_phrase(self):
        """Should normalize plurals appearing in the middle of a phrase."""
        assert normalize_skill_name("APIs Design") == "api design"
        assert normalize_skill_name("Web Services Architecture") == "web service architecture"
    
    def test_word_boundary_prevents_partial_match(self):
        """Should only match whole words, not substrings."""
        # 'Therapist' contains 'apis' but should not be affected
        assert normalize_skill_name("Therapist") == "therapist"
        # 'reservices' is not a real word, but tests substring safety
        assert normalize_skill_name("reservices") == "reservices"
    
    def test_multiple_plurals_in_one_skill(self):
        """Should handle multiple plurals in the same skill name."""
        assert normalize_skill_name("APIs and Services") == "api and service"

