import unittest
import os
import shutil
from src.self_healing import SelfHealer

class TestSelfHealer(unittest.TestCase):
    def setUp(self):
        self.test_trace_dir = "test_traces"
        self.healer = SelfHealer(trace_dir=self.test_trace_dir)

    def tearDown(self):
        if os.path.exists(self.test_trace_dir):
            shutil.rmtree(self.test_trace_dir)

    def test_monitor_failure(self):
        failure = {"exit_code": 1, "output": "error message"}
        monitored = self.healer.monitor(failure)
        self.assertIsNotNone(monitored)
        self.assertEqual(monitored["error_output"], "error message")

    def test_monitor_success(self):
        success = {"exit_code": 0, "output": "success"}
        monitored = self.healer.monitor(success)
        self.assertIsNone(monitored)

    def test_diagnosis_dependency(self):
        failure = {"error_output": "ModuleNotFoundError: No module named 'requests'"}
        diagnosis = self.healer.diagnose(failure)
        self.assertEqual(diagnosis["category"], "INFRA/DEPENDENCY")

    def test_diagnosis_syntax(self):
        failure = {"error_output": "SyntaxError: invalid syntax"}
        diagnosis = self.healer.diagnose(failure)
        self.assertEqual(diagnosis["category"], "LINT/SYNTAX")

    def test_trace_logging(self):
        data = {
            "timestamp": "2026-05-29T10:00:00",
            "diagnosis": {"category": "TEST/CAT"},
            "plan": {"strategy": "TEST/STRAT"}
        }
        self.healer.log_trace(data)
        
        # Check for JSON trace
        json_traces = [f for f in os.listdir(self.test_trace_dir) if f.endswith(".json")]
        self.assertEqual(len(json_traces), 1)
        self.assertTrue(json_traces[0].startswith("healing_"))
        
        # Check for history log
        self.assertTrue(os.path.exists(os.path.join(self.test_trace_dir, "healing_history.log")))

if __name__ == "__main__":
    unittest.main()
