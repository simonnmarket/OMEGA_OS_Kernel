"""DOS-TRADING V2.0 HARDENED — camadas MT5, sinais Decimal e backtest sem look-ahead."""

from omega_dos.trading.dos_trading_v1 import (
    DOS_TRADING_V1,
    BacktestConfig,
    MarketRegime,
    TradingSignal,
    VolatilityBins,
    main as run_dos_trading_main,
)

__all__ = [
    "BacktestConfig",
    "DOS_TRADING_V1",
    "MarketRegime",
    "TradingSignal",
    "VolatilityBins",
    "run_dos_trading_main",
]
