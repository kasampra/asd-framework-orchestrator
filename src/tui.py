import sys
import subprocess
import itertools
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, RichLog, Static, Button, Input
from textual import work

LOADING_MESSAGES = [
    "Aligning neural context...",
    "Injecting Cognitive RBAC constraints...",
    "Awaiting local Qwen inference...",
    "Synthesizing architectural boundaries...",
    "Computing deterministic gates...",
    "Cross-referencing output with AGENTS.md...",
]

class ControlPlaneDashboard(App):
    """A Textual App to monitor the Agentic SDLC Orchestrator in real-time."""

    CSS = """
    #left-pane {
        width: 30%;
        border-right: solid cyan;
        padding: 1;
    }
    #right-pane {
        width: 70%;
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
        
        self.phases = [
            ("Phase 1 Requirements", "pending"),
            ("Phase 2 Architecture", "pending"),
            ("Phase 3 Backend", "pending"),
            ("Phase 4 Frontend", "pending"),
            ("Phase 5 Infrastructure", "pending"),
            ("Phase 6 QA Testing", "pending"),
            ("Phase 7 Security", "pending"),
            ("Phase 8 Deployment", "pending"),
        ]
        
        self.current_loading_message = ""
        self.is_running = False
        self.message_iterator = itertools.cycle(LOADING_MESSAGES)

    def compose(self) -> ComposeResult:
        yield Header("🔍 ASD Orchestrator — Live Control Plane")
        
        with Horizontal():
            with Vertical(id="left-pane"):
                yield Static(f"[bold cyan]Objective:[/bold cyan]\n{self.objective}\n", id="objective-box")
                yield Static(self.render_phases(), id="sidebar-status")
                yield Static("\n[dim]Initializing system...[/dim]", id="loading-box")
                
            with Vertical(id="right-pane"):
                yield RichLog(id="console-log", highlight=True, markup=True)
                with Horizontal(id="input-container"):
                    yield Input(placeholder="Send manual feedback to the agent (if halted)...", id="feedback-input")
                    yield Button("Send", id="send-feedback", variant="primary")
                    
        yield Footer()

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#console-log", RichLog)
        self.sidebar = self.query_one("#sidebar-status", Static)
        self.loading_box = self.query_one("#loading-box", Static)
        
        self.log_widget.write("[dim]Starting Agentic Orchestrator v3.0 Sandbox...[/dim]")
        
        # Start rotating loading messages
        self.set_interval(3.0, self.update_loading_message)
        
        # Start the background pipeline
        self.run_pipeline()

    def render_phases(self) -> str:
        lines = ["[bold magenta]Pipeline Topology:[/bold magenta]\n"]
        for name, status in self.phases:
            if status == "pending":
                lines.append(f"[dim]○ {name}[/dim]")
            elif status == "running":
                lines.append(f"[bold yellow]⚡ {name} (Generating...)[/bold yellow]")
            elif status == "complete":
                lines.append(f"[bold green]✓ {name}[/bold green]")
        return "\n".join(lines)

    def update_sidebar(self):
        self.sidebar.update(self.render_phases())

    def update_loading_message(self):
        if self.is_running:
            msg = next(self.message_iterator)
            self.loading_box.update(f"\n[bold cyan]🧠 Active Neural Task:[/bold cyan]\n[italic]{msg}[/italic]")
        else:
            self.loading_box.update("\n[bold green]✨ AI Pipeline Resting[/bold green]")

    def set_phase_status(self, target_phase: str, status: str):
        for i, (name, _) in enumerate(self.phases):
            if name in target_phase:
                self.phases[i] = (name, status)

    @work(exclusive=True, thread=True)
    def run_pipeline(self) -> None:
        self.is_running = True
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        orchestrator_path = os.path.join(script_dir, "orchestrator.py")
        
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["FORCE_COLOR"] = "1"
        env["TUI_MODE"] = "1"
        
        python_exe = sys.executable

        self.process = subprocess.Popen(
            [python_exe, orchestrator_path, self.objective],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            encoding="utf-8"
        )

        for line in iter(self.process.stdout.readline, ""):
            if not line:
                break
            
            clean_line = line.strip()
            self.call_from_thread(self.log_widget.write, clean_line)
            
            # Identify phase starts
            if "Initializing Phase" in clean_line:
                # Mark specifically this phase as running
                self.call_from_thread(self.set_phase_status, clean_line, "running")
                self.call_from_thread(self.update_sidebar)
                self.is_running = True
                
            # Identify phase completions
            if "completed!" in clean_line and "Phase" in clean_line:
                self.call_from_thread(self.set_phase_status, clean_line, "complete")
                self.call_from_thread(self.update_sidebar)
                
            if "Gatekeeper Evaluating" in clean_line or "Gatekeeper AI" in clean_line:
                self.call_from_thread(self.loading_box.update, f"\n[bold red]🛡️ Gatekeeper Evaluating...[/bold red]\n[italic]Analyzing output against framework constraints...[/italic]")
                
            if "Action Required" in clean_line:
                self.is_running = False
                self.call_from_thread(self.loading_box.update, f"\n[bold red]🚨 ACTION REQUIRED:[/bold red]\n[italic]Pipeline paused. Waiting for human input below...[/italic]")

        self.is_running = False
        self.call_from_thread(self.loading_box.update, "\n[bold green]🏆 Execution Complete. Systems Secure.[/bold green]")
        self.process.stdout.close()
        self.process.wait()

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
            self.log_widget.write(f"\n[bold magenta]👨‍💻 Human Override >[/bold magenta] {text}\n")
            try:
                self.process.stdin.write(text + "\n")
                self.process.stdin.flush()
                inp.value = ""
                self.is_running = True
                self.loading_box.update("\n[dim]Processing override feedback...[/dim]")
            except Exception as e:
                self.log_widget.write(f"[red]Error sending input: {e}[/red]")
        else:
            self.log_widget.write("[red]Pipeline is not running or already finished.[/red]")

def main():
    objective = "Build a modern fullstack app"
    if len(sys.argv) > 1:
        objective = sys.argv[1]
    
    app = ControlPlaneDashboard(objective)
    app.run()

if __name__ == "__main__":
    main()
