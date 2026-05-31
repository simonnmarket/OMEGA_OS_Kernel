#!/usr/bin/env python3
"""PSA — Forense SKIP: porque nao abriu (GER40, XAGUSD, UKOIL) (MANDATO 20260601)."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / f"psa_skip_forensics_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
REPORT.parent.mkdir(parents=True, exist_ok=True)

LOG = ROOT / "audit" / "paper" / "omega_24x7_runner.log"
TRACE = ROOT / "audit" / "paper" / "decision_trace.jsonl"

TARGETS = {"GER40", "XAGUSD", "UKOIL+"}
SKIP_REASONS = [
    "MAX_POS_PER_ASSET", "SKIP_ALREADY_POSITIONED", "EDGE_GATE",
    "HOLD", "SKIP_MIN_CONF", "MARKET_CLOSED", "SKIP_NET_EDGE",
    "SKIP_MIN_TP_USD", "SKIP_RISK_BUDGET", "SKIP_DEDUP_CYCLE",
    "ENTRIES_FROZEN", "SKIP_LOT_FLOOR_RISK", "SKIP_SL_COOLDOWN",
]


def main() -> int:
    lines = ["# PSA Skip Forensics (MANDATO 20260601)\n"]
    lines.append(f"**UTC:** {datetime.now(timezone.utc).isoformat()}\n")
    lines.append(f"**Ativos alvo:** {', '.join(sorted(TARGETS))}\n\n")

    # 1) Contagem de SKIP no decision_trace
    trace_counts = {sym: {r: 0 for r in SKIP_REASONS} for sym in TARGETS}
    trace_total = {sym: 0 for sym in TARGETS}
    if TRACE.exists():
        with open(TRACE, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    sym = obj.get("asset", "")
                    if sym in TARGETS:
                        trace_total[sym] += 1
                        status = obj.get("status", "")
                        for reason in SKIP_REASONS:
                            if reason in status:
                                trace_counts[sym][reason] += 1
                except Exception:
                    pass

    lines.append("## Decision Trace (decision_trace.jsonl)\n")
    lines.append("| Ativo | Total | " + " | ".join(SKIP_REASONS) + " |\n")
    lines.append("|" + "|".join(["------"] * (2 + len(SKIP_REASONS))) + "|\n")
    for sym in sorted(TARGETS):
        vals = [str(trace_counts[sym].get(r, 0)) for r in SKIP_REASONS]
        lines.append(f"| {sym} | {trace_total[sym]} | " + " | ".join(vals) + " |\n")

    # 2) Contagem no log (regex)
    log_counts = {sym: {r: 0 for r in SKIP_REASONS} for sym in TARGETS}
    log_total = {sym: 0 for sym in TARGETS}
    if LOG.exists():
        with open(LOG, encoding="utf-8") as f:
            for line in f:
                for sym in TARGETS:
                    if sym in line:
                        log_total[sym] += 1
                        for reason in SKIP_REASONS:
                            if reason in line:
                                log_counts[sym][reason] += 1

    lines.append("\n## Log grep (omega_24x7_runner.log)\n")
    lines.append("| Ativo | Total linhas | " + " | ".join(SKIP_REASONS) + " |\n")
    lines.append("|" + "|".join(["------"] * (2 + len(SKIP_REASONS))) + "|\n")
    for sym in sorted(TARGETS):
        vals = [str(log_counts[sym].get(r, 0)) for r in SKIP_REASONS]
        lines.append(f"| {sym} | {log_total[sym]} | " + " | ".join(vals) + " |\n")

    # 3) Amostras de SKIP do log
    lines.append("\n## Amostras de linhas SKIP (últimas 20 por ativo)\n")
    if LOG.exists():
        with open(LOG, encoding="utf-8") as f:
            all_lines = f.readlines()
        for sym in sorted(TARGETS):
            samples = [l.strip() for l in all_lines if sym in l and any(r in l for r in SKIP_REASONS)]
            lines.append(f"\n### {sym}\n")
            for s in samples[-20:]:
                lines.append(f"```\n{s}\n```\n")
            if not samples:
                lines.append("_Nenhuma amostra encontrada_\n")

    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
