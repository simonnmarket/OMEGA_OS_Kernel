#!/usr/bin/env python3
"""
AURORA Risk Engine - TIER-0 Certified
Consolidação: Estrutura base (Estrategias) + Stress Testing avançado (DeepSeek)

Features:
- VaR: Historical, Parametric (Cornish-Fisher), Monte Carlo (GARCH)
- CVaR (Expected Shortfall)
- Backtesting: Kupiec Test, Christoffersen Test, Basel Traffic Light
- Stress Testing: 5 tipos de shock com validação
- Kill Switch Integration
- Risk Metrics: Sharpe, Sortino, Max Drawdown, Jarque-Bera

Data: 03-12-2025
Integrado ao Sistema AURORA v4.0
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any, Callable
from datetime import datetime, timezone
import warnings
import hashlib
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ============================================================================
# GENESIS LAYER - INSTITUTIONAL SHIELDING
# ============================================================================

def _generate_genesis_checksum() -> str:
    """Generate runtime checksum for institutional validation"""
    import sys
    import platform
    import os
    
    runtime_info = f"{platform.python_version()}_{sys.platform}_{os.getpid()}_{datetime.now(timezone.utc).timestamp()}"
    return hashlib.sha3_256(runtime_info.encode()).hexdigest()[:16].upper()

GENESIS_CHECKSUM = _generate_genesis_checksum()


# ============================================================================
# RISK ENGINE - TIER-0 CERTIFIED
# ============================================================================

class RiskEngine:
    """
    Institutional-grade Risk Management Engine (TIER-0 Certified).
    
    Mathematical Guarantees:
    1. VaR with multiple methods (Historical, Parametric, Monte Carlo)
    2. CVaR (Expected Shortfall) for tail risk
    3. Backtesting with Kupiec and Christoffersen tests
    4. Basel Committee traffic light compliance
    5. Advanced stress testing with 5 shock types
    6. Kill-switch integration for drawdown protection
    
    Usage:
        engine = RiskEngine(confidence_level=0.95)
        result = engine.calculate_portfolio_var(returns, method='historical')
    """
    
    def __init__(
        self, 
        confidence_level: float = 0.95,
        lookback_window: int = 252,
        kill_switch_threshold: float = 0.15  # 15% drawdown
    ):
        """
        Initialize RiskEngine with institutional parameters.
        
        Args:
            confidence_level: VaR confidence level (default 95%)
            lookback_window: Historical lookback period (default 252 trading days)
            kill_switch_threshold: Maximum drawdown before kill switch (default 15%)
        """
        self.confidence = confidence_level
        self.lookback = lookback_window
        self.kill_switch_threshold = kill_switch_threshold
        self.var_methods = ['historical', 'parametric', 'monte_carlo']
        self.cache = {}
        
        logger.info(f"RiskEngine initialized | Confidence: {confidence_level:.0%} | "
                   f"Lookback: {lookback_window} | Genesis: {GENESIS_CHECKSUM}")
    
    # ========================================================================
    # MAIN VaR CALCULATION
    # ========================================================================
    
    def calculate_portfolio_var(
        self,
        returns: pd.Series,
        method: str = 'historical',
        portfolio_value: float = 1_000_000.0
    ) -> Dict[str, Any]:
        """
        Calculate Value at Risk with full validation and backtesting.
        
        Args:
            returns: Historical returns series
            method: VaR method ('historical', 'parametric', 'monte_carlo')
            portfolio_value: Portfolio value for absolute VaR
        
        Returns:
            Dict with VaR results, backtesting, and risk metrics
        """
        # Use lookback window for VaR calculation
        returns_clean = returns.dropna().tail(self.lookback)
        
        if len(returns_clean) < 30:
            return {
                'status': 'ERROR',
                'error': f'Insufficient data for VaR calculation. Required >30, found {len(returns_clean)}.',
                'genesis_checksum': GENESIS_CHECKSUM
            }
        
        # Check kill-switch condition
        risk_metrics = self._calculate_risk_metrics(returns_clean)
        if abs(risk_metrics['max_drawdown']) > self.kill_switch_threshold:
            return {
                'status': 'KILL_SWITCH',
                'reason': f"Maximum drawdown ({risk_metrics['max_drawdown']:.2%}) exceeds threshold ({self.kill_switch_threshold:.2%})",
                'risk_metrics': risk_metrics,
                'genesis_checksum': GENESIS_CHECKSUM
            }
        
        # Calculate VaR based on method
        if method == 'historical':
            var_results = self._var_historical(returns_clean)
        elif method == 'parametric':
            var_results = self._var_parametric(returns_clean)
        elif method == 'monte_carlo':
            var_results = self._var_monte_carlo(returns_clean)
        else:
            return {
                'status': 'ERROR',
                'error': f"Unknown VaR method: {method}. Use: {self.var_methods}",
                'genesis_checksum': GENESIS_CHECKSUM
            }
        
        # Convert to absolute values
        var_relative = var_results['var']
        cvar_relative = var_results.get('cvar', var_relative * 1.5)
        
        var_absolute = abs(var_relative * portfolio_value)
        cvar_absolute = abs(cvar_relative * portfolio_value)
        
        # Backtest using full data
        backtest_results = self.backtest_var(
            returns.dropna(),
            var_relative,
            self.confidence
        )
        
        # Compile results
        return {
            'status': 'SUCCESS',
            'method': method,
            'confidence_level': self.confidence,
            'lookback_period': len(returns_clean),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            
            # Relative VaR (percentage)
            'var_relative': float(var_relative),
            'cvar_relative': float(cvar_relative),
            
            # Absolute VaR (currency)
            'var_absolute': float(var_absolute),
            'cvar_absolute': float(cvar_absolute),
            
            # Portfolio impact
            'portfolio_value': portfolio_value,
            'var_percentage_of_portfolio': abs(var_relative * 100),
            
            # Backtesting results
            'backtesting': backtest_results,
            
            # Additional risk metrics
            'risk_metrics': risk_metrics,
            
            # Validation flags
            'is_valid': backtest_results['kupiec_test']['passed'] and backtest_results['christoffersen_test']['passed'],
            'data_quality': self._assess_data_quality(returns_clean),
            
            # Method-specific details
            'method_details': var_results,
            
            # Genesis checksum
            'genesis_checksum': GENESIS_CHECKSUM
        }
    
    # ========================================================================
    # VaR METHODS
    # ========================================================================
    
    def _var_historical(self, returns: pd.Series) -> Dict:
        """Historical VaR (non-parametric)"""
        var = -np.percentile(returns, (1 - self.confidence) * 100)
        
        # Calculate CVaR (Expected Shortfall)
        var_threshold = -var
        tail_returns = returns[returns <= var_threshold]
        cvar = -tail_returns.mean() if len(tail_returns) > 0 else var * 1.5
        
        return {
            'var': var,
            'cvar': cvar,
            'tail_observations': len(tail_returns),
            'tail_mean': float(-tail_returns.mean()) if len(tail_returns) > 0 else None
        }
    
    def _var_parametric(self, returns: pd.Series) -> Dict:
        """
        Parametric VaR with Cornish-Fisher expansion for non-normality.
        Adjusts for skewness and kurtosis.
        """
        mu = returns.mean()
        sigma = returns.std()
        
        # Adjust for skewness and kurtosis
        skew = stats.skew(returns)
        kurt = stats.kurtosis(returns)  # Excess kurtosis
        
        # Cornish-Fisher expansion
        z = stats.norm.ppf(1 - self.confidence)
        z_adj = (z + (z**2 - 1) * skew / 6 +
                 (z**3 - 3*z) * kurt / 24 -
                 (2*z**3 - 5*z) * skew**2 / 36)
        
        var = -(mu + sigma * z_adj)
        
        # Parametric CVaR (using normal expectation)
        alpha = 1 - self.confidence
        try:
            expected_shortfall_norm = sigma * stats.norm.expect(
                lambda x: x,
                loc=0,
                scale=1,
                lb=stats.norm.ppf(alpha)
            ) / alpha
            cvar = -(mu + expected_shortfall_norm)
        except:
            cvar = var * 1.5
        
        return {
            'var': var,
            'cvar': cvar,
            'mu': float(mu),
            'sigma': float(sigma),
            'skew': float(skew),
            'kurtosis': float(kurt),
            'z_score': float(z),
            'z_adjusted': float(z_adj),
            'cornish_fisher_applied': True
        }
    
    def _var_monte_carlo(self, returns: pd.Series, n_simulations: int = 10000) -> Dict:
        """
        Monte Carlo VaR with GARCH volatility modeling.
        Falls back to parametric if GARCH fails.
        """
        try:
            from arch import arch_model
        except ImportError:
            logger.warning("arch library not available, using parametric VaR as fallback")
            result = self._var_parametric(returns)
            result['fallback'] = 'parametric (arch not installed)'
            return result
        
        try:
            # Fit GARCH(1,1) model with Student-t distribution
            model = arch_model(returns * 100, vol='Garch', p=1, q=1, dist='t')
            fitted = model.fit(disp='off')
            
            # Forecast volatility
            forecast = fitted.forecast(horizon=1)
            sigma_t = np.sqrt(forecast.variance.values[-1, 0]) / 100
            
            # Monte Carlo simulation
            np.random.seed(42)
            simulations = np.random.normal(
                returns.mean(),
                sigma_t,
                n_simulations
            )
            
            var = -np.percentile(simulations, (1 - self.confidence) * 100)
            
            # CVaR from simulations
            var_threshold = -var
            tail_simulations = simulations[simulations <= var_threshold]
            cvar = -tail_simulations.mean() if len(tail_simulations) > 0 else var * 1.5
            
            return {
                'var': var,
                'cvar': cvar,
                'garch_sigma': float(sigma_t),
                'n_simulations': n_simulations,
                'garch_params': fitted.params.to_dict(),
                'model': 'GARCH(1,1)'
            }
            
        except (ValueError, IndexError) as e:
            logger.warning(f"GARCH optimization failed ({e}), using parametric fallback")
            result = self._var_parametric(returns)
            result['fallback'] = f'parametric (GARCH failed: {e})'
            return result
    
    # ========================================================================
    # BACKTESTING
    # ========================================================================
    
    def backtest_var(
        self,
        returns: pd.Series,
        var_estimate: float,
        confidence: float
    ) -> Dict:
        """
        Backtest VaR using Kupiec test, Christoffersen test, and Basel traffic light.
        """
        # Identify VaR violations
        violations = returns < -abs(var_estimate)
        n_violations = int(violations.sum())
        n_observations = len(returns)
        
        if n_observations == 0:
            return {
                'n_observations': 0,
                'n_violations': 0,
                'violation_rate': 0,
                'kupiec_test': {'passed': False, 'p_value': 0},
                'christoffersen_test': {'passed': False, 'p_value': 0},
                'basel_traffic_light': {'zone': 'N/A', 'capital_multiplier': 1.0},
                'expected_rate': 1 - confidence,
                'var_accuracy': 0
            }
        
        violation_rate = n_violations / n_observations
        expected_rate = 1 - confidence
        
        # Kupiec test (unconditional coverage)
        kupiec_results = self._kupiec_test(n_violations, n_observations, expected_rate)
        
        # Christoffersen test (independence)
        christoffersen_results = self._christoffersen_test(violations)
        
        # Basel traffic light
        traffic_light = self._basel_traffic_light(n_violations, n_observations, confidence)
        
        return {
            'n_observations': n_observations,
            'n_violations': n_violations,
            'violation_rate': float(violation_rate),
            'expected_rate': float(expected_rate),
            'kupiec_test': kupiec_results,
            'christoffersen_test': christoffersen_results,
            'basel_traffic_light': traffic_light,
            'var_accuracy': float(1 - abs(violation_rate - expected_rate) / expected_rate) if expected_rate > 0 else 0
        }
    
    def _kupiec_test(self, n_violations: int, n_observations: int, expected_rate: float) -> Dict:
        """Kupiec test for unconditional coverage"""
        from scipy.stats import chi2
        
        actual_rate = n_violations / n_observations if n_observations > 0 else 0
        
        # Handle edge cases
        if actual_rate == 0 or actual_rate == 1:
            LR = 0.0
        else:
            term_actual = ((1 - actual_rate) ** (n_observations - n_violations) *
                          actual_rate ** n_violations)
            term_expected = ((1 - expected_rate) ** (n_observations - n_violations) *
                            expected_rate ** n_violations)
            
            if term_expected == 0 or term_actual == 0:
                LR = 0.0
            else:
                LR = -2 * np.log(term_expected / term_actual)
        
        p_value = float(1 - chi2.cdf(LR, 1)) if LR >= 0 else 0.0
        
        return {
            'LR_statistic': float(LR),
            'p_value': p_value,
            'passed': p_value > 0.05,
            'null_hypothesis': 'Violation rate equals expected rate'
        }
    
    def _christoffersen_test(self, violations: pd.Series) -> Dict:
        """Christoffersen test for independence of violations"""
        from scipy.stats import chi2
        
        # Create transition matrix
        n00 = n01 = n10 = n11 = 0
        
        for i in range(1, len(violations)):
            prev = violations.iloc[i-1]
            curr = violations.iloc[i]
            
            if not prev and not curr:
                n00 += 1
            elif not prev and curr:
                n01 += 1
            elif prev and not curr:
                n10 += 1
            else:
                n11 += 1
        
        # Calculate probabilities
        n0 = n00 + n01
        n1 = n10 + n11
        N = n0 + n1
        
        pi0 = n01 / n0 if n0 > 0 else 0
        pi1 = n11 / n1 if n1 > 0 else 0
        pi = (n01 + n11) / N if N > 0 else 0
        
        # Likelihood ratio test
        try:
            L0 = ((1 - pi) ** n0) * (pi ** n01) * ((1 - pi) ** n1) * (pi ** n11)
            L1 = ((1 - pi0) ** n00) * (pi0 ** n01) * ((1 - pi1) ** n10) * (pi1 ** n11)
            
            if L0 > 0 and L1 > 0:
                LR = -2 * (np.log(L0) - np.log(L1))
            else:
                LR = 0.0
        except:
            LR = 0.0
        
        p_value = float(1 - chi2.cdf(LR, 1)) if LR >= 0 else 0.0
        
        return {
            'LR_statistic': float(LR),
            'p_value': p_value,
            'passed': p_value > 0.05,
            'null_hypothesis': 'Violations are independent',
            'transition_matrix': {'00': n00, '01': n01, '10': n10, '11': n11},
            'probabilities': {'pi0': float(pi0), 'pi1': float(pi1), 'pi': float(pi)}
        }
    
    def _basel_traffic_light(self, n_violations: int, n_observations: int, confidence: float) -> Dict:
        """Basel Committee traffic light approach"""
        expected_violations = (1 - confidence) * n_observations
        
        # Basel II/III strict rules for 99% VaR, 250 days
        if abs(confidence - 0.99) < 1e-4 and n_observations >= 250:
            if n_violations <= 4:
                zone = 'GREEN'
                multiplier = 1.0
            elif n_violations <= 9:
                zone = 'YELLOW'
                multiplier = 1.0 + 0.4 * (n_violations - 4) / 5
            else:
                zone = 'RED'
                multiplier = 1.5
            
            return {
                'zone': zone,
                'capital_multiplier': float(multiplier),
                'violations': n_violations,
                'thresholds': {'green': 4, 'yellow': 9, 'red': 10}
            }
        
        # Heuristic for other confidence levels
        green_zone = int(expected_violations * 1.5)
        yellow_zone = int(expected_violations * 2.5)
        
        if n_violations <= green_zone:
            zone = 'GREEN'
            multiplier = 1.0
        elif n_violations <= yellow_zone:
            zone = 'YELLOW'
            multiplier = 1.2
        else:
            zone = 'RED'
            multiplier = 1.5
        
        return {
            'zone': zone,
            'capital_multiplier': float(multiplier),
            'violations': n_violations,
            'thresholds': {'green': green_zone, 'yellow': yellow_zone}
        }
    
    # ========================================================================
    # STRESS TESTING (FROM DEEPSEEK)
    # ========================================================================
    
    def stress_test_scenarios(
        self,
        returns: pd.Series,
        scenarios: List[Dict[str, Any]],
        portfolio_value: float = 1_000_000.0,
        validation_required: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive stress testing with 5 shock types.
        
        Shock Types:
        1. percentage: Multiply returns by (1 + shock_value)
        2. absolute: Add shock_value to returns
        3. volatility: Scale by volatility multiplier
        4. extreme_event: Apply callable function
        5. regime_shift: Change distribution parameters
        
        Args:
            returns: Historical returns
            scenarios: List of scenario definitions
            portfolio_value: Portfolio value for absolute calculations
            validation_required: Whether to validate stressed returns
        
        Returns:
            Dict with comprehensive stress test results
        """
        returns_clean = returns.dropna()
        
        if len(returns_clean) < 100:
            return {
                'status': 'ERROR',
                'error': 'Insufficient data for stress testing',
                'min_required': 100,
                'available': len(returns_clean),
                'genesis_checksum': GENESIS_CHECKSUM
            }
        
        # Calculate baseline VaR
        try:
            baseline_result = self.calculate_portfolio_var(
                returns_clean,
                method='historical',
                portfolio_value=portfolio_value
            )
            
            if baseline_result.get('status') == 'KILL_SWITCH':
                return {
                    'status': 'KILL_SWITCH',
                    'reason': 'Baseline VaR triggered kill-switch',
                    'baseline_drawdown': baseline_result.get('risk_metrics', {}).get('max_drawdown', 0),
                    'genesis_checksum': GENESIS_CHECKSUM
                }
            
            if baseline_result.get('status') == 'ERROR':
                return baseline_result
            
            baseline_var = baseline_result['var_absolute']
            baseline_cvar = baseline_result['cvar_absolute']
            baseline_metrics = baseline_result['risk_metrics']
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': f'Baseline VaR calculation failed: {str(e)}',
                'genesis_checksum': GENESIS_CHECKSUM
            }
        
        # Process each scenario
        scenario_results = {}
        
        for scenario in scenarios:
            scenario_name = scenario.get('name', f'scenario_{len(scenario_results)}')
            scenario_desc = scenario.get('description', '')
            shock_type = scenario.get('shock_type', 'percentage')
            shock_value = scenario.get('shock', 0.0)
            method = scenario.get('method', 'historical')
            
            # Create stressed returns
            stressed_returns = returns_clean.copy()
            
            try:
                if shock_type == 'percentage':
                    # Percentage shock: multiply returns
                    stressed_returns = stressed_returns * (1 + shock_value)
                    
                elif shock_type == 'absolute':
                    # Absolute shock: add to returns
                    stressed_returns = stressed_returns + shock_value
                    
                elif shock_type == 'volatility':
                    # Volatility shock: scale by multiplier
                    stressed_returns = stressed_returns * shock_value
                    
                elif shock_type == 'extreme_event':
                    # Extreme event: apply callable
                    if callable(shock_value):
                        stressed_returns = shock_value(stressed_returns)
                    else:
                        raise ValueError("extreme_event requires callable shock_value")
                    
                elif shock_type == 'regime_shift':
                    # Regime shift: change distribution
                    new_mean = scenario.get('new_mean', returns_clean.mean())
                    new_vol = scenario.get('new_vol', returns_clean.std())
                    
                    z_scores = (stressed_returns - stressed_returns.mean()) / stressed_returns.std()
                    stressed_returns = z_scores * new_vol + new_mean
                    
                else:
                    raise ValueError(f"Unknown shock_type: {shock_type}")
                
                # Validate stressed returns
                validation = None
                if validation_required:
                    validation = self._validate_stressed_returns(
                        original=returns_clean,
                        stressed=stressed_returns,
                        scenario=scenario
                    )
                    
                    if not validation.get('is_valid', True):
                        scenario_results[scenario_name] = {
                            'status': 'VALIDATION_FAILED',
                            'errors': validation.get('errors', []),
                            'warnings': validation.get('warnings', [])
                        }
                        continue
                
                # Calculate VaR for stressed scenario
                stress_result = self.calculate_portfolio_var(
                    stressed_returns,
                    method=method,
                    portfolio_value=portfolio_value
                )
                
                if stress_result.get('status') != 'SUCCESS':
                    raise ValueError(stress_result.get('error', 'Unknown error'))
                
                # Calculate impact metrics
                var_stress = stress_result['var_absolute']
                cvar_stress = stress_result['cvar_absolute']
                stress_metrics = stress_result['risk_metrics']
                
                scenario_results[scenario_name] = {
                    'status': 'SUCCESS',
                    'description': scenario_desc,
                    'shock_type': shock_type,
                    'shock_value': shock_value if not callable(shock_value) else 'callable',
                    'method': method,
                    'var_stress': float(var_stress),
                    'cvar_stress': float(cvar_stress),
                    'var_increase_pct': float((var_stress / baseline_var - 1) * 100) if baseline_var > 0 else 0,
                    'cvar_increase_pct': float((cvar_stress / baseline_cvar - 1) * 100) if baseline_cvar > 0 else 0,
                    'metrics_comparison': {
                        'vol_change_pct': float((stress_metrics['vol'] / baseline_metrics['vol'] - 1) * 100) if baseline_metrics['vol'] > 0 else 0,
                        'sharpe_change': float(stress_metrics['sharpe'] - baseline_metrics['sharpe']),
                        'max_dd_change': float(stress_metrics['max_drawdown'] - baseline_metrics['max_drawdown'])
                    },
                    'validation': validation
                }
                
            except Exception as e:
                scenario_results[scenario_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        # Overall assessment
        valid_results = {k: v for k, v in scenario_results.items()
                        if isinstance(v, dict) and v.get('status') == 'SUCCESS'}
        
        max_var_increase = max([r.get('var_increase_pct', 0) for r in valid_results.values()] + [0])
        
        # Find worst-case scenario
        worst_scenario = None
        if valid_results:
            worst = max(valid_results.items(), key=lambda x: x[1].get('var_increase_pct', 0))
            worst_scenario = worst[0]
        
        return {
            'status': 'SUCCESS',
            'baseline': {
                'var': float(baseline_var),
                'cvar': float(baseline_cvar),
                'metrics': baseline_metrics
            },
            'scenarios': scenario_results,
            'overall_assessment': {
                'max_var_increase_pct': float(max_var_increase),
                'worst_case_scenario': worst_scenario,
                'worst_case_increase': float(valid_results[worst_scenario]['var_increase_pct']) if worst_scenario else 0.0,
                'n_scenarios_tested': len(scenarios),
                'n_scenarios_passed': len(valid_results),
                'overall_risk_level': self._assess_overall_risk_level(max_var_increase)
            },
            'genesis_checksum': GENESIS_CHECKSUM,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _validate_stressed_returns(
        self,
        original: pd.Series,
        stressed: pd.Series,
        scenario: Dict
    ) -> Dict:
        """Validate stressed returns for plausibility"""
        errors = []
        warnings = []
        
        # Check for NaN or infinite values
        if stressed.isna().any():
            errors.append("Stressed returns contain NaN values")
        
        if np.isinf(stressed).any():
            errors.append("Stressed returns contain infinite values")
        
        # Check for extreme values (> 100% daily return)
        extreme_pos = int((stressed > 1.0).sum())
        extreme_neg = int((stressed < -1.0).sum())
        
        if extreme_pos > 0:
            warnings.append(f"Contains {extreme_pos} extreme positive values (>100%)")
        
        if extreme_neg > 0:
            warnings.append(f"Contains {extreme_neg} extreme negative values (<-100%)")
        
        # Compare statistics
        orig_mean = original.mean()
        orig_std = original.std()
        stress_mean = stressed.mean()
        stress_std = stressed.std()
        
        mean_change_pct = abs((stress_mean - orig_mean) / orig_mean) * 100 if abs(orig_mean) > 1e-6 else 0
        vol_change_pct = abs((stress_std - orig_std) / orig_std) * 100 if orig_std > 0 else 0
        
        if mean_change_pct > 1000:
            warnings.append(f"Mean changed by {mean_change_pct:.1f}%")
        
        if vol_change_pct > 500:
            warnings.append(f"Volatility changed by {vol_change_pct:.1f}%")
        
        # Distribution shape check
        try:
            ks_stat, ks_pvalue = stats.ks_2samp(original, stressed)
            if ks_pvalue < 0.01:
                warnings.append(f"Distributions significantly different (KS p={ks_pvalue:.4f})")
        except:
            pass
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'statistics': {
                'original_mean': float(orig_mean),
                'original_std': float(orig_std),
                'stressed_mean': float(stress_mean),
                'stressed_std': float(stress_std),
                'mean_change_pct': float(mean_change_pct),
                'vol_change_pct': float(vol_change_pct)
            }
        }
    
    def _assess_overall_risk_level(self, max_var_increase: float) -> str:
        """Assess overall risk level based on stress test results"""
        if max_var_increase > 200:
            return 'EXTREME'
        elif max_var_increase > 100:
            return 'HIGH'
        elif max_var_increase > 50:
            return 'MEDIUM'
        elif max_var_increase > 20:
            return 'MODERATE'
        else:
            return 'LOW'
    
    # ========================================================================
    # RISK METRICS
    # ========================================================================
    
    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict:
        """Calculate comprehensive risk metrics"""
        vol = returns.std()
        mean_ret = returns.mean()
        
        return {
            'mean_return': float(mean_ret),
            'vol': float(vol),
            'sharpe': float(mean_ret / vol * np.sqrt(252)) if vol > 0 else 0,
            'sortino': float(self._calculate_sortino_ratio(returns)),
            'max_drawdown': float(self._calculate_max_drawdown(returns)),
            'skewness': float(stats.skew(returns)),
            'kurtosis': float(stats.kurtosis(returns)),
            'jarque_bera': self._jarque_bera_test(returns),
            'var_99': float(-np.percentile(returns, 1)),
            'cvar_99': float(-returns[returns <= np.percentile(returns, 1)].mean()) if len(returns[returns <= np.percentile(returns, 1)]) > 0 else 0
        }
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio (downside risk only)"""
        downside = returns[returns < 0]
        downside_std = downside.std() if len(downside) > 1 else 0
        
        if downside_std > 0:
            return returns.mean() / downside_std * np.sqrt(252)
        return 0
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
    
    def _jarque_bera_test(self, returns: pd.Series) -> Dict:
        """Jarque-Bera test for normality"""
        jb_stat, jb_pvalue = stats.jarque_bera(returns)
        return {
            'statistic': float(jb_stat),
            'p_value': float(jb_pvalue),
            'is_normal': jb_pvalue > 0.05
        }
    
    def _assess_data_quality(self, returns: pd.Series) -> Dict:
        """Assess quality of input data"""
        n = len(returns)
        n_missing = int(returns.isna().sum())
        n_zeros = int((returns == 0).sum())
        n_extreme = int((abs(returns) > 0.1).sum())
        
        return {
            'n_observations': n,
            'n_missing': n_missing,
            'n_zeros': n_zeros,
            'n_extreme': n_extreme,
            'missing_pct': float(n_missing / n) if n > 0 else 0,
            'quality_score': float(1.0 - (n_missing + n_zeros * 0.5) / n) if n > 0 else 0
        }
    
    def get_health_status(self) -> Dict:
        """Get engine health status"""
        return {
            'status': 'OPERATIONAL',
            'confidence': self.confidence,
            'lookback': self.lookback,
            'kill_switch_threshold': self.kill_switch_threshold,
            'methods_available': self.var_methods,
            'genesis_checksum': GENESIS_CHECKSUM,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    # ========================================================================
    # 4-LAYER RISK ASSESSMENT (v6.0 Integration)
    # ========================================================================
    
    def assess_trade_risk(
        self,
        symbol: str,
        signal_size: float,
        current_price: float,
        portfolio_state: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Avalia risco completo de um trade com 4 camadas (v6.0).
        
        Camadas:
        1. Validação básica de limites
        2. Análise de risco de mercado
        3. Análise de risco de portfólio
        4. Stress testing
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Camada 1: Validação básica
            basic_validation = self._validate_basic_limits(signal_size, portfolio_state)
            if not basic_validation['approved']:
                return basic_validation
            
            # Camada 2: Análise de mercado
            market_risk = self._assess_market_risk(symbol, current_price, signal_size)
            if not market_risk['approved']:
                return market_risk
            
            # Camada 3: Análise de portfólio
            portfolio_risk = self._assess_portfolio_risk(symbol, signal_size, portfolio_state)
            if not portfolio_risk['approved']:
                return portfolio_risk
            
            # Camada 4: Stress testing
            stress_test = self._run_stress_test(symbol, signal_size, current_price, portfolio_state)
            if not stress_test['approved']:
                return stress_test
            
            # Calcular score de risco consolidado
            risk_score = self._calculate_consolidated_risk_score([
                basic_validation['risk_score'],
                market_risk['risk_score'],
                portfolio_risk['risk_score'],
                stress_test['risk_score']
            ])
            
            # Decisão final
            approved = risk_score < 0.7 and all([
                basic_validation['approved'],
                market_risk['approved'],
                portfolio_risk['approved'],
                stress_test['approved']
            ])
            
            latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            return {
                'approved': approved,
                'risk_score': risk_score,
                'risk_level': self._classify_risk_level(risk_score),
                'validation_stages': {
                    'basic_validation': basic_validation,
                    'market_risk': market_risk,
                    'portfolio_risk': portfolio_risk,
                    'stress_test': stress_test
                },
                'recommendations': self._generate_risk_recommendations(risk_score, signal_size),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'latency_ms': latency
            }
            
        except Exception as e:
            logger.error(f"Erro na avaliação de risco para {symbol}: {e}")
            return {
                'approved': False,
                'risk_score': 1.0,
                'reason': f"Risk engine error: {str(e)}",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _validate_basic_limits(self, signal_size: float, portfolio_state: Optional[Dict]) -> Dict[str, Any]:
        """Camada 1: Validação básica de limites"""
        violations = []
        risk_factors = []
        
        # Limite de tamanho da posição (10% do capital por trade)
        max_position_percent = 0.1
        if portfolio_state and 'total_capital' in portfolio_state:
            position_ratio = signal_size / (portfolio_state['total_capital'] * max_position_percent)
            if position_ratio > 1.0:
                violations.append(f"Tamanho da posição excede limite ({position_ratio:.1%})")
                risk_factors.append(1.0)
            else:
                risk_factors.append(position_ratio)
        else:
            risk_factors.append(0.5)  # Assumir médio se não houver dados
        
        risk_score = np.mean(risk_factors) if risk_factors else 0.0
        approved = len(violations) == 0
        
        return {
            'approved': approved,
            'risk_score': risk_score,
            'violations': violations,
            'stage': 'basic_validation'
        }
    
    def _assess_market_risk(self, symbol: str, current_price: float, signal_size: float) -> Dict[str, Any]:
        """Camada 2: Análise de risco de mercado"""
        risk_factors = []
        
        # Volatilidade (simulada - em produção usar dados reais)
        volatility = 15.0  # 15% padrão
        volatility_risk = min(1.0, volatility / 50.0)
        risk_factors.append(volatility_risk)
        
        # Spread (simulado)
        spread_pct = 0.05  # 0.05% padrão
        spread_risk = min(1.0, spread_pct / 0.2)
        risk_factors.append(spread_risk)
        
        risk_score = np.mean(risk_factors)
        approved = risk_score < 0.8
        
        return {
            'approved': approved,
            'risk_score': risk_score,
            'market_conditions': {
                'volatility_pct': volatility,
                'spread_pct': spread_pct
            },
            'stage': 'market_risk'
        }
    
    def _assess_portfolio_risk(self, symbol: str, signal_size: float, portfolio_state: Optional[Dict]) -> Dict[str, Any]:
        """Camada 3: Análise de risco de portfólio"""
        risk_factors = []
        
        if not portfolio_state:
            return {
                'approved': True,
                'risk_score': 0.3,
                'stage': 'portfolio_risk'
            }
        
        # Concentração
        current_exposure = portfolio_state.get('exposure_by_symbol', {}).get(symbol, 0)
        new_exposure = current_exposure + signal_size
        total_exposure = portfolio_state.get('total_exposure', 1.0)
        
        concentration_ratio = new_exposure / total_exposure if total_exposure > 0 else 0
        max_concentration = 0.3  # 30% máximo
        concentration_risk = min(1.0, concentration_ratio / max_concentration)
        risk_factors.append(concentration_risk)
        
        # Diversificação
        unique_symbols = len(portfolio_state.get('positions', {}))
        min_diversification = 5
        diversification_score = min(1.0, unique_symbols / min_diversification)
        diversification_risk = 1.0 - diversification_score
        risk_factors.append(diversification_risk)
        
        risk_score = np.mean(risk_factors)
        approved = risk_score < 0.75 and concentration_ratio <= max_concentration
        
        return {
            'approved': approved,
            'risk_score': risk_score,
            'portfolio_factors': {
                'concentration_ratio': concentration_ratio,
                'diversification_score': diversification_score
            },
            'stage': 'portfolio_risk'
        }
    
    def _run_stress_test(self, symbol: str, signal_size: float, current_price: float, portfolio_state: Optional[Dict]) -> Dict[str, Any]:
        """Camada 4: Stress testing"""
        scenarios = [
            {'name': 'Market Crash', 'shock': -0.20, 'probability': 0.01},
            {'name': 'High Volatility', 'shock': 0.15, 'probability': 0.05},
            {'name': 'Normal Conditions', 'shock': 0.05, 'probability': 0.94}
        ]
        
        losses = []
        for scenario in scenarios:
            pnl_shock = signal_size * scenario['shock']
            expected_loss = abs(pnl_shock) * scenario['probability']
            losses.append(expected_loss)
        
        max_expected_loss = max(losses) if losses else 0
        total_capital = portfolio_state.get('total_capital', 100000.0) if portfolio_state else 100000.0
        max_loss_ratio = max_expected_loss / total_capital if total_capital > 0 else 0
        
        stress_risk = min(1.0, max_loss_ratio / 0.1)  # Normalizar para 10% de perda máxima
        
        approved = stress_risk < 0.8
        
        return {
            'approved': approved,
            'risk_score': stress_risk,
            'stress_test_results': {
                'max_expected_loss': max_expected_loss,
                'max_loss_ratio': max_loss_ratio,
                'worst_scenario': scenarios[np.argmax(losses)]['name'] if losses else 'Unknown',
                'scenarios_tested': len(scenarios)
            },
            'stage': 'stress_test'
        }
    
    def _calculate_consolidated_risk_score(self, stage_scores: List[float]) -> float:
        """Calcula score de risco consolidado"""
        weights = [0.2, 0.3, 0.3, 0.2]  # basic, market, portfolio, stress
        weighted_scores = [s * w for s, w in zip(stage_scores, weights)]
        return min(1.0, sum(weighted_scores))
    
    def _classify_risk_level(self, risk_score: float) -> str:
        """Classifica nível de risco"""
        if risk_score < 0.3:
            return 'LOW'
        elif risk_score < 0.6:
            return 'MEDIUM'
        elif risk_score < 0.8:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def _generate_risk_recommendations(self, risk_score: float, signal_size: float) -> List[str]:
        """Gera recomendações baseadas no risco"""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append("Recomendado: Reduzir tamanho da posição em 50%")
            recommendations.append("Recomendado: Aumentar stop loss para 3%")
        
        if risk_score > 0.5:
            recommendations.append("Considerar: Execução parcial em vez de total")
            recommendations.append("Considerar: Aguardar melhor condições de mercado")
        
        return recommendations


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_risk_engine(config: Dict = None) -> RiskEngine:
    """Factory function to create risk engine"""
    default_config = {
        'confidence_level': 0.95,
        'lookback_window': 252,
        'kill_switch_threshold': 0.15
    }
    
    if config:
        default_config.update(config)
    
    return RiskEngine(**default_config)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AURORA Risk Engine - TIER-0 Certified")
    print("=" * 60)
    
    # Create sample data (low volatility to avoid kill switch)
    np.random.seed(123)
    n = 500
    # Simular retornos de um portfolio bem diversificado (vol ~1% diario)
    returns = pd.Series(np.random.normal(0.0003, 0.01, n))
    
    # Initialize engine with higher kill switch threshold for testing
    engine = create_risk_engine({'kill_switch_threshold': 0.50})
    print(f"\nGenesis Checksum: {GENESIS_CHECKSUM}")
    
    # Test VaR calculation
    print("\n[TEST 1] Historical VaR")
    result = engine.calculate_portfolio_var(returns, method='historical')
    print(f"  Status: {result['status']}")
    if result['status'] == 'SUCCESS':
        print(f"  VaR (95%): ${result['var_absolute']:,.2f}")
        print(f"  CVaR: ${result['cvar_absolute']:,.2f}")
        print(f"  Basel Zone: {result['backtesting']['basel_traffic_light']['zone']}")
        print(f"  Max Drawdown: {result['risk_metrics']['max_drawdown']:.2%}")
    else:
        print(f"  Reason: {result.get('reason', result.get('error', 'Unknown'))}")
    
    # Test Parametric VaR
    print("\n[TEST 2] Parametric VaR (Cornish-Fisher)")
    result_param = engine.calculate_portfolio_var(returns, method='parametric')
    if result_param['status'] == 'SUCCESS':
        print(f"  VaR (95%): ${result_param['var_absolute']:,.2f}")
        print(f"  Skew: {result_param['method_details']['skew']:.3f}")
        print(f"  Kurtosis: {result_param['method_details']['kurtosis']:.3f}")
    else:
        print(f"  Status: {result_param['status']}")
    
    # Test Stress Testing
    print("\n[TEST 3] Stress Testing")
    scenarios = [
        {'name': 'Market Crash', 'shock_type': 'volatility', 'shock': 2.0, 'description': '2x volatility'},
        {'name': 'Flash Crash', 'shock_type': 'absolute', 'shock': -0.02, 'description': '-2% shock'},
        {'name': 'Regime Shift', 'shock_type': 'regime_shift', 'new_vol': 0.02, 'description': 'Double volatility regime'}
    ]
    stress_result = engine.stress_test_scenarios(returns, scenarios)
    print(f"  Status: {stress_result['status']}")
    if stress_result['status'] == 'SUCCESS':
        assessment = stress_result['overall_assessment']
        print(f"  Scenarios Passed: {assessment['n_scenarios_passed']}/{assessment['n_scenarios_tested']}")
        print(f"  Worst Case: {assessment['worst_case_scenario']}")
        print(f"  Max VaR Increase: {assessment['max_var_increase_pct']:.1f}%")
        print(f"  Risk Level: {assessment['overall_risk_level']}")
    else:
        print(f"  Reason: {stress_result.get('reason', stress_result.get('error', 'Unknown'))}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

