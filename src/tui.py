import sys
import subprocess
import itertools
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, RichLog, Static, Button, Input, DataTable, Label
from textual.binding import Binding
from textual import work

# Ensure src/ is on the path so session imports resolve
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session.session_store import SessionStore, SessionMeta
from session.checkpoint_manager import CheckpointManager

LOADING_MESSAGES = [
    "Aligning neural context...",
    "Injecting Cognitive RBAC constraints...",
    "Awaiting local Qwen inference...",
    "Synthesizing architectural boundaries...",
    "Computing deterministic gates...",
    "Cross-referencing output with AGENTS.md...",
]


class SessionBrowser(Vertical):
    """
    Left-panel session history browser.

    Shows a DataTable of recent sessions with status, progress, and the
    last completed phase.  Pressing [R] on a highlighted row fires an
    on_session_selected event that the parent app handles to populate
    the live log pane with resume information.
    """

    DEFAULT_CSS = """
    SessionBrowser {
        width: 100%;
        height: 1fr;
        border: solid cyan;
        padding: 1;
    }
    SessionBrowser DataTable {
        height: 1fr;
    }
    SessionBrowser Label {
        color: $text-muted;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("r", "resume_selected", "Resume selected session", show=True),
    ]

    def __init__(self, ss: SessionStore):
        super().__init__()
        self.ss = ss
        self._sessions: list[SessionMeta] = []

    def compose(self) -> ComposeResult:
        yield Label("📋 Session History  [R] Resume")
        yield DataTable(id="session-table", cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one("#session-table", DataTable)
        table.add_columns("Status", "Run ID", "Project", "Progress", "Last Phase")
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        table = self.query_one("#session-table", DataTable)
        table.clear()
        self._sessions = self.ss.list_all(limit=20)
        for m in self._sessions:
            progress = f"{m.progress_pct}% ({len(m.completed_phases)}/{m.total_phases})"
            table.add_row(
                f"{m.status_emoji} {m.status}",
                m.run_id,
                m.project_name,
                progress,
                m.last_phase_completed or "—",
            )

    def action_resume_selected(self) -> None:
        table = self.query_one("#session-table", DataTable)
        idx = table.cursor_row
        if 0 <= idx < len(self._sessions):
            selected = self._sessions[idx]
            self.post_message(self.SessionSelected(selected))

    class SessionSelected(Static.Changed):
        """Posted when the user picks a session to resume."""
        def __init__(self, session: SessionMeta) -> None:
            super().__init__(None, None)  # type: ignore[arg-type]
            self.session = session


class ControlPlaneDashboard(App):
    """
    Textual app to monitor the Agentic SDLC Orchestrator in real-time.

    Layout:
    ┌──────────────────┬────────────────────────────────────┐
    │ Pipeline status  │                                    │
    │ + loading msg    │      Live log stream               │
    │──────────────────│                                    │
    │ Session browser  │      Feedback input (bottom)       │
    └──────────────────┴────────────────────────────────────┘
    """

    CSS = """
    #left-pane {
        width: 32%;
        border-right: solid cyan;
    }
    #pipeline-box {
        height: auto;
        padding: 1;
        border-bottom: solid dim;
    }
    #loading-box {
        height: auto;
        padding: 0 1;
        border-bottom: solid dim;
    }
    #right-pane {
        width: 68%;
    }
    RichLog {
        height: 1fr;
    }
    #input-container {
        height: auto;
        dock: bottom;
    }
    #resume-banner {
        height: auto;
        padding: 0 1;
        background: $warning;
        display: none;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("s", "toggle_session_browser", "Toggle Sessions", show=True),
    ]

    def __init__(self, objective: str, resume_run_id: str | None = None):
        super().__init__()
        self.objective = objective
        self.resume_run_id = resume_run_id
        self.process = None
        self.ss = SessionStore()

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

        # Mark already-completed phases if resuming
        if resume_run_id:
            cm = CheckpointManager.for_existing_run(resume_run_id)
            if cm:
                done = set(cm.get_completed_phases())
                self.phases = [
                    (name, "complete" if name in done else "pending")
                    for name, _ in self.phases
                ]

        self.is_pipeline_running = False
        self.message_iterator = itertools.cycle(LOADING_MESSAGES)

    def compose(self) -> ComposeResult:
        yield Header("🔍 ASD Orchestrator — Live Control Plane")

        with Horizontal():
            with Vertical(id="left-pane"):
                with Vertical(id="pipeline-box"):
                    yield Static(
                        f"[bold cyan]Objective:[/bold cyan]\n{self.objective[:80]}\n",
                        id="objective-box",
                    )
                    yield Static(self._render_phases(), id="sidebar-status")

                yield Static("\n[dim]Initializing system...[/dim]", id="loading-box")
                yield SessionBrowser(self.ss)

            with Vertical(id="right-pane"):
                yield Static(id="resume-banner")
                yield RichLog(id="console-log", highlight=True, markup=True)
                with Horizontal(id="input-container"):
                    yield Input(
                        placeholder="Send manual feedback to the agent (if halted)...",
                        id="feedback-input",
                    )
                    yield Button("Send", id="send-feedback", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#console-log", RichLog)
        self.sidebar = self.query_one("#sidebar-status", Static)
        self.loading_box = self.query_one("#loading-box", Static)

        if self.resume_run_id:
            banner = self.query_one("#resume-banner", Static)
            banner.styles.display = "block"
            banner.update(
                f"⏩ [bold]RESUME MODE[/bold]  Run ID: [cyan]{self.resume_run_id}[/cyan]"
            )
            self.log_widget.write(
                f"[bold yellow]Resuming run: {self.resume_run_id}[/bold yellow]"
            )

        self.log_widget.write("[dim]Starting Agentic Orchestrator v3.0...[/dim]")

        self.set_interval(3.0, self._update_loading_message)
        self.set_interval(30.0, self._refresh_session_browser)

        self.run_pipeline()

    def _render_phases(self) -> str:
        lines = ["[bold magenta]Pipeline Topology:[/bold magenta]\n"]
        for name, status in self.phases:
            if status == "pending":
                lines.append(f"[dim]○ {name}[/dim]")
            elif status == "running":
                lines.append(f"[bold yellow]⚡ {name} (Generating...)[/bold yellow]")
            elif status == "complete":
                lines.append(f"[bold green]✓ {name}[/bold green]")
        return "\n".join(lines)

    def _update_sidebar(self) -> None:
        self.sidebar.update(self._render_phases())

    def _update_loading_message(self) -> None:
        if self.is_pipeline_running:
            msg = next(self.message_iterator)
            self.loading_box.update(
                f"\n[bold cyan]🧠 Active Neural Task:[/bold cyan]\n[italic]{msg}[/italic]"
            )
        else:
            self.loading_box.update("\n[bold green]✨ AI Pipeline Resting[/bold green]")

    def _refresh_session_browser(self) -> None:
        """Periodically refresh the session list in the browser."""
        try:
            browser = self.query_one(SessionBrowser)
            browser.refresh_sessions()
        except Exception:
            pass

    def _set_phase_status(self, target_phase: str, status: str) -> None:
        for i, (name, _) in enumerate(self.phases):
            if name in target_phase:
                self.phases[i] = (name, status)

    def action_toggle_session_browser(self) -> None:
        browser = self.query_one(SessionBrowser)
        browser.visible = not browser.visible

    def on_session_browser_session_selected(
        self, event: SessionBrowser.SessionSelected
    ) -> None:
        """User selected a session from the browser — show resume hint."""
        m = event.session
        self.log_widget.write(
            f"\n[bold magenta]📋 Session Selected:[/bold magenta] {m.run_id}\n"
            f"  Status: {m.status_emoji} {m.status}\n"
            f"  Progress: {m.progress_pct}% ({len(m.completed_phases)}/{m.total_phases})\n"
            f"  Last phase: {m.last_phase_completed or '—'}\n\n"
            f"[dim]To resume in a new terminal:[/dim]\n"
            f"  [white]python src/orchestrator.py \"{m.objective}\" --resume {m.run_id}[/white]\n"
        )

    @work(exclusive=True, thread=True)
    def run_pipeline(self) -> None:
        self.is_pipeline_running = True
        script_dir = os.path.dirname(os.path.abspath(__file__))
        orchestrator_path = os.path.join(script_dir, "orchestrator.py")

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["FORCE_COLOR"] = "1"
        env["TUI_MODE"] = "1"

        python_exe = sys.executable

        cmd = [python_exe, orchestrator_path, self.objective]
        if self.resume_run_id:
            cmd += ["--resume", self.resume_run_id]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            encoding="utf-8",
        )

        for line in iter(self.process.stdout.readline, ""):
            if not line:
                break

            clean_line = line.strip()
            self.call_from_thread(self.log_widget.write, clean_line)

            # Detect checkpoint skips
            if "loaded from checkpoint (skipped)" in clean_line:
                self.call_from_thread(self._set_phase_status, clean_line, "complete")
                self.call_from_thread(self._update_sidebar)

            # Detect phase starts
            if "Initializing Phase" in clean_line:
                self.call_from_thread(self._set_phase_status, clean_line, "running")
                self.call_from_thread(self._update_sidebar)
                self.is_pipeline_running = True

            # Detect phase completions (live + checkpoint save)
            if ("completed!" in clean_line and "Phase" in clean_line) or (
                "Checkpoint saved" in clean_line
            ):
                self.call_from_thread(self._set_phase_status, clean_line, "complete")
                self.call_from_thread(self._update_sidebar)
                self.call_from_thread(self._refresh_session_browser)

            if "Gatekeeper Evaluating" in clean_line or "Gatekeeper AI" in clean_line:
                self.call_from_thread(
                    self.loading_box.update,
                    "\n[bold red]🛡️ Gatekeeper Evaluating...[/bold red]\n"
                    "[italic]Analyzing output against framework constraints...[/italic]",
                )

            if "Action Required" in clean_line:
                self.is_pipeline_running = False
                self.call_from_thread(
                    self.loading_box.update,
                    "\n[bold red]🚨 ACTION REQUIRED:[/bold red]\n"
                    "[italic]Pipeline paused. Waiting for human input below...[/italic]",
                )

            # Resume banner — remove once pipeline is clearly running
            if "RESUME MODE" in clean_line or "loaded from checkpoint" in clean_line:
                self.is_pipeline_running = True

        self.is_pipeline_running = False
        self.call_from_thread(
            self.loading_box.update,
            "\n[bold green]🏆 Execution Complete. Systems Secure.[/bold green]",
        )
        self.call_from_thread(self._refresh_session_browser)
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
            self.log_widget.write(
                f"\n[bold magenta]👨‍💻 Human Override >[/bold magenta] {text}\n"
            )
            try:
                self.process.stdin.write(text + "\n")
                self.process.stdin.flush()
                inp.value = ""
                self.is_pipeline_running = True
                self.loading_box.update("\n[dim]Processing override feedback...[/dim]")
            except Exception as e:
                self.log_widget.write(f"[red]Error sending input: {e}[/red]")
        else:
            self.log_widget.write("[red]Pipeline is not running or already finished.[/red]")


def main():
    objective = "Build a modern fullstack app"
    resume_run_id = None

    args = sys.argv[1:]
    if args:
        objective = args[0]
    if "--resume" in args:
        idx = args.index("--resume")
        if idx + 1 < len(args):
            resume_run_id = args[idx + 1]

    app = ControlPlaneDashboard(objective, resume_run_id=resume_run_id)
    app.run()


if __name__ == "__main__":
    main()
