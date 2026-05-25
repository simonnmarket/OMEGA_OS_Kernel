#!/usr/bin/env python3
"""
Microstructure Tracker - OMEGA Compliant Component
===================================================
Production-grade microstructure imbalance detection for quantitative trading.

This module implements a tick-level microstructure tracker that detects order flow
imbalances using Welford's online algorithm for efficient variance computation.
All metrics are dimensionless (z-scores, ratios, percentiles) for regime-agnostic operation.

Author: OMEGA Red Team Architect
Compliance: Full OMEGA Checklist Standard
Target: Top-tier Chinese quant funds (High-Flyer, Nine-Dimensional, Ming-Hong)

Dependencies:
    - numpy (required)
    - pandas (required)
    - numba (optional, JIT acceleration with pure-Python fallback)
    - MetaTrader5 (optional, live feed integration with stub fallback)
"""

from __future__ import annotations

import sys
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import deque

import numpy as np
import pandas as pd

# ============================================================================
# Optional Imports with Fallback - OMEGA MANDATORY
# ============================================================================
try:
    import MetaTrader5 as mt5
    _HAS_MT5 = True
except ImportError:
    mt5 = None
    _HAS_MT5 = False

try:
    from numba import jit, njit, prange
    _HAS_NUMBA = True
except ImportError:
    # Fallback: no-op decorators that return the original function
    def jit(*args, **kwargs):
        """No-op JIT decorator for environments without Numba."""
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    def njit(*args, **kwargs):
        """No-op NJIT decorator for environments without Numba."""
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    def prange(*args, **kwargs):
        """Fallback prange to standard range."""
        return range(*args)

    _HAS_NUMBA = False

# Module logger
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================
class RegimeType(str, Enum):
    """
    Trading regime types for parameter adaptation.
    
    Each regime has distinct microstructure characteristics:
    - FOREX: High liquidity, tight spreads, central bank interventions
    - METAL: Medium liquidity, gold/silver specific patterns
    - INDEX: Basket-driven, low tick-to-bar ratio
    - CRYPTO: 24/7 trading, high volatility, exchange fragmentation
    """
    FOREX = "forex"
    METAL = "metal"
    INDEX = "index"
    CRYPTO = "crypto"


# ============================================================================
# OMEGA MANDATORY: ComponentConfig Dataclass
# ============================================================================
@dataclass
class ComponentConfig:
    """
    Configuration container for MicrostructureTracker parameters.
    
    All thresholds and parameters are fully configurable by trading regime.
    No hardcoded values - OMEGA MANDATORY compliance.
    
    Attributes:
        regime: Trading regime type for parameter adaptation.
        lookback: Number of ticks/bars to maintain in rolling window.
        z_threshold: Z-score threshold for imbalance detection.
        min_bars: Minimum bars required before producing valid output.
        volume_column: Name of volume column in input DataFrame.
        buyer_maker_column: Name of buyer maker flag column in input DataFrame.
        close_column: Name of close price column (optional, for validation).
        imbalance_smoothing: Exponential smoothing factor for strength signal [0, 1].
    """
    regime: RegimeType = RegimeType.CRYPTO
    lookback: Optional[int] = None
    z_threshold: Optional[float] = None
    min_bars: Optional[int] = None
    volume_column: str = "volume"
    buyer_maker_column: str = "is_buyer_maker"
    close_column: str = "close"
    imbalance_smoothing: Optional[float] = None

    # Regime-specific defaults - all dimensionless or count-based
    _REGIME_DEFAULTS: Dict[RegimeType, Dict[str, float]] = field(default_factory=lambda: {
        RegimeType.FOREX: {
            "lookback": 100,
            "z_threshold": 2.5,
            "imbalance_smoothing": 0.05,
            "min_bars": 20,
        },
        RegimeType.METAL: {
            "lookback": 75,
            "z_threshold": 3.0,
            "imbalance_smoothing": 0.08,
            "min_bars": 15,
        },
        RegimeType.INDEX: {
            "lookback": 50,
            "z_threshold": 2.0,
            "imbalance_smoothing": 0.12,
            "min_bars": 10,
        },
        RegimeType.CRYPTO: {
            "lookback": 50,
            "z_threshold": 3.0,
            "imbalance_smoothing": 0.10,
            "min_bars": 10,
        },
    })

    def get_effective_params(self) -> Dict[str, Any]:
        """Get effective parameters: regime defaults as baseline, explicit (non-None) values override."""
        _ABS = {"lookback": 50, "z_threshold": 3.0, "min_bars": 10,
                "imbalance_smoothing": 0.10, "volume_column": "volume",
                "buyer_maker_column": "is_buyer_maker", "close_column": "close"}
        result = dict(_ABS)
        regime_defaults = self._REGIME_DEFAULTS.get(self.regime, {})
        result.update(regime_defaults)
        if self.lookback is not None:           result["lookback"] = self.lookback
        if self.z_threshold is not None:        result["z_threshold"] = self.z_threshold
        if self.min_bars is not None:           result["min_bars"] = self.min_bars
        if self.imbalance_smoothing is not None: result["imbalance_smoothing"] = self.imbalance_smoothing
        result["volume_column"] = self.volume_column
        result["buyer_maker_column"] = self.buyer_maker_column
        result["close_column"] = self.close_column
        return result


# ============================================================================
# OMEGA MANDATORY: ComponentState Dataclass
# ============================================================================
@dataclass
class ComponentState:
    """
    Output state container for microstructure analysis.
    
    Core output fields - OMEGA MANDATORY:
    - is_valid: Boolean validity flag
    - direction: Integer direction (+1/-1/0)
    - strength: Dimensionless strength (z-score)
    - n_bars: Number of bars processed
    
    Extended dimensionless metrics for downstream consumers:
    - cumulative_delta_ratio: Normalized order flow in [-1, +1]
    - mean_delta_zscore: Raw z-score of mean tick delta
    - imbalance_percentile: Non-parametric percentile rank [0, 100]
    
    Attributes:
        is_valid: Whether the signal is valid and actionable.
        direction: Trade direction (+1 = buyer aggression, -1 = seller, 0 = neutral).
        strength: Dimensionless signal strength (smoothed z-score).
        n_bars: Total bars processed in current computation window.
        cumulative_delta_ratio: Cumulative delta normalized by total volume [-1, +1].
        mean_delta_zscore: Z-score of mean tick delta (unsmoothed).
        imbalance_percentile: Percentile rank of current imbalance vs history [0, 100].
        timestamp_ns: Nanosecond timestamp of computation (0 if unavailable).
    """
    is_valid: bool = False
    direction: int = 0
    strength: float = 0.0
    n_bars: int = 0
    cumulative_delta_ratio: float = 0.0
    mean_delta_zscore: float = 0.0
    imbalance_percentile: float = 50.0
    timestamp_ns: int = 0


# ============================================================================
# Core Statistical Utilities
# ============================================================================
class WelfordStats:
    """
    Online mean/variance computation using Welford's algorithm.
    
    Numerically stable O(1) update per observation without storing full history.
    Used for real-time z-score computation of tick deltas.
    
    Note: Explicit instance attributes (no __slots__) to avoid OMEGA PROHIBITED
    structural error of slots + Lock incompatibility if threading is added later.
    
    Attributes:
        count: Number of observations processed.
        mean: Running mean of observations.
        m2: Running sum of squared deviations from mean.
    """

    def __init__(self) -> None:
        """Initialize empty statistics."""
        self.count: int = 0
        self.mean: float = 0.0
        self.m2: float = 0.0

    def update(self, x: float) -> None:
        """
        Update running statistics with a single observation.
        
        Uses numerically stable two-pass update to avoid catastrophic cancellation.
        
        Args:
            x: New observation value.
        """
        self.count += 1
        delta = x - self.mean
        self.mean += delta / self.count
        delta2 = x - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        """
        Population variance (Bessel's correction NOT used for z-scores).
        
        Returns:
            Population variance, or 0.0 if insufficient observations.
        """
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    @property
    def std(self) -> float:
        """
        Population standard deviation with numerical safety floor.
        
        Returns:
            Population std dev, or 1e-8 floor to prevent division by zero.
        """
        v = self.variance
        return float(np.sqrt(v)) if v > 0 else 1e-8

    def reset(self) -> None:
        """Reset all statistics to initial state."""
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0

    def get_zscore(self, x: float) -> float:
        """
        Compute z-score of a value against current distribution.
        
        Args:
            x: Value to score.
            
        Returns:
            Z-score, or 0.0 if insufficient observations.
        """
        if self.count < 2:
            return 0.0
        return (x - self.mean) / self.std


# ============================================================================
# Vectorized Computation Functions (Numba-accelerated with fallback)
# ============================================================================
def _compute_deltas_vectorized(
    volumes: np.ndarray,
    is_buyer_maker: np.ndarray,
) -> np.ndarray:
    """
    Vectorized tick delta computation.
    
    Delta convention:
    - Buyer aggressor (buyer_maker=False): delta = +volume
    - Seller aggressor (buyer_maker=True): delta = -volume
    
    Args:
        volumes: Array of trade volumes.
        is_buyer_maker: Boolean array (True = seller-initiated trade).
        
    Returns:
        Array of signed deltas as float64.
    """
    deltas = np.where(is_buyer_maker, -volumes, volumes)
    return deltas.astype(np.float64)


def _compute_rolling_stats_vectorized(
    deltas: np.ndarray,
    min_periods: int = 10,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Vectorized rolling mean, std, and z-score using Welford's algorithm.
    
    Args:
        deltas: Array of tick deltas.
        min_periods: Minimum observations before producing valid stats.
        
    Returns:
        Tuple of (means, stds, z_scores) arrays.
    """
    n = len(deltas)
    means = np.zeros(n, dtype=np.float64)
    stds = np.zeros(n, dtype=np.float64)
    z_scores = np.zeros(n, dtype=np.float64)

    running_mean = 0.0
    running_m2 = 0.0

    for i in range(n):
        delta = deltas[i] - running_mean
        running_mean += delta / (i + 1)
        delta2 = deltas[i] - running_mean
        running_m2 += delta * delta2

        means[i] = running_mean

        if i + 1 >= 2:
            variance = running_m2 / (i + 1)
            stds[i] = np.sqrt(variance) if variance > 0 else 1e-8
        else:
            stds[i] = 1e-8

        if i + 1 >= min_periods:
            z_scores[i] = running_mean / stds[i]

    return means, stds, z_scores


def _compute_cumulative_delta_ratio(
    deltas: np.ndarray,
    volumes: np.ndarray,
    window: int,
) -> np.ndarray:
    """
    Compute rolling cumulative delta ratio (dimensionless).
    
    Formula: ratio = sum(deltas) / sum(volumes) over rolling window.
    Range: [-1, +1] where +1 = all buyer-initiated, -1 = all seller-initiated.
    
    Args:
        deltas: Array of signed deltas.
        volumes: Array of absolute volumes.
        window: Rolling window size.
        
    Returns:
        Array of cumulative delta ratios.
    """
    n = len(deltas)
    ratios = np.zeros(n, dtype=np.float64)

    if n < window:
        return ratios

    # Pre-compute cumulative sums for O(n) window computation
    cum_deltas = np.cumsum(deltas)
    cum_volumes = np.cumsum(volumes)

    # Pad with zero at front for window subtraction
    cum_deltas_padded = np.concatenate(([0.0], cum_deltas))
    cum_volumes_padded = np.concatenate(([0.0], cum_volumes))

    for i in range(window - 1, n):
        window_delta = cum_deltas_padded[i + 1] - cum_deltas_padded[i + 1 - window]
        window_vol = cum_volumes_padded[i + 1] - cum_volumes_padded[i + 1 - window]

        if window_vol > 0:
            ratios[i] = window_delta / window_vol
        else:
            ratios[i] = 0.0

    return ratios


def _compute_percentile_rank(
    value: float,
    reference_array: np.ndarray,
) -> float:
    """
    Compute percentile rank of a value against reference array.
    
    Args:
        value: Value to rank.
        reference_array: Reference distribution.
        
    Returns:
        Percentile rank in [0, 100].
    """
    if len(reference_array) == 0:
        return 50.0
    count_leq = np.sum(reference_array <= value)
    percentile = count_leq / len(reference_array) * 100.0
    return float(min(100.0, max(0.0, percentile)))


# Apply Numba JIT if available (pure-Python fallback already defined)
if _HAS_NUMBA:
    _compute_deltas_vectorized = njit(_compute_deltas_vectorized)
    _compute_rolling_stats_vectorized = njit(_compute_rolling_stats_vectorized)
    _compute_cumulative_delta_ratio = njit(_compute_cumulative_delta_ratio)
    _compute_percentile_rank = njit(_compute_percentile_rank)


# ============================================================================
# OMEGA MANDATORY: ComponentEngine Class
# ============================================================================
class ComponentEngine:
    """
    Microstructure imbalance detection engine.
    
    Implements OMEGA MANDATORY interface:
        compute_from_bars(self, df: pd.DataFrame) -> ComponentState
    
    Detection methodology:
    1. Tick delta aggregation: buyer vs seller aggression quantification
    2. Welford's online z-score: statistical significance of imbalance
    3. Cumulative delta ratio: regime-independent order flow measurement
    4. Exponential smoothing: noise reduction for signal stability
    
    All outputs are dimensionless (z-scores, ratios, percentiles) per OMEGA mandate.
    
    Attributes:
        config: ComponentConfig instance with all parameters.
        _params: Effective parameters after regime defaults applied.
    """

    def __init__(
        self,
        config: Optional[ComponentConfig] = None,
    ) -> None:
        """
        Initialize microstructure tracker.
        
        Args:
            config: Component configuration. Uses CRYPTO defaults if None.
        """
        self.config = config or ComponentConfig()
        self._params = self.config.get_effective_params()
        self._welford = WelfordStats()
        self._delta_buffer: deque = deque(maxlen=self._params["lookback"])
        self._volume_buffer: deque = deque(maxlen=self._params["lookback"])
        self._cumulative_delta: float = 0.0
        self._total_volume: float = 0.0
        self._n_bars_processed: int = 0
        self._smoothed_strength: float = 0.0
        self._zscore_history: List[float] = []

        logger.debug(
            f"ComponentEngine initialized: regime={self.config.regime.value}, "
            f"lookback={self._params['lookback']}, "
            f"z_threshold={self._params['z_threshold']}"
        )

    @classmethod
    def from_config(cls, regime=None, **kwargs: Any) -> "ComponentEngine":
        """
        OMEGA MANDATORY — accepts regime string (shadow_loop) or ComponentConfig (legacy).
        Maps 'commodity' to 'crypto' for exchange-traded metals.
        """
        if isinstance(regime, ComponentConfig):
            return cls(config=regime)
        _MAP = {"commodity": "crypto", "precious": "crypto"}
        r = _MAP.get(str(regime or "forex").lower(), str(regime or "forex").lower())
        try:
            r_enum = RegimeType(r)
        except ValueError:
            r_enum = RegimeType.CRYPTO
        config = ComponentConfig(regime=r_enum, **kwargs)
        return cls(config=config)

    def reset(self) -> None:
        """
        Reset all internal state for fresh computation.
        
        Clears all buffers and statistics while preserving config.
        """
        self._welford.reset()
        self._delta_buffer.clear()
        self._volume_buffer.clear()
        self._cumulative_delta = 0.0
        self._total_volume = 0.0
        self._n_bars_processed = 0
        self._smoothed_strength = 0.0
        self._zscore_history.clear()
        logger.debug("ComponentEngine state reset")

    def compute_from_bars(self, df: pd.DataFrame) -> ComponentState:
        """
        Compute microstructure state from OHLCV+tick DataFrame.
        
        OMEGA MANDATORY interface. Expects DataFrame with columns:
        - {volume_column}: Trade volume (default: 'volume')
        - {buyer_maker_column}: Boolean flag, True = seller-initiated (default: 'is_buyer_maker')
        - {close_column}: Optional close price for timestamp extraction
        
        Args:
            df: DataFrame with required columns. Can be empty.
            
        Returns:
            ComponentState with is_valid, direction, strength, n_bars.
            If input is invalid, returns state with is_valid=False.
        """
        # Validate input
        if df is None or df.empty:
            return ComponentState(is_valid=False, n_bars=0)

        vol_col = self._params["volume_column"]
        bmk_col = self._params["buyer_maker_column"]

        if vol_col not in df.columns or bmk_col not in df.columns:
            logger.warning(
                f"Missing required columns: need '{vol_col}' and '{bmk_col}', "
                f"got {list(df.columns)}"
            )
            return ComponentState(is_valid=False, n_bars=len(df))

        # Extract arrays for vectorized computation
        volumes = df[vol_col].values.astype(np.float64)
        is_buyer_maker = df[bmk_col].values.astype(bool)
        n_bars = len(df)

        # Compute deltas: +vol for buyer aggressive, -vol for seller aggressive
        deltas = _compute_deltas_vectorized(volumes, is_buyer_maker)

        # Update rolling buffers and Welford stats
        for delta, vol in zip(deltas, volumes):
            self._delta_buffer.append(delta)
            self._volume_buffer.append(vol)
            self._cumulative_delta += delta
            self._total_volume += vol
            self._welford.update(delta)

        self._n_bars_processed += n_bars

        # Check minimum bar requirement
        min_bars = self._params["min_bars"]

        if len(self._delta_buffer) < min_bars:
            return ComponentState(
                is_valid=False,
                n_bars=self._n_bars_processed,
            )

        # Compute dimensionless metrics
        z_threshold = self._params["z_threshold"]
        smoothing = self._params["imbalance_smoothing"]

        # Metric 1: Z-score of mean delta (primary signal)
        mean_delta = self._welford.mean
        std_delta = self._welford.std
        z_score = mean_delta / std_delta if std_delta > 1e-9 else 0.0

        # Track z-score history for percentile computation
        self._zscore_history.append(abs(z_score))
        # Keep history bounded
        max_history = self._params["lookback"] * 2
        if len(self._zscore_history) > max_history:
            self._zscore_history = self._zscore_history[-max_history:]

        # Metric 2: Cumulative delta ratio [-1, +1]
        delta_ratio = (
            self._cumulative_delta / self._total_volume
            if self._total_volume > 0
            else 0.0
        )

        # Metric 3: Imbalance percentile (non-parametric)
        if self._zscore_history:
            z_arr = np.array(self._zscore_history)
            imbalance_percentile = _compute_percentile_rank(abs(z_score), z_arr)
        else:
            imbalance_percentile = 50.0

        # Apply exponential smoothing to strength
        raw_strength = abs(z_score)
        self._smoothed_strength = (
            smoothing * raw_strength + (1 - smoothing) * self._smoothed_strength
        )

        # Determine validity and direction
        is_valid = bool(self._smoothed_strength > z_threshold)
        direction = int(1 if mean_delta > 0 else -1) if is_valid else 0

        # Extract timestamp if available (try DatetimeIndex, then integer index)
        timestamp_ns = 0
        try:
            idx = df.index[-1]
            if hasattr(idx, "timestamp"):
                timestamp_ns = int(idx.timestamp() * 1e9)
            elif isinstance(idx, (int, np.integer)):
                timestamp_ns = int(idx)
        except (AttributeError, TypeError, IndexError):
            timestamp_ns = 0

        return ComponentState(
            is_valid=is_valid,
            direction=direction,
            strength=float(self._smoothed_strength),
            n_bars=self._n_bars_processed,
            cumulative_delta_ratio=float(delta_ratio),
            mean_delta_zscore=float(z_score),
            imbalance_percentile=float(imbalance_percentile),
            timestamp_ns=timestamp_ns,
        )

    def feed_tick(
        self,
        volume: float,
        is_buyer_maker: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Legacy tick-by-tick interface for backward compatibility.
        
        Processes single tick and returns signal dict if threshold exceeded.
        Note: For batch processing, prefer compute_from_bars().
        
        Args:
            volume: Trade volume (must be non-negative).
            is_buyer_maker: True if seller-initiated trade.
            
        Returns:
            Dict with signal data if threshold exceeded, else None.
        """
        if volume < 0:
            logger.warning("Negative volume received, clamping to 0")
            volume = 0.0

        delta = -float(volume) if is_buyer_maker else float(volume)

        self._delta_buffer.append(delta)
        self._cumulative_delta += delta
        self._total_volume += volume
        self._welford.update(delta)
        self._n_bars_processed += 1

        min_bars = self._params["min_bars"]

        if len(self._delta_buffer) < min_bars:
            return None

        z_score = self._welford.mean / self._welford.std

        # Track history
        self._zscore_history.append(abs(z_score))

        smoothing = self._params["imbalance_smoothing"]
        self._smoothed_strength = (
            smoothing * abs(z_score) + (1 - smoothing) * self._smoothed_strength
        )

        if self._smoothed_strength <= self._params["z_threshold"]:
            return None

        direction_str = "AGGRESSOR_BUY" if self._welford.mean > 0 else "AGGRESSOR_SELL"
        delta_ratio = (
            self._cumulative_delta / self._total_volume
            if self._total_volume > 0
            else 0.0
        )

        return {
            "type": "MICRO_IMBALANCE",
            "direction": direction_str,
            "strength": float(self._smoothed_strength),
            "cumulative_delta": float(self._cumulative_delta),
            "mean_delta": float(self._welford.mean),
            "z_score": float(z_score),
            "delta_ratio": float(delta_ratio),
        }

    @property
    def current_state(self) -> ComponentState:
        """
        Get current state without processing new data.
        
        Returns snapshot of current internal state as ComponentState.
        Useful for polling the engine status.
        
        Returns:
            ComponentState reflecting current buffer state.
        """
        if len(self._delta_buffer) < self._params["min_bars"]:
            return ComponentState(
                is_valid=False,
                n_bars=self._n_bars_processed,
            )

        z_score = self._welford.mean / self._welford.std
        delta_ratio = (
            self._cumulative_delta / self._total_volume
            if self._total_volume > 0
            else 0.0
        )

        is_valid = bool(self._smoothed_strength > self._params["z_threshold"])
        direction = int(1 if self._welford.mean > 0 else -1) if is_valid else 0

        return ComponentState(
            is_valid=is_valid,
            direction=direction,
            strength=float(self._smoothed_strength),
            n_bars=self._n_bars_processed,
            cumulative_delta_ratio=float(delta_ratio),
            mean_delta_zscore=float(z_score),
            imbalance_percentile=float(
                _compute_percentile_rank(
                    abs(z_score),
                    np.array(self._zscore_history) if self._zscore_history else np.array([0.0]),
                )
            ),
        )


# ============================================================================
# Factory Function
# ============================================================================
def create_engine(
    regime: str = "crypto",
    lookback: Optional[int] = None,
    z_threshold: Optional[float] = None,
    **kwargs: Any,
) -> ComponentEngine:
    """
    Factory function for engine creation with simplified interface.
    
    Args:
        regime: Trading regime (forex/metal/index/crypto).
        lookback: Rolling window size for tick buffer.
        z_threshold: Z-score threshold for signal generation.
        **kwargs: Additional ComponentConfig parameters.
        
    Returns:
        Configured ComponentEngine instance.
        
    Example:
        >>> engine = create_engine(regime="forex", lookback=100)
        >>> state = engine.compute_from_bars(df)
    """
    try:
        regime_enum = RegimeType(regime.lower())
    except ValueError:
        logger.warning(f"Unknown regime '{regime}', defaulting to CRYPTO")
        regime_enum = RegimeType.CRYPTO

    config = ComponentConfig(
        regime=regime_enum,
        lookback=lookback,
        z_threshold=z_threshold,
        **kwargs,
    )
    return ComponentEngine.from_config(config)


# ============================================================================
# Synthetic Data Generator for Self-Testing
# ============================================================================
def _generate_synthetic_tick_data(
    n_ticks: int = 200,
    imbalance_period: int = 50,
    imbalance_strength: float = 0.7,
    base_price: float = 50000.0,
) -> pd.DataFrame:
    """
    Generate synthetic tick data for self-testing.
    
    Creates alternating periods of neutral and imbalanced order flow
    to verify threshold detection and direction assignment.
    
    Args:
        n_ticks: Total number of ticks to generate.
        imbalance_period: Length of imbalance injection periods.
        imbalance_strength: Buyer-initiated probability during imbalance (>0.5 = buyer bias).
        base_price: Starting price level for close column.
        
    Returns:
        DataFrame with 'volume', 'is_buyer_maker', and 'close' columns.
    """
    np.random.seed(42)

    # Exponential volume distribution (realistic tick sizes)
    volumes = np.random.exponential(scale=100.0, size=n_ticks)

    # Baseline 50/50 order flow
    is_buyer_maker = np.random.random(n_ticks) > 0.5

    # Inject alternating imbalance periods
    for start in range(imbalance_period, n_ticks, imbalance_period * 2):
        end = min(start + imbalance_period, n_ticks)
        # Buyer aggression: fewer buyer_maker = more buyer-initiated
        is_buyer_maker[start:end] = np.random.random(end - start) > imbalance_strength

    # Generate realistic price path
    returns = np.random.normal(0, 0.0001, n_ticks)
    closes = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "volume": volumes,
            "is_buyer_maker": is_buyer_maker,
            "close": closes,
        }
    )


def _generate_strong_imbalance_data(
    n_ticks: int = 100,
    direction: int = 1,
    volume: float = 100.0,
) -> pd.DataFrame:
    """
    Generate data with uniform strong imbalance for threshold testing.
    
    Args:
        n_ticks: Number of ticks.
        direction: +1 for all buyer-initiated, -1 for all seller-initiated.
        volume: Constant volume per tick.
        
    Returns:
        DataFrame with 'volume' and 'is_buyer_maker' columns.
    """
    volumes = np.full(n_ticks, volume, dtype=np.float64)
    # direction=1 (buyer) -> buyer_maker=False; direction=-1 (seller) -> buyer_maker=True
    is_buyer_maker = np.full(n_ticks, direction == -1, dtype=bool)
    return pd.DataFrame({"volume": volumes, "is_buyer_maker": is_buyer_maker})


# ============================================================================
# OMEGA MANDATORY: Self-Test Block
# ============================================================================
def _run_self_tests() -> bool:
    """
    Execute comprehensive self-tests with synthetic data.
    
    Test coverage:
    1. Basic instantiation and default config
    2. Regime-specific parameter adaptation
    3. from_config factory classmethod
    4. compute_from_bars interface compliance
    5. OMEGA MANDATORY output field validation
    6. Dimensionless output range validation
    7. Threshold detection with strong imbalance
    8. Direction assignment correctness
    9. Edge case: empty DataFrame
    10. Edge case: missing columns
    11. State reset functionality
    12. Legacy feed_tick interface
    13. Factory function create_engine
    14. Optional imports availability reporting
    15. current_state property access
    
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("Running OMEGA self-test suite...")
    logger.info("=" * 60)

    all_passed = True

    # ------------------------------------------------------------------
    # Test 1: Basic instantiation and default config
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine()
        assert engine.config.regime == RegimeType.CRYPTO
        assert engine._params["lookback"] == 50
        assert engine._params["z_threshold"] == 3.0
        logger.info("  [PASS] Test 1: Basic instantiation")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 1: Basic instantiation - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 1: Basic instantiation - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 2: Regime-specific parameter adaptation
    # ------------------------------------------------------------------
    try:
        forex_engine = ComponentEngine(config=ComponentConfig(regime=RegimeType.FOREX))
        assert forex_engine._params["lookback"] == 100
        assert forex_engine._params["z_threshold"] == 2.5
        assert forex_engine._params["imbalance_smoothing"] == 0.05

        index_engine = ComponentEngine(config=ComponentConfig(regime=RegimeType.INDEX))
        assert index_engine._params["z_threshold"] == 2.0
        logger.info("  [PASS] Test 2: Regime-specific configuration")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 2: Regime-specific configuration - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 2: Regime-specific configuration - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 3: from_config factory classmethod
    # ------------------------------------------------------------------
    try:
        config = ComponentConfig(lookback=30, z_threshold=2.0, regime=RegimeType.METAL)
        engine = ComponentEngine.from_config(config)
        assert engine._params["lookback"] == 30
        assert engine._params["z_threshold"] == 2.0
        assert engine.config.regime == RegimeType.METAL
        logger.info("  [PASS] Test 3: from_config factory")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 3: from_config factory - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 3: from_config factory - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 4: compute_from_bars interface compliance
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine(
            config=ComponentConfig(lookback=40, min_bars=5, z_threshold=2.0)
        )
        df = _generate_synthetic_tick_data(n_ticks=100)
        state = engine.compute_from_bars(df)

        # Verify return type
        assert isinstance(state, ComponentState), f"Wrong type: {type(state)}"
        assert state.n_bars == 100, f"n_bars mismatch: {state.n_bars}"
        logger.info("  [PASS] Test 4: compute_from_bars interface")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 4: compute_from_bars interface - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 4: compute_from_bars interface - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 5: OMEGA MANDATORY output field validation
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine(config=ComponentConfig(lookback=40, min_bars=5))
        df = _generate_synthetic_tick_data(n_ticks=100)
        state = engine.compute_from_bars(df)

        # All four mandatory fields must exist and have correct types
        assert hasattr(state, "is_valid"), "Missing field: is_valid"
        assert hasattr(state, "direction"), "Missing field: direction"
        assert hasattr(state, "strength"), "Missing field: strength"
        assert hasattr(state, "n_bars"), "Missing field: n_bars"

        assert isinstance(state.is_valid, bool), f"is_valid wrong type: {type(state.is_valid)}"
        assert isinstance(state.direction, int), f"direction wrong type: {type(state.direction)}"
        assert isinstance(state.strength, float), f"strength wrong type: {type(state.strength)}"
        assert isinstance(state.n_bars, int), f"n_bars wrong type: {type(state.n_bars)}"

        # Direction must be in valid set
        assert state.direction in (-1, 0, 1), f"direction invalid: {state.direction}"

        logger.info("  [PASS] Test 5: OMEGA MANDATORY output fields")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 5: OMEGA MANDATORY output fields - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 5: OMEGA MANDATORY output fields - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 6: Dimensionless output range validation
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine(config=ComponentConfig(lookback=40, min_bars=5))
        df = _generate_synthetic_tick_data(n_ticks=100)
        state = engine.compute_from_bars(df)

        # Cumulative delta ratio: [-1, +1]
        assert -1.0 <= state.cumulative_delta_ratio <= 1.0, (
            f"delta_ratio out of range: {state.cumulative_delta_ratio}"
        )

        # Imbalance percentile: [0, 100]
        assert 0.0 <= state.imbalance_percentile <= 100.0, (
            f"percentile out of range: {state.imbalance_percentile}"
        )

        # Strength: non-negative
        assert state.strength >= 0.0, f"strength negative: {state.strength}"

        logger.info("  [PASS] Test 6: Dimensionless output validation")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 6: Dimensionless output validation - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 6: Dimensionless output validation - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 7: Threshold detection with strong imbalance
    # ------------------------------------------------------------------
    try:
        # All buyer-initiated should produce strong positive z-score
        engine = ComponentEngine(
            config=ComponentConfig(lookback=50, min_bars=10, z_threshold=2.0)
        )
        df = _generate_strong_imbalance_data(n_ticks=100, direction=1)
        state = engine.compute_from_bars(df)

        assert state.is_valid, "Should detect strong buyer imbalance"
        assert state.direction == 1, f"Wrong direction: {state.direction}"
        assert state.strength > 2.0, f"Strength too low: {state.strength}"
        assert state.cumulative_delta_ratio > 0.9, (
            f"Delta ratio too low: {state.cumulative_delta_ratio}"
        )
        logger.info("  [PASS] Test 7: Threshold detection (buyer)")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 7: Threshold detection (buyer) - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 7: Threshold detection (buyer) - {type(e).__name__}: {e}")
        all_passed = False

    # Test 7b: Seller imbalance
    try:
        engine = ComponentEngine(
            config=ComponentConfig(lookback=50, min_bars=10, z_threshold=2.0)
        )
        df = _generate_strong_imbalance_data(n_ticks=100, direction=-1)
        state = engine.compute_from_bars(df)

        assert state.is_valid, "Should detect strong seller imbalance"
        assert state.direction == -1, f"Wrong direction: {state.direction}"
        assert state.cumulative_delta_ratio < -0.9, (
            f"Delta ratio not negative enough: {state.cumulative_delta_ratio}"
        )
        logger.info("  [PASS] Test 7b: Threshold detection (seller)")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 7b: Threshold detection (seller) - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 7b: Threshold detection (seller) - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 8: Direction assignment correctness
    # ------------------------------------------------------------------
    try:
        # Neutral data should yield direction=0
        np.random.seed(999)
        n = 100
        volumes = np.random.exponential(100, n)
        is_buyer_maker = np.random.random(n) > 0.5  # Balanced

        engine = ComponentEngine(
            config=ComponentConfig(lookback=50, min_bars=10, z_threshold=10.0)
        )
        df = pd.DataFrame({"volume": volumes, "is_buyer_maker": is_buyer_maker})
        state = engine.compute_from_bars(df)

        assert state.direction == 0, f"Neutral data should have direction=0, got {state.direction}"
        assert not state.is_valid, "Neutral data should not be valid"
        logger.info("  [PASS] Test 8: Direction assignment (neutral)")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 8: Direction assignment (neutral) - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 8: Direction assignment (neutral) - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 9: Edge case - empty DataFrame
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine()
        state = engine.compute_from_bars(pd.DataFrame())
        assert state.is_valid is False
        assert state.n_bars == 0
        logger.info("  [PASS] Test 9: Empty DataFrame handling")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 9: Empty DataFrame handling - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 9: Empty DataFrame handling - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 10: Edge case - missing columns
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine()
        state = engine.compute_from_bars(pd.DataFrame({"price": [1, 2, 3]}))
        assert state.is_valid is False
        assert state.n_bars == 3  # Should still report bar count
        logger.info("  [PASS] Test 10: Missing columns handling")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 10: Missing columns handling - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 10: Missing columns handling - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 11: State reset functionality
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine()
        df1 = _generate_synthetic_tick_data(n_ticks=50)
        engine.compute_from_bars(df1)

        engine.reset()

        df2 = _generate_synthetic_tick_data(n_ticks=10, base_price=60000.0)
        state = engine.compute_from_bars(df2)
        assert state.n_bars == 10, f"Reset failed: n_bars={state.n_bars}"
        logger.info("  [PASS] Test 11: Reset functionality")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 11: Reset functionality - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 11: Reset functionality - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 12: Legacy feed_tick interface
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine(
            config=ComponentConfig(lookback=30, min_bars=10, z_threshold=2.0)
        )
        signal_count = 0
        for _ in range(50):
            result = engine.feed_tick(100.0, False)  # All buyer-initiated
            if result is not None:
                signal_count += 1

        assert engine._n_bars_processed == 50
        assert signal_count > 0, "Should have triggered at least one signal"
        assert result is not None
        assert result["direction"] == "AGGRESSOR_BUY"
        assert "z_score" in result
        assert "delta_ratio" in result
        logger.info("  [PASS] Test 12: Legacy feed_tick interface")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 12: Legacy feed_tick interface - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 12: Legacy feed_tick interface - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 13: Factory function create_engine
    # ------------------------------------------------------------------
    try:
        engine = create_engine(regime="forex", lookback=100)
        assert engine.config.regime == RegimeType.FOREX
        assert engine._params["lookback"] == 100

        # Invalid regime should fallback to CRYPTO
        engine2 = create_engine(regime="invalid_regime")
        assert engine2.config.regime == RegimeType.CRYPTO
        logger.info("  [PASS] Test 13: Factory function")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 13: Factory function - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 13: Factory function - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 14: Optional imports availability reporting
    # ------------------------------------------------------------------
    try:
        # These should never fail, just report status
        logger.info(f"  [INFO] MT5 available: {_HAS_MT5}")
        logger.info(f"  [INFO] Numba available: {_HAS_NUMBA}")
        # Verify fallback decorators work
        assert callable(jit)
        assert callable(njit)
        logger.info("  [PASS] Test 14: Optional imports check")
    except Exception as e:
        logger.error(f"  [FAIL] Test 14: Optional imports check - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 15: current_state property access
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine(
            config=ComponentConfig(lookback=30, min_bars=5, z_threshold=2.0)
        )
        # Before processing: should be invalid
        state_before = engine.current_state
        assert state_before.is_valid is False
        assert state_before.n_bars == 0

        # After processing
        df = _generate_strong_imbalance_data(n_ticks=50, direction=1)
        engine.compute_from_bars(df)

        state_after = engine.current_state
        assert state_after.is_valid is True
        assert state_after.direction == 1
        assert state_after.strength > 0
        logger.info("  [PASS] Test 15: current_state property")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 15: current_state property - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 15: current_state property - {type(e).__name__}: {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 16: Custom column names
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine(
            config=ComponentConfig(
                volume_column="vol",
                buyer_maker_column="seller_init",
                lookback=30,
                min_bars=5,
                z_threshold=2.0,
            )
        )
        df = pd.DataFrame({
            "vol": np.full(50, 100.0),
            "seller_init": np.zeros(50, dtype=bool),
        })
        state = engine.compute_from_bars(df)
        assert state.is_valid, "Should work with custom column names"
        assert state.n_bars == 50
        logger.info("  [PASS] Test 16: Custom column names")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 16: Custom column names - {e}")
        all_passed = False
    except Exception as e:
        logger.error(f"  [FAIL] Test 16: Custom column names - {type(e).__name__}: {e}")
        all_passed = False

    logger.info("=" * 60)
    return all_passed


# ============================================================================
# OMEGA MANDATORY: Self-Test Entry Point
# ============================================================================
if __name__ == "__main__":
    """
    Self-test entry point - OMEGA MANDATORY.
    
    Uses only synthetic data (no external dependencies).
    Exits with code 0 on success, 1 on failure.
    """
    # Configure logging for self-test output
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    success = _run_self_tests()

    if success:
        logger.info("ALL OMEGA SELF-TESTS PASSED")
        sys.exit(0)
    else:
        logger.error("SOME OMEGA SELF-TESTS FAILED")
        sys.exit(1)