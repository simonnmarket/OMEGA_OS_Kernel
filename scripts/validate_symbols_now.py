"""Validacao de feed de preco por simbolo — Conselho 28/04/2026."""
import MetaTrader5 as mt5
import numpy as np

SYMBOLS = [
    "BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD",
    "XAUUSD",
    "EURUSD", "GBPUSD", "USDJPY",
    "US500", "NAS100", "GER40",
]

if not mt5.initialize():
    print("MT5 FAIL:", mt5.last_error())
    raise SystemExit(1)

print("=" * 65)
print("SYMBOL VALIDATION REPORT — OMEGA CONSELHO 28/04/2026")
print("=" * 65)

valid, removed = [], []
for sym in SYMBOLS:
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym) if info else None
    ok = bool(info and info.visible and tick and tick.ask > 0)
    atr_info = ""
    if ok:
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 0, 20)
        if rates is not None and len(rates) >= 2:
            closes = np.array([r["close"] for r in rates])
            highs  = np.array([r["high"]  for r in rates])
            lows   = np.array([r["low"]   for r in rates])
            tr = max(
                highs[-1] - lows[-1],
                abs(highs[-1] - closes[-2]),
                abs(lows[-1]  - closes[-2]),
            )
            atr_pct = tr / closes[-1] * 100
            spread  = tick.ask - tick.bid
            atr_info = "  ATR_PCT=" + str(round(atr_pct, 4)) + "%  spread=" + str(round(spread, 5))
    status = "OK  " if ok else "FAIL"
    ask_val = ("%.5f" % tick.ask) if (tick and tick.ask) else "None"
    print("[%s] %-10s  ask=%s%s" % (status, sym, ask_val, atr_info))
    (valid if ok else removed).append(sym)

print("-" * 65)
print("VALIDOS  (%d): %s" % (len(valid), valid))
print("REMOVIDOS(%d): %s" % (len(removed), removed))
mt5.shutdown()
