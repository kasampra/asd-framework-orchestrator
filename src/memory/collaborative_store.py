import json
import os
import subprocess
from pathlib import Path
from memory.baseline_store import BaselineStore

class CollaborativeStore:
    """Enables sharing and synchronizing project baselines across teams via Git."""

    def __init__(self, local_store: BaselineStore, central_repo_url: str = None):
        self.local_store = local_store
        self.central_repo_url = central_repo_url
        self.sync_dir = Path(".asd/central_baselines")
        self.sync_dir.mkdir(parents=True, exist_ok=True)

    def sync_from_central(self):
        """Pulls the latest team-wide baselines from a central repository."""
        if not self.central_repo_url:
            return False
            
        try:
            if not (self.sync_dir / ".git").exists():
                subprocess.run(["git", "clone", self.central_repo_url, str(self.sync_dir)], check=True)
            else:
                subprocess.run(["git", "-C", str(self.sync_dir), "pull"], check=True)
            
            # Merge central baselines into local catalog or use as references
            central_baseline_file = self.sync_dir / "team_baseline.json"
            if central_baseline_file.exists():
                # Logic to optionally overwrite or suggest updates
                return True
        except Exception:
            return False
        return False

    def export_baseline_to_team(self, project_name: str):
        """Exports the local project baseline to the team's central repository."""
        baseline = self.local_store.get_baseline()
        if not baseline or not (self.sync_dir / ".git").exists():
            return False

        target_file = self.sync_dir / f"{project_name}_baseline.json"
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(baseline, f, indent=4)
            
            subprocess.run(["git", "-C", str(self.sync_dir), "add", "."], check=True)
            subprocess.run(["git", "-C", str(self.sync_dir), "commit", "-m", f"Update baseline for {project_name}"], check=True)
            subprocess.run(["git", "-C", str(self.sync_dir), "push"], check=True)
            return True
        except Exception:
            return False

if __name__ == "__main__":
    # Mock usage
    ls = BaselineStore()
    cs = CollaborativeStore(ls, "https://github.com/example/team-baselines.git")
    print("Collaborative Store initialized.")
