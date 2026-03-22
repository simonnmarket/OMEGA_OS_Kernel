#!/usr/bin/env python3
"""Testes mínimos para risk_circuit_breaker.py — executar: python test_risk_circuit_breaker.py"""
from datetime import datetime, timezone

from risk_circuit_breaker import CircuitState, IntradayCircuitBreaker, CircuitBreakerConfig, default_p01_breaker


def test_no_trip_under_threshold():
    cb = default_p01_breaker()
    t = datetime(2026, 3, 22, 8, 0, tzinfo=timezone.utc)
    cb.update(100_000.0, ts=t)
    r = cb.update(96_600.0, ts=t)  # -3.4%
    assert cb.state == CircuitState.CLOSED
    assert r["tripped"] is False
    assert cb.allow_new_orders()


def test_trip_at_exact_threshold():
    cb = IntradayCircuitBreaker(config=CircuitBreakerConfig(threshold_loss_pct=3.5))
    t = datetime(2026, 3, 22, 8, 0, tzinfo=timezone.utc)
    cb.update(100_000.0, ts=t)
    r = cb.update(96_500.0, ts=t)  # -3.5%
    assert cb.state == CircuitState.OPEN
    assert r["tripped"] is True
    assert not cb.allow_new_orders()


def test_new_day_resets():
    cb = default_p01_breaker()
    t1 = datetime(2026, 3, 22, 23, 0, tzinfo=timezone.utc)
    cb.update(100_000.0, ts=t1)
    t2 = datetime(2026, 3, 23, 8, 0, tzinfo=timezone.utc)
    cb.update(100_000.0, ts=t2)
    assert cb.state == CircuitState.CLOSED


if __name__ == "__main__":
    test_no_trip_under_threshold()
    test_trip_at_exact_threshold()
    test_new_day_resets()
    print("all tests passed")
