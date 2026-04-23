import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.pattern_catalog import PatternCatalog
from core.skill_researcher import SkillResearcher

class TestPatternCatalog(unittest.TestCase):

    def setUp(self):
        self.test_catalog_path = Path("tests/patterns/test_catalog.json")
        if self.test_catalog_path.exists():
            self.test_catalog_path.unlink()
        self.catalog = PatternCatalog(catalog_path=self.test_catalog_path)

    def test_add_and_search(self):
        self.catalog.add_pattern("Test Pattern", "Description", ["tag1"], "Content")
        results = self.catalog.search_patterns("Test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Test Pattern")

    @patch('core.skill_researcher.delegate_to_qwen_agent')
    @patch('core.skill_researcher.PatternCatalog.get_all_summaries')
    @patch('core.skill_researcher.PatternCatalog.search_patterns')
    def test_researcher_uses_existing_pattern(self, mock_search, mock_summaries, mock_delegate):
        # 1. Setup mocks
        mock_summaries.return_value = "- Existing Pattern (pat_123): A great pattern."
        mock_search.return_value = [{"name": "Existing Pattern", "content": "Verified Pattern Content"}]
        
        # Skill Gap Analysis output suggesting the known pattern
        mock_delegate.side_effect = [
            {"output": '[GAP_FOUND]\nReason: "Need existing pattern"\nUse Known Pattern: "Existing Pattern"\nSearch Query: "None"'},
            {"output": 'Specialized Role Name: "Pattern Agent"\nYAML:\nidentity: "Expert"\nallowed_tools: []\nalignment: []'}
        ]
        
        console = MagicMock()
        # Mock policy file
        with patch('builtins.open', unittest.mock.mock_open(read_data="agents: {}")):
            with patch('yaml.safe_load', return_value={"agents": {}}):
                researcher = SkillResearcher(console, policy_path="dummy.yaml")
                researcher.catalog = self.catalog
                researcher._apply_evolution = MagicMock(return_value=True)
                
                # 2. Run
                result = researcher.analyze_and_evolve("Requirements")
                
                # 3. Assertions
                self.assertTrue(result)
                # Should not have called web researcher (if we had a mock for it, it should be 0)
                mock_search.assert_called_with("Existing Pattern")
                self.assertEqual(mock_delegate.call_count, 2)

if __name__ == '__main__':
    unittest.main()
