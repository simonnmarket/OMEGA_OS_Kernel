#!/usr/bin/env python3
"""PSA — Gera snapshot textual MT5 para FORCE NOW 4H (F6 textual)."""
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audit" / "forensic" / "FORCE_NOW_20260601" / "mt5_snapshot_4h.txt"

sys.path.insert(0, str(ROOT))
import MetaTrader5 as mt5


def main():
    lines = []
    lines.append("=" * 70)
    lines.append("MT5 SNAPSHOT — FORCE NOW 4H (textual)")
    lines.append(f"UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    lines.append("=" * 70)

    if not mt5.initialize():
        lines.append("MT5 INIT FAILED")
        OUT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Saved: {OUT}")
        return 1

    ai = mt5.account_info()
    if ai:
        lines.append("")
        lines.append("--- ACCOUNT INFO ---")
        lines.append(f"Login: {ai.login} | Server: {ai.server} | Currency: {ai.currency}")
        lines.append(f"Balance: ${ai.balance:.2f} | Equity: ${ai.equity:.2f}")
        lines.append(f"Margin: ${ai.margin:.2f} | Free: ${ai.margin_free:.2f}")

    pos = mt5.positions_get()
    lines.append("")
    lines.append(f"--- OPEN POSITIONS: {len(pos) if pos else 0} ---")
    if pos:
        lines.append(f"{'Ticket':<10} {'Symbol':<8} {'Type':<6} {'Vol':<6} {'Open':<10} {'Price':<10} {'SL':<10} {'TP':<10} {'Profit':<10} {'Swap':<8}")
        lines.append("-" * 90)
        for p in pos:
            t = "BUY" if p.type == 0 else "SELL"
            lines.append(
                f"{p.ticket:<10} {p.symbol:<8} {t:<6} {p.volume:<6.2f} "
                f"{p.price_open:<10.5f} {p.price_current:<10.5f} {p.sl:<10.5f} "
                f"{p.tp:<10.5f} {p.profit:<10.2f} {p.swap:<8.2f}"
            )
            pos_deals = mt5.history_deals_get(position=p.ticket)
            if pos_deals:
                for d in pos_deals:
                    lines.append(
                        f"  -> Deal #{d.ticket} order={d.order} vol={d.volume:.2f} "
                        f"price={d.price:.5f} profit={d.profit:.2f} swap={d.swap:.2f} "
                        f"comm={d.commission:.2f} comment={d.comment}"
                    )

    from_date = datetime.datetime(2026, 5, 31, tzinfo=datetime.timezone.utc)
    to_date = datetime.datetime.now(datetime.timezone.utc)
    all_orders = mt5.history_orders_get(from_date, to_date)
    lines.append("")
    lines.append(f"--- HISTORY ORDERS (today): {len(all_orders) if all_orders else 0} ---")
    if all_orders:
        for o in all_orders:
            t = "BUY" if o.type == 0 else "SELL"
            lines.append(
                f"Order #{o.ticket} {o.symbol} {t} vol={o.volume_initial:.2f} "
                f"state={o.state} comment={o.comment}"
            )

    mt5.shutdown()

    lines.append("")
    lines.append("=" * 70)
    lines.append("F6 IMPEDIMENTO: Screenshots GUI")
    lines.append("=" * 70)
    lines.append("Ambiente: Terminal/bash headless (sem GUI)")
    lines.append("MT5 GUI: Disponivel no Windows desktop do CEO")
    lines.append("Acao: CEO captura 3 screenshots manualmente quando voltar:")
    lines.append("  1. Tab Trade — lista posicoes apos 4h")
    lines.append("  2. Ordem indice com TP >= $25 em USD")
    lines.append("  3. History — ultimos 10 deals com profit column")
    lines.append("Estado: NAO BLOQUEIA PASS se F4/F5 + snapshot textual OK")
    lines.append("=" * 70)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
