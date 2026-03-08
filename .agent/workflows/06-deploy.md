---
description: Phase 8 — Deploy AI Project Intake Manager to Cloud Run
---

# Deploy Workflow

## Prerequisites
- Read `AGENTS.md` in project root.
- Read `.agent/artifacts/test-report.md` — must show zero Critical issues.
- Read `.agent/artifacts/security-audit.md` — must show zero Critical issues.
- Phase 6–7 HARD GATE must have been passed (human-approved).

## Steps

1. **Validate reports**: Confirm no Critical issues in QA and Security reports.
2. **Deploy to staging**: Use GitHub Actions pipeline in `.github/workflows/deploy.yml`.
3. **Smoke tests on staging**:
   - Hit health endpoint
   - Submit a test project brief via API
   - Verify PDF download works
4. **Promote to production**: If smoke tests pass.
5. **Produce deploy report** (`.agent/artifacts/deploy-report.md`):
   - Staging URL
   - Production URL
   - Smoke test results (pass/fail)

## Output
`.agent/artifacts/deploy-report.md`
