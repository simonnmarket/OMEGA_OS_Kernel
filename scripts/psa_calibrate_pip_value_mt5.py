#!/usr/bin/env python3
"""PSA — Calibração pip_value_lot via MT5 order_calc_profit (MANDATO 20260601)."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import MetaTrader5 as mt5
except ImportError:
    print("MT5 nao disponivel — skip calibracao")
    sys.exit(0)

from modules.omega_usfe_engine import classify_symbol

REPORT = ROOT / "reports" / f"psa_pip_calibration_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
REPORT.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    if not mt5.initialize():
        print("MT5 init falhou")
        return 1

    # Ativos do discovery
    ativos = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "XAUUSD", "XAGUSD", "US500", "US100", "US30", "GER40", "UKOIL+",
        "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "ADAUSD", "LTCUSD", "AVAXUSD", "BNBUSD", "DOGUSD",
    ]

    results = []
    for sym in ativos:
        info = mt5.symbol_info(sym)
        if info is None:
            results.append({"symbol": sym, "status": "SKIP", "reason": "symbol_not_found"})
            continue
        pt = info.point
        price = info.ask if info.ask > 0 else info.bid
        # Simula: comprar 1.0 lot, fechar a +100 pontos
        profit = mt5.order_calc_profit(0, sym, 1.0, price, price + 100 * pt)
        # pip_value_lot = profit / (100 * point) = USD por ponto por lote
        pip_val = profit / (100 * pt) if pt > 0 and profit is not None else 0.0
        results.append({
            "symbol": sym,
            "status": "OK" if profit is not None else "FAIL",
            "point": float(pt),
            "price": float(price),
            "profit_100pts_1lot": float(profit) if profit is not None else None,
            "pip_value_lot": round(pip_val, 6),
            "class": str(classify_symbol(sym)),
        })

    payload = {
        "component": "psa_pip_calibration",
        "utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Report: {REPORT}")
    for r in results:
        if r["status"] == "OK":
            print(f"  {r['symbol']:8} pip_value_lot={r['pip_value_lot']:.6f}  ({r['class']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
