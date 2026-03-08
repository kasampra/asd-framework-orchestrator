import os
import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from qwen_client import QwenClient

# Initialize FastMCP Server
mcp = FastMCP("AgenticSDLC-Orchestrator")

# Initialize Qwen Client
qwen = QwenClient()

WORKSPACE_BASE_DIR = os.getenv("WORKSPACE_BASE_DIR", ".")
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "../.agent")

@mcp.tool()
def get_framework_instructions() -> str:
    """
    Claude Code: Use this tool to retrieve the system rules from AGENTS.md.
    This will inform you how the 8-agent SDLC operates.
    """
    # The AGENTS.md file lives in the root directory
    agents_path = Path("..") / "AGENTS.md"
    try:
        if agents_path.exists():
            return agents_path.read_text(encoding="utf-8")
        else:
            return "AGENTS.md not found in root directory. Proceed with standard software development best practices but strictly segregate frontend, backend, and infra."
    except Exception as e:
        return f"Error reading instructions: {str(e)}"

@mcp.tool()
def delegate_to_qwen_agent(phase_name: str, objective_prompt: str, context_documents: str = "") -> str:
    """
    Claude Code: Use this tool to delegate a specific project phase (e.g. backend, frontend) 
    to the specialized local Qwen worker agent.

    Args:
        phase_name: Name of the phase being run (e.g. "Requirements", "Backend", "Frontend").
        objective_prompt: The desired outcome or task description you want Qwen to produce.
        context_documents: Supporting files or architecture designs Qwen needs to do the job.
    """
    # Create the system prompt that forces Qwen to adhere to the framework
    system_prompt = f"""
You are executing the {phase_name} Phase of the Agentic SDLC framework.
You MUST strictly follow the boundaries of your phase. Do not write code outside your designated folder scope.
Your output should detail the exact modifications you want to make, including reasoning and the final code artifacts.
Always include your tradeoffs and decisions clearly.
"""
    # Construct the query
    user_prompt = f"""
Objective:
{objective_prompt}

Relevant Context & Artifacts:
{context_documents}

Execute the above objective and provide the generated code, designs, or output.
"""
    return qwen.generate_response(system_prompt, user_prompt, temperature=0.2)

@mcp.tool()
def evaluate_quality_gate(gate_name: str, phase_objective: str, verification_context: str) -> str:
    """
    Claude Code: Use this tool at the "Hard Gates" (Phase 2 Architect and Phase 7 Security/QA).
    This substitutes human intervention by using Qwen as a Gatekeeper AI to judge the outputs.
    
    Args:
        gate_name: e.g. "Architecture Review" or "Security Audit"
        phase_objective: What the phase *should* have done.
        verification_context: The outputs you want the Gatekeeper to evaluate.
    """
    result = qwen.evaluate_gate(gate_name, phase_objective, verification_context)
    # Result is a dictionary with 'decision' and 'reasoning'
    return f"GATE: {gate_name}\nDECISION: {result.get('decision', 'FAIL')}\nREASONING: {result.get('reasoning', 'No reasoning provided')}"

@mcp.tool()
def log_audit_decision(action: str, reasoning: str, context_file: str = "audit.md") -> str:
    """
    Claude Code: Use this tool after EVERY phase to log exactly what tradeoff or 
    architectural decision was just made.
    """
    try:
        # Determine log path. Defaulting to the workspace path or local dir
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        file_path = log_path / context_file
        
        timestamp = datetime.datetime.now().isoformat()
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"### Timestamp: {timestamp}\n")
            f.write(f"**Action/Phase:** {action}\n")
            f.write(f"**Decision Reasoning & Tradeoffs:**\n{reasoning}\n")
            f.write("---\n\n")
            
        return f"Successfully logged decision to {file_path.absolute()}"
    except Exception as e:
        return f"Failed to log decision: {str(e)}"

if __name__ == "__main__":
    mcp.run()
