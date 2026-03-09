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

*You can view the exact underlying rules for these agents in the `AGENTS.md` and `.agent/workflows/` directories.*

---

## 🚀 Quickstart: Running it Locally

### 1. Setup LMStudio (The AI Brain)
1. Download and install [LMStudio](https://lmstudio.ai/).
2. Download the **Qwen (Coder) 2.5/3.0** model (e.g., `qwen2.5-coder-7b-instruct`).
3. Start the Local Server in LMStudio (ensure it runs on `http://127.0.0.1:1234/v1`).

### 2. Install the Orchestrator
```bash
git clone https://github.com/your-username/asd-framework-orchestrator.git
cd asd-framework-orchestrator
python -m venv venv
# Windows: .\venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate an Application!
Just tell the CLI what you want to build at the root of the repository:
```bash
python src/orchestrator.py "Build me a fully secure, dark-mode Todo App with FastAPI and React"
```

The CLI will spin up, load the `AGENTS.md` rules, generate the files, pass them through the Gatekeeper validations, extract the physical code files to your hard drive, and write an audit trail to `logs/audit.md`!

---

## 🏆 Proof of Concept: The Hello World App

To prove the capability of this local framwork, see the `examples/hello-world-fullstack/` directory.

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
- Backend: `http://localhost:8000/health`
