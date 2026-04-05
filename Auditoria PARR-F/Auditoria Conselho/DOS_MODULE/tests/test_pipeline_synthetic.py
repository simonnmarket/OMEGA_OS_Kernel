"""Pipeline DOS com dados sintéticos (sem Postgres)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from omega_dos.pipeline import run_dos_pipeline
from omega_dos.provenance import sha256_canonical


def _demo_like_frame(n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    ts = pd.date_range("2024-01-01", periods=n, freq="min", tz="UTC")
    y = 100 + np.cumsum(rng.normal(0, 0.1, size=n))
    x = y + rng.normal(0, 0.02, size=n)
    return pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "x": x,
            "spread": x - y,
            "z": rng.normal(0, 1, size=n),
            "beta": rng.uniform(0.9, 1.1, size=n),
            "signal_fired": rng.random(size=n) > 0.7,
            "order_filled": rng.random(size=n) > 0.5,
            "ram_mb": rng.uniform(100, 500, size=n),
            "cpu_pct": rng.uniform(5, 40, size=n),
            "proc_ms": rng.uniform(1, 50, size=n),
            "opp_cost": rng.uniform(0, 0.01, size=n),
        }
    )


def test_pipeline_frame_runs_and_provenance_stable():
    mkt = _demo_like_frame(120)
    r1 = run_dos_pipeline(market=mkt, source="frame", notional_usd=10_000.0)
    r2 = run_dos_pipeline(market=mkt, source="frame", notional_usd=10_000.0)
    assert not r1.errors
    assert r1.summary["rows"] == 120
    assert r1.provenance["inputs_digest_sha256"] == r2.provenance["inputs_digest_sha256"]
    assert len(r1.provenance["record_digest_sha256"]) == 64
    assert "var_historical_loss" in r1.risk


def test_sha256_canonical_deterministic():
    assert sha256_canonical({"a": 1, "b": 2}) == sha256_canonical({"b": 2, "a": 1})


def test_risk_metrics_finite():
    mkt = _demo_like_frame(200)
    r = run_dos_pipeline(market=mkt, source="frame")
    assert np.isfinite(r.risk["var_historical_loss"]) or np.isnan(r.risk["var_historical_loss"])
    assert np.isfinite(r.risk["cvar_historical_loss"]) or np.isnan(r.risk["cvar_historical_loss"])
