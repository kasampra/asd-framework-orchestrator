"""
test_checkpoint_resume.py
Complete test suite for the Phase Checkpoint & Resume System.

Tests:
  1. CheckpointManager — save, load, invalidate, cascade, atomic writes
  2. SessionStore — create, update_phase, record_gate, mark_complete, mark_partial, list
  3. Orchestrator CLI — --help, --list-sessions, --resume (invalid), --rerun-phase (invalid)
  4. End-to-end dry-run — simulates 3 phases completing, then a crash + resume
"""

import json
import os
import sys
import shutil
import tempfile
import subprocess
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Colour helpers for terminal output
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0

def ok(msg: str):
    global passed
    passed += 1
    print(f"  {GREEN}PASS{RESET}  {msg}")

def fail(msg: str, detail: str = ""):
    global failed
    failed += 1
    print(f"  {RED}FAIL{RESET}  {msg}")
    if detail:
        print(f"         {YELLOW}{detail}{RESET}")

def section(title: str):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

def assert_eq(a, b, label: str):
    if a == b:
        ok(label)
    else:
        fail(label, f"Expected {b!r}, got {a!r}")

def assert_true(cond: bool, label: str, detail: str = ""):
    if cond:
        ok(label)
    else:
        fail(label, detail)

def assert_false(cond: bool, label: str):
    if not cond:
        ok(label)
    else:
        fail(label, f"Expected False but got True")

# ---------------------------------------------------------------------------
# Set up a temporary working directory so tests don't pollute .asd/
# ---------------------------------------------------------------------------
TMP_DIR = tempfile.mkdtemp(prefix="asd_test_")

def setup_tmp_asd():
    """Create a minimal .asd directory structure in TMP_DIR."""
    asd = Path(TMP_DIR) / ".asd"
    (asd / "checkpoints").mkdir(parents=True, exist_ok=True)
    (asd / "fingerprints").mkdir(parents=True, exist_ok=True)
    return asd


# ============================================================
# SECTION 1 — CheckpointManager
# ============================================================
section("1 — CheckpointManager unit tests")

# Temporarily point CheckpointManager at the tmp dir
os.chdir(TMP_DIR)
setup_tmp_asd()

# Add src/ to sys.path — resolve relative to this test file, not CWD
SRC = str(Path(__file__).parent.parent / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from session.checkpoint_manager import CheckpointManager

RUN_ID = "20260526_213600"
cm = CheckpointManager(RUN_ID)

# 1.1 save & load
cm.save("Phase 1 Requirements", "req output text", input_tokens=100, output_tokens=50, duration_seconds=12.3)
cp = cm.load("Phase 1 Requirements")
assert_true(cp is not None, "1.1a  load() returns dict after save()")
assert_eq(cp["phase_name"], "Phase 1 Requirements", "1.1b  phase_name stored correctly")
assert_eq(cp["output"], "req output text", "1.1c  output stored correctly")
assert_eq(cp["input_tokens"], 100, "1.1d  input_tokens stored correctly")
assert_eq(cp["duration_seconds"], 12.3, "1.1e  duration_seconds stored correctly")

# 1.2 load_output shortcut
out = cm.load_output("Phase 1 Requirements")
assert_eq(out, "req output text", "1.2   load_output() returns raw string")

# 1.3 missing phase returns None
assert_true(cm.load("Phase 99 Missing") is None, "1.3   load() returns None for missing phase")
assert_true(cm.load_output("Phase 99 Missing") is None, "1.3b  load_output() returns None for missing phase")

# 1.4 gate_decision stored
cm.save("Phase 2 Architecture", "arch output", gate_decision="PASS")
cp2 = cm.load("Phase 2 Architecture")
assert_eq(cp2["gate_decision"], "PASS", "1.4   gate_decision stored correctly")

# 1.5 get_completed_phases
cm.save("Phase 3 Backend", "backend output")
completed = cm.get_completed_phases()
assert_true("Phase 1 Requirements" in completed, "1.5a  get_completed_phases includes Phase 1")
assert_true("Phase 2 Architecture" in completed, "1.5b  get_completed_phases includes Phase 2")
assert_true("Phase 3 Backend" in completed, "1.5c  get_completed_phases includes Phase 3")
assert_eq(len(completed), 3, "1.5d  get_completed_phases returns exactly 3 items")

# 1.6 invalidate
assert_true(cm.invalidate("Phase 3 Backend"), "1.6a  invalidate() returns True when checkpoint existed")
assert_true(cm.load("Phase 3 Backend") is None, "1.6b  invalidated checkpoint returns None on load")
assert_false(cm.invalidate("Phase 3 Backend"), "1.6c  invalidate() returns False when already gone")

# 1.7 invalidate_from cascade
ALL_PHASES = [
    "Phase 1 Requirements",
    "Phase 2 Architecture",
    "Phase 3 Backend",
    "Phase 4 Frontend",
    "Phase 5 Infrastructure",
    "Phase 6 QA Testing",
    "Phase 7 Security",
    "Phase 8 Deployment",
]
for p in ["Phase 4 Frontend", "Phase 5 Infrastructure", "Phase 6 QA Testing"]:
    cm.save(p, f"output for {p}")

invalidated = cm.invalidate_from("Phase 4 Frontend", ALL_PHASES)
assert_true("Phase 4 Frontend" in invalidated, "1.7a  cascade invalidates Phase 4")
assert_true("Phase 5 Infrastructure" in invalidated, "1.7b  cascade invalidates Phase 5")
assert_true("Phase 6 QA Testing" in invalidated, "1.7c  cascade invalidates Phase 6")
assert_true("Phase 1 Requirements" not in invalidated, "1.7d  Phase 1 NOT in cascade (upstream)")
assert_true("Phase 2 Architecture" not in invalidated, "1.7e  Phase 2 NOT in cascade (upstream)")

# 1.8 for_existing_run factory
cm2 = CheckpointManager.for_existing_run(RUN_ID)
assert_true(cm2 is not None, "1.8a  for_existing_run returns manager for valid run")
assert_true(CheckpointManager.for_existing_run("nonexistent_run") is None,
            "1.8b  for_existing_run returns None for missing run")

# 1.9 list_all_run_ids
ids = CheckpointManager.list_all_run_ids()
assert_true(RUN_ID in ids, "1.9   list_all_run_ids includes our run")

# 1.10 atomic write: verify no .tmp file left behind after save
cm.save("Phase 7 Security", "sec output")
tmp_files = list(Path(TMP_DIR, ".asd", "checkpoints", RUN_ID).glob("*.tmp"))
assert_eq(len(tmp_files), 0, "1.10  No .tmp files remain after save (atomic write confirmed)")

# 1.11 overwrite existing checkpoint
cm.save("Phase 1 Requirements", "UPDATED OUTPUT")
assert_eq(cm.load_output("Phase 1 Requirements"), "UPDATED OUTPUT", "1.11  Overwrite existing checkpoint works")


# ============================================================
# SECTION 2 — SessionStore unit tests
# ============================================================
section("2 — SessionStore unit tests")

from session.session_store import SessionStore, SessionMeta

ss = SessionStore(index_path=Path(TMP_DIR) / ".asd" / "sessions.json")

# 2.1 create
meta = ss.create(RUN_ID, "my-project", "Build a todo app")
assert_eq(meta.run_id, RUN_ID, "2.1a  created session has correct run_id")
assert_eq(meta.project_name, "my-project", "2.1b  project_name stored")
assert_eq(meta.status, "running", "2.1c  initial status is 'running'")
assert_eq(meta.completed_phases, [], "2.1d  completed_phases starts empty")
assert_eq(meta.progress_pct, 0, "2.1e  progress_pct is 0 at start")

# 2.2 get
fetched = ss.get(RUN_ID)
assert_true(fetched is not None, "2.2a  get() returns meta")
assert_eq(fetched.run_id, RUN_ID, "2.2b  get() returns correct run")
assert_true(ss.get("nonexistent") is None, "2.2c  get() returns None for missing run")

# 2.3 update_phase_complete
ss.update_phase_complete(RUN_ID, "Phase 1 Requirements", tokens=150, duration=12.0)
m = ss.get(RUN_ID)
assert_true("Phase 1 Requirements" in m.completed_phases, "2.3a  completed_phases updated")
assert_eq(m.last_phase_completed, "Phase 1 Requirements", "2.3b  last_phase_completed updated")
assert_eq(m.total_tokens, 150, "2.3c  total_tokens accumulated")
assert_eq(m.progress_pct, 12, "2.3d  progress_pct = 1/8 = 12%")

ss.update_phase_complete(RUN_ID, "Phase 2 Architecture", tokens=200, duration=15.0)
m = ss.get(RUN_ID)
assert_eq(m.total_tokens, 350, "2.3e  total_tokens is cumulative")
assert_eq(m.progress_pct, 25, "2.3f  progress_pct = 2/8 = 25%")

# 2.3g no duplicate phases on repeated update
ss.update_phase_complete(RUN_ID, "Phase 1 Requirements", tokens=0, duration=0)
m = ss.get(RUN_ID)
assert_eq(m.completed_phases.count("Phase 1 Requirements"), 1, "2.3g  no duplicate in completed_phases")

# 2.4 record_gate
ss.record_gate(RUN_ID, "Architecture Review", "PASS")
m = ss.get(RUN_ID)
assert_eq(m.gate_results.get("Architecture Review"), "PASS", "2.4   gate result recorded")

# 2.5 mark_complete
ss.mark_complete(RUN_ID)
m = ss.get(RUN_ID)
assert_eq(m.status, "complete", "2.5   mark_complete sets status=complete")
assert_eq(m.status_emoji, "\u2705", "2.5b  status_emoji for complete is [OK]")

# 2.6 mark_partial / mark_failed
RUN_ID2 = "20260526_220000"
ss.create(RUN_ID2, "project-b", "Build a blog")
ss.mark_partial(RUN_ID2)
assert_eq(ss.get(RUN_ID2).status, "partial", "2.6a  mark_partial sets status=partial")

RUN_ID3 = "20260526_230000"
ss.create(RUN_ID3, "project-c", "Build a store")
ss.mark_failed(RUN_ID3)
assert_eq(ss.get(RUN_ID3).status, "failed", "2.6b  mark_failed sets status=failed")

# 2.7 list_all (newest first)
all_sessions = ss.list_all()
assert_eq(len(all_sessions), 3, "2.7a  list_all returns 3 sessions")
assert_eq(all_sessions[0].run_id, RUN_ID3, "2.7b  newest session is first")

# 2.8 list_resumable
resumable = ss.list_resumable()
resumable_ids = [m.run_id for m in resumable]
assert_true(RUN_ID2 in resumable_ids, "2.8a  partial session is resumable")
assert_true(RUN_ID3 in resumable_ids, "2.8b  failed session is resumable")
assert_false(RUN_ID in resumable_ids, "2.8c  complete session is NOT resumable")

# 2.9 find_latest_for_project
latest = ss.find_latest_for_project("my-project")
assert_true(latest is not None, "2.9a  find_latest_for_project finds result")
assert_eq(latest.run_id, RUN_ID, "2.9b  correct project matched")

# 2.10 atomic write: no .tmp left
tmp_files = list(Path(TMP_DIR, ".asd").glob("*.tmp"))
assert_eq(len(tmp_files), 0, "2.10  No .tmp files remain (atomic write confirmed)")

# 2.11 render_sessions_table
table_md = ss.render_sessions_table(all_sessions)
assert_true("|" in table_md, "2.11a  render_sessions_table returns markdown table")
assert_true(RUN_ID in table_md, "2.11b  table contains run IDs")


# ============================================================
# SECTION 3 — CLI integration tests
# ============================================================
section("3 — Orchestrator CLI integration tests")

# Run from the actual project root so policy files and src/ are found
PROJECT_DIR = str(Path(__file__).parent.parent)

def run_cli(*args, cwd=None, timeout=30):
    """Run the orchestrator CLI and return (returncode, stdout+stderr)."""
    cmd = [sys.executable, "-X", "utf8", "src/orchestrator.py"] + list(args)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        env=env,
    )
    return result.returncode, result.stdout + result.stderr

# 3.1 --help
rc, out = run_cli("--help")
assert_eq(rc, 0, "3.1a  --help exits with 0")
assert_true("--resume" in out, "3.1b  --help shows --resume flag")
assert_true("--rerun-phase" in out, "3.1c  --help shows --rerun-phase flag")
assert_true("--list-sessions" in out, "3.1d  --help shows --list-sessions flag")
assert_true("POLICY OK" in out, "3.1e  policy validates on startup")

# 3.2 --list-sessions (empty)
rc, out = run_cli("--list-sessions")
assert_eq(rc, 0, "3.2a  --list-sessions exits 0 when empty")
assert_true("No sessions found" in out or "Session History" in out,
            "3.2b  --list-sessions shows expected output")

# 3.3 --resume with nonexistent run_id
rc, out = run_cli("Build something", "--resume", "99999999_000000")
assert_eq(rc, 1, "3.3a  --resume with invalid run_id exits 1")
assert_true("No checkpoint data found" in out, "3.3b  error message mentions 'No checkpoint data found'")

# 3.4 --rerun-phase without valid phase name (requires --resume too)
# We need a real checkpoint dir for --resume to pass the first guard
test_run_id = "20260526_test001"
test_cp_dir = Path(PROJECT_DIR) / ".asd" / "checkpoints" / test_run_id
test_cp_dir.mkdir(parents=True, exist_ok=True)
# Write a dummy checkpoint
dummy = {
    "run_id": test_run_id, "phase_name": "Phase 1 Requirements",
    "timestamp": "2026-05-26T21:00:00", "output": "dummy", 
    "input_tokens": 0, "output_tokens": 0, "duration_seconds": 0.0,
    "gate_decision": None, "compression_tier": 0,
}
(test_cp_dir / "phase_1_requirements.json").write_text(json.dumps(dummy), encoding="utf-8")

rc, out = run_cli("Build something", "--resume", test_run_id, "--rerun-phase", "Phase 99 Invalid")
assert_eq(rc, 1, "3.4a  --rerun-phase with invalid phase name exits 1")
assert_true("Unknown phase" in out, "3.4b  error message mentions 'Unknown phase'")

# 3.5 --resume shows RESUME MODE banner before any LLM call
# This test uses --rerun-phase Phase 1 so ALL phases are invalidated; the
# orchestrator will try to call the LLM (which isn't running in CI) so we
# cap the timeout low and just verify the banner printed before the hang.
try:
    rc, out = run_cli(
        "Build something", "--resume", test_run_id,
        "--rerun-phase", "Phase 1 Requirements",
        timeout=15,
    )
except subprocess.TimeoutExpired as e:
    # Expected in CI: LLM not running. Banner should be in partial output.
    out = (e.stdout or "") + (e.stderr or "")
assert_true("RESUME MODE" in out, "3.5a  --resume banner appears before LLM call")

# Cleanup test checkpoint dir
shutil.rmtree(test_cp_dir, ignore_errors=True)


# ============================================================
# SECTION 4 — End-to-end dry-run simulation
# ============================================================
section("4 — End-to-end dry-run: simulate crash + resume")

# Use TMP_DIR as working dir
os.chdir(TMP_DIR)

# Simulate a pipeline that completes 3 phases then "crashes"
sim_run_id = "20260526_sim001"
sim_cm = CheckpointManager(sim_run_id)
sim_ss = SessionStore(index_path=Path(TMP_DIR) / ".asd" / "sessions.json")

sim_ss.create(sim_run_id, "sim-project", "Build a test app")

for i, phase in enumerate(ALL_PHASES[:3]):
    sim_cm.save(phase, f"output for {phase}", input_tokens=100*(i+1), duration_seconds=10.0)
    sim_ss.update_phase_complete(sim_run_id, phase, tokens=100*(i+1), duration=10.0)

# Simulate crash — mark partial
sim_ss.mark_partial(sim_run_id)

m = sim_ss.get(sim_run_id)
assert_eq(m.status, "partial", "4.1   Session correctly marked partial after 'crash'")
assert_eq(len(m.completed_phases), 3, "4.2   3 phases recorded in session")
assert_eq(m.progress_pct, 37, "4.3   Progress = 3/8 = 37%")
assert_eq(m.total_tokens, 600, "4.4   Total tokens = 100+200+300 = 600")

# Simulate resume
resumed_cm = CheckpointManager.for_existing_run(sim_run_id)
assert_true(resumed_cm is not None, "4.5   CheckpointManager found for partial run")
done = resumed_cm.get_completed_phases()
assert_eq(len(done), 3, "4.6   get_completed_phases returns 3 on resume")

# Verify cached outputs load correctly
for phase in ALL_PHASES[:3]:
    out = resumed_cm.load_output(phase)
    assert_eq(out, f"output for {phase}", f"4.7  Cache hit for: {phase}")

# Verify uncompleted phases return None
for phase in ALL_PHASES[3:]:
    out = resumed_cm.load_output(phase)
    assert_true(out is None, f"4.8  Cache miss for uncompleted: {phase}")

# Simulate completing remaining phases after resume
for i, phase in enumerate(ALL_PHASES[3:], start=3):
    sim_cm.save(phase, f"resumed output for {phase}")
    sim_ss.update_phase_complete(sim_run_id, phase)

sim_ss.mark_complete(sim_run_id)

m = sim_ss.get(sim_run_id)
assert_eq(m.status, "complete", "4.9   Session complete after all phases done")
assert_eq(len(m.completed_phases), 8, "4.10  All 8 phases in completed_phases")
assert_eq(m.progress_pct, 100, "4.11  Progress = 100%")

# Test re-run phase cascade in context of a completed run
resumed_cm.invalidate_from("Phase 6 QA Testing", ALL_PHASES)
still_cached = [resumed_cm.load_output(p) is not None for p in ALL_PHASES[:5]]
now_missing  = [resumed_cm.load_output(p) is None for p in ALL_PHASES[5:]]
assert_true(all(still_cached), "4.12  Phases 1-5 still cached after Phase 6 cascade")
assert_true(all(now_missing),  "4.13  Phases 6-8 invalidated by cascade")

# Simulate in list_all
all_s = sim_ss.list_all()
run_ids = [s.run_id for s in all_s]
assert_true(sim_run_id in run_ids, "4.14  Resumed session appears in list_all()")
assert_true(not any(s.run_id == sim_run_id and s.status != "complete" for s in all_s),
            "4.15  Resumed session status is 'complete' in list")


# ============================================================
# Final results
# ============================================================
print(f"\n{BOLD}{'='*60}{RESET}")
total = passed + failed
print(f"{BOLD}Results: {GREEN}{passed} passed{RESET} / {RED}{failed} failed{RESET} / {total} total{RESET}")
print(f"{BOLD}{'='*60}{RESET}\n")

# Cleanup
os.chdir(Path(__file__).parent.parent)
shutil.rmtree(TMP_DIR, ignore_errors=True)

if failed > 0:
    sys.exit(1)
else:
    print(f"{GREEN}{BOLD}All tests passed! Safe to commit.{RESET}\n")
    sys.exit(0)
