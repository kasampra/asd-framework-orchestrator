<tool_call>
```python
# requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.32.1
gunicorn==23.0.0
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.25.0
```

```python
# src/middleware.py
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers to every response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

def add_security_headers(app: FastAPI) -> None:
    """Register security headers middleware with the FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)
```

```python
# src/app.py
from fastapi import FastAPI
from src.middleware import add_security_headers

app = FastAPI(title="Secure Hello World API", version="1.0")

# Explicitly apply security headers middleware BEFORE defining routes
add_security_headers(app)

@app.get("/hello")
def read_hello():
    return {"message": "Hello, World!"}
```

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_hello_endpoint_returns_correct_response_and_headers():
    response = client.get("/hello")
    
    # Check status code and body
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
    
    # Verify required security headers are present
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    
    assert "X-XSS-Protection" in response.headers
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
```

```dockerfile
# Dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn==23.0.0

COPY src/ ./src/

FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy only necessary files from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /app/src/ ./src/
COPY --from=builder /app/requirements.txt .

EXPOSE 8000

# Switch to non-root user
USER appuser

CMD ["gunicorn", "src.app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```
<tool_call>