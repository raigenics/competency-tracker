"""add_fullname_columns_to_org_tables

Revision ID: l1g9h2i6j4k5
Revises: k0f8g1h4i5j3
Create Date: 2026-02-23

Adds fullname columns to organizational hierarchy tables:
- segments: segment_fullname
- sub_segments: sub_segment_fullname
- projects: project_fullname
- teams: team_fullname

All columns are VARCHAR, nullable.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'l1g9h2i6j4k5'
down_revision: Union[str, None] = 'k0f8g1h4i5j3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add fullname columns to organizational hierarchy tables."""
    op.add_column('segments',
        sa.Column('segment_fullname', sa.String(), nullable=True)
    )
    op.add_column('sub_segments',
        sa.Column('sub_segment_fullname', sa.String(), nullable=True)
    )
    op.add_column('projects',
        sa.Column('project_fullname', sa.String(), nullable=True)
    )
    op.add_column('teams',
        sa.Column('team_fullname', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Remove fullname columns from organizational hierarchy tables."""
    op.drop_column('teams', 'team_fullname')
    op.drop_column('projects', 'project_fullname')
    op.drop_column('sub_segments', 'sub_segment_fullname')
    op.drop_column('segments', 'segment_fullname')
