"""add_role_alias_column

Revision ID: g6b4c7d3e0f9
Revises: fa8ae91de57d
Create Date: 2026-02-17

Adds role_alias column to the roles table.
This column stores comma-separated alias names for each role.

Column details:
- role_alias: Text, nullable, no uniqueness constraint
- Positioned logically after role_name
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g6b4c7d3e0f9'
down_revision: Union[str, None] = 'f5a3b6c2d9e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role_alias column to roles table."""
    op.add_column('roles',
        sa.Column('role_alias', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove role_alias column from roles table."""
    op.drop_column('roles', 'role_alias')
