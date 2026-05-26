"""
SessionStore — Project session registry.

Maintains a single `sessions.json` index in `.asd/` that records metadata
for every orchestrator run. This is the source of truth for:
  - `--list-sessions`
  - The TUI session browser
  - Resolving `--resume <run_id>` to a full session record
"""

import json
import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

SESSIONS_INDEX_PATH = Path(".asd/sessions.json")


@dataclass
class SessionMeta:
    """Metadata record for a single orchestrator run."""

    run_id: str
    project_name: str
    objective: str
    status: str                     # "running" | "complete" | "failed" | "partial"
    created_at: str
    updated_at: str
    last_phase_completed: str = ""
    completed_phases: list = field(default_factory=list)
    total_phases: int = 8
    gate_results: dict = field(default_factory=dict)   # {gate_name: "PASS"|"FAIL"}
    total_tokens: int = 0
    total_duration_seconds: float = 0.0

    @property
    def progress_pct(self) -> int:
        """Return integer percentage of pipeline completion."""
        if self.total_phases == 0:
            return 0
        return min(100, int(len(self.completed_phases) / self.total_phases * 100))

    @property
    def status_emoji(self) -> str:
        return {
            "running": "⚡",
            "complete": "✅",
            "failed": "❌",
            "partial": "⏸️",
        }.get(self.status, "❓")


class SessionStore:
    """
    CRUD store for session metadata.

    All writes are atomic (write to .tmp, rename) so the index is never
    left in a corrupt state if the process is killed mid-write.
    """

    def __init__(self, index_path: Path = SESSIONS_INDEX_PATH):
        self.index_path = index_path
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, run_id: str, project_name: str, objective: str) -> SessionMeta:
        """Register a brand-new session and persist it to the index."""
        now = datetime.datetime.now().isoformat()
        meta = SessionMeta(
            run_id=run_id,
            project_name=project_name,
            objective=objective,
            status="running",
            created_at=now,
            updated_at=now,
        )
        sessions = self._load_all()
        sessions[run_id] = asdict(meta)
        self._save_all(sessions)
        return meta

    def get(self, run_id: str) -> Optional[SessionMeta]:
        """Return a SessionMeta for the given run_id, or None if not found."""
        sessions = self._load_all()
        raw = sessions.get(run_id)
        if raw is None:
            return None
        return self._from_dict(raw)

    def update_phase_complete(
        self,
        run_id: str,
        phase_name: str,
        tokens: int = 0,
        duration: float = 0.0,
    ) -> Optional[SessionMeta]:
        """
        Mark a phase as completed and update aggregate metrics.
        Called immediately after CheckpointManager.save().
        """
        sessions = self._load_all()
        raw = sessions.get(run_id)
        if raw is None:
            return None

        if phase_name not in raw.get("completed_phases", []):
            raw.setdefault("completed_phases", []).append(phase_name)
        raw["last_phase_completed"] = phase_name
        raw["total_tokens"] = raw.get("total_tokens", 0) + tokens
        raw["total_duration_seconds"] = raw.get("total_duration_seconds", 0.0) + duration
        raw["updated_at"] = datetime.datetime.now().isoformat()
        raw["status"] = "running"

        sessions[run_id] = raw
        self._save_all(sessions)
        return self._from_dict(raw)

    def record_gate(self, run_id: str, gate_name: str, decision: str) -> None:
        """Store a gate PASS/FAIL outcome in the session record."""
        sessions = self._load_all()
        raw = sessions.get(run_id)
        if raw is None:
            return
        raw.setdefault("gate_results", {})[gate_name] = decision
        raw["updated_at"] = datetime.datetime.now().isoformat()
        sessions[run_id] = raw
        self._save_all(sessions)

    def mark_complete(self, run_id: str) -> None:
        """Mark the pipeline as fully complete."""
        self._set_status(run_id, "complete")

    def mark_failed(self, run_id: str) -> None:
        """Mark the pipeline as failed (crashed or gate-exhausted)."""
        self._set_status(run_id, "failed")

    def mark_partial(self, run_id: str) -> None:
        """Mark the pipeline as paused/partial (user aborted, can resume)."""
        self._set_status(run_id, "partial")

    def list_all(self, limit: int = 50) -> list[SessionMeta]:
        """Return all sessions, newest first, up to `limit`."""
        sessions = self._load_all()
        metas = [self._from_dict(v) for v in sessions.values()]
        metas.sort(key=lambda m: m.created_at, reverse=True)
        return metas[:limit]

    def list_resumable(self) -> list[SessionMeta]:
        """Return sessions that can be resumed (partial or failed)."""
        return [m for m in self.list_all() if m.status in ("partial", "failed", "running")]

    def find_latest_for_project(self, project_name: str) -> Optional[SessionMeta]:
        """Return the most recent session for a given project name."""
        matches = [m for m in self.list_all() if m.project_name == project_name]
        return matches[0] if matches else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_status(self, run_id: str, status: str) -> None:
        sessions = self._load_all()
        raw = sessions.get(run_id)
        if raw is None:
            return
        raw["status"] = status
        raw["updated_at"] = datetime.datetime.now().isoformat()
        sessions[run_id] = raw
        self._save_all(sessions)

    def _load_all(self) -> dict:
        if not self.index_path.exists():
            return {}
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_all(self, sessions: dict) -> None:
        tmp = self.index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.index_path)

    @staticmethod
    def _from_dict(raw: dict) -> SessionMeta:
        # Guard against missing keys from older format records
        return SessionMeta(
            run_id=raw.get("run_id", ""),
            project_name=raw.get("project_name", ""),
            objective=raw.get("objective", ""),
            status=raw.get("status", "unknown"),
            created_at=raw.get("created_at", ""),
            updated_at=raw.get("updated_at", ""),
            last_phase_completed=raw.get("last_phase_completed", ""),
            completed_phases=raw.get("completed_phases", []),
            total_phases=raw.get("total_phases", 8),
            gate_results=raw.get("gate_results", {}),
            total_tokens=raw.get("total_tokens", 0),
            total_duration_seconds=raw.get("total_duration_seconds", 0.0),
        )

    # ------------------------------------------------------------------
    # Pretty-print helper (used by --list-sessions)
    # ------------------------------------------------------------------

    def render_sessions_table(self, sessions: list[SessionMeta]) -> str:
        """Render a markdown table of sessions for CLI display."""
        if not sessions:
            return "_No sessions found._\n"

        rows = [
            "| # | Run ID | Project | Status | Progress | Last Phase | Tokens |",
            "|---|--------|---------|--------|----------|------------|--------|",
        ]
        for i, m in enumerate(sessions, 1):
            progress = f"{m.progress_pct}% ({len(m.completed_phases)}/{m.total_phases})"
            last = m.last_phase_completed or "—"
            rows.append(
                f"| {i} | `{m.run_id}` | {m.project_name} | "
                f"{m.status_emoji} {m.status} | {progress} | {last} | {m.total_tokens:,} |"
            )
        return "\n".join(rows) + "\n"
