import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from memory.collaborative_store import CollaborativeStore

class TestCollaborativeStore(unittest.TestCase):

    def setUp(self):
        self.mock_local_store = MagicMock()
        self.cs = CollaborativeStore(self.mock_local_store, "https://github.com/test/repo.git")

    @patch('subprocess.run')
    def test_sync_pulls_if_exists(self, mock_run):
        # 1. Simulate existing git repo
        (self.cs.sync_dir / ".git").mkdir(parents=True, exist_ok=True)
        
        # 2. Run sync
        self.cs.sync_from_central()
        
        # 3. Assertions
        mock_run.assert_called_with(["git", "-C", str(self.cs.sync_dir), "pull"], check=True)

    @patch('subprocess.run')
    def test_export_baseline(self, mock_run):
        # 1. Setup mock baseline
        self.mock_local_store.get_baseline.return_value = {"id": "baseline_1"}
        (self.cs.sync_dir / ".git").mkdir(parents=True, exist_ok=True)
        
        # 2. Run export
        with patch('builtins.open', unittest.mock.mock_open()):
            self.cs.export_baseline_to_team("test_project")
            
        # 3. Assertions
        mock_run.assert_any_call(["git", "-C", str(self.cs.sync_dir), "push"], check=True)

if __name__ == '__main__':
    unittest.main()
