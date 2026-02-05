"""
Standalone test script for skill resolution embedding layer.

Run this script to verify the embedding-based skill resolution works correctly.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.skill_resolution.embedding_provider import FakeEmbeddingProvider
from app.services.skill_resolution.skill_resolver_service import SkillResolverService
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias


def test_exact_match():
    """Test exact match resolution."""
    print("\n=== Test: Exact Match ===")
    
    # Setup
    mock_db = Mock(spec=Session)
    mock_skill = Mock(spec=Skill)
    mock_skill.skill_id = 123
    mock_skill.skill_name = "Python"
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_skill
    mock_db.query.return_value = mock_query
    
    resolver = SkillResolverService(db=mock_db, enable_embedding=False)
    
    # Act
    result = resolver.resolve("python")
    
    # Assert
    assert result.resolved_skill_id == 123
    assert result.resolution_method == "exact"
    assert result.resolution_confidence == 1.0
    
    print("✓ Exact match works correctly")
    print(f"  - Resolved skill_id: {result.resolved_skill_id}")
    print(f"  - Method: {result.resolution_method}")
    print(f"  - Confidence: {result.resolution_confidence}")


def test_alias_match():
    """Test alias match resolution."""
    print("\n=== Test: Alias Match ===")
    
    # Setup
    mock_db = Mock(spec=Session)
    mock_alias = Mock(spec=SkillAlias)
    mock_alias.skill_id = 456
    
    def query_side_effect(model):
        mock_query = Mock()
        if model == Skill:
            mock_query.filter.return_value.first.return_value = None
        elif model == SkillAlias:
            mock_query.filter.return_value.first.return_value = mock_alias
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    resolver = SkillResolverService(db=mock_db, enable_embedding=False)
    
    # Act
    result = resolver.resolve("js")
    
    # Assert
    assert result.resolved_skill_id == 456
    assert result.resolution_method == "alias"
    assert result.resolution_confidence == 1.0
    
    print("✓ Alias match works correctly")
    print(f"  - Resolved skill_id: {result.resolved_skill_id}")
    print(f"  - Method: {result.resolution_method}")
    print(f"  - Confidence: {result.resolution_confidence}")


def test_embedding_not_called_on_exact():
    """Test that embedding provider is NOT called when exact match succeeds."""
    print("\n=== Test: Embedding Not Called on Exact Match ===")
    
    # Setup
    mock_db = Mock(spec=Session)
    mock_skill = Mock(spec=Skill)
    mock_skill.skill_id = 789
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_skill
    mock_db.query.return_value = mock_query
    
    fake_provider = FakeEmbeddingProvider()
    resolver = SkillResolverService(
        db=mock_db,
        embedding_provider=fake_provider,
        enable_embedding=True
    )
    
    # Track if embed was called
    original_embed = fake_provider.embed
    embed_called = []
    
    def tracked_embed(text):
        embed_called.append(text)
        return original_embed(text)
    
    fake_provider.embed = tracked_embed
    
    # Act
    result = resolver.resolve("python")
    
    # Assert
    assert result.resolved_skill_id == 789
    assert result.resolution_method == "exact"
    assert len(embed_called) == 0, "Embedding should NOT be called for exact match"
    
    print("✓ Embedding provider NOT called for exact match")
    print(f"  - Resolved via: {result.resolution_method}")
    print(f"  - Embed called: {len(embed_called)} times (expected: 0)")


def test_fake_embedding_provider():
    """Test FakeEmbeddingProvider works correctly."""
    print("\n=== Test: FakeEmbeddingProvider ===")
    
    provider = FakeEmbeddingProvider(dimension=1536, deterministic=True)
    
    # Test embedding generation
    embedding1 = provider.embed("python")
    embedding2 = provider.embed("python")
    embedding3 = provider.embed("javascript")
    
    assert len(embedding1) == 1536, "Embedding should have correct dimension"
    assert embedding1 == embedding2, "Deterministic embeddings should be identical"
    assert embedding1 != embedding3, "Different texts should have different embeddings"
    
    print("✓ FakeEmbeddingProvider works correctly")
    print(f"  - Dimension: {len(embedding1)}")
    print(f"  - Deterministic: {embedding1 == embedding2}")
    print(f"  - Different texts differ: {embedding1 != embedding3}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("SKILL RESOLUTION EMBEDDING LAYER - STANDALONE TESTS")
    print("=" * 60)
    
    try:
        test_exact_match()
        test_alias_match()
        test_embedding_not_called_on_exact()
        test_fake_embedding_provider()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
