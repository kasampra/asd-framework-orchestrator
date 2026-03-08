---
description: Phase 2 — Architecture design for AI Project Intake Manager
---

# Architecture Workflow

## Prerequisites
- Read `AGENTS.md` in project root.
- Read `.agent/artifacts/requirements.md`.

## Steps

1. **Define tech stack** (`.agent/knowledge/stack.md`):
   - Use Sovereign Stack defaults from AGENTS.md
   - Justify each choice for German SME context

2. **Design API contract** (`.agent/knowledge/openapi.yaml`):
   - Full OpenAPI 3.0 spec
   - All CRUD endpoints for projects
   - AI decomposition endpoint
   - PDF export endpoint
   - Auth endpoints (login, register, logout)
   - All routes scoped by `organisation_id`

3. **Design database schema** (`.agent/knowledge/schema.sql`):
   - Tables: organisations, users, projects, requirements, user_stories, risks
   - Retention policy: `created_at` + 90-day auto-delete
   - Indexes for performance

4. **Produce architecture diagram** (`.agent/artifacts/architecture.md`):
   - Text-based component diagram (Mermaid or ASCII)
   - Show: Frontend → API → AI Service → DB

5. **Produce folder structure** (`.agent/artifacts/folder-structure.md`):
   - Exact file/folder layout for backend, frontend, infra

## Output
Knowledge files to `.agent/knowledge/`, artifacts to `.agent/artifacts/`.

## HARD GATE
**Stop here. Await human approval before any code is written.**
