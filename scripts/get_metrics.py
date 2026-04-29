import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

mt5.initialize()
acc = mt5.account_info()
print(f"Equity: {acc.equity}  Balance: {acc.balance}  Profit: {acc.profit}  Currency: {acc.currency}")

deals = mt5.history_deals_get(
    datetime.now(timezone.utc) - timedelta(days=2),
    datetime.now(timezone.utc)
)
print(f"Deals historico 48h: {len(deals) if deals else 0}")

if deals:
    omega = [d for d in deals if d.magic == 234001 and d.entry == 1]  # entry=1 = saidas
    wins   = [d for d in omega if d.profit > 0]
    losses = [d for d in omega if d.profit < 0]
    total_pnl = sum(d.profit for d in omega)
    print(f"Trades fechados OMEGA: {len(omega)}")
    print(f"  Wins={len(wins)}  Losses={len(losses)}")
    wr = len(wins)/len(omega) if omega else 0
    print(f"  Win Rate={wr:.2%}")
    print(f"  Total PnL: USD {total_pnl:.2f}")
    if wins and losses:
        avg_win  = sum(d.profit for d in wins) / len(wins)
        avg_loss = sum(abs(d.profit) for d in losses) / len(losses)
        print(f"  Avg Win: USD {avg_win:.2f}  Avg Loss: USD {avg_loss:.2f}")
        print(f"  Profit Factor: {sum(d.profit for d in wins)/max(sum(abs(d.profit) for d in losses),0.01):.2f}")

mt5.shutdown()
