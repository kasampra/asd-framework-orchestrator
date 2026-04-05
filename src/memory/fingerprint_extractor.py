# src/memory/fingerprint_extractor.py
import os
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class EconomicsData(BaseModel):
    total_tokens: Optional[int] = None
    total_cost_usd: Optional[float] = None
    cost_per_phase: Optional[dict] = None    # {"Phase 1 Requirements": 0.024, ...}
    most_expensive_phase: Optional[str] = None
    token_budget_exceeded: Optional[bool] = None
    token_budget: Optional[int] = None       # From config if set, else None


class ArchitectureDecisions(BaseModel):
    web_framework: Optional[str] = None
    folder_structure: Optional[str] = None
    database: Optional[str] = None
    auth_pattern: Optional[str] = None
    async_pattern: Optional[str] = None


class InfrastructureDecisions(BaseModel):
    base_image: Optional[str] = None
    compose_version: Optional[str] = None
    ci_provider: Optional[str] = None
    port_mapping: Optional[str] = None


class QualityDecisions(BaseModel):
    test_runner: Optional[str] = None
    coverage_threshold: Optional[str] = None
    linter: Optional[str] = None
    dependency_manager: Optional[str] = None


class DecisionFingerprint(BaseModel):
    run_id: str
    project_name: str
    timestamp: str
    pipeline_hash: str
    architecture: ArchitectureDecisions
    infrastructure: InfrastructureDecisions
    quality: QualityDecisions
    economics: EconomicsData    # NEW
    passed_gates: list[str] = []


class FingerprintExtractor:
    def __init__(self, output_dir: str, run_id: str, project_name: str):
        self.output_dir = Path(output_dir)
        self.run_id = run_id
        self.project_name = project_name

    def extract(self) -> DecisionFingerprint:
        return DecisionFingerprint(
            run_id=self.run_id,
            project_name=self.project_name,
            timestamp=datetime.utcnow().isoformat(),
            pipeline_hash=self._hash_outputs(),
            architecture=self._extract_architecture(),
            infrastructure=self._extract_infrastructure(),
            quality=self._extract_quality(),
            economics=self._extract_economics(),
            passed_gates=self._extract_gates()
        )

    def _hash_outputs(self) -> str:
        h = hashlib.sha256()
        if not self.output_dir.exists():
            return "no_output"
        for root, _, files in os.walk(self.output_dir):
            for f in sorted(files):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, 'rb') as fh:
                        h.update(fh.read())
                except (IOError, OSError):
                    pass
        return h.hexdigest()[:8]

    def _read_file_safe(self, *paths) -> str:
        for path in paths:
            p = self.output_dir / path
            if p.exists():
                try:
                    return p.read_text(encoding="utf-8").lower()
                except Exception:
                    pass
        return ""

    def _extract_architecture(self) -> ArchitectureDecisions:
        req = self._read_file_safe("requirements.txt", "backend/requirements.txt")
        arch = self._read_file_safe("output_phase_2_architecture.md", "architecture.md")
        combined = req + arch

        framework = None
        for fw in ["fastapi", "flask", "django", "express", "fastify"]:
            if fw in combined:
                framework = fw
                break

        database = None
        for db in ["postgres", "postgresql", "sqlite", "mongodb", "mysql", "redis"]:
            if db in combined:
                database = db
                break

        auth = None
        for a in ["jwt", "oauth", "session"]:
            if a in combined:
                auth = a
                break

        async_p = None
        if "asyncio" in combined or "async def" in combined:
            async_p = "asyncio"
        elif "celery" in combined:
            async_p = "celery"

        src_exists = (self.output_dir / "src").exists() or (self.output_dir / "backend" / "src").exists()
        folder = "src_layout" if src_exists else "flat"

        return ArchitectureDecisions(
            web_framework=framework,
            folder_structure=folder,
            database=database,
            auth_pattern=auth,
            async_pattern=async_p
        )

    def _extract_infrastructure(self) -> InfrastructureDecisions:
        dockerfile = self._read_file_safe("Dockerfile", "backend/Dockerfile")
        compose = self._read_file_safe("docker-compose.yml", "docker-compose.yaml")

        base_image = None
        for line in dockerfile.splitlines():
            if line.strip().startswith("from "):
                parts = line.strip().split()
                if len(parts) >= 2:
                    base_image = parts[1]
                    break

        compose_ver = None
        for line in compose.splitlines():
            if line.strip().startswith("version:"):
                compose_ver = line.split(":", 1)[-1].strip().strip('"').strip("'")
                break

        port = None
        for line in dockerfile.splitlines():
            if line.strip().startswith("expose"):
                port = line.strip().split()[-1]
                break

        ci = "none"
        if (self.output_dir / ".github" / "workflows").exists():
            ci = "github_actions"
        elif (self.output_dir / ".gitlab-ci.yml").exists():
            ci = "gitlab"

        return InfrastructureDecisions(
            base_image=base_image,
            compose_version=compose_ver,
            ci_provider=ci,
            port_mapping=port
        )

    def _extract_quality(self) -> QualityDecisions:
        req = self._read_file_safe("requirements.txt", "backend/requirements.txt")
        pyproject = self._read_file_safe("pyproject.toml")
        combined = req + pyproject

        test_runner = None
        if "pytest" in combined:
            test_runner = "pytest"
        elif "unittest" in combined:
            test_runner = "unittest"

        linter = None
        if "ruff" in combined:
            linter = "ruff"
        elif "flake8" in combined:
            linter = "flake8"

        dep_manager = "pip"
        if (self.output_dir / "uv.lock").exists():
            dep_manager = "uv"
        elif (self.output_dir / "poetry.lock").exists():
            dep_manager = "poetry"

        threshold = None
        match = re.search(r"fail_under\s*=\s*(\d+)", pyproject)
        if match:
            threshold = match.group(1)

        return QualityDecisions(
            test_runner=test_runner,
            coverage_threshold=threshold,
            linter=linter,
            dependency_manager=dep_manager
        )

    def _extract_economics(self) -> EconomicsData:
        report_path = Path("logs/cost_report.json")
        if not report_path.exists():
            return EconomicsData()
            
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            return EconomicsData(
                total_tokens=report.get("total_tokens"),
                total_cost_usd=report.get("total_cost_usd"),
                cost_per_phase={p["phase_name"]: p["cost_usd"] for p in report.get("phases", [])},
                most_expensive_phase=report.get("most_expensive_phase")
            )
        except Exception:
            return EconomicsData()

    def _extract_gates(self) -> list[str]:
        gates = []
        audit_path = Path("logs/audit.md")
        if audit_path.exists():
            content = audit_path.read_text(encoding="utf-8")
            if "gate_1" in content.lower() or "architecture review" in content.lower():
                gates.append("gate_1")
            if "gate_2" in content.lower() or "qa review" in content.lower():
                gates.append("gate_2")
            if "gate_3" in content.lower() or "security review" in content.lower():
                gates.append("gate_3")
        return gates
