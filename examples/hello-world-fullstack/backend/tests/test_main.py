# backend/tests/test_main.py
"""
Test suite for the Hello World API backend using pytest.

This module tests:
- Health endpoint (/health)
- JWT token creation and verification logic
- Main application startup (basic smoke test)

Note: This is a minimal test suite focused on core functionality.
More comprehensive tests can be added as features expand.
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Set up test environment variables before importing app modules
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["JWT_EXPIRY_SECONDS"] = "3600"

from app.main import app  # noqa: E402
from app.auth.jwt import create_jwt_token, verify_jwt_token  # noqa: E402


# Fixtures
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Tests for /health endpoint
def test_health_check(client):
    """Test that the health check endpoint returns healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# Tests for JWT functionality
def test_create_jwt_token():
    """Test JWT token creation with valid inputs."""
    organisation_id = "org_123"
    token = create_jwt_token(organisation_id)
    
    # Token should be a non-empty string
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_valid_jwt_token():
    """Test verification of a valid JWT token."""
    organisation_id = "org_456"
    token = create_jwt_token(organisation_id)
    
    payload = verify_jwt_token(token)
    
    assert payload["sub"] == "system"
    assert payload["organisation_id"] == organisation_id
    assert "iat" in payload
    assert "exp" in payload


def test_verify_expired_jwt_token():
    """Test that expired tokens raise appropriate error."""
    # Temporarily set expiry to 0 seconds for testing
    with patch("app.auth.jwt.settings.JWT_EXPIRY_SECONDS", 0):
        organisation_id = "org_789"
        token = create_jwt_token(organisation_id)
        
        with pytest.raises(ValueError, match="Token has expired"):
            verify_jwt_token(token)


def test_verify_invalid_signature():
    """Test that tokens with invalid signatures raise error."""
    # Create a valid token first
    organisation_id = "org_abc"
    token = create_jwt_token(organisation_id)
    
    # Corrupt the signature by modifying the token string
    parts = token.split(".")
    if len(parts) == 3:
        corrupted_token = ".".join([parts[0], parts[1], "invalid"])
        
        with pytest.raises(ValueError, match="Invalid token"):
            verify_jwt_token(corrupted_token)


def test_verify_missing_organisation_id_claim():
    """Test that tokens without required claims raise error."""
    # Manually craft a JWT payload without organisation_id
    import jwt as pyjwt
    from app.config import settings
    
    payload = {"sub": "test", "iat": 1234567890}
    fake_token = pyjwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    with pytest.raises(ValueError, match="Missing 'organisation_id' claim"):
        verify_jwt_token(fake_token)


# Basic smoke test for app startup
def test_app_exists():
    """Smoke test to ensure the FastAPI app is properly instantiated."""
    assert app is not None
    assert hasattr(app, "router")