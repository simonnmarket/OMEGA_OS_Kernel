"""DOS-TRADING V1.0 — camadas MT5, sinais e backtest (especificação Conselho)."""

from omega_dos.trading.dos_trading_v1 import (
    DOS_TRADING_V1,
    MarketRegime,
    TradingSignal,
    main as run_dos_trading_main,
)

__all__ = [
    "DOS_TRADING_V1",
    "MarketRegime",
    "TradingSignal",
    "run_dos_trading_main",
]
