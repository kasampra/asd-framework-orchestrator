import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.benchmarking_arena import BenchmarkingArena

class TestBenchmarkingArena(unittest.TestCase):

    @patch('core.benchmarking_arena.delegate_to_qwen_agent')
    @patch('core.benchmarking_arena.evaluate_quality_gate')
    def test_smoke_test_pass(self, mock_gate, mock_delegate):
        # Setup mocks
        mock_delegate.return_value = {"output": "def calculate_roi(i, r): return (r-i)/i * 100"}
        mock_gate.return_value = {"decision": "PASS", "reasoning": "Correct implementation."}
        
        console = MagicMock()
        arena = BenchmarkingArena(console)
        
        role_data = {"identity": "Test", "alignment": []}
        result = arena.run_smoke_test("Test Role", role_data)
        
        self.assertTrue(result)
        mock_delegate.assert_called_once()
        mock_gate.assert_called_once()

    @patch('core.benchmarking_arena.delegate_to_qwen_agent')
    @patch('core.benchmarking_arena.evaluate_quality_gate')
    def test_smoke_test_fail(self, mock_gate, mock_delegate):
        # Setup mocks
        mock_delegate.return_value = {"output": "broken code"}
        mock_gate.return_value = {"decision": "FAIL", "reasoning": "Output is not valid Python."}
        
        console = MagicMock()
        arena = BenchmarkingArena(console)
        
        role_data = {"identity": "Test", "alignment": []}
        result = arena.run_smoke_test("Test Role", role_data)
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
