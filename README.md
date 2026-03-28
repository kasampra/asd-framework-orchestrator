# 🤖 ASD Framework Orchestrator

**The Agentic Software Delivery (ASD) Execution Kernel** 

A 100% Free, Fully Local, 8-Agent Software Development Life Cycle (SDLC) Execution Engine designed for deterministic control, observability, and human-in-the-loop intervention. 

This repository is the official automation Control Plane for the [Agentic Software Delivery Framework](https://github.com/kasampra/Agentic-Software-Delivery-Framework).

![Control Plane Header](https://img.shields.io/badge/Architecture-Control_Plane-00C7B7?style=for-the-badge) ![State](https://img.shields.io/badge/Agentic_AI-Local_Execution-000000?style=for-the-badge)

---

## 📖 The Philosophy: Moving Beyond "Prompt Spaghetti"
Most agentic frameworks today optimize for *demo success*—chaining unstructured LLM calls together and letting them write directly to your hard drive. They observe reasoning, but they trust reasoning as a primitive.

**The ASD Orchestrator optimizes for deterministic control.** 

We introduced a structure most developers skip: **Execution → Observation → Intervention → Recovery**.
The moment you run this Orchestrator, you insert a physical **transaction boundary** between the LLM's hallucinated *proposal* and the system's actual write-to-disk *action*.

---

## 🏗️ The 8-Agent Waterfall Workflow

The orchestrator abandons the brittle "mega-prompt" approach. Instead, it dynamically pulls your local LLM (like Qwen or LLaMA) through a strict, 8-phase SDLC sequence. Every phase is strictly isolated and gated.

| Phase | Agent Persona | Objective & Output |
| :--- | :--- | :--- |
| **Phase 1** | Requirements Engineer | Ingests the raw prompt, negotiates ambiguity, and outputs a strict Markdown PRD (Product Requirements Document). |
| **Phase 2** | System Architect | Intercepts the PRD. Designs the system architecture, component boundaries, and security stack. |
| **Gate 1** | **Gatekeeper AI** | *Architecture Review:* Ensures the architect included CORS, Auth, and Framework constraints. |
| **Phase 3** | Backend Developer | Generates DB schemas, endpoints, and middleware strictly matching the Phase 2 architecture. |
| **Phase 4** | Frontend Developer | Generates client-side React/Next components targeting the Phase 3 backend endpoints. |
| **Phase 5** | DevOps Engineer | Generates `Dockerfile`, `docker-compose.yml`, and CI/CD yaml pipelines. |
| **Phase 6** | QA Testing Engineer | Uses MCP terminal tools to run physical `pytest` validations on the generated code. |
| **Gate 2** | **Gatekeeper AI** | *QA Review:* Blocks execution if test coverage is failing or syntax errors exist. |
| **Phase 7** | Security Analyst | Performs static analysis (SAST) and outputs vulnerability audits. |
| **Gate 3** | **Gatekeeper AI** | *Security Review:* Blocks deployment if injection or access control flaws are detected. |
| **Phase 8** | Technical Writer | Generates the `README.md` and user deployment instructions. |

---

## 🔍 The Control Plane Layer

Between every single phase above, the system passes through the **Control Plane** — an enforcement boundary. 

For every single step, it physically records:
1. **Decision Trace:** The agent's raw `<think>` block trajectory.
2. **Context Snapshot:** Exactly what documents the agent was viewing when it made its decision.
3. **Tool Selection Record:** Which terminal commands or Python functions it tried to inject.
4. **Intent-Execution Diff:** The difference between what the agent hallucinated, and what code actually survived compilation onto your disk.

This makes debugging surgical and makes errors attributable to a specific persona. *You can view all of this in the `logs/control_plane.md` and `logs/audit.md` files generated during runtime.*

---

## 🛡️ v2.0 Resilience & Visual Feedback

The engine is engineered for operational survival. It handles failures gracefully through a multi-tiered resilience tree visible entirely through our **Textual UI (TUI)** dashboard.

### 1. Autonomous Auto-Healing
When the Gatekeeper AI rejects an agent's code at a hard gate (e.g., missing middleware), the Orchestrator doesn't crash. It autonomously feeds the Gatekeeper's strict rejection reason back to the agent in a bounded retry loop, forcing the agent to heal its own code.

### 2. Interactive Human Handoffs (The Ultimate Override)
If the agent exhausts its auto-retries, the engine safely halts execution. The **Visual TUI Dashboard** blinks red, pausing the pipeline and asking the human architect (you) in the terminal to:
- Provide manual, steering keyboard feedback
- Force-pass the gate
- Abort execution entirely

### 3. AST Validation Sandbox
The QA Agent possesses physical terminal execution capabilities via Model Context Protocol (MCP). It can autonomously compile abstract syntax trees and run `pytest` to physically validate code before passing a phase.

---

## ⚙️ v3.0 Modular Configuration (Cognitive RBAC)

In v3.0, the framework’s intelligence has been fractured into a scalable microservice-like configuration layer. You no longer need to edit Python code to mutate agent behaviors. 

Everything is governed strictly by the `config/` directory:
1. **Identity (`config/agents.md`)**: The topology map assigning specific SDLC phases to designated Agent Personas.
2. **Capability (`config/skills.md`)**: **Cognitive Role-Based Access Control (RBAC)**. This rigidly maps which specific execution tools (MCP) an agent is authorized to invoke. If the Requirements Engineer attempts to hallucinate a destructive shell command, the system intercepts and denies it.
3. **Alignment (`config/instructions.md`)**: The global constraints governing the framework (output formatting, mandated tech stacks, code styles, and operational rules).

---

## 🚀 Quickstart Guide

### 1. Setup LMStudio (The Local Brain)
1. Download and install [LMStudio](https://lmstudio.ai/).
2. Load a highly capable coding model (e.g., Qwen 2.5 Coder 7B).
3. Start the Local API Server on `http://127.0.0.1:1234/v1`.

### 2. Install the Orchestrator
```bash
git clone https://github.com/kasampra/asd-framework-orchestrator.git
cd asd-framework-orchestrator
python -m venv venv
# Windows: .\venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate a Microservice
Run the Orchestrator natively in your terminal using the stunning Live Control Plane TUI:

```bash
python src/tui.py "Build a sleek secure Hello World REST API with tests and docker"
```

*Note: The script dynamically detects your execution directory and drops the generated codebase perfectly scoped into your workspace.*

---

## 🏆 Proof of Concept
See the `examples/hello-world-fullstack/` directory for a pristine, 100% autonomously generated application triggered completely by the TUI. The orchestrator successfully negotiated the backend, frontend, infrastructure, and a passing test suite with zero human intervention.

---

## License
MIT — fork it, use the framework, and build your own sovereign AI systems.

---

*Part of the [OwnYourIntelligence Series](https://www.linkedin.com/build-relation/newsletter-follow?entityUrn=7410977532142874624) — because sovereign AI isn't about rejecting capabilities. It's about controlling where your data lives, how your systems are built, and who holds the keys.*
