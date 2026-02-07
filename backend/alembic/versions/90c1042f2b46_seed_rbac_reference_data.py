"""seed_rbac_reference_data

Revision ID: 90c1042f2b46
Revises: 4ab651c97862
Create Date: 2026-02-07 18:10:37.263757

Seeds RBAC reference data:
- auth_scope_types: GLOBAL, SEGMENT, SUB_SEGMENT, PROJECT, TEAM, EMPLOYEE
- auth_roles: SUPER_ADMIN, SEGMENT_HEAD, SUBSEGMENT_HEAD, PROJECT_MANAGER, TEAM_LEAD, TEAM_MEMBER

Idempotent: Uses ON CONFLICT DO NOTHING to prevent duplicates.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '90c1042f2b46'
down_revision: Union[str, None] = '4ab651c97862'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed RBAC reference data."""
    conn = op.get_bind()
    
    # Seed auth_scope_types (idempotent - only insert if not exists)
    scope_types_data = [
        (1, 'GLOBAL', 'Global access across all organizational units'),
        (2, 'SEGMENT', 'Segment-level access'),
        (3, 'SUB_SEGMENT', 'Sub-segment-level access'),
        (4, 'PROJECT', 'Project-level access'),
        (5, 'TEAM', 'Team-level access'),
        (6, 'EMPLOYEE', 'Individual employee-level access'),
    ]
    
    for scope_type_id, code, description in scope_types_data:
        conn.execute(text("""
            INSERT INTO auth_scope_types (scope_type_id, scope_type_code, description)
            VALUES (:id, :code, :desc)
            ON CONFLICT (scope_type_code) DO NOTHING
        """), {"id": scope_type_id, "code": code, "desc": description})
    
    # Seed auth_roles (idempotent - only insert if not exists)
    roles_data = [
        (1, 'SUPER_ADMIN', 'Super Administrator', 'Full system access across all organizational units', 1),
        (2, 'SEGMENT_HEAD', 'Segment Head', 'Manages an entire business segment', 2),
        (3, 'SUBSEGMENT_HEAD', 'Sub-Segment Head', 'Manages a sub-segment within a segment', 3),
        (4, 'PROJECT_MANAGER', 'Project Manager', 'Manages a specific project', 4),
        (5, 'TEAM_LEAD', 'Team Lead', 'Leads a team within a project or organization', 5),
        (6, 'TEAM_MEMBER', 'Team Member', 'Individual contributor assigned to specific employee', 6),
    ]
    
    for role_id, code, name, description, level in roles_data:
        conn.execute(text("""
            INSERT INTO auth_roles (role_id, role_code, role_name, description, level_rank)
            VALUES (:id, :code, :name, :desc, :level)
            ON CONFLICT (role_code) DO NOTHING
        """), {"id": role_id, "code": code, "name": name, "desc": description, "level": level})


def downgrade() -> None:
    """Remove seeded RBAC reference data (only if not referenced)."""
    conn = op.get_bind()
    
    # Delete only the seeded roles (if not in use)
    conn.execute(text("""
        DELETE FROM auth_roles 
        WHERE role_code IN ('SUPER_ADMIN', 'SEGMENT_HEAD', 'SUBSEGMENT_HEAD', 
                           'PROJECT_MANAGER', 'TEAM_LEAD', 'TEAM_MEMBER')
        AND NOT EXISTS (
            SELECT 1 FROM auth_user_scope_roles 
            WHERE auth_user_scope_roles.role_id = auth_roles.role_id
        )
    """))
    
    # Delete only the seeded scope types (if not in use)
    conn.execute(text("""
        DELETE FROM auth_scope_types 
        WHERE scope_type_code IN ('PROJECT', 'TEAM', 'EMPLOYEE')
        AND NOT EXISTS (
            SELECT 1 FROM auth_user_scope_roles 
            WHERE auth_user_scope_roles.scope_type_id = auth_scope_types.scope_type_id
        )
    """))

