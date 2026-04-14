import os
import yaml
import sys
from pathlib import Path

class PolicyValidator:
    POLICY_PATH = Path(".asd/policies/agent_rbac.yaml")

    @classmethod
    def validate(cls):
        if not cls.POLICY_PATH.exists():
            print(f"[ERROR] Policy file not found: {cls.POLICY_PATH}")
            sys.exit(1)

        try:
            with open(cls.POLICY_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                policy = yaml.safe_load(content)
        except Exception as e:
            print(f"[ERROR] Failed to parse policy file: {str(e)}")
            sys.exit(1)

        agents = policy.get("agents", {})
        if not agents:
            print("[POLICY VIOLATION] No agents defined in policy.")
            sys.exit(1)

        violations = []
        agent_count = 0

        for agent_name, config in agents.items():
            agent_count += 1
            
            # a. identity is present and non-empty
            identity = config.get("identity")
            if not identity:
                violations.append((agent_name, "identity", "Identity is missing or empty"))

            # b. allowed_tools is a non-empty list
            allowed_tools = config.get("allowed_tools")
            if not isinstance(allowed_tools, list) or not allowed_tools:
                violations.append((agent_name, "allowed_tools", "allowed_tools must be a non-empty list"))

            # c. denied_tools is a non-empty list
            denied_tools = config.get("denied_tools")
            if not isinstance(denied_tools, list) or not denied_tools:
                violations.append((agent_name, "denied_tools", "denied_tools must be a non-empty list (empty = violation)"))

            # d. alignment has at least one constraint
            alignment = config.get("alignment")
            if not isinstance(alignment, list) or not alignment:
                violations.append((agent_name, "alignment", "alignment must have at least one constraint"))

            # e. No tool appears in both allowed_tools and denied_tools simultaneously
            if allowed_tools and denied_tools:
                overlap = set(allowed_tools) & set(denied_tools)
                if overlap:
                    violations.append((agent_name, "tools", f"Tools appear in both allowed and denied: {list(overlap)}"))

            # f. No agent has access to write_deployment_path or run_terminal unless explicitly listed under allowed_tools with a justification comment in the YAML
            restricted_tools = ["write_deployment_path", "run_terminal"]
            if allowed_tools:
                for tool in restricted_tools:
                    if tool in allowed_tools:
                        # Check for justification comment in the YAML file
                        if not cls._has_justification(content, agent_name, tool):
                            violations.append((agent_name, "allowed_tools", f"Access to {tool} requires a justification comment in the YAML"))

        if violations:
            for agent_name, field, reason in violations:
                print(f"[POLICY VIOLATION] {agent_name}")
                print(f"  {field}: {reason}")
                # For specific constraint messages as requested in output format
                if field == "denied_tools" and "empty" in reason:
                     print(f"  No agent may have an empty denied_tools block — an empty list is a policy violation, not a safe default.")
            
            print("→ Policy failed. Pipeline halted.")
            raise Exception("Policy validation failed.")

        print(f"[POLICY OK] All {agent_count} agents validated. Default Deny enforced. Pipeline cleared.")

    @classmethod
    def _has_justification(cls, content: str, agent_name: str, tool: str) -> bool:
        lines = content.splitlines()
        in_agent_block = False
        in_allowed_tools = False
        
        for line in lines:
            stripped = line.strip()
            # This is a very basic YAML line parser to find the tool line within the agent's allowed_tools block
            if line.startswith(f"  \"{agent_name}\":") or line.startswith(f"  {agent_name}:"):
                in_agent_block = True
                continue
            
            if in_agent_block:
                if line.startswith("  ") and not line.startswith("    "):
                    # We've moved to another agent or top-level key
                    if stripped and not stripped.startswith("#"):
                        in_agent_block = False
                
                if "allowed_tools:" in line:
                    in_allowed_tools = True
                    continue
                
                if in_allowed_tools:
                    if "- " + tool in stripped:
                        # Found the tool line, check for comment
                        if "#" in line:
                            comment = line.split("#", 1)[1].strip()
                            if comment:
                                return True
                    elif stripped.startswith("-") or not stripped:
                        continue
                    else:
                        # Left allowed_tools block
                        in_allowed_tools = False
        
        return False

if __name__ == "__main__":
    # For testing purposes
    try:
        PolicyValidator.validate()
    except Exception:
        sys.exit(1)
