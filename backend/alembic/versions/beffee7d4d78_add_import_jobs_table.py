"""add_import_jobs_table

Revision ID: beffee7d4d78
Revises: 5b62805d7014
Create Date: 2026-02-06 18:21:14.506147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'beffee7d4d78'
down_revision: Union[str, None] = '5b62805d7014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create import_jobs table for tracking bulk import operations
    op.create_table(
        'import_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('message', sa.String(length=500), nullable=True),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('percent_complete', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('employees_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('employees_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skills_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skills_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index(op.f('ix_import_jobs_id'), 'import_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_import_jobs_job_id'), 'import_jobs', ['job_id'], unique=True)
    op.create_index(op.f('ix_import_jobs_status'), 'import_jobs', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_import_jobs_status'), table_name='import_jobs')
    op.drop_index(op.f('ix_import_jobs_job_id'), table_name='import_jobs')
    op.drop_index(op.f('ix_import_jobs_id'), table_name='import_jobs')
    
    # Drop table
    op.drop_table('import_jobs')
