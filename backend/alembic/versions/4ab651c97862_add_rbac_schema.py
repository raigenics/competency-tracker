"""add_rbac_schema

RBAC (Role-Based Access Control) Database Schema - Phase 0

PURPOSE:
Creates the complete RBAC database foundation:
- User authentication identities
- Role and permission structure
- Scoped role assignments (global to employee-level)
- Audit logging

SCOPE:
Database schema ONLY. No application logic, APIs, or services.
All tables are additive - NO modifications to existing tables.

TABLES CREATED:
1. users - Authentication identities
2. user_employee_link - Optional user↔employee mapping
3. auth_roles - Authorization roles (SUPER_ADMIN, SEGMENT_HEAD, etc.)
4. auth_permissions - Granular permissions (future-proofing)
5. auth_role_permissions - Role↔permission junction
6. auth_scope_types - Scope level definitions (GLOBAL, SEGMENT, etc.)
7. auth_user_scope_roles - Core RBAC assignment table
8. auth_audit_log - Security audit trail

Revision ID: 4ab651c97862
Revises: beffee7d4d78
Create Date: 2026-02-07 14:20:05.380935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ab651c97862'
down_revision: Union[str, None] = 'beffee7d4d78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create RBAC schema tables.
    
    Order matters due to foreign key dependencies:
    1. users (independent)
    2. user_employee_link (depends on users, employees)
    3. auth_roles, auth_permissions, auth_scope_types (independent)
    4. auth_role_permissions (depends on roles, permissions)
    5. auth_user_scope_roles (depends on users, roles, scope_types)
    6. auth_audit_log (depends on users)
    """
    
    # ==========================================
    # TABLE 1: users
    # Authentication identity (login account)
    # ==========================================
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    
    # ==========================================
    # TABLE 2: user_employee_link
    # Optional 1:1 mapping between User and Employee
    # ==========================================
    op.create_table(
        'user_employee_link',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('employee_id', name='uq_user_employee_link_employee_id')
    )
    op.create_index(op.f('ix_user_employee_link_user_id'), 'user_employee_link', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_employee_link_employee_id'), 'user_employee_link', ['employee_id'], unique=True)
    
    # ==========================================
    # TABLE 3: auth_roles
    # Authorization role definitions
    # ==========================================
    op.create_table(
        'auth_roles',
        sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_code', sa.String(length=50), nullable=False),
        sa.Column('role_name', sa.String(length=100), nullable=False),
        sa.Column('level_rank', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('role_id'),
        sa.UniqueConstraint('role_code', name='uq_auth_roles_role_code')
    )
    op.create_index(op.f('ix_auth_roles_role_id'), 'auth_roles', ['role_id'], unique=False)
    op.create_index(op.f('ix_auth_roles_role_code'), 'auth_roles', ['role_code'], unique=True)
    
    # ==========================================
    # TABLE 4: auth_permissions
    # Granular permission definitions
    # ==========================================
    op.create_table(
        'auth_permissions',
        sa.Column('permission_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('permission_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('permission_id'),
        sa.UniqueConstraint('permission_code', name='uq_auth_permissions_permission_code')
    )
    op.create_index(op.f('ix_auth_permissions_permission_id'), 'auth_permissions', ['permission_id'], unique=False)
    op.create_index(op.f('ix_auth_permissions_permission_code'), 'auth_permissions', ['permission_code'], unique=True)
    
    # ==========================================
    # TABLE 5: auth_role_permissions
    # Junction table: roles ↔ permissions
    # ==========================================
    op.create_table(
        'auth_role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['auth_roles.role_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['auth_permissions.permission_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )
    
    # ==========================================
    # TABLE 6: auth_scope_types
    # Scope level definitions (GLOBAL, SEGMENT, etc.)
    # ==========================================
    op.create_table(
        'auth_scope_types',
        sa.Column('scope_type_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scope_type_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('scope_type_id'),
        sa.UniqueConstraint('scope_type_code', name='uq_auth_scope_types_scope_type_code')
    )
    op.create_index(op.f('ix_auth_scope_types_scope_type_id'), 'auth_scope_types', ['scope_type_id'], unique=False)
    op.create_index(op.f('ix_auth_scope_types_scope_type_code'), 'auth_scope_types', ['scope_type_code'], unique=True)
    
    # ==========================================
    # TABLE 7: auth_user_scope_roles
    # Core RBAC assignment table
    # ==========================================
    op.create_table(
        'auth_user_scope_roles',
        sa.Column('user_scope_role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('scope_type_id', sa.Integer(), nullable=False),
        sa.Column('scope_id', sa.Integer(), nullable=True),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['auth_roles.role_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['scope_type_id'], ['auth_scope_types.scope_type_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('user_scope_role_id'),
        # Constraint: only one active assignment per user/role/scope combination
        sa.CheckConstraint(
            '(is_active = true AND revoked_at IS NULL) OR (is_active = false AND revoked_at IS NOT NULL)',
            name='chk_active_revoked_consistency'
        )
    )
    op.create_index(op.f('ix_auth_user_scope_roles_user_scope_role_id'), 'auth_user_scope_roles', ['user_scope_role_id'], unique=False)
    op.create_index(op.f('ix_auth_user_scope_roles_user_id'), 'auth_user_scope_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_auth_user_scope_roles_role_id'), 'auth_user_scope_roles', ['role_id'], unique=False)
    op.create_index(op.f('ix_auth_user_scope_roles_scope_type_id'), 'auth_user_scope_roles', ['scope_type_id'], unique=False)
    op.create_index(op.f('ix_auth_user_scope_roles_scope_id'), 'auth_user_scope_roles', ['scope_id'], unique=False)
    op.create_index(op.f('ix_auth_user_scope_roles_revoked_at'), 'auth_user_scope_roles', ['revoked_at'], unique=False)
    op.create_index(op.f('ix_auth_user_scope_roles_is_active'), 'auth_user_scope_roles', ['is_active'], unique=False)
    
    # Unique partial index: only one active assignment per user/role/scope
    op.create_index(
        'idx_active_user_role_scope',
        'auth_user_scope_roles',
        ['user_id', 'role_id', 'scope_type_id', 'scope_id', 'is_active'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )
    
    # ==========================================
    # TABLE 8: auth_audit_log
    # Security audit trail (immutable)
    # ==========================================
    op.create_table(
        'auth_audit_log',
        sa.Column('audit_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('action_code', sa.String(length=100), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('audit_id')
    )
    op.create_index(op.f('ix_auth_audit_log_audit_id'), 'auth_audit_log', ['audit_id'], unique=False)
    op.create_index(op.f('ix_auth_audit_log_actor_user_id'), 'auth_audit_log', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_auth_audit_log_action_code'), 'auth_audit_log', ['action_code'], unique=False)
    op.create_index(op.f('ix_auth_audit_log_target_user_id'), 'auth_audit_log', ['target_user_id'], unique=False)
    op.create_index(op.f('ix_auth_audit_log_created_at'), 'auth_audit_log', ['created_at'], unique=False)


def downgrade() -> None:
    """
    Drop all RBAC tables.
    
    Order matters - drop in reverse of creation to respect FK constraints.
    """
    
    # Drop auth_audit_log
    op.drop_index(op.f('ix_auth_audit_log_created_at'), table_name='auth_audit_log')
    op.drop_index(op.f('ix_auth_audit_log_target_user_id'), table_name='auth_audit_log')
    op.drop_index(op.f('ix_auth_audit_log_action_code'), table_name='auth_audit_log')
    op.drop_index(op.f('ix_auth_audit_log_actor_user_id'), table_name='auth_audit_log')
    op.drop_index(op.f('ix_auth_audit_log_audit_id'), table_name='auth_audit_log')
    op.drop_table('auth_audit_log')
    
    # Drop auth_user_scope_roles
    op.drop_index('idx_active_user_role_scope', table_name='auth_user_scope_roles')
    op.drop_index(op.f('ix_auth_user_scope_roles_is_active'), table_name='auth_user_scope_roles')
    op.drop_index(op.f('ix_auth_user_scope_roles_revoked_at'), table_name='auth_user_scope_roles')
    op.drop_index(op.f('ix_auth_user_scope_roles_scope_id'), table_name='auth_user_scope_roles')
    op.drop_index(op.f('ix_auth_user_scope_roles_scope_type_id'), table_name='auth_user_scope_roles')
    op.drop_index(op.f('ix_auth_user_scope_roles_role_id'), table_name='auth_user_scope_roles')
    op.drop_index(op.f('ix_auth_user_scope_roles_user_id'), table_name='auth_user_scope_roles')
    op.drop_index(op.f('ix_auth_user_scope_roles_user_scope_role_id'), table_name='auth_user_scope_roles')
    op.drop_table('auth_user_scope_roles')
    
    # Drop auth_scope_types
    op.drop_index(op.f('ix_auth_scope_types_scope_type_code'), table_name='auth_scope_types')
    op.drop_index(op.f('ix_auth_scope_types_scope_type_id'), table_name='auth_scope_types')
    op.drop_table('auth_scope_types')
    
    # Drop auth_role_permissions
    op.drop_table('auth_role_permissions')
    
    # Drop auth_permissions
    op.drop_index(op.f('ix_auth_permissions_permission_code'), table_name='auth_permissions')
    op.drop_index(op.f('ix_auth_permissions_permission_id'), table_name='auth_permissions')
    op.drop_table('auth_permissions')
    
    # Drop auth_roles
    op.drop_index(op.f('ix_auth_roles_role_code'), table_name='auth_roles')
    op.drop_index(op.f('ix_auth_roles_role_id'), table_name='auth_roles')
    op.drop_table('auth_roles')
    
    # Drop user_employee_link
    op.drop_index(op.f('ix_user_employee_link_employee_id'), table_name='user_employee_link')
    op.drop_index(op.f('ix_user_employee_link_user_id'), table_name='user_employee_link')
    op.drop_table('user_employee_link')
    
    # Drop users
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_table('users')
