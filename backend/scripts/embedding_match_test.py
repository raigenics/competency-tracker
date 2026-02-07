"""
Embedding-Based Skill Matching Test Script
===========================================

PURPOSE:
    Validate embedding-based skill matching against existing master skills.
    Test raw employee skill names to see how well they match via semantic similarity.

USAGE:
    python scripts/embedding_match_test.py [--csv output.csv] [--top-k 5]

REQUIREMENTS:
    - Master skills already imported (SkillMasterData.xlsx)
    - skill_embeddings table populated with vectors
    - OpenAI/Azure OpenAI API key configured

READS:
    - skill_embeddings table (existing embeddings)
    - skills table (master skill names)

WRITES:
    - Console output (always)
    - CSV file (optional, if --csv specified)
"""

import sys
import os
import csv
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding
from app.models.skill_alias import SkillAlias
from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.services.skill_resolution.embedding_provider import create_embedding_provider


# ============================================================================
# TEST DATA - Hardcoded raw skill names to test
# ============================================================================

TEST_SKILLS = [
    ")",
    "4",
    "6",
    "SuperObscureFramework2026",
]


# ============================================================================
# MATCHING THRESHOLDS
# ============================================================================

class MatchThreshold:
    """Thresholds for match classification based on cosine similarity."""
    EXACT = 0.95      # >= 0.95 = EXACT
    HIGH = 0.85       # >= 0.85 = HIGH
    MEDIUM = 0.70     # >= 0.70 = MEDIUM
    LOW = 0.50        # >= 0.50 = LOW
    # < 0.50 = NO_MATCH


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_skill_name(skill_name: str) -> str:
    """Normalize skill name (same as embedding service)."""
    return skill_name.strip().lower()


def cosine_distance_to_similarity(distance: float) -> float:
    """
    Convert cosine distance to similarity.
    
    pgvector returns cosine distance (0 = identical, 2 = opposite).
    Cosine similarity = 1 - distance
    
    Returns:
        Similarity score between 0 and 1 (1 = identical)
    """
    return 1.0 - distance


def classify_match(similarity: float) -> str:
    """Classify match quality based on similarity score."""
    if similarity >= MatchThreshold.EXACT:
        return "EXACT"
    elif similarity >= MatchThreshold.HIGH:
        return "HIGH"
    elif similarity >= MatchThreshold.MEDIUM:
        return "MEDIUM"
    elif similarity >= MatchThreshold.LOW:
        return "LOW"
    else:
        return "NO_MATCH"


def format_percentage(value: float) -> str:
    """Format float as percentage string."""
    return f"{value * 100:.2f}%"


# ============================================================================
# CORE MATCHING LOGIC - Replicates actual employee skill resolution workflow
# ============================================================================

def resolve_skill_with_full_workflow(
    db: Session,
    embedding_provider,
    raw_skill_name: str,
    top_k: int = 5,
    model_name: str = "text-embedding-3-small"
) -> Dict[str, Any]:
    """
    Resolve skill using the ACTUAL workflow: exact match → alias match → embedding match.
    
    This replicates the employee skill resolution process:
    1. Try exact match (normalized skill name)
    2. Try alias match (skill_aliases table)
    3. Try embedding match (semantic similarity)
    4. Return full skill details with category/subcategory
    
    Args:
        db: Database session
        embedding_provider: Embedding provider instance
        raw_skill_name: Raw skill name to match
        top_k: Number of top embedding matches to return if needed
        model_name: Model name used for embeddings
        
    Returns:
        Dictionary with keys:
            - input_skill: Original input
            - normalized_input: Normalized version
            - match_method: "EXACT" | "ALIAS" | "EMBEDDING" | "NOT_FOUND"
            - matched_skill: Skill object or None
            - alias_matched: Alias name if alias match
            - embedding_matches: List of top K embedding matches (if embedding method used)
            - skill_details: Dict with skill_id, skill_name, category_name, subcategory_name
    """
    result = {
        'input_skill': raw_skill_name,
        'normalized_input': normalize_skill_name(raw_skill_name),
        'match_method': None,
        'matched_skill': None,
        'alias_matched': None,
        'embedding_matches': [],
        'skill_details': None
    }
    
    normalized_input = result['normalized_input']
      # ========================================================================
    # STEP 1: Try EXACT MATCH (normalized skill name)
    # ========================================================================
    exact_match = db.query(Skill).filter(
        func.lower(func.trim(Skill.skill_name)) == normalized_input
    ).first()
    
    if exact_match:
        result['match_method'] = "EXACT"
        result['matched_skill'] = exact_match
        result['skill_details'] = get_skill_full_details(db, exact_match.skill_id)
        return result
      # ========================================================================
    # STEP 2: Try ALIAS MATCH (skill_aliases table)
    # ========================================================================
    alias_match = db.query(SkillAlias).filter(
        func.lower(func.trim(SkillAlias.alias_text)) == normalized_input
    ).first()
    
    if alias_match:
        matched_skill = db.query(Skill).filter(
            Skill.skill_id == alias_match.skill_id
        ).first()
        
        if matched_skill:
            result['match_method'] = "ALIAS"
            result['matched_skill'] = matched_skill
            result['alias_matched'] = alias_match.alias_text  # Original alias text
            result['skill_details'] = get_skill_full_details(db, matched_skill.skill_id)
            return result
    
    # ========================================================================
    # STEP 3: Try EMBEDDING MATCH (semantic similarity using pgvector)
    # ========================================================================
    embedding_matches = find_similar_skills_via_embedding(
        db=db,
        embedding_provider=embedding_provider,
        normalized_input=normalized_input,
        top_k=top_k,
        model_name=model_name
    )
    
    if embedding_matches:
        # Take best match (highest similarity)
        best_match = embedding_matches[0]
        
        # Only consider it a match if similarity is above threshold
        if best_match['similarity'] >= MatchThreshold.LOW:
            matched_skill = db.query(Skill).filter(
                Skill.skill_id == best_match['skill_id']
            ).first()
            
            if matched_skill:
                result['match_method'] = "EMBEDDING"
                result['matched_skill'] = matched_skill
                result['embedding_matches'] = embedding_matches
                result['skill_details'] = get_skill_full_details(db, matched_skill.skill_id)
                return result
    
    # ========================================================================
    # STEP 4: NOT FOUND
    # ========================================================================
    result['match_method'] = "NOT_FOUND"
    result['embedding_matches'] = embedding_matches  # Include even if below threshold
    return result


def get_skill_full_details(db: Session, skill_id: int) -> Dict[str, Any]:
    """
    Get full skill details including category and subcategory.
    
    Returns:
        Dictionary with: skill_id, skill_name, category_id, category_name,
                        subcategory_id, subcategory_name
    """
    # Query skill with joined category and subcategory
    result = db.query(
        Skill.skill_id,
        Skill.skill_name,
        SkillSubcategory.subcategory_id,
        SkillSubcategory.subcategory_name,
        SkillCategory.category_id,
        SkillCategory.category_name
    ).join(
        SkillSubcategory, Skill.subcategory_id == SkillSubcategory.subcategory_id
    ).join(
        SkillCategory, SkillSubcategory.category_id == SkillCategory.category_id
    ).filter(
        Skill.skill_id == skill_id
    ).first()
    
    if not result:
        return None
    
    return {
        'skill_id': result[0],
        'skill_name': result[1],
        'subcategory_id': result[2],
        'subcategory_name': result[3],
        'category_id': result[4],
        'category_name': result[5]
    }


def find_similar_skills_via_embedding(
    db: Session,
    embedding_provider,
    normalized_input: str,
    top_k: int = 5,
    model_name: str = "text-embedding-3-small"
) -> List[Dict[str, Any]]:
    """
    Find similar skills using embedding-based matching.
    
    Args:
        db: Database session
        embedding_provider: Embedding provider instance
        normalized_input: Already normalized skill name
        top_k: Number of top matches to return
        model_name: Model name used for embeddings
        
    Returns:
        List of match dictionaries with keys:
            - skill_id
            - skill_name
            - distance (cosine distance from pgvector)
            - similarity (converted from distance, 0-1)
            - confidence (percentage string)
            - match_label (EXACT/HIGH/MEDIUM/LOW/NO_MATCH)
    """
    # Step 1: Generate embedding for input skill
    try:
        input_embedding = embedding_provider.embed(normalized_input)
    except Exception as e:
        print(f"  ⚠️  ERROR: Failed to generate embedding: {e}")
        return []
    
    # Step 2: Query skill_embeddings for nearest neighbors using pgvector
    query = text("""
        SELECT 
            se.skill_id,
            s.skill_name,
            se.embedding <=> CAST(:embedding AS vector) AS distance
        FROM skill_embeddings se
        JOIN skills s ON se.skill_id = s.skill_id
        WHERE se.model_name = :model_name
        ORDER BY distance ASC
        LIMIT :top_k
    """)
    
    try:
        result = db.execute(
            query,
            {
                "embedding": input_embedding,
                "model_name": model_name,
                "top_k": top_k
            }
        )
        rows = result.fetchall()
    except Exception as e:
        print(f"  ⚠️  ERROR: Database query failed: {e}")
        return []
    
    # Step 3: Process results
    matches = []
    for row in rows:
        skill_id = row[0]
        skill_name = row[1]
        distance = float(row[2])
        
        # Convert distance to similarity
        similarity = cosine_distance_to_similarity(distance)
        
        # Classify match
        match_label = classify_match(similarity)
        
        matches.append({
            'skill_id': skill_id,
            'skill_name': skill_name,
            'distance': distance,
            'similarity': similarity,
            'confidence': format_percentage(similarity),
            'match_label': match_label
        })
    
    return matches


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def print_header():
    """Print script header."""
    print("=" * 100)
    print("EMBEDDING-BASED SKILL MATCHING TEST")
    print("=" * 100)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Skills Count: {len(TEST_SKILLS)}")
    print("=" * 100)
    print()


def print_match_result(resolution_result: Dict[str, Any], index: int, total: int):
    """Print formatted match results following the actual workflow."""
    input_skill = resolution_result['input_skill']
    normalized = resolution_result['normalized_input']
    match_method = resolution_result['match_method']
    skill_details = resolution_result['skill_details']
    
    print(f"\n{'='*100}")
    print(f"[{index}/{total}] INPUT SKILL: '{input_skill}'")
    print(f"{'='*100}")
    print(f"Normalized: '{normalized}'")
    print()
    
    # Show workflow steps
    print("Resolution Workflow:")
    print(f"  1️⃣  Exact Match (skill_name_normalized)...  ", end="")
    if match_method == "EXACT":
        print("✅ FOUND")
    else:
        print("❌ Not found")
    
    print(f"  2️⃣  Alias Match (skill_aliases)...          ", end="")
    if match_method == "ALIAS":
        alias_name = resolution_result.get('alias_matched', '')
        print(f"✅ FOUND (matched alias: '{alias_name}')")
    else:
        print("❌ Not found")
    
    print(f"  3️⃣  Embedding Match (semantic search)...   ", end="")
    if match_method == "EMBEDDING":
        print("✅ FOUND")
    elif match_method == "NOT_FOUND":
        print("❌ Not found")
    else:
        print("⏭️  Skipped (already matched)")
    
    print()
    print("-" * 100)
    
    # Show final result
    if match_method == "NOT_FOUND":
        print("❌ NO MATCH FOUND")
        
        # Show embedding candidates if any
        embedding_matches = resolution_result.get('embedding_matches', [])
        if embedding_matches:
            print("\n🔍 Top embedding candidates (below threshold):")
            print(f"  {'Rank':<6} {'Skill Name':<35} {'Similarity':<12} {'Match Label':<12}")
            print(f"  {'-'*6} {'-'*35} {'-'*12} {'-'*12}")
            for rank, match in enumerate(embedding_matches[:3], 1):
                print(f"  {rank:<6} {match['skill_name']:<35} {match['similarity']:<12.4f} {match['match_label']}")
        
        return
    
    # Show matched skill details
    print(f"✅ MATCHED via {match_method}")
    print()
    print("Matched Skill Details:")
    print(f"  Skill ID:         {skill_details['skill_id']}")
    print(f"  Skill Name:       {skill_details['skill_name']}")
    print(f"  Category:         {skill_details['category_name']}")
    print(f"  Subcategory:      {skill_details['subcategory_name']}")
    
    # Show embedding candidates if embedding match was used
    if match_method == "EMBEDDING":
        embedding_matches = resolution_result.get('embedding_matches', [])
        if embedding_matches:
            best_match = embedding_matches[0]
            print(f"  Similarity:       {best_match['similarity']:.4f} ({best_match['confidence']})")
            print(f"  Match Quality:    {best_match['match_label']}")
            
            # Show top alternatives
            if len(embedding_matches) > 1:
                print(f"\n  📊 Alternative embedding matches:")
                print(f"     {'Rank':<6} {'Skill Name':<35} {'Similarity':<12} {'Label':<12}")
                print(f"     {'-'*6} {'-'*35} {'-'*12} {'-'*12}")
                for rank, match in enumerate(embedding_matches[1:4], 2):  # Show ranks 2-4
                    print(f"     {rank:<6} {match['skill_name']:<35} {match['similarity']:<12.4f} {match['match_label']}")


def print_summary(all_results: List[Dict[str, Any]]):
    """Print summary statistics."""
    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)
    
    total_tests = len(all_results)
    
    # Count by resolution method
    method_counts = {
        "EXACT": 0,
        "ALIAS": 0,
        "EMBEDDING": 0,
        "NOT_FOUND": 0
    }
    
    # Count embedding match quality (for embedding matches only)
    embedding_label_counts = {
        "EXACT": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "NO_MATCH": 0
    }
    
    for result in all_results:
        method = result['match_method']
        method_counts[method] += 1
        
        if method == "EMBEDDING" and result.get('embedding_matches'):
            best_match = result['embedding_matches'][0]
            embedding_label_counts[best_match['match_label']] += 1
    
    print(f"\nTotal Skills Tested: {total_tests}")
    
    print(f"\nResolution Method Distribution:")
    print(f"  1️⃣  EXACT Match:      {method_counts['EXACT']:3d} ({method_counts['EXACT']/total_tests*100:5.1f}%)")
    print(f"  2️⃣  ALIAS Match:      {method_counts['ALIAS']:3d} ({method_counts['ALIAS']/total_tests*100:5.1f}%)")
    print(f"  3️⃣  EMBEDDING Match:  {method_counts['EMBEDDING']:3d} ({method_counts['EMBEDDING']/total_tests*100:5.1f}%)")
    print(f"  ❌ NOT FOUND:        {method_counts['NOT_FOUND']:3d} ({method_counts['NOT_FOUND']/total_tests*100:5.1f}%)")
    
    if method_counts['EMBEDDING'] > 0:
        print(f"\nEmbedding Match Quality (for {method_counts['EMBEDDING']} embedding matches):")
        print(f"  ✅ EXACT:     {embedding_label_counts['EXACT']:3d}")
        print(f"  🟢 HIGH:      {embedding_label_counts['HIGH']:3d}")
        print(f"  🟡 MEDIUM:    {embedding_label_counts['MEDIUM']:3d}")
        print(f"  🟠 LOW:       {embedding_label_counts['LOW']:3d}")
    
    success_rate = (method_counts['EXACT'] + method_counts['ALIAS'] + method_counts['EMBEDDING']) / total_tests * 100
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({total_tests - method_counts['NOT_FOUND']}/{total_tests} matched)")
    
    print("\n" + "=" * 100)


def export_to_csv(all_results: List[Dict[str, Any]], csv_path: str):
    """Export results to CSV file."""
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'input_skill',
                'normalized_input',
                'match_method',
                'skill_id',
                'skill_name',
                'category_name',
                'subcategory_name',
                'alias_matched',
                'embedding_similarity',
                'embedding_confidence',
                'embedding_label'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in all_results:
                input_skill = result['input_skill']
                normalized = result['normalized_input']
                method = result['match_method']
                skill_details = result.get('skill_details')
                
                row = {
                    'input_skill': input_skill,
                    'normalized_input': normalized,
                    'match_method': method,
                    'skill_id': skill_details['skill_id'] if skill_details else 'N/A',
                    'skill_name': skill_details['skill_name'] if skill_details else 'NOT_FOUND',
                    'category_name': skill_details['category_name'] if skill_details else 'N/A',
                    'subcategory_name': skill_details['subcategory_name'] if skill_details else 'N/A',
                    'alias_matched': result.get('alias_matched', ''),
                    'embedding_similarity': '',
                    'embedding_confidence': '',
                    'embedding_label': ''
                }
                
                # Add embedding details if embedding match
                if method == "EMBEDDING" and result.get('embedding_matches'):
                    best_match = result['embedding_matches'][0]
                    row['embedding_similarity'] = f"{best_match['similarity']:.4f}"
                    row['embedding_confidence'] = best_match['confidence']
                    row['embedding_label'] = best_match['match_label']
                
                writer.writerow(row)
        
        print(f"\n✅ Results exported to: {csv_path}")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to export CSV: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Test embedding-based skill matching against master skills."
    )
    parser.add_argument(
        '--csv',
        type=str,
        help='Export results to CSV file (e.g., results.csv)',
        default=None
    )
    parser.add_argument(
        '--top-k',
        type=int,
        help='Number of top matches to retrieve per skill (default: 5)',
        default=5
    )
    
    args = parser.parse_args()
    
    # Print header
    print_header()
    
    # Initialize database session
    print("Initializing database connection...")
    db = SessionLocal()
    
    try:
        # Initialize embedding provider
        print("Initializing embedding provider...")
        try:
            embedding_provider = create_embedding_provider()
            print("✅ Embedding provider initialized successfully")
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize embedding provider: {e}")
            print("   Make sure OPENAI_API_KEY or AZURE_OPENAI_* environment variables are set.")
            return
        
        # Check if skill_embeddings table has data
        print("\nChecking skill_embeddings table...")
        embedding_count = db.query(SkillEmbedding).count()
        skill_count = db.query(Skill).count()
        
        print(f"  Total master skills: {skill_count}")
        print(f"  Total skill embeddings: {embedding_count}")
        
        if embedding_count == 0:
            print("\n❌ ERROR: No embeddings found in skill_embeddings table!")
            print("   Run the master import first to populate embeddings.")
            return
        
        print(f"\n✅ Ready to test {len(TEST_SKILLS)} skills against {embedding_count} master skill embeddings")
        print(f"   (Retrieving top {args.top_k} matches per skill)\n")
          # Process each test skill
        all_results = []
        
        for index, test_skill in enumerate(TEST_SKILLS, 1):
            resolution_result = resolve_skill_with_full_workflow(
                db=db,
                embedding_provider=embedding_provider,
                raw_skill_name=test_skill,
                top_k=args.top_k
            )
            
            # Store result
            all_results.append(resolution_result)
            
            # Print result
            print_match_result(resolution_result, index, len(TEST_SKILLS))
        
        # Print summary
        print_summary(all_results)
        
        # Export to CSV if requested
        if args.csv:
            export_to_csv(all_results, args.csv)
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
