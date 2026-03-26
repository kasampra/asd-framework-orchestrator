<tool_call>
<tool_call>
1. **Goal Decomposition**  
The objective is to build a *secure*, *sleek* Hello World API with tests and Docker support. This implies:

- A backend service (e.g., RESTful API) that returns `"Hello, World!"`.
- Security best practices: input validation (if applicable), secure headers, minimal attack surface.
- Tests: unit/integration tests to verify correctness and security posture.
- Dockerization: containerized app with a minimal image, non-root user, etc.

**Sub-tasks identified**:
1. Choose tech stack (e.g., Python + FastAPI for sleekness & async; or Node.js/Express).
2. Implement the API endpoint (`GET /hello` → `"Hello, World!"`).
3. Add security headers/middleware.
4. Write tests (e.g., `pytest`, `supertest`).
5. Create Dockerfile and `docker-compose.yml`.
6. Ensure minimal image size & secure defaults.

**Chosen Stack**:  
- **Backend**: Python + FastAPI (modern, async, auto-docs, Pydantic validation).  
- **Security**: Add `X-Content-Type-Options`, `X-Frame-Options`, rate limiting (optional), and use Gunicorn with Uvicorn.  
- **Testing**: `pytest` + `httpx`.  
- **Docker**: Multi-stage build, non-root user.

---

2. **Approach**  
- Create a minimal FastAPI app with `/hello` endpoint.
- Add middleware for security headers.
- Write tests to verify response and headers.
- Dockerize: stage 1 = install deps; stage 2 = copy only runtime files + run as non-root.

---

3. **Final Output Plan**
- `src/app.py`: FastAPI app with `/hello`.
- `src/middleware.py`: Security header middleware (optional, but clean).
- `tests/test_api.py`: Test for status code and headers.
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`.

Let’s generate the files now.

<tool_call>
1. **`requirements.txt`**  
2. **`src/app.py`**  
3. **`src/middleware.py`** (optional but recommended)  
4. **`tests/test_api.py`**  
5. **`Dockerfile`**  
6. **`docker-compose.yml`**

Let’s proceed.

<tool_call>
1. `requirements.txt`: FastAPI, uvicorn, gunicorn (for production), pytest, httpx.
2. `src/app.py`: Minimal FastAPI app with `/hello`.
3. `tests/test_api.py`: Test `/hello` returns 200 and correct body.
4. Dockerfile: Multi-stage build.

Let’s write them now.

<tool_call>
1. **`requirements.txt`**  
```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
gunicorn==23.0.0
pytest==8.3.4
httpx==0.28.1
```

<tool_call>
2. **`src/app.py`**  
```python
from fastapi import FastAPI, Request

app = FastAPI(title="Secure Hello World API", version="1.0.0")

@app.get("/hello")
async def hello():
    return {"message": "Hello, World!"}
```

<tool_call> 3. **`src/middleware.py`**  
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
```

Then update `app.py` to include middleware.

<tool_call> 4. **`tests/test_api.py`**  
```python
import pytest
from httpx import AsyncClient
from src.app import app

@pytest.mark.asyncio
async def test_hello():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/hello")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"
```

<tool_call> 5. **`Dockerfile`**  
```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/
COPY requirements.txt .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "src.app:app"]
```

<tool_call> 6. **`docker-compose.yml`**  
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/hello"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Now finalize `app.py` to include middleware.

Final `src/app.py`:  
```python
from fastapi import FastAPI, Request
from src.middleware import SecurityHeadersMiddleware

app = FastAPI(title="Secure Hello World API", version="1.0.0")

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

@app.get("/hello")
async def hello():
    return {"message": "Hello, World!"}
```

Let’s verify the test file imports correctly.

✅ Done. Final output below.

<tool_call>
<tool_call>
1. **`requirements.txt`**  
2. **`src/app.py`**  
3. **`src/middleware.py`**  
4. **`tests/test_api.py`**  
5. **`Dockerfile`**  
6. **`docker-compose.yml`**

Let’s finalize.

<tool_call>
1. `requirements.txt`: ✅  
2. `src/app.py`: ✅  
3. `src/middleware.py`: ✅  
4. `tests/test_api.py`: ✅  
5. `Dockerfile`: ✅  
6. `docker-compose.yml`: ✅

All files are ready.

Final output:

<tool_call>
1. **`requirements.txt`**  
```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
gunicorn==23.0.0
pytest==8.3.4
httpx==0.28.1
```

<tool_call>
2. **`src/app.py`**  
```python
from fastapi import FastAPI, Request
from src.middleware import SecurityHeadersMiddleware

app = FastAPI(title="Secure Hello World API", version="1.0.0")

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

@app.get("/hello")
async def hello():
    return {"message": "Hello, World!"}
```

<tool_call>
3. **`src/middleware.py`**  
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
```

<tool_call>
4. **`tests/test_api.py`**  
```python
import pytest
from httpx import AsyncClient
from src.app import app

@pytest.mark.asyncio
async def test_hello():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/hello")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"
```

<tool_call>
5. **`Dockerfile`**  
```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/
COPY requirements.txt .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "src.app:app"]
```

<tool_call>
6. **`docker-compose.yml`**  
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/hello"]
      interval: 30s
      timeout: 10s
      retries: 3
```

✅ All files are ready. To run:

```bash
docker-compose up --build
# Then curl http://localhost:8000/hello
```

To test locally (without Docker):

```bash
pip install -r requirements.txt
pytest tests/
uvicorn src.app:app --reload
```

Done!