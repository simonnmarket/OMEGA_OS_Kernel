"""Localiza deal ticket 183692590 e 183692614 no historico da conta."""
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

if not mt5.initialize():
    print("MT5 FAIL:", mt5.last_error())
    raise SystemExit(1)

acct = mt5.account_info()
print("Login=%d  Balance=%.2f" % (acct.login, acct.balance))

TARGET_TICKETS = {183692590, 183692614}

# Busca janela ampla hoje
t_from = datetime(2026, 4, 28, 0, 0, 0, tzinfo=timezone.utc)
t_to   = datetime.now(timezone.utc) + timedelta(hours=1)

deals = mt5.history_deals_get(t_from, t_to) or []
print("Total deals hoje: %d" % len(deals))

found = [d for d in deals if d.ticket in TARGET_TICKETS]
print("Deals target encontrados: %d" % len(found))
for d in found:
    ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
    print("  ticket=%d sym=%s magic=%d profit=%.4f ts=%s" % (
        d.ticket, d.symbol, d.magic, d.profit, ts))

# Faixa de tickets ao redor de 183692590
nearby = [d for d in deals if 183692500 <= d.ticket <= 183692700]
print()
print("Deals com ticket em [183692500-183692700]: %d" % len(nearby))
for d in nearby[:20]:
    ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
    print("  ticket=%d sym=%s magic=%d entry=%d profit=%.4f" % (
        d.ticket, d.symbol, d.magic, d.entry, d.profit))

# Ticket max e min
if deals:
    tickets = [d.ticket for d in deals]
    print()
    print("Ticket range hoje: min=%d max=%d" % (min(tickets), max(tickets)))

mt5.shutdown()
