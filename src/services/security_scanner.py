import os
import subprocess
import json
import re
from pathlib import Path
from rich.console import Console

class SecurityScanner:
    """Orchestrates deterministic security checks (SAST and Secret Scanning)."""

    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.bandit_path = r"C:\Users\Praveen Kasam\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\bandit.exe"

    def run_sast_scan(self, target_dir: str) -> dict:
        """Runs Bandit SAST scan on the target directory."""
        self.console.print(f"  🔍 [dim]Running Bandit SAST scan on {target_dir}...[/dim]")
        try:
            # -f json -r (recursive)
            result = subprocess.run(
                [self.bandit_path, "-f", "json", "-r", target_dir],
                capture_output=True,
                text=True
            )
            # Bandit returns non-zero if issues found, but we want the JSON
            if result.stdout:
                return json.loads(result.stdout)
            return {"results": [], "errors": ["No output from Bandit"]}
        except Exception as e:
            return {"results": [], "errors": [str(e)]}

    def scan_for_secrets(self, target_dir: str) -> list:
        """Simple regex-based secret scanning."""
        self.console.print(f"  🔑 [dim]Scanning for secrets in {target_dir}...[/dim]")
        secret_patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic API Key": r"(?:key|api|token|secret|password|passwd|auth)[-_=:\s]+['\"]([a-zA-Z0-9]{16,})['\"]",
            "Private Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"
        }
        
        findings = []
        path = Path(target_dir)
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".py", ".env", ".yaml", ".json", ".md", ".txt"]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    for name, pattern in secret_patterns.items():
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            findings.append({
                                "file": str(file_path),
                                "type": name,
                                "line": content.count('\n', 0, match.start()) + 1
                            })
                except Exception:
                    continue
        return findings

    def generate_report(self, sast_results: dict, secret_findings: list) -> str:
        """Formats scan results into a markdown report."""
        report = ["# 🛡️ Hard Security Gate Report", ""]
        
        # 1. SAST Findings
        report.append("## 🐍 Bandit SAST Findings")
        if not sast_results.get("results"):
            report.append("✅ No SAST vulnerabilities detected.")
        else:
            for issue in sast_results["results"]:
                report.append(f"- **[{issue['issue_severity']}]** {issue['issue_text']}")
                report.append(f"  - File: `{issue['filename']}` (Line {issue['line_number']})")
                report.append(f"  - More info: {issue['test_id']}")
        
        report.append("")
        
        # 2. Secret Findings
        report.append("## 🔑 Secret Scanning Findings")
        if not secret_findings:
            report.append("✅ No hardcoded secrets found.")
        else:
            for finding in secret_findings:
                report.append(f"- **[CRITICAL]** Potential {finding['type']} detected")
                report.append(f"  - File: `{finding['file']}` (Line {finding['line']})")
        
        return "\n".join(report)

if __name__ == "__main__":
    scanner = SecurityScanner()
    # Test on repo/src
    sast = scanner.run_sast_scan("src")
    secrets = scanner.scan_for_secrets("src")
    print(scanner.generate_report(sast, secrets))
