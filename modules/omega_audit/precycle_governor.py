"""Pré-ciclo: ancora diária (fail-closed), conflito de sinais por (ativo, timeframe)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.omega_audit.reporting import AuditIssue

# Sensibilidade mínima para contar como "alta convicção" no conflito
CONFLICT_SENSITIVITY = 0.85


def default_anchor_path(source_root: Path) -> Path:
    return source_root / "audit" / "risk" / "ks_daily_anchor.json"


def _today_local() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_daily_anchor_fail_closed(anchor_path: Path) -> tuple[float | None, list[AuditIssue]]:
    """
    Lê ks_daily_anchor.json. Fail-closed: ficheiro ausente, JSON inválido,
    chaves em falta, ou data != dia local => ancora inválida.
    """
    issues: list[AuditIssue] = []
    if not anchor_path.exists():
        issues.append(
            AuditIssue(
                "CRITICAL",
                "PRECYCLE_ANCHOR",
                "ks_daily_anchor.json ausente — Fail-Closed",
                "AUD-PC-001",
                detail={"path": str(anchor_path)},
            )
        )
        return None, issues

    try:
        raw = anchor_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as e:
        issues.append(
            AuditIssue(
                "CRITICAL",
                "PRECYCLE_ANCHOR",
                f"ks_daily_anchor.json corrompido ou ilegível: {e}",
                "AUD-PC-002",
                detail={"path": str(anchor_path)},
            )
        )
        return None, issues

    today = _today_local()
    file_date = data.get("date")
    if file_date != today:
        issues.append(
            AuditIssue(
                "CRITICAL",
                "PRECYCLE_ANCHOR",
                f"Data da ancora ({file_date!r}) != dia local ({today}) — Fail-Closed",
                "AUD-PC-003",
                detail={"path": str(anchor_path)},
            )
        )
        return None, issues

    try:
        anchor = float(data["anchor_equity"])
    except (KeyError, TypeError, ValueError):
        issues.append(
            AuditIssue(
                "CRITICAL",
                "PRECYCLE_ANCHOR",
                "Campo anchor_equity ausente ou inválido",
                "AUD-PC-004",
                detail={"path": str(anchor_path)},
            )
        )
        return None, issues

    return anchor, issues


def _signal_key(s: dict[str, Any]) -> tuple[str, str]:
    sym = str(s.get("symbol") or s.get("ativo") or "").strip().upper()
    tf = str(s.get("timeframe") or s.get("tf") or "").strip().upper()
    return sym, tf


def detect_signal_conflicts(
    signal_matrix: list[dict[str, Any]],
    *,
    sensitivity: float = CONFLICT_SENSITIVITY,
) -> list[AuditIssue]:
    """
    Conflito apenas dentro do mesmo (symbol, timeframe).
    """
    issues: list[AuditIssue] = []
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for s in signal_matrix:
        sym, tf = _signal_key(s)
        if not sym or not tf:
            continue
        buckets.setdefault((sym, tf), []).append(s)

    for (sym, tf), rows in buckets.items():
        buy = sum(
            1
            for r in rows
            if str(r.get("direction", "")).upper() == "BUY"
            and float(r.get("confidence") or 0) > sensitivity
        )
        sell = sum(
            1
            for r in rows
            if str(r.get("direction", "")).upper() == "SELL"
            and float(r.get("confidence") or 0) > sensitivity
        )
        if buy > 0 and sell > 0:
            issues.append(
                AuditIssue(
                    "HIGH",
                    "STRATEGY_FUSION",
                    f"Conflito BUY/SELL alta convicção em {sym} {tf}",
                    "AUD-PC-010",
                    detail={"symbol": sym, "timeframe": tf, "buy": buy, "sell": sell},
                )
            )
    return issues


@dataclass
class PreCycleResult:
    allowed: bool
    issues: list[AuditIssue] = field(default_factory=list)

    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "CRITICAL")


def run_pre_cycle_check(
    source_root: Path,
    account_state: dict[str, Any],
    signal_matrix: list[dict[str, Any]],
    *,
    strict_mode: bool = True,
    anchor_path: Path | None = None,
    max_dd_allowed: float | None = None,
) -> PreCycleResult:
    """
    Validação pré-ciclo Tier-0.
    - Ancora: lê ks_daily_anchor.json (fail-closed).
    - Risco: equity < anchor * (1 - max_dd) => CRITICAL.
    - Sinais: conflito por (ativo, TF); em strict_mode HIGH de conflito => veto.
    """
    issues: list[AuditIssue] = []
    root = source_root.resolve()
    ap = anchor_path or default_anchor_path(root)

    anchor, anchor_issues = load_daily_anchor_fail_closed(ap)
    issues.extend(anchor_issues)
    if anchor is None:
        return PreCycleResult(False, issues)

    max_dd = max_dd_allowed
    if max_dd is None:
        max_dd = float(account_state.get("max_dd_allowed", 0.02))

    current_equity = float(account_state.get("equity", 0))
    floor = anchor * (1.0 - max_dd)
    if current_equity < floor:
        issues.append(
            AuditIssue(
                "CRITICAL",
                "RISK_ENGINE",
                f"Equity {current_equity:.2f} abaixo do limiar {floor:.2f} (anchor={anchor:.2f}, max_dd={max_dd})",
                "AUD-PC-020",
                detail={"equity": current_equity, "floor": floor, "anchor": anchor},
            )
        )
        return PreCycleResult(False, issues)

    conflict_issues = detect_signal_conflicts(signal_matrix)
    issues.extend(conflict_issues)
    if strict_mode and conflict_issues:
        return PreCycleResult(False, issues)

    if any(i.severity == "CRITICAL" for i in issues):
        return PreCycleResult(False, issues)

    return PreCycleResult(True, issues)
