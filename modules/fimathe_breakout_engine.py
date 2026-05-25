#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIMATHE Breakout Engine - OMEGA Compliant Component
====================================================
Production-grade breakout detection and risk calculation engine derived from 
the FIMATHE TIER-0 institutional framework. Completely refactored to adhere to 
the strict OMEGA checklist standard for top-tier quantitative funds.

Over-engineered components (Shield, Multi-Agent, ISO checks, SHA3 integrity) 
have been stripped to focus purely on quantitative logic. All metrics are 
strictly dimensionless (ratios, z-scores, percentages).

Dependencies:
    - numpy (required)
    - pandas (required)
    - numba (optional, JIT acceleration with pure-Python fallback)
    - MetaTrader5 (optional, available for execution wrappers, not used in core logic)
"""

from __future__ import annotations

import sys
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

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
    from numba import njit
    _HAS_NUMBA = True
except ImportError:
    def njit(*args, **kwargs):
        """No-op NJIT decorator for environments without Numba."""
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    _HAS_NUMBA = False

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================
class RegimeType(str, Enum):
    """
    Trading regime types for parameter adaptation.
    
    Attributes:
        FOREX: Standard FX pairs.
        METAL: Precious metals (e.g., XAUUSD).
        INDEX: Equity indices.
        CRYPTO: Cryptocurrencies.
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
    Configuration container for FIMATHE Breakout Engine parameters.
    
    All thresholds and values are fully parameterized to prevent hardcoded logic.
    Parameters adapt automatically based on the selected trading regime.
    
    Attributes:
        regime: Trading regime type for parameter adaptation.
        lookback: Number of bars to consider for the lookback window.
        min_range_pts: Minimum acceptable channel range in points.
        max_range_pts: Maximum acceptable channel range in points.
        rompimento_min_pct: Minimum breakout ratio (0.0 to 1.0) of channel range.
        min_breakout_pts: Absolute minimum breakout distance in points.
        atr_period: Period for Average True Range calculation.
        atr_multiplier: Multiplier for ATR to determine stop distance ratio.
        risk_pct: Fraction of capital to risk per trade (e.g., 0.01 for 1%).
        capital: Total capital baseline for risk calculations.
        min_lot: Minimum allowable lot size.
        max_lot: Maximum allowable lot size.
        high_col: Name of the high price column in the input DataFrame.
        low_col: Name of the low price column in the input DataFrame.
        close_col: Name of the close price column in the input DataFrame.
        open_col: Name of the open price column in the input DataFrame.
    """
    regime: RegimeType = RegimeType.METAL
    lookback: int = 20
    min_range_pts: float = 300.0
    max_range_pts: float = 1200.0
    rompimento_min_pct: float = 0.3
    min_breakout_pts: float = 10.0
    atr_period: int = 14
    atr_multiplier: float = 2.5
    risk_pct: float = 0.01
    capital: float = 15000.0
    min_lot: float = 0.01
    max_lot: float = 5.0
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"
    open_col: str = "open"

    _REGIME_DEFAULTS: Dict[RegimeType, Dict[str, Any]] = field(default_factory=lambda: {
        RegimeType.FOREX: {
            "min_range_pts": 10.0, 
            "max_range_pts": 50.0, 
            "atr_multiplier": 2.0, 
            "min_breakout_pts": 1.0
        },
        RegimeType.METAL: {
            "min_range_pts": 300.0, 
            "max_range_pts": 1200.0, 
            "atr_multiplier": 2.5, 
            "min_breakout_pts": 10.0
        },
        RegimeType.INDEX: {
            "min_range_pts": 50.0, 
            "max_range_pts": 200.0, 
            "atr_multiplier": 2.0, 
            "min_breakout_pts": 5.0
        },
        RegimeType.CRYPTO: {
            "min_range_pts": 100.0, 
            "max_range_pts": 500.0, 
            "atr_multiplier": 3.0, 
            "min_breakout_pts": 20.0
        },
    })

    def get_effective_params(self) -> Dict[str, Any]:
        """
        Get effective parameters after applying regime-specific defaults.
        
        Returns:
            Dictionary of effective runtime parameters.
        """
        regime_defaults = self._REGIME_DEFAULTS.get(self.regime, {})
        base = {
            "lookback": self.lookback,
            "min_range_pts": self.min_range_pts,
            "max_range_pts": self.max_range_pts,
            "rompimento_min_pct": self.rompimento_min_pct,
            "min_breakout_pts": self.min_breakout_pts,
            "atr_period": self.atr_period,
            "atr_multiplier": self.atr_multiplier,
            "risk_pct": self.risk_pct,
            "capital": self.capital,
            "min_lot": self.min_lot,
            "max_lot": self.max_lot,
            "high_col": self.high_col,
            "low_col": self.low_col,
            "close_col": self.close_col,
            "open_col": self.open_col,
        }
        return {**base, **regime_defaults}


# ============================================================================
# OMEGA MANDATORY: ComponentState Dataclass
# ============================================================================
@dataclass
class ComponentState:
    """
    Output state container for FIMATHE breakout analysis.
    
    Core output fields - OMEGA MANDATORY:
    - is_valid: Boolean validity flag
    - direction: Integer direction (+1/-1/0)
    - strength: Dimensionless strength (breakout ratio)
    - n_bars: Number of bars processed
    
    Extended dimensionless metrics:
    - breakout_ratio: Exact breakout distance / channel range
    - range_to_atr_ratio: Channel range normalized by ATR
    - risk_reward_ratio: TP1 distance / Stop distance
    - stop_distance_atr_ratio: Stop distance normalized by ATR
    - tp1_distance_ratio: TP1 distance normalized by Stop distance
    
    Attributes:
        is_valid: Whether the breakout signal is valid and actionable.
        direction: Trade direction (+1 = Long breakout, -1 = Short breakout, 0 = Neutral).
        strength: Dimensionless signal strength (breakout ratio).
        n_bars: Total bars processed in current computation window.
        breakout_ratio: Breakout magnitude relative to channel range.
        range_to_atr_ratio: Channel volatility relative to recent ATR.
        risk_reward_ratio: Initial Risk-to-Reward ratio for TP1.
        stop_distance_atr_ratio: Stop loss distance as a multiple of ATR.
        tp1_distance_ratio: Take profit 1 distance as a multiple of stop distance.
    """
    is_valid: bool = False
    direction: int = 0
    strength: float = 0.0
    n_bars: int = 0
    breakout_ratio: float = 0.0
    range_to_atr_ratio: float = 0.0
    risk_reward_ratio: float = 0.0
    stop_distance_atr_ratio: float = 0.0
    tp1_distance_ratio: float = 0.0


# ============================================================================
# Core Vectorized Computation Functions (Numba-accelerated with fallback)
# ============================================================================
if _HAS_NUMBA:
    @njit
    def _compute_tr(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """
        Numba-optimized True Range calculation.
        """
        n = len(high)
        tr = np.empty(n, dtype=np.float64)
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            hl = high[i] - low[i]
            hcp = np.abs(high[i] - close[i - 1])
            lcp = np.abs(low[i] - close[i - 1])
            tr[i] = max(hl, hcp, lcp)
        return tr
else:
    def _compute_tr(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """
        Pure-Python True Range calculation fallback.
        """
        hl = high - low
        hcp = np.abs(high - np.roll(close, 1))
        lcp = np.abs(low - np.roll(close, 1))
        tr = np.maximum(np.maximum(hl, hcp), lcp)
        tr[0] = high[0] - low[0]
        return tr


# ============================================================================
# OMEGA MANDATORY: ComponentEngine Class
# ============================================================================
class ComponentEngine:
    """
    FIMATHE Breakout Detection and Risk Calculation Engine.
    
    Implements OMEGA MANDATORY interface:
        compute_from_bars(self, df: pd.DataFrame) -> ComponentState
    
    Methodology derived from FIMATHE TIER-0:
    1. Canal Abertura: Identifies a baseline channel using the first 4 bars 
       of the lookback window. Validates if the range is within acceptable limits.
    2. Primeiro Ciclo: Detects breakouts beyond the channel boundaries. Calculates
       the dimensionless breakout ratio (distance / range).
    3. Gestao Fimathe: Calculates ATR, translates absolute stop distances into 
       dimensionless ATR ratios, and computes Risk/Reward metrics.
    
    All outputs are dimensionless (ratios) per OMEGA mandate.
    
    Attributes:
        config: ComponentConfig instance with all parameters.
        _params: Effective parameters after regime defaults applied.
    """

    def __init__(self, config: Optional[ComponentConfig] = None) -> None:
        """
        Initialize the FIMATHE breakout engine.
        
        Args:
            config: Component configuration. Uses METAL defaults if None.
        """
        self.config = config or ComponentConfig()
        self._params = self.config.get_effective_params()
        self._n_bars_processed: int = 0

    @classmethod
    def from_config(cls, regime=None, **kwargs: Any) -> "ComponentEngine":
        """
        Factory method — OMEGA MANDATORY interface.
        Accepts both regime string (shadow_loop) and ComponentConfig (legacy).
        Maps 'commodity' to 'metal' for XAU/XAG compatibility.
        """
        if isinstance(regime, ComponentConfig):
            return cls(config=regime)
        _REGIME_MAP = {"commodity": "metal", "precious": "metal"}
        regime_str = _REGIME_MAP.get(str(regime or "metal").lower(), str(regime or "metal").lower())
        try:
            regime_enum = RegimeType(regime_str)
        except ValueError:
            regime_enum = RegimeType.METAL
        config = ComponentConfig(regime=regime_enum, **kwargs)
        return cls(config=config)

    def reset(self) -> None:
        """
        Reset all internal state for fresh computation.
        
        Clears bar counter while preserving configuration.
        """
        self._n_bars_processed = 0

    def compute_from_bars(self, df: pd.DataFrame) -> ComponentState:
        """
        Compute breakout state from standard OHLCV DataFrame.
        
        OMEGA MANDATORY interface. Expects DataFrame with columns:
        - {open_col}: Open prices
        - {high_col}: High prices
        - {low_col}: Low prices
        - {close_col}: Close prices
        
        Args:
            df: DataFrame with required OHLC columns. Can be empty.
            
        Returns:
            ComponentState with is_valid, direction, strength, n_bars.
            If input is invalid or no breakout is detected, returns state with is_valid=False.
        """
        # Validate input
        if df is None or df.empty:
            return ComponentState(is_valid=False, n_bars=0)

        high_col = self._params["high_col"]
        low_col = self._params["low_col"]
        close_col = self._params["close_col"]
        open_col = self._params["open_col"]

        if not all(col in df.columns for col in [high_col, low_col, close_col, open_col]):
            logger.warning(
                f"Missing required OHLC columns: need '{high_col}', '{low_col}', "
                f"'{close_col}', '{open_col}'. Got {list(df.columns)}"
            )
            return ComponentState(is_valid=False, n_bars=len(df))

        self._n_bars_processed += len(df)
        lookback = self._params["lookback"]
        
        # 1. CANAL ABERTURA (4 bars)
        df_lookback = df.tail(lookback)
        if len(df_lookback) < 4:
            return ComponentState(is_valid=False, n_bars=self._n_bars_processed)
            
        canal_bars = df_lookback.head(4)
        canal_high = canal_bars[high_col].max()
        canal_low = canal_bars[low_col].min()
        canal_range = canal_high - canal_low
        
        # Validate channel range
        min_range = self._params["min_range_pts"]
        max_range = self._params["max_range_pts"]
        valid_range = min_range <= canal_range <= max_range
        
        if not valid_range or canal_range <= 0:
            return ComponentState(is_valid=False, n_bars=self._n_bars_processed)
            
        # 2. PRIMEIRO CICLO (Breakout Detection)
        # Look at the last 3 bars for breakout confirmation
        recent_bars = df.tail(3)
        current_high = recent_bars[high_col].max()
        current_low = recent_bars[low_col].min()
        
        # Calculate dimensionless breakout ratios
        long_strength = (current_high - canal_high) / canal_range
        short_strength = (canal_low - current_low) / canal_range
        
        # Determine minimum breakout threshold dimensionlessly
        rompimento_min_pct = self._params["rompimento_min_pct"]
        min_breakout_pts = self._params["min_breakout_pts"]
        min_breakout_ratio = max(
            rompimento_min_pct, 
            (min_breakout_pts / canal_range)
        )
        
        long_rompeu = long_strength > min_breakout_ratio
        short_rompeu = short_strength > min_breakout_ratio
        
        direction = 0
        strength = 0.0
        is_valid = False
        breakout_ratio = 0.0
        
        if long_rompeu or short_rompeu:
            is_valid = True
            if long_rompeu and long_strength >= short_strength:
                direction = 1
                strength = long_strength
                breakout_ratio = long_strength
            else:
                direction = -1
                strength = short_strength
                breakout_ratio = short_strength
        else:
            return ComponentState(
                is_valid=False, 
                n_bars=self._n_bars_processed,
                strength=strength,
                direction=direction
            )
            
        # 3. GESTAO FIMATHE (Risk and ATR Metrics)
        atr_period = self._params["atr_period"]
        
        # Compute True Range vector
        high_arr = df[high_col].values.astype(np.float64)
        low_arr = df[low_col].values.astype(np.float64)
        close_arr = df[close_col].values.astype(np.float64)
        
        tr = _compute_tr(high_arr, low_arr, close_arr)
        
        # Exponential Moving Average of True Range (ATR)
        atr_series = pd.Series(tr).ewm(span=atr_period, adjust=False).mean()
        atr_value = atr_series.iloc[-1] if len(atr_series) > 0 else canal_range * 0.1
        
        # Fallback for zero ATR
        if atr_value <= 0:
            atr_value = canal_range * 0.1
            
        # Stop distance as ratio of ATR (dimensionless)
        atr_multiplier = self._params["atr_multiplier"]
        stop_distance_atr_ratio = atr_multiplier
        
        # TP1 defined as 1:1 R:R -> ratio of 1.0 relative to stop distance
        tp1_distance_ratio = 1.0 
        
        # Calculate Risk/Reward ratio
        risk_reward_ratio = tp1_distance_ratio / stop_distance_atr_ratio if stop_distance_atr_ratio > 0 else 0.0
        
        # Range to ATR ratio (volatility context)
        range_to_atr_ratio = canal_range / atr_value if atr_value > 0 else 0.0

        return ComponentState(
            is_valid=is_valid,
            direction=direction,
            strength=strength,
            n_bars=self._n_bars_processed,
            breakout_ratio=breakout_ratio,
            range_to_atr_ratio=range_to_atr_ratio,
            risk_reward_ratio=risk_reward_ratio,
            stop_distance_atr_ratio=stop_distance_atr_ratio,
            tp1_distance_ratio=tp1_distance_ratio,
        )


# ============================================================================
# Factory Function
# ============================================================================
def create_engine(
    regime: str = "metal",
    lookback: int = 20,
    **kwargs: Any,
) -> ComponentEngine:
    """
    Factory function for engine creation with simplified interface.
    
    Args:
        regime: Trading regime (forex/metal/index/crypto).
        lookback: Rolling window size for channel lookback.
        **kwargs: Additional ComponentConfig parameters.
        
    Returns:
        Configured ComponentEngine instance.
    """
    try:
        regime_enum = RegimeType(regime.lower())
    except ValueError:
        logger.warning(f"Unknown regime '{regime}', defaulting to METAL")
        regime_enum = RegimeType.METAL

    config = ComponentConfig(
        regime=regime_enum,
        lookback=lookback,
        **kwargs,
    )
    return ComponentEngine.from_config(config)


# ============================================================================
# OMEGA MANDATORY: Self-Test Block
# ============================================================================
def _run_self_tests() -> bool:
    """
    Execute comprehensive self-tests with synthetic data.
    
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("Running OMEGA self-test suite...")
    logger.info("=" * 60)
    all_passed = True

    # ------------------------------------------------------------------
    # Test 1: Basic Instantiation and Defaults
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine()
        assert engine.config.regime == RegimeType.METAL
        assert engine._params["lookback"] == 20
        assert engine._params["atr_multiplier"] == 2.5
        logger.info("  [PASS] Test 1: Basic instantiation")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 1: Basic instantiation - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 2: Regime-Specific Adaptation
    # ------------------------------------------------------------------
    try:
        forex_engine = ComponentEngine(config=ComponentConfig(regime=RegimeType.FOREX))
        assert forex_engine._params["min_range_pts"] == 10.0
        assert forex_engine._params["atr_multiplier"] == 2.0
        
        crypto_engine = ComponentEngine(config=ComponentConfig(regime=RegimeType.CRYPTO))
        assert crypto_engine._params["atr_multiplier"] == 3.0
        logger.info("  [PASS] Test 2: Regime-specific adaptation")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 2: Regime-specific adaptation - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 3: from_config Factory Classmethod
    # ------------------------------------------------------------------
    try:
        config = ComponentConfig(lookback=50, rompimento_min_pct=0.5)
        engine = ComponentEngine.from_config(config)
        assert engine._params["lookback"] == 50
        assert engine._params["rompimento_min_pct"] == 0.5
        logger.info("  [PASS] Test 3: from_config factory")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 3: from_config factory - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 4: OMEGA MANDATORY Output Field Validation
    # ------------------------------------------------------------------
    try:
        # Generate synthetic long breakout data
        np.random.seed(42)
        n = 100
        base_price = 2000.0
        
        # Create a valid channel in the first 4 bars of the lookback
        opens = np.full(n, base_price) + np.random.normal(0, 1, n)
        highs = np.full(n, base_price + 500.0) + np.random.normal(0, 1, n)
        lows = np.full(n, base_price) + np.random.normal(0, 1, n)
        closes = np.full(n, base_price + 250.0) + np.random.normal(0, 1, n)
        
        # Inject strong breakout in last 3 bars
        highs[-3:] = base_price + 900.0
        lows[-3:] = base_price + 400.0
        closes[-3:] = base_price + 800.0
        
        df_long = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes})
        
        engine = ComponentEngine()
        state = engine.compute_from_bars(df_long)
        
        assert hasattr(state, "is_valid")
        assert hasattr(state, "direction")
        assert hasattr(state, "strength")
        assert hasattr(state, "n_bars")
        assert isinstance(state.is_valid, bool)
        assert isinstance(state.direction, int)
        assert isinstance(state.strength, float)
        assert isinstance(state.n_bars, int)
        assert state.direction in (-1, 0, 1)
        logger.info("  [PASS] Test 4: OMEGA output fields")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 4: OMEGA output fields - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 5: Valid Long Breakout Logic
    # ------------------------------------------------------------------
    try:
        assert state.is_valid is True, "Should detect valid long breakout"
        assert state.direction == 1, f"Direction should be 1 (Long), got {state.direction}"
        assert state.strength > 0.0, "Strength must be positive"
        assert state.n_bars == 100
        # Breakout distance is 400 (900 - 500). Channel range is 500. Ratio is 0.8.
        assert abs(state.breakout_ratio - 0.8) < 0.1, f"Breakout ratio unexpected: {state.breakout_ratio}"
        logger.info("  [PASS] Test 5: Valid Long Breakout logic")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 5: Valid Long Breakout logic - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 6: Valid Short Breakout Logic
    # ------------------------------------------------------------------
    try:
        np.random.seed(42)
        n = 100
        base_price = 2000.0
        
        opens = np.full(n, base_price) + np.random.normal(0, 1, n)
        highs = np.full(n, base_price + 500.0) + np.random.normal(0, 1, n)
        lows = np.full(n, base_price) + np.random.normal(0, 1, n)
        closes = np.full(n, base_price + 250.0) + np.random.normal(0, 1, n)
        
        # Inject short breakout
        lows[-3:] = base_price - 400.0
        highs[-3:] = base_price + 100.0
        closes[-3:] = base_price - 300.0
        
        df_short = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes})
        
        engine = ComponentEngine()
        state_short = engine.compute_from_bars(df_short)
        
        assert state_short.is_valid is True
        assert state_short.direction == -1, f"Direction should be -1 (Short), got {state_short.direction}"
        logger.info("  [PASS] Test 6: Valid Short Breakout logic")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 6: Valid Short Breakout logic - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 7: Dimensionless Output Range Validation
    # ------------------------------------------------------------------
    try:
        # state_long from Test 5
        assert state.stop_distance_atr_ratio > 0, "Stop distance ratio must be > 0"
        assert state.tp1_distance_ratio == 1.0, "TP1 ratio should be 1.0 (1:1 R:R)"
        assert state.risk_reward_ratio > 0, "Risk reward ratio must be > 0"
        assert state.range_to_atr_ratio > 0, "Range/ATR ratio must be > 0"
        logger.info("  [PASS] Test 7: Dimensionless output validation")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 7: Dimensionless output validation - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 8: Invalid Channel Range Handling
    # ------------------------------------------------------------------
    try:
        np.random.seed(42)
        n = 100
        base_price = 2000.0
        
        # Channel range is only 10 points (violates min_range_pts=300)
        opens = np.full(n, base_price)
        highs = np.full(n, base_price + 5.0)
        lows = np.full(n, base_price - 5.0)
        closes = np.full(n, base_price)
        
        # Even with massive breakout, invalid range should invalidate signal
        highs[-3:] = base_price + 500.0
        
        df_invalid_range = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes})
        
        engine = ComponentEngine()
        state_invalid = engine.compute_from_bars(df_invalid_range)
        
        assert state_invalid.is_valid is False, "Should be invalid due to small channel range"
        logger.info("  [PASS] Test 8: Invalid channel range handling")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 8: Invalid channel range handling - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 9: Edge Case - Empty DataFrame
    # ------------------------------------------------------------------
    try:
        engine = ComponentEngine()
        state_empty = engine.compute_from_bars(pd.DataFrame())
        assert state_empty.is_valid is False
        assert state_empty.n_bars == 0
        logger.info("  [PASS] Test 9: Empty DataFrame handling")
    except AssertionError as e:
        logger.error(f"  [FAIL] Test 9: Empty DataFrame handling - {e}")
        all_passed = False

    # ------------------------------------------------------------------
    # Test 10: Optional Imports Status
    # ------------------------------------------------------------------
    try:
        logger.info(f"  [INFO] MT5 available: {_HAS_MT5}")
        logger.info(f"  [INFO] Numba available: {_HAS_NUMBA}")
        assert callable(njit)
        logger.info("  [PASS] Test 10: Optional imports check")
    except Exception as e:
        logger.error(f"  [FAIL] Test 10: Optional imports check - {e}")
        all_passed = False

    logger.info("=" * 60)
    return all_passed


if __name__ == "__main__":
    """
    Self-test entry point - OMEGA MANDATORY.
    
    Uses only synthetic data (no external API dependencies).
    Exits with code 0 on success, 1 on failure.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    success = _run_self_tests()
    if success:
        logger.info("ALL OMEGA SELF-TESTS PASSED")
        sys.exit(0)
    else:
        logger.error("SOME OMEGA SELF-TESTS FAILED")
        sys.exit(1)
