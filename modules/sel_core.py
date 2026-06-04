#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEL — Structural Energy Layers (Grupo A — Hot Path)
CKO diretiva 2026-06-01 | L4/L5 apenas offline (sel_research_offline.py)

Não prevê candles. Mede energia, tensão, ruptura, vazamento, impacto.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from modules.omega_usfe_engine import AssetClass, classify_symbol, normalize_ohlcv_df

log = logging.getLogger("OMEGA.SEL")
__version__ = "0.1.0-SEL-GROUP-A"

_HEAL_WINDOW = {"M15": 20, "H1": 20, "H4": 50, "D1": 100, "W1": 120, "MN1": 150}
_STI_HISTORY: Dict[str, list] = {}


def _norm01(x: float, cap: float = 3.0) -> float:
    return float(max(0.0, min(1.0, abs(x) / max(cap, 1e-12))))


def _zscore_last(series: pd.Series, window: int = 50) -> float:
    if len(series) < 5:
        return 0.0
    w = min(window, len(series))
    tail = series.iloc[-w:]
    mu = float(tail.mean())
    sd = float(tail.std(ddof=0))
    if sd < 1e-12:
        return 0.0
    return float((tail.iloc[-1] - mu) / sd)


@dataclass
class SELState:
    symbol: str
    timeframe: str
    asset_class: str
    sel_version: str = __version__

    energy_score: float = 0.0
    energy_z: float = 0.0
    poc_price: float = 0.0
    poc_distance: float = 0.0
    poc_velocity_away: float = 0.0

    residual_energy: float = 0.0
    heal: float = 0.0

    sti: float = 0.0
    sti_norm: float = 0.0
    rif: float = 0.0
    rif_norm: float = 0.0
    fragmentation_density: float = 0.0
    fd_norm: float = 0.0
    rupture_probability: float = 0.0

    leakage: float = 0.0
    leakage_norm: float = 0.0
    impact_score: float = 0.0
    impact_tp_pts: float = 0.0

    audit_divergence: float = 0.0
    audit_veto: bool = False
    rupture_readiness: float = 0.0

    direction_hint: int = 0
    is_valid: bool = True
    block_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SELCore:
    """Motor SEL Grupo A — integrar via USFE / gate paralelo no shadow_loop."""

    # Fallback point sizes by asset class (used when MT5 unavailable)
    _PT_FALLBACK = {
        "forex":     1e-5,   # 5-digit EURUSD, GBPUSD, etc.
        "crypto":    0.01,   # BTCUSD, ETHUSD (most brokers)
        "commodity": 0.01,   # XAUUSD, XAGUSD
        "energy":    0.01,   # UKOIL+, USOIL
        "index":     0.1,    # US500, GER40 (approximate)
    }

    def __init__(self, symbol: str, asset_class: Optional[AssetClass] = None):
        self.symbol = (symbol or "EURUSD").upper()
        self.asset_class = asset_class or classify_symbol(self.symbol)
        self._pip_val = 0.01
        # Fix Bug3b: per-class fallback (1e-5 was wrong for crypto/commodity)
        self._pt_size = self._PT_FALLBACK.get(self.asset_class.value, 1e-5)

    def _load_pip(self) -> float:
        p = Path(__file__).resolve().parent.parent / "config" / "pip_value_cache.json"
        if p.is_file():
            raw = json.loads(p.read_text(encoding="utf-8"))
            v = float((raw.get("pip_value_lot") or {}).get(self.symbol, 0.0))
            pt = float((raw.get("point_size") or {}).get(self.symbol, 0.0))
            if pt > 0:
                self._pt_size = pt
            if v > 0:
                return v
        try:
            import MetaTrader5 as mt5

            if mt5.initialize():
                sym = mt5.symbol_info(self.symbol)
                if sym and sym.point and sym.ask:
                    self._pt_size = float(sym.point)  # Fix Bug3: capture point size for impact_tp_pts scaling
                    pr = mt5.order_calc_profit(0, self.symbol, 1.0, sym.ask, sym.ask + 100 * sym.point)
                    if pr is not None:
                        return abs(float(pr)) / 100.0
                mt5.shutdown()
        except Exception:
            pass
        return 0.01

    def _poc(self, df: pd.DataFrame, n_bins: int = 20) -> Tuple[float, float]:
        closes = df["close"].astype(float).values
        vols = df["volume"].astype(float).values
        if len(closes) < 2:
            return float(closes[-1]) if len(closes) else 0.0, 0.0
        lo, hi = float(np.min(closes)), float(np.max(closes))
        if hi <= lo:
            return lo, float(np.sum(vols))
        bins = np.linspace(lo, hi, n_bins + 1)
        idx = np.clip(np.digitize(closes, bins) - 1, 0, n_bins - 1)
        vpb = np.bincount(idx, weights=vols, minlength=n_bins)
        best = int(np.argmax(vpb))
        poc = float((bins[best] + bins[best + 1]) / 2.0)
        return poc, float(vpb[best])

    def compute(
        self,
        df: pd.DataFrame,
        timeframe: str = "H1",
        signal_direction: Optional[str] = None,
    ) -> SELState:
        tf = (timeframe or "H1").upper()
        raw = normalize_ohlcv_df(df)
        n = len(raw)
        if n < 30:
            return SELState(
                symbol=self.symbol,
                timeframe=tf,
                asset_class=self.asset_class.value,
                is_valid=False,
                block_reason="MIN_BARS",
            )

        self._pip_val = self._load_pip()
        close = raw["close"].astype(float)
        high = raw["high"].astype(float)
        low = raw["low"].astype(float)
        vol = raw["volume"].astype(float)
        rng = (high - low).abs()

        # L1 — Temporal energy (z-score por classe)
        energy = vol * rng
        energy_z = _zscore_last(energy, window=min(80, max(20, n // 2)))
        energy_last = float(energy.iloc[-1])

        # L2 — POC energy
        poc, _ = self._poc(raw)
        price = float(close.iloc[-1])
        poc_dist = abs(price - poc)
        poc_dist_series = (close - poc).abs()
        poc_vel = float(poc_dist_series.diff().fillna(0).iloc[-3:].mean())

        # L6 residual / L7 HEAL
        delta = close.diff().fillna(0.0)
        energy_in = vol * delta.abs()
        displacement = delta.abs()
        residual = energy_in - displacement * vol * 0.5
        heal_n = _HEAL_WINDOW.get(tf, 30)
        heal = float(residual.rolling(heal_n, min_periods=5).sum().iloc[-1])

        # L8 — STL
        disp_last = float(displacement.iloc[-1]) + 1e-9
        sti_raw = float(energy_last / disp_last)
        hist_key = f"{self.symbol}:{tf}"
        hist = _STI_HISTORY.setdefault(hist_key, [])
        hist.append(sti_raw)
        if len(hist) > 500:
            del hist[:-500]
        hist_max = max(hist) if hist else sti_raw
        sti = min(sti_raw, hist_max * 1.05)

        # RIF — oscilações × frequência (proxy: sign changes / bar)
        signs = np.sign(delta.values)
        flips = int(np.sum(signs[1:] != signs[:-1]))
        rif = float(flips / max(n - 1, 1)) * float(np.std(close.values[-20:]))

        fd = float(rng.iloc[-5:].mean() / (abs(delta.iloc[-5:]).sum() + 1e-9))

        sti_n = _norm01(sti / max(hist_max, 1e-9), 1.0)
        rif_n = _norm01(rif, 2.0)
        heal_n = _norm01(heal, heal_n * 2.0 if heal_n else 60.0)
        fd_n = _norm01(fd, 5.0)
        rp = float(min(1.0, 0.35 * sti_n + 0.25 * rif_n + 0.25 * heal_n + 0.15 * fd_n))

        # L9 — Leakage (expected vs observed USD move via pip cache)
        expected_pts = max(poc_dist * 0.5, float(rng.iloc[-10:].mean()) * 2.0)
        observed_pts = float(abs(close.iloc[-1] - close.iloc[-5]))
        expected_usd = expected_pts * self._pip_val
        observed_usd = observed_pts * self._pip_val
        leakage = max(0.0, expected_usd - observed_usd)
        leakage_norm = _norm01(leakage, max(expected_usd, 1.0))

        # L10 — Impact
        amplitude = float(rng.iloc[-3:].max())
        persistence = float(np.mean(np.sign(delta.iloc[-8:]) == np.sign(delta.iloc[-1])))
        impact = amplitude * max(persistence, 0.1)
        impact_n = _norm01(impact, float(rng.quantile(0.95) + 1e-9))
        # Fix Bug3 2026-06-04: convert price-units → broker points (/ pt_size)
        _raw_impact = max(amplitude * 3.0, float(rng.iloc[-20:].sum() * 0.25))
        impact_tp_pts = _raw_impact / max(self._pt_size, 1e-12)
        impact_tp_pts = min(impact_tp_pts, 5000.0)  # cap: no asset needs TP > 5000 pts

        # Audit — L8 ruptura vs L1 energia baixa
        audit_div = abs(rp - _norm01(energy_z, 2.0))
        audit_veto = bool(rp > 0.7 and energy_z < -0.5)

        # Direction hint
        d_hint = 0
        if signal_direction:
            sd = signal_direction.upper()
            if sd in ("BUY", "LONG"):
                d_hint = 1
            elif sd in ("SELL", "SHORT"):
                d_hint = -1
        else:
            d_hint = 1 if float(delta.iloc[-1]) > 0 else (-1 if float(delta.iloc[-1]) < 0 else 0)

        rupture_readiness = float(
            max(0.0, min(1.0, rp + 0.2 * impact_n + 0.1 * heal_n - 0.3 * leakage_norm))
        )
        if audit_veto:
            rupture_readiness *= 0.5
            block_reason = "AUDIT_VETO_L8_vs_L1"
        else:
            block_reason = ""

        return SELState(
            symbol=self.symbol,
            timeframe=tf,
            asset_class=self.asset_class.value,
            energy_score=energy_last,
            energy_z=energy_z,
            poc_price=poc,
            poc_distance=poc_dist,
            poc_velocity_away=poc_vel,
            residual_energy=float(residual.iloc[-1]),
            heal=heal,
            sti=sti,
            sti_norm=sti_n,
            rif=rif,
            rif_norm=rif_n,
            fragmentation_density=fd,
            fd_norm=fd_n,
            rupture_probability=rp,
            leakage=leakage,
            leakage_norm=leakage_norm,
            impact_score=impact_n,
            impact_tp_pts=impact_tp_pts,
            audit_divergence=audit_div,
            audit_veto=audit_veto,
            rupture_readiness=rupture_readiness,
            direction_hint=d_hint,
            is_valid=True,
            block_reason=block_reason,
        )


def self_test() -> None:
    rng = np.random.default_rng(7)
    n = 120
    px = 100 + np.cumsum(rng.normal(0.2, 0.5, n))
    df = pd.DataFrame(
        {
            "open": px,
            "high": px + 0.4,
            "low": px - 0.4,
            "close": px,
            "volume": rng.integers(100, 5000, n).astype(float),
        }
    )
    st = SELCore("GER40").compute(df, "H1", "BUY")
    assert st.is_valid and 0 <= st.rupture_probability <= 1
    print(f"SEL self-test OK rp={st.rupture_probability:.3f} heal={st.heal:.2f} veto={st.audit_veto}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    self_test()
