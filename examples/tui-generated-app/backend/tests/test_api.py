# backend/tests/test_api.py

"""
Test suite for the FastAPI backend application.

This test suite covers:
1. Basic /hello endpoint functionality (status, body, security headers)
2. Authentication logic: login, token generation/validation, protected endpoints
3. Error handling for auth-related failures (missing/invalid tokens)
4. Consistent application of security headers across all routes (including auth routes)

Assumptions based on architecture:
- The app uses JWT-based authentication.
- There is a /login endpoint that returns an access token.
- Protected endpoints require Bearer token in Authorization header.
- Security headers middleware applies to *all* routes.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app  # Import the actual FastAPI app

# Create test client
client = TestClient(app)


class TestHelloEndpoint:
    """Tests for /hello endpoint."""

    def test_hello_endpoint_returns_correct_response_and_headers(self):
        """Verify /hello returns correct JSON and all required security headers."""
        response = client.get("/hello")
        
        # Status code check
        assert response.status_code == 200
        
        # Body check
        assert response.json() == {"message": "Hello, World!"}
        
        # Security headers checks (must be present on ALL routes)
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestSecurityHeadersConsistency:
    """Ensure security headers are applied to all routes, including auth endpoints."""

    def test_security_headers_on_404_route(self):
        """Verify 404 responses also include security headers."""
        response = client.get("/nonexistent-route")
        
        assert response.status_code == 404
        
        # All required headers must still be present
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestAuthenticationFlow:
    """Tests for authentication endpoints and token handling."""

    def test_login_returns_valid_jwt_token(self):
        """Verify /login accepts valid credentials and returns a JWT."""
        # Use known test credentials (assumed to be configured in app)
        payload = {"username": "testuser", "password": "securepassword123"}
        
        response = client.post("/login", data=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Token must be present and non-empty
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        
        # Token type should be 'Bearer'
        assert data["token_type"] == "bearer"

    def test_login_fails_with_invalid_credentials(self):
        """Verify /login rejects invalid credentials."""
        payload = {"username": "testuser", "password": "wrongpassword"}
        
        response = client.post("/login", data=payload)
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        
        # Optional: verify error detail (if implemented)
        if response.headers.get("content-type") == "application/json":
            error_detail = response.json()
            assert "detail" in error_detail

    def test_protected_endpoint_requires_auth(self):
        """Verify a protected endpoint returns 401 when no token is provided."""
        # Assume there's a /me or /protected route (common pattern)
        # If not, create one temporarily for testing — but per spec, app already has auth logic
        response = client.get("/me")
        
        assert response.status_code == 401
        
        # Check standard WWW-Authenticate header is present
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_protected_endpoint_accepts_valid_token(self):
        """Verify /me returns user info when valid token is provided."""
        # First, get a valid token via login (using known credentials)
        payload = {"username": "testuser", "password": "securepassword123"}
        login_response = client.post("/login", data=payload)
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Now call protected endpoint with Bearer token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/me", headers=headers)
        
        assert response.status_code == 200
        
        # Should return user info (e.g., username, roles)
        data = response.json()
        assert "sub" in data or "username" in data

    def test_protected_endpoint_rejects_invalid_token(self):
        """Verify /me rejects malformed/invalid tokens."""
        headers = {"Authorization": "Bearer invalidtoken123"}
        response = client.get("/me", headers=headers)
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    def test_protected_endpoint_rejects_missing_token(self):
        """Verify /me rejects requests with empty Authorization header."""
        # Explicitly send empty Bearer token
        headers = {"Authorization": "Bearer "}
        response = client.get("/me", headers=headers)
        
        assert response.status_code == 401

    def test_security_headers_on_login_route(self):
        """Ensure security headers are applied even to /login (including POST)."""
        payload = {"username": "testuser", "password": "securepassword123"}
        response = client.post("/login", data=payload)
        
        assert response.status_code == 200
        
        # All required headers must be present
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_security_headers_on_protected_route(self):
        """Ensure security headers are applied to protected routes."""
        # Get token first
        payload = {"username": "testuser", "password": "securepassword123"}
        login_response = client.post("/login", data=payload)
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/me", headers=headers)
        
        assert response.status_code == 200
        
        # Verify all security headers
        for header in ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection"]:
            assert header in response.headers

    def test_cache_control_no_store_on_auth_routes(self):
        """Verify sensitive auth routes include Cache-Control: no-store to prevent caching."""
        # Test on /login (POST)
        payload = {"username": "testuser", "password": "securepassword123"}
        login_response = client.post("/login", data=payload)
        
        assert "Cache-Control" in login_response.headers
        assert "no-store" in login_response.headers["Cache-Control"]
        
        # Test on /me (GET with auth) — sensitive user info should not be cached
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/me", headers=headers)
        
        assert "Cache-Control" in me_response.headers
        assert "no-store" in me_response.headers["Cache-Control"]


# Optional: Add async tests if needed (e.g., for token expiration, refresh tokens)
# For now, sync tests cover core functionality.