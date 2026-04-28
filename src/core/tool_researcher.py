import re
import yaml
from pathlib import Path
from rich.console import Console
from mcp_server import delegate_to_qwen_agent
from services.web_researcher import WebResearcher

class ToolResearcher:
    """Specialized researcher for discovering and recommending MCP tools."""

    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.log_path = Path("logs/tool_discoveries.md")
        self.log_path.parent.mkdir(exist_ok=True)

    def analyze_and_discover(self, requirements: str, existing_tools: list):
        self.console.print("🛠️  [bold cyan]Starting MCP Tool Discovery...[/bold cyan]")
        
        # 1. Identify Technical Gaps
        discovery_prompt = f"""
        You are a Sovereign AI Systems Integrator. Review the project requirements and our current MCP toolkit.
        
        PROJECT REQUIREMENTS:
        {requirements}
        
        CURRENT TOOLS:
        {', '.join(existing_tools)}
        
        TASK:
        Identify a specific technical capability (e.g., "PostgreSQL introspection", "AWS Lambda management") 
        that would significantly accelerate this project but is NOT in our current toolkit.
        
        Provide a search query to find an MCP Server (Model Context Protocol) that provides this capability.
        
        Output Format:
        [TOOL_GAP_FOUND]
        Capability: "Capability name"
        Search Query: "A precise search query for an MCP server"
        
        If no tool gap is found, respond with [NO_TOOL_GAP].
        """
        
        result = delegate_to_qwen_agent("Tool Discovery", discovery_prompt, "")
        output = result.get("output", "")
        
        if "[TOOL_GAP_FOUND]" in output:
            query_match = re.search(r'Search Query: "(.*?)"', output)
            capability_match = re.search(r'Capability: "(.*?)"', output)
            
            if query_match and capability_match:
                search_query = query_match.group(1)
                capability = capability_match.group(1)
                
                self.console.print(f"🔍 [bold yellow]Discovery Goal:[/bold yellow] Finding MCP server for '{capability}'")
                
                # 2. Research MCP Ecosystem
                web_res = WebResearcher()
                research_res = web_res.conduct_research(f"MCP server for {search_query} GitHub", model="mini")
                
                if research_res["success"]:
                    self.console.print("🚀 [bold green]MCP Tool Found! Logging discovery...[/bold green]")
                    return self._log_discovery(capability, research_res["content"])
        
        self.console.print("✅ [dim]No new MCP tools needed for this specific stack.[/dim]")
        return False

    def _log_discovery(self, capability: str, research_content: str):
        report_prompt = f"""
        You are a Systems Integrator. You have researched an MCP server for: {capability}.
        
        RESEARCH DATA:
        {research_content}
        
        TASK:
        Summarize the discovery for the user. Identify the GitHub repository and how to install/configure it.
        
        Output Format (Markdown):
        ### Discovery: [Tool Name]
        - **Capability:** {capability}
        - **Repository:** [URL]
        - **Install Command:** `[command]`
        - **MCP Config Snippet:**
        ```json
        [config]
        ```
        """
        
        result = delegate_to_qwen_agent("Discovery Report", report_prompt, "")
        report_md = result.get("output", "")
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"## {capability} - Discovered {Path(__file__).parent}\n")
            f.write(report_md)
            f.write("\n\n---\n\n")
            
        self.console.print(f"✨ [bold green]New tool discovered![/bold green] Details logged to [cyan]{self.log_path}[/cyan]")
        return True

if __name__ == "__main__":
    arena = ToolResearcher()
    arena.analyze_and_discover("Build a secure database migration tool for PostgreSQL", ["bash", "qwen"])
