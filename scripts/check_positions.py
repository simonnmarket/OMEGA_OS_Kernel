"""Lista posições OMEGA reconhecidas (comment + legados)."""
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
if positions:
    print(f"{len(positions)} posicoes OMEGA (tracked):")
    for p in positions:
        info = mt5.symbol_info(p.symbol)
        pt = info.point if info else 0.001
        tp_dist = abs(p.tp - p.price_open) / pt if p.tp > 0 else 0
        sl_dist = abs(p.sl - p.price_open) / pt if p.sl > 0 else 0
        rr = round(tp_dist / sl_dist, 2) if sl_dist > 0 else 0
        direction = "BUY" if p.type == 0 else "SELL"
        cm = getattr(p, "comment", "") or ""
        print(
            f"  #{p.ticket} {p.symbol} {direction} lot={p.volume} entry={p.price_open:.3f} "
            f"SL={p.sl:.3f}({sl_dist:.0f}pts) TP={p.tp:.3f}({tp_dist:.0f}pts) "
            f"R:R=1:{rr}  pnl=${p.profit:.2f}  comment={cm!r}"
        )
else:
    print("Nenhuma posicao OMEGA rastreada.")
mt5.shutdown()
