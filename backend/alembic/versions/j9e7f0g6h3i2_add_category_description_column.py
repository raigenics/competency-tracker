"""add_category_description_column

Revision ID: j9e7f0g6h3i2
Revises: i8d6e9f5g2h1
Create Date: 2026-02-22

Adds description column to the skill_categories table.
This column stores an optional description for each category.

Column details:
- description: VARCHAR(500), nullable
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j9e7f0g6h3i2'
down_revision: Union[str, None] = 'i8d6e9f5g2h1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add description column to skill_categories table."""
    op.add_column('skill_categories',
        sa.Column('description', sa.String(500), nullable=True)
    )


def downgrade() -> None:
    """Remove description column from skill_categories table."""
    op.drop_column('skill_categories', 'description')
