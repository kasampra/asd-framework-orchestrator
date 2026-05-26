"""
CheckpointManager — Atomic phase-level checkpoint persistence.

Each completed phase writes a checkpoint to:
    .asd/checkpoints/<run_id>/<safe_phase_name>.json

Writes are atomic: data is written to a .tmp file first, then
renamed to the final path so a crash mid-write never corrupts a
checkpoint that was previously valid.
"""

import json
import os
import datetime
from pathlib import Path
from typing import Optional


CHECKPOINTS_DIR = Path(".asd/checkpoints")


class CheckpointManager:
    """
    Manages phase-level checkpoints for crash recovery and selective re-runs.

    Usage:
        cm = CheckpointManager(run_id="20260526_143022")
        cm.save("Phase 3 Backend", output_text, tokens=1200, duration=42.1, gate="PASS")

        cached = cm.load("Phase 3 Backend")
        if cached:
            output = cached["output"]
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.checkpoint_dir = CHECKPOINTS_DIR / run_id
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(
        self,
        phase_name: str,
        output: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_seconds: float = 0.0,
        gate_decision: Optional[str] = None,
        compression_tier: int = 0,
    ) -> Path:
        """
        Atomically persist a completed phase output to disk.

        Returns the path of the written checkpoint file.
        """
        payload = {
            "run_id": self.run_id,
            "phase_name": phase_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "output": output,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_seconds": duration_seconds,
            "gate_decision": gate_decision,
            "compression_tier": compression_tier,
        }

        target_path = self.checkpoint_dir / f"{self._safe(phase_name)}.json"
        tmp_path = target_path.with_suffix(".tmp")

        # Atomic write: write to .tmp, then replace (replace() is cross-platform atomic overwrite)
        tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_path.replace(target_path)

        return target_path

    def load(self, phase_name: str) -> Optional[dict]:
        """
        Load a checkpoint for the given phase.

        Returns the full checkpoint dict (including 'output') or None if not found.
        """
        path = self.checkpoint_dir / f"{self._safe(phase_name)}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def load_output(self, phase_name: str) -> Optional[str]:
        """Convenience wrapper — returns just the output string or None."""
        cp = self.load(phase_name)
        return cp["output"] if cp else None

    def get_completed_phases(self) -> list[str]:
        """Return a list of phase names that have valid checkpoints for this run."""
        completed = []
        for path in sorted(self.checkpoint_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                completed.append(data["phase_name"])
            except (json.JSONDecodeError, KeyError):
                continue
        return completed

    def invalidate(self, phase_name: str) -> bool:
        """
        Delete the checkpoint for a specific phase (used when forcing a re-run).

        Returns True if a checkpoint existed and was deleted.
        """
        path = self.checkpoint_dir / f"{self._safe(phase_name)}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def invalidate_from(self, phase_name: str, all_phases: list[str]) -> list[str]:
        """
        Delete checkpoints for phase_name and all subsequent phases in the pipeline.

        This ensures re-running a phase also cascades to downstream phases that
        depended on it.

        Returns the list of phase names whose checkpoints were deleted.
        """
        try:
            start_idx = all_phases.index(phase_name)
        except ValueError:
            return []

        invalidated = []
        for phase in all_phases[start_idx:]:
            if self.invalidate(phase):
                invalidated.append(phase)
        return invalidated

    def checkpoint_path(self, phase_name: str) -> Path:
        """Return the expected path for a phase checkpoint (may not exist)."""
        return self.checkpoint_dir / f"{self._safe(phase_name)}.json"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe(name: str) -> str:
        """Convert a phase name to a safe filename."""
        return name.lower().replace(" ", "_").replace("/", "_")

    @classmethod
    def for_existing_run(cls, run_id: str) -> Optional["CheckpointManager"]:
        """
        Factory: return a CheckpointManager for a prior run if its directory exists.
        Returns None if the run_id has no checkpoint data.
        """
        path = CHECKPOINTS_DIR / run_id
        if path.exists() and path.is_dir():
            return cls(run_id)
        return None

    @classmethod
    def list_all_run_ids(cls) -> list[str]:
        """Return all run IDs that have checkpoint directories, newest first."""
        if not CHECKPOINTS_DIR.exists():
            return []
        dirs = sorted(
            [d.name for d in CHECKPOINTS_DIR.iterdir() if d.is_dir()],
            reverse=True,
        )
        return dirs
