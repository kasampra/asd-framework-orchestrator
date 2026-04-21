# Research: Reflection-Driven Refinement (RDD)

## 1. The Pattern
*   **Concept**: Based on the "Reflexion" (Shinn et al.) and "Self-Refine" (Madaan et al.) patterns.
*   **Problem**: Agents often produce "hallucinated" or "lazy" code in the first pass. Relying solely on a Gatekeeper (Phase Gate) creates high latency and "Failure Ping-Pong."
*   **Solution**: Insert a **Self-Critique** step. The agent generates code, then switches to a "Critic" persona to find bugs, and finally produces a refined version—all before the human or the formal Gatekeeper sees it.

## 2. Benefits for ASD Framework
*   **Lower Gate Failure Rate**: Gatekeeper only sees high-quality "v2" or "v3" artifacts.
*   **Deterministic Reasoning**: The "Critique" becomes a logged artifact in the Control Plane, providing better observability.
*   **Sovereign Efficiency**: Reduces total calls to the Gatekeeper (which might be a more expensive/slower local model).

## 3. Knowledge Nugget (Series Idea)
*   **Title**: "Don't let your agents be lazy—give them a mirror."
*   **Summary**: How adding a reflection loop saved 40% in token spend by catching bugs locally before they reached the expensive orchestrator gate.
