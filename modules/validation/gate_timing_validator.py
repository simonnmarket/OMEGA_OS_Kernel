#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from scipy import stats
from datetime import datetime
from typing import Dict

class GateTimingValidator:
    def __init__(self, target_precision=0.70, min_acceptable_precision=0.60, confidence_level=0.95):
        self.target_p = target_precision
        self.min_p = min_acceptable_precision
        self.z_alpha = stats.norm.ppf((1 + confidence_level) / 2)
        self.confidence_level = confidence_level
    
    def validate(self, observed_precision: float, observed_samples: int) -> Dict:
        p_hat = max(0.01, min(0.99, observed_precision))
        n = max(1, observed_samples)
        se = np.sqrt(p_hat * (1 - p_hat) / n)
        ci_lower = p_hat - self.z_alpha * se
        ci_upper = p_hat + self.z_alpha * se
        z_stat = (p_hat - self.min_p) / se if se > 0 else 0.0
        p_value = 1.0 - stats.norm.cdf(z_stat)
        
        ci_above_threshold = ci_lower > self.min_p
        statistically_significant = p_value < 0.05
        gate_approved = ci_above_threshold and statistically_significant
        
        if gate_approved: rec = 'APPROVE_GATE'
        elif observed_samples < 30: rec = 'NEED_MORE_SAMPLES'
        elif ci_lower <= self.min_p: rec = 'PRECISION_TOO_LOW'
        else: rec = 'EXTEND_VALIDATION'
        
        return {
            'observed_precision': round(p_hat, 4),
            'observed_samples': n,
            'confidence_interval_95': [round(ci_lower, 4), round(ci_upper, 4)],
            'p_value': round(p_value, 6),
            'gate_approved': gate_approved,
            'recommendation': rec,
            'min_samples_for_power_80': self._calculate_required_samples(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_required_samples(self) -> dict:
        delta = self.target_p - self.min_p
        if delta <= 0: return {'samples_per_group': 1000, 'total_samples': 2000, 'warning': 'Delta negativo'}
        z_beta = stats.norm.ppf(0.80)
        n_per_group = ((self.z_alpha + z_beta) ** 2 * (self.target_p*(1-self.target_p) + self.min_p*(1-self.min_p)) / delta**2)
        return {'samples_per_group': int(np.ceil(n_per_group)), 'total_samples': int(np.ceil(n_per_group * 2)), 'power': 0.80}

if __name__ == "__main__":
    v = GateTimingValidator()
    v.validate(0.72, 48)
