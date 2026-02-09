"""drop_employee_team_and_project_tables

Revision ID: c22a7d6b8419
Revises: c3f8a2b7e9d1
Create Date: 2026-02-09 16:09:50.419013

PURPOSE:
Remove unused employee_team_assignments and employee_project_allocations tables.
These were created for future team history and matrix allocation features but
are not currently used by any code.

TABLES DROPPED:
- employee_project_allocations (dropped first - references employees/projects)
- employee_team_assignments (dropped second - references employees/teams)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c22a7d6b8419'
down_revision: Union[str, None] = 'c3f8a2b7e9d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the unused employee assignment/allocation tables."""
    
    # Drop employee_project_allocations first (has FKs to employees and projects)
    op.drop_index('ix_project_allocations_project_enddate', table_name='employee_project_allocations')
    op.drop_index('ix_project_allocations_employee_project', table_name='employee_project_allocations')
    op.drop_table('employee_project_allocations')
    
    # Drop employee_team_assignments second (has FKs to employees and teams)
    # Note: partial unique index uq_employee_one_active_team is dropped automatically with table
    op.drop_index('ix_team_assignments_team_enddate', table_name='employee_team_assignments')
    op.drop_index('ix_team_assignments_employee_enddate', table_name='employee_team_assignments')
    op.drop_table('employee_team_assignments')


def downgrade() -> None:
    """Re-create the tables exactly as they were defined."""
    
    # Re-create employee_team_assignments
    op.create_table(
        'employee_team_assignments',
        sa.Column('assignment_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.team_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('assignment_id'),
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_assignment_dates_valid')
    )
    op.create_index('ix_team_assignments_employee_enddate', 'employee_team_assignments', 
                    ['employee_id', 'end_date'], unique=False)
    op.create_index('ix_team_assignments_team_enddate', 'employee_team_assignments', 
                    ['team_id', 'end_date'], unique=False)
    # Partial unique index: only one active assignment per employee
    op.execute("""
        CREATE UNIQUE INDEX uq_employee_one_active_team 
        ON employee_team_assignments(employee_id) 
        WHERE end_date IS NULL
    """)
    
    # Re-create employee_project_allocations
    op.create_table(
        'employee_project_allocations',
        sa.Column('allocation_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('allocation_pct', sa.Numeric(5, 2), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('allocation_id'),
        sa.CheckConstraint('allocation_pct >= 0 AND allocation_pct <= 100', name='ck_allocation_pct_range'),
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_allocation_dates_valid')
    )
    op.create_index('ix_project_allocations_employee_project', 'employee_project_allocations', 
                    ['employee_id', 'project_id'], unique=False)
    op.create_index('ix_project_allocations_project_enddate', 'employee_project_allocations', 
                    ['project_id', 'end_date'], unique=False)
