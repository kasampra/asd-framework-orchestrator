# Phase Checkpoint & Resume System — Delivery Summary

**Feature:** Phase Checkpoint & Resume System  
**Status:** ✅ Complete  
**Commit scope:** `feat(session): add phase checkpoint and resume capability`

---

## What Was Built

### New Files

| File | Purpose |
|------|---------|
| `src/session/__init__.py` | Package init — exports `CheckpointManager`, `SessionStore`, `SessionMeta` |
| `src/session/checkpoint_manager.py` | Atomic per-phase checkpoint save/load with cascade invalidation |
| `src/session/session_store.py` | JSON session index with status tracking and progress metrics |

### Modified Files

| File | Changes |
|------|---------|
| `src/orchestrator.py` | Added `--resume`, `--rerun-phase`, `--list-sessions` CLI flags; wrapped all 8 phases in `_run_phase_checkpointed()`; added `try/except` to mark sessions as `partial`/`failed` on crash |
| `src/tui.py` | Added `SessionBrowser` DataTable panel, resume banner, `[S]` toggle, checkpoint-skip phase detection |

---

## How It Works

### Fresh Run
```bash
python src/orchestrator.py "Build a todo app" --project my-app
```
- Generates a new `run_id` (e.g. `20260526_212230`)
- Creates a session record in `.asd/sessions.json`
- After each phase: writes `💾 .asd/checkpoints/20260526_212230/<phase>.json`
- On completion: marks session `complete`
- On crash/Ctrl+C: marks session `partial` or `failed`

### Resume After Crash
```bash
python src/orchestrator.py "Build a todo app" --resume 20260526_212230
```
- Loads checkpoint directory for the run
- Prints which phases are already complete
- For each phase: loads output from disk (⏭ skipped) if checkpoint exists, else executes normally
- Resumes exactly where the pipeline left off

### Force Re-run a Specific Phase
```bash
python src/orchestrator.py "Build a todo app" --resume 20260526_212230 --rerun-phase "Phase 6 QA Testing"
```
- Invalidates checkpoints for Phase 6, 7, and 8 (cascade)
- Phases 1–5 still load from cache
- Only Phase 6+ are re-executed

### List All Sessions
```bash
python src/orchestrator.py --list-sessions
```
Prints a Rich table:
```
 #  Run ID              Project   Status       Progress         Last Phase
 1  20260526_212230     my-app    ✅ complete   100% (8/8)       Phase 8 Deployment
 2  20260526_190011     my-app    ⏸️ partial    62% (5/8)        Phase 5 Infrastructure
```

---

## Storage Layout

```
.asd/
  sessions.json                         ← session index (atomic writes)
  checkpoints/
    20260526_212230/
      phase_1_requirements.json
      phase_2_architecture.json
      phase_3_backend.json
      ...
      phase_8_deployment.json
```

Each checkpoint JSON contains:
```json
{
  "run_id": "20260526_212230",
  "phase_name": "Phase 3 Backend",
  "timestamp": "2026-05-26T21:23:45.123456",
  "output": "... full LLM output ...",
  "input_tokens": 3842,
  "output_tokens": 1201,
  "duration_seconds": 67.4,
  "gate_decision": null,
  "compression_tier": 1
}
```

---

## Verification Checklist

- [ ] Run orchestrator and kill mid-pipeline (`Ctrl+C` at Phase 4)
- [ ] Confirm session shows `partial` in `--list-sessions`
- [ ] Resume — verify Phases 1–3 show `⏭ loaded from checkpoint (skipped)`
- [ ] Verify Phase 4 executes normally from the checkpoint boundary
- [ ] Run `--rerun-phase "Phase 6 QA Testing"` and verify Phase 5 is cached, Phase 6 re-runs
- [ ] Verify `.tmp` files are cleaned up after each checkpoint write
- [ ] Verify session shows `complete` at end of full pipeline

---

## Security Notes

- [SECURITY] Checkpoints store raw LLM output on disk — no encryption. If the pipeline processes sensitive credentials or PII, checkpoint files should be excluded from version control via `.gitignore` entry for `.asd/checkpoints/`.
- Atomic writes (`.tmp` → rename) prevent partial checkpoint files from poisoning a future resume.
