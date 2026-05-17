"""
OMEGA Intelligence Audit — pacote Tier-0 (fachada única).

O ecossistema deve importar apenas deste módulo:
  from modules.omega_audit import run_pre_cycle_check, verify_against_baseline, ...

CLI oficial (Windows): python scripts/omega_audit_cli.py <comando> ...
"""
from __future__ import annotations

from pathlib import Path

from modules.omega_audit.precycle_governor import (
    CONFLICT_SENSITIVITY,
    PreCycleResult,
    default_anchor_path,
    detect_signal_conflicts,
    load_daily_anchor_fail_closed,
    run_pre_cycle_check,
)
from modules.omega_audit.registry import (
    default_registry_path,
    load_registry,
    register_component,
    save_registry,
)
from modules.omega_audit.reporting import AuditIssue, write_json_report as _write_json_report
from modules.omega_audit.static_inventory import (
    BaselineVerification,
    default_baseline_path,
    run_static_inventory,
    verify_against_baseline,
    write_baseline,
)

__all__ = [
    "CONFLICT_SENSITIVITY",
    "AuditIssue",
    "BaselineVerification",
    "PreCycleResult",
    "default_anchor_path",
    "default_baseline_path",
    "default_registry_path",
    "detect_signal_conflicts",
    "load_daily_anchor_fail_closed",
    "load_registry",
    "register_component",
    "run_pre_cycle_check",
    "run_static_inventory",
    "save_registry",
    "verify_against_baseline",
    "write_audit_report",
    "write_baseline",
]


def write_audit_report(
    issues: list[AuditIssue],
    source_root: Path,
    *,
    prefix: str = "audit_report",
) -> Path:
    """Conveniência: grava em audit/omega_audit/logs/."""
    out_dir = Path(source_root).resolve() / "audit" / "omega_audit" / "logs"
    return _write_json_report(issues, out_dir, prefix=prefix)
