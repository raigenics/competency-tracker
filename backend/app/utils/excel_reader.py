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
    'Segment': 'segment',  # NEW: Top-level organizational unit
    'Sub-Segment': 'sub_segment',
    'Project': 'project',
    'Team': 'team',
    'Role/Designation': 'role',
    'Start Date of Working': 'start_date_of_working',
    'Project Allocation %': 'project_allocation_pct'  # For employee_project_allocations
}

EMPLOYEE_SKILLS_COLUMN_MAPPING = {
    'Employee ID (ZID)': 'zid',
    'Employee Full Name': 'employee_full_name',  # For validation only
    'Skill Name': 'skill_name',
    'Proficiency': 'proficiency',
    'Experience Years': 'years_experience',
    'Last Used': 'last_used',
    'Started learning from (Date)': 'started_learning_from',
    'Certification': 'certification',
    'Comment': 'comment',
    'Interest Level': 'interest_level'  # Added optional field
}

# Required columns for validation
REQUIRED_EMPLOYEE_COLUMNS = [
    'Employee ID (ZID)',
    'Employee Full Name', 
    'Sub-Segment',
    'Project',
    'Team'
]

# Required columns for skills - only ZID, Skill Name, and Proficiency are mandatory
# Skill Category is optional (for skills-only format)
REQUIRED_EMPLOYEE_SKILLS_COLUMNS = [
    'Employee ID (ZID)',
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
    """
    Validate and normalize skills data.
    
    NOTE: NEW FORMAT - No longer expects Skill Category or Skill Subcategory columns.
    Skills will be resolved against master skill data using exact match or alias match.
    """
    logger.info("Validating skills data (NEW FORMAT - no category/subcategory columns)...")
    
    # Check for required columns
    missing_cols = []
    for col in REQUIRED_EMPLOYEE_SKILLS_COLUMNS:
        if col not in df.columns:
            missing_cols.append(col)
    
    if missing_cols:
        raise ExcelReaderError(f"Missing required skill columns: {missing_cols}")
    
    # Rename columns to database field names
    df_normalized = df.rename(columns=EMPLOYEE_SKILLS_COLUMN_MAPPING)
    
    # Log normalized columns for debugging
    logger.info(f"Normalized skills columns: {list(df_normalized.columns)}")
    
    # Clean and validate data
    df_normalized = df_normalized.dropna(subset=['zid', 'skill_name', 'proficiency'])
    
    # Convert ZID to string
    df_normalized['zid'] = df_normalized['zid'].astype(str)
    
    # Clean string columns (removed skill_category and skill_subcategory)
    string_cols = ['skill_name', 'proficiency', 'certification', 'comment']
    for col in string_cols:
        if col in df_normalized.columns:
            df_normalized[col] = df_normalized[col].astype(str).str.strip()
            # Replace 'nan' string with None
            df_normalized[col] = df_normalized[col].replace('nan', None)# Convert numeric columns
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
    
    NOTE: NEW FORMAT - Only scans EMPLOYEE sheet for org hierarchy (Segment → SubSegment → Project → Team/Role).
    Does NOT scan skills sheet for Category/Subcategory - those are derived from DB lookups.
    
    Returns:
        Dict with sets of unique values for each master data type    """
    logger.info("Scanning Excel data for org master data (NEW FORMAT - employee sheet only)...")
    
    master_data = {
        # Hierarchical org data (Segment → Sub-Segment → Project → Team) from Employee sheet
        'segments': set(),
        'sub_segments': set(),
        'projects': set(),
        'teams': set(),
        'segment_subsegment_mappings': set(),  # (segment, sub_segment) pairs
        'sub_segment_project_mappings': set(),  # (sub_segment, project) pairs
        'project_team_mappings': set(),  # (sub_segment, project, team) triples - FIXED to include sub_segment
        
        # Other master data from Employee sheet
        'roles': set(),
        
        # Removed: skill_categories, skill_subcategories, skills - these come from DB, not Excel
    }
    
    # Process employees data
    if not employees_df.empty:
        # Extract unique values for each organizational level
        # Segment is optional - if not present or empty, will use default "Legacy" segment
        if 'segment' in employees_df.columns:
            master_data['segments'].update(employees_df['segment'].dropna().unique())
        master_data['sub_segments'].update(employees_df['sub_segment'].dropna().unique())
        master_data['projects'].update(employees_df['project'].dropna().unique())
        master_data['teams'].update(employees_df['team'].dropna().unique())
        master_data['roles'].update(employees_df['role'].dropna().unique())
        
        # Create hierarchical mappings
        for _, row in employees_df.iterrows():
            # Segment → Sub-Segment mapping (optional, backward compatible)
            if 'segment' in employees_df.columns and pd.notna(row.get('segment')) and pd.notna(row['sub_segment']):
                segment_val = str(row['segment']).strip()
                if segment_val:  # Only add if not empty/whitespace
                    master_data['segment_subsegment_mappings'].add((segment_val, row['sub_segment']))
            
            if pd.notna(row['sub_segment']) and pd.notna(row['project']):
                master_data['sub_segment_project_mappings'].add((row['sub_segment'], row['project']))
            # FIX: Include sub_segment in project_team_mappings to handle duplicate project names across sub_segments
            if pd.notna(row['sub_segment']) and pd.notna(row['project']) and pd.notna(row['team']):
                master_data['project_team_mappings'].add((row['sub_segment'], row['project'], row['team']))
    
    # Log summary
    for key, value_set in master_data.items():
        logger.info(f"Found {len(value_set)} unique {key}")
    
    logger.info("NOTE: Skills will be resolved from DB master data (skills table + skill_aliases), not from Excel")
    
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
