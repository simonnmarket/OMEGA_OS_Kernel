import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

from modules.mt5_position_tag import human_tag_line, omega_tracked_history_deals

mt5.initialize()
acc = mt5.account_info()
print(human_tag_line())
print(f"Equity: {acc.equity}  Balance: {acc.balance}  Profit: {acc.profit}  Currency: {acc.currency}")

deals = mt5.history_deals_get(
    datetime.now(timezone.utc) - timedelta(days=2),
    datetime.now(timezone.utc),
) or []
tracked = omega_tracked_history_deals(list(deals))
print(f"Deals historico 48h: raw={len(deals)} | OMEGA tracked={len(tracked)}")

if tracked:
    omega = [d for d in tracked if d.entry == 1]  # entry=1 = saidas
    wins = [d for d in omega if d.profit > 0]
    losses = [d for d in omega if d.profit < 0]
    total_pnl = sum(d.profit for d in omega)
    print(f"Trades fechados OMEGA (saidas): {len(omega)}")
    print(f"  Wins={len(wins)}  Losses={len(losses)}")
    wr = len(wins) / len(omega) if omega else 0
    print(f"  Win Rate={wr:.2%}")
    print(f"  Total PnL: USD {total_pnl:.2f}")
    if wins and losses:
        avg_win = sum(d.profit for d in wins) / len(wins)
        avg_loss = sum(abs(d.profit) for d in losses) / len(losses)
        print(f"  Avg Win: USD {avg_win:.2f}  Avg Loss: USD {avg_loss:.2f}")
        print(
            f"  Profit Factor: {sum(d.profit for d in wins) / max(sum(abs(d.profit) for d in losses), 0.01):.2f}"
        )

mt5.shutdown()
