"""Smoke test DOS-TRADING V2.0 HARDENED com CSV MT5 sintético (sem rede)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

from omega_dos.trading.dos_trading_v1 import DOS_TRADING_V1, BacktestConfig, VolatilityBins


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
    assert r.get("trace_id") is not None
    assert "total_costs_bps" in r.get("backtest", {})


def test_signals_use_decimal(tmp_path: Path) -> None:
    csv = tmp_path / "XAUUSD_M1_2024.csv"
    _write_minimal_mt5_csv(csv, n=500)
    trader = DOS_TRADING_V1(str(tmp_path))
    data = trader.load_mt5_data("XAUUSD")
    data = trader.layer1_price_structure(data)
    data = trader.layer2_microstructure(data)
    data = trader.layer3_market_regime(data)
    data = trader.layer4_signal_composition(data)
    signals = trader.generate_signals(data, symbol="XAUUSD")
    if signals:
        s = signals[0]
        assert isinstance(s.entry_price, Decimal)
        assert isinstance(s.stop_loss, Decimal)
        assert isinstance(s.take_profit, Decimal)
        audit = s.to_audit_dict()
        assert isinstance(audit["entry_price"], str)


def test_configurable_vol_bins(tmp_path: Path) -> None:
    csv = tmp_path / "XAUUSD_M1_2024.csv"
    _write_minimal_mt5_csv(csv, n=500)
    bins = VolatilityBins(low_upper=0.003, medium_upper=0.010)
    bt_cfg = BacktestConfig(slippage_bps=1.0, commission_bps=2.0)
    trader = DOS_TRADING_V1(str(tmp_path), vol_bins=bins, backtest_config=bt_cfg)
    r = trader.run_full_pipeline("XAUUSD")
    assert r["status"] == "SUCCESS"
    assert r["vol_bins"]["low_upper"] == 0.003
    assert r["backtest_config"]["slippage_bps"] == 1.0


def test_malformed_csv_rejected(tmp_path: Path) -> None:
    """CSV com colunas erradas deve ser rejeitado sem crash."""
    bad = tmp_path / "XAUUSD_M1_2024.csv"
    pd.DataFrame({"wrong": [1, 2], "columns": [3, 4]}).to_csv(bad, index=False)
    trader = DOS_TRADING_V1(str(tmp_path))
    r = trader.run_full_pipeline("XAUUSD")
    assert r["status"] == "ERROR"


def test_sanitization_removes_nan_inf(tmp_path: Path) -> None:
    """Linhas com NaN/inf devem ser removidas silenciosamente."""
    csv = tmp_path / "XAUUSD_M1_2024.csv"
    t = pd.date_range("2024-01-01", periods=10, freq="min", tz="UTC")
    df = pd.DataFrame({
        "time": t,
        "open": [100, float("nan"), 102, float("inf"), 104, 105, 106, 107, 108, 109],
        "high": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        "low": [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
    })
    df.to_csv(csv, index=False)
    trader = DOS_TRADING_V1(str(tmp_path))
    data = trader.load_mt5_data("XAUUSD")
    # NaN e inf linhas devem ter sido removidas
    assert len(data) < 10
    assert data["open"].isna().sum() == 0
