"""add_subcategory_description_column

Revision ID: k0f8g1h4i5j3
Revises: j9e7f0g6h3i2
Create Date: 2026-02-22

Adds description column to the skill_subcategories table.
This column stores an optional description for each subcategory.

Column details:
- description: VARCHAR(500), nullable
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k0f8g1h4i5j3'
down_revision: Union[str, None] = 'j9e7f0g6h3i2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add description column to skill_subcategories table."""
    op.add_column('skill_subcategories',
        sa.Column('description', sa.String(500), nullable=True)
    )


def downgrade() -> None:
    """Remove description column from skill_subcategories table."""
    op.drop_column('skill_subcategories', 'description')
