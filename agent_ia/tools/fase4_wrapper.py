"""
PSA-WIND | Fase 4 wrapper — A/B real cripto (paper) com >=50 trades por fase.

Para cada ciclo:
  1. invoca core_engines/shadow_loop.py como subprocesso
  2. fecha posicoes OMEGA cripto criadas (slate limpo entre ciclos)
  3. agrega metricas (trades, hit_rate, latencias, retcodes, KS)

Uso:
  python agent_ia/tools/fase4_wrapper.py --label BASELINE --cycles 30
  python agent_ia/tools/fase4_wrapper.py --label IA_ON    --cycles 30

Saidas (logs/agent_ia_phase3/fase4_<label>_<ts>/):
  - cycle_NN.log
  - paper_summary_NN.json
  - fase4_<label>_aggregate.json
  - fase4_<label>_aggregate.sha3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parents[2]
SHADOW_LOOP = ROOT / "core_engines" / "shadow_loop.py"
AUDIT_PAPER = ROOT / "audit" / "paper"
LOGS_DIR = ROOT / "logs" / "agent_ia_phase3"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

OMEGA_MAGIC = 234001
CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD"]
TIMEFRAMES = ["H1", "H4"]
EQUITY = 10000.0


def close_crypto_omega(label: str) -> List[Dict[str, Any]]:
    if not mt5.initialize():
        return [{"error": "mt5_init_failed"}]
    try:
        positions = mt5.positions_get() or []
        results = []
        for p in positions:
            if p.magic != OMEGA_MAGIC or p.symbol not in CRYPTO_SYMBOLS:
                continue
            tk = mt5.symbol_info_tick(p.symbol)
            if tk is None:
                results.append({"ticket": p.ticket, "symbol": p.symbol, "reason": "no_tick"})
                continue
            if p.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tk.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tk.ask
            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": p.ticket,
                "symbol": p.symbol,
                "volume": p.volume,
                "type": order_type,
                "price": price,
                "deviation": 100,
                "magic": OMEGA_MAGIC,
                "comment": f"FASE4_CLOSE_{label}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            r = mt5.order_send(req)
            results.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "retcode": r.retcode if r else None,
                "comment": r.comment if r else None,
            })
        return results
    finally:
        mt5.shutdown()


def run_shadow_loop(cycle_log: Path) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    cmd = [
        sys.executable, str(SHADOW_LOOP),
        "--mode", "paper",
        "--ativos", *CRYPTO_SYMBOLS,
        "--timeframes", *TIMEFRAMES,
        "--equity", str(EQUITY),
    ]
    with open(cycle_log, "w", encoding="utf-8") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=str(ROOT))
    return proc.returncode


def parse_paper_summary(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def aggregate(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_signals = total_executed = total_skipped = 0
    hit_rates: List[float] = []
    latencies: List[float] = []
    max_lats: List[float] = []
    slippages: List[float] = []
    ks_triggered = 0
    by_asset: Dict[str, int] = {}
    by_action: Dict[str, int] = {}
    retcodes: Dict[str, int] = {}
    for s in summaries:
        if not s:
            continue
        ks_triggered += 1 if s.get("kill_switch") else 0
        os_ = s.get("online_stats", {})
        total_signals += os_.get("total_signals", 0)
        total_executed += os_.get("executed", 0)
        total_skipped += os_.get("skipped", 0)
        if os_.get("avg_hit_rate_134"):
            hit_rates.append(float(os_["avg_hit_rate_134"]))
        if os_.get("avg_latency_ms"):
            latencies.append(float(os_["avg_latency_ms"]))
        if os_.get("max_latency_ms"):
            max_lats.append(float(os_["max_latency_ms"]))
        if os_.get("avg_slippage_pts") is not None:
            slippages.append(float(os_["avg_slippage_pts"]))
        for r in s.get("results", []) or []:
            asset = r.get("asset")
            if asset:
                by_asset[asset] = by_asset.get(asset, 0) + (1 if r.get("status") in ("BUY", "SELL", "ORDER_DONE") or r.get("retcode") == 10009 else 0)
            action = r.get("status", "UNKNOWN")
            by_action[action] = by_action.get(action, 0) + 1
            rc = r.get("retcode")
            if rc is not None:
                retcodes[str(rc)] = retcodes.get(str(rc), 0) + 1

    def _percentile(vals: List[float], pct: float) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        k = max(0, min(len(s) - 1, int(round(pct / 100.0 * (len(s) - 1)))))
        return s[k]

    total_trades = sum(by_asset.values())
    max_concentration = (max(by_asset.values()) / total_trades) if total_trades > 0 else 0.0
    return {
        "cycles": len(summaries),
        "total_signals": total_signals,
        "total_executed": total_executed,
        "total_skipped": total_skipped,
        "total_trades_per_asset": by_asset,
        "total_trades": total_trades,
        "by_action": by_action,
        "retcodes": retcodes,
        "hit_rate_avg": round(sum(hit_rates) / len(hit_rates), 4) if hit_rates else 0.0,
        "hit_rate_min": round(min(hit_rates), 4) if hit_rates else 0.0,
        "latency_ms_avg": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "latency_ms_max": round(max(max_lats), 2) if max_lats else 0.0,
        "latency_ms_p95": round(_percentile(max_lats, 95), 2) if max_lats else 0.0,
        "slippage_avg_pts": round(sum(slippages) / len(slippages), 4) if slippages else 0.0,
        "kill_switch_triggers": ks_triggered,
        "max_concentration_pct": round(max_concentration * 100, 2),
        "max_concentration_asset": max(by_asset, key=by_asset.get) if by_asset else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, choices=["BASELINE", "IA_ON"])
    ap.add_argument("--cycles", type=int, default=30)
    ap.add_argument("--sleep-after-run", type=float, default=2.0)
    ap.add_argument("--sleep-after-close", type=float, default=2.0)
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = LOGS_DIR / f"fase4_{args.label}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[FASE4] label={args.label} cycles={args.cycles} out_dir={out_dir}")

    summaries: List[Dict[str, Any]] = []
    closes: List[List[Dict[str, Any]]] = []

    for i in range(1, args.cycles + 1):
        cycle_log = out_dir / f"cycle_{i:02d}.log"
        rc = run_shadow_loop(cycle_log)
        time.sleep(args.sleep_after_run)
        ps_src = AUDIT_PAPER / "paper_summary.json"
        ps_dst = out_dir / f"paper_summary_{i:02d}.json"
        if ps_src.exists():
            shutil.copy(ps_src, ps_dst)
            summaries.append(parse_paper_summary(ps_dst))
        else:
            summaries.append({})
        closed = close_crypto_omega(args.label)
        closes.append(closed)
        time.sleep(args.sleep_after_close)
        n_closed = sum(1 for c in closed if c.get("retcode") == 10009)
        last = summaries[-1].get("online_stats", {}) if summaries[-1] else {}
        print(f"[CYCLE {i:02d}/{args.cycles}] rc={rc} executed={last.get('executed', 0)} hit={last.get('avg_hit_rate_134', 0)} lat_max={last.get('max_latency_ms', 0)} closed={n_closed}")

    agg = aggregate(summaries)
    agg["label"] = args.label
    agg["timestamp_utc"] = ts
    agg["cycles_requested"] = args.cycles
    agg["closes_per_cycle"] = [
        {"cycle": i + 1, "n_success": sum(1 for c in cl if c.get("retcode") == 10009)}
        for i, cl in enumerate(closes)
    ]

    agg_path = out_dir / f"fase4_{args.label}_aggregate.json"
    with open(agg_path, "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)
    sha = hashlib.sha3_256(open(agg_path, "rb").read()).hexdigest()
    (out_dir / f"fase4_{args.label}_aggregate.sha3").write_text(sha + "\n", encoding="utf-8")

    print("=" * 70)
    print(f"[FASE4 {args.label}] AGGREGATE: {agg_path}")
    print(f"  cycles={agg['cycles']} total_trades={agg['total_trades']} executed={agg['total_executed']}")
    print(f"  hit_rate_avg={agg['hit_rate_avg']} latency_p95={agg['latency_ms_p95']}ms latency_max={agg['latency_ms_max']}ms")
    print(f"  ks_triggers={agg['kill_switch_triggers']} max_concentration={agg['max_concentration_pct']}% on {agg['max_concentration_asset']}")
    print(f"  retcodes={agg['retcodes']}")
    print(f"  SHA3={sha}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
