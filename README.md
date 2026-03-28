# 🤖 ASD Framework Orchestrator v3.0

**A 100% Free, Fully Local, 8-Agent Software Development Life Cycle (SDLC) Execution Engine.**

This repository is the official automation CLI and Control Plane for the [Agentic Software Delivery (ASD) Framework](https://github.com/kasampra/Agentic-Software-Delivery-Framework). It leverages your local Large Language Models (like Qwen via LMStudio) to autonomously architect, write, test, and containerize full-stack applications directly on your host machine—with zero cloud dependencies and maximum governance.

---

## 🏗️ The 8-Agent Architecture

This Orchestrator abandons the brittle "mega-prompt" approach. Instead, it sequentially injects 8 specialized personas into your local LLM, pulling them through a strict, multi-gated pipeline:

1. **Requirements Engineer** (Phase 1)
2. **System Architect** (Phase 2 & Gate 1)
3. **Backend Developer** (Phase 3)
4. **Frontend Developer** (Phase 4)
5. **DevOps Engineer** (Phase 5)
6. **QA Engineer** (Phase 6 & Gate 2)
7. **Security Analyst** (Phase 7 & Gate 3)
8. **Technical Writer** (Phase 8)

---

## ⚙️ v3.0 Modular Configuration (Cognitive RBAC)

In v3.0, the framework’s intelligence has been fractured into a scalable microservice-like configuration layer. You no longer need to edit Python code to change agent behaviors. 

Everything is governed by the `config/` directory:
1. **Identity (`config/agents.md`)**: The topology map assigning specific SDLC phases to designated Agent Personas.
2. **Capability (`config/skills.md`)**: **Cognitive Role-Based Access Control (RBAC)**. This rigidly maps which specific execution tools (MCP) an agent is authorized to invoke. If the Requirements Engineer attempts to hallucinate a shell command, the system intercepts and denies it.
3. **Alignment (`config/instructions.md`)**: The global constraints governing the framework (output formatting, mandated tech stacks, code styles, and operational rules).

---

## 🛡️ v2.0 Resilience & Human-in-the-Loop

The engine is engineered for operational survival. It is not a blind generator; it is a self-healing system:
* **Autonomous Auto-Healing:** If the Gatekeeper AI rejects an agent's code at a hard gate (e.g., missing security middleware), the Orchestrator autonomously feeds the Gatekeeper's strict reasoning back to the agent in a bounded retry loop, forcing the agent to heal its own code.
* **Interactive Handoffs:** If the agent exhausts its auto-retries, the engine safely halts execution and prompts the human architect (you) in the terminal to provide manual, steering feedback, force-pass the gate, or abort.
* **Live Terminal Dashboard (TUI):** A stunning, real-time split-pane Textual UI that live-streams the agent's inner `<think>` reasoning while tracking pipeline phase progression.
* **AST Validation Sandbox:** The QA Agent possesses a physical terminal execution tool, allowing it to autonomously run `pytest` and `npm lint` to physically validate its code before passing a phase.

---

## 🔍 The Control Plane Layer

The Orchestrator includes a deep **Control Plane** that sits between cognitive reasoning and physical action. For every step, it records:
* **Decision Trace:** The agent's raw thinking block and sub-task decomposition.
* **Context Snapshot:** Exactly what specifications the agent was viewing when it made a decision.
* **Intent-Execution Diff:** The difference between what the agent hallucinated and the physical code it successfully executed on disk.

Every pipeline run yields a detailed `logs/audit.md` and `logs/control_plane.md` report.

---

## 🚀 Quickstart

### 1. Setup LMStudio (The AI Brain)
1. Download and install [LMStudio](https://lmstudio.ai/).
2. Load a highly capable coding model (e.g., Qwen 2.5 Coder 7B).
3. Start the Local Server on `http://127.0.0.1:1234/v1`.

### 2. Install the Orchestrator
```bash
git clone https://github.com/kasampra/asd-framework-orchestrator.git
cd asd-framework-orchestrator
python -m venv venv
# Windows: .\venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate an Application!
You can run the Orchestrator natively in your terminal using the new Textual UI:

```bash
python src/tui.py "Build a sleek secure Hello World REST API with tests and docker"
```

*Note: The script dynamically detects your execution directory and drops the generated codebase perfectly scoped into your workspace.*

---

## 🏆 Proof of Concept: The Hello World App

See the `examples/tui-generated-app/` directory for a pristine, 100% autonomously generated application triggered completely by the TUI. The orchestrator successfully orchestrated the backend, frontend, infrastructure, and a passing test suite with zero human intervention.

---

## License
MIT — fork it, use the framework, and build your own sovereign AI systems.

---

*Part of the [OwnYourIntelligence Series](https://www.linkedin.com/build-relation/newsletter-follow?entityUrn=7410977532142874624) — because sovereign AI isn't about rejecting capabilities. It's about controlling where your data lives, how your systems are built, and who holds the keys.*
