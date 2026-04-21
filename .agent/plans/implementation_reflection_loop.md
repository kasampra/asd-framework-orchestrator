# Improvement Plan: Implementation of Reflection Loop

## 1. Target Files
*   `src/orchestrator.py`: Add the `ReflectionManager` call to the `Execution Loop`.
*   `src/control_plane.py`: Update telemetry to capture the "Reflection Trace."

## 2. Proposed Implementation
1.  **New Module**: `src/reflection.py` to handle the `Reflector` class.
2.  **Workflow Change**:
    ```python
    # Current
    proposal = Agent.execute(context)
    result = Gatekeeper.evaluate(proposal)
    
    # New
    initial_draft = Agent.execute(context)
    critique = Reflector.critique(initial_draft) # New Step
    refined_draft = Agent.execute(context + critique) # New Step
    result = Gatekeeper.evaluate(refined_draft)
    ```

## 3. Success Metric
*   The system must log the "Critique" as an internal artifact in `.agent/artifacts/reflection_log.json`.
