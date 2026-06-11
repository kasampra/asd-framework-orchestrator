import unittest
import os
import sys
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from model_router import ModelRouter
from services.security_scanner import SecurityScanner
from self_healing import SelfHealer
from mcp_server import execute_bash_command

class TestOrchestratorFixes(unittest.TestCase):

    def test_model_router(self):
        """Test ModelRouter routing based on task type."""
        # Set up env vars
        os.environ["MODEL_NAME"] = "full-qwen-model"
        os.environ["FAST_MODEL_NAME"] = "fast-qwen-model"
        
        router = ModelRouter()
        self.assertEqual(router.get_model("reflection"), "fast-qwen-model")
        self.assertEqual(router.get_model("content"), "fast-qwen-model")
        self.assertEqual(router.get_model("summary"), "fast-qwen-model")
        self.assertEqual(router.get_model("generation"), "full-qwen-model")
        self.assertEqual(router.get_model("gate"), "full-qwen-model")

        # Test fallback when FAST_MODEL_NAME is not set
        del os.environ["FAST_MODEL_NAME"]
        router_fallback = ModelRouter()
        self.assertEqual(router_fallback.get_model("reflection"), "full-qwen-model")

    def test_security_scanner_dynamic_resolution(self):
        """Test dynamic resolution of Bandit path in SecurityScanner."""
        scanner = SecurityScanner()
        # If bandit is not in PATH, bandit_path should be None
        with patch("shutil.which", return_value=None):
            scanner_no_bandit = SecurityScanner()
            self.assertIsNone(scanner_no_bandit.bandit_path)
            res = scanner_no_bandit.run_sast_scan(".")
            self.assertEqual(res["results"], [])
            self.assertIn("Bandit executable not found in PATH.", res["errors"])

        # If bandit is in PATH, bandit_path should be resolved
        with patch("shutil.which", return_value="/usr/local/bin/bandit"):
            scanner_with_bandit = SecurityScanner()
            self.assertEqual(scanner_with_bandit.bandit_path, "/usr/local/bin/bandit")

    def test_execute_bash_command_sandboxing(self):
        """Test sandbox and command whitelist controls in execute_bash_command."""
        # Test command whitelist rejection
        res = execute_bash_command("rm -rf /")
        self.assertIn("not in the allowed command whitelist", res)

        res = execute_bash_command("cat /etc/passwd")
        self.assertIn("not in the allowed command whitelist", res)

        # Test directory traversal escape rejection
        # WORKSPACE_BASE_DIR defaults to "."
        res = execute_bash_command("pytest", cwd="../../")
        self.assertIn("is outside the workspace", res)

        # Test safe command passing checks (e.g. invalid executable)
        with patch("shutil.which", return_value=None):
            res = execute_bash_command("pytest")
            self.assertIn("not found in PATH", res)

    def test_self_healing_infra_dependency(self):
        """Test self-healing for missing pip packages (INFRA/DEPENDENCY)."""
        healer = SelfHealer(trace_dir="test_traces")
        
        failure_context = {
            "error_output": "ModuleNotFoundError: No module named 'tavily'",
            "output": "",
            "phase": "Phase 6 QA Testing"
        }
        
        # Mock subprocess.run to prevent actual pip installs during tests
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Successfully installed"
            mock_run.return_value.stderr = ""
            
            res = healer.execute_heal({"strategy": "Install package"}, failure_context)
            self.assertIn("Successfully installed", res)
            mock_run.assert_called_once()
            self.assertIn("tavily", mock_run.call_args[0][0])

        if os.path.exists("test_traces"):
            shutil.rmtree("test_traces")

    def test_self_healing_lint_syntax(self):
        """Test self-healing for code syntax issues (LINT/SYNTAX)."""
        healer = SelfHealer(trace_dir="test_traces")
        
        failure_context = {
            "error_output": "SyntaxError: invalid syntax",
            "output": "print('hello'  # Missing closing paren",
            "phase": "Phase 3 Backend"
        }
        
        # Mock QwenClient generate_response
        with patch("qwen_client.QwenClient.generate_response") as mock_qwen:
            mock_qwen.return_value = {"output": "print('hello')"}
            
            res = healer.execute_heal({"strategy": "Fix syntax"}, failure_context)
            self.assertEqual(res, "print('hello')")
            mock_qwen.assert_called_once()

        if os.path.exists("test_traces"):
            shutil.rmtree("test_traces")

if __name__ == '__main__':
    unittest.main()
