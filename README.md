# ASD Framework Orchestrator

**A 100% Free, Fully Local, 8-Agent Software Development Life Cycle (SDLC) Execution Engine.**

This repository is the official automation CLI for the [Agentic Software Delivery (ASD) Framework]([https://github.com/kasampra/Agentic-Software-Delivery-Framework]). It leverages your local Qwen model (via LMStudio) to autonomously architect, write, test, and containerize full-stack applications on your hard drive with zero cloud dependencies.
https://github.com/kasampra/Agentic-Software-Delivery-Framework

---

## 🤖 The 8-Agent Architecture

This Orchestrator does not use a single "mega-prompt". Instead, `src/orchestrator.py` dynamically injects 8 distinct personas into your local LLM, executing the SDLC in a strict, gated sequence:

1. **Requirements Engineer** (Phase 1)
2. **System Architect** (Phase 2 & Gate 1)
3. **Backend Developer** (Phase 3)
4. **Frontend Developer** (Phase 4)
5. **DevOps Engineer** (Phase 5)
6. **QA Engineer** (Phase 6 & Gate 2)
7. **Security Analyst** (Phase 7 & Gate 3)
8. **Technical Writer** (Phase 8)

### ⚙️ v3.0 Configuration Boundary (Cognitive RBAC)
The Orchestrator's intelligence is fractured into three distinct configuration files inside the `config/` directory, making it infinitely scalable for enterprise teams without touching Python code:
1. **Identity (`config/agents.md`)**: The topology mapping Phases to Agent Personas.
2. **Capability (`config/skills.md`)**: Cognitive Role-Based Access Control (RBAC). It rigidly maps which MCP tools an agent is authorized to use. If the Requirements Engineer tries to hallucinate a shell command, the control plane intercepts and denies the request.
3. **Alignment (`config/instructions.md`)**: The global constraints and system prompts governing the framework (e.g., output formatting, tech stack, and compliance rules).

---

## 🔍 The Control Plane

The Orchestrator includes a **Control Plane** — a layer that sits between the agent's reasoning and the agent's action. Every decision passes through it before anything executes.

For every single step, the control plane captures:

| Capture | What it records |
|---------|----------------|
| **Decision Trace** | The agent's full reasoning chain — which goal it was pursuing, which sub-tasks it decomposed, and which path it chose. |
| **Context Snapshot** | The exact documents, specifications, and prior agent outputs loaded into the prompt at the moment of the decision. |
| **Tool Selection Record** | Which tools the agent considered, which one it picked, and what inputs it passed. |
| **Intent-to-Execution Diff** | The difference between what the agent planned to do and what it actually executed. |

After every run, the control plane generates:
- A **terminal summary table** via `rich` showing all phases, durations, gate decisions, and reasoning previews.
- A detailed **`logs/control_plane.md`** report with the full trace for every step.

This makes debugging surgical, trust earned (not assumed), and errors attributable to a specific agent reading a specific document.

---

## 🛡️ Orchestrator v2.0 Resilience Features

The engine is now a self-healing, human-in-the-loop system:
- **Autonomous Self-Healing:** If the Gatekeeper AI rejects an agent's code, the Orchestrator autonomously feeds the Gatekeeper's reasoning back to the agent in a bounded retry loop, allowing the agent to fix its own bugs.
- **Interactive Human Handoffs:** If the agent fails to heal the code twice, the engine pauses and directly asks the human architect (you) to provide manual context, force pass the gate, or abort.
- **Live Terminal Dashboard (TUI):** Run the orchestrator inside a stunning, real-time split-pane terminal UI that live-streams the agent's inner `<think>` reasoning while tracking pipeline progress.
- **AST Execution Sandbox:** The QA Agent is wired to physical terminal access, allowing it to natively run `pytest` and `npm lint` to physically validate the codebase.

---

## 🚀 Quickstart: Running it Locally

### 1. Setup LMStudio (The AI Brain)
1. Download and install [LMStudio](https://lmstudio.ai/).
2. Download the **Qwen (Coder) 2.5/3.0** model (e.g., `qwen2.5-coder-7b-instruct`).
3. Start the Local Server in LMStudio (ensure it runs on `http://127.0.0.1:1234/v1`).

### 2. Install the Orchestrator
```bash
git clone https://github.com/kasampra/asd-framework-orchestrator.git
cd asd-framework-orchestrator
python -m venv venv
# Windows: .\venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate an Application!
You have two ways to run the Orchestrator:

**Standard CLI Mode:**
```bash
python src/orchestrator.py "Build me a fully secure, dark-mode Todo App with FastAPI and React"
```

**Live TUI Dashboard Mode (Recommended):**
```bash
python src/tui.py "Build a sleek secure Hello World API with tests and docker"
```

The CLI will spin up, load the `AGENTS.md` rules, generate the files, pass them through the Gatekeeper validations, extract the physical code files to your hard drive, and write:
- An audit trail to `logs/audit.md`
- A full Control Plane trace to `logs/control_plane.md`

---

## 🏆 Proof of Concept: The Hello World App

To prove the capability of this local framework, see the `examples/hello-world-fullstack/` directory.

This exact directory was generated **100% autonomously** by the Orchestrator running Qwen in response to the prompt: *"Build a sleek secure Hello World API with tests and docker"*.

The orchestrator successfully:
1. Designed the architecture.
2. Built the FastAPI backend (`backend/app/main.py`).
3. Built the React frontend (`frontend/src/App.tsx`).
4. Containerized the PostgreSQL database (`docker-compose.yml`).
5. Generated a `pytest` suite that achieved a 100% pass rate.

**To test the generated proof-of-concept yourself:**
```bash
cd examples/hello-world-fullstack
docker-compose up --build
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/api/health`

---

## License

MIT — fork it, use the framework, and build your own sovereign AI systems.

---

*Part of the [OwnYourIntelligence Series](https://www.linkedin.com/build-relation/newsletter-follow?entityUrn=7410977532142874624) — because sovereign AI isn't about rejecting capabilities. It's about controlling where your data lives, how your systems are built, and who holds the keys. #ownYourIntelligence*
