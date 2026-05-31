#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA USFE — Unified Structural Field Engine v1.1.0
================================================================================
Fusão conceptual: TRE (Temporal Resonance) + TEPA (Temporal Energy Propagation)
+ Macro Regime Engine (generalizado multi-classe).

NÃO integrado em shadow_loop — pacote de desenvolvimento para testes e refinamento.
Interface OMEGA-ready: ComponentEngine.from_config(regime).compute_from_bars(df).

Autor: AIC Tech Lead (fusão CEO) | Data: 2026-05-29
"""
from __future__ import annotations

import json
import logging
import statistics
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger("OMEGA.USFE")
__version__ = "1.1.2-USFE-FUSION"

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
_PKG_DIR = Path(__file__).resolve().parent
_LAB_CALIB = _PKG_DIR.parent / "config" / "usfe_calibration.json"
_DEFAULT_CALIBRATION = (
    _LAB_CALIB if _LAB_CALIB.exists() else _PKG_DIR / "usfe_calibration.json"
)


# -----------------------------------------------------------------------------
# Asset classification (alinhado a shadow_loop._asset_regime + energy)
# -----------------------------------------------------------------------------
class AssetClass(str, Enum):
    FOREX = "forex"
    COMMODITY = "commodity"
    CRYPTO = "crypto"
    INDEX = "index"
    ENERGY = "energy"


def classify_symbol(symbol: str) -> AssetClass:
    s = (symbol or "").upper()
    if any(c in s for c in ("XAU", "XAG")):
        return AssetClass.COMMODITY
    if any(c in s for c in ("OIL", "BRENT", "WTI", "UKOIL", "USOIL")):
        return AssetClass.ENERGY
    if any(c in s for c in ("BTC", "ETH", "SOL", "DOG", "ADA", "XRP", "LTC", "BNB", "AVAX")):
        return AssetClass.CRYPTO
    if any(c in s for c in ("US500", "US100", "US30", "NAS", "GER", "UK100", "JPN", "SP5", "DOW", "DAX")):
        return AssetClass.INDEX
    return AssetClass.FOREX


# -----------------------------------------------------------------------------
# Calibration
# -----------------------------------------------------------------------------
@dataclass
class ClassCalibration:
    temporal_weight: float = 1.0
    structural_weight: float = 1.0
    energy_weight: float = 1.0
    observational_weight: float = 1.0
    macro_weight: float = 1.0
    liquidity_weight: float = 1.0
    energy_decay: float = 0.92
    impact_decay: float = 0.97
    residual_threshold: float = 0.35
    dissipation_threshold: float = 0.60
    pressure_threshold: float = 1.25
    geometry_density: float = 5.0
    fractal_groups: List[int] = field(default_factory=lambda: [3, 6, 9, 12, 18])
    probability_threshold: float = 0.28  # gate mínimo para alignment_score
    risk_cap: float = 0.75
    macro_veto_high: float = 0.8
    macro_veto_low: float = -0.8
    poc_bins: int = 20
    eci_risk_weight: float = 0.10
    dei_risk_weight: float = 0.20
    conflict_risk_weight: float = 0.25
    confidence_risk_damp: float = 0.55
    active_hours_utc: List[int] = field(default_factory=lambda: [8, 9, 13, 14, 15])
    min_bars: int = 60
    renko_brick_pct: float = 0.001


def load_calibration(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path or _DEFAULT_CALIBRATION
    if not p.is_file():
        log.warning("USFE calibration not found: %s — using builtins", p)
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def get_class_calibration(
    asset_class: AssetClass,
    calib_root: Optional[Dict[str, Any]] = None,
) -> ClassCalibration:
    root = calib_root if calib_root is not None else load_calibration()
    raw = (root.get("asset_classes") or {}).get(asset_class.value, {})
    return ClassCalibration(
        temporal_weight=float(raw.get("temporal_weight", 1.0)),
        structural_weight=float(raw.get("structural_weight", 1.0)),
        energy_weight=float(raw.get("energy_weight", 1.0)),
        observational_weight=float(raw.get("observational_weight", 1.0)),
        macro_weight=float(raw.get("macro_weight", 1.0)),
        liquidity_weight=float(raw.get("liquidity_weight", 1.0)),
        energy_decay=float(raw.get("energy_decay", 0.92)),
        impact_decay=float(raw.get("impact_decay", 0.97)),
        residual_threshold=float(raw.get("residual_threshold", 0.35)),
        dissipation_threshold=float(raw.get("dissipation_threshold", 0.60)),
        pressure_threshold=float(raw.get("pressure_threshold", 1.25)),
        geometry_density=float(raw.get("geometry_density", 5)),
        fractal_groups=list(raw.get("fractal_groups", [3, 6, 9, 12, 18])),
        probability_threshold=float(raw.get("probability_threshold", 0.28)),
        risk_cap=float(raw.get("risk_cap", 0.75)),
        macro_veto_high=float(raw.get("macro_veto_high", 0.8)),
        macro_veto_low=float(raw.get("macro_veto_low", -0.8)),
        poc_bins=int(raw.get("poc_bins", 20)),
        eci_risk_weight=float(raw.get("eci_risk_weight", 0.10)),
        dei_risk_weight=float(raw.get("dei_risk_weight", 0.20)),
        conflict_risk_weight=float(raw.get("conflict_risk_weight", 0.25)),
        confidence_risk_damp=float(raw.get("confidence_risk_damp", 0.55)),
        active_hours_utc=list(raw.get("active_hours_utc", [8, 9, 13, 14, 15])),
        min_bars=int(raw.get("min_bars", 60)),
        renko_brick_pct=float(raw.get("renko_brick_pct", 0.001)),
    )


# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
class StructuralSignal(str, Enum):
    EXPANSION = "STRUCTURAL_EXPANSION"
    COLLAPSE = "STRUCTURAL_COLLAPSE"
    NEUTRAL = "STRUCTURAL_NEUTRAL"


class TradeBias(str, Enum):
    ALLOW_LONG = "ALLOW_LONG"
    ALLOW_SHORT = "ALLOW_SHORT"
    BLOCK = "BLOCK"
    NEUTRAL = "NEUTRAL"


@dataclass
class UnifiedFieldResult:
    symbol: str
    asset_class: str
    usfe_version: str
    # Temporal (TRE)
    trs: float = 0.0
    session_pressure: float = 0.0
    propagation_delay: float = 0.0
    # Structural (TRE + TEPA)
    sps: float = 0.0
    hpi: float = 0.0
    curvature: float = 0.0
    wave_impact: float = 0.0
    # Energy (TEPA)
    energy_last: float = 0.0
    pressure_last: float = 0.0
    dissipation_last: float = 0.0
    residual_impact_last: float = 0.0
    poc_price: float = 0.0
    fractal_resonance: int = 0
    energy_exhaustion: int = 0
    # Observational (TRE)
    dei: float = 0.0
    odi: float = 0.0
    representation_conflict: float = 0.0
    candle_direction: float = 0.0
    line_direction: float = 0.0
    renko_direction: float = 0.0
    # Fusion
    rei: float = 0.0
    eci: float = 0.0
    macro_regime: str = "NEUTRAL"
    macro_pressure_score: float = 0.0
    alignment_score: float = 0.0  # média de métricas normalizadas (não é P(win))
    probability: float = 0.0  # alias legado = alignment_score
    risk: float = 0.0
    structural_signal: str = StructuralSignal.NEUTRAL.value
    trade_bias: str = TradeBias.NEUTRAL.value
    confidence: float = 0.0
    block_reason: str = ""
    score_components: int = 0
    is_valid: bool = True
    n_bars: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["alignment_score"] = self.alignment_score
        d["probability"] = self.alignment_score  # compat OMEGA / logs legados
        d["hour_recurrence_ratio"] = self.trs  # TRS = distribuição horária UTC
        return d


# OMEGA kernel compatibility
@dataclass
class ComponentState:
    is_valid: bool
    direction: int
    strength: float
    n_bars: int
    regime: str = ""
    usfe: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Data preparation
# -----------------------------------------------------------------------------
def normalize_ohlcv_df(df: pd.DataFrame) -> pd.DataFrame:
    """Aceita colunas MT5 / CSV variados."""
    out = df.copy()
    colmap = {c.lower(): c for c in out.columns}
    renames = {}
    for std, aliases in [
        ("open", ["open", "o"]),
        ("high", ["high", "h"]),
        ("low", ["low", "l"]),
        ("close", ["close", "c"]),
        ("volume", ["volume", "vol", "tick_volume", "real_volume"]),
        ("timestamp", ["timestamp", "time", "datetime", "date"]),
    ]:
        for a in aliases:
            if a in colmap and std not in out.columns:
                renames[colmap[a]] = std
                break
    if renames:
        out = out.rename(columns=renames)
    if "volume" not in out.columns:
        out["volume"] = 1.0
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(1.0).clip(lower=0)
    for c in ("open", "high", "low", "close"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["close"]).reset_index(drop=True)
    return out


def _hour_buckets(df: pd.DataFrame) -> List[int]:
    if "timestamp" not in df.columns:
        return list(range(len(df)))
    ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    if ts.dt.tz is not None:
        ts = ts.dt.tz_convert("UTC")
    if ts.isna().all():
        return list(range(len(df)))
    return ts.dt.hour.fillna(0).astype(int).tolist()


def _direction_from_returns(closes: np.ndarray, lookback: int = 3) -> float:
    if len(closes) < lookback + 1:
        return 0.0
    d = closes[-1] - closes[-lookback - 1]
    if d > 0:
        return 1.0
    if d < 0:
        return -1.0
    return 0.0


def _line_direction(closes: np.ndarray, span: int = 21) -> float:
    if len(closes) < span:
        return _direction_from_returns(closes)
    ema = pd.Series(closes).ewm(span=span, adjust=False).mean().values
    slope = ema[-1] - ema[-5] if len(ema) >= 5 else ema[-1] - ema[0]
    if slope > 0:
        return 1.0
    if slope < 0:
        return -1.0
    return 0.0


def _renko_direction(closes: np.ndarray, brick_pct: float) -> float:
    if len(closes) < 2:
        return 0.0
    brick = max(closes[-1] * brick_pct, 1e-8)
    last_brick = closes[0]
    direction = 0.0
    for px in closes[1:]:
        diff = px - last_brick
        if diff >= brick:
            n = int(diff // brick)
            last_brick += n * brick
            direction = 1.0
        elif diff <= -brick:
            n = int(abs(diff) // brick)
            last_brick -= n * brick
            direction = -1.0
    return direction


# -----------------------------------------------------------------------------
# Sub-engines (TRE lineage)
# -----------------------------------------------------------------------------
class _TemporalCore:
    @staticmethod
    def recurrence_strength(hours: List[int]) -> float:
        if not hours:
            return 0.0
        _, counts = np.unique(hours, return_counts=True)
        return float(np.max(counts) / np.sum(counts))

    @staticmethod
    def session_pressure(hours: List[int], active: List[int]) -> float:
        if not hours:
            return 0.0
        m = sum(1 for h in hours if h in active)
        return m / len(hours)

    @staticmethod
    def propagation_delay(hours: List[int]) -> float:
        if len(hours) < 2:
            return 0.0
        u = sorted(set(hours))
        if len(u) < 2:
            return 0.0
        return float(np.mean(np.diff(u)))


class _StructuralCore:
    @staticmethod
    def persistence(prices: np.ndarray) -> float:
        if len(prices) < 2:
            return 0.0
        d = np.sign(np.diff(prices))
        if len(d) == 0:
            return 0.0
        return float(np.mean(d == d[0]))

    @staticmethod
    def hidden_propagation(volume: np.ndarray, volatility: np.ndarray) -> float:
        if len(volume) == 0:
            return 0.0
        return float(np.mean(volume) / (1.0 + np.mean(volatility)))


class _ObservationalCore:
    @staticmethod
    def distortion(attention: float, retail_vol: float) -> float:
        return attention * 0.7 + retail_vol * 0.3

    @staticmethod
    def conflict(candle: float, line: float, renko: float) -> float:
        return float(np.var([candle, line, renko]))


# -----------------------------------------------------------------------------
# TEPA energy pipeline (vectorized where possible)
# -----------------------------------------------------------------------------
class _EnergyCore:
    def __init__(self, cfg: ClassCalibration):
        self.cfg = cfg

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        delta = d["close"].diff().fillna(0.0)
        d["energy"] = d["volume"] * delta.abs()
        d["pressure"] = (
            d["energy"].rolling(10, min_periods=1).mean()
            / (d["volume"].rolling(10, min_periods=1).mean() + 1e-9)
        )
        e = d["energy"].fillna(0.0).to_numpy(dtype=np.float64)
        prev_e = np.roll(e, 1)
        prev_e[0] = 0.0
        d["dissipation"] = prev_e * self.cfg.energy_decay - e
        d["residual_impact"] = prev_e - (e * self.cfg.impact_decay)
        closes = d["close"].to_numpy(dtype=np.float64)
        geom = np.zeros(len(closes), dtype=np.float64)
        if len(closes) > 1:
            geom[1:] = np.abs(np.diff(closes)) * self.cfg.geometry_density
        d["geometry_fill"] = geom
        idx = np.arange(len(d), dtype=np.int64)
        fractal = np.zeros(len(d), dtype=np.int64)
        for fg in self.cfg.fractal_groups:
            if fg > 0:
                fractal += (idx % fg == 0).astype(np.int64)
        d["fractal_resonance"] = fractal
        vel = np.gradient(closes)
        acc = np.gradient(vel)
        d["curvature"] = np.abs(acc)
        pv = np.zeros(len(closes), dtype=np.float64)
        if len(closes) > 1:
            pv[1:] = np.diff(closes)
        d["propagation_vector"] = pv
        d["wave_impact"] = np.abs(pv) * e * (d["curvature"].to_numpy() + 1.0)
        d["energy_exhaustion"] = (
            (d["pressure"] > self.cfg.pressure_threshold) & (d["energy"] < d["pressure"])
        ).astype(int)
        return d

    def poc(self, df: pd.DataFrame) -> Tuple[float, float]:
        n_bins = max(5, int(self.cfg.poc_bins))
        if df.empty or "close" not in df.columns:
            return 0.0, 0.0
        closes = df["close"].dropna().to_numpy(dtype=np.float64)
        volumes = df.loc[df["close"].notna(), "volume"].fillna(0).to_numpy(dtype=np.float64)
        if len(closes) < 2:
            return float(closes[-1]) if len(closes) else 0.0, float(volumes.sum()) if len(volumes) else 0.0
        lo, hi = float(np.min(closes)), float(np.max(closes))
        if hi <= lo:
            return lo, float(volumes.sum())
        bins = np.linspace(lo, hi, n_bins + 1)
        bin_idx = np.clip(np.digitize(closes, bins) - 1, 0, n_bins - 1)
        vol_per_bin = np.bincount(bin_idx, weights=volumes, minlength=n_bins)
        best = int(np.argmax(vol_per_bin))
        poc_price = float((bins[best] + bins[best + 1]) / 2.0)
        return poc_price, float(vol_per_bin[best])


# -----------------------------------------------------------------------------
# Macro regime (generalized — OHLCV proxy mode + optional external features)
# -----------------------------------------------------------------------------
class _MacroRegimeCore:
    def __init__(self, regime_weights: Dict[str, Dict[str, float]]):
        self.regime_weights = regime_weights or {}

    def ohlcv_features(self, df: pd.DataFrame) -> Dict[str, float]:
        c = df["close"].astype(float).values
        v = df["volume"].astype(float).values
        ret = np.diff(c) / (c[:-1] + 1e-12) if len(c) > 1 else np.array([0.0])
        lb = min(500, len(ret))
        ret_w = ret[-lb:] if lb else ret
        # vol_stress: janela fixa (não sqrt(n_barras) — evita LIQUIDITY_STRESS em CSV longos)
        vol_stress = float(np.std(ret_w) * np.sqrt(96)) if len(ret_w) else 0.0
        trend_persistence = _StructuralCore.persistence(c[-lb:] if lb else c)
        drawdown = 0.0
        if len(c) > 5:
            seg = c[-min(2000, len(c)) :]
            peak = np.maximum.accumulate(seg)
            dd = (seg - peak) / (peak + 1e-12)
            drawdown = float(np.min(dd))
        volume_surge = 0.0
        if len(v) > 20:
            volume_surge = float(v[-1] / (np.mean(v[-20:]) + 1e-9))
        # proxies when sem DXY/FRED
        dxy_proxy = -float((c[-1] - c[0]) / (c[0] + 1e-12)) if len(c) > 1 else 0.0
        real_yield_proxy = vol_stress * (-1 if trend_persistence > 0.55 else 1)
        defense_flow = float(min(1.0, abs(drawdown) * 5.0))
        hedge_flow = float(min(1.0, vol_stress * 2.0))
        dissipation = float(np.mean(np.abs(df["dissipation"].values))) if "dissipation" in df else 0.0
        residual = float(np.mean(np.abs(df["residual_impact"].values))) if "residual_impact" in df else 0.0
        pressure = float(df["pressure"].iloc[-1]) if "pressure" in df else 0.0
        return {
            "real_yield_proxy": real_yield_proxy,
            "dxy_proxy": dxy_proxy,
            "vol_stress": vol_stress,
            "trend_persistence": trend_persistence,
            "drawdown_stress": abs(drawdown),
            "defense_flow": defense_flow,
            "hedge_flow": hedge_flow,
            "volume_surge": volume_surge,
            "dissipation": dissipation,
            "residual": residual,
            "pressure": pressure,
        }

    def detect_regime(self, features: Dict[str, float]) -> str:
        vs = features.get("vol_stress", 0)
        dd = features.get("drawdown_stress", 0)
        tp = features.get("trend_persistence", 0)
        if vs > 0.08 and dd > 0.06:
            return "LIQUIDITY_STRESS"
        if vs > 0.05 and features.get("defense_flow", 0) > 0.3:
            return "RISK_OFF"
        if tp > 0.6 and vs < 0.012:
            return "TREND_STABLE"
        if abs(features.get("real_yield_proxy", 0)) > 0.5:
            return "MONETARY"
        return "NEUTRAL"

    def pressure_score(self, regime: str, features: Dict[str, float], extra: Dict[str, float]) -> float:
        merged = {**features, **extra}
        weights = self.regime_weights.get(regime) or self.regime_weights.get("NEUTRAL", {})
        if not weights:
            return 0.0
        score = 0.0
        for k, w in weights.items():
            score += float(merged.get(k, 0.0)) * float(w)
        return score


# -----------------------------------------------------------------------------
# USFE Master Engine
# -----------------------------------------------------------------------------
class UnifiedStructuralFieldEngine:
    """
    Motor unificado multi-classe.
    Entrada: DataFrame OHLCV + símbolo (+ features macro externas opcionais).
    Saída: UnifiedFieldResult
    """

    def __init__(
        self,
        symbol: str,
        calibration_path: Optional[Path] = None,
        class_override: Optional[AssetClass] = None,
    ):
        self.symbol = symbol
        self.asset_class = class_override or classify_symbol(symbol)
        self.calib_root = load_calibration(calibration_path)
        self.cfg = get_class_calibration(self.asset_class, self.calib_root)
        macro_w = self.calib_root.get("macro_regime_weights") or {}
        self._macro = _MacroRegimeCore(macro_w)
        self._energy = _EnergyCore(self.cfg)
        log.info(
            "USFE init symbol=%s class=%s version=%s calib=%s",
            symbol,
            self.asset_class.value,
            __version__,
            calibration_path or _DEFAULT_CALIBRATION,
        )

    def process(
        self,
        df: pd.DataFrame,
        external_macro: Optional[Dict[str, float]] = None,
        signal_direction: Optional[str] = None,
    ) -> UnifiedFieldResult:
        """
        signal_direction: 'BUY' | 'SELL' | None — usado para trade_bias vs macro.
        """
        external_macro = external_macro or {}
        raw = normalize_ohlcv_df(df)
        n = len(raw)
        if n < self.cfg.min_bars:
            return UnifiedFieldResult(
                symbol=self.symbol,
                asset_class=self.asset_class.value,
                usfe_version=__version__,
                is_valid=False,
                n_bars=n,
                block_reason=f"INSUFFICIENT_BARS need>={self.cfg.min_bars}",
            )

        hours = _hour_buckets(raw)
        closes = raw["close"].astype(float).values
        volumes = raw["volume"].astype(float).values
        volatility = pd.Series(closes).pct_change().abs().fillna(0).values

        # --- Representations (TRE) ---
        candle_dir = _direction_from_returns(closes)
        line_dir = _line_direction(closes)
        renko_dir = _renko_direction(closes, self.cfg.renko_brick_pct)

        visual_move = float(abs(closes[-1] - closes[max(0, len(closes) - 10)]))
        structural_move = float(abs(closes[-1] - closes[max(0, len(closes) - 30)]))

        trs = _TemporalCore.recurrence_strength(hours)
        session_p = _TemporalCore.session_pressure(hours, self.cfg.active_hours_utc)
        prop_delay = _TemporalCore.propagation_delay(hours)

        sps = _StructuralCore.persistence(closes)
        hpi = _StructuralCore.hidden_propagation(volumes, volatility)

        dei = abs(visual_move - structural_move) / (structural_move + 1e-9)
        attention = float(min(1.0, np.std(volumes[-20:]) / (np.mean(volumes[-20:]) + 1e-9))) if n >= 20 else 0.5
        retail_vol = float(volumes[-1] / (np.mean(volumes) + 1e-9))
        odi = _ObservationalCore.distortion(attention, retail_vol)
        conflict = _ObservationalCore.conflict(candle_dir, line_dir, renko_dir)

        # --- TEPA pipeline ---
        enriched = self._energy.enrich(raw)
        poc_price, _ = self._energy.poc(enriched)
        last = enriched.iloc[-1]
        energy_last = float(last.get("energy", 0))
        pressure_last = float(last.get("pressure", 0))
        dissipation_last = float(last.get("dissipation", 0))
        residual_last = float(last.get("residual_impact", 0))
        curvature = float(last.get("curvature", 0))
        wave_impact = float(last.get("wave_impact", 0))
        fractal_res = int(last.get("fractal_resonance", 0))
        exhaustion = int(last.get("energy_exhaustion", 0))

        # TEPA structural score (last bar)
        score = 0
        if pressure_last > self.cfg.pressure_threshold:
            score += 1
        if abs(residual_last) > self.cfg.residual_threshold:
            score += 1
        if curvature > float(enriched["curvature"].mean()):
            score += 1
        if float(last.get("geometry_fill", 0)) > float(enriched["geometry_fill"].mean()):
            score += 1
        if fractal_res >= 3:
            score += 1
        if abs(dissipation_last) > self.cfg.dissipation_threshold:
            score += 1

        if score >= 5:
            struct_sig = StructuralSignal.EXPANSION
        elif score <= 2:
            struct_sig = StructuralSignal.COLLAPSE
        else:
            struct_sig = StructuralSignal.NEUTRAL

        # --- Fusion ---
        rei = 1.0 / (1.0 + statistics.pstdev([trs, sps, hpi]) if len([trs, sps, hpi]) > 1 else 1.0)
        vol_norm = volumes / (np.sum(volumes) + 1e-9)
        eci = 0.0
        vn = vol_norm[vol_norm > 0]
        if len(vn) > 0:
            eci = float(-np.sum(vn * np.log2(vn + 1e-12)))

        macro_feat = self._macro.ohlcv_features(enriched)
        regime = self._macro.detect_regime(macro_feat)
        msp = self._macro.pressure_score(regime, macro_feat, external_macro)

        # Normalize sub-scores to 0..1 band
        def _norm01(x: float, cap: float = 3.0) -> float:
            return max(0.0, min(1.0, abs(x) / cap))

        align_vars = {
            "trs": _norm01(trs),
            "sps": sps,
            "rei": min(1.0, rei),
            "odi": min(1.0, odi),
        }
        alignment_score = float(np.mean(list(align_vars.values())))

        risk = min(
            self.cfg.risk_cap,
            eci * self.cfg.eci_risk_weight
            + _norm01(dei) * self.cfg.dei_risk_weight
            + min(1.0, conflict) * self.cfg.conflict_risk_weight,
        )

        # Trade bias
        trade_bias = TradeBias.NEUTRAL
        block_reason = ""
        risk_ratio = min(1.0, risk / max(self.cfg.risk_cap, 1e-9))
        damp = max(0.0, min(1.0, float(self.cfg.confidence_risk_damp)))
        confidence = max(
            0.0,
            min(1.0, alignment_score * (1.0 - damp * risk_ratio)),
        )

        if struct_sig == StructuralSignal.COLLAPSE or exhaustion == 1:
            trade_bias = TradeBias.BLOCK
            block_reason = "STRUCTURAL_COLLAPSE_OR_EXHAUSTION"
        elif alignment_score >= self.cfg.probability_threshold and risk <= self.cfg.risk_cap:
            if candle_dir > 0 and line_dir >= 0:
                trade_bias = TradeBias.ALLOW_LONG
            elif candle_dir < 0 and line_dir <= 0:
                trade_bias = TradeBias.ALLOW_SHORT
            else:
                trade_bias = TradeBias.NEUTRAL
                block_reason = "REPRESENTATION_MIXED"
        else:
            trade_bias = TradeBias.BLOCK
            block_reason = "LOW_PROB_OR_HIGH_RISK"

        # Macro veto (generalizado — qualquer classe)
        if signal_direction and trade_bias != TradeBias.BLOCK:
            sd = signal_direction.upper()
            if msp > self.cfg.macro_veto_high and sd == "SELL" and trade_bias == TradeBias.ALLOW_LONG:
                trade_bias = TradeBias.BLOCK
                block_reason = "MACRO_PRESSURE_VS_SIGNAL"
            elif msp < self.cfg.macro_veto_low and sd == "BUY" and trade_bias == TradeBias.ALLOW_SHORT:
                trade_bias = TradeBias.BLOCK
                block_reason = "MACRO_PRESSURE_VS_SIGNAL"

        # Apply class weights to confidence
        w = (
            self.cfg.temporal_weight * trs
            + self.cfg.structural_weight * sps
            + self.cfg.energy_weight * _norm01(pressure_last)
            + self.cfg.observational_weight * min(1.0, odi)
            + self.cfg.macro_weight * _norm01(msp)
        ) / max(
            self.cfg.temporal_weight
            + self.cfg.structural_weight
            + self.cfg.energy_weight
            + self.cfg.observational_weight
            + self.cfg.macro_weight,
            1e-9,
        )
        confidence = max(0.0, min(1.0, confidence * w))

        return UnifiedFieldResult(
            symbol=self.symbol,
            asset_class=self.asset_class.value,
            usfe_version=__version__,
            trs=trs,
            session_pressure=session_p,
            propagation_delay=prop_delay,
            sps=sps,
            hpi=hpi,
            curvature=curvature,
            wave_impact=wave_impact,
            energy_last=energy_last,
            pressure_last=pressure_last,
            dissipation_last=dissipation_last,
            residual_impact_last=residual_last,
            poc_price=poc_price,
            fractal_resonance=fractal_res,
            energy_exhaustion=exhaustion,
            dei=dei,
            odi=odi,
            representation_conflict=conflict,
            candle_direction=candle_dir,
            line_direction=line_dir,
            renko_direction=renko_dir,
            rei=rei,
            eci=eci,
            macro_regime=regime,
            macro_pressure_score=msp,
            alignment_score=alignment_score,
            probability=alignment_score,
            risk=risk,
            structural_signal=struct_sig.value,
            trade_bias=trade_bias.value,
            confidence=confidence,
            block_reason=block_reason,
            score_components=score,
            is_valid=True,
            n_bars=n,
        )


# -----------------------------------------------------------------------------
# OMEGA ComponentEngine adapter
# -----------------------------------------------------------------------------
@dataclass
class ComponentConfig:
    regime: str = "forex"
    symbol: str = "EURUSD"


class ComponentEngine:
    """Wrapper para futura entrada em _KERNEL_MODULE_MAP como chave 'usfe'."""

    def __init__(self, config: ComponentConfig):
        try:
            ac = AssetClass(config.regime)
        except ValueError:
            ac = classify_symbol(config.symbol)
        self._inner = UnifiedStructuralFieldEngine(config.symbol, class_override=ac)
        self._config = config

    @classmethod
    def from_config(cls, regime: str = "forex", symbol: str = "EURUSD", **kwargs) -> "ComponentEngine":
        sym = kwargs.get("symbol", symbol)
        return cls(ComponentConfig(regime=regime, symbol=sym))

    def compute_from_bars(self, df: pd.DataFrame, signal_direction: Optional[str] = None) -> ComponentState:
        res = self._inner.process(df, signal_direction=signal_direction)
        d = 0
        if res.trade_bias == TradeBias.ALLOW_LONG.value:
            d = 1
        elif res.trade_bias == TradeBias.ALLOW_SHORT.value:
            d = -1
        strength = (
            max(res.confidence, res.alignment_score * 0.5)
            if res.is_valid
            else 0.0
        )
        return ComponentState(
            is_valid=res.is_valid,
            direction=d,
            strength=strength,
            n_bars=res.n_bars,
            regime=self._config.regime,
            usfe=res.to_dict(),
        )


# -----------------------------------------------------------------------------
# Self-test
# -----------------------------------------------------------------------------
def _synthetic_ohlcv(
    n: int = 200,
    seed: int = 42,
    trend: str = "random",
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if trend == "uptrend":
        px = 100.0 + np.linspace(0, 12, n) + rng.normal(0, 0.08, n)
        vol = rng.integers(2000, 8000, n).astype(float)
    elif trend == "downtrend":
        px = 100.0 - np.linspace(0, 12, n) + rng.normal(0, 0.08, n)
        vol = rng.integers(2000, 8000, n).astype(float)
    else:
        px = 100.0 + np.cumsum(rng.normal(0, 0.15, n))
        vol = rng.integers(100, 5000, n).astype(float)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC"),
            "open": px,
            "high": px + rng.uniform(0, 0.3, n),
            "low": px - rng.uniform(0, 0.3, n),
            "close": px,
            "volume": vol,
        }
    )


def self_test() -> None:
    symbols = [
        ("EURUSD", AssetClass.FOREX),
        ("XAUUSD", AssetClass.COMMODITY),
        ("BTCUSD", AssetClass.CRYPTO),
        ("US500", AssetClass.INDEX),
        ("USOIL+", AssetClass.ENERGY),
    ]
    print(f"USFE self-test {__version__}")
    for sym, ac in symbols:
        for trend in ("random", "uptrend", "downtrend"):
            eng = UnifiedStructuralFieldEngine(sym, class_override=ac)
            out = eng.process(_synthetic_ohlcv(150, trend=trend))
            assert out.is_valid, f"{sym}/{trend} invalid: {out.block_reason}"
        print(f"  [{sym:8}] OK random/uptrend/downtrend")
    eng_u = UnifiedStructuralFieldEngine("EURUSD", class_override=AssetClass.FOREX)
    up = eng_u.process(_synthetic_ohlcv(200, trend="uptrend"))
    assert up.is_valid and (up.candle_direction > 0 or up.line_direction > 0), (
        f"uptrend repr failed: candle={up.candle_direction} line={up.line_direction}"
    )
    dn = eng_u.process(_synthetic_ohlcv(200, trend="downtrend"))
    assert dn.is_valid and (dn.candle_direction < 0 or dn.line_direction < 0), (
        f"downtrend repr failed: candle={dn.candle_direction} line={dn.line_direction}"
    )
    print("  [trend] candle/line direction OK (trade_bias may stay BLOCK by design)")
    ce = ComponentEngine.from_config(regime="forex", symbol="GBPUSD")
    st = ce.compute_from_bars(_synthetic_ohlcv(120))
    assert st.is_valid
    ce2 = ComponentEngine.from_config(regime="metal", symbol="XAUUSD")
    assert ce2._inner.asset_class == AssetClass.COMMODITY
    print(f"  [ComponentEngine] dir={st.direction} strength={st.strength:.3f}")
    print("USFE self-test OK")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    self_test()
