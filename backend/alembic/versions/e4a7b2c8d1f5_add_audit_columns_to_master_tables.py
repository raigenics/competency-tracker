"""add_audit_columns_to_master_tables

Revision ID: e4a7b2c8d1f5
Revises: fa8ae91de57d
Create Date: 2026-02-11

Adds audit columns (created_at, created_by) to master/dimension tables:
- segments (already has created_at, only adding created_by)
- sub_segments
- projects
- teams
- roles
- skill_categories
- skill_subcategories
- skills

Migration strategy:
1. Add columns as nullable
2. Backfill existing rows with default values (now() for created_at, 'system' for created_by)
3. Alter columns to NOT NULL
4. Add indexes on created_by and created_at columns
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e4a7b2c8d1f5'
down_revision: Union[str, None] = 'd8f2a1c3b4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that need both created_at and created_by
TABLES_NEEDING_BOTH = [
    'sub_segments',
    'projects', 
    'teams',
    'roles',
    'skill_categories',
    'skill_subcategories',
    'skills'
]

# Table that only needs created_by (already has created_at)
TABLE_NEEDING_CREATED_BY_ONLY = 'segments'


def upgrade() -> None:
    """Add audit columns to master tables with safe backfill."""
    conn = op.get_bind()
    
    # === SEGMENTS TABLE (already has created_at) ===
    # Add created_by as nullable
    op.add_column('segments', 
        sa.Column('created_by', sa.String(100), nullable=True)
    )
    # Backfill existing rows
    conn.execute(text("UPDATE segments SET created_by = 'system' WHERE created_by IS NULL"))
    # Make NOT NULL
    op.alter_column('segments', 'created_by', nullable=False)
    # Add index
    op.create_index('ix_segments_created_by', 'segments', ['created_by'], unique=False)
    
    # === TABLES NEEDING BOTH COLUMNS ===
    for table in TABLES_NEEDING_BOTH:
        # Add created_at as nullable first
        op.add_column(table,
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True)
        )
        # Add created_by as nullable
        op.add_column(table,
            sa.Column('created_by', sa.String(100), nullable=True)
        )
        
        # Backfill existing rows
        conn.execute(text(f"UPDATE {table} SET created_at = now() WHERE created_at IS NULL"))
        conn.execute(text(f"UPDATE {table} SET created_by = 'system' WHERE created_by IS NULL"))
        
        # Alter to NOT NULL with server default for created_at
        op.alter_column(table, 'created_at', 
            nullable=False,
            server_default=sa.text('now()')
        )
        op.alter_column(table, 'created_by', nullable=False)
        
        # Add indexes
        op.create_index(f'ix_{table}_created_at', table, ['created_at'], unique=False)
        op.create_index(f'ix_{table}_created_by', table, ['created_by'], unique=False)


def downgrade() -> None:
    """Remove audit columns from master tables."""
    
    # === SEGMENTS TABLE ===
    op.drop_index('ix_segments_created_by', table_name='segments')
    op.drop_column('segments', 'created_by')
    
    # === TABLES THAT HAD BOTH COLUMNS ADDED ===
    for table in TABLES_NEEDING_BOTH:
        op.drop_index(f'ix_{table}_created_at', table_name=table)
        op.drop_index(f'ix_{table}_created_by', table_name=table)
        op.drop_column(table, 'created_at')
        op.drop_column(table, 'created_by')
