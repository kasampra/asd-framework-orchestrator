import unittest
from pathlib import Path
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from services.admin_dashboard import AdminDashboard

class TestAdminDashboard(unittest.TestCase):

    def setUp(self):
        self.dashboard = AdminDashboard()

    def test_rendering_methods(self):
        # 1. Project Info
        project_info = self.dashboard.render_project_info()
        self.assertIn("Project Health", project_info)
        self.assertIn("OPTIMAL", project_info)
        
        # 2. Agent Health
        agent_health = self.dashboard.render_agent_health()
        self.assertIn("Agent Personas", agent_health)
        self.assertIn("Active", agent_health)
        
        # 3. ROI Summary
        roi_summary = self.dashboard.render_roi_summary()
        self.assertIn("ROI Dashboard", roi_summary)

if __name__ == '__main__':
    unittest.main()
