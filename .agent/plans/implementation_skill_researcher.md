# Improvement Plan: Implementation of SkillResearcher

## 1. Target Files
*   `src/core/skill_researcher.py`: New module to analyze requirements vs. current skills.
*   `config/agents.yaml` or `AGENTS.md`: Targeted for autonomous updates.
*   `src/orchestrator.py`: Add a "Phase 0.5: Skill Alignment" step.

## 2. Proposed Implementation
1.  **Skill Gap Analysis**: Compare `Phase 1 Requirements` against the `AGENTS.md` skills list.
2.  **Skill Generation**: If a gap is found (e.g., "Needs Redis optimization"), create a new `Skill` definition.
3.  **Self-Mutation**: Update the project's own documentation and config files via agentic PR.

## 3. Success Metric
*   The Orchestrator must detect a requirement not covered by current agent roles and propose a specific update to `AGENTS.md`.
