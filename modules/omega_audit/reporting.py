"""Relatórios forenses JSON (UTF-8) — fonte de verdade para auditoria Tier-0."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Severity = Literal["CRITICAL", "HIGH", "WARNING", "INFO"]


@dataclass
class AuditIssue:
    severity: Severity
    module: str
    message: str
    code: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    detail: dict[str, Any] | None = None


def write_json_report(
    issues: list[AuditIssue],
    out_dir: Path,
    *,
    prefix: str = "audit_report",
) -> Path:
    """Escreve relatório JSON em UTF-8 (mitigação Windows)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{prefix}_{int(time.time())}.json"
    path = out_dir / name
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SECURE" if not issues else "ATTENTION",
        "critical_count": sum(1 for i in issues if i.severity == "CRITICAL"),
        "high_count": sum(1 for i in issues if i.severity == "HIGH"),
        "warning_count": sum(1 for i in issues if i.severity == "WARNING"),
        "issues": [asdict(i) for i in issues],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def issues_to_simple_dict(issues: list[AuditIssue]) -> list[dict[str, Any]]:
    return [asdict(i) for i in issues]
