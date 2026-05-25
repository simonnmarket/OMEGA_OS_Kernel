"""
PSA helper — gera CSVs OHLCV de cripto via MT5 no formato esperado pelo
omega_harmonic_engine_v3.py (data/ohlcv/grafico_linha/SYMBOL_TF.csv +
data/ohlcv/grafico_candle/SYMBOL_TF.csv).

Uso:
  python agent_ia/tools/fetch_crypto_ohlcv.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parents[2]
LINHA = ROOT / "data" / "ohlcv" / "grafico_linha"
CANDLE = ROOT / "data" / "ohlcv" / "grafico_candle"
LINHA.mkdir(parents=True, exist_ok=True)
CANDLE.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD"]
TFS = {
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
}
N_BARS = 5000


def fetch(symbol: str, tf_name: str, tf_const: int) -> int:
    rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, N_BARS)
    if rates is None or len(rates) == 0:
        print(f"[FAIL] {symbol} {tf_name}: rates None")
        return 0
    candle_path = CANDLE / f"{symbol}_{tf_name}.csv"
    linha_path = LINHA / f"{symbol}_{tf_name}.csv"
    with open(candle_path, "w", encoding="utf-8", newline="\n") as fc:
        fc.write("time,open,high,low,close,tick_volume\n")
        for r in rates:
            from datetime import datetime, timezone
            ts = datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            fc.write(f"{ts},{r['open']},{r['high']},{r['low']},{r['close']},{int(r['tick_volume'])}\n")
    with open(linha_path, "w", encoding="utf-8", newline="\n") as fl:
        fl.write("time,linha\n")
        for r in rates:
            from datetime import datetime, timezone
            ts = datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            fl.write(f"{ts},{r['close']}\n")
    return len(rates)


def main() -> int:
    if not mt5.initialize():
        print("MT5 initialize FAILED")
        return 1
    try:
        total = 0
        for sym in SYMBOLS:
            si = mt5.symbol_info(sym)
            if si is None:
                print(f"[SKIP] {sym}: not in MT5")
                continue
            if not si.visible:
                mt5.symbol_select(sym, True)
            for tf_name, tf_const in TFS.items():
                n = fetch(sym, tf_name, tf_const)
                print(f"[OK] {sym} {tf_name}: {n} bars")
                total += n
        print(f"TOTAL_BARS={total}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
