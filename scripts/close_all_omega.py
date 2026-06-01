"""Fecha todas as posições OMEGA reconhecidas (padrão institucional por comment)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5
from modules.mt5_position_tag import filter_omega_tracked_positions, human_tag_line

mt5.initialize()
print(human_tag_line())
all_p = mt5.positions_get() or []
positions = filter_omega_tracked_positions(list(all_p))
if not positions:
    print("Nenhuma posicao OMEGA (tracked) para fechar.")
    mt5.shutdown()
    raise SystemExit()

print(f"Fechando {len(positions)} posicao(oes) OMEGA...")
for p in positions:
    tick = mt5.symbol_info_tick(p.symbol)
    if not tick:
        print(f"  #{p.ticket} ERRO: sem tick para {p.symbol}")
        continue
    order_type = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
    price = tick.bid if p.type == 0 else tick.ask
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": p.ticket,
        "symbol": p.symbol,
        "volume": p.volume,
        "type": order_type,
        "price": price,
        "deviation": 50,
        "comment": "OMEGA_CLOSE_FIX_SL_TP",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    r = mt5.order_send(req)
    status = "OK" if r and r.retcode == 10009 else f"ERRO retcode={r.retcode if r else 'None'}"
    print(f"  #{p.ticket} {p.symbol} lot={p.volume} pnl=${p.profit:.2f} → {status}")

mt5.shutdown()
print("Concluido.")
