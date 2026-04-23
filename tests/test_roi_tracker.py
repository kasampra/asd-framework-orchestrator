import unittest
from unittest.mock import MagicMock
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from services.roi_tracker import ROITracker
from memory.cost_tracker import PhaseEconomics

class TestROITracker(unittest.TestCase):

    def test_roi_calculation(self):
        # 1. Setup mock cost tracker
        mock_ct = MagicMock()
        mock_ct.phases = [
            PhaseEconomics("Phase 1", "Role 1", 1000, 500, 0.0, 60.0),
            PhaseEconomics("Phase 2", "Role 2", 2000, 1000, 0.0, 120.0)
        ]
        
        tracker = ROITracker(mock_ct)
        
        # 2. Run
        roi_md = tracker.calculate_roi()
        
        # 3. Assertions
        self.assertIn("Sovereign ROI Dashboard", roi_md)
        self.assertIn("Labor Cost", roi_md)
        self.assertIn("€0.00", roi_md) # Local cost should be 0

    def test_append_to_report(self):
        # 1. Setup dummy report
        report_path = Path("tests/logs/test_cp_roi.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# Old Report", encoding="utf-8")
        
        tracker = ROITracker(MagicMock())
        
        # 2. Run
        tracker.append_to_report(str(report_path), "### ROI Dashboard")
        
        # 3. Assertions
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("ROI Dashboard", content)

if __name__ == '__main__':
    unittest.main()
