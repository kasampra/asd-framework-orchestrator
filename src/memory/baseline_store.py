# src/memory/baseline_store.py
import json
from pathlib import Path
from .fingerprint_extractor import DecisionFingerprint

BASELINE_PATH = Path(".asd/fingerprints/baseline.json")
MAX_HISTORY = 50


class BaselineStore:

    def load_history(self) -> list[dict]:
        if not BASELINE_PATH.exists():
            return []
        try:
            with open(BASELINE_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save(self, fingerprint: DecisionFingerprint) -> None:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        history = self.load_history()
        history.append(fingerprint.model_dump())
        if len(history) > MAX_HISTORY + 1:
            history = [history[0]] + history[-(MAX_HISTORY):]
        with open(BASELINE_PATH, 'w') as f:
            json.dump(history, f, indent=2)

    def get_baseline(self) -> dict | None:
        history = self.load_history()
        return history[0] if history else None

    def promote_to_baseline(self, run_id: str) -> bool:
        history = self.load_history()
        for i, entry in enumerate(history):
            if entry.get("run_id") == run_id:
                history.insert(0, history.pop(i))
                with open(BASELINE_PATH, 'w') as f:
                    json.dump(history, f, indent=2)
                return True
        return False

    def get_history_count(self) -> int:
        return len(self.load_history())

    def is_empty(self) -> bool:
        return self.get_history_count() == 0
