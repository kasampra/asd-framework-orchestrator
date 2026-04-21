import os
import yaml
from pathlib import Path
from mcp_server import delegate_to_qwen_agent

class SkillResearcher:
    """Analyzes requirements to identify and implement missing agent skills."""
    
    def __init__(self, console, policy_path=".asd/policies/agent_rbac.yaml"):
        self.console = console
        self.policy_path = Path(policy_path)

    def analyze_and_evolve(self, requirements: str):
        self.console.print("🔬 [bold blue]Starting Skill Gap Analysis...[/bold blue]")
        
        # 1. Load current policy
        with open(self.policy_path, "r", encoding="utf-8") as f:
            current_policy = yaml.safe_load(f)
            
        current_agents = list(current_policy.get("agents", {}).keys())
        
        # 2. Ask Agent to find gaps
        analysis_prompt = f"""
        You are a Sovereign AI Architect. Review the project requirements and the current Agentic SDLC capabilities.
        
        PROJECT REQUIREMENTS:
        {requirements}
        
        CURRENT AGENT ROLES:
        {', '.join(current_agents)}
        
        TASK:
        1. Identify if this project requires a specialized skill NOT covered by standard roles.
        2. If a gap is found, define a new 'Specialized Agent' role in YAML format.
        3. The YAML must include 'identity', 'allowed_tools', and 'alignment'.
        
        Example Output:
        [GAP_FOUND]
        Specialized Role Name: "Phase 3.5 Database Optimizer"
        YAML:
        identity: "Database Tuning Expert"
        allowed_tools: ["delegate_to_qwen_agent", "execute_bash_command"]
        alignment: ["focus_on_index_optimization", "use_explain_analyze"]
        
        If no gap is found, respond with [NO_GAP].
        """
        
        result = delegate_to_qwen_agent("Skill Research", analysis_prompt, "")
        analysis_output = result.get("output", "")
        
        if "[GAP_FOUND]" in analysis_output:
            self.console.print("🚀 [bold green]Skill Gap Found! Evolving framework...[/bold green]")
            self._apply_evolution(analysis_output, current_policy)
            return True
        else:
            self.console.print("✅ [dim]No skill gaps identified for this project stack.[/dim]")
            return False

    def _apply_evolution(self, agent_suggestion: str, current_policy: dict):
        # Extract YAML part (naive extraction for prototype)
        try:
            import re
            name_match = re.search(r'Specialized Role Name: "(.*?)"', agent_suggestion)
            yaml_match = re.search(r'YAML:\n(.*?)(?:\n\n|$)', agent_suggestion, re.DOTALL)
            
            if name_match and yaml_match:
                role_name = name_match.group(1)
                role_yaml_str = yaml_match.group(1)
                role_data = yaml.safe_load(role_yaml_str)
                
                # Update policy
                current_policy["agents"][role_name] = role_data
                
                with open(self.policy_path, "w", encoding="utf-8") as f:
                    yaml.dump(current_policy, f, sort_keys=False)
                
                self.console.print(f"✨ [bold green]Framework Evolved:[/bold green] Added '{role_name}' to RBAC policies.")
        except Exception as e:
            self.console.print(f"❌ [red]Failed to apply evolution: {str(e)}[/red]")
