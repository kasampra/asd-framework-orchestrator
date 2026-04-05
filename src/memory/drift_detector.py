# src/memory/drift_detector.py
from typing import List, Optional
from pydantic import BaseModel
from .fingerprint_extractor import DecisionFingerprint

SEVERITY_MAP = {
    "web_framework":       "BREAKING",
    "base_image":          "BREAKING",
    "database":            "BREAKING",
    "auth_pattern":        "BREAKING",
    "folder_structure":    "WARNING",
    "async_pattern":       "WARNING",
    "test_runner":         "WARNING",
    "linter":              "INFO",
    "coverage_threshold":  "WARNING",
    "dependency_manager":  "WARNING",
    "compose_version":     "INFO",
    "port_mapping":        "WARNING",
    "ci_provider":         "INFO",
    "token_budget_exceeded": "BREAKING",   # NEW
    "total_cost_usd":        "WARNING",    # NEW
    "total_tokens":          "WARNING",    # NEW
    "most_expensive_phase":  "INFO",       # NEW
}

COST_DRIFT_THRESHOLD = 0.30   # 30% above baseline triggers WARNING


class DriftIssue(BaseModel):
    field: str
    old_value: Optional[str]
    new_value: Optional[str]
    severity: str


class DriftReport(BaseModel):
    has_drift: bool
    issues: List[DriftIssue]
    breaking_count: int
    warning_count: int

    @property
    def has_breaking_drift(self) -> bool:
        return self.breaking_count > 0

    def generate_rbac_snippet(self) -> str:
        """Generates a markdown snippet for logs/rbac_suggestions.md"""
        if self.breaking_count == 0:
            return ""
        
        lines = [
            "### 🔒 Cognitive RBAC Lock Suggestion",
            "Breaking drift detected in core architectural or economic decisions. Apply this lock to config/agents.md to prevent future drift.",
            "",
            "```json",
            "{"
        ]
        
        locks = [f'  "{i.field}": "{i.old_value}"' for i in self.issues if i.severity == "BREAKING"]
        lines.append(",\n".join(locks))
        lines.append("}")
        lines.append("```")
        lines.append("\n---\n")
        return "\n".join(lines)


class DriftDetector:
    def detect(self, baseline: dict, current: DecisionFingerprint) -> DriftReport:
        issues = []
        b_flat = self._flatten(baseline)
        c_flat = self._flatten(current.model_dump())
        
        # 1. Standard structural drift (string equality)
        for field, severity in SEVERITY_MAP.items():
            if field in ["total_cost_usd", "total_tokens", "token_budget_exceeded"]:
                continue # Handled by _check_cost_drift
                
            old_val = b_flat.get(field)
            new_val = c_flat.get(field)
            
            if old_val != new_val:
                issues.append(DriftIssue(
                    field=field,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                    severity=severity
                ))
        
        # 2. Economic drift (numeric threshold check)
        baseline_econ = baseline.get("economics", {})
        current_econ = current.economics.model_dump()
        issues.extend(self._check_cost_drift(baseline_econ, current_econ))

        breaking = sum(1 for i in issues if i.severity == "BREAKING")
        warning = sum(1 for i in issues if i.severity == "WARNING")
        
        return DriftReport(
            has_drift=len(issues) > 0,
            issues=issues,
            breaking_count=breaking,
            warning_count=warning
        )

    def _check_cost_drift(self, baseline_econ: dict, current_econ: dict) -> List[DriftIssue]:
        issues = []
        
        # Check budget first
        if current_econ.get("token_budget_exceeded"):
            issues.append(DriftIssue(
                field="token_budget_exceeded",
                old_value="False",
                new_value="True",
                severity="BREAKING"
            ))

        # Check total cost drift
        baseline_cost = baseline_econ.get("total_cost_usd") or 0
        current_cost = current_econ.get("total_cost_usd") or 0
        if baseline_cost > 0:
            delta = (current_cost - baseline_cost) / baseline_cost
            if delta > COST_DRIFT_THRESHOLD:
                issues.append(DriftIssue(
                    field="total_cost_usd",
                    old_value=f"${baseline_cost:.4f}",
                    new_value=f"${current_cost:.4f} (+{delta:.0%})",
                    severity="WARNING"
                ))

        # Check token volume drift
        baseline_tokens = baseline_econ.get("total_tokens") or 0
        current_tokens = current_econ.get("total_tokens") or 0
        if baseline_tokens > 0:
            delta = (current_tokens - baseline_tokens) / baseline_tokens
            if delta > COST_DRIFT_THRESHOLD:
                issues.append(DriftIssue(
                    field="total_tokens",
                    old_value=f"{baseline_tokens:,}",
                    new_value=f"{current_tokens:,} (+{delta:.0%})",
                    severity="WARNING"
                ))

        return issues

    def _flatten(self, data: dict) -> dict:
        flat = {}
        for section in ["architecture", "infrastructure", "quality", "economics"]:
            content = data.get(section, {})
            if isinstance(content, dict):
                flat.update(content)
        return flat
