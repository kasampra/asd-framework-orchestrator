import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from services.content_agent import ContentAgent

class TestContentAgent(unittest.TestCase):

    @patch('services.content_agent.delegate_to_qwen_agent')
    def test_nugget_generation(self, mock_delegate):
        # 1. Setup Mock for Content Generation
        mock_delegate.return_value = {
            "output": "### Nugget: Sovereign Compression\n- **Sovereign Insight:** Data stays local.\n- **LinkedIn Post:** Big news!\n- **Substack Snippet:** Deep dive here."
        }
        
        # 2. Setup a dummy control plane log
        log_path = Path("tests/logs/dummy_cp.md")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_content = "# Control Plane Report\nStep 1: Requirements\nStep 2: Architecture"
        log_path.write_text(log_content, encoding="utf-8")
        
        console = MagicMock()
        agent = ContentAgent(console)
        agent.log_path = Path("tests/logs/content_nuggets.md")
        
        if agent.log_path.exists():
            agent.log_path.unlink()
            
        # 3. Run
        result = agent.generate_nuggets(str(log_path))
        
        # 4. Assertions
        self.assertTrue(result)
        self.assertTrue(agent.log_path.exists())
        content = agent.log_path.read_text(encoding="utf-8")
        self.assertIn("Sovereign Compression", content)
        mock_delegate.assert_called_once()

if __name__ == '__main__':
    unittest.main()
