import os
import re
from pathlib import Path

# Resolve base paths regardless of where the script is executed
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"

def load_agent_roles() -> dict:
    """
    Parses config/agents.md to return a mapping of phase strings to agent personas.
    Example line: "- Phase 1 Requirements > Requirements Engineer"
    """
    roles = {}
    agents_file = CONFIG_DIR / "agents.md"
    
    if not agents_file.exists():
        # Fallback if config is missing during initial run
        return {}

    content = agents_file.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("-") and ">" in line:
            parts = line[1:].split(">")
            if len(parts) == 2:
                phase = parts[0].strip()
                persona = parts[1].strip()
                roles[phase] = persona

    return roles

def load_agent_skills() -> dict:
    """
    Parses config/skills.md to return a mapping of personas to their allowed MCP tools.
    Example:
    ## Backend Developer
    - delegate_to_qwen_agent
    """
    skills = {}
    skills_file = CONFIG_DIR / "skills.md"
    
    if not skills_file.exists():
        return {}

    content = skills_file.read_text(encoding="utf-8")
    current_persona = None
    
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("## "):
            current_persona = line[3:].strip()
            skills[current_persona] = []
        elif line.startswith("- ") and current_persona:
            tool_name = line[2:].strip()
            skills[current_persona].append(tool_name)

    return skills

def load_instructions() -> str:
    """
    Reads the global system alignment from config/instructions.md.
    """
    inst_file = CONFIG_DIR / "instructions.md"
    if inst_file.exists():
        return inst_file.read_text(encoding="utf-8")
    return "No instructions found. Operate as a standard coding assistant."
