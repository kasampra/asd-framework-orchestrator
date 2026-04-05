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
    "ci_provider":         "INFO"
}


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

    def generate_rbac_snippet(self) -> str:
        """Generates a markdown snippet for logs/rbac_suggestions.md"""
        if self.breaking_count == 0:
            return ""
        
        lines = [
            "### 🔒 Cognitive RBAC Lock Suggestion",
            "Breaking drift detected in core architectural decisions. Apply this lock to config/agents.md to prevent future drift.",
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
        
        for field, severity in SEVERITY_MAP.items():
            old_val = b_flat.get(field)
            new_val = c_flat.get(field)
            
            if old_val != new_val:
                issues.append(DriftIssue(
                    field=field,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                    severity=severity
                ))
        
        breaking = sum(1 for i in issues if i.severity == "BREAKING")
        warning = sum(1 for i in issues if i.severity == "WARNING")
        
        return DriftReport(
            has_drift=len(issues) > 0,
            issues=issues,
            breaking_count=breaking,
            warning_count=warning
        )

    def _flatten(self, data: dict) -> dict:
        flat = {}
        for section in ["architecture", "infrastructure", "quality"]:
            content = data.get(section, {})
            if isinstance(content, dict):
                flat.update(content)
        return flat
