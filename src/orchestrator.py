import os
import sys
import time
import argparse
from pathlib import Path

# Ensure imports resolve when running `python src/orchestrator.py`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_server import (
    get_framework_instructions,
    delegate_to_qwen_agent,
    evaluate_quality_gate,
    log_audit_decision,
    AVAILABLE_TOOLS,
)
from control_plane import ControlPlane, ContextSnapshot, ToolSelectionRecord, IntentExecutionDiff

console = Console()

# Agent roles mapped to phases (from the ASD Framework)
AGENT_ROLES = {
    "Phase 1 Requirements": "Requirements Engineer",
    "Phase 2 Architecture": "System Architect",
    "Phase 3 Backend": "Backend Developer",
    "Phase 4 Frontend": "Frontend Developer",
    "Phase 5 Infrastructure": "DevOps Engineer",
    "Phase 6 QA Testing": "QA Engineer",
    "Phase 7 Security": "Security Analyst",
    "Phase 8 Deployment": "Technical Writer",
    "Architecture Review": "Gatekeeper AI",
    "QA Review": "Gatekeeper AI",
    "Security Review": "Gatekeeper AI",
}


def print_header():
    console.print(Panel.fit(
        "[bold cyan]🤖 Agentic SDLC Orchestrator[/bold cyan]\n"
        "[dim]Powered by Local LMStudio (Qwen) · Control Plane Active[/dim]", 
        border_style="cyan"
    ))


def extract_and_write_files(markdown_text: str) -> list[str]:
    """Parses markdown for code blocks containing file paths and writes them to disk.
    Returns a list of file paths that were actually written."""
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


def run_phase(cp: ControlPlane, phase_name: str, objective: str, context: str) -> str:
    """Runs a single phase using the Qwen agent, wired into the Control Plane."""
    agent_role = AGENT_ROLES.get(phase_name, "Agent")
    step = cp.begin_step(phase_name, agent_role)
    start = time.time()

    # --- 2. Context Snapshot ---
    step.context_snapshot.record("AGENTS.md (framework rules)", context[:500])
    step.context_snapshot.record("Phase Objective", objective)

    with Progress(SpinnerColumn(), TextColumn(f"[bold yellow]Executing {phase_name}...[/bold yellow]"), console=console) as progress:
        task = progress.add_task("working", total=None)
        
        # 1. Call Agent (returns structured dict)
        result = delegate_to_qwen_agent(phase_name, objective, context)
        
        # --- 1. Decision Trace ---
        step.decision_trace = result.get("reasoning", "")

        # --- 3. Tool Selection Record ---
        step.tool_selection = ToolSelectionRecord(
            available_tools=result.get("available_tools", AVAILABLE_TOOLS),
            selected_tool=result.get("tool_used", "delegate_to_qwen_agent"),
            tool_inputs={
                "phase_name": phase_name,
                "objective_prompt": objective[:200] + "..." if len(objective) > 200 else objective,
                "context_length": len(context),
            },
            selection_reasoning=f"Phase {phase_name} requires code generation; delegate_to_qwen_agent is the appropriate tool.",
        )

        output = result.get("output", "")
        
        # 2. Log Action
        log_audit_decision(f"Phase Execute: {phase_name}", f"Delegated task to Qwen worker.\nReasoning: {step.decision_trace[:300]}")
        
        # 3. Save Artifact
        filename = f"output_{phase_name.lower().replace(' ', '_')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output)
            
        progress.update(task, completed=100)
    
    # --- 4. Intent-to-Execution Diff ---
    written_files = extract_and_write_files(output)
    step.intent_diff = IntentExecutionDiff(
        intended_plan=objective[:300],
        actual_output_summary=f"Generated {len(output)} chars of output, extracted {len(written_files)} files.",
        files_planned=[],  # We don't know planned files ahead of time
        files_actually_written=written_files,
    )
    step.output_file = filename

    cp.finalize_step(step, start)
    console.print(f"[green]✓ {phase_name} completed![/green] (Saved to [cyan]{filename}[/cyan])\n")
    return output


def run_gate(cp: ControlPlane, gate_name: str, objective: str, context: str) -> bool:
    """Evaluates a hard gate using the Gatekeeper AI, wired into the Control Plane."""
    step = cp.begin_step(gate_name, "Gatekeeper AI")
    start = time.time()

    # --- 2. Context Snapshot ---
    step.context_snapshot.record("Gate Objective", objective)
    step.context_snapshot.record("Verification Evidence", context[:500])

    with Progress(SpinnerColumn(), TextColumn(f"[bold red]Gatekeeper Evaluating: {gate_name}...[/bold red]"), console=console) as progress:
        task = progress.add_task("working", total=None)
        
        result = evaluate_quality_gate(gate_name, objective, context)

        # --- 1. Decision Trace ---
        step.decision_trace = result.get("thinking", "")

        # --- 3. Tool Selection Record ---
        step.tool_selection = ToolSelectionRecord(
            available_tools=result.get("available_tools", AVAILABLE_TOOLS),
            selected_tool=result.get("tool_used", "evaluate_quality_gate"),
            tool_inputs={
                "gate_name": gate_name,
                "phase_objective": objective[:200],
                "evidence_length": len(context),
            },
            selection_reasoning=f"Gate {gate_name} requires quality evaluation; evaluate_quality_gate was selected over direct execution.",
        )

        decision = result.get("decision", "FAIL")
        reasoning = result.get("reasoning", "No reasoning provided")
        
        log_audit_decision(f"Gatekeeper: {gate_name}", f"DECISION: {decision}\nREASONING: {reasoning}")
        
        progress.update(task, completed=100)
    
    step.gate_decision = decision

    # --- 4. Intent-to-Execution Diff ---
    step.intent_diff = IntentExecutionDiff(
        intended_plan=f"Evaluate whether the evidence meets the criteria for: {objective[:200]}",
        actual_output_summary=f"Gate {gate_name} returned {decision}. {reasoning[:200]}",
    )

    cp.finalize_step(step, start)
    
    if decision == "PASS":
        console.print(f"[bold green]✓ GATE PASSED:[/bold green] {gate_name}\n")
        return True
    else:
        console.print(f"[bold red]✗ GATE FAILED:[/bold red] {gate_name}")
        console.print(f"[dim]{reasoning}[/dim]")
        return False


def main():
    parser = argparse.ArgumentParser(description="Agentic SDLC CLI")
    parser.add_argument("objective", type=str, help="What do you want to build?")
    args = parser.parse_args()

    print_header()
    console.print(f"[bold]Target Objective:[/bold] {args.objective}\n")

    # Initialize the Control Plane
    cp = ControlPlane()
    cp.objective = args.objective
    console.print("[dim cyan]🔍 Control Plane initialized. All agent decisions will be traced.[/dim cyan]\n")

    # 1. Load Framework
    console.print("[dim]Loading AGENTS.md framework rules...[/dim]")
    instructions = get_framework_instructions()

    # Phase 1: Requirements
    req_output = run_phase(cp, "Phase 1 Requirements", args.objective, instructions)

    # Phase 2: Architecture
    arch_output = run_phase(
        cp,
        "Phase 2 Architecture", 
        "Generate a simple schema and architecture components for the project. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# architecture.md`).", 
        req_output[:2000]
    )

    # Gate 1: Architecture Review
    passed = run_gate(cp, "Architecture Review", "Ensure the architecture meets the requirements and is secure.", arch_output)
    if not passed:
        console.print("[red]Pipeline halted due to architectural failure. Check audit logs.[/red]")
        cp.print_summary(console)
        report_path = cp.write_report()
        console.print(f"[cyan]📄 Control Plane report saved to: {report_path}[/cyan]")
        sys.exit(1)

    # Phase 3: Backend
    backend_output = run_phase(
        cp,
        "Phase 3 Backend", 
        "Implement the backend code based strictly on the architecture design. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# backend/app/main.py`).", 
        arch_output[:3000]
    )
    
    # Phase 4: Frontend
    frontend_output = run_phase(
        cp,
        "Phase 4 Frontend", 
        "Implement the frontend application code to securely communicate with the backend. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `// frontend/src/App.tsx`).", 
        req_output[:1000] + "\n" + backend_output[:2000]
    )

    # Phase 5: Infrastructure
    infra_output = run_phase(
        cp,
        "Phase 5 Infrastructure", 
        "Write Dockerfiles for the backend and frontend, and a root docker-compose.yml to run the full stack including the database. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# docker-compose.yml`).", 
        arch_output[:1000] + "\n" + backend_output[:1000] + "\n" + frontend_output[:1000]
    )

    # Phase 6: QA Testing
    qa_output = run_phase(
        cp,
        "Phase 6 QA Testing", 
        "Write a test suite for the backend application using pytest. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# backend/tests/test_main.py`).", 
        backend_output[:3000]
    )

    # Gate 2: QA Review
    passed = run_gate(cp, "QA Review", "Evaluate the test cases to ensure they adequately cover the backend business logic and authentication.", qa_output)
    if not passed:
        console.print("[red]Pipeline halted due to QA Testing failure. Check audit logs.[/red]")
        cp.print_summary(console)
        report_path = cp.write_report()
        console.print(f"[cyan]📄 Control Plane report saved to: {report_path}[/cyan]")
        sys.exit(1)

    # Phase 7: Security Audit
    sec_output = run_phase(
        cp,
        "Phase 7 Security", 
        "Perform a security audit of the backend code and provide any secured file overwrites if vulnerabilities exist. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path.", 
        backend_output[:3000]
    )

    # Gate 3: Security Review
    passed = run_gate(cp, "Security Review", "Validate that the backend code does not contain injection or auth vulnerabilities.", sec_output)
    if not passed:
        console.print("[red]Pipeline halted due to Security vulnerabilities. Check audit logs.[/red]")
        cp.print_summary(console)
        report_path = cp.write_report()
        console.print(f"[cyan]📄 Control Plane report saved to: {report_path}[/cyan]")
        sys.exit(1)

    # Phase 8: Deployment & Documentation
    deploy_output = run_phase(
        cp,
        "Phase 8 Deployment", 
        "Write the final `README.md` that explains exactly how a user can build, start (e.g. docker-compose up), and execute the pytest test suite for the entire application stack locally. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `<!-- README.md -->` or `# README.md`).", 
        infra_output[:2000] + "\n" + qa_output[:1000]
    )

    # --- Render the Control Plane ---
    cp.print_summary(console)
    report_path = cp.write_report()

    console.print(Panel(
        "[bold green]Agentic SDLC Completed All 8 Phases Successfully![/bold green]\n"
        f"Check [cyan]logs/audit.md[/cyan] for the audit trail.\n"
        f"Check [cyan]{report_path}[/cyan] for the full Control Plane trace.\n"
        "Open [cyan]README.md[/cyan] to test your generated app.",
        border_style="green"
    ))

if __name__ == "__main__":
    main()
