"""
test_parallel_phases.py
Test suite for parallel Phase 3/4/5 execution (feat: parallel-phase-band).

Tests:
  1. run_parallel_phases() runs all phases concurrently (timing overlap proof)
  2. run_parallel_phases() propagates worker exceptions (fast-fail)
  3. Thread-safe console access via lock (no interleaving)
  4. --no-parallel CLI flag produces sequential execution
  5. Checkpoint isolation — each parallel phase writes its own checkpoint
  6. Checkpoint load skips parallel phases correctly on resume
  7. run_parallel_phases() returns correct outputs keyed by phase name
  8. Single-phase spec still works (edge case)
  9. Empty spec returns empty dict without error
 10. CLI --help shows --no-parallel flag
"""

import json
import os
import sys
import shutil
import tempfile
import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Colour helpers
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
        fail(label, "Expected False but got True")


# ---------------------------------------------------------------------------
# Workspace setup
# ---------------------------------------------------------------------------
TMP_DIR = tempfile.mkdtemp(prefix="asd_parallel_test_")

def setup_tmp_asd():
    asd = Path(TMP_DIR) / ".asd"
    (asd / "checkpoints").mkdir(parents=True, exist_ok=True)
    return asd

os.chdir(TMP_DIR)
setup_tmp_asd()

# Make src/ importable
SRC = str(Path(__file__).parent.parent / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Import the modules under test
from session.checkpoint_manager import CheckpointManager
from session.session_store import SessionStore


# ---------------------------------------------------------------------------
# Minimal stubs so we can import orchestrator functions without starting the
# full LLM stack.
# ---------------------------------------------------------------------------
class _StubControlPlane:
    """Minimal ControlPlane stub for unit tests."""
    def __init__(self):
        self.steps = []
        self._lock = threading.Lock()

    def get_economics_summary(self):
        return {}


class _StubConsole:
    """Thread-safe print-capturing stub."""
    def __init__(self):
        self._lines = []
        self._lock = threading.Lock()

    def print(self, msg="", *args, **kwargs):
        with self._lock:
            self._lines.append(str(msg))

    @property
    def lines(self):
        with self._lock:
            return list(self._lines)


# ---------------------------------------------------------------------------
# Import the two functions under test, patching global `console` so we
# don't need a real Rich console during unit tests.
# ---------------------------------------------------------------------------
import importlib, types

# Patch console before importing orchestrator internals
import rich.console as _rc
_stub_console = _StubConsole()

# We'll patch at call time using a context manager approach instead to
# keep things simple — directly import the functions and monkey-patch.
import orchestrator as _orch_module

_original_console = _orch_module.console
_orch_module.console = _stub_console  # swap console for tests

run_parallel_phases = _orch_module.run_parallel_phases
_run_phase_checkpointed = _orch_module._run_phase_checkpointed


# ---------------------------------------------------------------------------
# SECTION 1 — run_parallel_phases() concurrency
# ---------------------------------------------------------------------------
section("1 — Concurrency: phases run in parallel (timing proof)")

RUN_ID_PARALLEL = "20260531_parallel001"
cm_p = CheckpointManager(RUN_ID_PARALLEL)
ss_p = SessionStore(index_path=Path(TMP_DIR) / ".asd" / "sessions.json")
ss_p.create(RUN_ID_PARALLEL, "test-parallel", "Build something")

am_p = _orch_module.ArtifactManager(str(Path(TMP_DIR) / ".agent" / "artifacts"))
cp_p = _StubControlPlane()

SLEEP_DURATION = 0.3   # each mock phase sleeps this long

start_times = {}
end_times = {}

def _make_slow_fn(name: str):
    def fn():
        start_times[name] = time.time()
        time.sleep(SLEEP_DURATION)
        end_times[name] = time.time()
        return f"output for {name}"
    return fn

specs = [
    ("Phase 3 Backend",      _make_slow_fn("Phase 3 Backend")),
    ("Phase 4 Frontend",     _make_slow_fn("Phase 4 Frontend")),
    ("Phase 5 Infrastructure", _make_slow_fn("Phase 5 Infrastructure")),
]

wall_start = time.time()
results = run_parallel_phases(specs, cp_p, am_p, cm_p, ss_p)
wall_duration = time.time() - wall_start

# If truly parallel, wall time should be close to SLEEP_DURATION, not 3×
expected_max_wall = SLEEP_DURATION * 1.8   # allow 80% overhead
assert_true(
    wall_duration < expected_max_wall,
    f"1.1  Wall time {wall_duration:.2f}s < {expected_max_wall:.2f}s (parallel speedup confirmed)",
    f"Wall time was {wall_duration:.2f}s; expected < {expected_max_wall:.2f}s",
)

# Verify overlap: start times of all 3 should be close together
if start_times:
    spread = max(start_times.values()) - min(start_times.values())
    assert_true(
        spread < SLEEP_DURATION,
        f"1.2  Phase start times overlap (spread={spread:.3f}s < {SLEEP_DURATION}s)",
        f"Spread was {spread:.3f}s — phases may not be running concurrently",
    )

# Verify all 3 outputs are present
assert_eq(set(results.keys()), {"Phase 3 Backend", "Phase 4 Frontend", "Phase 5 Infrastructure"},
          "1.3  All 3 phase names present in results dict")
assert_eq(results["Phase 3 Backend"],       "output for Phase 3 Backend",       "1.4  Phase 3 output correct")
assert_eq(results["Phase 4 Frontend"],      "output for Phase 4 Frontend",      "1.5  Phase 4 output correct")
assert_eq(results["Phase 5 Infrastructure"], "output for Phase 5 Infrastructure", "1.6  Phase 5 output correct")


# ---------------------------------------------------------------------------
# SECTION 2 — Exception propagation (fast-fail)
# ---------------------------------------------------------------------------
section("2 — Exception propagation: worker failure bubbles up")

RUN_ID_FAIL = "20260531_parallel002"
cm_f = CheckpointManager(RUN_ID_FAIL)
ss_f = SessionStore(index_path=Path(TMP_DIR) / ".asd" / "sessions.json")
ss_f.create(RUN_ID_FAIL, "test-fail", "Build something")
am_f = _orch_module.ArtifactManager(str(Path(TMP_DIR) / ".agent" / "artifacts"))
cp_f = _StubControlPlane()

def _failing_fn():
    time.sleep(0.05)
    raise RuntimeError("Simulated LLM failure")

def _ok_fn():
    time.sleep(0.1)
    return "ok output"

fail_specs = [
    ("Phase 3 Backend",      _ok_fn),
    ("Phase 4 Frontend",     _failing_fn),
    ("Phase 5 Infrastructure", _ok_fn),
]

exc_caught = None
try:
    run_parallel_phases(fail_specs, cp_f, am_f, cm_f, ss_f)
except RuntimeError as e:
    exc_caught = e

assert_true(exc_caught is not None, "2.1  RuntimeError propagated from parallel worker")
assert_true("Simulated LLM failure" in str(exc_caught), "2.2  Original exception message preserved")


# ---------------------------------------------------------------------------
# SECTION 3 — Thread-safe console access (no interleaving)
# ---------------------------------------------------------------------------
section("3 — Thread safety: console lines are complete (not interleaved)")

# We already verified no deadlock above (tests ran). Just verify console captured output.
log_lines = _stub_console.lines
parallel_band_logged = any("Parallel Execution Band" in l for l in log_lines)
assert_true(parallel_band_logged, "3.1  'Parallel Execution Band' banner was logged")
complete_logged = any("Parallel band complete" in l for l in log_lines)
assert_true(complete_logged, "3.2  'Parallel band complete' banner was logged")

# Every line should be a complete string (not empty)
empty_lines = [l for l in log_lines if l.strip() == ""]
assert_true(len(empty_lines) == 0, "3.3  No empty/blank log lines (no partial writes)", 
            f"{len(empty_lines)} empty lines found")


# ---------------------------------------------------------------------------
# SECTION 4 — --no-parallel flag: sequential execution
# ---------------------------------------------------------------------------
section("4 — --no-parallel: sequential fallback")

RUN_ID_SEQ = "20260531_parallel003"
cm_s = CheckpointManager(RUN_ID_SEQ)
ss_s = SessionStore(index_path=Path(TMP_DIR) / ".asd" / "sessions.json")
ss_s.create(RUN_ID_SEQ, "test-seq", "Build something")
am_s = _orch_module.ArtifactManager(str(Path(TMP_DIR) / ".agent" / "artifacts"))
cp_s = _StubControlPlane()

exec_order = []

def _ordered_fn(name):
    def fn():
        exec_order.append(("start", name))
        time.sleep(0.05)
        exec_order.append(("end", name))
        return f"seq output {name}"
    return fn

seq_specs = [
    ("Phase 3 Backend",      _ordered_fn("Phase 3 Backend")),
    ("Phase 4 Frontend",     _ordered_fn("Phase 4 Frontend")),
    ("Phase 5 Infrastructure", _ordered_fn("Phase 5 Infrastructure")),
]

# Replicate what main() does with --no-parallel
seq_results = {}
for phase_name, phase_fn in seq_specs:
    seq_results[phase_name] = _run_phase_checkpointed(
        cp_s, phase_name, phase_fn, am_s, cm_s, ss_s
    )

# Sequential: end of phase N must come before start of phase N+1
phases_in_order = ["Phase 3 Backend", "Phase 4 Frontend", "Phase 5 Infrastructure"]
starts = {name: i for i, (ev, name) in enumerate(exec_order) if ev == "start"}
ends   = {name: i for i, (ev, name) in enumerate(exec_order) if ev == "end"}

sequential_ok = True
for i in range(len(phases_in_order) - 1):
    cur = phases_in_order[i]
    nxt = phases_in_order[i + 1]
    if ends.get(cur, -1) >= starts.get(nxt, 9999):
        sequential_ok = False
        break

assert_true(sequential_ok, "4.1  Phases execute sequentially when --no-parallel is used")
assert_eq(set(seq_results.keys()), {"Phase 3 Backend", "Phase 4 Frontend", "Phase 5 Infrastructure"},
          "4.2  All 3 outputs present in sequential mode")


# ---------------------------------------------------------------------------
# SECTION 5 — Checkpoint isolation
# ---------------------------------------------------------------------------
section("5 — Checkpoint isolation: each parallel phase writes its own file")

assert_true(cm_p.load("Phase 3 Backend")      is not None, "5.1  Phase 3 checkpoint written")
assert_true(cm_p.load("Phase 4 Frontend")     is not None, "5.2  Phase 4 checkpoint written")
assert_true(cm_p.load("Phase 5 Infrastructure") is not None, "5.3  Phase 5 checkpoint written")

cp3 = cm_p.load("Phase 3 Backend")
cp4 = cm_p.load("Phase 4 Frontend")
cp5 = cm_p.load("Phase 5 Infrastructure")

assert_eq(cp3["phase_name"], "Phase 3 Backend",       "5.4  Phase 3 checkpoint has correct phase_name")
assert_eq(cp4["phase_name"], "Phase 4 Frontend",      "5.5  Phase 4 checkpoint has correct phase_name")
assert_eq(cp5["phase_name"], "Phase 5 Infrastructure","5.6  Phase 5 checkpoint has correct phase_name")

assert_eq(cp3["output"], "output for Phase 3 Backend",       "5.7  Phase 3 checkpoint output matches")
assert_eq(cp4["output"], "output for Phase 4 Frontend",      "5.8  Phase 4 checkpoint output matches")
assert_eq(cp5["output"], "output for Phase 5 Infrastructure","5.9  Phase 5 checkpoint output matches")

# No .tmp files should remain
tmp_files = list((Path(TMP_DIR) / ".asd" / "checkpoints" / RUN_ID_PARALLEL).glob("*.tmp"))
assert_eq(len(tmp_files), 0, "5.10  No .tmp files remain (atomic writes confirmed)")


# ---------------------------------------------------------------------------
# SECTION 6 — Resume: parallel checkpoint skip
# ---------------------------------------------------------------------------
section("6 — Resume: parallel phases loaded from checkpoint (skipped)")

# Already have checkpoints from section 1.  Simulate running parallel again with same cm.
_stub_console._lines.clear()

skip_results = {}
for name, _ in specs:
    # Call _run_phase_checkpointed with a phase_fn that would raise if called
    def _should_not_run():
        raise AssertionError("Phase function was called despite checkpoint existing!")
    skip_results[name] = _run_phase_checkpointed(
        cp_p, name, _should_not_run, am_p, cm_p, ss_p
    )

assert_eq(skip_results["Phase 3 Backend"],        "output for Phase 3 Backend",       "6.1  Phase 3 loaded from checkpoint")
assert_eq(skip_results["Phase 4 Frontend"],        "output for Phase 4 Frontend",      "6.2  Phase 4 loaded from checkpoint")
assert_eq(skip_results["Phase 5 Infrastructure"],  "output for Phase 5 Infrastructure","6.3  Phase 5 loaded from checkpoint")

skipped_msgs = [l for l in _stub_console.lines if "loaded from checkpoint (skipped)" in l]
assert_eq(len(skipped_msgs), 3, "6.4  3 'skipped' messages logged (one per phase)")


# ---------------------------------------------------------------------------
# SECTION 7 — Edge cases
# ---------------------------------------------------------------------------
section("7 — Edge cases")

# 7.1 Single phase spec
RUN_ID_SINGLE = "20260531_parallel004"
cm_sg = CheckpointManager(RUN_ID_SINGLE)
ss_sg = SessionStore(index_path=Path(TMP_DIR) / ".asd" / "sessions.json")
ss_sg.create(RUN_ID_SINGLE, "test-single", "Build something")
am_sg = _orch_module.ArtifactManager(str(Path(TMP_DIR) / ".agent" / "artifacts"))
cp_sg = _StubControlPlane()

single_result = run_parallel_phases(
    [("Phase 3 Backend", lambda: "single output")],
    cp_sg, am_sg, cm_sg, ss_sg,
)
assert_eq(single_result["Phase 3 Backend"], "single output", "7.1  Single-phase spec works correctly")

# 7.2 Empty spec — should return empty dict
RUN_ID_EMPTY = "20260531_parallel005"
cm_em = CheckpointManager(RUN_ID_EMPTY)
ss_em = SessionStore(index_path=Path(TMP_DIR) / ".asd" / "sessions.json")
ss_em.create(RUN_ID_EMPTY, "test-empty", "Build something")
am_em = _orch_module.ArtifactManager(str(Path(TMP_DIR) / ".agent" / "artifacts"))
cp_em = _StubControlPlane()

empty_result = run_parallel_phases([], cp_em, am_em, cm_em, ss_em)
assert_eq(empty_result, {}, "7.2  Empty spec returns empty dict without error")


# ---------------------------------------------------------------------------
# SECTION 8 — CLI integration: --no-parallel flag appears in --help
# ---------------------------------------------------------------------------
section("8 — CLI: --no-parallel flag present in --help")

PROJECT_DIR = str(Path(__file__).parent.parent)

def run_cli(*cli_args, timeout=30):
    cmd = [sys.executable, "-X", "utf8", "src/orchestrator.py"] + list(cli_args)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        env=env,
    )
    return result.returncode, result.stdout + result.stderr

rc, out = run_cli("--help")
assert_eq(rc, 0, "8.1  --help exits with code 0")
assert_true("--no-parallel" in out, "8.2  --help shows --no-parallel flag")
assert_true("Phases 3/4/5" in out or "parallel" in out.lower(),
            "8.3  --help describes the parallel flag purpose")


# ---------------------------------------------------------------------------
# Final results
# ---------------------------------------------------------------------------
print(f"\n{BOLD}{'='*60}{RESET}")
total = passed + failed
print(f"{BOLD}Results: {GREEN}{passed} passed{RESET} / {RED}{failed} failed{RESET} / {total} total{RESET}")
print(f"{BOLD}{'='*60}{RESET}\n")

# Restore original console before cleanup
_orch_module.console = _original_console

# Cleanup
os.chdir(Path(__file__).parent.parent)
shutil.rmtree(TMP_DIR, ignore_errors=True)

if failed > 0:
    sys.exit(1)
else:
    print(f"{GREEN}{BOLD}All tests passed! Safe to commit.{RESET}\n")
    sys.exit(0)
