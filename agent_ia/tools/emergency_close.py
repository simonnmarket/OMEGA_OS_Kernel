"""EMERGENCY_CLOSE — Protocolo DOC-AGENT-IA-EMERGENCY-EXEC-20260427 Passo 3.
Fecha TODAS as posições MT5 com magic 234001.
"""
import MetaTrader5 as mt5
import json
from datetime import datetime

result = {"timestamp": datetime.utcnow().isoformat(), "closed": [], "errors": []}

if not mt5.initialize():
    print(f"[FATAL] MT5 init failed: {mt5.last_error()}")
    raise SystemExit(1)

OMEGA_MAGIC = 234001
all_pos = mt5.positions_get()
positions = [p for p in (all_pos or []) if p.magic == OMEGA_MAGIC]
n_total = len(all_pos) if all_pos else 0
n = len(positions)
print(f"[EMERGENCY] Posicoes abertas (total conta): {n_total}")
print(f"[EMERGENCY] Posicoes OMEGA (magic={OMEGA_MAGIC}): {n}")

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
        "magic": 234001,
        "comment": "EMERGENCY_CLOSE",
    }
    res = mt5.order_send(req)
    rc = res.retcode if res else None
    entry = {"symbol": p.symbol, "ticket": p.ticket, "volume": p.volume,
             "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL", "retcode": rc}
    result["closed"].append(entry)
    print(f"[CLOSE] {p.symbol} #{p.ticket} vol={p.volume} retcode={rc}")

# Verificacao pos
all_remaining = mt5.positions_get()
remaining = [p for p in (all_remaining or []) if p.magic == OMEGA_MAGIC]
result["remaining_count"] = len(remaining)
print(f"[VERIFY] Posicoes remanescentes: {result['remaining_count']}")

mt5.shutdown()

out = "logs/agent_ia_phase3/emergency_close_20260427.json"
import os
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(result, f, indent=2)
print(f"[SAVED] {out}")
