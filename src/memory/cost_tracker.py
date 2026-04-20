import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

@dataclass
class PhaseEconomics:
    phase_name: str
    agent_role: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0

class CostTracker:
    def __init__(self, model: str = "qwen/qwen3.6-35b-a3b"):
        self.phases: List[PhaseEconomics] = []
        self.model = model
        # Simple pricing for gpt-4o as a fallback/reference
        # Input: $2.50 / 1M tokens, Output: $10.00 / 1M tokens
        self.pricing = {
            "gpt-4o": {"input": 0.0000025, "output": 0.000010},
            "qwen/qwen3.6-35b-a3b": {"input": 0.0, "output": 0.0},
            "local-qwen": {"input": 0.0, "output": 0.0}
        }

    def record_phase(self, phase_name: str, agent_role: str, input_tokens: int, output_tokens: int, duration_seconds: float):
        cost = 0.0
        if self.model in self.pricing:
            cost = (input_tokens * self.pricing[self.model]["input"]) + (output_tokens * self.pricing[self.model]["output"])
        
        phase = PhaseEconomics(
            phase_name=phase_name,
            agent_role=agent_role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            duration_seconds=duration_seconds
        )
        self.phases.append(phase)

    def total_tokens(self) -> int:
        return sum(p.input_tokens + p.output_tokens for p in self.phases)

    def total_cost_usd(self) -> float:
        return sum(p.cost_usd for p in self.phases)

    def most_expensive_phase(self) -> str:
        if not self.phases:
            return "None"
        expensive = max(self.phases, key=lambda p: p.cost_usd if p.cost_usd > 0 else p.input_tokens + p.output_tokens)
        return expensive.phase_name

    def write_report(self, output_dir: str = "logs") -> str:
        Path(output_dir).mkdir(exist_ok=True)
        report = {
            "model": self.model,
            "total_tokens": self.total_tokens(),
            "total_cost_usd": self.total_cost_usd(),
            "most_expensive_phase": self.most_expensive_phase(),
            "phases": [asdict(p) for p in self.phases]
        }
        
        filepath = Path(output_dir) / "cost_report.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        return str(filepath)
