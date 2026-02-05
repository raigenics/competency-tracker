"""
Enable pgvector extension in Azure PostgreSQL.

Run this script once before creating the skill_embeddings table.
"""
from app.db.session import engine
from sqlalchemy import text

print("Enabling pgvector extension in Azure PostgreSQL...")

try:
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
        
        print("✅ pgvector extension enabled successfully!")
        
        # Verify extension is available
        result = conn.execute(text(
            "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
        )).fetchone()
        
        if result:
            print(f"✅ Extension verified: {result}")
        else:
            print("⚠️ Warning: Extension not found in pg_available_extensions")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nIf you get a permission error, you may need to:")
    print("1. Enable 'vector' in Azure PostgreSQL Server Parameters")
    print("2. Grant extension creation privileges to your user")
    print("3. Or ask your database administrator to run:")
    print("   CREATE EXTENSION IF NOT EXISTS vector;")
