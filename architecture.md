# ASD Framework Architecture

This document describes the high-level architecture of the Agentic Software Delivery (ASD) Framework Orchestrator, a control plane for sovereign AI-driven engineering.

## System Topology

The ASD Orchestrator is a **Control Plane** that sits between an LLM (the Brain) and the File System (the Action), ensuring deterministic execution of a software lifecycle.

### 1. The Core Orchestration Engine (`src/orchestrator.py`)
-   **8-Phase SDLC Waterfall**: Manages the progression from Requirements to Deployment.
-   **Sub-Agent Context Isolation (`ArtifactManager`)**: Prevents "Context Pollution" by discarding the intermediate reasoning/thinking chains of sub-agents. Only finalized markdown artifacts are passed to the next phase's input.
-   **Autonomous Auto-Healing**: Handles gate failures by feeding critique back into the agent's prompt for a correction loop.
-   **Human-in-the-Loop (HITL)**: Provides a fallback mechanism for manual steering when automated healing fails.

### 2. The Control Plane Layer (`src/control_plane.py`)
-   **Real-time Observability**: Captures 4 types of telemetry for every single step (Decision Trace, Context Snapshot, Tool Selection, Intent-Execution Diff).
-   **Deterministic Lifecycle Hooks (`HookManager`)**: Fires system-level events (`pre_phase`, `post_phase`, `on_gate_evaluate`, `on_gate_fail`) that operate independently of LLM prompts.
-   **Three-Tier Context Compression (`ContextCompressor`)**: Prevents context window overflows for local models (e.g., Qwen) by applying tiered compression:
    -   **Tier 1 (MicroCompact)**: Strips comments, formatting, and empty lines via regex.
    -   **Tier 2 (AutoCompact)**: Semantically truncates code blocks while preserving signatures and docstrings.
    -   **Tier 3 (FullCompact)**: Uses a specialized LLM call to summarize the context into strict constraints and requirements.

### 3. The Memory Layer (`src/memory/`)
-   **Fingerprint Extractor**: Analyzes artifacts on disk (e.g., `requirements.txt`, `Dockerfile`) to identify the "ground truth" architectural decisions.
-   **Cost Tracker**: Accumulates token spend, duration, and compression telemetry per phase.
-   **Drift Detector**: Automatically diffs current decisions and economics against a project baseline (`.asd/fingerprints/baseline.json`).
-   **Governance**: Sugests **Cognitive RBAC Locks** in `logs/rbac_suggestions.md` to maintain project consistency.

### 4. The Configuration Layer (`config/`)
-   **Personas & Skills**: Defines agent roles and tool permissions (Cognitive RBAC).
-   **SDLC Instructions**: Global rules and constraints that govern every agentic action.

---

## Data Flow Diagram

```mermaid
graph TD
    User[User Prompt] --> Orchestrator
    
    subgraph Execution Loop
        Orchestrator --> AM[Artifact Manager]
        AM -->|Assembles Isolated Context| CC[Context Compressor]
        CC -->|Compressed Artifacts| Agent[Agent Brain]
        Agent --> proposal[Proposed Code Artifacts]
        proposal --> Hook[Hook Manager]
        Hook -->|Triggers Lifecycle Events| CP[Control Plane Trace]
        proposal --> Gate[Gatekeeper AI]
        Gate -- Fail -->|Healing Feedback| Agent
        Gate -- Pass -->|Finalize| Disk[(Physical Disk)]
    end
    
    subgraph Governance (Memory Layer)
        Disk -->|Scan Artifacts| Extractor[Memory Extractor]
        CP -->|Telemetry & Cost| Tracker[Cost Tracker]
        Extractor -->|Current Fingerprint| Detector[Drift Detector]
        Detector -->|Baseline Diff| Audit[logs/audit.md]
        Detector -->|Breaking Drift| RBAC[logs/rbac_suggestions.md]
    end
    
    Orchestrator -->|Final Report| Report[logs/control_plane.md]
```

---

## Failure Recovery Modes

1.  **Autonomous Healing**: Agent attempts to fix its own code based on Gatekeeper's critique (max retries configurable).
2.  **Human-in-the-Loop**: If retries fail, the system pauses and asks the human for steering feedback, force pass, or abortion.
3.  **Silent Drift Mitigation**: If the Memory Layer detects a breaking framework switch, it alerts the user in the audit logs before the drift becomes permanent.
