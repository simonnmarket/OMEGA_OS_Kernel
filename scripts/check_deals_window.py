"""Diagnostico preciso: deals na janela exata do run OMEGA 14:42-14:50 CET."""
import MetaTrader5 as mt5
from datetime import datetime, timezone

if not mt5.initialize():
    print("MT5 FAIL:", mt5.last_error())
    raise SystemExit(1)

acct = mt5.account_info()
print("Login=%d  Servidor=%s  Balance=%.2f  Equity=%.2f" % (
    acct.login, acct.server, acct.balance, acct.equity))

# Janela exata do run: 14:42 a 14:50 CET = 12:42 a 12:50 UTC
t_from = datetime(2026, 4, 28, 12, 42, 0, tzinfo=timezone.utc)
t_to   = datetime(2026, 4, 28, 13, 15, 0, tzinfo=timezone.utc)

deals = mt5.history_deals_get(t_from, t_to) or []
print("Total deals 12:42-13:15 UTC: %d" % len(deals))

by_sym = {}
by_magic = {}
for d in deals:
    by_sym[d.symbol]   = by_sym.get(d.symbol, 0) + 1
    by_magic[d.magic]  = by_magic.get(d.magic, 0) + 1

print("Por magic: %s" % dict(sorted(by_magic.items())))
print("Por simbolo: %s" % dict(sorted(by_sym.items())))

print()
# GER40 e XAUUSD na janela
for sym in ["XAUUSD", "GER40"]:
    sym_deals = [d for d in deals if d.symbol == sym]
    print("%s: %d deals" % (sym, len(sym_deals)))
    for d in sym_deals[:20]:
        ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
        try:
            entry_map = {0: "IN", 1: "OUT", 2: "INOUT"}
            entry_str = entry_map.get(d.entry, str(d.entry))
        except Exception:
            entry_str = "?"
        print("  [%s] ticket=%d magic=%d entry=%s profit=%.4f vol=%.4f" % (
            ts, d.ticket if hasattr(d,'ticket') else 0,
            d.magic, entry_str, d.profit, d.volume))

mt5.shutdown()
