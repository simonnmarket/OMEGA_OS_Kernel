#!/usr/bin/env python3
"""
OMEGA PSA — Exportador OHLCV MT5 → data/ohlcv/
Exporta CSVs no formato canónico do Motor Harmônico V3:
  time,open,high,low,close,tick_volume

Uso:
  python scripts/export_ohlcv_mt5.py
  python scripts/export_ohlcv_mt5.py --symbols ADAUSD XRPUSD --timeframes H1 M15 --bars 12000
  python scripts/export_ohlcv_mt5.py --symbols BTCUSD ETHUSD --bars 5000

Requisito Motor Harmônico V3: ficheiros em data/ohlcv/grafico_linha e grafico_candle
({SYMBOL}_{TF}.csv). Este script gera-os a partir do MT5 (terminal aberto).
"""
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5

TIMEFRAMES = {
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

# Lista alargada (alinhada ao shadow_loop); exporta só o que o broker tiver no MT5.
ALL_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
    "XAUUSD", "XAGUSD", "UKOIL", "USOIL",
    "US500", "NAS100", "GER40", "UK100",
    "BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD",
    "BNBUSD", "LTCUSD", "XRPUSD", "ADAUSD", "DOTUSD", "AVAXUSD", "LINKUSD",
    "UNIUSD", "ATOMUSD", "NEARUSD", "APTUSD", "ARBUSD", "OPUSD", "FILUSD",
    "MATICUSD", "POLUSD", "TRXUSD", "XLMUSD", "ETCUSD", "ALGOUSD", "VETUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY",
]

def export_symbol(symbol: str, tf_name: str, tf_mt5: int,
                  bars: int, out_dir: Path) -> bool:
    rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, bars)
    if rates is None or len(rates) == 0:
        print(f"  [SKIP] {symbol}_{tf_name}: sem dados MT5")
        return False
    fname = f"{symbol}_{tf_name}.csv"

    # 1. root (formato candle — compatibilidade geral)
    root_file = out_dir / fname
    with open(root_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "open", "high", "low", "close", "tick_volume"])
        for r in rates:
            dt = datetime.fromtimestamp(r["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([dt, r["open"], r["high"], r["low"], r["close"], r["tick_volume"]])

    # 2. grafico_candle/ — formato Motor V3 (time,open,high,low,close,tick_volume)
    candle_dir = out_dir / "grafico_candle"
    candle_dir.mkdir(parents=True, exist_ok=True)
    with open(candle_dir / fname, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "open", "high", "low", "close", "tick_volume"])
        for r in rates:
            dt = datetime.fromtimestamp(r["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([dt, r["open"], r["high"], r["low"], r["close"], r["tick_volume"]])

    # 3. grafico_linha/ — formato Motor V3 (time,linha = close only)
    linha_dir = out_dir / "grafico_linha"
    linha_dir.mkdir(parents=True, exist_ok=True)
    with open(linha_dir / fname, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "linha"])
        for r in rates:
            dt = datetime.fromtimestamp(r["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([dt, r["close"]])

    # SHA3-256 integrity hash (CQO Opcao B — look-ahead bias audit trail)
    audit_meta = {
        "symbol": symbol, "timeframe": tf_name, "bars": len(rates),
        "first_time": datetime.fromtimestamp(rates[0]["time"], tz=timezone.utc).isoformat(),
        "last_time":  datetime.fromtimestamp(rates[-1]["time"], tz=timezone.utc).isoformat(),
        "export_ts":  datetime.now(timezone.utc).isoformat(),
    }
    export_hash = hashlib.sha3_256(
        json.dumps(audit_meta, sort_keys=True).encode()
    ).hexdigest()
    sha3_file = out_dir / f"{symbol}_{tf_name}.sha3"
    sha3_file.write_text(export_hash, encoding="utf-8")

    print(f"  [OK]   {symbol}_{tf_name}: {len(rates)} candles -> root + candle + linha | sha3={export_hash[:16]}...")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=ALL_SYMBOLS)
    ap.add_argument("--bars", type=int, default=10000)
    ap.add_argument("--timeframes", nargs="+", default=["H1", "M15", "H4"])
    ap.add_argument("--out-dir", default=str(ROOT / "data" / "ohlcv"))
    ap.add_argument("--skip-existing", action="store_true",
                    help="Pular simbolos que já têm CSV")
    ap.add_argument(
        "--strict-exit",
        action="store_true",
        help="Exit 1 se qualquer símbolo×TF falhar. Default: exit 0 se pelo menos um export OK (útil para runner 24/7 com lista larga).",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not mt5.initialize():
        print("ERRO: MT5 não conectado"); sys.exit(1)

    acc = mt5.account_info()
    print(f"MT5 conectado | {acc.name} | {acc.server} | equity={acc.equity:.2f}")
    print(f"Exportando {len(args.symbols)} simbolos x {len(args.timeframes)} TFs "
          f"| {args.bars} candles | out={out_dir}")
    print("-" * 60)

    ok = skip = fail = 0
    for sym in args.symbols:
        for tf_name in args.timeframes:
            if tf_name not in TIMEFRAMES:
                print(f"  [WARN] TF {tf_name} desconhecido - pulando")
                continue
            out_file = out_dir / f"{sym}_{tf_name}.csv"
            if args.skip_existing and out_file.exists():
                print(f"  [SKIP-EXIST] {sym}_{tf_name}")
                skip += 1
                continue
            result = export_symbol(sym, tf_name, TIMEFRAMES[tf_name], args.bars, out_dir)
            if result: ok += 1
            else: fail += 1

    mt5.shutdown()
    print("-" * 60)
    print(f"Exportados: {ok} | Pulados: {skip} | Falhas: {fail}")
    print(f"CSV path: {out_dir}")
    if args.strict_exit:
        return 0 if fail == 0 else 1
    # Parcial: não bloquear 24/7 quando o broker não tem parte dos símbolos da lista
    if ok == 0:
        return 1
    if fail > 0:
        print(f"[AVISO] {fail} export(s) falharam - exit 0 porque ok={ok} (use --strict-exit para exit 1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
