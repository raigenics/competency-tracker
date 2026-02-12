"""add_soft_delete_columns_to_master_tables

Revision ID: f5a3b6c2d9e8
Revises: e4a7b2c8d1f5
Create Date: 2026-02-11

Adds soft-delete audit columns (deleted_at, deleted_by) to master/dimension tables:
- segments
- sub_segments
- projects
- teams
- roles
- skill_categories
- skill_subcategories
- skills

These columns enable soft-delete functionality:
- deleted_at: NULL = active record, timestamp = when record was soft-deleted
- deleted_by: NULL = active record, string = who soft-deleted the record

Migration strategy:
1. Add columns as nullable (they should remain nullable for soft-delete semantics)
2. Add indexes on deleted_at for query filtering (WHERE deleted_at IS NULL)
3. Add indexes on deleted_by for audit queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a3b6c2d9e8'
down_revision: Union[str, None] = 'e4a7b2c8d1f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# All master tables that need soft-delete columns
MASTER_TABLES = [
    'segments',
    'sub_segments',
    'projects', 
    'teams',
    'roles',
    'skill_categories',
    'skill_subcategories',
    'skills'
]


def upgrade() -> None:
    """Add soft-delete columns (deleted_at, deleted_by) to master tables."""
    
    for table in MASTER_TABLES:
        # Add deleted_at column (nullable - NULL means record is active)
        op.add_column(table,
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        # Add deleted_by column (nullable - NULL means record is active)
        op.add_column(table,
            sa.Column('deleted_by', sa.String(100), nullable=True)
        )
        
        # Add indexes for efficient filtering and audit queries
        # Index on deleted_at is crucial for queries like: WHERE deleted_at IS NULL
        op.create_index(f'ix_{table}_deleted_at', table, ['deleted_at'], unique=False)
        op.create_index(f'ix_{table}_deleted_by', table, ['deleted_by'], unique=False)


def downgrade() -> None:
    """Remove soft-delete columns from master tables."""
    
    for table in MASTER_TABLES:
        # Drop indexes first
        op.drop_index(f'ix_{table}_deleted_at', table_name=table)
        op.drop_index(f'ix_{table}_deleted_by', table_name=table)
        # Drop columns
        op.drop_column(table, 'deleted_at')
        op.drop_column(table, 'deleted_by')
