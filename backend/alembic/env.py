"""
Alembic environment configuration for Competency Tracker.

This module configures Alembic to work with our SQLAlchemy models
and Azure PostgreSQL database with pgvector support.
"""
from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Base and all models to ensure they're registered
from app.db.base import Base

# Import all models to register them with Base.metadata
# This ensures Alembic can detect all tables for autogenerate
from app.models.sub_segment import SubSegment
from app.models.project import Project
from app.models.team import Team
from app.models.category import SkillCategory
from app.models.subcategory import SkillSubcategory
from app.models.proficiency import ProficiencyLevel
from app.models.role import Role
from app.models.skill import Skill
from app.models.employee import Employee
from app.models.employee_skill import EmployeeSkill
from app.models.skill_history import EmployeeSkillHistory, ProficiencyChangeHistory
from app.models.raw_skill_input import RawSkillInput
from app.models.skill_alias import SkillAlias
from app.models.skill_embedding import SkillEmbedding

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from environment variable
# This allows the same DATABASE_URL to be used for both app and migrations
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/competency_tracker"
)
config.set_main_option("sqlalchemy.url", database_url)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Compare types to detect column type changes
        compare_type=True,
        # Compare server defaults
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare types to detect column type changes
            compare_type=True,
            # Compare server defaults
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
