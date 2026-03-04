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


def normalize_designation(value: str) -> str:
    """
    Normalize role/designation text for matching.
    
    Specifically handles whitespace around slashes which is common in
    compound designations like "Scrum Master/Team Lead".
    
    Rules:
    - Return "" if None
    - Lowercase
    - Strip leading/trailing whitespace
    - Collapse multiple internal spaces to single space
    - Normalize slash spacing: remove spaces around "/" 
      (e.g., "Scrum Master/ TL" -> "scrum master/tl")
    
    Examples:
        >>> normalize_designation("Scrum Master/ TL")
        'scrum master/tl'
        >>> normalize_designation("Scrum Master /TL")
        'scrum master/tl'
        >>> normalize_designation("Scrum Master / TL")
        'scrum master/tl'
        >>> normalize_designation("  SENIOR   ENGINEER  ")
        'senior engineer'
    
    Args:
        value: Raw designation/role string from Excel or database
        
    Returns:
        Normalized lowercase string ready for matching
    """
    if value is None:
        return ""
    
    # Convert to lowercase and strip
    normalized = str(value).lower().strip()
    
    # Collapse multiple internal spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove spaces around slashes: "Scrum Master / TL" -> "Scrum Master/TL"
    normalized = re.sub(r'\s*/\s*', '/', normalized)
    
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


# Plural forms that should be normalized to singular for skill matching
# Format: (plural_suffix, singular_suffix)
_SKILL_PLURAL_RULES = [
    ('apis', 'api'),
    ('services', 'service'),
    ('frameworks', 'framework'),
]


def normalize_skill_name(value: str) -> str:
    """
    Normalize skill name for matching, including simple plural normalization.
    
    This function is used for skill resolution to handle cases like:
    - "RESTful APIs" matching "RESTful API"
    - "Web Services" matching "Web Service"
    - "Frameworks" matching "Framework"
    
    Rules:
    - Return "" if None or empty
    - Lowercase
    - Strip leading/trailing whitespace
    - Collapse multiple spaces to single space
    - Normalize slash spacing: remove spaces around "/"
    - Apply explicit plural→singular normalization for specific words only
      (does NOT blindly strip trailing 's')
    
    Examples:
        >>> normalize_skill_name("RESTful APIs")
        'restful api'
        >>> normalize_skill_name("Web Services")
        'web service'
        >>> normalize_skill_name("Glass")  # NOT affected - 'glass' != 'glas'
        'glass'
        >>> normalize_skill_name("Scrum Master / TL")
        'scrum master/tl'
    
    Args:
        value: Raw skill name from Excel or database
        
    Returns:
        Normalized skill name ready for matching
    """
    if value is None:
        return ""
    
    # Convert to string, lowercase, and strip
    normalized = str(value).lower().strip()
    
    if not normalized:
        return ""
    
    # Collapse multiple internal spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Normalize slash spacing: "Scrum Master / TL" -> "scrum master/tl"
    normalized = re.sub(r'\s*/\s*', '/', normalized)
    
    # Apply explicit plural→singular rules (word-boundary aware)
    for plural, singular in _SKILL_PLURAL_RULES:
        # Match whole word at end or followed by non-alpha
        # Use word boundary \b to ensure we match whole words only
        pattern = r'\b' + re.escape(plural) + r'\b'
        normalized = re.sub(pattern, singular, normalized)
    
    return normalized


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
