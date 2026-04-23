import os
from pathlib import Path
from rich.console import Console
from mcp_server import delegate_to_qwen_agent

class ContentAgent:
    """Automates the creation of high-value social content from technical logs."""

    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.log_path = Path("logs/content_nuggets.md")
        self.log_path.parent.mkdir(exist_ok=True)

    def generate_nuggets(self, control_plane_path: str):
        self.console.print("✍️  [bold magenta]Starting Knowledge Nugget Factory...[/bold magenta]")
        
        path = Path(control_plane_path)
        if not path.exists():
            self.console.print(f"⚠️ [yellow]Control plane log not found at {control_plane_path}. Cannot generate content.[/yellow]")
            return False

        log_content = path.read_text(encoding="utf-8")
        
        # 1. Extract Insights
        self.console.print("  🔍 [dim]Distilling technical breakthroughs from logs...[/dim]")
        extraction_prompt = f"""
        You are a Sovereign AI Content Strategist. Review the following Control Plane report from an Agentic SDLC run.
        
        REPORT:
        {log_content[:15000]} # Truncated if too long
        
        TASK:
        Identify the top 3 technical breakthroughs, interesting agentic decisions, or "sovereign wins" (e.g., efficient compression, autonomous healing).
        
        For each, generate:
        1. A catchy headline.
        2. A "Sovereign Insight" (why this matters for data-sensitive businesses).
        3. A draft LinkedIn post (professional, authoritative, bold).
        4. A draft Substack snippet (deep-dive technical context).
        
        Output Format (Markdown):
        ### Nugget: [Headline]
        - **Sovereign Insight:** [Why it matters]
        - **LinkedIn Post:** [Draft]
        - **Substack Snippet:** [Draft]
        """
        
        result = delegate_to_qwen_agent("Content Generation", extraction_prompt, "")
        nuggets_md = result.get("output", "")
        
        # 2. Save to Logs
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"## Run ID: {datetime_now_str()} - Content Nuggets\n")
            f.write(nuggets_md)
            f.write("\n\n---\n\n")
            
        self.console.print(f"✨ [bold green]Content Nuggets generated![/bold green] Check [cyan]{self.log_path}[/cyan]")
        return True

def datetime_now_str():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    # Test with a dummy or existing log
    agent = ContentAgent()
    agent.generate_nuggets("logs/control_plane.md")
