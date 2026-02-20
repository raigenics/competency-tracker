"""add_job_id_status_to_raw_skill_inputs

Revision ID: i8d6e9f5g2h1
Revises: h7c5d8e4f1g0
Create Date: 2024-02-18

Add columns to raw_skill_inputs table to support the "Resolve Unmatched Skills"
workflow for Employee Bulk Import failures:

Changes:
- job_id: Links raw_skill_input to import job (UUID string)
- status: UNRESOLVED or RESOLVED
- resolved_by: User who resolved the skill
- resolved_at: Timestamp when resolved
- Composite index for job_id + status queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i8d6e9f5g2h1'
down_revision: Union[str, None] = 'h7c5d8e4f1g0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to raw_skill_inputs
    op.add_column('raw_skill_inputs', sa.Column('job_id', sa.String(36), nullable=True))
    op.add_column('raw_skill_inputs', sa.Column('status', sa.String(20), nullable=False, server_default='UNRESOLVED'))
    op.add_column('raw_skill_inputs', sa.Column('resolved_by', sa.String(50), nullable=True))
    op.add_column('raw_skill_inputs', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add indexes
    op.create_index('ix_raw_skill_inputs_job_id', 'raw_skill_inputs', ['job_id'])
    op.create_index('ix_raw_skill_inputs_status', 'raw_skill_inputs', ['status'])
    op.create_index('idx_raw_skills_job_status', 'raw_skill_inputs', ['job_id', 'status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_raw_skills_job_status', table_name='raw_skill_inputs')
    op.drop_index('ix_raw_skill_inputs_status', table_name='raw_skill_inputs')
    op.drop_index('ix_raw_skill_inputs_job_id', table_name='raw_skill_inputs')
    
    # Drop columns
    op.drop_column('raw_skill_inputs', 'resolved_at')
    op.drop_column('raw_skill_inputs', 'resolved_by')
    op.drop_column('raw_skill_inputs', 'status')
    op.drop_column('raw_skill_inputs', 'job_id')
