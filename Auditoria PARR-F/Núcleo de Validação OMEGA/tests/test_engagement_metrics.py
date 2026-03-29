"""Métricas de engajamento e convenções n=0 (Métrica 9 — DEFINICOES v1.1)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engagement_metrics import (
    engagement_rate,
    opportunity_cost_points,
    performance_placeholders_when_n_trades_zero,
)


def test_engagement_rate_none_when_zero_signals():
    assert engagement_rate(0, 0) is None


def test_engagement_rate_value():
    assert engagement_rate(10, 8) == pytest.approx(0.8)


def test_engagement_rate_invalid():
    with pytest.raises(ValueError):
        engagement_rate(5, 6)


def test_n_zero_placeholders():
    d = performance_placeholders_when_n_trades_zero()
    assert d["winrate"] is None
    assert d["sharpe"] is None
    assert d["max_drawdown_pct"] == 0.0
    assert d["status"] == "N_A_ZERO_TRADES"


def test_opportunity_cost_only_when_signal_not_filled():
    assert opportunity_cost_points(False, False, 10.0, 2.0, 1.0) is None
    assert opportunity_cost_points(True, True, 10.0, 2.0, 1.0) is None
    oc = opportunity_cost_points(True, False, 10.0, 2.0, 0.5)
    assert oc == pytest.approx(abs(10.0 - 2.0) * 0.5)
