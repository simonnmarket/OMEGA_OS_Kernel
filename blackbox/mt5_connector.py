"""
Esqueleto MT5 para integrar com blackbox_system:
- Enviar ordens
- Ler posições
- Alimentar record_trade_return com PnL incremental

Nota: Requer MetaTrader5 (pip install MetaTrader5) e terminal MT5 aberto/logado.
"""
from __future__ import annotations

from typing import Optional, Dict, Any

import MetaTrader5 as mt5

from blackbox_system import BlackboxSystem, Config


def init_mt5() -> bool:
    return mt5.initialize()


def send_order(symbol: str, direction: int, volume: float,
               sl: Optional[float] = None, tp: Optional[float] = None,
               deviation: int = 10, comment: str = "blackbox") -> Optional[int]:
    info = mt5.symbol_info(symbol)
    if info is None or not info.visible:
        mt5.symbol_select(symbol, True)
    price = info.ask if direction == 1 else info.bid
    order_type = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": 20251203,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        return result.order
    return None


def get_positions(symbol: str) -> list:
    return mt5.positions_get(symbol=symbol) or []


def compute_incremental_pnl(symbol: str) -> float:
    """Soma PnL de todas as posições do símbolo (simplificado)."""
    positions = get_positions(symbol)
    pnl = 0.0
    for p in positions:
        pnl += p.profit
    return pnl


def run_blackbox_with_mt5(symbol: str, cfg: Optional[Config] = None) -> None:
    bb = BlackboxSystem(cfg or Config())
    if not init_mt5():
        raise SystemExit("MT5 init failed")

    # Exemplo simplificado: processa ticks (substitua por loop real de ticks)
    ticks = mt5.copy_ticks_from(symbol, mt5.TIME_CURRENT, 100, mt5.COPY_TICKS_ALL)
    equity = mt5.account_info().equity
    last_pnl = 0.0

    for t in ticks:
        bar = {
            "time": t.time,
            "close": t.ask,
            "open": t.ask,
            "high": t.ask,
            "low": t.bid,
            "volume": t.volume,
        }
        bb.update_bar(bar)
        bb.detect_liquidity_zone()
        sig = bb.generate_signal()
        # calcular bench
        bench = bb.compute_benchmark_ret()
        # incremental pnl
        current_pnl = compute_incremental_pnl(symbol)
        incremental_pnl = current_pnl - last_pnl
        last_pnl = current_pnl

        bb.record_trade_return(incremental_pnl / equity if equity > 0 else 0.0, bench_ret=bench)

        if sig.direction != 0:
            send_order(symbol, sig.direction, volume=0.1, comment=sig.reason)

    bb.export_metrics("blackbox_mt5_metrics.json")
    print("Metrics:", bb.compute_metrics())


if __name__ == "__main__":
    run_blackbox_with_mt5("EURUSD")
