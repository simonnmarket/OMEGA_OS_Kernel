"""Paridade EWMA e relatório batch vs online (Métrica 10 — DEFINICOES v1.1)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parity_report import (
    parity_ewma_z_pandas_vs_recursive,
    parity_full_batch_vs_online,
    recursive_ewma_z_on_spreads,
)


def test_recursive_z_first_is_zero():
    s = np.array([1.0, 2.0, 3.0])
    z = recursive_ewma_z_on_spreads(s, ewma_span=4)
    assert z[0] == 0.0
    assert np.all(np.isfinite(z))


def test_parity_ewma_report_finite():
    rng = np.random.default_rng(0)
    spread = rng.normal(size=200)
    rep = parity_ewma_z_pandas_vs_recursive(spread, ewma_span=30)
    assert rep["n_points"] > 50
    assert np.isfinite(rep["mse"])
    assert np.isfinite(rep["mean_abs_diff"])


def test_full_pipeline_report_runs():
    rng = np.random.default_rng(1)
    n = 150
    y = rng.normal(size=n)
    x = rng.normal(size=n)
    rep = parity_full_batch_vs_online(y, x, window_ols=40, ewma_span=20)
    assert rep["n_points"] > 0
    assert np.isfinite(rep["mse"])
