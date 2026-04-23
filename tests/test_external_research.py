import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.skill_researcher import SkillResearcher

class TestExternalResearch(unittest.TestCase):

    @patch('core.skill_researcher.delegate_to_qwen_agent')
    @patch('services.web_researcher.WebResearcher.conduct_research')
    def test_research_triggered_on_gap(self, mock_conduct_research, mock_delegate):
        # 1. Setup Mock for Gap Analysis
        mock_delegate.side_effect = [
            {"output": '[GAP_FOUND]\nReason: "Need deep expertise in Kubernetes orchestration"\nSearch Query: "agentic patterns for autonomous kubernetes management"'},
            {"output": 'Specialized Role Name: "K8s Architect"\nYAML:\nidentity: "K8s Expert"\nallowed_tools: ["bash"]\nalignment: ["scale"]'}
        ]
        
        # 2. Setup Mock for Web Research
        mock_conduct_research.return_value = {
            "success": True,
            "content": "Found patterns: Pattern A, Pattern B for K8s."
        }
        
        # 3. Initialize SkillResearcher with dummy paths
        console = MagicMock()
        # Mocking policy file existence and content
        with patch('builtins.open', unittest.mock.mock_open(read_data="agents: {}")):
            with patch('yaml.safe_load', return_value={"agents": {}}):
                researcher = SkillResearcher(console, policy_path="dummy.yaml")
                
                # We need to mock _apply_evolution to avoid side effects like git commands
                researcher._apply_evolution = MagicMock(return_value=True)
                
                # 4. Run analysis
                result = researcher.analyze_and_evolve("Build a production K8s cluster")
                
                # 5. Assertions
                self.assertTrue(result)
                mock_conduct_research.assert_called_once_with("agentic patterns for autonomous kubernetes management", model="mini")
                self.assertEqual(mock_delegate.call_count, 2)
                
    @patch('core.skill_researcher.delegate_to_qwen_agent')
    def test_no_research_on_no_gap(self, mock_delegate):
        mock_delegate.return_value = {"output": "[NO_GAP]"}
        
        console = MagicMock()
        with patch('builtins.open', unittest.mock.mock_open(read_data="agents: {}")):
            with patch('yaml.safe_load', return_value={"agents": {}}):
                researcher = SkillResearcher(console, policy_path="dummy.yaml")
                result = researcher.analyze_and_evolve("Build a simple calculator")
                
                self.assertFalse(result)
                mock_delegate.assert_called_once()

if __name__ == '__main__':
    unittest.main()
