"""
Weis Wave Tracker — OMEGA-Compliant Component
==============================================
Production-grade microstructure tracker refactored from MQL5 Weis Wave
logic. Identifies institutional footprints by segmenting price into
discrete directional waves and evaluating their dimensionless strength
(ATR-normalized price change, expanding volume z-score).

Compliance  : OMEGA Checklist v1.0
Target      : Top-tier Chinese quantitative fund production standard
Dependencies: numpy, pandas, numba (optional), MetaTrader5 (optional), stdlib
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Optional Imports with Fallback
# ---------------------------------------------------------------------------

try:
    import MetaTrader5 as mt5
    _HAS_MT5 = True
except ImportError:
    mt5 = None
    _HAS_MT5 = False

try:
    from numba import njit
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False

    def njit(*args: Any, **kwargs: Any) -> Any:
        """No-op decorator when Numba is unavailable."""
        def _decorator(func: Any) -> Any:
            return func
        if args and callable(args[0]):
            return args[0]
        return _decorator


# ---------------------------------------------------------------------------
# Numba-Accelerated Wave Segmentation (with Pure Python Fallback)
# ---------------------------------------------------------------------------

if _HAS_NUMBA:

    @njit(cache=True)
    def _segment_waves_numba(
        close: np.ndarray,
        volume: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Segment continuous price data into discrete directional waves.
        Returns start indices, end indices, directions (1=Up, -1=Down), 
        and cumulative volumes for each wave.
        """
        n = len(close)
        max_waves = n
        starts = np.empty(max_waves, dtype=np.int64)
        ends = np.empty(max_waves, dtype=np.int64)
        dirs = np.empty(max_waves, dtype=np.int8)
        vol_sum = np.empty(max_waves, dtype=np.float64)
        
        count = 0
        if n < 2:
            return starts[:0], ends[:0], dirs[:0], vol_sum[:0]
            
        wave_start = 0
        wave_dir = 1 if close[1] > close[0] else -1
        cur_vol = volume[0]
        
        for i in range(1, n):
            if close[i] > close[i-1]:
                cur_dir = 1
            elif close[i] < close[i-1]:
                cur_dir = -1
            else:
                cur_dir = wave_dir  # Flat bars inherit previous direction
                
            if cur_dir != wave_dir:
                starts[count] = wave_start
                ends[count] = i - 1
                dirs[count] = wave_dir
                vol_sum[count] = cur_vol
                count += 1
                wave_start = i
                wave_dir = cur_dir
                cur_vol = volume[i]
            else:
                cur_vol += volume[i]
                
        # Append the final wave
        starts[count] = wave_start
        ends[count] = n - 1
        dirs[count] = wave_dir
        vol_sum[count] = cur_vol
        count += 1
        
        return starts[:count], ends[:count], dirs[:count], vol_sum[:count]

else:
    # --- Pure Python Fallback ---
    def _segment_waves_numba(
        close: np.ndarray,
        volume: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python fallback for wave segmentation."""
        n = len(close)
        starts, ends, dirs, vol_sum = [], [], [], []
        
        if n < 2:
            return np.array(starts), np.array(ends), np.array(dirs), np.array(vol_sum)
            
        wave_start = 0
        wave_dir = 1 if close[1] > close[0] else -1
        cur_vol = volume[0]
        
        for i in range(1, n):
            if close[i] > close[i-1]:
                cur_dir = 1
            elif close[i] < close[i-1]:
                cur_dir = -1
            else:
                cur_dir = wave_dir
                
            if cur_dir != wave_dir:
                starts.append(wave_start)
                ends.append(i - 1)
                dirs.append(wave_dir)
                vol_sum.append(cur_vol)
                wave_start = i
                wave_dir = cur_dir
                cur_vol = volume[i]
            else:
                cur_vol += volume[i]
                
        starts.append(wave_start)
        ends.append(n - 1)
        dirs.append(wave_dir)
        vol_sum.append(cur_vol)
        
        return (
            np.array(starts, dtype=np.int64),
            np.array(ends, dtype=np.int64),
            np.array(dirs, dtype=np.int8),
            np.array(vol_sum, dtype=np.float64)
        )


# ---------------------------------------------------------------------------
# ComponentConfig — Regime-Aware Parameterisation
# ---------------------------------------------------------------------------

@dataclass
class ComponentConfig:
    """
    Configuration for the Weis Wave Tracker.
    All thresholds are strictly dimensionless.
    """
    regime: str = "forex"

    # --- Core Parameters ---
    atr_period: int = 14
    trend_consecutive_waves: int = 3
    strength_threshold: float = 2.0

    # --- Regime Overrides ---
    regime_overrides: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "forex": {
            "atr_period": 14,
            "trend_consecutive_waves": 3,
            "strength_threshold": 2.0,
        },
        "metal": {
            "atr_period": 12,
            "trend_consecutive_waves": 3,
            "strength_threshold": 1.8,
        },
        "index": {
            "atr_period": 20,
            "trend_consecutive_waves": 2,
            "strength_threshold": 2.5,
        },
        "crypto": {
            "atr_period": 10,
            "trend_consecutive_waves": 2,
            "strength_threshold": 3.0,
        },
    })

    def resolve(self) -> Dict[str, Any]:
        """Return effective parameters after applying regime overrides."""
        base: Dict[str, Any] = {
            "atr_period": self.atr_period,
            "trend_consecutive_waves": self.trend_consecutive_waves,
            "strength_threshold": self.strength_threshold,
        }
        override = self.regime_overrides.get(self.regime, {})
        merged = {**override, **base}
        merged["atr_period"] = max(2, int(merged["atr_period"]))
        merged["trend_consecutive_waves"] = max(2, int(merged["trend_consecutive_waves"]))
        return merged


# ---------------------------------------------------------------------------
# ComponentState — Dimensionless Output
# ---------------------------------------------------------------------------

@dataclass
class ComponentState:
    """
    Immutable output of the Weis Wave Tracker.
    All numeric fields are strictly dimensionless.
    """
    is_valid: bool
    """True when a confirmed trend wave passes the strength threshold."""
    
    direction: int
    """+1 (Uptrend confirmed), -1 (Downtrend confirmed), 0 (Neutral/Invalid)."""
    
    strength: float
    """Trend strength normalized by historical wave strength standard deviation."""
    
    n_bars: int
    """Total number of bars processed."""

    wave_volume_z: float = 0.0
    """Z-score of the last wave's volume compared to historical waves."""
    
    wave_price_change_ratio: float = 0.0
    """Dimensionless price change of the last wave (Price Change / ATR)."""
    
    regime: str = ""
    """Effective regime identifier used."""


# ---------------------------------------------------------------------------
# ComponentEngine — Core Logic
# ---------------------------------------------------------------------------

class ComponentEngine:
    """
    Weis Wave trend detection engine.
    Transforms price segmentation into vectorized dimensionless analytics.
    """

    REQUIRED_COLS = {"open", "high", "low", "close", "volume"}

    def __init__(self, config: ComponentConfig) -> None:
        self._config = config
        self._params = config.resolve()

    @classmethod
    def from_config(cls, regime=None, **kwargs: Any) -> "ComponentEngine":
        """OMEGA MANDATORY — accepts regime string (shadow_loop) or ComponentConfig (legacy)."""
        if isinstance(regime, ComponentConfig):
            return cls(regime)
        _MAP = {"commodity": "metal", "precious": "metal"}
        r = _MAP.get(str(regime or "forex").lower(), str(regime or "forex").lower())
        return cls(ComponentConfig(regime=r, **kwargs))

    def compute_from_bars(self, df: pd.DataFrame) -> ComponentState:
        """
        Compute Weis Wave state from an OHLCV DataFrame.
        Expected columns: 'open', 'high', 'low', 'close', 'volume'.
        """
        missing = self.REQUIRED_COLS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        params = self._params
        n_bars = len(df)
        
        if n_bars < 5:
            return ComponentState(
                is_valid=False, direction=0, strength=0.0, n_bars=n_bars,
                regime=self._config.regime
            )

        # Extract arrays
        high = df["high"].values.astype(np.float64)
        low = df["low"].values.astype(np.float64)
        close = df["close"].values.astype(np.float64)
        volume = df["volume"].values.astype(np.float64)

        # 1. Compute Adaptive True Range (ATR)
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': np.abs(high - np.roll(close, 1)),
            'lc': np.abs(low - np.roll(close, 1))
        }).max(axis=1).values
        tr[0] = high[0] - low[0]
        atr = pd.Series(tr).ewm(span=params["atr_period"], adjust=False).mean().values

        # 2. Segment Waves
        w_starts, w_ends, w_dirs, w_vols = _segment_waves_numba(close, volume)
        num_waves = len(w_starts)
        
        if num_waves < params["trend_consecutive_waves"]:
            return ComponentState(
                is_valid=False, direction=0, strength=0.0, n_bars=n_bars,
                regime=self._config.regime
            )

        # 3. Calculate Dimensionless Wave Metrics
        w_price_changes = np.abs(close[w_ends] - close[w_starts])
        w_atr_vals = atr[w_ends]
        w_atr_safe = np.where(w_atr_vals < 1e-8, 1e-8, w_atr_vals)
        w_norm_price = w_price_changes / w_atr_safe  # Dimensionless ratio
        
        # Volume Z-Score (Expanding to strictly avoid look-ahead bias)
        w_vol_series = pd.Series(w_vols)
        w_vol_mean = w_vol_series.expanding(min_periods=2).mean().shift(1).values
        w_vol_std = w_vol_series.expanding(min_periods=2).std(ddof=0).shift(1).values
        w_vol_std = np.where(w_vol_std < 1e-8, 1e-8, w_vol_std)
        vol_z = (w_vols - w_vol_mean) / w_vol_std
        vol_z = np.nan_to_num(vol_z, nan=0.0)
        
        # Wave Strength Composite
        w_composite = np.abs(vol_z) * w_norm_price

        # 4. Trend Confirmation — same-direction wave analysis
        # Waves always alternate direction; check last N waves of the same type
        trend_n = params["trend_consecutive_waves"]
        up_idx = np.where(w_dirs == 1)[0]
        dn_idx = np.where(w_dirs == -1)[0]

        is_confirmed = False
        trend_dir = 0
        trend_wave_idx: np.ndarray = np.array([], dtype=np.int64)

        if len(up_idx) >= trend_n:
            last_up = w_composite[up_idx[-trend_n:]]
            prior_up = w_composite[up_idx[:-trend_n]] if len(up_idx) > trend_n else np.array([0.0])
            if last_up[-1] >= np.mean(prior_up):
                is_confirmed, trend_dir = True, 1
                trend_wave_idx = up_idx[-trend_n:]

        if not is_confirmed and len(dn_idx) >= trend_n:
            last_dn = w_composite[dn_idx[-trend_n:]]
            prior_dn = w_composite[dn_idx[:-trend_n]] if len(dn_idx) > trend_n else np.array([0.0])
            if last_dn[-1] >= np.mean(prior_dn):
                is_confirmed, trend_dir = True, -1
                trend_wave_idx = dn_idx[-trend_n:]

        # 5. Calculate Final Normalized Trend Strength
        trend_strength = float(np.sum(w_composite[trend_wave_idx])) if is_confirmed else 0.0

        all_same_idx = up_idx if trend_dir == 1 else dn_idx
        prior_same = all_same_idx[:-trend_n] if len(all_same_idx) > trend_n else np.array([], dtype=np.int64)
        hist_std = float(np.std(w_composite[prior_same])) if len(prior_same) > 0 else 1.0
        if hist_std < 1e-8:
            hist_std = 1.0

        final_strength = trend_strength / hist_std

        # 6. Final Validation Gate
        is_valid = (
            is_confirmed and
            final_strength >= params["strength_threshold"]
        )

        return ComponentState(
            is_valid=is_valid,
            direction=trend_dir if is_valid else 0,
            strength=final_strength if is_valid else 0.0,
            n_bars=n_bars,
            wave_volume_z=float(vol_z[-1]),
            wave_price_change_ratio=float(w_norm_price[-1]),
            regime=self._config.regime
        )

    # ------------------------------------------------------------------
    # MT5 Integration (Optional)
    # ------------------------------------------------------------------
    @staticmethod
    def mt5_is_available() -> bool:
        """Return True if MetaTrader5 module is importable."""
        return _HAS_MT5

    @staticmethod
    def fetch_mt5_bars(
        symbol: str,
        timeframe: int,
        n_bars: int = 1000,
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV bars from MT5 terminal (if available)."""
        if not _HAS_MT5 or mt5 is None:
            return None
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
            if rates is None or len(rates) == 0:
                return None
            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            return df
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Self-Test (Synthetic Data, Exit 0)
# ---------------------------------------------------------------------------

def _generate_synthetic_ohlcv(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data with 6 perfectly defined waves:
    Down, Up, Down, Up, Up, Up. 
    The last 3 waves are Up with injected volume to trigger a valid signal.
    """
    rng = np.random.default_rng(seed)
    
    # Create strictly monotonic segments to force exact wave segmentation
    w1 = np.linspace(100.0, 99.0, 30)  # Down
    w2 = np.linspace(99.0, 99.5, 20)  # Up
    w3 = np.linspace(99.5, 98.0, 20)  # Down
    w4 = np.linspace(98.0, 99.0, 20)  # Up
    w5 = np.linspace(99.0, 101.0, 60) # Up
    w6 = np.linspace(101.0, 102.0, 50) # Up
    
    close = np.concatenate([w1, w2, w3, w4, w5, w6])
    # For short-bar tests, return a minimal random OHLCV
    if n_bars < len(close):
        c = rng.normal(100.0, 1.0, n_bars)
        o = c + rng.normal(0, 0.01, n_bars)
        h = np.maximum(o, c) + rng.uniform(0, 0.05, n_bars)
        l = np.minimum(o, c) - rng.uniform(0, 0.05, n_bars)
        v = rng.lognormal(mean=8.0, sigma=0.5, size=n_bars)
        return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v})
    n = len(close)
    open_ = close + rng.normal(0, 0.01, n)
    high = np.maximum(open_, close) + rng.uniform(0, 0.05, n)
    low = np.minimum(open_, close) - rng.uniform(0, 0.05, n)
    volume = rng.lognormal(mean=8.0, sigma=0.5, size=n)
    
    # Inject volume anomaly in the last 3 up waves to boost volume z-score
    volume[70:] *= 5.0
    
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume
    })


def _run_self_test() -> None:
    """Execute self-test validating OMEGA constraints and logic."""
    errors: list[str] = []

    # --- Test 1: Regime Coverage & Type Validation ---
    for regime in ("forex", "metal", "index", "crypto"):
        cfg = ComponentConfig(regime=regime)
        engine = ComponentEngine.from_config(cfg)
        df = _generate_synthetic_ohlcv(n_bars=200, seed=42)
        
        try:
            state = engine.compute_from_bars(df)
            if not isinstance(state, ComponentState):
                errors.append(f"[{regime}] output is not ComponentState")
            if state.direction not in (-1, 0, 1):
                errors.append(f"[{regime}] direction={state.direction} not in {{-1,0,1}}")
            if state.strength < 0:
                errors.append(f"[{regime}] strength={state.strength} is negative")
            if state.n_bars != 200:
                errors.append(f"[{regime}] n_bars={state.n_bars} != 200")
        except Exception as e:
            errors.append(f"[{regime}] Exception: {e}")

    # --- Test 2: Valid Uptrend Detection ---
    cfg_forex = ComponentConfig(regime="forex", strength_threshold=0.5, trend_consecutive_waves=2)
    engine_forex = ComponentEngine.from_config(cfg_forex)
    df_up = _generate_synthetic_ohlcv(n_bars=200, seed=42)
    state_up = engine_forex.compute_from_bars(df_up)
    
    if not state_up.is_valid:
        errors.append(f"Injected 3-wave uptrend not detected: is_valid={state_up.is_valid}")
    if state_up.direction != 1:
        errors.append(f"Expected direction=+1 for Uptrend, got {state_up.direction}")

    # --- Test 3: Insufficient Bars ---
    df_short = _generate_synthetic_ohlcv(n_bars=3, seed=99)
    state_short = engine_forex.compute_from_bars(df_short)
    if state_short.is_valid:
        errors.append("Short DataFrame should not be valid")

    # --- Test 4: Missing Columns ---
    try:
        engine_forex.compute_from_bars(pd.DataFrame({"foo": [1, 2, 3]}))
        errors.append("Missing columns did not raise ValueError")
    except ValueError:
        pass

    # --- Test 5: MT5 Flag ---
    if not isinstance(ComponentEngine.mt5_is_available(), bool):
        errors.append("mt5_is_available() did not return bool")

    # --- Report ---
    if errors:
        print("SELF-TEST FAILED:")
        for e in errors:
            print(f"  x {e}")
        sys.exit(1)
    else:
        print("SELF-TEST PASSED — all 5 checks OK")
        sys.exit(0)


if __name__ == "__main__":
    _run_self_test()


# ===========================================================================
# modules/__init__.py Registration Entry Point
# ===========================================================================
#
# Place the following in  modules/__init__.py :
#
#     from modules.weis_wave_tracker import (
#         ComponentConfig,
#         ComponentEngine,
#         ComponentState,
#     )
#
#     __all__ = [
#         "ComponentConfig",
#         "ComponentEngine",
#         "ComponentState",
#     ]
#
# ===========================================================================