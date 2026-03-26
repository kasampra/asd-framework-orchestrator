<tool_call>
```python
# README.md

"""
README.md for the full-stack application using Docker Compose.

This document explains how to build, start, and run the application locally.
The stack consists of:
- Backend: FastAPI (Python 3.12) on port 8000
- Frontend: React app built with Node.js, served via Nginx on port 3000
- Database: PostgreSQL 16 Alpine on port 5432

All services are orchestrated using `docker-compose.yml`.
"""

# README.md content starts here:
"""
# Full-Stack Application (FastAPI + React + PostgreSQL)

This project is a full-stack web application with:

- **Backend**: FastAPI (Python 3.12) serving REST API on port `8000`
- **Frontend**: React app built in production mode and served via Nginx on port `3000`
- **Database**: PostgreSQL 16 Alpine on port `5432`

All services are containerized using Docker and orchestrated with `docker-compose`.

---

## 📁 Project Structure

```
.
├── backend/
│   ├── app/                # FastAPI application entrypoint
│   │   └── main.py         # FastAPI app definition
│   ├── src/                # Core Python modules (models, utils, etc.)
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Multi-stage build for backend
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package*.json       # NPM config & lock files
│   ├── nginx.conf          # Nginx config (note: Dockerfile has a typo, see below)
│   └── Dockerfile          # Multi-stage build for frontend
├── docker-compose.yml      # Service orchestration
└── README.md               # This file
```

> ⚠️ **Note**: The `frontend/Dockerfile` contains an incomplete `COPY` command (`COPY nginx.conf /e`).  
> It should be:  
> ```dockerfile
> COPY nginx.conf /etc/nginx/conf.d/default.conf
> ```
> We assume this is fixed before deployment.

---

## 🛠️ Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) (v20+ recommended)
- [Docker Compose Plugin](https://docs.docker.com/compose/install/) (v2.0+)

Verify installation:
```bash
docker --version
docker compose version
```

---

## 🚀 Build & Run Locally

### 1️⃣ Clone the repository

```bash
git clone <your-repo-url>
cd <project-root>
```

### 2️⃣ Start all services (build + run)

From the project root directory (where `docker-compose.yml` resides):

```bash
docker compose up --build
```

- This will:
  - Build images for `backend`, `frontend`, and use pre-pulled `postgres:16-alpine`
  - Start all containers
  - Expose ports:
    - `8000`: Backend API (e.g., `http://localhost:8000`)
    - `3000`: Frontend app (e.g., `http://localhost:3000`)
    - `5432`: PostgreSQL (for local DB access — optional)

> ✅ Once running, visit:
> - Frontend UI: [http://localhost:3000](http://localhost:3000)
> - Backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
> - PostgreSQL: `postgresql://appuser:secret@localhost:5432/appdb`

---

## 🧪 Run Tests

### Backend tests (Python + pytest)

Run inside the backend container:

```bash
docker compose exec backend python -m pytest backend/tests/
```

Or, if you have local Python environment:
```bash
cd backend
pip install -r requirements.txt
pytest tests/
```

> ✅ The test suite covers `/hello`, auth flow (`/login`, protected endpoints), and security headers.

---

## 🧹 Stop & Clean Up

### Stop services (keep images):

```bash
docker compose down
```

### Stop + remove volumes (e.g., PostgreSQL data):

⚠️ **Warning**: This deletes all database content!

```bash
docker compose down -v
```

---

## 🔐 Environment Variables (Optional Customization)

By default, `docker-compose.yml` defines:

| Service | Variable             | Default Value      |
|---------|----------------------|--------------------|
| DB      | `POSTGRES_USER`      | `appuser`          |
| DB      | `POSTGRES_PASSWORD`  | `secret`           |
| DB      | `POSTGRES_DB`        | `appdb`            |
| Backend | `PYTHONUNBUFFERED`   | `1` (stdout flush) |
| Frontend| `NODE_ENV`           | `production`       |

To customize:
- Create a `.env` file in the project root:

```env
# .env
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=myappdb
APP_HOST=0.0.0.0
APP_PORT=8000
```

Then re-run `docker compose up`.

---

## 📦 Troubleshooting

| Issue | Solution |
|-------|----------|
| Frontend fails to build (`nginx.conf` not found) | Ensure `frontend/nginx.conf` exists and is valid (see note above). |
| Port already in use (e.g., 8000, 3000, 5432) | Stop conflicting services or change port mappings in `docker-compose.yml`. |
| Backend can’t connect to DB (`connection refused`) | Wait ~10s for PostgreSQL startup; add healthcheck if needed. |

---

## 📝 License

MIT — see `LICENSE` file.
"""
```