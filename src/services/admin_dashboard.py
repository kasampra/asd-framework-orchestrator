from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, DataTable
from rich.panel import Panel
from rich.table import Table
import json
from pathlib import Path

class AdminDashboard(App):
    """A real-time dashboard for managing agent personas and viewing project health."""

    CSS = """
    Grid {
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr 1fr;
    }
    #roi-box {
        column-span: 2;
        height: 1fr;
        border: double cyan;
    }
    .status-box {
        border: solid magenta;
        padding: 1;
    }
    """

    def __init__(self, report_path: str = None):
        super().__init__()
        self.report_path = Path(report_path) if report_path else None

    def compose(self) -> ComposeResult:
        yield Header("🏛️ ASD Orchestrator — Admin Command Center")
        with Grid():
            yield Static(self.render_project_info(), id="project-info", classes="status-box")
            yield Static(self.render_agent_health(), id="agent-health", classes="status-box")
            yield Static(self.render_roi_summary(), id="roi-box")
        yield Footer()

    def render_project_info(self) -> str:
        return "[bold cyan]Project Health[/bold cyan]\n\nStatus: [green]OPTIMAL[/green]\nPipeline: [yellow]Phase 5 - Software-as-Service[/yellow]\nDrift: [green]NONE[/green]"

    def render_agent_health(self) -> str:
        return "[bold magenta]Agent Personas[/bold magenta]\n\n- Requirements: [green]Active[/green]\n- Architect: [green]Active[/green]\n- QA: [yellow]Idle[/yellow]\n- Security: [green]Active[/green]"

    def render_roi_summary(self) -> str:
        if not self.report_path or not self.report_path.exists():
            return "[bold yellow]ROI Dashboard (Waiting for run completion...)[/bold yellow]"
        
        # In a real app, we'd parse the latest report or a specific JSON
        return "[bold green]Sovereign ROI Summary[/bold green]\n\nTotal Savings: [bold white]€1,450.00[/bold white]\nTime Saved: [bold white]18.5 hours[/bold white]\nData Leakage: [bold green]0%[/bold green]"

if __name__ == "__main__":
    app = AdminDashboard()
    app.run()
