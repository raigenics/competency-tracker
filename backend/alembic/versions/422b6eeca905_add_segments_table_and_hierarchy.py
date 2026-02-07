"""add_segments_table_and_hierarchy

Revision ID: 422b6eeca905
Revises: 90c1042f2b46
Create Date: 2026-02-07 18:42:33.530304

Adds organizational hierarchy: segments -> sub_segments

Schema changes:
1. Creates new 'segments' table (top-level org unit)
2. Adds nullable FK sub_segments.segment_id -> segments.segment_id
3. Seeds a default "Legacy" segment for existing data
4. Backfills all existing sub_segments to reference the Legacy segment

Design decisions:
- segment_id remains NULLABLE for backward compatibility
  (Existing code may not populate this field; we can make it NOT NULL in a future
   migration once all business logic is updated to handle segments)
- ON DELETE RESTRICT prevents accidental deletion of segments with child sub_segments
- Idempotent: Legacy segment insert uses ON CONFLICT DO NOTHING
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '422b6eeca905'
down_revision: Union[str, None] = '90c1042f2b46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add segments table and establish hierarchy with sub_segments."""
    conn = op.get_bind()
    
    # 1. Create segments table
    op.create_table(
        'segments',
        sa.Column('segment_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('segment_name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('segment_id'),
        sa.UniqueConstraint('segment_name', name='uq_segments_segment_name')
    )
    op.create_index(op.f('ix_segments_segment_id'), 'segments', ['segment_id'], unique=False)
    op.create_index(op.f('ix_segments_segment_name'), 'segments', ['segment_name'], unique=True)
    
    # 2. Seed default "Legacy" segment (idempotent)
    #    This provides a home for all existing sub_segments during migration
    conn.execute(text("""
        INSERT INTO segments (segment_id, segment_name)
        VALUES (1, 'Legacy')
        ON CONFLICT (segment_name) DO NOTHING
    """))
    
    # 2b. Reset the sequence to avoid PK conflicts when inserting new segments
    #     Since we manually set segment_id=1, we need to advance the sequence
    #     so the next auto-generated ID will be 2
    conn.execute(text("SELECT setval('segments_segment_id_seq', 1, true)"))
    
    # 3. Add nullable segment_id FK column to sub_segments
    #    NULL allowed for backward compatibility - existing code may create sub_segments
    #    without specifying a segment. Future migration can enforce NOT NULL once
    #    all business logic is updated.
    op.add_column('sub_segments', 
                  sa.Column('segment_id', sa.Integer(), nullable=True))
    
    # 4. Create foreign key constraint
    #    ON DELETE RESTRICT: Prevents deletion of segments that have child sub_segments
    #    This is safer than CASCADE (which would delete sub_segments) or SET NULL
    #    (which would orphan sub_segments). Admin must reassign or delete sub_segments first.
    op.create_foreign_key(
        'fk_sub_segments_segment_id',
        'sub_segments', 'segments',
        ['segment_id'], ['segment_id'],
        ondelete='RESTRICT'
    )
    
    # 5. Create index on FK column for query performance
    op.create_index(op.f('ix_sub_segments_segment_id'), 
                    'sub_segments', ['segment_id'], unique=False)
    
    # 6. Backfill existing sub_segments to point to Legacy segment
    #    This ensures all existing data has a valid parent in the hierarchy
    conn.execute(text("""
        UPDATE sub_segments
        SET segment_id = 1
        WHERE segment_id IS NULL
    """))


def downgrade() -> None:
    """Remove segments table and hierarchy."""
    # Drop FK constraint and index from sub_segments
    op.drop_index(op.f('ix_sub_segments_segment_id'), table_name='sub_segments')
    op.drop_constraint('fk_sub_segments_segment_id', 'sub_segments', type_='foreignkey')
    
    # Drop segment_id column from sub_segments
    op.drop_column('sub_segments', 'segment_id')
    
    # Drop segments table (includes all data and indexes)
    op.drop_index(op.f('ix_segments_segment_name'), table_name='segments')
    op.drop_index(op.f('ix_segments_segment_id'), table_name='segments')
    op.drop_table('segments')

