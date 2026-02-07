"""
Password hashing and verification service.

⚠️  SECURITY WARNING: PLACEHOLDER IMPLEMENTATION ONLY ⚠️
This is a temporary insecure implementation that stores passwords in plain text.

TODO BEFORE PRODUCTION:
1. Install passlib[bcrypt]: pip install passlib[bcrypt]
2. Replace placeholder implementation with proper bcrypt hashing
3. Remove TEMP_PLAIN_ prefix and implement secure hashing
"""
import logging

logger = logging.getLogger(__name__)


class PasswordService:
    """Service for password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        ⚠️  SECURITY WARNING: This is a PLACEHOLDER that stores plain text!
        
        TODO: Replace with proper implementation:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password (currently prefixed with TEMP_PLAIN_)
        """
        logger.warning(
            "⚠️  PASSWORD HASHING NOT IMPLEMENTED - STORING PLAIN TEXT (INSECURE!) ⚠️"
        )
        return f"TEMP_PLAIN_{password}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        ⚠️  SECURITY WARNING: This is a PLACEHOLDER that compares plain text!
        
        TODO: Replace with proper implementation:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
        
        Returns:
            True if password matches, False otherwise
        """
        return hashed_password == f"TEMP_PLAIN_{plain_password}"
