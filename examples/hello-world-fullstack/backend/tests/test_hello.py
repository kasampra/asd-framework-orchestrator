# backend/tests/test_hello.py
from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt import create_jwt_token

client = TestClient(app)


def test_hello_missing_auth():
    response = client.post("/api/hello")
    assert response.status_code == 401


def test_hello_invalid_token():
    response = client.post(
        "/api/hello",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401
    detail = response.json()["detail"]
    assert "Invalid token" in detail or "Token has expired" in detail


def test_hello_valid_token():
    token = create_jwt_token(organisation_id="org_test123", subject="user@example.com")
    response = client.post(
        "/api/hello",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Hello, organisation org_test123!" in data["message"]
    assert data["user"] == "user@example.com"