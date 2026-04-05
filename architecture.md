# ASD Framework Architecture

This document describes the high-level architecture of the Agentic Software Delivery (ASD) Framework Orchestrator.

## System Topology

The ASD Orchestrator is a **Control Plane** that sits between an LLM (the Brain) and the File System (the Action).

### 1. The Core Orchestration Engine (`src/orchestrator.py`)
- Manages the 8-phase SDLC waterfall.
- Injects personas (from `config/agents.md`) into the LLM prompts.
- Enforces Hard Gates (Architecture, QA, Security) via the `Gatekeeper AI`.
- Handles autonomous auto-healing when a gate fails.

### 2. The Control Plane Layer (`src/control_plane.py`)
- Provides real-time observability.
- Records **Decision Traces**, **Context Snapshots**, and **Intent-Execution Diffs**.
- Exports full pipeline reports to `logs/control_plane.md`.

### 3. The Memory Layer (`src/memory/`)
- **Fingerprint Extractor:** Analyzes artifacts on disk (e.g., `requirements.txt`, `Dockerfile`) to identify the "ground truth" architectural decisions.
- **Cost Tracker:** Accumulates token spend and duration per phase, writing `logs/cost_report.json`.
- **Baseline Store:** Persists the project's first run as the "golden state" in `.asd/fingerprints/baseline.json`.
- **Drift Detector:** Automatically diffs current decisions and economics against the baseline.
- **Governance:** Detects framework and economic drift, suggesting **Cognitive RBAC Locks** to maintain project consistency.

### 4. The Configuration Layer (`config/`)
- **Agents:** Defines personas and phase assignments.
- **Skills:** Defines tool permissions (Cognitive RBAC).
- **Instructions:** Global SDLC rules and constraints.

---

## Data Flow Diagram

```mermaid
graph TD
    User[User Prompt] --> Orchestrator
    
    subgraph Execution Loop
        Orchestrator -->|Phase Objective| Agent[Agent Brain]
        Agent -->|Proposal| CP[Control Plane]
        CP -->|Validate| Gate[Gatekeeper AI]
        Gate -- Fail -->|Healing Feedback| Agent
        Gate -- Pass -->|Write| Disk[(Physical Disk)]
    end
    
    subgraph Governance (Memory Layer)
        Disk -->|Scan Artifacts| Extractor[Memory Extractor]
        CP -->|Telemetry| Tracker[Cost Tracker]
        Tracker -->|Report| Extractor
        Extractor -->|Current Fingerprint| Detector[Drift Detector]
        Detector -->|Baseline Diff| Audit[logs/audit.md]
        Detector -->|Breaking Drift| RBAC[logs/rbac_suggestions.md]
    end
    
    Orchestrator -->|Final Report| Report[logs/control_plane.md]
```

---

## Core Decision Fields (Memory Layer)

The framework monitors these 17 critical fields to ensure project stability:

| Category | Fields |
| :--- | :--- |
| **Architecture** | `web_framework`, `database`, `auth_pattern`, `async_pattern`, `folder_structure` |
| **Infrastructure** | `base_image`, `compose_version`, `ci_provider`, `port_mapping` |
| **Quality** | `test_runner`, `coverage_threshold`, `linter`, `dependency_manager` |
| **Economics** | `total_tokens`, `total_cost_usd`, `most_expensive_phase`, `token_budget_exceeded` |

---

## Failure Recovery Modes

1.  **Autonomous Healing:** Agent attempts to fix its own code based on Gatekeeper's critique.
2.  **Human-in-the-Loop:** If retries fail, the system pauses and asks the human for steering feedback via the TUI/Terminal.
3.  **Silent Drift Mitigation:** If the Memory Layer detects a breaking framework switch, it alerts the user and provides a fix before the drift becomes permanent.
