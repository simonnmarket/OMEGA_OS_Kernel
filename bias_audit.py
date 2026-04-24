"""V10 Bias Audit — Collect metrics from MT5 positions + paper reports"""
import json, glob, os
from datetime import datetime, timezone

# ── MT5 Ground Truth ──
import MetaTrader5 as mt5
mt5.initialize()
positions = mt5.positions_get()
mt5_rows = []
buy = sell = 0
symbols_seen = set()
total_profit = 0.0
slippages = []
latencies = []

if positions:
    for p in positions:
        if p.magic != 234001:
            continue
        side = "BUY" if p.type == 0 else "SELL"
        if p.type == 0: buy += 1
        else: sell += 1
        symbols_seen.add(p.symbol)
        total_profit += p.profit
        mt5_rows.append({
            "symbol": p.symbol, "direction": side,
            "lot": p.volume, "price_open": p.price_open,
            "sl": p.sl, "tp": p.tp, "profit": p.profit,
            "magic": p.magic, "ticket": p.ticket,
        })

# ── Paper Reports ──
reports = sorted(glob.glob("audit/paper/*/PaperReport_*.json"))
report_rows = []
for r in reports:
    d = json.load(open(r, encoding="utf-8"))
    ex = d.get("execution", {})
    report_rows.append({
        "asset": d.get("asset", "?"),
        "tf": d.get("timeframe", "?"),
        "action": d.get("signal", {}).get("action", "?"),
        "retcode": ex.get("retcode", "?"),
        "retcode_str": ex.get("retcode_str", "?"),
        "slippage_pts": ex.get("slippage_pts", 0),
        "latency_ms": ex.get("latency_ms", 0),
        "fill_price": ex.get("fill_price", 0),
    })
    slippages.append(ex.get("slippage_pts", 0))
    latencies.append(ex.get("latency_ms", 0))

mt5.shutdown()

total = buy + sell

print("=" * 70)
print("  V10 BIAS & STRESS AUDIT")
print("=" * 70)
print(f"\n  MT5 OMEGA Positions (magic=234001):")
for row in mt5_rows:
    print(f"    {row['symbol']:8s} | {row['direction']:4s} | lot={row['lot']:.2f} | open={row['price_open']:.5f} | pnl={row['profit']:+.2f}")

print(f"\n  ── Direction Distribution ──")
print(f"    BUY:  {buy}")
print(f"    SELL: {sell}")
print(f"    Total: {total}")
if total > 0:
    pct_buy = buy / total * 100
    pct_sell = sell / total * 100
    print(f"    Ratio: {pct_buy:.1f}% BUY / {pct_sell:.1f}% SELL")
    if buy > 0 and sell > 0:
        verdict = "NEUTRAL" if abs(buy - sell) <= 1 else "ACCEPTABLE"
        print(f"    VERDICT: ✅ {verdict} — Both sides active")
    elif buy == 0:
        print("    VERDICT: ⚠️ SELL-ONLY (check momentum direction logic)")
    elif sell == 0:
        print("    VERDICT: ⚠️ BUY-ONLY BIAS DETECTED")

print(f"\n  ── Symbol Coverage ──")
print(f"    Symbols: {sorted(symbols_seen)}")
print(f"    Count: {len(symbols_seen)}")
print(f"    Multi-asset: {'✅ YES' if len(symbols_seen) > 1 else '⚠️ SINGLE ASSET'}")

print(f"\n  ── Execution Quality ──")
if latencies:
    print(f"    Avg latency: {sum(latencies)/len(latencies):.1f} ms")
    print(f"    Max latency: {max(latencies):.1f} ms")
    print(f"    Avg slippage: {sum(slippages)/len(slippages):.2f} pts")
    print(f"    Max slippage: {max(slippages):.2f} pts")
print(f"    Total PnL: {total_profit:+.2f}")

print(f"\n  ── Retcode Summary ──")
retcodes = {}
for rr in report_rows:
    rc = rr.get("retcode_str", "?")
    retcodes[rc] = retcodes.get(rc, 0) + 1
for rc, cnt in retcodes.items():
    print(f"    {rc}: {cnt}")

# Save
summary = {
    "audit_type": "V10_BIAS_STRESS",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "direction": {"buy": buy, "sell": sell, "total": total,
                  "pct_buy": round(buy/total*100,1) if total else 0},
    "symbols": sorted(symbols_seen),
    "multi_asset": len(symbols_seen) > 1,
    "both_sides_active": buy > 0 and sell > 0,
    "execution": {
        "avg_latency_ms": round(sum(latencies)/len(latencies), 1) if latencies else 0,
        "max_latency_ms": round(max(latencies), 1) if latencies else 0,
        "avg_slippage_pts": round(sum(slippages)/len(slippages), 2) if slippages else 0,
        "total_pnl": round(total_profit, 2),
    },
    "retcodes": retcodes,
    "positions": mt5_rows,
    "reports": report_rows,
}
os.makedirs("audit", exist_ok=True)
with open("audit/bias_audit_v10.json", "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"\n  Saved: audit/bias_audit_v10.json")
print("=" * 70)
