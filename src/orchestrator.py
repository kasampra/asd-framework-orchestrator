import os
import sys
import argparse
from pathlib import Path

# Ensure imports resolve when running `python src/orchestrator.py`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_server import get_framework_instructions, delegate_to_qwen_agent, evaluate_quality_gate, log_audit_decision

console = Console()

def print_header():
    console.print(Panel.fit(
        "[bold cyan]🤖 Agentic SDLC Orchestrator[/bold cyan]\n"
        "[dim]Powered by Local LMStudio (Qwen)[/dim]", 
        border_style="cyan"
    ))

def run_phase(phase_name: str, objective: str, context: str) -> str:
    """Runs a single phase using the Qwen agent and logs it."""
    with Progress(SpinnerColumn(), TextColumn(f"[bold yellow]Executing {phase_name}...[/bold yellow]"), console=console) as progress:
        task = progress.add_task("working", total=None)
        
        # 1. Call Agent
        output = delegate_to_qwen_agent(phase_name, objective, context)
        
        # 2. Log Action
        log_audit_decision(f"Phase Execute: {phase_name}", "Delegated task to Qwen worker.")
        
        # 3. Save Artifact
        filename = f"output_{phase_name.lower().replace(' ', '_')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output)
            
        progress.update(task, completed=100)
        
    console.print(f"[green]✓ {phase_name} completed![/green] (Saved to [cyan]{filename}[/cyan])\n")
    return output

def extract_and_write_files(markdown_text: str):
    """Parses markdown for code blocks containing file paths in the first line and writes them to disk."""
    import re
    # Find all code blocks
    pattern = r"```[a-zA-Z0-9]*\n(.*?)\n```"
    matches = re.finditer(pattern, markdown_text, re.DOTALL)
    
    extracted_count = 0
    for match in matches:
        content = match.group(1).strip()
        if not content:
            continue
            
        first_line = content.split('\n')[0].strip()
        
        # Heuristic: Find paths like `# app/main.py`, `// src/index.ts`, or `/* docker-compose.yml */`
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
            # Clean up path just in case
            file_path = file_path.replace("\\", "/")
            
            # Create directories if they don't exist
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
                
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[dim]  ↳ Extracted physical file: {file_path}[/dim]")
            extracted_count += 1
            
    if extracted_count > 0:
        console.print(f"[bold green]✓ Physically wrote {extracted_count} codebase files to disk![/bold green]\n")

def run_gate(gate_name: str, objective: str, context: str) -> bool:
    """Evaluates a hard gate using the Gatekeeper AI."""
    with Progress(SpinnerColumn(), TextColumn(f"[bold red]Gatekeeper Evaluating: {gate_name}...[/bold red]"), console=console) as progress:
        task = progress.add_task("working", total=None)
        
        result_text = evaluate_quality_gate(gate_name, objective, context)
        log_audit_decision(f"Gatekeeper: {gate_name}", result_text)
        
        progress.update(task, completed=100)
    
    if "DECISION: PASS" in result_text:
        console.print(f"[bold green]✓ GATE PASSED:[/bold green] {gate_name}\n")
        return True
    else:
        console.print(f"[bold red]✗ GATE FAILED:[/bold red] {gate_name}")
        console.print(result_text)
        return False

def main():
    parser = argparse.ArgumentParser(description="Agentic SDLC CLI")
    parser.add_argument("objective", type=str, help="What do you want to build?")
    args = parser.parse_args()

    print_header()
    console.print(f"[bold]Target Objective:[/bold] {args.objective}\n")

    # 1. Load Framework
    console.print("[dim]Loading AGENTS.md framework rules...[/dim]")
    instructions = get_framework_instructions()

    # Phase 1: Requirements
    req_output = run_phase("Phase 1 Requirements", args.objective, instructions)
    extract_and_write_files(req_output)

    # Phase 2: Architecture
    arch_output = run_phase(
        "Phase 2 Architecture", 
        "Generate a simple schema and architecture components for the project. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# architecture.md`).", 
        req_output[:2000] # Pass previous context
    )
    extract_and_write_files(arch_output)

    # Gate 1: Architecture Review
    passed = run_gate("Architecture Review", "Ensure the architecture meets the requirements and is secure.", arch_output)
    if not passed:
        console.print("[red]Pipeline halted due to architectural failure. Check audit logs.[/red]")
        sys.exit(1)

    # Phase 3: Backend
    backend_output = run_phase(
        "Phase 3 Backend", 
        "Implement the backend code based strictly on the architecture design. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# backend/app/main.py`).", 
        arch_output[:3000]
    )
    extract_and_write_files(backend_output)
    
    # Phase 4: Frontend
    frontend_output = run_phase(
        "Phase 4 Frontend", 
        "Implement the frontend application code to securely communicate with the backend. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `// frontend/src/App.tsx`).", 
        req_output[:1000] + "\n" + backend_output[:2000]
    )
    extract_and_write_files(frontend_output)

    # Phase 5: Infrastructure
    infra_output = run_phase(
        "Phase 5 Infrastructure", 
        "Write Dockerfiles for the backend and frontend, and a root docker-compose.yml to run the full stack including the database. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# docker-compose.yml`).", 
        arch_output[:1000] + "\n" + backend_output[:1000] + "\n" + frontend_output[:1000]
    )
    extract_and_write_files(infra_output)

    # Phase 6: QA Testing
    qa_output = run_phase(
        "Phase 6 QA Testing", 
        "Write a test suite for the backend application using pytest. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `# backend/tests/test_main.py`).", 
        backend_output[:3000]
    )
    extract_and_write_files(qa_output)

    # Gate 2: QA Review
    passed = run_gate("QA Review", "Evaluate the test cases to ensure they adequately cover the backend business logic and authentication.", qa_output)
    if not passed:
        console.print("[red]Pipeline halted due to QA Testing failure. Check audit logs.[/red]")
        sys.exit(1)

    # Phase 7: Security Audit
    sec_output = run_phase(
        "Phase 7 Security", 
        "Perform a security audit of the backend code and provide any secured file overwrites if vulnerabilities exist. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path.", 
        backend_output[:3000]
    )
    extract_and_write_files(sec_output)

    # Gate 3: Security Review
    passed = run_gate("Security Review", "Validate that the backend code does not contain injection or auth vulnerabilities.", sec_output)
    if not passed:
        console.print("[red]Pipeline halted due to Security vulnerabilities. Check audit logs.[/red]")
        sys.exit(1)

    # Phase 8: Deployment & Documentation
    deploy_output = run_phase(
        "Phase 8 Deployment", 
        "Write the final `README.md` that explains exactly how a user can build, start (e.g. docker-compose up), and execute the pytest test suite for the entire application stack locally. VERY IMPORTANT: Every single code block MUST start with a comment containing the exact file path (e.g., `<!-- README.md -->` or `# README.md`).", 
        infra_output[:2000] + "\n" + qa_output[:1000]
    )
    extract_and_write_files(deploy_output)

    console.print(Panel("[bold green]Agentic SDLC Completed All 8 Phases Successfully![/bold green]\nCheck the [cyan]logs/audit.md[/cyan] for the full automated reasoning trail, and open [cyan]README.md[/cyan] to test your generated app.", border_style="green"))

if __name__ == "__main__":
    main()
