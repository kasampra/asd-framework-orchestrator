from pathlib import Path
from typing import List
from memory.cost_tracker import CostTracker

class ROITracker:
    """Calculates and visualizes the Return on Investment for sovereign agentic delivery."""

    def __init__(self, cost_tracker: CostTracker):
        self.ct = cost_tracker
        # Heuristics
        self.HUMAN_HOURLY_RATE = 80.0  # EUR/hr
        self.ESTIMATED_HUMAN_HOURS_PER_PHASE = 2.5 # Average hours a human takes for a full SDLC phase
        self.GPT4O_INPUT_PRICE = 2.50 / 1_000_000
        self.GPT4O_OUTPUT_PRICE = 10.00 / 1_000_000

    def calculate_roi(self) -> str:
        total_input = sum(p.input_tokens for p in self.ct.phases)
        total_output = sum(p.output_tokens for p in self.ct.phases)
        total_duration_sec = sum(p.duration_seconds for p in self.ct.phases)
        total_duration_min = total_duration_sec / 60
        
        # 1. Cloud Cost Avoidance
        cloud_cost = (total_input * self.GPT4O_INPUT_PRICE) + (total_output * self.GPT4O_OUTPUT_PRICE)
        
        # 2. Time Savings (Human vs Agent)
        num_phases = len(self.ct.phases)
        human_estimated_hours = num_phases * self.ESTIMATED_HUMAN_HOURS_PER_PHASE
        human_estimated_cost = human_estimated_hours * self.HUMAN_HOURLY_RATE
        
        time_saved_hours = human_estimated_hours - (total_duration_sec / 3600)
        
        # 3. Final ROI Dashboard
        dashboard = [
            "## 💰 Sovereign ROI Dashboard",
            "",
            f"| Metric | Sovereign (Local) | Legacy (Cloud/Human) | Savings |",
            f"|--------|-------------------|----------------------|---------|",
            f"| **Direct Cost** | €0.00 | €{cloud_cost:.4f} (Cloud LLM) | 100% |",
            f"| **Labor Cost** | €0.00 | €{human_estimated_cost:.2f} (Human) | 100% |",
            f"| **Execution Time** | {total_duration_min:.1f}m | {human_estimated_hours:.1f}h | ~{ (1 - (total_duration_sec/(human_estimated_hours*3600)))*100:.1f}% |",
            "",
            f"### Key Sovereign Benefits:",
            f"- **Data Sovereignty:** 0KB of sensitive context left your local infrastructure.",
            f"- **Intelligence Retained:** All fine-tuning and patterns are stored in your private `PatternCatalog`.",
            f"- **Cost Floor:** Your marginal cost per feature is now effectively €0 (excluding electricity).",
            ""
        ]
        
        return "\n".join(dashboard)

    def append_to_report(self, report_path: str, roi_md: str):
        path = Path(report_path)
        if path.exists():
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n\n---\n")
                f.write(roi_md)
            return True
        return False
