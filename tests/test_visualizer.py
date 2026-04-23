import unittest
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from services.visualizer import Visualizer
from control_plane import StepTrace

class TestVisualizer(unittest.TestCase):

    def test_mermaid_generation(self):
        # 1. Setup dummy steps
        step1 = StepTrace(phase_name="Phase 1", agent_role="Requirements Engineer")
        step2 = StepTrace(phase_name="Phase 2", agent_role="Architect", gate_decision="PASS")
        
        # 2. Run
        mermaid_md = Visualizer.generate_mermaid([step1, step2])
        
        # 3. Assertions
        self.assertIn("graph TD", mermaid_md)
        self.assertIn("sequenceDiagram", mermaid_md)
        self.assertIn("Requirements Engineer", mermaid_md)
        self.assertIn("Architect", mermaid_md)
        self.assertIn("Gate Result: PASS", mermaid_md)

    def test_append_to_report(self):
        # 1. Setup dummy report
        report_path = Path("tests/logs/test_cp_visual.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# Old Report", encoding="utf-8")
        
        # 2. Run
        Visualizer.append_to_report(str(report_path), "### Mermaid Diagram")
        
        # 3. Assertions
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("Mermaid Diagram", content)

if __name__ == '__main__':
    unittest.main()
