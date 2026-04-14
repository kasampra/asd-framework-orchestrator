import os
import yaml
from pathlib import Path

# Resolve base paths regardless of where the script is executed
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
POLICY_PATH = BASE_DIR / ".asd" / "policies" / "agent_rbac.yaml"

def _load_policy():
    if not POLICY_PATH.exists():
        return {}
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_agent_roles() -> dict:
    """
    Returns a mapping of phase strings to agent personas from the YAML policy.
    """
    policy = _load_policy()
    agents = policy.get("agents", {})
    roles = {}
    for phase, config in agents.items():
        # Identity might be "Requirements Engineer — Phase 1"
        # We need to extract the persona part or just use the identity
        roles[phase] = config.get("identity", "Agent")
    return roles

def load_agent_skills() -> dict:
    """
    Returns a mapping of personas to their allowed MCP tools from the YAML policy.
    Note: The policy is keyed by phase/agent name, but skills are often looked up by persona.
    To maintain compatibility, we map identities to allowed_tools.
    """
    policy = _load_policy()
    agents = policy.get("agents", {})
    skills = {}
    for phase, config in agents.items():
        persona = config.get("identity")
        if persona:
            skills[persona] = config.get("allowed_tools", [])
    return skills

def load_instructions() -> str:
    """
    Reads the global system alignment from config/instructions.md.
    """
    inst_file = CONFIG_DIR / "instructions.md"
    if inst_file.exists():
        return inst_file.read_text(encoding="utf-8")
    return "No instructions found. Operate as a standard coding assistant."
