"""
Create skill_embeddings table in Azure PostgreSQL.

This script creates ONLY the skill_embeddings table.
Run this after enabling the pgvector extension.
"""
from app.db.session import engine
from app.db.base import Base
from app.models.skill_embedding import SkillEmbedding
from sqlalchemy import inspect

print("=" * 70)
print("CREATING skill_embeddings TABLE IN AZURE POSTGRESQL")
print("=" * 70)

try:
    # Check if pgvector extension is enabled
    print("\n1. Checking pgvector extension...")
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT extname FROM pg_extension WHERE extname = 'vector';"
        )).fetchone()
        
        if result:
            print("   ✅ pgvector extension is enabled")
        else:
            print("   ❌ pgvector extension NOT enabled!")
            print("   Run: python enable_pgvector.py first")
            exit(1)
    
    # Check if table already exists
    print("\n2. Checking if skill_embeddings table exists...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if 'skill_embeddings' in existing_tables:
        print("   ⚠️  skill_embeddings table already exists")
        print("   Skipping creation...")
    else:
        print("   ℹ️  skill_embeddings table does not exist")
        
        # Create only the skill_embeddings table
        print("\n3. Creating skill_embeddings table...")
        SkillEmbedding.__table__.create(bind=engine, checkfirst=True)
        print("   ✅ skill_embeddings table created successfully!")
    
    # Verify table structure
    print("\n4. Verifying table structure...")
    columns = inspector.get_columns('skill_embeddings')
    
    print("   Columns in skill_embeddings:")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        print(f"      • {col['name']:<20} {str(col['type']):<20} {nullable}")
    
    # Check foreign keys
    foreign_keys = inspector.get_foreign_keys('skill_embeddings')
    print("\n   Foreign Keys:")
    for fk in foreign_keys:
        print(f"      • {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}")
        if 'ondelete' in fk['options']:
            print(f"        ON DELETE: {fk['options']['ondelete']}")
    
    print("\n" + "=" * 70)
    print("✅ TABLE CREATION COMPLETE!")
    print("=" * 70)
    print("\nYou can now start storing skill embeddings:")
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
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\nTroubleshooting:")
    print("1. Ensure pgvector extension is enabled (run enable_pgvector.py)")
    print("2. Check your database connection in .env file")
    print("3. Verify you have CREATE TABLE privileges")
    print("4. Ensure skills table exists (it's required for foreign key)")
