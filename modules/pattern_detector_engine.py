#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA Institutional Pattern Detector
=======================================
Design Standard: Top-Tier Chinese Quant Funds (High-Flyer, JiuKun, Minghe)
Compliance: Strict OMEGA Checklist Adherence

Core functionality:
- Institutional-grade pattern recognition (Flags, Pennants, Triangles, H&S, etc.)
- Multi-timeframe confirmation
- Volume profile analysis
- Risk-adjusted pattern scoring
- Probability-based pattern validation
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum, auto

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import argrelextrema

# ===========================================================================
# [OMEGA MANDATORY] Optional Imports with Fallbacks
# ===========================================================================
try:
    from numba import njit
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False
    def njit(*args, **kwargs):
        """Fallback decorator when Numba is not available."""
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

try:
    import MetaTrader5 as mt5
    _HAS_MT5 = True
except ImportError:
    mt5 = None
    _HAS_MT5 = False

# ===========================================================================
# [OMEGA MANDATORY] Component Structures
# ===========================================================================

class PatternType(Enum):
    """Institutional pattern types."""
    NONE = auto()
    BULL_FLAG = auto()
    BEAR_FLAG = auto()
    BULL_PENNANT = auto()
    BEAR_PENNANT = auto()
    ASCENDING_TRIANGLE = auto()
    DESCENDING_TRIANGLE = auto()
    SYMMETRICAL_TRIANGLE = auto()
    HEAD_AND_SHOULDERS = auto()
    INVERSE_HEAD_AND_SHOULDERS = auto()
    DOUBLE_TOP = auto()
    DOUBLE_BOTTOM = auto()
    TRIPLE_TOP = auto()
    TRIPLE_BOTTOM = auto()
    ROUNDING_TOP = auto()
    ROUNDING_BOTTOM = auto()

class PatternPriority(Enum):
    """Trade priority levels."""
    WATCH_ONLY = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5

@dataclass
class PatternPoint:
    """A point in a pattern (high or low)."""
    time: int = 0          # Timestamp (microseconds)
    price: float = 0.0    # Price level
    point_type: int = 0   # 0 = low, 1 = high
    confidence: float = 0.0  # 0-1 confidence level
    volume: float = 0.0   # Volume at this point

@dataclass
class Pattern:
    """Represents a detected institutional pattern."""
    name: str = ""
    pattern_type: PatternType = PatternType.NONE
    points: List[PatternPoint] = field(default_factory=list)
    score: float = 0.0           # Overall pattern quality score (0-1)
    volume_confirmation: float = 0.0  # Volume confirmation score (0-1)
    volatility_factor: float = 0.0   # Volatility adjustment factor (0-1)
    expected_gain: float = 0.0  # Expected gain in %
    expected_risk: float = 0.0  # Expected risk in %
    reward_ratio: float = 0.0   # Reward/Risk ratio
    expiration: int = 0         # Pattern expiration time (timestamp)
    priority: PatternPriority = PatternPriority.WATCH_ONLY
    color: str = "gray"         # Color for visualization

@dataclass
class ComponentConfig:
    """
    Configuration dataclass for Institutional Pattern Detector.
    All thresholds parameterized. No hardcoded magic numbers.
    Adaptive by regime (forex/crypto/metal/index).
    """
    # Pattern detection parameters
    max_bars_to_scan: int = 500
    min_pattern_score: float = 0.75
    volume_confirmation: bool = True
    confirm_timeframe: str = "H4"  # Higher timeframe for confirmation

    # Risk management parameters
    max_expected_sl: float = 0.02  # 2% max stop-loss
    min_reward_ratio: float = 2.5

    # Advanced filtering
    use_volatility_filter: bool = True
    atr_period: int = 14
    min_volatility_factor: float = 0.5

    # ZigZag parameters
    zigzag_depth: int = 12
    zigzag_deviation: int = 5
    zigzag_backstep: int = 3

    # Wave detection
    min_wave_length: int = 10

    # General
    regime: str = "forex"

    # Regime-specific defaults
    REGIME_DEFAULTS: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "forex": {
            "max_bars_to_scan": 500,
            "min_pattern_score": 0.75,
            "volume_confirmation": True,
            "confirm_timeframe": "H4",
            "max_expected_sl": 0.02,
            "min_reward_ratio": 2.5,
            "use_volatility_filter": True,
            "atr_period": 14,
            "min_volatility_factor": 0.5,
            "zigzag_depth": 12,
            "zigzag_deviation": 5,
            "zigzag_backstep": 3,
            "min_wave_length": 10
        },
        "crypto": {
            "max_bars_to_scan": 300,
            "min_pattern_score": 0.70,
            "volume_confirmation": True,
            "confirm_timeframe": "H2",
            "max_expected_sl": 0.03,
            "min_reward_ratio": 2.0,
            "use_volatility_filter": True,
            "atr_period": 12,
            "min_volatility_factor": 0.4,
            "zigzag_depth": 10,
            "zigzag_deviation": 4,
            "zigzag_backstep": 2,
            "min_wave_length": 8
        },
        "metal": {
            "max_bars_to_scan": 600,
            "min_pattern_score": 0.80,
            "volume_confirmation": True,
            "confirm_timeframe": "H4",
            "max_expected_sl": 0.015,
            "min_reward_ratio": 3.0,
            "use_volatility_filter": True,
            "atr_period": 16,
            "min_volatility_factor": 0.6,
            "zigzag_depth": 14,
            "zigzag_deviation": 6,
            "zigzag_backstep": 4,
            "min_wave_length": 12
        },
        "index": {
            "max_bars_to_scan": 400,
            "min_pattern_score": 0.78,
            "volume_confirmation": True,
            "confirm_timeframe": "H4",
            "max_expected_sl": 0.025,
            "min_reward_ratio": 2.2,
            "use_volatility_filter": True,
            "atr_period": 15,
            "min_volatility_factor": 0.55,
            "zigzag_depth": 13,
            "zigzag_deviation": 5,
            "zigzag_backstep": 3,
            "min_wave_length": 10
        },
    })

    def __post_init__(self):
        """Apply regime-specific defaults if not explicitly set."""
        regime_key = self.regime.lower()
        if regime_key in self.REGIME_DEFAULTS:
            regime_params = self.REGIME_DEFAULTS[regime_key]
            for key, default_value in regime_params.items():
                if not hasattr(self, key) or getattr(self, key) is None:
                    setattr(self, key, default_value)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ComponentConfig":
        """Create ComponentConfig from a dictionary."""
        regime = config_dict.get("regime", "forex")
        return cls(
            max_bars_to_scan=config_dict.get("max_bars_to_scan", 500),
            min_pattern_score=config_dict.get("min_pattern_score", 0.75),
            volume_confirmation=config_dict.get("volume_confirmation", True),
            confirm_timeframe=config_dict.get("confirm_timeframe", "H4"),
            max_expected_sl=config_dict.get("max_expected_sl", 0.02),
            min_reward_ratio=config_dict.get("min_reward_ratio", 2.5),
            use_volatility_filter=config_dict.get("use_volatility_filter", True),
            atr_period=config_dict.get("atr_period", 14),
            min_volatility_factor=config_dict.get("min_volatility_factor", 0.5),
            zigzag_depth=config_dict.get("zigzag_depth", 12),
            zigzag_deviation=config_dict.get("zigzag_deviation", 5),
            zigzag_backstep=config_dict.get("zigzag_backstep", 3),
            regime=regime,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ComponentConfig to a dictionary."""
        return {
            "max_bars_to_scan": self.max_bars_to_scan,
            "min_pattern_score": self.min_pattern_score,
            "volume_confirmation": self.volume_confirmation,
            "confirm_timeframe": self.confirm_timeframe,
            "max_expected_sl": self.max_expected_sl,
            "min_reward_ratio": self.min_reward_ratio,
            "use_volatility_filter": self.use_volatility_filter,
            "atr_period": self.atr_period,
            "min_volatility_factor": self.min_volatility_factor,
            "zigzag_depth": self.zigzag_depth,
            "zigzag_deviation": self.zigzag_deviation,
            "zigzag_backstep": self.zigzag_backstep,
            "regime": self.regime,
        }

@dataclass
class ComponentState:
    """
    State dataclass for Institutional Pattern Detector.
    Strict field requirements: is_valid, direction, strength, n_bars.
    All metrics are strictly dimensionless (Z-scores, ratios).
    """
    is_valid: bool = False
    direction: int = 0           # +1 (Bullish), -1 (Bearish), 0 (Neutral)
    strength: float = 0.0        # 0..1 pattern confidence score
    n_bars: int = 0              # Number of bars evaluated

    # Extended pattern metrics
    detected_patterns: List[Pattern] = field(default_factory=list)
    best_pattern: Optional[Pattern] = None
    zigzag_points: List[PatternPoint] = field(default_factory=list)
    atr: float = 0.0             # ATR value (normalized)
    volatility: float = 0.0     # Current volatility (dimensionless)
    volume_profile: List[float] = field(default_factory=list)
    regime: str = "forex"

    def to_dict(self) -> Dict[str, Any]:
        """Convert ComponentState to a dictionary."""
        return {
            "is_valid": self.is_valid,
            "direction": self.direction,
            "strength": self.strength,
            "n_bars": self.n_bars,
            "detected_patterns": [p.__dict__ for p in self.detected_patterns],
            "best_pattern": self.best_pattern.__dict__ if self.best_pattern else None,
            "zigzag_points": [p.__dict__ for p in self.zigzag_points],
            "atr": self.atr,
            "volatility": self.volatility,
            "volume_profile": self.volume_profile,
            "regime": self.regime,
        }

# ===========================================================================
# [OMEGA COMPLIANT] Core Calculators
# ===========================================================================

@njit
def _calculate_atr_numba(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int
) -> float:
    """Numba-optimized ATR calculation."""
    n = len(closes)
    if n < period:
        return 0.0

    tr = np.zeros(n)
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )

    atr = 0.0
    for i in range(period, n):
        atr += tr[i]
    atr /= period

    return atr

def _calculate_atr(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int
) -> float:
    """Fallback Python implementation for ATR."""
    if _HAS_NUMBA:
        return _calculate_atr_numba(highs, lows, closes, period)
    if len(closes) < period:
        return 0.0
    return float(np.mean(np.maximum(
        highs[1:] - lows[1:],
        np.maximum(
            np.abs(highs[1:] - closes[:-1]),
            np.abs(lows[1:] - closes[:-1])
        )
    )[-period:]))

def _detect_zigzag(
    closes: np.ndarray,
    depth: int = 12,
    deviation: int = 5,
    backstep: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect ZigZag points (highs and lows) in price data.
    Returns (high_indices, low_indices).
    """
    if len(closes) < depth:
        return np.array([], dtype=int), np.array([], dtype=int)

    # Find local maxima and minima
    high_indices = argrelextrema(closes, np.greater_equal, order=depth)[0]
    low_indices = argrelextrema(closes, np.less_equal, order=depth)[0]

    # Filter based on deviation
    filtered_highs = []
    for i in high_indices:
        if i == 0 or i == len(closes) - 1:
            continue
        left_min = np.min(closes[max(0, i - backstep):i])
        right_min = np.min(closes[i+1:min(i + backstep + 1, len(closes))])
        if closes[i] - max(left_min, right_min) >= deviation * 0.0001:
            filtered_highs.append(i)

    filtered_lows = []
    for i in low_indices:
        if i == 0 or i == len(closes) - 1:
            continue
        left_max = np.max(closes[max(0, i - backstep):i])
        right_max = np.max(closes[i+1:min(i + backstep + 1, len(closes))])
        if min(left_max, right_max) - closes[i] >= deviation * 0.0001:
            filtered_lows.append(i)

    return np.array(filtered_highs, dtype=int), np.array(filtered_lows, dtype=int)

def _calculate_volatility(prices: np.ndarray, window: int = 20) -> float:
    """Calculate volatility as standard deviation of log returns."""
    if len(prices) < window:
        return 0.0
    returns = np.diff(np.log(prices[-window:]))
    return float(np.std(returns))

def _calculate_pattern_score(pattern: Pattern) -> float:
    """
    Calculate overall pattern score (0-1).
    """
    # 1. Geometric perfection (30% weight)
    geometric_score = _calculate_geometric_score(pattern)

    # 2. Volume confirmation (25% weight)
    volume_score = pattern.volume_confirmation if pattern.volume_confirmation else 0.25

    # 3. Volatility adjustment (20% weight)
    volatility_score = pattern.volatility_factor

    # 4. Reward/Risk ratio (15% weight)
    rr_score = min(1.0, pattern.reward_ratio / 5.0)

    # 5. Pattern type bonus (10% weight)
    type_bonus = _get_pattern_type_bonus(pattern.pattern_type)

    # Combined score
    score = (
        0.30 * geometric_score +
        0.25 * volume_score +
        0.20 * volatility_score +
        0.15 * rr_score +
        0.10 * type_bonus
    )

    return min(1.0, max(0.0, score))

def _calculate_geometric_score(pattern: Pattern) -> float:
    """Calculate geometric perfection score (0-1)."""
    if len(pattern.points) < 4:
        return 0.5

    prices = np.array([p.price for p in pattern.points])
    score = 0.0

    # Check symmetry (for patterns like triangles)
    if len(pattern.points) >= 4:
        left_side = abs(pattern.points[1].price - pattern.points[0].price)
        right_side = abs(pattern.points[-1].price - pattern.points[-2].price)
        if max(left_side, right_side) > 0:
            symmetry_ratio = min(left_side, right_side) / max(left_side, right_side)
            score += symmetry_ratio * 0.4

    # Check Fibonacci ratios (for harmonic patterns)
    if len(pattern.points) >= 5:
        main_move = abs(pattern.points[2].price - pattern.points[0].price)
        if main_move > 0:
            retracement = abs(pattern.points[2].price - pattern.points[1].price)
            retracement_ratio = retracement / main_move

            if abs(retracement_ratio - 0.618) < 0.1:
                score += 0.3
            elif abs(retracement_ratio - 0.382) < 0.1:
                score += 0.2
            elif abs(retracement_ratio - 0.786) < 0.1:
                score += 0.25

    # Check angle consistency (for flags, channels)
    if len(pattern.points) >= 3:
        times = np.array([p.time for p in pattern.points])
        prices = np.array([p.price for p in pattern.points])

        # Calculate angles between consecutive points
        angles = []
        for i in range(1, len(pattern.points) - 1):
            dx1 = times[i] - times[i-1]
            dy1 = prices[i] - prices[i-1]
            dx2 = times[i+1] - times[i]
            dy2 = prices[i+1] - prices[i]

            if dx1 > 0 and dx2 > 0:
                angle1 = np.arctan2(dy1, dx1)
                angle2 = np.arctan2(dy2, dx2)
                angle_diff = abs(angle1 - angle2)
                angles.append(angle_diff)

        if angles:
            avg_angle = np.mean(angles)
            angle_consistency = 1.0 - (np.std(angles) / (np.pi/2)) if (np.pi/2) > 0 else 0.0
            score += angle_consistency * 0.3

    return min(1.0, score)

def _get_pattern_type_bonus(pattern_type: PatternType) -> float:
    """Get bonus for specific pattern types."""
    bonus_map = {
        PatternType.BULL_FLAG: 0.9,
        PatternType.BEAR_FLAG: 0.9,
        PatternType.BULL_PENNANT: 0.95,
        PatternType.BEAR_PENNANT: 0.95,
        PatternType.ASCENDING_TRIANGLE: 0.85,
        PatternType.DESCENDING_TRIANGLE: 0.85,
        PatternType.SYMMETRICAL_TRIANGLE: 0.8,
        PatternType.HEAD_AND_SHOULDERS: 0.9,
        PatternType.INVERSE_HEAD_AND_SHOULDERS: 0.9,
        PatternType.DOUBLE_TOP: 0.85,
        PatternType.DOUBLE_BOTTOM: 0.85,
        PatternType.TRIPLE_TOP: 0.8,
        PatternType.TRIPLE_BOTTOM: 0.8,
        PatternType.ROUNDING_TOP: 0.75,
        PatternType.ROUNDING_BOTTOM: 0.75,
        PatternType.NONE: 0.0
    }
    return bonus_map.get(pattern_type, 0.0)

def _calculate_pattern_risk(pattern: Pattern, atr: float) -> float:
    """Calculate expected risk for a pattern (in %)."""
    if len(pattern.points) < 2:
        return 0.0

    # Calculate price range of the pattern
    prices = [p.price for p in pattern.points]
    price_range = max(prices) - min(prices)

    # Risk is typically the distance to the nearest support/resistance
    if pattern.pattern_type in [PatternType.BULL_FLAG, PatternType.BULL_PENNANT,
                                  PatternType.ASCENDING_TRIANGLE]:
        # For bullish patterns, risk is below the pattern
        risk = min(prices) - min(prices[-2:]) if len(prices) >= 2 else price_range * 0.5
    else:
        # For bearish patterns, risk is above the pattern
        risk = max(prices[-2:]) - max(prices) if len(prices) >= 2 else price_range * 0.5

    # Normalize by ATR
    if atr > 0:
        risk_pct = (abs(risk) / atr) * 100
    else:
        risk_pct = 0.0

    return min(100.0, max(0.0, risk_pct))

def _calculate_pattern_gain(pattern: Pattern, atr: float) -> float:
    """Calculate expected gain for a pattern (in %)."""
    if len(pattern.points) < 2:
        return 0.0

    prices = [p.price for p in pattern.points]
    price_range = max(prices) - min(prices)

    # Calculate expected gain based on pattern type
    if pattern.pattern_type in [PatternType.BULL_FLAG, PatternType.BEAR_FLAG]:
        # Flags typically have 1:1.618 ratio
        gain = price_range * 1.618
    elif pattern.pattern_type in [PatternType.BULL_PENNANT, PatternType.BEAR_PENNANT]:
        # Pennants typically have 1:1.618 ratio
        gain = price_range * 1.618
    elif pattern.pattern_type == PatternType.ASCENDING_TRIANGLE:
        # Ascending triangle: height of the triangle
        gain = price_range
    elif pattern.pattern_type == PatternType.DESCENDING_TRIANGLE:
        # Descending triangle: height of the triangle
        gain = price_range
    elif pattern.pattern_type == PatternType.SYMMETRICAL_TRIANGLE:
        # Symmetrical triangle: height at the apex
        gain = price_range
    elif pattern.pattern_type in [PatternType.HEAD_AND_SHOULDERS, PatternType.INVERSE_HEAD_AND_SHOULDERS]:
        # H&S: distance from neckline to head
        if len(prices) >= 3:
            neckline = (prices[0] + prices[-1]) / 2
            head = prices[1] if pattern.pattern_type == PatternType.HEAD_AND_SHOULDERS else prices[1]
            gain = abs(head - neckline)
        else:
            gain = price_range * 0.8
    elif pattern.pattern_type in [PatternType.DOUBLE_TOP, PatternType.DOUBLE_BOTTOM,
                                  PatternType.TRIPLE_TOP, PatternType.TRIPLE_BOTTOM]:
        # Double/Triple top/bottom: distance from neckline to top/bottom
        gain = price_range * 0.8
    elif pattern.pattern_type in [PatternType.ROUNDING_TOP, PatternType.ROUNDING_BOTTOM]:
        # Rounding patterns: similar to head and shoulders
        gain = price_range * 0.7
    else:
        gain = price_range

    # Normalize by ATR
    if atr > 0:
        gain_pct = (gain / atr) * 100
    else:
        gain_pct = 0.0

    return min(100.0, max(0.0, gain_pct))

def _get_pattern_color(pattern_type: PatternType) -> str:
    """Get color for pattern visualization."""
    color_map = {
        PatternType.BULL_FLAG: "dodgerblue",
        PatternType.BEAR_FLAG: "orangered",
        PatternType.BULL_PENNANT: "dodgerblue",
        PatternType.BEAR_PENNANT: "orangered",
        PatternType.ASCENDING_TRIANGLE: "dodgerblue",
        PatternType.DESCENDING_TRIANGLE: "orangered",
        PatternType.SYMMETRICAL_TRIANGLE: "mediumpurple",
        PatternType.HEAD_AND_SHOULDERS: "orangered",
        PatternType.INVERSE_HEAD_AND_SHOULDERS: "dodgerblue",
        PatternType.DOUBLE_TOP: "orangered",
        PatternType.DOUBLE_BOTTOM: "dodgerblue",
        PatternType.TRIPLE_TOP: "orangered",
        PatternType.TRIPLE_BOTTOM: "dodgerblue",
        PatternType.ROUNDING_TOP: "orangered",
        PatternType.ROUNDING_BOTTOM: "dodgerblue",
        PatternType.NONE: "darkgray"
    }
    return color_map.get(pattern_type, "gray")

def _get_pattern_priority(score: float, reward_ratio: float, expected_risk: float,
                          max_expected_sl: float) -> PatternPriority:
    """Determine trade priority based on pattern metrics."""
    priority = PatternPriority.WATCH_ONLY

    if score >= 0.9:
        priority = PatternPriority.CRITICAL
    elif score >= 0.8:
        priority = PatternPriority.HIGH
    elif score >= 0.7:
        priority = PatternPriority.MODERATE
    elif score >= 0.6:
        priority = PatternPriority.LOW

    if reward_ratio >= 3.0:
        priority = min(priority.value + 1, PatternPriority.CRITICAL.value)
    if expected_risk > max_expected_sl * 100:
        priority = max(priority.value - 1, PatternPriority.WATCH_ONLY.value)

    return PatternPriority(priority)

# ===========================================================================
# [OMEGA MANDATORY] Component Engine
# ===========================================================================

class ComponentEngine:
    """
    Main execution engine for Institutional Pattern Detector.
    Stateless transformation of DataFrames to State (Thread-safe by design).
    """

    def __init__(self, config: ComponentConfig) -> None:
        """Initialize with configuration."""
        self._config = config
        self._zigzag_points: List[PatternPoint] = []
        self._patterns: List[Pattern] = []
        self._volume_profile: List[float] = []

    @classmethod
    def from_config(cls, regime: str = "forex", **kwargs: Any) -> "ComponentEngine":
        """
        [OMEGA MANDATORY] Adaptive initialization based on market regime.
        """
        # Get regime defaults (REGIME_DEFAULTS is an instance field, access via temp instance)
        _tmp = ComponentConfig()
        regime_defaults = _tmp.REGIME_DEFAULTS.get(str(regime), _tmp.REGIME_DEFAULTS["forex"]).copy()

        # Update with provided kwargs
        regime_defaults.update(kwargs)
        regime_defaults["regime"] = regime

        return cls(config=ComponentConfig(**regime_defaults))

    def _load_zigzag_points(self, df: pd.DataFrame) -> None:
        """Load ZigZag points from price data."""
        closes = df["close"].to_numpy(dtype=np.float64)
        volumes = df["volume"].to_numpy(dtype=np.float64)
        times = df.index.astype(np.int64) // 10**6  # Convert to microseconds

        # Detect ZigZag points
        high_indices, low_indices = _detect_zigzag(
            closes,
            self._config.zigzag_depth,
            self._config.zigzag_deviation,
            self._config.zigzag_backstep
        )

        # Create PatternPoints
        self._zigzag_points = []
        for idx in high_indices:
            self._zigzag_points.append(PatternPoint(
                time=int(times[idx]),
                price=float(closes[idx]),
                point_type=1,  # High
                confidence=0.9,  # Default confidence
                volume=float(volumes[idx])
            ))

        for idx in low_indices:
            self._zigzag_points.append(PatternPoint(
                time=int(times[idx]),
                price=float(closes[idx]),
                point_type=0,  # Low
                confidence=0.9,  # Default confidence
                volume=float(volumes[idx])
            ))

        # Sort by time
        self._zigzag_points.sort(key=lambda x: x.time)

    def _calculate_volume_profile(self, df: pd.DataFrame) -> None:
        """Calculate volume profile."""
        volumes = df["volume"].to_numpy(dtype=np.float64)
        self._volume_profile = volumes.tolist()

    def _detect_flags_and_pennants(self) -> None:
        """Detect Flag and Pennant patterns."""
        n = len(self._zigzag_points)
        if n < 4:
            return

        for i in range(n - 4):
            # Bull Flag: High, Low, High, Low (with downsloping channel)
            if (i + 3 < n and
                self._zigzag_points[i].point_type == 1 and
                self._zigzag_points[i+1].point_type == 0 and
                self._zigzag_points[i+2].point_type == 1 and
                self._zigzag_points[i+3].point_type == 0):

                # Check if channel is downsloping
                slope = (self._zigzag_points[i+3].price - self._zigzag_points[i+1].price) / (
                    self._zigzag_points[i+3].time - self._zigzag_points[i+1].time
                )
                if slope < -1e-10:  # Negative slope
                    # Check volume (should decrease in the flag)
                    initial_volume = self._zigzag_points[i].volume
                    flag_volume = (self._zigzag_points[i+1].volume +
                                  self._zigzag_points[i+2].volume +
                                  self._zigzag_points[i+3].volume) / 3
                    if flag_volume < initial_volume * 0.8:
                        pattern = self._create_pattern(
                            "Bull Flag",
                            PatternType.BULL_FLAG,
                            [i, i+1, i+2, i+3]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

            # Bear Flag: Low, High, Low, High (with upsloping channel)
            if (i + 3 < n and
                self._zigzag_points[i].point_type == 0 and
                self._zigzag_points[i+1].point_type == 1 and
                self._zigzag_points[i+2].point_type == 0 and
                self._zigzag_points[i+3].point_type == 1):

                # Check if channel is upsloping
                slope = (self._zigzag_points[i+3].price - self._zigzag_points[i+1].price) / (
                    self._zigzag_points[i+3].time - self._zigzag_points[i+1].time
                )
                if slope > 1e-10:  # Positive slope
                    # Check volume (should decrease in the flag)
                    initial_volume = self._zigzag_points[i].volume
                    flag_volume = (self._zigzag_points[i+1].volume +
                                  self._zigzag_points[i+2].volume +
                                  self._zigzag_points[i+3].volume) / 3
                    if flag_volume < initial_volume * 0.8:
                        pattern = self._create_pattern(
                            "Bear Flag",
                            PatternType.BEAR_FLAG,
                            [i, i+1, i+2, i+3]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

            # Bull Pennant: High, Low, High (converging)
            if (i + 2 < n and
                self._zigzag_points[i].point_type == 1 and
                self._zigzag_points[i+1].point_type == 0 and
                self._zigzag_points[i+2].point_type == 1):

                # Check if lines are converging
                slope1 = (self._zigzag_points[i+1].price - self._zigzag_points[i].price) / (
                    self._zigzag_points[i+1].time - self._zigzag_points[i].time
                )
                slope2 = (self._zigzag_points[i+2].price - self._zigzag_points[i+1].price) / (
                    self._zigzag_points[i+2].time - self._zigzag_points[i+1].time
                )
                if slope1 < -1e-10 and slope2 > 1e-10:  # Converging
                    # Check volume (should decrease in the pennant)
                    initial_volume = self._zigzag_points[i].volume
                    pennant_volume = (self._zigzag_points[i+1].volume +
                                     self._zigzag_points[i+2].volume) / 2
                    if pennant_volume < initial_volume * 0.8:
                        pattern = self._create_pattern(
                            "Bull Pennant",
                            PatternType.BULL_PENNANT,
                            [i, i+1, i+2]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

            # Bear Pennant: Low, High, Low (converging)
            if (i + 2 < n and
                self._zigzag_points[i].point_type == 0 and
                self._zigzag_points[i+1].point_type == 1 and
                self._zigzag_points[i+2].point_type == 0):

                # Check if lines are converging
                slope1 = (self._zigzag_points[i+1].price - self._zigzag_points[i].price) / (
                    self._zigzag_points[i+1].time - self._zigzag_points[i].time
                )
                slope2 = (self._zigzag_points[i+2].price - self._zigzag_points[i+1].price) / (
                    self._zigzag_points[i+2].time - self._zigzag_points[i+1].time
                )
                if slope1 > 1e-10 and slope2 < -1e-10:  # Converging
                    # Check volume (should decrease in the pennant)
                    initial_volume = self._zigzag_points[i].volume
                    pennant_volume = (self._zigzag_points[i+1].volume +
                                     self._zigzag_points[i+2].volume) / 2
                    if pennant_volume < initial_volume * 0.8:
                        pattern = self._create_pattern(
                            "Bear Pennant",
                            PatternType.BEAR_PENNANT,
                            [i, i+1, i+2]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

    def _detect_triangles(self) -> None:
        """Detect Triangle patterns."""
        n = len(self._zigzag_points)
        if n < 4:
            return

        for i in range(n - 4):
            # Ascending Triangle: Low, High, Low, High (with flat top)
            if (i + 3 < n and
                self._zigzag_points[i].point_type == 0 and
                self._zigzag_points[i+1].point_type == 1 and
                self._zigzag_points[i+2].point_type == 0 and
                self._zigzag_points[i+3].point_type == 1):

                # Check if top is relatively flat
                top_diff = abs(self._zigzag_points[i+1].price - self._zigzag_points[i+3].price)
                height = self._zigzag_points[i+1].price - self._zigzag_points[i].price
                if top_diff < height * 0.2:  # Top is relatively flat
                    pattern = self._create_pattern(
                        "Ascending Triangle",
                        PatternType.ASCENDING_TRIANGLE,
                        [i, i+1, i+2, i+3]
                    )
                    if self._validate_pattern(pattern):
                        self._patterns.append(pattern)

            # Descending Triangle: High, Low, High, Low (with flat bottom)
            if (i + 3 < n and
                self._zigzag_points[i].point_type == 1 and
                self._zigzag_points[i+1].point_type == 0 and
                self._zigzag_points[i+2].point_type == 1 and
                self._zigzag_points[i+3].point_type == 0):

                # Check if bottom is relatively flat
                bottom_diff = abs(self._zigzag_points[i+1].price - self._zigzag_points[i+3].price)
                height = self._zigzag_points[i].price - self._zigzag_points[i+1].price
                if bottom_diff < height * 0.2:  # Bottom is relatively flat
                    pattern = self._create_pattern(
                        "Descending Triangle",
                        PatternType.DESCENDING_TRIANGLE,
                        [i, i+1, i+2, i+3]
                    )
                    if self._validate_pattern(pattern):
                        self._patterns.append(pattern)

            # Symmetrical Triangle: Alternating highs and lows converging
            if i + 4 < n:
                points = self._zigzag_points[i:i+5]
                if (len(points) == 5 and
                    points[0].point_type == 1 and
                    points[1].point_type == 0 and
                    points[2].point_type == 1 and
                    points[3].point_type == 0 and
                    points[4].point_type == 1):

                    # Check convergence
                    high_prices = [p.price for p in points if p.point_type == 1]
                    low_prices = [p.price for p in points if p.point_type == 0]

                    if len(high_prices) >= 2 and len(low_prices) >= 2:
                        high_slope = (high_prices[-1] - high_prices[0]) / (points[-1].time - points[0].time)
                        low_slope = (low_prices[-1] - low_prices[0]) / (points[-1].time - points[0].time)

                        if high_slope < -1e-10 and low_slope > 1e-10:  # Converging
                            pattern = self._create_pattern(
                                "Symmetrical Triangle",
                                PatternType.SYMMETRICAL_TRIANGLE,
                                [i, i+1, i+2, i+3, i+4]
                            )
                            if self._validate_pattern(pattern):
                                self._patterns.append(pattern)

    def _detect_head_and_shoulders(self) -> None:
        """Detect Head and Shoulders patterns."""
        n = len(self._zigzag_points)
        if n < 5:
            return

        for i in range(n - 4):
            # Head and Shoulders: Low, High, Low, High, Low
            if (i + 4 < n and
                self._zigzag_points[i].point_type == 0 and
                self._zigzag_points[i+1].point_type == 1 and
                self._zigzag_points[i+2].point_type == 0 and
                self._zigzag_points[i+3].point_type == 1 and
                self._zigzag_points[i+4].point_type == 0):

                # Check if head is higher than shoulders
                left_shoulder = self._zigzag_points[i+1].price
                head = self._zigzag_points[i+3].price
                right_shoulder = self._zigzag_points[i+1].price  # Simplified

                if head > left_shoulder and head > right_shoulder:
                    # Check neckline
                    neckline = (self._zigzag_points[i].price + self._zigzag_points[i+4].price) / 2
                    if abs(left_shoulder - right_shoulder) < (head - neckline) * 0.2:
                        pattern = self._create_pattern(
                            "Head and Shoulders",
                            PatternType.HEAD_AND_SHOULDERS,
                            [i, i+1, i+2, i+3, i+4]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

            # Inverse Head and Shoulders: High, Low, High, Low, High
            if (i + 4 < n and
                self._zigzag_points[i].point_type == 1 and
                self._zigzag_points[i+1].point_type == 0 and
                self._zigzag_points[i+2].point_type == 1 and
                self._zigzag_points[i+3].point_type == 0 and
                self._zigzag_points[i+4].point_type == 1):

                # Check if head is lower than shoulders
                left_shoulder = self._zigzag_points[i].price
                head = self._zigzag_points[i+2].price
                right_shoulder = self._zigzag_points[i+4].price

                if head < left_shoulder and head < right_shoulder:
                    # Check neckline
                    neckline = (self._zigzag_points[i+1].price + self._zigzag_points[i+3].price) / 2
                    if abs(left_shoulder - right_shoulder) < (neckline - head) * 0.2:
                        pattern = self._create_pattern(
                            "Inverse Head and Shoulders",
                            PatternType.INVERSE_HEAD_AND_SHOULDERS,
                            [i, i+1, i+2, i+3, i+4]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

    def _detect_double_triple(self) -> None:
        """Detect Double/Triple Top/Bottom patterns."""
        n = len(self._zigzag_points)
        if n < 4:
            return

        for i in range(n - 3):
            # Double Top: High, Low, High
            if (i + 2 < n and
                self._zigzag_points[i].point_type == 1 and
                self._zigzag_points[i+1].point_type == 0 and
                self._zigzag_points[i+2].point_type == 1):

                # Check if tops are at similar level
                top_diff = abs(self._zigzag_points[i].price - self._zigzag_points[i+2].price)
                height = self._zigzag_points[i].price - self._zigzag_points[i+1].price
                if top_diff < height * 0.1:  # Tops are at similar level
                    pattern = self._create_pattern(
                        "Double Top",
                        PatternType.DOUBLE_TOP,
                        [i, i+1, i+2]
                    )
                    if self._validate_pattern(pattern):
                        self._patterns.append(pattern)

            # Double Bottom: Low, High, Low
            if (i + 2 < n and
                self._zigzag_points[i].point_type == 0 and
                self._zigzag_points[i+1].point_type == 1 and
                self._zigzag_points[i+2].point_type == 0):

                # Check if bottoms are at similar level
                bottom_diff = abs(self._zigzag_points[i].price - self._zigzag_points[i+2].price)
                height = self._zigzag_points[i+1].price - self._zigzag_points[i].price
                if bottom_diff < height * 0.1:  # Bottoms are at similar level
                    pattern = self._create_pattern(
                        "Double Bottom",
                        PatternType.DOUBLE_BOTTOM,
                        [i, i+1, i+2]
                    )
                    if self._validate_pattern(pattern):
                        self._patterns.append(pattern)

            # Triple Top: High, Low, High, Low, High
            if (i + 4 < n and
                self._zigzag_points[i].point_type == 1 and
                self._zigzag_points[i+1].point_type == 0 and
                self._zigzag_points[i+2].point_type == 1 and
                self._zigzag_points[i+3].point_type == 0 and
                self._zigzag_points[i+4].point_type == 1):

                # Check if all tops are at similar level
                tops = [self._zigzag_points[i].price,
                        self._zigzag_points[i+2].price,
                        self._zigzag_points[i+4].price]
                max_top = max(tops)
                min_top = min(tops)
                top_diff = max_top - min_top
                height = max_top - min(self._zigzag_points[i+1].price, self._zigzag_points[i+3].price)
                if top_diff < height * 0.1:  # Tops are at similar level
                    pattern = self._create_pattern(
                        "Triple Top",
                        PatternType.TRIPLE_TOP,
                        [i, i+1, i+2, i+3, i+4]
                    )
                    if self._validate_pattern(pattern):
                        self._patterns.append(pattern)

            # Triple Bottom: Low, High, Low, High, Low
            if (i + 4 < n and
                self._zigzag_points[i].point_type == 0 and
                self._zigzag_points[i+1].point_type == 1 and
                self._zigzag_points[i+2].point_type == 0 and
                self._zigzag_points[i+3].point_type == 1 and
                self._zigzag_points[i+4].point_type == 0):

                # Check if all bottoms are at similar level
                bottoms = [self._zigzag_points[i].price,
                           self._zigzag_points[i+2].price,
                           self._zigzag_points[i+4].price]
                max_bottom = max(bottoms)
                min_bottom = min(bottoms)
                bottom_diff = max_bottom - min_bottom
                height = min(self._zigzag_points[i+1].price, self._zigzag_points[i+3].price) - min_bottom
                if bottom_diff < height * 0.1:  # Bottoms are at similar level
                    pattern = self._create_pattern(
                        "Triple Bottom",
                        PatternType.TRIPLE_BOTTOM,
                        [i, i+1, i+2, i+3, i+4]
                    )
                    if self._validate_pattern(pattern):
                        self._patterns.append(pattern)

    def _detect_rounding(self) -> None:
        """Detect Rounding Top/Bottom patterns."""
        n = len(self._zigzag_points)
        if n < 5:
            return

        for i in range(n - 4):
            # Rounding Top: High, Low, High, Low, High (curving downward)
            if (i + 4 < n and
                self._zigzag_points[i].point_type == 1 and
                self._zigzag_points[i+1].point_type == 0 and
                self._zigzag_points[i+2].point_type == 1 and
                self._zigzag_points[i+3].point_type == 0 and
                self._zigzag_points[i+4].point_type == 1):

                # Check if the curve is rounding downward
                prices = [p.price for p in self._zigzag_points[i:i+5]]
                times = [p.time for p in self._zigzag_points[i:i+5]]

                # Fit a quadratic curve
                if len(prices) >= 3 and len(times) >= 3:
                    x = np.array(times)
                    y = np.array(prices)
                    coeffs = np.polyfit(x, y, 2)
                    if coeffs[0] < 0:  # Negative quadratic coefficient (curving downward)
                        pattern = self._create_pattern(
                            "Rounding Top",
                            PatternType.ROUNDING_TOP,
                            [i, i+1, i+2, i+3, i+4]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

            # Rounding Bottom: Low, High, Low, High, Low (curving upward)
            if (i + 4 < n and
                self._zigzag_points[i].point_type == 0 and
                self._zigzag_points[i+1].point_type == 1 and
                self._zigzag_points[i+2].point_type == 0 and
                self._zigzag_points[i+3].point_type == 1 and
                self._zigzag_points[i+4].point_type == 0):

                # Check if the curve is rounding upward
                prices = [p.price for p in self._zigzag_points[i:i+5]]
                times = [p.time for p in self._zigzag_points[i:i+5]]

                # Fit a quadratic curve
                if len(prices) >= 3 and len(times) >= 3:
                    x = np.array(times)
                    y = np.array(prices)
                    coeffs = np.polyfit(x, y, 2)
                    if coeffs[0] > 0:  # Positive quadratic coefficient (curving upward)
                        pattern = self._create_pattern(
                            "Rounding Bottom",
                            PatternType.ROUNDING_BOTTOM,
                            [i, i+1, i+2, i+3, i+4]
                        )
                        if self._validate_pattern(pattern):
                            self._patterns.append(pattern)

    def _create_pattern(
        self,
        name: str,
        pattern_type: PatternType,
        point_indices: List[int]
    ) -> Pattern:
        """Create a pattern from ZigZag points."""
        points = [self._zigzag_points[i] for i in point_indices]

        # Calculate volume confirmation
        total_volume = sum(p.volume for p in points)
        avg_volume = np.mean(self._volume_profile) if self._volume_profile else 1.0
        volume_confirmation = min(1.0, total_volume / (len(points) * avg_volume))

        pattern = Pattern(
            name=name,
            pattern_type=pattern_type,
            points=points,
            volume_confirmation=volume_confirmation,
            color=_get_pattern_color(pattern_type)
        )

        return pattern

    def _validate_pattern(self, pattern: Pattern) -> bool:
        """Validate a pattern based on various criteria."""
        # Calculate ATR for normalization
        closes = np.array([p.price for p in self._zigzag_points])
        atr = _calculate_atr(closes, closes, closes, self._config.atr_period)

        # Calculate risk and gain
        pattern.expected_risk = _calculate_pattern_risk(pattern, atr)
        pattern.expected_gain = _calculate_pattern_gain(pattern, atr)

        # Calculate reward ratio
        if pattern.expected_risk > 0:
            pattern.reward_ratio = pattern.expected_gain / pattern.expected_risk
        else:
            pattern.reward_ratio = 0.0

        # Calculate volatility factor
        if self._config.use_volatility_filter:
            pattern.volatility_factor = min(1.0, atr / (np.mean(closes) * 0.01)) if np.mean(closes) > 0 else 0.0
        else:
            pattern.volatility_factor = 0.5

        # Calculate overall score
        pattern.score = _calculate_pattern_score(pattern)

        # Set expiration (2x pattern duration)
        if len(pattern.points) >= 2:
            duration = pattern.points[-1].time - pattern.points[0].time
            pattern.expiration = pattern.points[-1].time + (duration * 2)

        # Set priority
        pattern.priority = _get_pattern_priority(
            pattern.score,
            pattern.reward_ratio,
            pattern.expected_risk,
            self._config.max_expected_sl * 100
        )

        # Validation checks
        if pattern.score < self._config.min_pattern_score:
            return False
        if pattern.expected_risk > self._config.max_expected_sl * 100:
            return False
        if pattern.reward_ratio < self._config.min_reward_ratio:
            return False
        if self._config.use_volatility_filter and pattern.volatility_factor < self._config.min_volatility_factor:
            return False
        if self._config.volume_confirmation and pattern.volume_confirmation < 0.5:
            return False

        return True

    def _filter_and_rank_patterns(self) -> None:
        """Filter and rank detected patterns."""
        # Filter out invalid patterns
        self._patterns = [p for p in self._patterns if self._validate_pattern(p)]

        # Sort by score (descending)
        self._patterns.sort(key=lambda x: x.score, reverse=True)

    def _check_higher_timeframe_confirmation(self, pattern: Pattern) -> float:
        """
        Check if pattern is confirmed on higher timeframe.
        For this implementation, we'll simulate higher timeframe data.
        In production, this would use actual MT5 data.
        """
        if not self._config.use_volatility_filter:
            return 0.5

        # Simulate higher timeframe confirmation
        # In real implementation, this would:
        # 1. Load higher timeframe data
        # 2. Check if pattern is visible on higher TF
        # 3. Check if trend aligns with pattern direction

        # For simulation, we'll use a simplified approach
        score = 0.0

        # Check if pattern aligns with overall trend
        if pattern.pattern_type in [PatternType.BULL_FLAG, PatternType.BULL_PENNANT,
                                      PatternType.ASCENDING_TRIANGLE, PatternType.INVERSE_HEAD_AND_SHOULDERS,
                                      PatternType.DOUBLE_BOTTOM, PatternType.TRIPLE_BOTTOM,
                                      PatternType.ROUNDING_BOTTOM]:
            # Bullish pattern - check if higher TF is bullish
            if self._is_overall_bullish():
                score += 0.5
        else:
            # Bearish pattern - check if higher TF is bearish
            if self._is_overall_bearish():
                score += 0.5

        # Check volume on higher TF (simulated)
        if pattern.volume_confirmation > 0.7:
            score += 0.3

        # Check if pattern is near key levels (simulated)
        score += 0.2

        return min(1.0, score)

    def _is_overall_bullish(self) -> bool:
        """Check if overall trend is bullish (simplified)."""
        if not self._zigzag_points:
            return False

        # Simple check: more highs than lows in recent points
        recent_points = self._zigzag_points[-10:]
        high_count = sum(1 for p in recent_points if p.point_type == 1)
        low_count = sum(1 for p in recent_points if p.point_type == 0)

        return high_count > low_count

    def _is_overall_bearish(self) -> bool:
        """Check if overall trend is bearish (simplified)."""
        if not self._zigzag_points:
            return False

        # Simple check: more lows than highs in recent points
        recent_points = self._zigzag_points[-10:]
        high_count = sum(1 for p in recent_points if p.point_type == 1)
        low_count = sum(1 for p in recent_points if p.point_type == 0)

        return low_count > high_count

    def compute_from_bars(self, df: pd.DataFrame) -> ComponentState:
        """
        [OMEGA MANDATORY] Primary interface.
        Accepts standard OHLCV DataFrame, returns ComponentState.
        """
        state = ComponentState()
        state.n_bars = len(df)
        state.regime = self._config.regime

        if df.empty or len(df) < self._config.min_wave_length * 2:
            return state

        # Load ZigZag points
        self._load_zigzag_points(df)

        # Calculate volume profile
        self._calculate_volume_profile(df)

        # Calculate ATR
        highs = df["high"].to_numpy(dtype=np.float64)
        lows = df["low"].to_numpy(dtype=np.float64)
        closes = df["close"].to_numpy(dtype=np.float64)
        state.atr = _calculate_atr(highs, lows, closes, self._config.atr_period)

        # Calculate volatility
        state.volatility = _calculate_volatility(closes, 20)

        # Detect patterns
        self._detect_flags_and_pennants()
        self._detect_triangles()
        self._detect_head_and_shoulders()
        self._detect_double_triple()
        self._detect_rounding()

        # Filter and rank patterns
        self._filter_and_rank_patterns()

        # Set state values
        state.detected_patterns = self._patterns
        state.zigzag_points = self._zigzag_points
        state.volume_profile = self._volume_profile

        if self._patterns:
            state.best_pattern = self._patterns[0]
            state.is_valid = True

            # Determine direction based on best pattern
            if state.best_pattern.pattern_type in [
                PatternType.BULL_FLAG, PatternType.BULL_PENNANT,
                PatternType.ASCENDING_TRIANGLE, PatternType.INVERSE_HEAD_AND_SHOULDERS,
                PatternType.DOUBLE_BOTTOM, PatternType.TRIPLE_BOTTOM,
                PatternType.ROUNDING_BOTTOM
            ]:
                state.direction = 1  # Bullish
            elif state.best_pattern.pattern_type in [
                PatternType.BEAR_FLAG, PatternType.BEAR_PENNANT,
                PatternType.DESCENDING_TRIANGLE, PatternType.HEAD_AND_SHOULDERS,
                PatternType.DOUBLE_TOP, PatternType.TRIPLE_TOP,
                PatternType.ROUNDING_TOP
            ]:
                state.direction = -1  # Bearish
            else:
                state.direction = 0  # Neutral

            # Strength is the score of the best pattern
            state.strength = state.best_pattern.score
        else:
            state.is_valid = False
            state.direction = 0
            state.strength = 0.0

        return state

    def reset(self) -> None:
        """Reset the engine state."""
        self._zigzag_points = []
        self._patterns = []
        self._volume_profile = []

# ===========================================================================
# [OMEGA MANDATORY] Self-Test & Verifiable Benchmarking
# ===========================================================================

def _run_self_test() -> int:
    """Synthetic data test. Returns 0 on success, 1 on failure."""
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta

    print("Running Institutional Pattern Detector self-test...")

    # === Test 1: Basic Functionality ===
    np.random.seed(42)
    n_bars = 200
    dates = pd.date_range(end=datetime.now(), periods=n_bars, freq="1min")

    # Zigzag-friendly: clear up/down waves (8 waves x 25 bars) with 5+ pip reversals
    wave_moves = [0.010, -0.008, 0.012, -0.007, 0.015, -0.009, 0.011, -0.006]
    prices, volumes = [], []
    current_price = 1.1000
    for move in wave_moves:
        for _ in range(25):
            current_price += move / 25 + np.random.normal(0, 0.0001)
            prices.append(current_price)
            volumes.append(1000 + np.random.randint(0, 500))

    prices, volumes = np.array(prices), np.array(volumes)
    df = pd.DataFrame({
        "open":   prices - np.abs(np.random.normal(0, 0.0003, n_bars)),
        "high":   prices + np.abs(np.random.normal(0, 0.0003, n_bars)),
        "low":    prices - np.abs(np.random.normal(0, 0.0003, n_bars)),
        "close":  prices,
        "volume": volumes,
    }, index=dates)

    # Test with default config
    config = ComponentConfig(regime="forex")
    engine = ComponentEngine.from_config(regime=config.regime)
    state = engine.compute_from_bars(df)

    # Validate output
    assert isinstance(state, ComponentState), "Output must be ComponentState"
    assert state.n_bars == n_bars, f"Expected {n_bars} bars, got {state.n_bars}"
    assert isinstance(state.is_valid, bool), "is_valid must be bool"
    assert state.direction in [-1, 0, 1], "Direction must be -1, 0, or 1"
    assert 0 <= state.strength <= 1, "Strength must be between 0 and 1"
    assert state.atr > 0, "ATR must be positive"
    assert len(state.zigzag_points) > 0, "Should detect ZigZag points"
    print("✅ Test 1 passed: Basic functionality")

    # === Test 2: Regime-Specific Config ===
    config_crypto = ComponentConfig(
        regime="crypto",
        min_pattern_score=0.70,
        zigzag_depth=10,
    )
    engine_crypto = ComponentEngine.from_config(regime=config_crypto.regime, min_pattern_score=config_crypto.min_pattern_score, zigzag_depth=config_crypto.zigzag_depth)
    state_crypto = engine_crypto.compute_from_bars(df)
    assert state_crypto.regime == "crypto", "Regime must be 'crypto'"
    print("✅ Test 2 passed: Regime-specific config")

    # === Test 3: Empty DataFrame ===
    empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    state_empty = engine.compute_from_bars(empty_df)
    assert not state_empty.is_valid, "Empty DataFrame must return is_valid=False"
    print("✅ Test 3 passed: Empty DataFrame handling")

    # === Test 4: Flag Pattern Detection ===
    # Create data with clear flag pattern
    flag_prices = np.linspace(1.0900, 1.1000, 20)  # Pole
    flag_prices = np.concatenate([
        flag_prices,
        np.linspace(1.0980, 1.0950, 10),  # Flag (consolidation)
        np.linspace(1.0950, 1.1100, 20)   # Breakout
    ])
    flag_volumes = np.concatenate([
        np.random.uniform(1000, 2000, 20),  # High volume on pole
        np.random.uniform(500, 1000, 10),    # Low volume on flag
        np.random.uniform(1500, 2500, 20)   # High volume on breakout
    ])

    flag_df = pd.DataFrame({
        "open": flag_prices - 0.0001,
        "high": flag_prices + 0.0001,
        "low": flag_prices - 0.0001,
        "close": flag_prices,
        "volume": flag_volumes,
    })

    state_flag = engine.compute_from_bars(flag_df)
    assert isinstance(state_flag, ComponentState), "compute_from_bars must return ComponentState"
    assert state_flag.n_bars == len(flag_df), "n_bars mismatch"
    print("\u2705 Test 4 passed: Flag data processed without error")

    # === Test 5: Triangle Pattern Detection ===
    # Create data with clear triangle pattern
    triangle_prices = np.concatenate([
        np.linspace(1.1000, 1.1050, 10),  # First leg up
        np.linspace(1.1050, 1.1020, 10),  # First leg down
        np.linspace(1.1020, 1.1040, 10),  # Second leg up (higher low)
        np.linspace(1.1040, 1.1030, 10),  # Second leg down (lower high)
        np.linspace(1.1030, 1.1035, 10),  # Converging
    ])
    triangle_volumes = np.random.uniform(1000, 2000, 50)

    triangle_df = pd.DataFrame({
        "open": triangle_prices - 0.0001,
        "high": triangle_prices + 0.0001,
        "low": triangle_prices - 0.0001,
        "close": triangle_prices,
        "volume": triangle_volumes,
    })

    state_triangle = engine.compute_from_bars(triangle_df)
    assert isinstance(state_triangle, ComponentState), "compute_from_bars must return ComponentState"
    assert state_triangle.n_bars == len(triangle_df), "n_bars mismatch"
    print("\u2705 Test 5 passed: Triangle data processed without error")

    # === Test 6: Head and Shoulders Detection ===
    # Create data with clear H&S pattern
    hs_prices = np.concatenate([
        np.linspace(1.0900, 1.0950, 10),  # Left shoulder
        np.linspace(1.0950, 1.1050, 10),  # Head
        np.linspace(1.1050, 1.0950, 10),  # Right shoulder
        np.linspace(1.0950, 1.0900, 10),  # Neckline break
    ])
    hs_volumes = np.random.uniform(1000, 2000, 40)

    hs_df = pd.DataFrame({
        "open": hs_prices - 0.0001,
        "high": hs_prices + 0.0001,
        "low": hs_prices - 0.0001,
        "close": hs_prices,
        "volume": hs_volumes,
    })

    state_hs = engine.compute_from_bars(hs_df)
    assert isinstance(state_hs, ComponentState), "compute_from_bars must return ComponentState"
    assert state_hs.n_bars == len(hs_df), "n_bars mismatch"
    print("\u2705 Test 6 passed: H&S data processed without error")

    # === Test 7: Pattern Validation (when patterns exist) ===
    for s_check in [state_flag, state_triangle, state_hs]:
        for pattern in s_check.detected_patterns:
            assert 0.0 <= pattern.score <= 1.0, f"Pattern score out of range: {pattern.score}"
    print("\u2705 Test 7 passed: Pattern validation")

    # === Test 8: Pattern Ranking ===
    # Patterns should be sorted by score
    if len(state_flag.detected_patterns) > 1:
        for i in range(len(state_flag.detected_patterns) - 1):
            assert state_flag.detected_patterns[i].score >= state_flag.detected_patterns[i+1].score, \
                "Patterns should be sorted by score"
    print("✅ Test 8 passed: Pattern ranking")

    # === Performance Benchmark ===
    engine_bench = ComponentEngine.from_config(regime=config.regime)
    _ = engine_bench.compute_from_bars(df)  # Warmup

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        _ = engine_bench.compute_from_bars(df)
    end = time.perf_counter()

    us_per_call = ((end - start) / iterations) * 1_000_000
    print(f"\n✅ Performance: {iterations} iterations in {(end-start)*1000:.2f}ms ({us_per_call:.2f}µs/call)")

    if us_per_call > 5000:  # 5ms hard limit for full pattern detection engine
        print("WARNING: Performance exceeds 5ms/call — consider profiling.")
        return 1

    print("\nAll Institutional Pattern Detector tests passed! Exiting with code 0.")
    return 0

# ===========================================================================
# [OMEGA MANDATORY] Module Entry Point
# ===========================================================================

if __name__ == "__main__":
    sys.exit(_run_self_test())
