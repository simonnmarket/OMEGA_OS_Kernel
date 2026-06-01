"""P&L FORENSE — Auditoria das 480 operações do overnight N=120.
Coleta history MT5 da janela 2026-04-26 22:12 → 23:00 UTC+02 (= 20:12-21:00 UTC).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5
from datetime import datetime, timezone
import json
from collections import defaultdict
import statistics as st

from modules.mt5_position_tag import omega_tracked_history_deals, human_tag_line

if not mt5.initialize():
    raise SystemExit(f"MT5 init failed: {mt5.last_error()}")

print(human_tag_line())

# Janela ampla cobrindo overnight (UTC). Wrapper iniciou 22:12 local UTC+02 = 20:12 UTC.
t_from = datetime(2026, 4, 26, 19, 0, tzinfo=timezone.utc)
t_to   = datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc)

_raw = mt5.history_deals_get(t_from, t_to) or []
deals = omega_tracked_history_deals(list(_raw))
print(f"[INFO] Deals OMEGA tracked na janela: {len(deals)} (raw={len(_raw)})")

# Agrupar por position_id (entry+exit)
positions = defaultdict(list)
for d in deals:
    positions[d.position_id].append(d)

closed = []
for pid, dlist in positions.items():
    dlist.sort(key=lambda x: x.time)
    if len(dlist) < 2:
        continue
    entry = dlist[0]
    exit_ = dlist[-1]
    profit_total = sum(d.profit for d in dlist)
    swap_total   = sum(d.swap   for d in dlist)
    comm_total   = sum(d.commission for d in dlist)
    net = profit_total + swap_total + comm_total
    closed.append({
        "position_id": pid,
        "symbol": entry.symbol,
        "volume": entry.volume,
        "entry_time": datetime.fromtimestamp(entry.time, tz=timezone.utc).isoformat(),
        "exit_time":  datetime.fromtimestamp(exit_.time, tz=timezone.utc).isoformat(),
        "duration_s": exit_.time - entry.time,
        "type": "BUY" if entry.type == mt5.DEAL_TYPE_BUY else "SELL",
        "entry_price": entry.price,
        "exit_price": exit_.price,
        "profit": profit_total,
        "swap": swap_total,
        "commission": comm_total,
        "net": net,
        "comment_exit": exit_.comment,
    })

mt5.shutdown()

closed.sort(key=lambda x: x["entry_time"])

# Agregados
total = len(closed)
gross_profit = sum(c["profit"]    for c in closed)
gross_swap   = sum(c["swap"]      for c in closed)
gross_comm   = sum(c["commission"] for c in closed)
gross_net    = sum(c["net"]       for c in closed)
wins   = [c for c in closed if c["net"] > 0]
losses = [c for c in closed if c["net"] < 0]
flats  = [c for c in closed if c["net"] == 0]
nets = [c["net"] for c in closed]

per_symbol = defaultdict(lambda: {"n": 0, "net": 0.0, "wins": 0, "losses": 0,
                                  "best": -1e18, "worst": 1e18, "profit": 0.0,
                                  "swap": 0.0, "comm": 0.0})
for c in closed:
    s = per_symbol[c["symbol"]]
    s["n"]      += 1
    s["net"]    += c["net"]
    s["profit"] += c["profit"]
    s["swap"]   += c["swap"]
    s["comm"]   += c["commission"]
    if c["net"] > 0: s["wins"] += 1
    if c["net"] < 0: s["losses"] += 1
    s["best"]  = max(s["best"],  c["net"])
    s["worst"] = min(s["worst"], c["net"])

# Per-type (BUY/SELL)
per_type = defaultdict(lambda: {"n": 0, "net": 0.0, "wins": 0})
for c in closed:
    t = c["type"]
    per_type[t]["n"]   += 1
    per_type[t]["net"] += c["net"]
    if c["net"] > 0: per_type[t]["wins"] += 1

# Distribuição de comments (exit reason)
exit_reasons = defaultdict(int)
for c in closed:
    exit_reasons[c["comment_exit"] or "(empty)"] += 1

# Duração
durations = [c["duration_s"] for c in closed]

print("\n" + "="*70)
print(f"OVERNIGHT P&L AUDIT — N={total} operações fechadas")
print("="*70)
print(f"Gross profit (price)  : ${gross_profit:+.2f}")
print(f"Gross swap            : ${gross_swap:+.2f}")
print(f"Gross commission      : ${gross_comm:+.2f}")
print(f"NET TOTAL             : ${gross_net:+.2f}")
print(f"Wins / Losses / Flats : {len(wins)} / {len(losses)} / {len(flats)}")
if total:
    print(f"Win rate              : {100*len(wins)/total:.2f}%")
    print(f"Avg net per trade     : ${gross_net/total:+.4f}")
    print(f"Median net            : ${st.median(nets):+.4f}")
    print(f"Worst trade           : ${min(nets):+.4f}")
    print(f"Best trade            : ${max(nets):+.4f}")
    print(f"Avg duration          : {st.mean(durations):.1f}s  (median {st.median(durations):.0f}s)")

print("\n--- POR SÍMBOLO ---")
for sym, s in sorted(per_symbol.items()):
    wr = 100*s["wins"]/s["n"] if s["n"] else 0
    print(f"{sym:8s} n={s['n']:3d}  win_rate={wr:5.1f}%  "
          f"profit=${s['profit']:+.2f} swap=${s['swap']:+.2f} comm=${s['comm']:+.2f} "
          f"NET=${s['net']:+.2f}  best=${s['best']:+.2f}  worst=${s['worst']:+.2f}")

print("\n--- POR TIPO ---")
for t, x in per_type.items():
    wr = 100*x["wins"]/x["n"] if x["n"] else 0
    print(f"{t:5s} n={x['n']:3d}  win_rate={wr:5.1f}%  NET=${x['net']:+.2f}")

print("\n--- EXIT COMMENTS ---")
for r, n in sorted(exit_reasons.items(), key=lambda x: -x[1]):
    print(f"  {r:30s} {n:4d}  ({100*n/total:.1f}%)")

# Save
out = {
    "audit_id": "PNL_OVERNIGHT_20260427",
    "window_utc": [t_from.isoformat(), t_to.isoformat()],
    "total_closed": total,
    "gross_profit_price": round(gross_profit, 4),
    "gross_swap": round(gross_swap, 4),
    "gross_commission": round(gross_comm, 4),
    "net_total": round(gross_net, 4),
    "wins": len(wins), "losses": len(losses), "flats": len(flats),
    "win_rate_pct": round(100*len(wins)/total, 2) if total else 0,
    "avg_net": round(gross_net/total, 4) if total else 0,
    "median_net": round(st.median(nets), 4) if nets else 0,
    "worst": round(min(nets), 4) if nets else 0,
    "best": round(max(nets), 4) if nets else 0,
    "per_symbol": {k: {kk: (round(vv,4) if isinstance(vv,float) else vv) for kk,vv in v.items()}
                   for k,v in per_symbol.items()},
    "per_type": {k: dict(v) for k,v in per_type.items()},
    "exit_reasons": dict(exit_reasons),
    "trades": closed,
}
import os
os.makedirs("logs/agent_ia_phase3", exist_ok=True)
fp = "logs/agent_ia_phase3/PNL_OVERNIGHT_AUDIT_20260427.json"
with open(fp, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)
print(f"\n[SAVED] {fp}")
