import os
import yaml
import subprocess
from pathlib import Path
from mcp_server import delegate_to_qwen_agent

class SkillResearcher:
    """Analyzes requirements to identify and implement missing agent skills."""
    
    def __init__(self, console, policy_path=".asd/policies/agent_rbac.yaml", repo_path="."):
        self.console = console
        self.policy_path = Path(policy_path)
        self.repo_path = Path(repo_path)

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
        2. If a gap is found, provide a search query to find the industry-best agentic patterns for this specific need.
        
        Output Format:
        [GAP_FOUND]
        Reason: "Reason why a new role is needed"
        Search Query: "A precise search query for agentic patterns"
        
        If no gap is found, respond with [NO_GAP].
        """
        
        result = delegate_to_qwen_agent("Skill Gap Analysis", analysis_prompt, "")
        analysis_output = result.get("output", "")
        
        if "[GAP_FOUND]" in analysis_output:
            import re
            query_match = re.search(r'Search Query: "(.*?)"', analysis_output)
            if query_match:
                search_query = query_match.group(1)
                self.console.print(f"🔍 [bold yellow]Intelligence Gap Found. Researching:[/bold yellow] {search_query}")
                
                # 3. Conduct Web Research
                from services.web_researcher import WebResearcher
                web_res = WebResearcher()
                research_res = web_res.conduct_research(search_query, model="mini")
                
                if research_res["success"]:
                    self.console.print("🚀 [bold green]Research complete! Evolving framework with industry patterns...[/bold green]")
                    return self._implement_evolution_with_research(research_res["content"], current_policy)
                else:
                    self.console.print(f"⚠️ [yellow]Research failed: {research_res.get('error')}. Falling back to internal reasoning.[/yellow]")
            
            return self._apply_evolution(analysis_output, current_policy)
        else:
            self.console.print("✅ [dim]No skill gaps identified for this project stack.[/dim]")
            return False

    def _implement_evolution_with_research(self, research_content: str, current_policy: dict):
        evolution_prompt = f"""
        You are a Sovereign AI Architect. You have discovered new industry patterns for an agentic skill gap.
        
        RESEARCH DATA:
        {research_content}
        
        TASK:
        Based on the research, define a new 'Specialized Agent' role in YAML format that implements these best practices.
        
        Output Format:
        Specialized Role Name: "Role Name"
        YAML:
        identity: "Detailed persona describing their expertise based on research"
        allowed_tools: ["delegate_to_qwen_agent", "execute_bash_command"]
        alignment: ["List of specific architectural constraints or patterns found in research"]
        """
        
        result = delegate_to_qwen_agent("Framework Evolution", evolution_prompt, "")
        return self._apply_evolution(result.get("output", ""), current_policy)

    def _apply_evolution(self, agent_suggestion: str, current_policy: dict):
        try:
            import re
            name_match = re.search(r'Specialized Role Name: "(.*?)"', agent_suggestion)
            yaml_match = re.search(r'YAML:\n(.*?)(?:\n\n|$)', agent_suggestion, re.DOTALL)
            
            if name_match and yaml_match:
                role_name = name_match.group(1)
                role_yaml_str = yaml_match.group(1)
                role_data = yaml.safe_load(role_yaml_str)
                
                # --- NEW: Autonomous Benchmarking ---
                from core.benchmarking_arena import BenchmarkingArena
                arena = BenchmarkingArena(self.console)
                if not arena.run_smoke_test(role_name, role_data):
                    self.console.print(f"🛑 [bold red]Evolution Aborted:[/bold red] Role '{role_name}' failed benchmarking. Scrapping evolution.")
                    return False
                # ------------------------------------
                
                # 1. Create a new feature branch for the evolution
                safe_role_name = role_name.lower().replace(" ", "-").replace(".", "-")
                branch_name = f"evolution/add-{safe_role_name}"
                
                self.console.print(f"🌿 [dim]Creating new branch: {branch_name}[/dim]")
                subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.repo_path, capture_output=True)
                
                # 2. Update policy
                current_policy["agents"][role_name] = role_data
                
                with open(self.policy_path, "w", encoding="utf-8") as f:
                    yaml.dump(current_policy, f, sort_keys=False)
                
                # 3. Commit the evolution
                self.console.print(f"📝 [dim]Committing framework evolution...[/dim]")
                subprocess.run(["git", "add", str(self.policy_path)], cwd=self.repo_path, capture_output=True)
                subprocess.run(["git", "commit", "-m", f"evolve: autonomously add {role_name} capability"], cwd=self.repo_path, capture_output=True)
                
                self.console.print(f"✨ [bold green]Framework Evolved:[/bold green] Added '{role_name}' in branch [cyan]{branch_name}[/cyan].")
                return True
        except Exception as e:
            self.console.print(f"❌ [red]Failed to apply evolution: {str(e)}[/red]")
            return False
        return False
