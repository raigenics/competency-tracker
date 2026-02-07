"""
Skill Token Validation and Cleanup.

Single Responsibility: Clean and validate skill tokens before resolution.
Prevents garbage tokens like ")", "4", "6" from being processed.
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class SkillTokenValidator:
    """Validates and cleans skill tokens before resolution."""
    
    # Whitelist of valid 1-character skills (programming languages)
    VALID_SINGLE_CHAR_SKILLS = frozenset(['C', 'R', 'V'])
    
    # Minimum skill name length (after cleaning)
    MIN_SKILL_LENGTH = 2
    
    def __init__(self):
        """Initialize skill token validator."""
        pass
    
    def clean_and_validate(self, raw_token: str) -> Optional[str]:
        """
        Clean and validate a skill token.
        
        Cleaning steps:
            1. Strip leading/trailing whitespace
            2. Remove excessive internal whitespace
            3. Strip leading/trailing punctuation (except for valid cases)
        
        Validation rules (reject if):
            - Empty after cleaning
            - Only punctuation
            - Only digits
            - Length < 2 (except whitelisted: C, R, V)
            - Only whitespace
        
        Args:
            raw_token: Raw skill token from Excel (e.g., "Python", ")", "4", "C++")
            
        Returns:
            Cleaned token if valid, None if invalid (should be rejected)
            
        Examples:
            "Python" → "Python"
            "C++" → "C++"
            "C" → "C" (whitelisted)
            ")" → None (only punctuation)
            "4" → None (only digit)
            "  JavaScript  " → "JavaScript"
            "" → None (empty)
            "   " → None (only whitespace)
            "(Python)" → "Python" (stripped punctuation)
            "6" → None (only digit)
            "V" → "V" (whitelisted)
        """
        # Step 1: Basic cleanup
        cleaned = self._clean_token(raw_token)
        
        # Step 2: Validate
        is_valid, reason = self._validate_token(cleaned)
        
        if not is_valid:
            logger.debug(f"Token rejected: '{raw_token}' → '{cleaned}' (reason: {reason})")
            return None
        
        return cleaned
    
    def _clean_token(self, raw_token: str) -> str:
        """
        Clean a skill token.
        
        Steps:
            1. Convert to string (handle pandas edge cases)
            2. Strip leading/trailing whitespace
            3. Normalize internal whitespace (multiple spaces → single space)
            4. Strip leading/trailing common punctuation (but preserve internal)
        """
        # Convert to string and strip
        token = str(raw_token).strip()
        
        # Normalize internal whitespace
        token = re.sub(r'\s+', ' ', token)
        
        # Strip leading/trailing punctuation (but preserve C++, C#, etc.)
        # Only strip if the ENTIRE token is not just punctuation + letters
        token = self._strip_boundary_punctuation(token)
        
        return token
    
    def _strip_boundary_punctuation(self, token: str) -> str:
        """
        Strip leading/trailing punctuation, but preserve valid cases like C++.
        
        Examples:
            "(Python)" → "Python"
            "C++" → "C++"
            "C#" → "C#"
            ")test" → "test"
            "test(" → "test"
        """
        # Only strip punctuation if it's at the boundaries AND the token contains alphanumeric
        if not any(c.isalnum() for c in token):
            # Token has no alphanumeric chars, don't strip (will be rejected later)
            return token
        
        # Strip leading non-alphanumeric (except for technical names like ".NET")
        token = re.sub(r'^[^\w.#]+', '', token)
        
        # Strip trailing non-alphanumeric (except for valid cases like "C++")
        token = re.sub(r'[^\w+#.]+$', '', token)
        
        return token
    
    def _validate_token(self, cleaned_token: str) -> tuple[bool, str]:
        """
        Validate a cleaned token.
        
        Returns:
            (is_valid, rejection_reason)
        """
        # Rule 1: Empty check
        if not cleaned_token:
            return False, "empty"
        
        # Rule 2: Only whitespace check
        if cleaned_token.isspace():
            return False, "only_whitespace"
        
        # Rule 3: Only punctuation check
        if not any(c.isalnum() for c in cleaned_token):
            return False, "only_punctuation"
        
        # Rule 4: Only digits check
        if cleaned_token.isdigit():
            return False, "only_digits"
        
        # Rule 5: Length check (with whitelist)
        if len(cleaned_token) < self.MIN_SKILL_LENGTH:
            # Check whitelist for single-character skills
            if cleaned_token.upper() not in self.VALID_SINGLE_CHAR_SKILLS:
                return False, f"too_short_and_not_whitelisted (length={len(cleaned_token)})"
        
        # Valid token
        return True, "valid"
    
    def is_valid_token(self, raw_token: str) -> bool:
        """
        Quick check if a token is valid (without cleaning).
        
        Args:
            raw_token: Raw skill token
            
        Returns:
            True if token would pass validation after cleaning
        """
        cleaned = self.clean_and_validate(raw_token)
        return cleaned is not None
