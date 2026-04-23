import os
import datetime
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from qwen_client import QwenClient
from config_loader import load_agent_roles, load_agent_skills, load_instructions

# Initialize FastMCP Server
mcp = FastMCP("AgenticSDLC-Orchestrator")

# Initialize Qwen Client
qwen = QwenClient()

WORKSPACE_BASE_DIR = os.getenv("WORKSPACE_BASE_DIR", ".")
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "../.agent")

# Registry of available tools for control plane visibility
AVAILABLE_TOOLS = [
    "delegate_to_qwen_agent",
    "evaluate_quality_gate",
    "log_audit_decision",
    "get_framework_instructions",
    "execute_bash_command",
    "search_web",
]

@mcp.tool()
def search_web(query: str, depth: str = "mini") -> dict:
    """
    Conduct deep research on a topic using the Tavily-powered WebResearcher.
    Set depth to 'pro' for comprehensive analysis or 'mini' for quick lookups.
    """
    from services.web_researcher import WebResearcher
    researcher = WebResearcher()
    return researcher.conduct_research(query, model=depth)

@mcp.tool()
def get_framework_instructions() -> str:
    """
    Use this tool to retrieve the system rules.
    This will inform you how the 8-agent SDLC operates.
    """
    try:
        return load_instructions()
    except Exception as e:
        return f"Error reading instructions: {str(e)}"

@mcp.tool()
def execute_bash_command(command: str, cwd: str = ".") -> str:
    """
    Execute a native bash/terminal command on the host system.
    CRITICAL FOR QA AGENT: Use this to physically run `pytest` or `npm run lint` 
    to validate the AST/code correctness before marking the phase complete.
    
    Returns the stdout and stderr of the command.
    """
    try:
        # Ensure the directory exists
        Path(cwd).mkdir(parents=True, exist_ok=True)
        
        # We use shell=True to allow complex piping if needed, with a timeout to prevent infinite hangs
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = f"EXIT CODE: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        return output
    except Exception as e:
        return f"Failed to execute bash command: {str(e)}"

@mcp.tool()
def delegate_to_qwen_agent(phase_name: str, objective_prompt: str, context_documents: str = "") -> dict:
    """
    Delegate a specific project phase to the specialized local Qwen worker agent.

    Returns a structured dict:
    {
        "reasoning": str,       # The agent's thinking/reasoning chain
        "output": str,          # The final actionable output
        "raw": str,             # The complete unmodified response
        "tool_used": str,       # The tool name that was selected
        "available_tools": list # All tools that were available
    }
    """
    system_prompt = f"""
You are executing the {phase_name} Phase of the Agentic SDLC framework.
You MUST strictly follow the boundaries of your phase. Do not write code outside your designated folder scope.
Your output should detail the exact modifications you want to make, including reasoning and the final code artifacts.

IF YOU ARE THE QA AGENT: You MUST state that you are utilizing the execute_bash_command tool to run your tests to verify them. 
(Note: in this orchestrated pipeline, just state exactly the test commands you would run, and the orchestrator engine expects your final code output to be thoroughly verified).
"""
    user_prompt = f"""
Objective:
{objective_prompt}

Relevant Context & Artifacts:
{context_documents}

Execute the above objective and provide the generated code, designs, or output.
"""
    result = qwen.generate_response(system_prompt, user_prompt, temperature=0.2)
    
    roles = load_agent_roles()
    skills = load_agent_skills()
    persona = roles.get(phase_name, "Agent")
    allowed_tools = skills.get(persona, ["delegate_to_qwen_agent"])
    
    result["tool_used"] = "delegate_to_qwen_agent"
    result["available_tools"] = allowed_tools
    return result

@mcp.tool()
def evaluate_quality_gate(gate_name: str, phase_objective: str, verification_context: str) -> dict:
    """
    Use this tool at the "Hard Gates" (Architecture, QA, Security).
    Uses Qwen as a Gatekeeper AI to judge the outputs.

    Returns a structured dict:
    {
        "decision": str,        # PASS or FAIL
        "reasoning": str,       # Detailed explanation
        "thinking": str,        # The gatekeeper's internal reasoning chain
        "tool_used": str,
        "available_tools": list
    }
    """
    result = qwen.evaluate_gate(gate_name, phase_objective, verification_context)
    result["tool_used"] = "evaluate_quality_gate"
    result["available_tools"] = AVAILABLE_TOOLS
    return result

@mcp.tool()
def log_audit_decision(action: str, reasoning: str, context_file: str = "audit.md") -> str:
    """
    Log exactly what tradeoff or architectural decision was just made.
    """
    try:
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
