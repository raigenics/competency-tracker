"""
Database initialization and table creation.
"""
import logging
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import engine

# Import all models to ensure they are registered with Base.metadata
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
from app.models.skill_embedding import SkillEmbedding

logger = logging.getLogger(__name__)


def create_all_tables():
    """
    Create all database tables.
    
    This function creates all tables in the correct order to handle foreign key constraints.
    Master/dimension tables are created first, followed by fact tables.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize proficiency levels if they don't exist
        _initialize_proficiency_levels()
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def drop_all_tables():
    """
    Drop all database tables.
    
    WARNING: This will delete all data! Use only for development/testing.
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        raise


def clear_all_data():
    """
    Clear all data from database tables without dropping the table structure.
    Useful for resetting data while preserving schema and proficiency levels.
    """
    from app.db.session import SessionLocal
    
    try:
        logger.info("Clearing all data from database tables...")
        db = SessionLocal()
        
        # Delete in proper order to respect foreign key constraints
        # Delete fact tables first
        db.query(EmployeeSkill).delete()
        logger.info("Cleared employee skills")
        
        db.query(Employee).delete()
        logger.info("Cleared employees")
        
        # Delete master tables
        db.query(Skill).delete()
        db.query(SkillSubcategory).delete()
        db.query(SkillCategory).delete()
        db.query(Team).delete()
        db.query(Project).delete()
        db.query(SubSegment).delete()
        logger.info("Cleared master data")
        
        # Note: We keep ProficiencyLevel as it's static reference data
        
        db.commit()
        db.close()
        logger.info("All data cleared successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Error clearing database data: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise


def clear_fact_tables_only():
    """
    Clear only fact tables (employees, employee_skills) preserving all master data.
    This is what the Excel import service does before importing new data.
    """
    from app.db.session import SessionLocal
    
    try:
        logger.info("Clearing fact tables only...")
        db = SessionLocal()
        
        # Delete fact tables only
        db.query(EmployeeSkill).delete()
        logger.info("Cleared employee skills")
        
        db.query(Employee).delete()
        logger.info("Cleared employees")
        
        db.commit()
        db.close()
        logger.info("Fact tables cleared successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Error clearing fact tables: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise


def reset_database():
    """
    Complete database reset - drop all tables and recreate with proficiency levels.
    WARNING: This will delete ALL data and recreate the database from scratch.
    """
    try:
        logger.warning("Performing complete database reset...")
        drop_all_tables()
        create_all_tables()
        logger.info("Database reset completed successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Error during database reset: {str(e)}")
        raise


def _initialize_proficiency_levels():
    """
    Initialize default proficiency levels if they don't exist.
    Uses the Dreyfus Model of Skill Acquisition (5 levels).
    """
    from app.db.session import SessionLocal
    
    # Dreyfus Model of Skill Acquisition (5 levels)
    default_levels = [
        {"proficiency_level_id": 1, "level_name": "Novice", "level_description": "Rigid adherence to rules or plans, little situational perception"},
        {"proficiency_level_id": 2, "level_name": "Advanced Beginner", "level_description": "Slight situational perception, all attributes treated separately"},
        {"proficiency_level_id": 3, "level_name": "Competent", "level_description": "Coping with crowdedness, sees actions at least partially in terms of goals"},
        {"proficiency_level_id": 4, "level_name": "Proficient", "level_description": "Sees situations holistically, priorities by importance"},
        {"proficiency_level_id": 5, "level_name": "Expert", "level_description": "Intuitive grasp of situations, analytical approach only in novel situations"}
    ]
    
    db = SessionLocal()
    try:
        # Check if proficiency levels already exist
        existing_count = db.query(ProficiencyLevel).count()
        if existing_count == 0:
            logger.info("Initializing default proficiency levels (Dreyfus Model)...")
            for level_data in default_levels:
                level = ProficiencyLevel(**level_data)
                db.add(level)
            
            db.commit()
            logger.info(f"Initialized {len(default_levels)} proficiency levels")
        else:
            # Update existing levels to new Dreyfus model (without deleting due to foreign keys)
            logger.info(f"Checking proficiency levels against Dreyfus Model ({existing_count} existing levels found)")
            
            # Instead of deleting, update or create each level individually
            for level_data in default_levels:
                existing_level = db.query(ProficiencyLevel).filter(
                    ProficiencyLevel.proficiency_level_id == level_data['proficiency_level_id']
                ).first()
                
                if existing_level:
                    # Update existing level
                    existing_level.level_name = level_data['level_name']
                    existing_level.level_description = level_data['level_description']
                else:
                    # Create new level
                    level = ProficiencyLevel(**level_data)
                    db.add(level)
            
            db.commit()
            logger.info(f"Verified/updated proficiency levels to match Dreyfus Model")
            
    except SQLAlchemyError as e:
        logger.error(f"Error initializing proficiency levels: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def setup_initial_data():
    """
    Setup initial data for a fresh database installation.
    
    This function ensures that essential master data is available
    for the application to function properly.
    """
    logger.info("Setting up initial data...")
    
    try:
        # Initialize proficiency levels (required for the system to work)
        _initialize_proficiency_levels()
        
        logger.info("Initial data setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up initial data: {str(e)}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create all tables
    create_all_tables()
    print("Database initialization completed!")
