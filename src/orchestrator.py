import os
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
)
from control_plane import ControlPlane, ContextSnapshot, ToolSelectionRecord, IntentExecutionDiff

console = Console()

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

def run_phase(cp: ControlPlane, phase_name: str, objective: str, context: str) -> str:
    agent_role = AGENT_ROLES.get(phase_name, "Agent")
    step = cp.begin_step(phase_name, agent_role)
    start = time.time()

    step.context_snapshot.record("AGENTS.md (framework rules)", context[:500])
    step.context_snapshot.record("Phase Objective", objective)

    with Progress(SpinnerColumn(), TextColumn(f"[bold yellow]Executing {phase_name}...[/bold yellow]"), console=console) as progress:
        task = progress.add_task("working", total=None)
        
        result = delegate_to_qwen_agent(phase_name, objective, context)
        step.decision_trace = result.get("reasoning", "")
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
        log_audit_decision(f"Phase Execute: {phase_name}", f"Delegated task to Qwen worker.\nReasoning: {step.decision_trace[:300]}")
        
        filename = f"output_{phase_name.lower().replace(' ', '_')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output)
            
        progress.update(task, completed=100)
    
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
    return output

def run_gate(cp: ControlPlane, gate_name: str, objective: str, context: str) -> tuple[bool, str]:
    step = cp.begin_step(gate_name, "Gatekeeper AI")
    start = time.time()

    step.context_snapshot.record("Gate Objective", objective)
    step.context_snapshot.record("Verification Evidence", context[:500])

    with Progress(SpinnerColumn(), TextColumn(f"[bold red]Gatekeeper Evaluating: {gate_name}...[/bold red]"), console=console) as progress:
        task = progress.add_task("working", total=None)
        result = evaluate_quality_gate(gate_name, objective, context)
        
        step.decision_trace = result.get("thinking", "")
        step.tool_selection = ToolSelectionRecord(
            available_tools=result.get("available_tools", AVAILABLE_TOOLS),
            selected_tool=result.get("tool_used", "evaluate_quality_gate"),
            tool_inputs={
                "gate_name": gate_name,
                "phase_objective": objective[:200],
                "evidence_length": len(context),
            },
            selection_reasoning=f"Gate {gate_name} requires quality evaluation.",
        )

        decision = result.get("decision", "FAIL")
        reasoning = result.get("reasoning", "No reasoning provided")
        log_audit_decision(f"Gatekeeper: {gate_name}", f"DECISION: {decision}\nREASONING: {reasoning}")
        progress.update(task, completed=100)
    
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
        return False, reasoning

def execute_phase_with_resilience(cp: ControlPlane, phase_name: str, phase_objective: str, context: str, gate_name: str, gate_objective: str, max_retries: int = 2) -> str:
    """
    Executes a phase and its corresponding gate.
    If the gate fails, it autonomously auto-heals by passing the failure reasoning back to the agent.
    If auto-heals are exhausted, it pauses for an Interactive Human-in-the-Loop Handoff.
    """
    current_objective = phase_objective
    retries = 0
    
    while retries <= max_retries:
        output = run_phase(cp, phase_name, current_objective, context)
        passed, reasoning = run_gate(cp, gate_name, gate_objective, output)
        
        if passed:
            return output
            
        retries += 1
        if retries <= max_retries:
            console.print(f"\n[bold yellow]⚠️  Gate Failed. Triggering Auto-Heal (Retry {retries}/{max_retries})...[/bold yellow]")
            console.print(f"[dim]Passing Gatekeeper's reasoning back to the {phase_name} agent...[/dim]\n")
            current_objective = phase_objective + f"\n\n[CRITICAL CORRECTION REQUIRED]\nThe Gatekeeper rejected your previous code. Reason:\n{reasoning}\n\nPlease explicitly fix these issues and regenerate the code."
        else:
            console.print(f"\n[bold red]❌ Gate Failed {max_retries} times. Auto-Heal Exhausted.[/bold red]")
            console.print(Panel("Human-in-the-loop intervention required.", border_style="red"))
            
            choice = Prompt.ask(
                "Action Required", 
                choices=["1", "2", "3"], 
                default="1", 
                prompt="\n[1] Abort Pipeline\n[2] Provide Manual Feedback to Agent (Retry)\n[3] Force Pass Gate\nChoice"
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

def main():
    parser = argparse.ArgumentParser(description="Agentic SDLC CLI v2.0")
    parser.add_argument("objective", type=str, help="What do you want to build?")
    args = parser.parse_args()

    print_header()
    console.print(f"[bold]Target Objective:[/bold] {args.objective}\n")

    cp = ControlPlane()
    cp.objective = args.objective

    instructions = get_framework_instructions()

    # Phase 1: Requirements
    req_output = run_phase(cp, "Phase 1 Requirements", args.objective, instructions)

    # Phase 2 & Gate 1 (Resilient)
    arch_output = execute_phase_with_resilience(
        cp,
        phase_name="Phase 2 Architecture",
        phase_objective="Generate a simple schema and architecture components for the project. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# architecture.md`).",
        context=req_output[:2000],
        gate_name="Architecture Review",
        gate_objective="Ensure the architecture meets the requirements and is secure. If missing CORS or any security middleware, FAIL the gate."
    )

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

    # Phase 6 & Gate 2 (Resilient)
    qa_output = execute_phase_with_resilience(
        cp,
        phase_name="Phase 6 QA Testing",
        phase_objective="Write a test suite for the backend application using pytest. IMPORTANT: You must write tests that physically execute. VERY IMPORTANT: Every code block MUST start with a comment containing the file path.",
        context=backend_output[:3000],
        gate_name="QA Review",
        gate_objective="Evaluate the test cases to ensure they adequately cover the backend business logic and authentication."
    )

    # Phase 7 & Gate 3 (Resilient)
    sec_output = execute_phase_with_resilience(
        cp,
        phase_name="Phase 7 Security",
        phase_objective="Perform a security audit of the backend code and provide any secured file overwrites if vulnerabilities exist. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path.",
        context=backend_output[:3000],
        gate_name="Security Review",
        gate_objective="Validate that the backend code does not contain injection or auth vulnerabilities."
    )

    # Phase 8: Deployment & Documentation
    deploy_output = run_phase(
        cp,
        "Phase 8 Deployment", 
        "Write the final `README.md` that explains exactly how a user can build, start, and execute the application locally. VERY IMPORTANT: Every code block MUST start with a comment containing the file path.", 
        infra_output[:2000] + "\n" + qa_output[:1000]
    )

    cp.print_summary(console)
    report_path = cp.write_report()

    console.print(Panel(
        "[bold green]Agentic SDLC v2.0 Completed All Phases Successfully![/bold green]\n"
        f"Check [cyan]logs/audit.md[/cyan] for the audit trail.\n"
        f"Check [cyan]{report_path}[/cyan] for the full Control Plane trace.",
        border_style="green"
    ))

if __name__ == "__main__":
    main()
