"""Historico amplo de deals para diagnostico."""
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

OMEGA_MAGIC = 234001

if not mt5.initialize():
    print("MT5 FAIL:", mt5.last_error())
    raise SystemExit(1)

now = datetime.now(timezone.utc)
t_from = now - timedelta(hours=4)

print("=" * 65)
print("OMEGA DEALS — janela 4h (%s UTC)" % t_from.strftime("%H:%M"))
print("=" * 65)

deals = mt5.history_deals_get(t_from, now) or []
print("Total deals conta (4h): %d" % len(deals))

omega_deals = [d for d in deals if d.magic == OMEGA_MAGIC]
other_deals  = [d for d in deals if d.magic != OMEGA_MAGIC]
print("  OMEGA magic=%d: %d deals" % (OMEGA_MAGIC, len(omega_deals)))
print("  Outros EAs: %d deals" % len(other_deals))

print()
print("--- OMEGA DEALS ---")
net_pnl = 0.0
wins = losses = opens = 0
symbols_seen = {}
for d in omega_deals:
    net_pnl += d.profit + d.swap + d.commission
    ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
    entry_str = ["IN","OUT","INOUT"][d.entry] if d.entry <= 2 else str(d.entry)
    print("  [%s] %s #%d entry=%s profit=%.4f vol=%.2f" % (
        ts, d.symbol, d.ticket, entry_str, d.profit, d.volume))
    symbols_seen[d.symbol] = symbols_seen.get(d.symbol, 0) + 1
    if d.entry == mt5.DEAL_ENTRY_IN:   opens += 1
    if d.entry == mt5.DEAL_ENTRY_OUT:
        if d.profit >= 0: wins += 1
        else: losses += 1

if not omega_deals:
    print("  Nenhum deal OMEGA encontrado.")

print()
print("Resumo: opens=%d closes(win=%d loss=%d) net_pnl=$%.4f" % (opens, wins, losses, net_pnl))
print("Simbolos: %s" % symbols_seen)

# Verificar saldo conta
acct = mt5.account_info()
if acct:
    print()
    print("--- CONTA ---")
    print("Balance: %.2f | Equity: %.2f | Margin: %.2f | FreeMargin: %.2f" % (
        acct.balance, acct.equity, acct.margin, acct.margin_free))
    print("Servidor: %s | Login: %d | Moeda: %s" % (acct.server, acct.login, acct.currency))

mt5.shutdown()
