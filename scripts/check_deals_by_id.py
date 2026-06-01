"""Busca deals OMEGA por ID e por janela ampliada."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

from modules.mt5_position_tag import human_tag_line, is_omega_tracked_deal

if not mt5.initialize():
    print("MT5 FAIL:", mt5.last_error())
    raise SystemExit(1)

acct = mt5.account_info()
print(human_tag_line())
print(
    "Login: %d | Servidor: %s | Balance: %.2f | Equity: %.2f"
    % (acct.login, acct.server, acct.balance, acct.equity)
)

now = datetime.now(timezone.utc)

t_from = datetime(2026, 4, 28, 0, 0, 0, tzinfo=timezone.utc)
t_to = now + timedelta(hours=1)

print("=" * 65)
print("BUSCA: %s -> %s" % (t_from.strftime("%H:%M UTC"), t_to.strftime("%H:%M UTC")))
print("=" * 65)

all_deals = mt5.history_deals_get(t_from, t_to) or []
print("Total deals hoje: %d" % len(all_deals))

by_magic = {}
for d in all_deals:
    by_magic[d.magic] = by_magic.get(d.magic, 0) + 1
for mag, cnt in sorted(by_magic.items()):
    mark = ""
    for d in all_deals:
        if d.magic == mag and is_omega_tracked_deal(d):
            mark = " <<< OMEGA tracked"
            break
    print("  magic=%d: %d deals%s" % (mag, cnt, mark))

known_deals = [183692590, 183692614]
print()
print("--- BUSCA POR DEAL ID ---")
for did in known_deals:
    result = mt5.history_deals_get(position=did)
    if result:
        for d in result:
            ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
            print(
                "[FOUND] deal=%d sym=%s magic=%d entry=%s profit=%.4f ts=%s"
                % (d.deal, d.symbol, d.magic, d.entry, d.profit, ts)
            )
    else:
        print("[NOT FOUND by position] deal_id=%d — tentando por ticket" % did)

print()
print("--- XAUUSD deals hoje ---")
xau_deals = [d for d in all_deals if d.symbol == "XAUUSD"]
print("XAUUSD: %d deals" % len(xau_deals))
for d in xau_deals[-10:]:
    ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
    om = " [OMEGA]" if is_omega_tracked_deal(d) else ""
    print(
        "  [%s] deal=%d magic=%d entry=%s profit=%.4f vol=%.2f%s"
        % (ts, d.deal, d.magic, d.entry, d.profit, d.volume, om)
    )

mt5.shutdown()
