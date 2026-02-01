"""
Excel reading utility for the Competency Tracking System.
Handles Excel file parsing with data validation and normalization.
"""
import pandas as pd
import logging
from typing import Tuple, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ExcelReaderError(Exception):
    """Custom exception for Excel reading errors."""
    pass


# Excel column to database field mapping
EMPLOYEE_COLUMN_MAPPING = {
    'Employee ID (ZID)': 'zid',
    'Employee Full Name': 'full_name', 
    'Sub-Segment': 'sub_segment',
    'Project': 'project',
    'Team': 'team',
    'Role/Designation': 'role',
    'Start Date of Working': 'start_date_of_working'
}

EMPLOYEE_SKILLS_COLUMN_MAPPING = {
    'Employee ID (ZID)': 'zid',
    'Employee Full Name': 'employee_full_name',  # For validation only
    'Skill Category': 'skill_category',
    'Skill Subcategory': 'skill_subcategory', 
    'Skill Name': 'skill_name',
    'Proficiency': 'proficiency',    'Experience Years': 'years_experience',    'Last Used': 'last_used',  # Changed from last_used_year to last_used
    'Started learning from (Date)': 'started_learning_from',
    'Certification': 'certification',
    'Comment': 'comment'
}

# Required columns for validation
REQUIRED_EMPLOYEE_COLUMNS = [
    'Employee ID (ZID)',
    'Employee Full Name', 
    'Sub-Segment',
    'Project',
    'Team'
]

REQUIRED_EMPLOYEE_SKILLS_COLUMNS = [
    'Employee ID (ZID)',
    'Skill Category',
    'Skill Name',
    'Proficiency'
]


def read_excel(file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read and validate Excel file with employee and skills data.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: employees_df, skills_df
        
    Raises:
        ExcelReaderError: If file reading or validation fails
    """
    logger.info(f"Reading Excel file: {file_path}")
    
    try:
        # Check if file exists
        if not Path(file_path).exists():
            raise ExcelReaderError(f"File not found: {file_path}")
        
        # Read specific sheets by name (more reliable than position)
        try:
            employees_df = pd.read_excel(file_path, sheet_name='Employee')
            skills_df = pd.read_excel(file_path, sheet_name='Employee_Skills')
        except ValueError as e:
            # If named sheets don't exist, try to read first two sheets
            excel_data = pd.read_excel(file_path, sheet_name=None)
            sheet_names = list(excel_data.keys())
            if len(sheet_names) < 2:
                raise ExcelReaderError("Excel file must contain at least 2 sheets")
            
            employees_df = excel_data[sheet_names[0]]
            skills_df = excel_data[sheet_names[1]]
            logger.warning(f"Using sheets by position: '{sheet_names[0]}' and '{sheet_names[1]}'")
        
        logger.info(f"Successfully read Employee sheet ({len(employees_df)} rows) and Skills sheet ({len(skills_df)} rows)")
        
        # Validate and normalize column names
        employees_df = _validate_and_normalize_employees(employees_df)
        skills_df = _validate_and_normalize_skills(skills_df)
        
        return employees_df, skills_df
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        raise ExcelReaderError(f"Failed to read Excel file: {str(e)}")


def _validate_and_normalize_employees(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize employee data."""
    logger.info("Validating employee data...")
    
    # Check for required columns
    missing_cols = []
    for col in REQUIRED_EMPLOYEE_COLUMNS:
        if col not in df.columns:
            missing_cols.append(col)
    
    if missing_cols:
        raise ExcelReaderError(f"Missing required employee columns: {missing_cols}")
      # Rename columns to database field names
    df_normalized = df.rename(columns=EMPLOYEE_COLUMN_MAPPING)
    
    # Replace empty strings with NaN for proper dropna() behavior
    df_normalized = df_normalized.replace('', pd.NA)
    
    # Clean and validate data - drop rows with missing required fields
    df_normalized = df_normalized.dropna(subset=['zid', 'full_name', 'sub_segment', 'project', 'team'])
    
    # Convert ZID to string (in case it's numeric in Excel)
    df_normalized['zid'] = df_normalized['zid'].astype(str)
      # Clean string columns and validate for PostgreSQL compatibility
    string_cols = ['full_name', 'sub_segment', 'project', 'team', 'role']
    for col in string_cols:
        if col in df_normalized.columns:
            df_normalized[col] = df_normalized[col].astype(str).str.strip()
            # PostgreSQL has limits - validate string lengths
            if col == 'full_name' and (df_normalized[col].str.len() > 255).any():
                logger.warning("Some full_name values exceed 255 characters and will be truncated")
                df_normalized[col] = df_normalized[col].str[:255]
      # Parse dates with PostgreSQL compatibility
    if 'start_date_of_working' in df_normalized.columns:
        df_normalized['start_date_of_working'] = pd.to_datetime(
            df_normalized['start_date_of_working'], 
            errors='coerce'
        ).dt.date
        
        # Validate date ranges for PostgreSQL (year 1-9999)
        invalid_dates = df_normalized['start_date_of_working'].notna() & (
            (pd.to_datetime(df_normalized['start_date_of_working'], errors='coerce').dt.year < 1000) |
            (pd.to_datetime(df_normalized['start_date_of_working'], errors='coerce').dt.year > 9999)
        )
        if invalid_dates.any():
            logger.warning(f"Found {invalid_dates.sum()} start dates outside PostgreSQL valid range (year 1000-9999)")
            df_normalized.loc[invalid_dates, 'start_date_of_working'] = None
    
    logger.info(f"Processed {len(df_normalized)} employee records")
    return df_normalized


def _validate_and_normalize_skills(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize skills data."""
    logger.info("Validating skills data...")
    
    # Check for required columns
    missing_cols = []
    for col in REQUIRED_EMPLOYEE_SKILLS_COLUMNS:
        if col not in df.columns:
            missing_cols.append(col)
    
    if missing_cols:
        raise ExcelReaderError(f"Missing required skill columns: {missing_cols}")
    
    # Rename columns to database field names
    df_normalized = df.rename(columns=EMPLOYEE_SKILLS_COLUMN_MAPPING)
    
    # Clean and validate data
    df_normalized = df_normalized.dropna(subset=['zid', 'skill_name', 'proficiency'])
    
    # Convert ZID to string
    df_normalized['zid'] = df_normalized['zid'].astype(str)
    
    # Clean string columns
    string_cols = ['skill_category', 'skill_subcategory', 'skill_name', 'proficiency', 'certification', 'comment']
    for col in string_cols:
        if col in df_normalized.columns:
            df_normalized[col] = df_normalized[col].astype(str).str.strip()
            # Replace 'nan' string with None
            df_normalized[col] = df_normalized[col].replace('nan', None)    # Convert numeric columns
    if 'years_experience' in df_normalized.columns:
        df_normalized['years_experience'] = pd.to_numeric(df_normalized['years_experience'], errors='coerce')
    
    # Parse last_used - can be date string, "Jun-24" format, or year
    # Keep as string for import service to parse with _parse_date_safely
    if 'last_used' in df_normalized.columns:
        # Keep the raw value for the import service to parse
        # Don't convert to string 'nan' - keep as None for proper handling
        df_normalized['last_used'] = df_normalized['last_used'].replace('nan', None)
    
    # Parse started_learning_from date
    if 'started_learning_from' in df_normalized.columns:
        # Keep as raw value for import service to parse with _parse_date_safely
        # The import service handles various formats better than pandas
        df_normalized['started_learning_from'] = df_normalized['started_learning_from'].replace('nan', None)
      # Validate proficiency levels (Dreyfus Model)
    valid_proficiency = ['Novice', 'Advanced Beginner', 'Competent', 'Proficient', 'Expert']
    invalid_prof = df_normalized[~df_normalized['proficiency'].isin(valid_proficiency)]['proficiency'].unique()
    if len(invalid_prof) > 0:
        logger.warning(f"Found invalid proficiency levels: {invalid_prof}. Valid values are: {valid_proficiency}")
    
    logger.info(f"Processed {len(df_normalized)} skill records")
    return df_normalized


def get_master_data_for_scanning(employees_df: pd.DataFrame, skills_df: pd.DataFrame) -> Dict[str, set]:
    """
    Extract all unique master data values from the DataFrames for hierarchical validation.
    This follows the 2-step approach: scan first, then validate/update master tables.
    
    Returns:
        Dict with sets of unique values for each master data type
    """
    logger.info("Scanning Excel data for master data values...")
    
    master_data = {
        # Hierarchical data (Sub-Segment → Project → Team)
        'sub_segments': set(),
        'projects': set(),
        'teams': set(),
        'sub_segment_project_mappings': set(),  # (sub_segment, project) pairs
        'project_team_mappings': set(),  # (project, team) pairs
        
    # Hierarchical skills data (Category → Subcategory → Skills)
        'skill_categories': set(),
        'skill_subcategories': set(),
        'skills': set(),
        'category_subcategory_mappings': set(),  # (category, subcategory) pairs
        'subcategory_skill_mappings': set(),  # (category, subcategory, skill) triplets - category added to prevent collisions
        
        # Other master data
        'roles': set()
    }
    
    # Process employees data
    if not employees_df.empty:
        master_data['sub_segments'].update(employees_df['sub_segment'].dropna().unique())
        master_data['projects'].update(employees_df['project'].dropna().unique())
        master_data['teams'].update(employees_df['team'].dropna().unique())
        master_data['roles'].update(employees_df['role'].dropna().unique())
        
        # Create hierarchical mappings
        for _, row in employees_df.iterrows():
            if pd.notna(row['sub_segment']) and pd.notna(row['project']):
                master_data['sub_segment_project_mappings'].add((row['sub_segment'], row['project']))
            if pd.notna(row['project']) and pd.notna(row['team']):
                master_data['project_team_mappings'].add((row['project'], row['team']))
    
    # Process skills data
    if not skills_df.empty:
        master_data['skill_categories'].update(skills_df['skill_category'].dropna().unique())
        master_data['skill_subcategories'].update(skills_df['skill_subcategory'].dropna().unique())
        master_data['skills'].update(skills_df['skill_name'].dropna().unique())
          # Create hierarchical mappings
        for _, row in skills_df.iterrows():
            if pd.notna(row['skill_category']) and pd.notna(row['skill_subcategory']):
                master_data['category_subcategory_mappings'].add((row['skill_category'], row['skill_subcategory']))
            # Changed to triplet (category, subcategory, skill) to prevent subcategory name collisions across categories
            if pd.notna(row['skill_category']) and pd.notna(row['skill_subcategory']) and pd.notna(row['skill_name']):
                master_data['subcategory_skill_mappings'].add((row['skill_category'], row['skill_subcategory'], row['skill_name']))
    
    # Log summary
    for key, value_set in master_data.items():
        logger.info(f"Found {len(value_set)} unique {key}")
    
    return master_data


def get_dataframe_summary(df: pd.DataFrame, name: str) -> Dict[str, Any]:
    """
    Get a summary of the dataframe for logging/reporting.
    
    Args:
        df: The dataframe to summarize
        name: Name of the dataframe for display
        
    Returns:
        Dict with summary information
    """
    return {
        'name': name,
        'rows': len(df),
        'columns': list(df.columns),
        'memory_usage': df.memory_usage(deep=True).sum(),
        'null_counts': df.isnull().sum().to_dict()
    }
