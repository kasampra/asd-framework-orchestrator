import os
import sys
import time
import argparse
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session.checkpoint_manager import CheckpointManager
from session.session_store import SessionStore

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from mcp_server import (
    get_framework_instructions,
    delegate_to_qwen_agent,
    evaluate_quality_gate,
    log_audit_decision,
    AVAILABLE_TOOLS,
    qwen,
)
from control_plane import ControlPlane, ContextSnapshot, ToolSelectionRecord, IntentExecutionDiff

console = Console()

class ArtifactManager:
    """Manages verified phase outputs via disk storage for isolated context passing."""
    def __init__(self, storage_dir: str = ".agent/artifacts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, phase_name: str, content: str):
        safe_name = phase_name.lower().replace(" ", "_")
        artifact_path = self.storage_dir / f"{safe_name}.md"
        artifact_path.write_text(content, encoding="utf-8")

    def get(self, *phase_names: str) -> str:
        """Combine specific phase artifacts from disk into a single context string."""
        contents = []
        for name in phase_names:
            safe_name = name.lower().replace(" ", "_")
            artifact_path = self.storage_dir / f"{safe_name}.md"
            if artifact_path.exists():
                artifact_content = artifact_path.read_text(encoding="utf-8")
                contents.append(f"### Source: {name}\n{artifact_content}")
            else:
                contents.append(f"### Source: {name}\n(Artifact not found on disk)")
        return "\n\n---\n\n".join(contents)

from config_loader import load_agent_roles
AGENT_ROLES = load_agent_roles()

from memory.fingerprint_extractor import FingerprintExtractor
from memory.baseline_store import BaselineStore
from memory.drift_detector import DriftDetector

from memory.cost_tracker import CostTracker
from core.reflection import ReflectionManager
from core.skill_researcher import SkillResearcher
from core.tool_researcher import ToolResearcher
from services.content_agent import ContentAgent
from services.visualizer import Visualizer
from services.roi_tracker import ROITracker
from services.security_scanner import SecurityScanner
from self_healing import SelfHealer
from mcp_server import AVAILABLE_TOOLS

def print_header():
    console.print(Panel.fit(
        "[bold cyan]🤖 Agentic SDLC Orchestrator v2.0[/bold cyan]\n"
        "[dim]Sovereign AI · Control Plane Active · Self-Healing Enabled[/dim]", 
        border_style="cyan"
    ))

def extract_and_write_files(markdown_text: str) -> list[str]:
    import re
    pattern = r"```[a-zA-Z0-9]*\n(.*?)\n```"
    matches = re.finditer(pattern, markdown_text, re.DOTALL)
    
    written_files = []
    for match in matches:
        content = match.group(1).strip()
        if not content:
            continue
            
        first_line = content.split('\n')[0].strip()
        
        file_path = None
        if first_line.startswith('# ') or first_line.startswith('// '):
            potential_path = first_line[2:].strip()
            if '/' in potential_path or '.' in potential_path:
                file_path = potential_path
        elif first_line.startswith('/* ') and first_line.endswith(' */'):
            potential_path = first_line[3:-3].strip()
            if '/' in potential_path or '.' in potential_path:
                file_path = potential_path
                
        if file_path:
            file_path = file_path.replace("\\", "/")
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[dim]  ↳ Extracted physical file: {file_path}[/dim]")
            written_files.append(file_path)
            
    if written_files:
        console.print(f"[bold green]✓ Physically wrote {len(written_files)} codebase files to disk![/bold green]\n")
    
    return written_files

def run_phase(cp: ControlPlane, phase_name: str, objective: str, context: str, skip_compression: bool = False) -> str:
    agent_role = AGENT_ROLES.get(phase_name, "Agent")
    
    # --- Cognitive Lock Check ---
    from policy_validator import PolicyValidator
    violations = PolicyValidator.check_lock_violation(objective)
    if violations:
        console.print(Panel(
            f"[bold red]🔓 COGNITIVE LOCK TRIGGERED![/bold red]\n"
            f"Phase: [cyan]{phase_name}[/cyan]\n"
            f"Prohibited Keywords: [red]{', '.join(violations)}[/red]\n\n"
            f"The agent objective contains high-risk actions locked by sovereign policy.",
            title="Policy Enforcement",
            border_style="red"
        ))
        
        if os.getenv("ARCHITECT_BYPASS") == "1":
            console.print("[yellow]⚠️  Manual Architect Bypass detected (Env: ARCHITECT_BYPASS=1). Proceeding with caution...[/yellow]")
        else:
            choice = Prompt.ask(
                "\n[bold]Risk Mitigation Required[/bold]\n"
                "[1] Abort (Safe)\n"
                "[2] Manual Bypass (I take full responsibility)\nChoice", 
                choices=["1", "2"], 
                default="1"
            )
            if choice == "1":
                console.print("[red]Execution blocked by Cognitive Lock.[/red]")
                sys.exit(1)
            else:
                log_audit_decision(f"Manual Bypass: {phase_name}", f"User bypassed cognitive lock for keywords: {violations}")

    cp.hooks.trigger("pre_phase_start", phase_name, agent_role)
    
    step = cp.begin_step(phase_name, agent_role)
    start = time.time()

    # Context Compression
    if skip_compression:
        compressed_context, tier = context, 0
    else:
        compressed_context, tier = cp.compressor.compress(context, max_tokens=8000, qwen_client=qwen)
    
    step.compression_tier = tier
    if tier > 0:
        console.print(f"[dim]  ⚡ Context compressed using Tier {tier}[/dim]")

    step.context_snapshot.record("AGENTS.md (framework rules)", context[:500])
    step.context_snapshot.record("Phase Objective", objective)
    step.context_snapshot.record("Injected Context", compressed_context)

    if os.getenv("TUI_MODE"):
        console.print(f"🌍 [bold yellow]Initializing {phase_name}[/bold yellow]")
        console.print(f"🧠 Loading [cyan]{agent_role}[/cyan] Persona...")
        console.print(f"📚 Ingesting context boundaries (Length: {len(compressed_context)})")
        console.print("⚡ Delegating neural execution to Local Qwen...")
        result = delegate_to_qwen_agent(phase_name, objective, compressed_context)
    else:
        with Progress(SpinnerColumn(), TextColumn(f"[bold yellow]Executing {phase_name}...[/bold yellow]"), console=console) as progress:
            task = progress.add_task("working", total=None)
            result = delegate_to_qwen_agent(phase_name, objective, compressed_context)
            progress.update(task, completed=100)
            
    step.decision_trace = result.get("reasoning", "")
    step.tool_selection = ToolSelectionRecord(
        available_tools=result.get("available_tools", []),
        selected_tool=result.get("tool_used", "delegate_to_qwen_agent"),
        tool_inputs={
            "phase_name": phase_name,
            "objective_prompt": objective[:200] + "..." if len(objective) > 200 else objective,
            "context_length": len(compressed_context),
        },
        selection_reasoning=f"Phase {phase_name} requires code generation; delegate_to_qwen_agent is the appropriate tool.",
    )

    output = result.get("output", "")
    log_audit_decision(f"Phase Execute: {phase_name}", f"Delegated task to Qwen worker.\nReasoning: {step.decision_trace[:300]}")
    
    usage = result.get("usage", {})
    step.input_tokens = usage.get("prompt_tokens", 0)
    step.output_tokens = usage.get("completion_tokens", 0)

    filename = f"output_{phase_name.lower().replace(' ', '_')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)
    
    written_files = extract_and_write_files(output)
    step.intent_diff = IntentExecutionDiff(
        intended_plan=objective[:300],
        actual_output_summary=f"Generated {len(output)} chars of output, extracted {len(written_files)} files.",
        files_planned=[],
        files_actually_written=written_files,
    )
    step.output_file = filename
    cp.finalize_step(step, start)
    console.print(f"[green]✓ {phase_name} completed![/green] (Saved to [cyan]{filename}[/cyan])\n")
    
    cp.hooks.trigger("post_phase_complete", phase_name, step.intent_diff.actual_output_summary)
    return output

def run_gate(cp: ControlPlane, gate_name: str, objective: str, context: str) -> tuple[bool, str]:
    cp.hooks.trigger("on_gate_evaluate", gate_name, hashlib.sha256(context.encode()).hexdigest()[:8])
    
    # --- Hard Security Gate Logic ---
    if gate_name == "Security Review":
        scanner = SecurityScanner(console)
        sast = scanner.run_sast_scan(".") # Scan whole repo
        secrets = scanner.scan_for_secrets(".")
        security_report = scanner.generate_report(sast, secrets)
        
        # Inject the deterministic report into the context for the Gatekeeper AI
        context = f"{context}\n\n### DETERMINISTIC SECURITY EVIDENCE:\n{security_report}"
        console.print("  🛡️  [bold green]Deterministic security evidence injected into Gate context.[/bold green]")

    step = cp.begin_step(gate_name, "Gatekeeper AI")
    start = time.time()

    # Context Compression (Gate output context varies per iteration, so we ALWAYS compress here)
    compressed_context, tier = cp.compressor.compress(context, max_tokens=8000, qwen_client=qwen)
    step.compression_tier = tier

    step.context_snapshot.record("Gate Objective", objective)
    step.context_snapshot.record("Verification Evidence", compressed_context)

    if os.getenv("TUI_MODE"):
        console.print(f"\n🛡️ [bold red]Initializing Gatekeeper AI: {gate_name}[/bold red]")
        console.print(f"⚖️ Evaluating evidence against Phase boundaries...")
        console.print("⏳ Awaiting Gatekeeper Decision Matrix...")
        result = evaluate_quality_gate(gate_name, objective, compressed_context)
    else:
        with Progress(SpinnerColumn(), TextColumn(f"[bold red]Gatekeeper Evaluating: {gate_name}...[/bold red]"), console=console) as progress:
            task = progress.add_task("working", total=None)
            result = evaluate_quality_gate(gate_name, objective, compressed_context)
            progress.update(task, completed=100)
            
    step.decision_trace = result.get("thinking", "")
    step.tool_selection = ToolSelectionRecord(
        available_tools=result.get("available_tools", []),
        selected_tool=result.get("tool_used", "evaluate_quality_gate"),
        tool_inputs={
            "gate_name": gate_name,
            "phase_objective": objective[:200],
            "evidence_length": len(compressed_context),
        },
        selection_reasoning=f"Gate {gate_name} requires quality evaluation.",
    )

    decision = result.get("decision", "FAIL")
    reasoning = result.get("reasoning", "No reasoning provided")
    log_audit_decision(f"Gatekeeper: {gate_name}", f"DECISION: {decision}\nREASONING: {reasoning}")
    
    usage = result.get("usage", {})
    step.input_tokens = usage.get("prompt_tokens", 0)
    step.output_tokens = usage.get("completion_tokens", 0)

    step.gate_decision = decision
    step.intent_diff = IntentExecutionDiff(
        intended_plan=f"Evaluate whether the evidence meets the criteria for: {objective[:200]}",
        actual_output_summary=f"Gate {gate_name} returned {decision}. {reasoning[:200]}",
    )
    cp.finalize_step(step, start)
    
    if decision == "PASS":
        console.print(f"[bold green]✓ GATE PASSED:[/bold green] {gate_name}\n")
        return True, reasoning
    else:
        console.print(f"[bold red]✗ GATE FAILED:[/bold red] {gate_name}")
        console.print(f"[dim]{reasoning}[/dim]")
        cp.hooks.trigger("on_gate_fail", gate_name, reasoning)
        return False, reasoning

def execute_phase_with_resilience(cp: ControlPlane, phase_name: str, phase_objective: str, context: str, gate_name: str, gate_objective: str, max_retries: int = 2, reflection_manager: ReflectionManager = None) -> str:
    """
    Executes a phase and its corresponding gate.
    Includes a self-reflection step before the gate check.
    If the gate fails, it autonomously auto-heals by passing the failure reasoning back to the agent.
    """
    current_objective = phase_objective
    retries = 0
    healer = SelfHealer(trace_dir="traces")
    
    # Pre-compress static input context before the loop to save cycles on retries
    compressed_context, tier = cp.compressor.compress(context, max_tokens=8000, qwen_client=qwen)
    if tier > 0:
        console.print(f"[dim]  ⚡ Input context pre-compressed (Tier {tier})[/dim]")

    while retries <= max_retries:
        output = run_phase(cp, phase_name, current_objective, compressed_context, skip_compression=True)
        
        # New Reflection Step
        if reflection_manager:
            output = reflection_manager.reflect_and_refine(phase_name, current_objective, output, compressed_context)
            
        passed, reasoning = run_gate(cp, gate_name, gate_objective, output)
        
        if passed:
            healer.metrics["successes"] += 1
            return output
            
        # [SELF-HEALING FLYWHEEL]
        retries += 1
        failure_context = {
            "output": output,
            "reasoning": reasoning,
            "phase": phase_name,
            "exit_code": 1 if not passed else 0
        }
        
        failure = healer.monitor(failure_context)
        if failure:
            diagnosis = healer.diagnose(failure)
            plan = healer.plan(diagnosis)
            
            trace_data = {
                "timestamp": datetime.now().isoformat(),
                "failure": failure,
                "diagnosis": diagnosis,
                "plan": plan,
                "retry_count": retries
            }
            healer.log_trace(trace_data)
            
            console.print(f"\n[bold yellow]⚠️  Self-Healing Flywheel Engaged: {diagnosis['category']} Detected.[/bold yellow]")
            console.print(f"[dim]Strategy: {plan['strategy']}[/dim]\n")
            
            if retries <= max_retries:
                current_objective = phase_objective + f"\n\n[CRITICAL CORRECTION REQUIRED]\nDiagnosis: {diagnosis['category']}\nReason: {reasoning}\nStrategy: {plan['strategy']}\n\nPlease apply the correction and regenerate."
            else:
                healer.metrics["failures"] += 1
                suggestion = healer.get_adaptive_suggestion()
                if suggestion:
                    console.print(f"[bold red]{suggestion}[/bold red]")
                    
                console.print(f"\n[bold red]❌ Self-Healing exhausted after {max_retries} retries.[/bold red]")
                console.print(Panel("Human-in-the-loop intervention required.", border_style="red"))
            
            if os.getenv("NON_INTERACTIVE") and retries > max_retries:
                console.print("[yellow]NON_INTERACTIVE mode: Auto-aborting pipeline.[/yellow]")
                sys.exit(1)

            if retries > max_retries:
                choice = Prompt.ask(
                    "\n[bold]Action Required[/bold]\n[1] Abort Pipeline\n[2] Provide Manual Feedback to Agent (Retry)\n[3] Force Pass Gate\nChoice", 
                    choices=["1", "2", "3"], 
                    default="1"
                )
                
                if choice == "1":
                    console.print("[red]Pipeline aborted by user.[/red]")
                    cp.print_summary(console)
                    report_path = cp.write_report()
                    console.print(f"[cyan]📄 Control Plane report saved to: {report_path}[/cyan]")
                    sys.exit(1)
                elif choice == "2":
                    feedback = Prompt.ask("\n[cyan]Enter your specific feedback for the agent[/cyan]")
                    current_objective = phase_objective + f"\n\n[HUMAN ARCHITECT FEEDBACK]\n{feedback}\n\nPlease apply this feedback and regenerate."
                    retries -= 1  # Give it one more try
                    console.print("\n[bold yellow]Restarting phase with human feedback...[/bold yellow]\n")
                elif choice == "3":
                    console.print("\n[bold yellow]Forcing pass by human override...[/bold yellow]\n")
                    return output
                
    return ""

# ---------------------------------------------------------------------------
# Ordered list of all phases — used by the checkpoint cascade logic.
# ---------------------------------------------------------------------------
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


def _run_phase_checkpointed(
    cp: ControlPlane,
    phase_name: str,
    phase_fn,
    am: "ArtifactManager",
    cm: CheckpointManager,
    ss: SessionStore,
    lock: threading.Lock = None,
) -> str:
    """
    Wrapper that adds checkpoint save/load around a phase execution function.

    If a valid checkpoint exists for `phase_name`, the phase is skipped and
    the cached output is returned immediately.  Otherwise, `phase_fn()` is
    called, and its output is persisted to a checkpoint before returning.

    Args:
        phase_fn: A zero-argument callable that executes the phase and returns
                  the output string.  Use functools.partial or a lambda to
                  bind arguments before passing.
        lock: Optional threading.Lock for thread-safe console/CP/SS access when
              called from a parallel context.
    """
    _lock = lock or threading.Lock()  # default: no-op private lock

    cached = cm.load_output(phase_name)
    if cached is not None:
        with _lock:
            console.print(
                f"[dim]⏭  {phase_name} — loaded from checkpoint (skipped)[/dim]"
            )
        am.save(phase_name, cached)
        return cached

    output = phase_fn()
    am.save(phase_name, output)

    # Persist checkpoint (CheckpointManager writes are already atomic/thread-safe)
    with _lock:
        econ = cp.get_economics_summary()
    phase_econ = econ.get(phase_name, {})
    cp_path = cm.save(
        phase_name,
        output,
        input_tokens=phase_econ.get("input_tokens", 0),
        output_tokens=phase_econ.get("output_tokens", 0),
        duration_seconds=phase_econ.get("duration_seconds", 0.0),
    )
    with _lock:
        console.print(f"[dim]  💾 Checkpoint saved → {cp_path}[/dim]")

    # Update session index (read-modify-write; must be serialised)
    with _lock:
        ss.update_phase_complete(
            cm.run_id,
            phase_name,
            tokens=phase_econ.get("input_tokens", 0) + phase_econ.get("output_tokens", 0),
            duration=phase_econ.get("duration_seconds", 0.0),
        )

    return output


def run_parallel_phases(
    phase_specs: list,
    cp: ControlPlane,
    am: "ArtifactManager",
    cm: CheckpointManager,
    ss: SessionStore,
) -> dict:
    """
    Execute multiple independent phases concurrently using threads.

    ``phase_specs`` is a list of ``(phase_name, phase_fn)`` tuples where
    ``phase_fn`` is a zero-argument callable that runs the full phase
    (including resilience retries) and returns the output string.

    A single ``threading.Lock`` is shared across all workers so that:
    - ``console.print()`` lines are not interleaved
    - ``ControlPlane.get_economics_summary()`` reads the consistent list
    - ``SessionStore.update_phase_complete()`` writes are serialised

    Returns a ``dict[phase_name -> output_str]`` with one entry per phase.
    Raises the first exception encountered in any worker thread (fast-fail).
    """
    lock = threading.Lock()
    n = len(phase_specs)

    # Nothing to do — avoid ThreadPoolExecutor(max_workers=0) error
    if n == 0:
        return {}

    with lock:
        console.print(
            f"[bold cyan]⚡ Parallel Execution Band: {n} phases running concurrently[/bold cyan]\n"
            + "\n".join(f"   • {name}" for name, _ in phase_specs)
        )

    outputs: dict = {}
    futures = {}

    with ThreadPoolExecutor(max_workers=n, thread_name_prefix="asd-phase") as executor:
        for phase_name, phase_fn in phase_specs:
            future = executor.submit(
                _run_phase_checkpointed,
                cp, phase_name, phase_fn, am, cm, ss, lock,
            )
            futures[future] = phase_name

        first_exc = None
        for future in as_completed(futures):
            phase_name = futures[future]
            exc = future.exception()
            if exc is not None:
                with lock:
                    console.print(
                        f"[bold red]❌ Parallel phase '{phase_name}' failed: {exc}[/bold red]"
                    )
                if first_exc is None:
                    first_exc = exc
            else:
                outputs[phase_name] = future.result()
                with lock:
                    console.print(
                        f"[bold green]✓ {phase_name} completed (parallel)[/bold green]"
                    )

        if first_exc is not None:
            raise first_exc

    with lock:
        console.print(
            f"[bold green]✅ Parallel band complete — {n} phases finished[/bold green]\n"
        )

    return outputs


def _list_sessions_and_exit(ss: SessionStore) -> None:
    """Print a formatted session history table and exit."""
    from rich.table import Table

    sessions = ss.list_all()
    if not sessions:
        console.print("[dim]No sessions found in .asd/sessions.json[/dim]")
        sys.exit(0)

    table = Table(
        title="📋 ASD Orchestrator — Session History",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Run ID", style="white")
    table.add_column("Project", style="yellow")
    table.add_column("Status", style="bold")
    table.add_column("Progress", style="green")
    table.add_column("Last Phase", style="white", max_width=30)
    table.add_column("Tokens", style="dim")
    table.add_column("Created", style="dim")

    for i, m in enumerate(sessions, 1):
        progress = f"{m.progress_pct}% ({len(m.completed_phases)}/{m.total_phases})"
        status_str = f"{m.status_emoji} {m.status}"
        created = m.created_at[:19].replace("T", " ")  # trim microseconds
        table.add_row(
            str(i),
            m.run_id,
            m.project_name,
            status_str,
            progress,
            m.last_phase_completed or "—",
            f"{m.total_tokens:,}",
            created,
        )

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]To resume a run:        python src/orchestrator.py \"<objective>\" --resume <run_id>[/dim]")
    console.print("[dim]To rerun a phase:       python src/orchestrator.py \"<objective>\" --resume <run_id> --rerun-phase \"Phase N Name\"[/dim]")
    sys.exit(0)


def main():
    # Import PolicyValidator from .asd folder
    asd_path = str(Path(__file__).parent.parent / ".asd")
    if asd_path not in sys.path:
        sys.path.insert(0, asd_path)

    from policy_validator import PolicyValidator
    PolicyValidator.validate()
    console.print("[bold green]Policy-as-Code active. Governance loaded from .asd/policies/agent_rbac.yaml[/bold green]")

    # ------------------------------------------------------------------
    # CLI argument parsing (extended with resume/rerun/list flags)
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Agentic SDLC CLI v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python src/orchestrator.py \"Build a todo app\"\n"
            "  python src/orchestrator.py \"Build a todo app\" --resume 20260526_143022\n"
            "  python src/orchestrator.py \"Build a todo app\" --resume 20260526_143022 --rerun-phase \"Phase 6 QA Testing\"\n"
            "  python src/orchestrator.py --list-sessions\n"
        ),
    )
    parser.add_argument(
        "objective",
        type=str,
        nargs="?",
        default=None,
        help="What do you want to build? (required unless --list-sessions)",
    )
    parser.add_argument(
        "--project",
        type=str,
        default="default_project",
        help="Project name for decision fingerprinting and session grouping",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        metavar="RUN_ID",
        help="Resume a previous run from its last successful phase (e.g. --resume 20260526_143022)",
    )
    parser.add_argument(
        "--rerun-phase",
        type=str,
        default=None,
        metavar="PHASE_NAME",
        help="Force re-run a specific phase and all downstream phases (requires --resume)",
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all past pipeline sessions and exit",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel execution of Phases 3/4/5 (run sequentially — useful for debugging or low-VRAM setups)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Session Store initialisation (needed even for --list-sessions)
    # ------------------------------------------------------------------
    ss = SessionStore()

    if args.list_sessions:
        _list_sessions_and_exit(ss)

    if not args.objective:
        parser.error("objective is required unless --list-sessions is specified.")

    # ------------------------------------------------------------------
    # Determine run_id and set up CheckpointManager
    # ------------------------------------------------------------------
    if args.resume:
        run_id = args.resume
        existing_cm = CheckpointManager.for_existing_run(run_id)
        if existing_cm is None:
            console.print(
                f"[bold red]✗ No checkpoint data found for run_id: {run_id}[/bold red]\n"
                "Run [cyan]python src/orchestrator.py --list-sessions[/cyan] to see available runs."
            )
            sys.exit(1)
        cm = existing_cm
        console.print(
            Panel(
                f"[bold yellow]⏩ RESUME MODE[/bold yellow]\n"
                f"Run ID: [cyan]{run_id}[/cyan]\n"
                f"Completed phases: [green]{', '.join(cm.get_completed_phases()) or 'none'}[/green]",
                border_style="yellow",
            )
        )

        # Handle --rerun-phase: invalidate the target phase + all downstream
        if args.rerun_phase:
            if args.rerun_phase not in ALL_PHASES:
                console.print(
                    f"[bold red]✗ Unknown phase: '{args.rerun_phase}'[/bold red]\n"
                    f"Valid phases: {ALL_PHASES}"
                )
                sys.exit(1)
            invalidated = cm.invalidate_from(args.rerun_phase, ALL_PHASES)
            console.print(
                Panel(
                    f"[bold magenta]🔄 RE-RUN MODE[/bold magenta]\n"
                    f"Target phase: [cyan]{args.rerun_phase}[/cyan]\n"
                    f"Invalidated checkpoints: [yellow]{', '.join(invalidated)}[/yellow]",
                    border_style="magenta",
                )
            )
    else:
        # Fresh run — generate a new run_id (same logic as ControlPlane)
        import datetime as _dt
        run_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        cm = CheckpointManager(run_id)

    # ------------------------------------------------------------------
    # Control Plane (reuse run_id for traceability)
    # ------------------------------------------------------------------
    cp = ControlPlane()
    cp.run_id = run_id          # override the auto-generated run_id
    cp.objective = args.objective

    print_header()
    console.print(f"[bold]Target Objective:[/bold] {args.objective}")
    console.print(f"[bold]Project Name:[/bold] {args.project}")
    console.print(f"[bold]Run ID:[/bold] [cyan]{run_id}[/cyan]\n")

    # Register session in the store
    if not args.resume:
        ss.create(run_id, args.project, args.objective)
    # (If resuming, the session record already exists — update_phase_complete handles updates)

    # Register default hooks
    cp.hooks.register("pre_phase_start", lambda name, role: console.print(f"[bold cyan]HOOK: Starting {name} as {role}[/bold cyan]"))
    cp.hooks.register("post_phase_complete", lambda name, summary: console.print(f"[bold green]HOOK: Completed {name}. {summary}[/bold green]"))
    cp.hooks.register("on_gate_evaluate", lambda name, chash: console.print(f"[bold red]HOOK: Evaluating Gate {name} (Context Hash: {chash})[/bold red]"))
    cp.hooks.register("on_gate_fail", lambda name, reason: log_audit_decision(f"GATE_FAIL: {name}", f"Reason: {reason}", "audit.md"))

    # Artifact Manager, Reflection Manager
    am = ArtifactManager()
    rm = ReflectionManager(console)

    # Memory Layer
    baseline_store = BaselineStore()
    extractor = FingerprintExtractor(output_dir=".", run_id=run_id, project_name=args.project)
    detector = DriftDetector()

    model_name = os.getenv("MODEL_NAME", "local-qwen")
    cost_tracker = CostTracker(model=model_name)

    instructions = get_framework_instructions()

    try:
        # ------------------------------------------------------------------
        # Phase 1: Requirements
        # ------------------------------------------------------------------
        req_output = _run_phase_checkpointed(
            cp, "Phase 1 Requirements",
            lambda: run_phase(cp, "Phase 1 Requirements", args.objective, instructions),
            am, cm, ss,
        )

        # Phase 1.5: Skill & Tool Research (Framework Evolution)
        # Only run if Phase 1 was NOT loaded from cache (i.e. fresh execution)
        if not cm.load("Phase 1 Requirements") or args.rerun_phase == "Phase 1 Requirements":
            sr = SkillResearcher(console)
            evolved = sr.analyze_and_evolve(req_output)
            if evolved:
                from config_loader import load_agent_roles
                global AGENT_ROLES
                AGENT_ROLES = load_agent_roles()
                console.print("[bold green]🔄 Agent Roles reloaded with newly acquired skills.[/bold green]")
            tr = ToolResearcher(console)
            tr.analyze_and_discover(req_output, AVAILABLE_TOOLS)

        # ------------------------------------------------------------------
        # Phase 2 & Gate 1 (Resilient)
        # ------------------------------------------------------------------
        arch_output = _run_phase_checkpointed(
            cp, "Phase 2 Architecture",
            lambda: execute_phase_with_resilience(
                cp,
                phase_name="Phase 2 Architecture",
                phase_objective=(
                    "Generate a simple schema and architecture components for the project. "
                    "VERY IMPORTANT: Every single code block MUST start with a comment containing "
                    "the exact file path (e.g., `# architecture.md`)."
                ),
                context=am.get("Phase 1 Requirements"),
                gate_name="Architecture Review",
                gate_objective="Ensure the architecture meets the requirements and is secure. If missing CORS or any security middleware, FAIL the gate.",
                reflection_manager=rm,
            ),
            am, cm, ss,
        )

        # Record gate result
        ss.record_gate(run_id, "Architecture Review", "PASS")

        # ------------------------------------------------------------------
        # Phases 3, 4, 5 — run in parallel (no inter-phase data dependency)
        # ------------------------------------------------------------------
        # Phase 4 (Frontend) benefits from Phase 3 context at runtime but Phase 3
        # artifacts are read from the ArtifactManager which is already populated
        # by Phase 2.  We pre-snapshot the arch context so lambdas close over it.
        arch_context    = am.get("Phase 2 Architecture")
        req_arch_context = am.get("Phase 1 Requirements", "Phase 2 Architecture")
        arch_be_fe_context = am.get("Phase 2 Architecture")

        parallel_specs = [
            (
                "Phase 3 Backend",
                lambda: run_phase(
                    cp,
                    "Phase 3 Backend",
                    "Implement the backend code based strictly on the architecture design. "
                    "VERY IMPORTANT: Every single code block MUST start with a comment containing "
                    "the exact file path (e.g., `# backend/app/main.py`).",
                    arch_context,
                ),
            ),
            (
                "Phase 4 Frontend",
                lambda: run_phase(
                    cp,
                    "Phase 4 Frontend",
                    "Implement the frontend application code to securely communicate with the backend. "
                    "VERY IMPORTANT: Every single code block MUST start with a comment containing "
                    "the exact file path (e.g., `// frontend/src/App.tsx`).",
                    req_arch_context,
                ),
            ),
            (
                "Phase 5 Infrastructure",
                lambda: run_phase(
                    cp,
                    "Phase 5 Infrastructure",
                    "Write Dockerfiles for the backend and frontend, and a root docker-compose.yml to run "
                    "the full stack including the database. VERY IMPORTANT: Every single code block MUST "
                    "start with a comment containing the exact file path (e.g., `# docker-compose.yml`).",
                    arch_be_fe_context,
                ),
            ),
        ]

        if args.no_parallel:
            # Sequential fallback (for debugging or low-VRAM setups)
            console.print(
                "[yellow]⚠️  --no-parallel flag set: running Phases 3/4/5 sequentially.[/yellow]"
            )
            parallel_results = {}
            for phase_name, phase_fn in parallel_specs:
                parallel_results[phase_name] = _run_phase_checkpointed(
                    cp, phase_name, phase_fn, am, cm, ss
                )
        else:
            parallel_results = run_parallel_phases(parallel_specs, cp, am, cm, ss)

        backend_output  = parallel_results["Phase 3 Backend"]
        frontend_output = parallel_results["Phase 4 Frontend"]
        infra_output    = parallel_results["Phase 5 Infrastructure"]

        # ------------------------------------------------------------------
        # Phase 6 & Gate 2 (Resilient)
        # ------------------------------------------------------------------
        qa_output = _run_phase_checkpointed(
            cp, "Phase 6 QA Testing",
            lambda: execute_phase_with_resilience(
                cp,
                phase_name="Phase 6 QA Testing",
                phase_objective=(
                    "Write a test suite for the backend application using pytest. "
                    "IMPORTANT: You must write tests that physically execute. "
                    "VERY IMPORTANT: Every code block MUST start with a comment containing the file path."
                ),
                context=am.get("Phase 3 Backend"),
                gate_name="QA Review",
                gate_objective="Evaluate the test cases to ensure they adequately cover the backend business logic and authentication.",
                reflection_manager=rm,
            ),
            am, cm, ss,
        )
        ss.record_gate(run_id, "QA Review", "PASS")

        # ------------------------------------------------------------------
        # Phase 7 & Gate 3 (Resilient)
        # ------------------------------------------------------------------
        sec_output = _run_phase_checkpointed(
            cp, "Phase 7 Security",
            lambda: execute_phase_with_resilience(
                cp,
                phase_name="Phase 7 Security",
                phase_objective=(
                    "Perform a security audit of the backend code and provide any secured file overwrites "
                    "if vulnerabilities exist. VERY IMPORTANT: Every single code block MUST start with a "
                    "comment containing the exact file path."
                ),
                context=am.get("Phase 3 Backend"),
                gate_name="Security Review",
                gate_objective="Validate that the backend code does not contain injection or auth vulnerabilities.",
                reflection_manager=rm,
            ),
            am, cm, ss,
        )
        ss.record_gate(run_id, "Security Review", "PASS")

        # ------------------------------------------------------------------
        # Phase 8: Deployment & Documentation
        # ------------------------------------------------------------------
        deploy_output = _run_phase_checkpointed(
            cp, "Phase 8 Deployment",
            lambda: run_phase(
                cp,
                "Phase 8 Deployment",
                "Write the final `README.md` that explains exactly how a user can build, start, and "
                "execute the application locally. VERY IMPORTANT: Every code block MUST start with a "
                "comment containing the file path.",
                am.get("Phase 5 Infrastructure", "Phase 6 QA Testing"),
            ),
            am, cm, ss,
        )

        ss.mark_complete(run_id)
        console.print("[bold green]✅ Session marked complete in session store.[/bold green]")

    except (KeyboardInterrupt, SystemExit):
        ss.mark_partial(run_id)
        console.print(
            Panel(
                f"[bold yellow]⏸️  Pipeline interrupted.[/bold yellow]\n"
                f"Session [cyan]{run_id}[/cyan] marked as [yellow]partial[/yellow].\n"
                f"Resume with: [white]python src/orchestrator.py \"{args.objective}\" --resume {run_id}[/white]",
                border_style="yellow",
            )
        )
        raise
    except Exception as pipeline_err:
        ss.mark_failed(run_id)
        console.print(
            Panel(
                f"[bold red]❌ Pipeline failed: {pipeline_err}[/bold red]\n"
                f"Session [cyan]{run_id}[/cyan] marked as [red]failed[/red].\n"
                f"Resume with: [white]python src/orchestrator.py \"{args.objective}\" --resume {run_id}[/white]",
                border_style="red",
            )
        )
        raise

    # ------------------------------------------------------------------
    # Memory Layer: Drift Detection
    # ------------------------------------------------------------------
    try:
        econ_summary = cp.get_economics_summary()
        for phase_name, data in econ_summary.items():
            cost_tracker.record_phase(
                phase_name=phase_name,
                agent_role=data["agent_role"],
                input_tokens=data["input_tokens"],
                output_tokens=data["output_tokens"],
                duration_seconds=data["duration_seconds"],
            )
        cost_tracker.write_report()

        console.print("\n[bold cyan]🧠 Memory Layer: Extracting Decision Fingerprint...[/bold cyan]")
        current_fingerprint = extractor.extract()

        baseline = baseline_store.get_baseline()
        if baseline:
            console.print("[yellow]🔍 Comparing with project baseline...[/yellow]")
            report = detector.detect(baseline, current_fingerprint)

            if report.has_drift:
                console.print(Panel(
                    f"[bold red]⚠️ Drift Detected![/bold red]\n"
                    f"Breaking Changes: [red]{report.breaking_count}[/red]\n"
                    f"Warnings: [yellow]{report.warning_count}[/yellow]\n\n"
                    + "\n".join(
                        [f"• [bold]{i.field}[/bold]: {i.old_value} -> {i.new_value} ({i.severity})"
                         for i in report.issues]
                    ),
                    title="Decision Drift Report",
                    border_style="red",
                ))
                log_audit_decision("[MEMORY] Drift Detection", f"Drift detected: {len(report.issues)} changes across architecture, infra, or quality.")

                if report.breaking_count > 0:
                    rbac_path = Path("logs/rbac_suggestions.md")
                    rbac_path.parent.mkdir(exist_ok=True)
                    with open(rbac_path, "a", encoding="utf-8") as rf:
                        rf.write(f"## Run ID: {run_id}\n")
                        rf.write(report.generate_rbac_snippet())
                    console.print(f"[dim]  ↳ RBAC lock suggested in logs/rbac_suggestions.md[/dim]")
            else:
                console.print("[bold green]✅ No drift — baseline confirmed[/bold green]")
                log_audit_decision("[MEMORY] Drift Detection", "No drift detected — baseline confirmed.")
        else:
            console.print("[bold cyan]✨ Baseline established in .asd/fingerprints/[/bold cyan]")
            log_audit_decision("[MEMORY] Establishing Baseline", f"First successful run for {args.project}. Baseline established.")

        baseline_store.save(current_fingerprint)
        console.print(f"[dim]↳ Fingerprint saved to: .asd/fingerprints/baseline.json[/dim]\n")
    except Exception as e:
        log_audit_decision("[MEMORY] Error", f"Memory Layer failed silently: {str(e)}")
        console.print(f"[dim red]⚠️ Memory Layer encountered a silent error (logged to audit).[/dim red]")

    cp.print_summary(console)
    report_path = cp.write_report()

    # ROI Tracker
    rt = ROITracker(cost_tracker)
    roi_md = rt.calculate_roi()
    rt.append_to_report(report_path, roi_md)

    # Visual Traceability
    mermaid_md = Visualizer.generate_mermaid(cp.steps)
    Visualizer.append_to_report(report_path, mermaid_md)

    # Knowledge Nugget Factory
    ca = ContentAgent(console)
    ca.generate_nuggets(report_path)

    console.print(Panel(
        "[bold green]Agentic SDLC v2.0 Completed All Phases Successfully![/bold green]\n"
        f"Run ID: [cyan]{run_id}[/cyan]\n"
        f"Check [cyan]logs/audit.md[/cyan] for the audit trail.\n"
        f"Check [cyan]{report_path}[/cyan] for the full Control Plane trace.\n"
        f"Checkpoints: [cyan].asd/checkpoints/{run_id}/[/cyan]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
