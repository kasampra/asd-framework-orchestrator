"""
Control Plane Layer for the ASD Framework Orchestrator.

Sits between the agent's reasoning and the agent's action.
Every decision passes through it before anything executes.

Captures 4 types of telemetry for every single step:
1. Decision Trace     — the agent's full reasoning chain
2. Context Snapshot   — exact documents loaded into the prompt
3. Tool Selection Record — which tool was picked and why
4. Intent-to-Execution Diff — plan vs. actual output
"""

import hashlib
import datetime
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ContextSnapshot:
    """Records exact documents, character lengths, and content hashes loaded into the prompt."""
    documents: list = field(default_factory=list)  # list of {"name", "chars", "hash"}

    def record(self, name: str, content: str):
        self.documents.append({
            "name": name,
            "chars": len(content),
            "hash": hashlib.sha256(content.encode("utf-8")).hexdigest()[:12],
        })

    def to_markdown(self) -> str:
        if not self.documents:
            return "_No documents loaded._\n"
        lines = ["| Document | Characters | Content Hash |",
                 "|----------|-----------|--------------|"]
        for doc in self.documents:
            lines.append(f"| {doc['name']} | {doc['chars']:,} | `{doc['hash']}` |")
        return "\n".join(lines) + "\n"


@dataclass
class ToolSelectionRecord:
    """Records which tools the agent considered, which one it picked, and what inputs it passed."""
    available_tools: list = field(default_factory=list)
    selected_tool: str = ""
    tool_inputs: dict = field(default_factory=dict)
    selection_reasoning: str = ""

    def to_markdown(self) -> str:
        lines = [f"**Available Tools:** {', '.join(self.available_tools)}",
                 f"**Selected Tool:** `{self.selected_tool}`",
                 f"**Selection Reasoning:** {self.selection_reasoning}",
                 "",
                 "**Inputs Passed:**",
                 "```json"]
        import json
        lines.append(json.dumps(self.tool_inputs, indent=2, default=str))
        lines.append("```")
        return "\n".join(lines) + "\n"


@dataclass
class IntentExecutionDiff:
    """Diffs the agent's stated plan vs. the actual output."""
    intended_plan: str = ""
    actual_output_summary: str = ""
    files_planned: list = field(default_factory=list)
    files_actually_written: list = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = ["**Intended Plan:**",
                 f"> {self.intended_plan}" if self.intended_plan else "> _No explicit plan stated._",
                 "",
                 "**Actual Output Summary:**",
                 f"> {self.actual_output_summary}" if self.actual_output_summary else "> _No summary available._",
                 ""]

        # File diff
        planned_set = set(self.files_planned)
        actual_set = set(self.files_actually_written)
        missing = planned_set - actual_set
        extra = actual_set - planned_set
        matched = planned_set & actual_set

        if matched:
            lines.append(f"✅ **Matched ({len(matched)}):** {', '.join(sorted(matched))}")
        if missing:
            lines.append(f"❌ **Planned but missing ({len(missing)}):** {', '.join(sorted(missing))}")
        if extra:
            lines.append(f"➕ **Unplanned extras ({len(extra)}):** {', '.join(sorted(extra))}")
        if not planned_set and not actual_set:
            lines.append("_No file-level plan or output to compare._")

        return "\n".join(lines) + "\n"


@dataclass
class StepTrace:
    """Complete telemetry record for a single agent step."""
    phase_name: str
    agent_role: str
    timestamp: str = ""
    duration_seconds: float = 0.0

    # The 4 captures
    decision_trace: str = ""            # Raw reasoning chain from the agent
    context_snapshot: ContextSnapshot = field(default_factory=ContextSnapshot)
    tool_selection: ToolSelectionRecord = field(default_factory=ToolSelectionRecord)
    intent_diff: IntentExecutionDiff = field(default_factory=IntentExecutionDiff)

    # Outcome
    gate_decision: Optional[str] = None  # PASS / FAIL / None if not a gate
    output_file: str = ""

    def to_markdown(self) -> str:
        lines = [
            f"## {self.phase_name}",
            f"**Agent Role:** {self.agent_role}  ",
            f"**Timestamp:** {self.timestamp}  ",
            f"**Duration:** {self.duration_seconds:.1f}s  ",
        ]
        if self.gate_decision:
            emoji = "✅" if self.gate_decision == "PASS" else "❌"
            lines.append(f"**Gate Decision:** {emoji} {self.gate_decision}  ")
        if self.output_file:
            lines.append(f"**Output Artifact:** `{self.output_file}`  ")

        lines.append("")

        # 1. Decision Trace
        lines.append("### 1. Decision Trace")
        if self.decision_trace:
            lines.append(f"```\n{self.decision_trace}\n```")
        else:
            lines.append("_Agent did not expose an explicit reasoning chain._")
        lines.append("")

        # 2. Context Snapshot
        lines.append("### 2. Context Snapshot")
        lines.append(self.context_snapshot.to_markdown())

        # 3. Tool Selection Record
        lines.append("### 3. Tool Selection Record")
        lines.append(self.tool_selection.to_markdown())

        # 4. Intent-to-Execution Diff
        lines.append("### 4. Intent-to-Execution Diff")
        lines.append(self.intent_diff.to_markdown())

        lines.append("---\n")
        return "\n".join(lines)


class ControlPlane:
    """
    Manages the trace log for the entire pipeline run.
    Sits between the agent's reasoning and the agent's action.
    """

    def __init__(self):
        self.run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_start = datetime.datetime.now()
        self.steps: list[StepTrace] = []
        self.objective: str = ""

    def begin_step(self, phase_name: str, agent_role: str) -> StepTrace:
        """Start recording a new pipeline step."""
        step = StepTrace(
            phase_name=phase_name,
            agent_role=agent_role,
            timestamp=datetime.datetime.now().isoformat(),
        )
        self.steps.append(step)
        return step

    def finalize_step(self, step: StepTrace, start_time: float):
        """Record the duration of a completed step."""
        import time
        step.duration_seconds = time.time() - start_time

    def render_report(self) -> str:
        """Generate the full control plane report as markdown."""
        run_duration = (datetime.datetime.now() - self.run_start).total_seconds()

        lines = [
            "# 🔍 ASD Orchestrator — Control Plane Report",
            "",
            f"**Run ID:** `{self.run_id}`  ",
            f"**Objective:** {self.objective}  ",
            f"**Total Duration:** {run_duration:.1f}s  ",
            f"**Steps Traced:** {len(self.steps)}  ",
            f"**Generated:** {datetime.datetime.now().isoformat()}  ",
            "",
            "---",
            "",
        ]

        # Summary table
        lines.append("## Pipeline Summary")
        lines.append("")
        lines.append("| # | Phase | Agent | Duration | Gate | Files |")
        lines.append("|---|-------|-------|----------|------|-------|")
        for i, step in enumerate(self.steps, 1):
            gate = step.gate_decision or "—"
            n_files = len(step.intent_diff.files_actually_written)
            lines.append(
                f"| {i} | {step.phase_name} | {step.agent_role} | "
                f"{step.duration_seconds:.1f}s | {gate} | {n_files} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

        # Full traces
        lines.append("## Detailed Step Traces")
        lines.append("")
        for step in self.steps:
            lines.append(step.to_markdown())

        return "\n".join(lines)

    def write_report(self, output_dir: str = "logs"):
        """Write the control plane report to disk."""
        Path(output_dir).mkdir(exist_ok=True)
        report = self.render_report()
        filepath = Path(output_dir) / "control_plane.md"
        filepath.write_text(report, encoding="utf-8")
        return str(filepath)

    def print_summary(self, console):
        """Print a rich summary table to the terminal."""
        from rich.table import Table

        table = Table(
            title="🔍 Control Plane Summary",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Phase", style="white")
        table.add_column("Agent", style="yellow")
        table.add_column("Duration", style="green")
        table.add_column("Gate", style="bold")
        table.add_column("Reasoning", style="dim", max_width=50)

        for i, step in enumerate(self.steps, 1):
            gate_str = ""
            if step.gate_decision == "PASS":
                gate_str = "[green]✅ PASS[/green]"
            elif step.gate_decision == "FAIL":
                gate_str = "[red]❌ FAIL[/red]"
            else:
                gate_str = "—"

            reasoning_preview = (step.decision_trace[:47] + "...") if len(step.decision_trace) > 50 else step.decision_trace
            if not reasoning_preview:
                reasoning_preview = "—"

            table.add_row(
                str(i),
                step.phase_name,
                step.agent_role,
                f"{step.duration_seconds:.1f}s",
                gate_str,
                reasoning_preview,
            )

        console.print()
        console.print(table)
        console.print()
