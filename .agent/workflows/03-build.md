---
description: Phase 3–5 — Build backend, frontend, and infrastructure
---

# Build Workflow

## Prerequisites
- Read `AGENTS.md` in project root.
- Read `.agent/knowledge/openapi.yaml`, `schema.sql`, `stack.md`.
- Confirm Phase 2 HARD GATE has been passed (human-approved).

## Backend Agent (Phase 3) — `/backend/` only
1. Scaffold FastAPI app with `main.py` entry point
2. Implement all endpoints from `openapi.yaml`
3. Set up SQLAlchemy with `DATABASE_URL` env var in `app/db.py`
4. Add custom JWT auth middleware in `app/middleware/auth.py` (bcrypt + python-jose, no Supabase dependency)
5. Scope all `/projects` routes to authenticated user's `organisation_id`
6. Integrate Gemini AI for requirements decomposition in `app/services/ai_service.py`
7. Implement PDF export via reportlab in `app/services/pdf_service.py`
8. Implement `DELETE /projects/{id}` for GDPR right to erasure
9. Write tests in `backend/tests/`

## Frontend Agent (Phase 4) — `/frontend/` only
1. Scaffold Next.js 15 app with App Router
2. Build project brief submission form with GDPR privacy notice (EN/DE)
3. Build results display page
4. Build PDF download button
5. All API calls must match `openapi.yaml` exactly
6. Style with Tailwind CSS

## Infra Agent (Phase 5) — `/infra/` only
1. Create `backend.Dockerfile` (multi-stage, non-root user)
2. Create `frontend.Dockerfile` (multi-stage, non-root user)
3. Create `docker-compose.yml` with raw PostgreSQL for local dev
4. Create `.github/workflows/deploy.yml` for Cloud Run CI/CD

## Output
Working application code in `backend/`, `frontend/`, `infra/`.
