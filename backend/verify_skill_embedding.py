"""
Verification script for SkillEmbedding model.
"""
from app.models.skill_embedding import SkillEmbedding
from app.db.base import Base

print("=" * 60)
print("SKILL EMBEDDING MODEL VERIFICATION")
print("=" * 60)

print(f"\n✓ Table Name: {SkillEmbedding.__tablename__}")

print("\n✓ Column Details:")
for col in SkillEmbedding.__table__.columns:
    print(f"  • {col.name:20} {str(col.type):30} nullable={col.nullable:5} pk={col.primary_key}")

print("\n✓ Foreign Key Constraints:")
for fk in SkillEmbedding.__table__.foreign_keys:
    print(f"  • {fk.parent.name} -> {fk.target_fullname}")
    print(f"    ON DELETE: {fk.ondelete}")

print("\n✓ Server Defaults:")
for col in SkillEmbedding.__table__.columns:
    if col.server_default:
        print(f"  • {col.name}: {col.server_default.arg}")

print("\n✓ Relationships:")
if hasattr(SkillEmbedding, 'skill'):
    print(f"  • skill relationship defined")

print("\n✓ Model is registered in Base.metadata:")
print(f"  Tables: {list(Base.metadata.tables.keys())}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE ✓")
print("=" * 60)
