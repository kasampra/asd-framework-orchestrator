import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class SelfHealer:
    """
    The Self-Healing Flywheel for ASD Orchestrator.
    Follows the MAPE-K loop pattern (Monitor, Analyze, Plan, Execute, Knowledge).
    Designed for Sovereign AI compliance (Article 13).
    """
    
    def __init__(self, trace_dir: str = "traces"):
        self.trace_dir = Path(trace_dir)
        self.recursion_limit = 3
        self.metrics = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "categories": {}
        }
        self._ensure_trace_dir()

    def _ensure_trace_dir(self):
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def monitor(self, result: Dict) -> Optional[Dict]:
        """
        [MONITOR] Detects anomalies in tool outputs or phase results.
        """
        if result.get("exit_code", 0) != 0 or "error" in result or result.get("decision") == "FAIL":
            return {
                "timestamp": datetime.now().isoformat(),
                "error_output": result.get("output", result.get("error", result.get("reasoning", ""))),
                "context": result.get("context", {}),
                "phase": result.get("phase", "unknown")
            }
        return None

    def diagnose(self, failure_context: Dict) -> Dict:
        """
        [ANALYZE] Deterministic root-cause analysis with severity scoring.
        """
        output = failure_context["error_output"].lower()
        
        # Pattern-based diagnosis (Industrial-strength regex or string matching)
        if any(x in output for x in ["syntaxerror", "indentationerror", "unexpected token"]):
            category = "LINT/SYNTAX"
            severity = 5
        elif any(x in output for x in ["modulenotfounderror", "import-error", "pip install"]):
            category = "INFRA/DEPENDENCY"
            severity = 4
        elif any(x in output for x in ["assertionerror", "failed", "gate failed", "rejected"]):
            category = "LOGIC/QUALITY"
            severity = 3
        elif any(x in output for x in ["ambiguous", "multiple occurrences", "not unique"]):
            category = "AMBIGUITY/TOOL"
            severity = 2
        else:
            category = "UNKNOWN/HEURISTIC"
            severity = 1
            
        self.metrics["categories"][category] = self.metrics["categories"].get(category, 0) + 1
        
        return {
            "category": category,
            "severity": severity,
            "summary": failure_context["error_output"][:500],
            "timestamp": datetime.now().isoformat()
        }

    def plan(self, diagnosis: Dict) -> Dict:
        """
        [PLAN] Formulates a recovery strategy based on diagnosis.
        """
        category = diagnosis["category"]
        
        strategies = {
            "LINT/SYNTAX": "Identify the malformed block and apply surgical syntax correction.",
            "INFRA/DEPENDENCY": "Update requirements.txt or run specific package installation commands.",
            "LOGIC/QUALITY": "Reflect on the Gatekeeper's reasoning and refine the business logic.",
            "AMBIGUITY/TOOL": "Expand the search context or provide line-specific ranges to ensure tool uniqueness.",
            "UNKNOWN/HEURISTIC": "General retry with expanded error context for the agent."
        }
        
        return {
            "strategy": strategies.get(category, "Standard recovery protocol."),
            "requires_human": category == "UNKNOWN/HEURISTIC" and self.metrics["attempts"] >= self.recursion_limit
        }

    def log_trace(self, data: Dict):
        """
        [KNOWLEDGE] Writes an immutable 'Glass Box' trace for auditability.
        Ensures compliance with EU AI Act Article 13.
        """
        timestamp = data.get("timestamp", datetime.now().isoformat())
        category = data.get("diagnosis", {}).get("category", "unknown")
        strategy = data.get("plan", {}).get("strategy", "No strategy provided")

        filename = f"healing_{int(time.time())}_{category.replace('/', '_')}.json"
        filepath = self.trace_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        # Also append to a summary log for easier content generation
        with open(self.trace_dir / "healing_history.log", 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {category} - {strategy}\n")

    def execute_heal(self, plan: Dict):
        """
        Placeholder for the actual healing action (using tools).
        """
        print(f"Executing Heal: {plan['strategy']}")

    def get_adaptive_suggestion(self) -> Optional[str]:
        """
        Analyzes healing history to suggest systemic improvements (Policy-as-Code).
        """
        for cat, count in self.metrics["categories"].items():
            if count > 2:
                return f"SYSTEMIC ALERT: Category '{cat}' has failed {count} times. Suggest updating .asd/policies/ to include automated pre-checks for this failure type."
        return None

# Prototype usage
if __name__ == "__main__":
    healer = SelfHealer(trace_dir="projects/asd-orchestrator/traces")
    
    # Simulate a failure
    simulated_failure = {
        "exit_code": 1,
        "output": "ModuleNotFoundError: No module named 'tavily'",
        "context": {"file": "research_agent.py"}
    }
    
    failure = healer.monitor(simulated_failure)
    if failure:
        diagnosis = healer.diagnose(failure)
        healing_plan = healer.plan(diagnosis)
        
        trace_data = {
            "failure": failure,
            "diagnosis": diagnosis,
            "plan": healing_plan
        }
        healer.log_trace(trace_data)
        healer.execute_heal(healing_plan)
