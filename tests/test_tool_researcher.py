import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.tool_researcher import ToolResearcher

class TestToolResearcher(unittest.TestCase):

    @patch('core.tool_researcher.delegate_to_qwen_agent')
    @patch('services.web_researcher.WebResearcher.conduct_research')
    def test_discovery_logged_on_gap(self, mock_conduct_research, mock_delegate):
        # 1. Setup Mock for Tool Gap Analysis
        mock_delegate.side_effect = [
            {"output": '[TOOL_GAP_FOUND]\nCapability: "PostgreSQL Migration"\nSearch Query: "MCP server for postgresql migration github"'},
            {"output": "### Discovery: Postgres MCP\n- **Capability:** Migration\n- **Repository:** https://github.com/example/postgres-mcp"}
        ]
        
        # 2. Setup Mock for Web Research
        mock_conduct_research.return_value = {
            "success": True,
            "content": "Found repository: https://github.com/example/postgres-mcp"
        }
        
        console = MagicMock()
        researcher = ToolResearcher(console)
        researcher.log_path = Path("tests/logs/tool_discoveries.md")
        researcher.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if researcher.log_path.exists():
            researcher.log_path.unlink()
            
        # 3. Run analysis
        result = researcher.analyze_and_discover("Add database migration support", ["bash"])
        
        # 4. Assertions
        self.assertTrue(result)
        self.assertTrue(researcher.log_path.exists())
        mock_conduct_research.assert_called_once()
        self.assertEqual(mock_delegate.call_count, 2)

if __name__ == '__main__':
    unittest.main()
