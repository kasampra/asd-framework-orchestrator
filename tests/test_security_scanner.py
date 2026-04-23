import unittest
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from services.security_scanner import SecurityScanner

class TestSecurityScanner(unittest.TestCase):

    def setUp(self):
        self.scanner = SecurityScanner()

    def test_secret_scanning(self):
        # 1. Create a dummy file with a secret
        test_file = Path("tests/tmp/secrets.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("my_api_key = 'AKIA1234567890123456'", encoding="utf-8")
        
        # 2. Run scan
        findings = self.scanner.scan_for_secrets("tests/tmp")
        
        # 3. Assertions
        self.assertTrue(len(findings) > 0)
        self.assertEqual(findings[0]["type"], "AWS Access Key")

    def test_report_generation(self):
        sast = {"results": [{"issue_severity": "HIGH", "issue_text": "Hardcoded password", "filename": "app.py", "line_number": 10, "test_id": "B101"}]}
        secrets = [{"file": "config.yaml", "type": "Generic API Key", "line": 5}]
        
        report = self.scanner.generate_report(sast, secrets)
        
        self.assertIn("Hard Security Gate Report", report)
        self.assertIn("Bandit SAST Findings", report)
        self.assertIn("Hardcoded password", report)
        self.assertIn("Generic API Key", report)

if __name__ == '__main__':
    unittest.main()
