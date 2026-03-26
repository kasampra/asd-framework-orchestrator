import sys
import subprocess
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, RichLog, Static, Button, Input
from textual import work
from textual.worker import WorkerState

class ControlPlaneDashboard(App):
    """A Textual App to monitor the Agentic SDLC Orchestrator in real-time."""

    CSS = """
    #left-pane {
        width: 25%;
        border-right: solid cyan;
    }
    #right-pane {
        width: 75%;
    }
    RichLog {
        height: 1fr;
    }
    #input-container {
        height: auto;
        dock: bottom;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit Dashboard"),
        ("ctrl+c", "quit", "Quit Dashboard"),
    ]

    def __init__(self, objective: str):
        super().__init__()
        self.objective = objective
        self.process = None

    def compose(self) -> ComposeResult:
        yield Header("🔍 ASD Orchestrator — Live Control Plane")
        
        with Horizontal():
            with Vertical(id="left-pane"):
                yield Static(f"[bold cyan]Objective:[/bold cyan]\n{self.objective}\n\n[bold yellow]Pipeline Status:[/bold yellow]\n⏳ Waiting for engine...", id="sidebar-status", classes="box")
                
            with Vertical(id="right-pane"):
                yield RichLog(id="console-log", highlight=True, markup=True)
                with Horizontal(id="input-container"):
                    yield Input(placeholder="Send manual feedback to the agent (if halted)...", id="feedback-input")
                    yield Button("Send", id="send-feedback", variant="primary")
                    
        yield Footer()

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#console-log", RichLog)
        self.sidebar = self.query_one("#sidebar-status", Static)
        
        self.log_widget.write("[dim]Starting Agentic Orchestrator v2.0 Sandbox...[/dim]")
        
        # Start the background pipeline
        self.run_pipeline()

    @work(exclusive=True, thread=True)
    def run_pipeline(self) -> None:
        """Runs the orchestrator as a subprocess and streams output to to the RichLog."""
        import os
        orchestrator_path = os.path.join("src", "orchestrator.py")
        
        # Use unbuffered output to get it real-time
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        python_exe = sys.executable

        self.process = subprocess.Popen(
            [python_exe, orchestrator_path, self.objective],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

        for line in iter(self.process.stdout.readline, ""):
            if not line:
                break
            
            clean_line = line.strip()
            self.call_from_thread(self.log_widget.write, clean_line)
            
            # Simple heuristic to update the left sidebar based on phase
            if "Executing Phase" in clean_line or "Gatekeeper Evaluating" in clean_line:
                self.call_from_thread(self.update_sidebar, clean_line)
                
            if "Action Required" in clean_line:
                self.call_from_thread(self.update_sidebar, "[bold red]ACTION REQUIRED:[/bold red]\nWaiting for human input...")

        self.process.stdout.close()
        self.process.wait()

    def update_sidebar(self, status: str):
        # Clean rich formatting tags if present loosely
        sidebar_text = f"[bold cyan]Objective:[/bold cyan]\n{self.objective}\n\n[bold yellow]Current Stage:[/bold yellow]\n{status}"
        self.sidebar.update(sidebar_text)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-feedback":
            await self.send_input()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "feedback-input":
            await self.send_input()

    async def send_input(self) -> None:
        inp = self.query_one("#feedback-input", Input)
        text = inp.value
        
        if self.process and self.process.poll() is None:
            self.log_widget.write(f"[bold magenta]Human >[/bold magenta] {text}")
            try:
                # Write to the subprocess stdin
                self.process.stdin.write(text + "\n")
                self.process.stdin.flush()
                inp.value = ""
                self.update_sidebar("[dim]Processing feedback...[/dim]")
            except Exception as e:
                self.log_widget.write(f"[red]Error sending input: {e}[/red]")
        else:
            self.log_widget.write("[red]Pipeline is not running or already finished.[/red]")

def main():
    import sys
    objective = "Build a modern fullstack app"
    if len(sys.argv) > 1:
        objective = sys.argv[1]
    
    app = ControlPlaneDashboard(objective)
    app.run()

if __name__ == "__main__":
    main()
