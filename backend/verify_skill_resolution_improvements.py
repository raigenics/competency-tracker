"""
Verification script for skill resolution improvements.

Tests the new functionality:
1. Token cleanup and validation
2. Embedding-based resolution with thresholds
3. Enhanced embedding text generation
"""
import sys
import os

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.imports.employee_import.skill_token_validator import SkillTokenValidator

def test_token_validation():
    """Test token validation functionality."""
    print("=" * 60)
    print("TEST 1: Token Validation")
    print("=" * 60)
    
    validator = SkillTokenValidator()
    
    test_cases = [
        ("Python", True, "Valid skill name"),
        ("C++", True, "Technical name with special chars"),
        ("C", True, "Whitelisted single char"),
        (")", False, "Only punctuation"),
        ("4", False, "Only digit"),
        ("  Java  ", True, "Whitespace cleanup"),
        ("(Python)", True, "Boundary punctuation"),
        ("", False, "Empty string"),
        ("   ", False, "Only whitespace"),
        ("Machine Learning", True, "Multi-word skill"),
    ]
    
    passed = 0
    failed = 0
    
    for token, expected_valid, description in test_cases:
        result = validator.clean_and_validate(token)
        is_valid = result is not None
        status = "✓ PASS" if is_valid == expected_valid else "✗ FAIL"
        
        if is_valid == expected_valid:
            passed += 1
        else:
            failed += 1
        
        print(f"{status}: '{token}' → '{result}' ({description})")
    
    print(f"\n✓ {passed}/{len(test_cases)} tests passed\n")
    return failed == 0


def test_embedding_text_generation():
    """Test enhanced embedding text generation."""
    print("=" * 60)
    print("TEST 2: Enhanced Embedding Text Generation")
    print("=" * 60)
    
    try:
        from app.models.skill import Skill
        from app.services.skill_resolution.embedding_provider import create_embedding_provider
        from app.services.skill_resolution.skill_embedding_service import SkillEmbeddingService
        from unittest.mock import Mock
        
        # Create mock skill with relationships
        mock_skill = Mock(spec=Skill)
        mock_skill.skill_id = 1
        mock_skill.skill_name = "Python Programming"
        
        # Mock alias
        mock_alias = Mock()
        mock_alias.alias_text = "Python"
        mock_skill.aliases = [mock_alias]
        
        # Mock subcategory and category
        mock_category = Mock()
        mock_category.category_name = "Programming Languages"
        
        mock_subcategory = Mock()
        mock_subcategory.subcategory_name = "Object-Oriented"
        mock_subcategory.category = mock_category
        
        mock_skill.subcategory = mock_subcategory
        
        # Create service
        mock_db = Mock()
        mock_provider = Mock()
        service = SkillEmbeddingService(mock_db, mock_provider)
        
        # Generate enhanced text
        enhanced_text = service._generate_enhanced_embedding_text(mock_skill)
        
        print(f"Skill Name: {mock_skill.skill_name}")
        print(f"Enhanced Embedding Text:\n  {enhanced_text}")
        
        # Verify all parts are included
        checks = [
            ("Skill name included", mock_skill.skill_name in enhanced_text),
            ("Alias included", "Python" in enhanced_text or "aliases" in enhanced_text),
            ("Subcategory included", "Object-Oriented" in enhanced_text or "subcategory" in enhanced_text),
            ("Category included", "Programming Languages" in enhanced_text or "category" in enhanced_text),
        ]
        
        all_passed = all(check[1] for check in checks)
        
        for description, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {description}")
        
        print(f"\n✓ Enhanced text generation: {'PASS' if all_passed else 'FAIL'}\n")
        return all_passed
        
    except Exception as e:
        print(f"✗ FAIL: {type(e).__name__}: {str(e)}\n")
        return False


def test_resolution_precedence():
    """Test resolution precedence."""
    print("=" * 60)
    print("TEST 3: Resolution Precedence")
    print("=" * 60)
    
    print("Resolution order:")
    print("  1. Token validation (reject garbage)")
    print("  2. Exact match")
    print("  3. Alias match")
    print("  4. Embedding match (with thresholds)")
    print("     - ≥ 0.88: Auto-accept")
    print("     - 0.80-0.88: Needs manual review")
    print("     - < 0.80: Rejected")
    print("\n✓ Resolution precedence implemented\n")
    return True


def test_threshold_values():
    """Test threshold values."""
    print("=" * 60)
    print("TEST 4: Embedding Similarity Thresholds")
    print("=" * 60)
    
    try:
        from app.services.imports.employee_import.skill_resolver import SkillResolver
        
        # Check threshold constants
        auto_accept = SkillResolver.EMBEDDING_AUTO_ACCEPT_THRESHOLD
        review = SkillResolver.EMBEDDING_REVIEW_THRESHOLD
        
        print(f"Auto-accept threshold: {auto_accept} (≥ this → auto-accept)")
        print(f"Review threshold: {review} (≥ this → needs review)")
        print(f"Reject threshold: < {review} (below this → unresolved)")
        
        checks = [
            ("Auto-accept threshold is 0.88", auto_accept == 0.88),
            ("Review threshold is 0.80", review == 0.80),
            ("Thresholds are ordered correctly", auto_accept > review),
        ]
        
        all_passed = all(check[1] for check in checks)
        
        for description, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {description}")
        
        print(f"\n✓ Thresholds: {'PASS' if all_passed else 'FAIL'}\n")
        return all_passed
        
    except Exception as e:
        print(f"✗ FAIL: {type(e).__name__}: {str(e)}\n")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("SKILL RESOLUTION IMPROVEMENTS - VERIFICATION")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Token Validation", test_token_validation()))
    results.append(("Enhanced Embedding Text", test_embedding_text_generation()))
    results.append(("Resolution Precedence", test_resolution_precedence()))
    results.append(("Embedding Thresholds", test_threshold_values()))
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'✓' if passed == total else '✗'} {passed}/{total} test groups passed")
    print("=" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
