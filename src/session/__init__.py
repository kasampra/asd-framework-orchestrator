"""
Session management package for the ASD Framework Orchestrator.

Provides checkpoint persistence and session tracking so pipeline runs
can be resumed after crashes, and individual phases can be re-run
in isolation without restarting the full 8-phase waterfall.
"""

from .checkpoint_manager import CheckpointManager
from .session_store import SessionStore, SessionMeta

__all__ = ["CheckpointManager", "SessionStore", "SessionMeta"]
