"""Checa posicoes abertas OMEGA e historico recente de deals."""
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

OMEGA_MAGIC = 234001

if not mt5.initialize():
    print("MT5 FAIL:", mt5.last_error())
    raise SystemExit(1)

now = datetime.now(timezone.utc)
print("=" * 60)
print("OMEGA POSICOES ABERTAS — " + now.strftime("%Y-%m-%d %H:%M:%S UTC"))
print("=" * 60)

pos = mt5.positions_get()
omega_pos = [p for p in (pos or []) if p.magic == OMEGA_MAGIC]
print("Total conta: %d | OMEGA (magic=%d): %d" % (len(pos or []), OMEGA_MAGIC, len(omega_pos)))

if omega_pos:
    for p in omega_pos:
        age_s = int(now.timestamp()) - int(p.time)
        pnl = p.profit
        dir_str = "BUY" if p.type == 0 else "SELL"
        print("  [OPEN] %s #%d %s vol=%.2f profit=%.4f age=%ds" % (
            p.symbol, p.ticket, dir_str, p.volume, pnl, age_s))
else:
    print("  Nenhuma posicao OMEGA aberta.")

print()
print("--- DEALS RECENTES (ultima 2h) ---")
t_from = now - timedelta(hours=2)
deals = mt5.history_deals_get(t_from, now) or []
omega_deals = [d for d in deals if d.magic == OMEGA_MAGIC]
print("Deals OMEGA ultimas 2h: %d" % len(omega_deals))
net_pnl = 0.0
wins = losses = 0
for d in omega_deals:
    net_pnl += d.profit + d.swap + d.commission
    if d.entry == mt5.DEAL_ENTRY_OUT:
        if d.profit > 0: wins += 1
        elif d.profit < 0: losses += 1
    ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
    print("  [%s] %s #%d entry=%s profit=%.4f" % (
        ts, d.symbol, d.ticket, ["IN","OUT","INOUT"][d.entry], d.profit))

print()
print("Net P&L deals recentes: $%.4f | Wins: %d | Losses: %d" % (net_pnl, wins, losses))
print("=" * 60)
mt5.shutdown()
