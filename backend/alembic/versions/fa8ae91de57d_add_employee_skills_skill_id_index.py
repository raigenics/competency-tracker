"""add_employee_skills_skill_id_index

Add index on employee_skills.skill_id for performance optimization.

This index improves the performance of EXISTS subqueries used in the
"in-use only" filtering for the Capability Structure taxonomy endpoints:
- GET /skills/capability/categories
- GET /skills/capability/categories/{category_id}/subcategories
- GET /skills/capability/subcategories/{subcategory_id}/skills

The index is also beneficial for any skill-based employee lookups.

Revision ID: fa8ae91de57d
Revises: 422b6eeca905
Create Date: 2026-02-09 13:46:20.040004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa8ae91de57d'
down_revision: Union[str, None] = '422b6eeca905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on employee_skills.skill_id for efficient "in-use" skill lookups
    op.create_index(
        op.f('ix_employee_skills_skill_id'),
        'employee_skills',
        ['skill_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_employee_skills_skill_id'), table_name='employee_skills')
