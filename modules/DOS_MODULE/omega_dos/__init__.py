"""OMEGA Data Operating System (DOS) — FIN-SENSE, MT5 Tier-0 e métricas institucionais.

Versão: 2.0.0 — HARDENED (Decimal, JSON logs, custos variáveis, PnL HYPOTHETICAL).
"""

from omega_dos.bridge_fin_sense import PNL_DISCLAIMER
from omega_dos.metrics.institutional import Tier0Metrics
from omega_dos.pipeline import DosPipelineResult, run_dos_pipeline
from omega_dos.provenance import build_provenance_record, sha256_canonical
from omega_dos.trading.dos_trading_v1 import (
    DOS_TRADING_V1,
    BacktestConfig,
    TradingSignal,
    VolatilityBins,
)

__version__ = "2.0.0"

__all__ = [
    "__version__",
    "BacktestConfig",
    "DosPipelineResult",
    "DOS_TRADING_V1",
    "PNL_DISCLAIMER",
    "run_dos_pipeline",
    "build_provenance_record",
    "sha256_canonical",
    "Tier0Metrics",
    "TradingSignal",
    "VolatilityBins",
]
