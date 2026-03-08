# backend/app/auth/jwt.py
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import re

from app.config import settings


def create_jwt_token(organisation_id: str, subject: str = "system") -> str:
    """Create a signed JWT with organisation_id claim."""
    # 🔐 SECURITY: Validate organisation_id format (alphanumeric + hyphen/underscore only)
    if not isinstance(organisation_id, str):
        raise ValueError("organisation_id must be a string")
    
    if len(organisation_id) == 0:
        raise ValueError("organisation_id cannot be empty")
    
    if len(organisation_id) > 64:
        raise ValueError("organisation_id too long (max 64 chars)")
    
    # Allow only safe characters: letters, digits, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', organisation_id):
        raise ValueError("organisation_id contains invalid characters")
    
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "organisation_id": organisation_id,
        "iat": now,
        "exp": now + timedelta(seconds=settings.JWT_EXPIRY_SECONDS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT. Raises exception on invalid token."""
    if not isinstance(token, str):
        raise ValueError("Token must be a string")
    
    # 🔐 SECURITY: Reject empty or whitespace-only tokens
    if not token.strip():
        raise ValueError("Empty token provided")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if "organisation_id" not in payload:
            raise ValueError("Missing 'organisation_id' claim")
        
        # 🔐 SECURITY: Validate organisation_id format on decode too (defensive)
        org_id = payload["organisation_id"]
        if not isinstance(org_id, str) or len(org_id) == 0 or len(org_id) > 64:
            raise ValueError("Invalid organisation_id in token")
        if not re.match(r'^[a-zA-Z0-9_-]+$', org_id):
            raise ValueError("Malformed organisation_id in token")

        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")