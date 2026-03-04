"""roles_soft_delete_partial_unique_index

Revision ID: h7c5d8e4f1g0
Revises: g6b4c7d3e0f9
Create Date: 2026-02-17

Replace global UNIQUE index on roles.role_name with a partial unique index
that only enforces uniqueness on ACTIVE roles (deleted_at IS NULL).

This allows soft-deleted role names to be reused when creating new roles.

Changes:
- Drop existing unique index: ix_roles_role_name
- Create partial unique index with SAME name: ix_roles_role_name
  WHERE deleted_at IS NULL
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h7c5d8e4f1g0'
down_revision: Union[str, None] = 'g6b4c7d3e0f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Replace global unique index with partial unique index.
    
    The partial index only enforces uniqueness on active roles (deleted_at IS NULL),
    allowing soft-deleted role names to be reused.
    """
    # Drop the existing global unique index on role_name
    op.execute("DROP INDEX IF EXISTS ix_roles_role_name")
    
    # Create partial unique index for active roles only
    # Uses LOWER() for case-insensitive uniqueness
    # Re-uses same index name to avoid touching other code
    op.execute("""
        CREATE UNIQUE INDEX ix_roles_role_name
        ON roles (LOWER(role_name)) 
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    """
    Restore global unique index.
    
    WARNING: This may fail if there are duplicate role_names among soft-deleted roles.
    """
    # Drop the partial unique index
    op.execute("DROP INDEX IF EXISTS ix_roles_role_name")
    
    # Recreate global unique index (non-partial)
    op.create_index('ix_roles_role_name', 'roles', ['role_name'], unique=True)
