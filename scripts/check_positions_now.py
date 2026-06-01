"""Checa posicoes abertas OMEGA e historico recente de deals."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

from modules.mt5_position_tag import (
    filter_omega_tracked_positions,
    human_tag_line,
    omega_tracked_history_deals,
)

if not mt5.initialize():
    print("MT5 FAIL:", mt5.last_error())
    raise SystemExit(1)

now = datetime.now(timezone.utc)
print("=" * 60)
print("OMEGA POSICOES ABERTAS — " + now.strftime("%Y-%m-%d %H:%M:%S UTC"))
print("=" * 60)
print(human_tag_line())

pos = mt5.positions_get() or []
omega_pos = filter_omega_tracked_positions(list(pos))
print("Total conta: %d | OMEGA tracked: %d" % (len(pos), len(omega_pos)))

if omega_pos:
    for p in omega_pos:
        age_s = int(now.timestamp()) - int(p.time)
        pnl = p.profit
        dir_str = "BUY" if p.type == 0 else "SELL"
        cm = getattr(p, "comment", "") or ""
        print(
            "  [OPEN] %s #%d %s vol=%.2f profit=%.4f age=%ds comment=%r"
            % (p.symbol, p.ticket, dir_str, p.volume, pnl, age_s, cm)
        )
else:
    print("  Nenhuma posicao OMEGA rastreada.")

print()
print("--- DEALS RECENTES (ultima 2h, OMEGA tracked) ---")
t_from = now - timedelta(hours=2)
raw_deals = mt5.history_deals_get(t_from, now) or []
omega_deals = omega_tracked_history_deals(list(raw_deals))
print("Deals tracked ultimas 2h: %d (raw=%d)" % (len(omega_deals), len(raw_deals)))
net_pnl = 0.0
wins = losses = 0
for d in omega_deals:
    net_pnl += d.profit + d.swap + d.commission
    if d.entry == mt5.DEAL_ENTRY_OUT:
        if d.profit > 0:
            wins += 1
        elif d.profit < 0:
            losses += 1
    ts = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%H:%M:%S")
    print(
        "  [%s] %s #%d entry=%s profit=%.4f"
        % (ts, d.symbol, d.ticket, ["IN", "OUT", "INOUT"][d.entry], d.profit)
    )

print()
print("Net P&L deals recentes: $%.4f | Wins: %d | Losses: %d" % (net_pnl, wins, losses))
print("=" * 60)
mt5.shutdown()
