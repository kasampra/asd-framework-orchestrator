import unittest
from pathlib import Path
import os
import sys

# Add .asd to path
asd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.asd'))
sys.path.insert(0, asd_path)

from policy_validator import PolicyValidator

class TestCognitiveLocks(unittest.TestCase):

    def test_lock_violation_detected(self):
        # 1. Test objective with blocked keyword
        objective = "I need to delete database entries for the user."
        violations = PolicyValidator.check_lock_violation(objective)
        
        self.assertIn("delete database", violations)

    def test_no_violation_on_safe_objective(self):
        # 2. Test safe objective
        objective = "Build a simple calculator UI."
        violations = PolicyValidator.check_lock_violation(objective)
        
        self.assertEqual(len(violations), 0)

    def test_rm_rf_lock(self):
        objective = "Run rm -rf / in the container."
        violations = PolicyValidator.check_lock_violation(objective)
        self.assertIn("rm -rf /", violations)

if __name__ == '__main__':
    unittest.main()
