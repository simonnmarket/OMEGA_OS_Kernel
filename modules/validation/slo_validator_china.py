#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from datetime import datetime
from typing import Dict

class RegimeSLOValidatorChinaCouncil:
    def __init__(self, damping_ratio=1.0, min_phase_margin_deg=45.0):
        self.zeta = damping_ratio
        self.min_phase_margin = min_phase_margin_deg
    
    def validate(self, decision_timescale_sec: float, measured_rtt_ms: float) -> Dict:
        rtt_sec = measured_rtt_ms / 1000.0
        omega_required = 4.0 / (self.zeta * decision_timescale_sec)
        omega_achieved = 4.0 / (self.zeta * rtt_sec) if rtt_sec > 0 else float('inf')
        
        if self.zeta < 1.0:
            PM_rad = np.arctan(2 * self.zeta / np.sqrt(np.sqrt(1 + 4*self.zeta**4) - 2*self.zeta**2))
            PM_deg = np.degrees(PM_rad)
        else:
            PM_deg = 90.0
        
        omega_adequate = omega_achieved >= omega_required
        pm_adequate = PM_deg >= self.min_phase_margin
        overall_adequate = omega_adequate and pm_adequate
        
        return {
            'overall_adequate': overall_adequate,
        }
        
    def validate_with_transport_delay(self, decision_timescale_sec: float, measured_rtt_ms: float, transport_delay_ms=50.0) -> dict:
        rtt_sec = measured_rtt_ms / 1000.0
        delay_sec = transport_delay_ms / 1000.0
        omega_c = 4.0 / (self.zeta * rtt_sec) if rtt_sec > 0 else float('inf')
        pm_reduction_deg = np.degrees(omega_c * delay_sec) if omega_c != float('inf') else 0.0
        pm_ideal = 90.0 if self.zeta >= 1.0 else np.degrees(np.arctan(2 * self.zeta / np.sqrt(np.sqrt(1 + 4*self.zeta**4) - 2*self.zeta**2)))
        pm_effective = pm_ideal - pm_reduction_deg
        is_stable = pm_effective > 0.0
        is_robust = pm_effective >= self.min_phase_margin
        return {'is_stable': is_stable, 'is_robust': is_robust}

if __name__ == "__main__":
    v = RegimeSLOValidatorChinaCouncil()
    assert v.validate(2.0, 200.0)['overall_adequate']
