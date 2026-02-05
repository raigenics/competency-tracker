"""
One-command deployment script for skill_embeddings table.

This script:
1. Checks pgvector extension
2. Enables it if needed
3. Creates skill_embeddings table
4. Verifies everything

Usage: python deploy_skill_embeddings.py
"""
from app.db.session import engine
from app.db.base import Base
from app.models.skill_embedding import SkillEmbedding
from sqlalchemy import text, inspect
import sys

def check_and_enable_pgvector():
    """Check if pgvector is enabled, enable if not."""
    print("🔍 Step 1: Checking pgvector extension...")
    
    try:
        with engine.connect() as conn:
            # Check if extension exists
            result = conn.execute(text(
                "SELECT extname FROM pg_extension WHERE extname = 'vector';"
            )).fetchone()
            
            if result:
                print("   ✅ pgvector extension is already enabled")
                return True
            
            # Try to enable it
            print("   ⚙️  Enabling pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("   ✅ pgvector extension enabled successfully!")
            return True
            
    except Exception as e:
        print(f"   ❌ Failed to enable pgvector: {e}")
        print("\n   Please enable it manually:")
        print("   1. Azure Portal → PostgreSQL → Server parameters")
        print("   2. Add 'VECTOR' to azure.extensions")
        print("   3. Or ask DBA to run: CREATE EXTENSION vector;")
        return False

def create_table():
    """Create skill_embeddings table."""
    print("\n🔧 Step 2: Creating skill_embeddings table...")
    
    try:
        inspector = inspect(engine)
        
        # Check if table exists
        if 'skill_embeddings' in inspector.get_table_names():
            print("   ℹ️  Table already exists, skipping creation")
            return True
        
        # Create table
        SkillEmbedding.__table__.create(bind=engine, checkfirst=True)
        print("   ✅ skill_embeddings table created successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create table: {e}")
        return False

def verify_deployment():
    """Verify table structure."""
    print("\n✔️  Step 3: Verifying deployment...")
    
    try:
        inspector = inspect(engine)
        
        # Check table exists
        if 'skill_embeddings' not in inspector.get_table_names():
            print("   ❌ Table not found!")
            return False
        
        # Check columns
        columns = inspector.get_columns('skill_embeddings')
        column_names = [col['name'] for col in columns]
        
        required_columns = ['skill_id', 'model_name', 'embedding', 'embedding_version', 'updated_at']
        missing = [col for col in required_columns if col not in column_names]
        
        if missing:
            print(f"   ❌ Missing columns: {missing}")
            return False
        
        print("   ✅ All columns present:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"      • {col['name']:<20} {str(col['type']):<20} {nullable}")
        
        # Check foreign keys
        foreign_keys = inspector.get_foreign_keys('skill_embeddings')
        if foreign_keys:
            print("\n   ✅ Foreign keys configured:")
            for fk in foreign_keys:
                print(f"      • {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False

def main():
    """Run deployment."""
    print("=" * 70)
    print("SKILL EMBEDDINGS TABLE DEPLOYMENT")
    print("=" * 70)
    
    # Step 1: Enable pgvector
    if not check_and_enable_pgvector():
        print("\n❌ Deployment failed: Could not enable pgvector")
        sys.exit(1)
    
    # Step 2: Create table
    if not create_table():
        print("\n❌ Deployment failed: Could not create table")
        sys.exit(1)
    
    # Step 3: Verify
    if not verify_deployment():
        print("\n❌ Deployment failed: Verification failed")
        sys.exit(1)
    
    # Success!
    print("\n" + "=" * 70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 70)
    print("\n🎉 The skill_embeddings table is ready to use!")
    print("\nNext steps:")
    print("  • Start storing embeddings: See SKILL_EMBEDDINGS_IMPLEMENTATION.md")
    print("  • Test with: python -c 'from app.models import SkillEmbedding'")
    print("\nExample usage:")
    print("""
    from app.models import SkillEmbedding
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    embedding = SkillEmbedding(
        skill_id=1,
        model_name='text-embedding-ada-002',
        embedding=[0.1, 0.2, ...],  # 1536 floats
        embedding_version='v1'
    )
    db.add(embedding)
    db.commit()
    """)

if __name__ == "__main__":
    main()
