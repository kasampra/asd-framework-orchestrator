---
description: Phase 7 — Security audit for AI Project Intake Manager
---

# Security Workflow

## Prerequisites
- Read `AGENTS.md` in project root.
- All build phases (3–5) must be complete.
- This agent is **read-only** — do NOT modify any source code.

## Checks

1. **Authentication**:
   - All `/projects` routes require valid JWT
   - Test with missing auth header → expect 401 response
   - Verify `organisation_id` scoping prevents cross-tenant access

2. **Secrets exposure**:
   - Grep for `GOOGLE_API_KEY`, `DATABASE_URL`, `JWT_SECRET` in source files
   - Verify `.env` is in `.gitignore`
   - Check no hardcoded credentials in Dockerfiles or CI/CD

3. **SQL injection**:
   - Verify all SQL queries use parameterized inputs (SQLAlchemy ORM)
   - No f-strings or string concatenation in SQL queries

4. **XSS**:
   - Verify frontend sanitizes user input before rendering
   - Check for `dangerouslySetInnerHTML` usage

5. **Docker security**:
   - Containers must run as non-root user
   - No unnecessary ports exposed
   - Base images use specific tags (no `latest`)

6. **OWASP Top 10** general scan across the codebase.

## Output
`.agent/artifacts/security-audit.md` with findings rated: Critical / High / Medium / Low.

## HARD GATE
**After both QA and Security are complete, stop and await human approval before Deploy Agent runs.**
