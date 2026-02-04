"""
Skill expansion logic for employee import.

Single Responsibility: Expand comma-separated skills into individual rows.
"""
import logging
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)


class SkillExpander:
    """Expands comma-separated skills into individual rows."""
    
    def expand_skills(self, skills_df: pd.DataFrame) -> pd.DataFrame:
        """
        Expand comma-separated skills into individual rows.
        Excel can have "PostgreSQL, SQL Server" → split into 2 rows.
        
        Args:
            skills_df: Original skills DataFrame
            
        Returns:
            Expanded skills DataFrame
        """
        expanded_rows = []
        
        for idx, row in skills_df.iterrows():
            skill_name_raw = str(row.get('skill_name', '')).strip()
            
            # Split on comma or semicolon
            if ',' in skill_name_raw or ';' in skill_name_raw:
                # Split and clean each skill
                skill_names = [s.strip() for s in skill_name_raw.replace(';', ',').split(',')]
                skill_names = [s for s in skill_names if s]  # Remove empty
                
                # Create a row for each skill (copy all other columns)
                for skill_name in skill_names:
                    row_copy = row.copy()
                    row_copy['skill_name'] = skill_name
                    expanded_rows.append(row_copy)
            else:
                expanded_rows.append(row)
        
        # Replace original dataframe with expanded one
        if len(expanded_rows) > len(skills_df):
            logger.info(f"📊 Expanded {len(expanded_rows) - len(skills_df)} comma-separated skills → total {len(expanded_rows)} skill rows")
            return pd.DataFrame(expanded_rows)
        
        return skills_df
