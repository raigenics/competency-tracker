"""
Normalization utilities for skill data.
Provides consistent text normalization for matching and deduplication.
"""
import re


def normalize_key(text: str) -> str:
    """
    Normalize text for matching/uniqueness checks.
    
    Rules:
    - Trim whitespace
    - Lowercase
    - Replace underscores and hyphens with space
    - Collapse multiple spaces to single space
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized lowercase string with collapsed spaces
    """
    if not text:
        return ""
    
    # Trim and lowercase
    normalized = text.strip().lower()
    
    # Replace underscores and hyphens with space
    normalized = normalized.replace("_", " ").replace("-", " ")
    
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def normalize_skill_text(text: str) -> str:
    """
    Normalize skill text for resolution and matching.
    
    This is a specialized version for skill names that follows the same
    rules as normalize_key() for consistency.
    
    Args:
        text: Raw skill text from Excel
        
    Returns:
        Normalized skill text ready for matching
    """
    return normalize_key(text)


def normalize_and_preserve(text: str) -> tuple[str, str]:
    """
    Normalize text while preserving the original trimmed form.
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (normalized_key, trimmed_original)
    """
    if not text:
        return ("", "")
    
    trimmed = text.strip()
    normalized = normalize_key(trimmed)
    
    return (normalized, trimmed)
