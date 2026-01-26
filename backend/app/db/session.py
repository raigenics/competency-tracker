"""
Database session configuration and engine setup.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL - PostgreSQL configuration
# Format: postgresql://username:password@host:port/database_name
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/competency_tracker"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    # PostgreSQL-specific optimizations
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    echo=False  # Set to True for development debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session with enhanced error handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Enhanced error logging for PostgreSQL debugging
        logger = logging.getLogger(__name__)
        logger.error(f"Database session error: {str(e)}")
        # If an exception occurred, rollback the transaction
        db.rollback()
        raise
    finally:
        db.close()
