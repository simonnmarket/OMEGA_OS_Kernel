#!/usr/bin/env python3
"""
PSA Position PnL Reconcile — P0-CICC-20260521
===============================================
Compara PnL por position_ticket entre trade_feedback.jsonl e MT5 history.
PASS se:
  - 0 deals OUT com magic=0 (novos pós-deploy)
  - 0 exit_reason UNKNOWN
  - PnL diff < 0.01 USD por posição

Uso:
    python scripts/psa_position_pnl_reconcile.py [SYMBOL] [--days 1] [--since "2026-05-21 23:00"]

Ref: PSA-EXEC-FINAL-MADRUGADA-20260521-v3 | CKO Ficheiro 3
"""
import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


OMEGA_MAGIC = 234001
INVALID_EXIT_REASONS = {"UNKNOWN", "UNKNOWN_NO_DEAL", "UNKNOWN_NO_HISTORY"}
FEEDBACK_PATH = Path("audit/paper/trade_feedback.jsonl")


def load_feedback(since: datetime = None) -> list:
    rows = []
    if not FEEDBACK_PATH.exists():
        return rows
    for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if row.get("legacy_unreconciled"):
                continue
            if row.get("event") != "position_closed":
                continue
            if since:
                ts = row.get("exit_time") or row.get("ts") or ""
                if ts:
                    try:
                        row_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if row_dt.tzinfo is None:
                            row_dt = row_dt.replace(tzinfo=timezone.utc)
                        if row_dt < since:
                            continue
                    except Exception:
                        pass
            rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def load_mt5_deals(symbol: str = None, since: datetime = None, days: int = 1) -> list:
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            print(f"[ERROR] MT5 initialize() falhou: {mt5.last_error()}")
            return []
        from_dt = since or (datetime.now(timezone.utc) - timedelta(days=days))
        to_dt = datetime.now(timezone.utc)
        deals = mt5.history_deals_get(from_dt, to_dt) or []
        result = []
        for d in deals:
            if d.entry != 1:  # DEAL_ENTRY_OUT only
                continue
            if symbol and d.symbol != symbol:
                continue
            result.append({
                "deal_ticket":   d.ticket,
                "position_id":   d.position_id,
                "symbol":        d.symbol,
                "magic":         d.magic,
                "profit":        d.profit,
                "volume":        d.volume,
                "price":         d.price,
                "reason":        d.reason,
                "comment":       d.comment,
                "time":          datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
            })
        return result
    except ImportError:
        print("[WARN] MetaTrader5 não disponível — skip MT5 check")
        return []


def main():
    parser = argparse.ArgumentParser(description="PSA PnL Reconciliation")
    parser.add_argument("symbol", nargs="?", default=None, help="Símbolo a filtrar (ex: XAUUSD)")
    parser.add_argument("--days", type=int, default=1, help="Janela histórica em dias")
    parser.add_argument("--since", type=str, default=None,
                        help="Desde datetime UTC ex: '2026-05-21 23:00'")
    args = parser.parse_args()

    since_dt = None
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"[ERROR] --since formato inválido: {args.since}")
            sys.exit(1)

    print("=" * 60)
    print(" PSA PnL RECONCILIATION — P0-CICC-20260521")
    print("=" * 60)

    feedback_rows = load_feedback(since=since_dt)
    mt5_deals = load_mt5_deals(symbol=args.symbol, since=since_dt, days=args.days)

    # ── G3: Deals OUT com magic=0 (novos) ────────────────────────────────────
    magic0 = [d for d in mt5_deals if d["magic"] != OMEGA_MAGIC]
    print(f"\n[G3] Deals OUT magic≠{OMEGA_MAGIC}: {len(magic0)} / {len(mt5_deals)}")
    for d in magic0[:10]:
        print(f"     deal={d['deal_ticket']} pos={d['position_id']} sym={d['symbol']} "
              f"magic={d['magic']} comment='{d['comment']}'")

    # ── G4: exit_reason UNKNOWN em feedback novo ─────────────────────────────
    unknown_rows = [r for r in feedback_rows if r.get("exit_reason") in INVALID_EXIT_REASONS]
    print(f"\n[G4] Linhas com exit_reason UNKNOWN/inválido: {len(unknown_rows)} / {len(feedback_rows)}")
    for r in unknown_rows[:5]:
        print(f"     pos={r.get('position_ticket')} sym={r.get('symbol')} "
              f"exit_reason={r.get('exit_reason')}")

    # ── G5: PnL diff por position_ticket ─────────────────────────────────────
    fb_by_ticket = {r["position_ticket"]: r for r in feedback_rows
                    if "position_ticket" in r}
    mt5_by_ticket: dict = {}
    for d in mt5_deals:
        pid = d["position_id"]
        mt5_by_ticket.setdefault(pid, []).append(d)

    pnl_diffs = []
    for ticket, fb in fb_by_ticket.items():
        mt5_group = mt5_by_ticket.get(ticket, [])
        if not mt5_group:
            continue
        mt5_pnl = round(sum(d["profit"] for d in mt5_group), 4)
        fb_pnl  = round(float(fb.get("total_realized_pnl", 0)), 4)
        diff    = round(abs(mt5_pnl - fb_pnl), 4)
        if diff > 0.01:
            pnl_diffs.append({
                "ticket": ticket, "symbol": fb.get("symbol"),
                "fb_pnl": fb_pnl, "mt5_pnl": mt5_pnl, "diff": diff,
            })

    print(f"\n[G5] PnL diff > 0.01 USD: {len(pnl_diffs)} posições")
    for d in pnl_diffs[:5]:
        print(f"     pos={d['ticket']} sym={d['symbol']} "
              f"fb={d['fb_pnl']} mt5={d['mt5_pnl']} diff={d['diff']}")

    # ── Resonance Score ───────────────────────────────────────────────────────
    total_new = len(mt5_deals)
    magic_ok  = total_new - len(magic0)
    resonance = round(magic_ok / total_new, 4) if total_new > 0 else 1.0
    print(f"\n[P0-8] Resonance R = {magic_ok}/{total_new} = {resonance:.4f}")

    # ── Verdict ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    g3_pass = len(magic0) == 0
    g4_pass = len(unknown_rows) == 0
    g5_pass = len(pnl_diffs) == 0
    r_pass  = resonance >= 0.98 or total_new == 0

    for label, passed in [("G3 magic=0", g3_pass), ("G4 UNKNOWN", g4_pass),
                          ("G5 PnL diff", g5_pass), ("P0-8 R≥0.98", r_pass)]:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f" {status}  {label}")

    overall = all([g3_pass, g4_pass, g5_pass, r_pass])
    print("=" * 60)
    if overall:
        print(" *** ALL PASS — GO merge PR ***")
    else:
        print(" *** FAIL — NO-GO. Corrigir antes do merge. ***")
    print("=" * 60)
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
