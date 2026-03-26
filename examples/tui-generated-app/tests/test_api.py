# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create a test client for the FastAPI app
client = TestClient(app)

@pytest.mark.asyncio
async def test_hello_endpoint_returns_correct_response_and_headers():
    """
    Test that the /hello endpoint:
    - Returns status code 200
    - Returns correct JSON body: {"message": "Hello, World!"}
    - Includes all required security headers:
        * X-Content-Type-Options: nosniff
        * X-Frame-Options: DENY
        * X-XSS-Protection: 1; mode=block
    """
    response = client.get("/hello")
    
    # Assert status code
    assert response.status_code == 200
    
    # Assert JSON body
    expected_body = {"message": "Hello, World!"}
    assert response.json() == expected_body
    
    # Assert security headers are present and correct
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"

# Optional: Add a test for missing route to ensure middleware doesn't break 404s
@pytest.mark.asyncio
async def test_nonexistent_route_returns_404():
    """
    Ensure that non-existent routes still return 404 and do not crash.
    (Middleware should not interfere with routing.)
    """
    response = client.get("/nonexistent")
    assert response.status_code == 404

# Optional: Test OPTIONS preflight if CORS is configured later
# For now, just verify GET works as expected — per current implementation.