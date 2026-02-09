"""normalize_employee_org_add_team_history

Revision ID: c3f8a2b7e9d1
Revises: fa8ae91de57d
Create Date: 2026-02-09

NORMALIZATION MIGRATION - Employee Organizational Structure
============================================================

This migration normalizes the Employee table by:
1. Creating employee_team_assignments table for team history
2. Creating employee_project_allocations table for matrix allocations
3. Removing denormalized columns (sub_segment_id, project_id) from employees
4. Keeping team_id as "current team" for performance (HYBRID pattern)

DESIGN DECISIONS:
-----------------
Pattern: HYBRID (keep employees.team_id)
- Rationale: Codebase heavily relies on Employee.team_id for queries and RBAC filtering
- team_id remains as "current team" FK
- employee_team_assignments is source-of-truth for history
- Consistency: team_id MUST match the active assignment (end_date IS NULL)

Dropped Columns:
- employees.sub_segment_id -> Derived via: team -> project -> sub_segment
- employees.project_id -> Derived via: team -> project

New Tables:
- employee_team_assignments: Tracks team membership over time
- employee_project_allocations: Tracks project allocation % over time

Constraints:
- Partial unique index on employee_team_assignments(employee_id) WHERE end_date IS NULL
  Ensures only one active team assignment per employee
- Check constraint on allocation_pct between 0 and 100

HOW TO GET CURRENT TEAM:
------------------------
SELECT * FROM employee_team_assignments 
WHERE employee_id = ? AND end_date IS NULL;

Or use employees.team_id for performance (MUST be kept in sync).

DOWNGRADE WARNING:
------------------
Downgrade will re-add project_id and sub_segment_id as NULLABLE.
History data in assignment tables will be LOST if tables are dropped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c3f8a2b7e9d1'
down_revision: Union[str, None] = 'fa8ae91de57d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Normalize employee org structure:
    1. Create assignment/allocation tables
    2. Backfill team assignments from existing data
    3. Drop denormalized columns (project_id, sub_segment_id)
    """
    conn = op.get_bind()
    
    # ===========================================================================
    # STEP 1: Create employee_team_assignments table
    # ===========================================================================
    op.create_table(
        'employee_team_assignments',
        sa.Column('assignment_id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),  # NULL = active assignment
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('assignment_id'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.team_id'], ondelete='CASCADE'),
        # Ensure end_date >= start_date when end_date is not null
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_assignment_dates_valid')
    )
    
    # Indexes for common queries
    op.create_index('ix_team_assignments_employee_enddate', 'employee_team_assignments', 
                    ['employee_id', 'end_date'], unique=False)
    op.create_index('ix_team_assignments_team_enddate', 'employee_team_assignments', 
                    ['team_id', 'end_date'], unique=False)
    
    # Partial unique index: enforce only ONE active assignment per employee
    # PostgreSQL-specific: partial index with WHERE clause
    conn.execute(text("""
        CREATE UNIQUE INDEX uq_employee_one_active_team 
        ON employee_team_assignments(employee_id) 
        WHERE end_date IS NULL
    """))
    
    # ===========================================================================
    # STEP 2: Create employee_project_allocations table
    # ===========================================================================
    op.create_table(
        'employee_project_allocations',
        sa.Column('allocation_id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('allocation_pct', sa.Numeric(5, 2), nullable=False),  # 0.00 to 100.00
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),  # NULL = active allocation
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('allocation_id'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        # Ensure allocation_pct is between 0 and 100
        sa.CheckConstraint('allocation_pct >= 0 AND allocation_pct <= 100', name='ck_allocation_pct_range'),
        # Ensure end_date >= start_date when end_date is not null
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_allocation_dates_valid')
    )
    
    # Indexes for common queries
    op.create_index('ix_project_allocations_employee_project', 'employee_project_allocations', 
                    ['employee_id', 'project_id'], unique=False)
    op.create_index('ix_project_allocations_project_enddate', 'employee_project_allocations', 
                    ['project_id', 'end_date'], unique=False)
    
    # ===========================================================================
    # STEP 3: Backfill team assignments from existing employees.team_id
    # ===========================================================================
    # For each employee with a team_id, create an active assignment
    # Use start_date_of_working if available, else created_at
    conn.execute(text("""
        INSERT INTO employee_team_assignments (employee_id, team_id, start_date, end_date, created_at)
        SELECT 
            employee_id,
            team_id,
            COALESCE(start_date_of_working, created_at::date) as start_date,
            NULL as end_date,
            now() as created_at
        FROM employees
        WHERE team_id IS NOT NULL
          AND deleted_at IS NULL
    """))
    
    # Log backfill count
    result = conn.execute(text("SELECT COUNT(*) FROM employee_team_assignments"))
    backfill_count = result.scalar()
    print(f"[MIGRATION] Backfilled {backfill_count} employee team assignments")
    
    # ===========================================================================
    # STEP 4: Validate backfill - every active employee has exactly 1 assignment
    # ===========================================================================
    # Check for employees without assignments (that have team_id)
    result = conn.execute(text("""
        SELECT COUNT(*) 
        FROM employees e
        WHERE e.team_id IS NOT NULL 
          AND e.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM employee_team_assignments eta 
              WHERE eta.employee_id = e.employee_id AND eta.end_date IS NULL
          )
    """))
    missing_count = result.scalar()
    if missing_count > 0:
        raise Exception(f"[MIGRATION FAILED] {missing_count} employees have team_id but no active assignment")
    
    # Check for duplicate active assignments
    result = conn.execute(text("""
        SELECT employee_id, COUNT(*) as cnt
        FROM employee_team_assignments
        WHERE end_date IS NULL
        GROUP BY employee_id
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    if duplicates:
        raise Exception(f"[MIGRATION FAILED] Duplicate active assignments found: {duplicates}")
    
    print("[MIGRATION] Validation passed: all employees have exactly 1 active team assignment")
    
    # ===========================================================================
    # STEP 5: Drop denormalized columns from employees
    # ===========================================================================
    # Drop FK constraints first
    op.drop_constraint('employees_project_id_fkey', 'employees', type_='foreignkey')
    op.drop_constraint('employees_sub_segment_id_fkey', 'employees', type_='foreignkey')
    
    # Drop the columns
    op.drop_column('employees', 'project_id')
    op.drop_column('employees', 'sub_segment_id')
    
    # ===========================================================================
    # STEP 6: Add updated_at to employees if not exists
    # ===========================================================================
    # Check if column exists
    result = conn.execute(text("""
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = 'employees' AND column_name = 'updated_at'
    """))
    has_updated_at = result.scalar() > 0
    
    if not has_updated_at:
        op.add_column('employees', 
                      sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    
    # ===========================================================================
    # STEP 7: Email uniqueness check (conditional)
    # ===========================================================================
    result = conn.execute(text("""
        SELECT email, COUNT(*) as cnt 
        FROM employees 
        WHERE email IS NOT NULL 
        GROUP BY email 
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    
    if not duplicates:
        # No duplicates - safe to add unique index
        op.create_index('ix_employees_email_unique', 'employees', ['email'], 
                        unique=True, postgresql_where=text('email IS NOT NULL'))
        print("[MIGRATION] Added unique index on employees.email")
    else:
        print(f"[MIGRATION WARNING] Duplicate emails found: {len(duplicates)} groups. "
              "NOT adding unique constraint. Fix duplicates manually.")
    
    print("[MIGRATION] Normalization complete. employees.project_id and sub_segment_id removed.")


def downgrade() -> None:
    """
    Reverse normalization (data loss warning for history).
    Re-add project_id and sub_segment_id as NULLABLE columns.
    """
    conn = op.get_bind()
    
    # ===========================================================================
    # STEP 1: Re-add dropped columns as NULLABLE
    # ===========================================================================
    op.add_column('employees', 
                  sa.Column('project_id', sa.Integer(), nullable=True))
    op.add_column('employees', 
                  sa.Column('sub_segment_id', sa.Integer(), nullable=True))
    
    # ===========================================================================
    # STEP 2: Repopulate from current team assignment (best effort)
    # ===========================================================================
    # Derive project_id and sub_segment_id from team -> project -> sub_segment
    conn.execute(text("""
        UPDATE employees e
        SET 
            project_id = t.project_id,
            sub_segment_id = p.sub_segment_id
        FROM teams t
        JOIN projects p ON t.project_id = p.project_id
        WHERE e.team_id = t.team_id
    """))
    
    # ===========================================================================
    # STEP 3: Re-add FK constraints (nullable, so no enforcement issue)
    # ===========================================================================
    op.create_foreign_key(
        'employees_project_id_fkey', 'employees', 'projects',
        ['project_id'], ['project_id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'employees_sub_segment_id_fkey', 'employees', 'sub_segments',
        ['sub_segment_id'], ['sub_segment_id'], ondelete='CASCADE'
    )
    
    # ===========================================================================
    # STEP 4: Drop unique email index if it was added
    # ===========================================================================
    try:
        op.drop_index('ix_employees_email_unique', 'employees')
    except Exception:
        pass  # Index may not exist
    
    # ===========================================================================
    # STEP 5: Drop updated_at if we added it (skip if user data exists)
    # ===========================================================================
    # Note: We keep updated_at since it's useful and dropping could lose data
    
    # ===========================================================================
    # STEP 6: Drop new tables (WARNING: HISTORY LOSS)
    # ===========================================================================
    print("[DOWNGRADE WARNING] Dropping employee_team_assignments - history will be LOST")
    print("[DOWNGRADE WARNING] Dropping employee_project_allocations - allocations will be LOST")
    
    op.drop_index('ix_project_allocations_project_enddate', 'employee_project_allocations')
    op.drop_index('ix_project_allocations_employee_project', 'employee_project_allocations')
    op.drop_table('employee_project_allocations')
    
    # Drop partial unique index first
    conn.execute(text("DROP INDEX IF EXISTS uq_employee_one_active_team"))
    op.drop_index('ix_team_assignments_team_enddate', 'employee_team_assignments')
    op.drop_index('ix_team_assignments_employee_enddate', 'employee_team_assignments')
    op.drop_table('employee_team_assignments')
    
    print("[DOWNGRADE] Complete. Denormalized columns restored, history tables dropped.")
