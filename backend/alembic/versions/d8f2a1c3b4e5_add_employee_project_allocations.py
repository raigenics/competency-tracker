"""add_employee_project_allocations

Revision ID: d8f2a1c3b4e5
Revises: c22a7d6b8419
Create Date: 2026-02-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f2a1c3b4e5'
down_revision: Union[str, None] = 'c22a7d6b8419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create employee_project_allocations table
    op.create_table(
        'employee_project_allocations',
        sa.Column('allocation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('allocation_pct', sa.Integer(), nullable=False),
        sa.Column('allocation_type', sa.String(length=30), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('allocation_id'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id']),
        sa.CheckConstraint('allocation_pct >= 0 AND allocation_pct <= 100', name='ck_allocation_pct_range'),
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_end_date_after_start')
    )
    
    # Create indexes
    op.create_index('ix_employee_project_allocations_employee_id', 'employee_project_allocations', ['employee_id'])
    op.create_index('ix_employee_project_allocations_project_id', 'employee_project_allocations', ['project_id'])
    op.create_index('ix_employee_project_allocations_emp_dates', 'employee_project_allocations', ['employee_id', 'start_date', 'end_date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_employee_project_allocations_emp_dates', table_name='employee_project_allocations')
    op.drop_index('ix_employee_project_allocations_project_id', table_name='employee_project_allocations')
    op.drop_index('ix_employee_project_allocations_employee_id', table_name='employee_project_allocations')
    
    # Drop table
    op.drop_table('employee_project_allocations')
