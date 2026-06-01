"""EMERGENCY_CLOSE — Protocolo DOC-AGENT-IA-EMERGENCY-EXEC-20260427 Passo 3.
Fecha TODAS as posições OMEGA rastreadas (comment / escala / magic legado).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.mt5_position_tag import filter_omega_tracked_positions, human_tag_line

result = {"timestamp": datetime.utcnow().isoformat(), "closed": [], "errors": []}

if not mt5.initialize():
    print(f"[FATAL] MT5 init failed: {mt5.last_error()}")
    raise SystemExit(1)

print(human_tag_line())
all_pos = mt5.positions_get()
positions = filter_omega_tracked_positions(list(all_pos or []))
n_total = len(all_pos) if all_pos else 0
n = len(positions)
print(f"[EMERGENCY] Posicoes abertas (total conta): {n_total}")
print(f"[EMERGENCY] Posicoes OMEGA (tracked): {n}")

for p in positions:
    tick = mt5.symbol_info_tick(p.symbol)
    if not tick:
        msg = f"Sem tick para {p.symbol} #{p.ticket}"
        print(f"[WARN] {msg}")
        result["errors"].append(msg)
        continue
    price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
    order_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": p.symbol,
        "volume": p.volume,
        "type": order_type,
        "position": p.ticket,
        "price": price,
        "deviation": 20,
        "comment": "EMERGENCY_CLOSE",
    }
    res = mt5.order_send(req)
    rc = res.retcode if res else None
    entry = {"symbol": p.symbol, "ticket": p.ticket, "volume": p.volume,
             "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL", "retcode": rc}
    result["closed"].append(entry)
    print(f"[CLOSE] {p.symbol} #{p.ticket} vol={p.volume} retcode={rc}")

all_remaining = mt5.positions_get()
remaining = filter_omega_tracked_positions(list(all_remaining or []))
result["remaining_count"] = len(remaining)
print(f"[VERIFY] Posicoes OMEGA remanescentes: {result['remaining_count']}")

mt5.shutdown()

out = "logs/agent_ia_phase3/emergency_close_20260427.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(result, f, indent=2)
print(f"[SAVED] {out}")
