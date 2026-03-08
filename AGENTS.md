# AGENTS.md — Agentic Software Delivery Framework

## Project Overview
AI Project Intake Manager: a web app where German SMEs submit project briefs and receive
AI-generated structured requirements documents (user stories, risks, acceptance criteria)
with PDF export.

## Behaviour Rules
1. Always read this file before starting any task.
2. Read `.agent/workflows/` before starting any phase.
3. Write all output artifacts to `.agent/artifacts/`.
4. Never modify files outside your assigned folder.
5. Never delete files without explicit human approval.
6. Write atomic commits: one commit per logical change, not per file.
7. Flag any security risk with `[SECURITY]` prefix in your response.

## HARD GATES — Agent Must Stop and Await Human Approval
- **After Phase 2** (Architecture complete) — before any application code is written.
- **After Phase 5** (Security Audit complete, see `05-security.md`) — before Deploy Agent runs.

## Folder Ownership
| Folder       | Owner            |
|-------------|------------------|
| `backend/`  | Backend Agent    |
| `frontend/` | Frontend Agent   |
| `infra/`    | Infra Agent      |
| `docs/`     | Docs Agent       |
| `.agent/`   | All agents (read), Planning agents (write) |

## Code Style
- **TypeScript**: strict mode always on.
- **Python**: type hints on all functions, Black formatter, Python 3.11+.
- All APIs must follow the `openapi.yaml` contract in `.agent/knowledge/`.
- All environment variables stored in `.env`, never hardcoded.

## Tech Stack (Sovereign Stack)
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Next.js 15 (TypeScript, App Router)
- **Database**: PostgreSQL (local: raw via docker-compose, prod: Supabase)
- **Auth**: Custom JWT (bcrypt + python-jose, scoped by `organisation_id`) — no Supabase required
- **Deployment**: Cloud Run (Docker)
- **LLM**: Gemini 2.0 Flash via Google AI SDK
- **GDPR**: EU-hosted, 90-day retention, right to erasure

## Output
- Always write a summary artifact at the end of every task.
- All artifacts go to `.agent/artifacts/`.
