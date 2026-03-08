---
description: Phase 1 — Requirements gathering for AI Project Intake Manager
---

# Requirements Workflow

## Prerequisites
- Read `AGENTS.md` in project root first.

## Steps

1. **Understand the domain**: German SMEs submitting project briefs for AI-powered decomposition.

2. **Produce functional requirements** (`requirements.md`):
   - Project brief submission (title, description, industry, budget range, timeline)
   - AI-powered decomposition into user stories, risks, acceptance criteria
   - PDF export of structured requirements
   - Multi-tenant auth (organisation-scoped data)
   - GDPR compliance: 90-day retention, right to erasure, bilingual privacy notice

3. **Produce non-functional requirements** (append to `requirements.md`):
   - Response time < 5s for AI decomposition
   - Support 100 concurrent users
   - GDPR-compliant data storage (EU-hosted)
   - Accessibility: WCAG 2.1 AA

4. **Produce user stories** (`user-stories.md`):
   - Group by Epic → Story → Acceptance Criteria
   - Cover: submission, AI processing, results viewing, PDF export, auth, admin

5. **Produce risk register** (`risk-register.md`):
   - Top 5 risks with likelihood, impact, and mitigation strategy

## Output
All artifacts written to `.agent/artifacts/`.

## Gate
Await human review of all 3 artifacts before proceeding to Phase 2.
