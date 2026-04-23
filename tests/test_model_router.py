import unittest
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.model_router import ModelRouter

class TestModelRouter(unittest.TestCase):

    def setUp(self):
        # Set environment variables for testing
        os.environ["MODEL_REASONING"] = "test-reasoning"
        os.environ["MODEL_CODER"] = "test-coder"
        os.environ["MODEL_FAST"] = "test-fast"
        self.router = ModelRouter()

    def test_routing_logic(self):
        # 1. Coding Phase
        self.assertEqual(self.router.route("coding", "Phase 3 Backend"), "test-coder")
        
        # 2. Gate/Architecture
        self.assertEqual(self.router.route("gate", "Architecture Review"), "test-reasoning")
        
        # 3. Requirements/Fast
        self.assertEqual(self.router.route("summary", "Phase 1 Requirements"), "test-fast")

    def test_default_routing(self):
        # Unknown task should fallback to reasoning (or whatever default)
        self.assertEqual(self.router.route("unknown", "Some Random Phase"), "test-reasoning")

if __name__ == '__main__':
    unittest.main()
