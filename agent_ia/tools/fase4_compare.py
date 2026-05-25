"""
PSA-WIND | Fase 4 — comparativo A/B (BASELINE vs IA_ON).
Le os ultimos aggregates produzidos por fase4_wrapper.py e gera:
  logs/agent_ia_phase3/fase4_AB_compare_<ts>.json (+ .sha3)

Saida: tabela de criterios GO/NO-GO no stdout.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = ROOT / "logs" / "agent_ia_phase3"

CRITERIA = {
    "hit_rate_min_pct": 60.0,
    "p95_latency_ms_max": 200.0,
    "max_concentration_pct_max": 40.0,
    "min_trades_per_phase": 50,
    "ks_triggers_max": 0,
}


def latest_aggregate(label: str) -> dict:
    dirs = sorted([p for p in LOGS_DIR.glob(f"fase4_{label}_*") if p.is_dir()])
    if not dirs:
        return {}
    last = dirs[-1]
    p = last / f"fase4_{label}_aggregate.json"
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    d["_dir"] = str(last)
    return d


def evaluate(d: dict) -> dict:
    out = {}
    out["hit_rate"] = (d.get("hit_rate_avg", 0), d.get("hit_rate_avg", 0) >= CRITERIA["hit_rate_min_pct"])
    out["p95_latency"] = (d.get("latency_ms_p95", 0), d.get("latency_ms_p95", 0) <= CRITERIA["p95_latency_ms_max"])
    out["max_concentration"] = (d.get("max_concentration_pct", 0), d.get("max_concentration_pct", 0) < CRITERIA["max_concentration_pct_max"])
    out["min_trades"] = (d.get("total_trades", 0), d.get("total_trades", 0) >= CRITERIA["min_trades_per_phase"])
    out["ks_triggers"] = (d.get("kill_switch_triggers", 0), d.get("kill_switch_triggers", 0) <= CRITERIA["ks_triggers_max"])
    return out


def main() -> int:
    A = latest_aggregate("BASELINE")
    B = latest_aggregate("IA_ON")
    if not A or not B:
        print("[ERR] aggregates ausentes (BASELINE ou IA_ON)")
        return 1

    evalA = evaluate(A)
    evalB = evaluate(B)

    print("=" * 78)
    print(f"{'Metrica':<26} {'BASELINE':>18} {'IA_ON':>18} {'Threshold':>12}")
    print("-" * 78)
    rows = [
        ("trades", A["total_trades"], B["total_trades"], f">={CRITERIA['min_trades_per_phase']}"),
        ("hit_rate_avg %", A["hit_rate_avg"], B["hit_rate_avg"], f">={CRITERIA['hit_rate_min_pct']}"),
        ("latency_p95 ms", A["latency_ms_p95"], B["latency_ms_p95"], f"<={CRITERIA['p95_latency_ms_max']}"),
        ("latency_max ms", A["latency_ms_max"], B["latency_ms_max"], "—"),
        ("ks_triggers", A["kill_switch_triggers"], B["kill_switch_triggers"], f"<={CRITERIA['ks_triggers_max']}"),
        ("max_concentration %", A["max_concentration_pct"], B["max_concentration_pct"], f"<{CRITERIA['max_concentration_pct_max']}"),
    ]
    for r in rows:
        print(f"{r[0]:<26} {str(r[1]):>18} {str(r[2]):>18} {str(r[3]):>12}")
    print("=" * 78)

    print("\nGO/NO-GO criterion-by-criterion:")
    for k in evalA:
        v_a, ok_a = evalA[k]
        v_b, ok_b = evalB[k]
        flag_a = "PASS" if ok_a else "FAIL"
        flag_b = "PASS" if ok_b else "FAIL"
        print(f"  {k:<22} A={v_a} [{flag_a}]  |  B={v_b} [{flag_b}]")

    overall_a = all(ok for _, ok in evalA.values())
    overall_b = all(ok for _, ok in evalB.values())
    print(f"\n  OVERALL  BASELINE={'GO' if overall_a else 'NO-GO'}   IA_ON={'GO' if overall_b else 'NO-GO'}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = {
        "timestamp_utc": ts,
        "criteria": CRITERIA,
        "BASELINE": A,
        "IA_ON": B,
        "evaluations": {
            "BASELINE": {k: {"value": v, "pass": ok} for k, (v, ok) in evalA.items()},
            "IA_ON": {k: {"value": v, "pass": ok} for k, (v, ok) in evalB.items()},
        },
        "verdict": {
            "BASELINE": "GO" if overall_a else "NO-GO",
            "IA_ON": "GO" if overall_b else "NO-GO",
        },
    }
    out_path = LOGS_DIR / f"fase4_AB_compare_{ts}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    sha = hashlib.sha3_256(open(out_path, "rb").read()).hexdigest()
    (LOGS_DIR / f"fase4_AB_compare_{ts}.sha3").write_text(sha + "\n", encoding="utf-8")
    print(f"\n[COMPARE_JSON] {out_path}")
    print(f"[COMPARE_SHA3] {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
