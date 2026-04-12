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
import re
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable


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
    input_tokens: int = 0
    output_tokens: int = 0
    compression_tier: int = 0  # 0: None, 1: Micro, 2: Auto, 3: Full

    # The 4 captures
    decision_trace: str = ""            # Raw reasoning chain from the agent
    context_snapshot: ContextSnapshot = field(default_factory=ContextSnapshot)
    tool_selection: ToolSelectionRecord = field(default_factory=ToolSelectionRecord)
    intent_diff: IntentExecutionDiff = field(default_factory=IntentExecutionDiff)

    # Outcome
    gate_decision: Optional[str] = None  # PASS / FAIL / None if not a gate
    output_file: str = ""

    def to_markdown(self) -> str:
        compression_labels = {0: "None", 1: "MicroCompact", 2: "AutoCompact", 3: "FullCompact"}
        lines = [
            f"## {self.phase_name}",
            f"**Agent Role:** {self.agent_role}  ",
            f"**Timestamp:** {self.timestamp}  ",
            f"**Duration:** {self.duration_seconds:.1f}s  ",
            f"**Tokens:** {self.input_tokens + self.output_tokens} (I:{self.input_tokens}/O:{self.output_tokens})  ",
            f"**Compression:** {compression_labels.get(self.compression_tier, 'Unknown')}  ",
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


class HookManager:
    """Manages event-driven hooks for the pipeline lifecycle."""
    def __init__(self):
        self.hooks: dict[str, list[Callable]] = {
            "pre_phase_start": [],
            "post_phase_complete": [],
            "on_gate_evaluate": [],
            "on_gate_fail": [],
        }

    def register(self, event_name: str, callback: Callable):
        if event_name in self.hooks:
            self.hooks[event_name].append(callback)

    def trigger(self, event_name: str, *args, **kwargs):
        if event_name in self.hooks:
            for callback in self.hooks[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️  Warning: Hook '{event_name}' failed: {str(e)}")


class ContextCompressor:
    """Implements three-tier context compression to prevent context window overflow."""
    
    @staticmethod
    def micro_compact(text: str) -> str:
        """Tier 1: Strip formatting, comments, and empty lines."""
        # Remove single line comments
        text = re.sub(r'(^|\s)(#|//).*', '', text)
        # Remove multi-line comments (simple regex approach)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'\'\'\'.*?\'\'\'', '', text, flags=re.DOTALL)
        text = re.sub(r'\"\"\".*?\"\"\"', '', text, flags=re.DOTALL)
        # Remove extra whitespace/newlines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    @staticmethod
    def auto_compact(text: str) -> str:
        """Tier 2: Truncate code block bodies while keeping signatures/docstrings."""
        def truncate_code_block(match):
            lang = match.group(1)
            content = match.group(2)
            lines = content.splitlines()
            if len(lines) <= 20:
                return match.group(0)
            
            # Keep first 5 and last 5 lines as a heuristic for signatures/end
            truncated = lines[:10] + [f"\n[... code truncated ... ({len(lines)-15} lines) ...]\n"] + lines[-5:]
            return f"```{lang}\n" + "\n".join(truncated) + "\n```"

        return re.sub(r"```([a-zA-Z0-9]*)\n(.*?)\n```", truncate_code_block, text, flags=re.DOTALL)

    @staticmethod
    def full_compact(text: str, qwen_client=None) -> str:
        """Tier 3: Use LLM to summarize context into a strict bulleted list."""
        if not qwen_client:
            return text[:1000] + "\n\n[... TRUNCATED DUE TO FALLBACK ...]\n\n" + text[-1000:]
        
        prompt = "Summarize the following project context and code into a strict, concise bulleted list of constraints, schemas, and requirements. Keep only essential technical details."
        result = qwen_client.generate_response("You are a context compression utility.", f"{prompt}\n\nContext:\n{text}")
        output = result.get("output", "")
        
        if not output or len(output) < 10:
            return text[:1000] + "\n\n[... TRUNCATED DUE TO FALLBACK ...]\n\n" + text[-1000:]
        return output

    def compress(self, text: str, max_tokens: int = 8000, qwen_client=None) -> tuple[str, int]:
        """Runs the compression pipeline until the estimated tokens are under max_tokens."""
        # Heuristic: 1 token ~= 4 characters for code/text
        def estimate_tokens(t):
            return len(t) // 4

        if estimate_tokens(text) <= max_tokens:
            return text, 0
        
        # Tier 1
        text = self.micro_compact(text)
        if estimate_tokens(text) <= max_tokens:
            return text, 1
        
        # Tier 2
        text = self.auto_compact(text)
        if estimate_tokens(text) <= max_tokens:
            return text, 2
        
        # Tier 3
        text = self.full_compact(text, qwen_client)
        return text, 3


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
        self.hooks = HookManager()
        self.compressor = ContextCompressor()

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
        lines.append("| # | Phase | Agent | Duration | Gate | Files | Comp |")
        lines.append("|---|-------|-------|----------|------|-------|------|")
        for i, step in enumerate(self.steps, 1):
            gate = step.gate_decision or "—"
            n_files = len(step.intent_diff.files_actually_written)
            lines.append(
                f"| {i} | {step.phase_name} | {step.agent_role} | "
                f"{step.duration_seconds:.1f}s | {gate} | {n_files} | {step.compression_tier} |"
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

    def get_economics_summary(self) -> dict:
        return {
            step.phase_name: {
                "agent_role": step.agent_role,
                "input_tokens": step.input_tokens,
                "output_tokens": step.output_tokens,
                "duration_seconds": step.duration_seconds
            }
            for step in self.steps
        }

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
