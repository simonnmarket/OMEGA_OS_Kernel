"""Smoke test DOS-TRADING com CSV MT5 sintético (sem rede)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from omega_dos.trading.dos_trading_v1 import DOS_TRADING_V1


def _write_minimal_mt5_csv(path: Path, n: int = 400) -> None:
    rng = np.random.default_rng(42)
    t = pd.date_range("2024-01-01", periods=n, freq="min", tz="UTC")
    close = 2000 + np.cumsum(rng.normal(0, 0.1, size=n))
    open_ = np.r_[close[0], close[:-1]] + rng.normal(0, 0.02, size=n)
    high = np.maximum(open_, close) + rng.uniform(0.05, 0.5, size=n)
    low = np.minimum(open_, close) - rng.uniform(0.05, 0.5, size=n)
    df = pd.DataFrame({"time": t, "open": open_, "high": high, "low": low, "close": close})
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def test_run_full_pipeline_success(tmp_path: Path) -> None:
    csv = tmp_path / "XAUUSD_M1_2024.csv"
    _write_minimal_mt5_csv(csv, n=500)
    trader = DOS_TRADING_V1(str(tmp_path))
    r = trader.run_full_pipeline("XAUUSD")
    assert r["status"] == "SUCCESS"
    assert r["inputs_sha256"] is not None
    assert "backtest" in r
    assert r["signals_generated"] >= 0
