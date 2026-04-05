"""OMEGA Data Operating System (DOS) — FIN-SENSE, MT5 Tier-0 e métricas institucionais."""

from omega_dos.metrics.institutional import Tier0Metrics
from omega_dos.pipeline import DosPipelineResult, run_dos_pipeline
from omega_dos.provenance import build_provenance_record, sha256_canonical
from omega_dos.trading.dos_trading_v1 import DOS_TRADING_V1

__version__ = "1.1.0"

__all__ = [
    "__version__",
    "DosPipelineResult",
    "run_dos_pipeline",
    "build_provenance_record",
    "sha256_canonical",
    "Tier0Metrics",
    "DOS_TRADING_V1",
]
