import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from collections import deque
import logging
from datetime import datetime

# =============================================================================
# OMEGA SUPREME V5.9.0 — TOTAL RECONCILIATION KERNEL (PSA FINAL)
# =============================================================================
# Mandato: Sincronização Absoluta Dados-Relatório | Tier-0 SRE
# =============================================================================

class OmegaParrFEngine:
    def __init__(self, config: Dict = None):
        self.cfg = {
            'hfd_window': 50,          
            'hfd_threshold': 0.82,     
            'hfd_r2_min': 0.85,         
            'poc_window': 100,
            'poc_density_min': 0.045,  
            'z_vol_min': 0.65,         
            'z_price_min': 0.90,       
            'ha_strength_min': 0.35,   
            'weights': {'L0': 50, 'L1': 20, 'L2': 15, 'L3': 15} # L0 Peso Elite
        }
        if config: self.cfg.update(config)
        self.history = {'poc': deque(maxlen=100)}
        self.prev_ha = None

    def _compute_hfd_atomic(self, series: np.ndarray) -> Tuple[float, float]:
        n = len(series)
        k_max = 6
        lk = []
        for k in range(1, k_max + 1):
            lm = []
            for m in range(k):
                idx = np.arange(m, n, k)
                if len(idx) < 2: continue
                norm = (n - 1) / (int((n - 1 - m) / k) * k)
                l_m = np.sum(np.abs(np.diff(series[idx]))) * norm / k
                lm.append(l_m)
            lk.append(np.mean(lm))
        x = np.log(np.arange(1, len(lk) + 1))
        y = np.log(lk)
        slope, _, r_val, _, _ = stats.linregress(x, y)
        hfd = float(np.clip(2.0 + slope, 0.0, 2.0))
        return hfd, r_val**2

    def execute_audit(self, ohlcv: np.ndarray) -> Dict:
        c = ohlcv[:, 3]
        v = ohlcv[:, 4]
        highs, lows, opens = ohlcv[:, 1], ohlcv[:, 2], ohlcv[:, 0]
        tr = np.maximum(highs[1:]-lows[1:], np.maximum(abs(highs[1:]-c[:-1]), abs(lows[1:]-c[:-1])))
        atr = float(np.mean(tr[-14:]))
        
        telemetry = {}
        flags = {'L0': [], 'L1': [], 'L2': [], 'L3': []}
        
        # L0: Fractal
        hfd, r2 = self._compute_hfd_atomic(c[-self.cfg['hfd_window']:])
        l0_ok = (hfd < self.cfg['hfd_threshold']) and (r2 >= self.cfg['hfd_r2_min'])
        if hfd >= self.cfg['hfd_threshold']: flags['L0'].append("HIGH_HFD")
        if r2 < self.cfg['hfd_r2_min']: flags['L0'].append("LOW_R2")
        
        # L1: POC
        hist, edges = np.histogram(c[-self.cfg['poc_window']:], bins=30, weights=v[-self.cfg['poc_window']:])
        poc_p = (edges[np.argmax(hist)] + edges[np.argmax(hist)+1]) / 2.0
        dens = np.max(hist) / (np.sum(v[-self.cfg['poc_window']:]) + 1e-10)
        lag = abs(poc_p - self.history['poc'][-1]) / max(atr, 0.01) if self.history['poc'] else 0.0
        self.history['poc'].append(poc_p)
        l1_ok = (lag < 1.0) and (dens >= self.cfg['poc_density_min'])
        if lag >= 1.0: flags['L1'].append("LAG_SAT")
        if dens < self.cfg['poc_density_min']: flags['L1'].append("LOW_DENS")

        # L2: Vector Flow
        z_p = (c[-1] - np.mean(c[-30:])) / (np.std(c[-30:]) + 1e-10)
        log_v = np.log(np.where(v[-60:] <= 0, 1.0, v[-60:]))
        z_v = (np.log(max(v[-1], 1.0)) - np.mean(log_v)) / (np.std(log_v) + 1e-10)
        l2_ok = (z_v > self.cfg['z_vol_min']) and (abs(z_p) > self.cfg['z_price_min'])
        if z_v <= self.cfg['z_vol_min']: flags['L2'].append("LOW_VOL")
        if abs(z_p) <= self.cfg['z_price_min']: flags['L2'].append("NO_THRUST")

        # L3: Inertia
        ha_c = (opens[-1] + highs[-1] + lows[-1] + c[-1]) / 4.0
        ha_o = (opens[-2] + c[-2]) / 2.0
        ha_str = abs(ha_c - ha_o) / (atr + 1e-10)
        l3_ok = (ha_str > self.cfg['ha_strength_min'])
        if not l3_ok: flags['L3'].append("WEAK_CMD")

        score = sum([self.cfg['weights'][f'L{i}'] if layer_ok else 0 for i, layer_ok in enumerate([l0_ok, l1_ok, l2_ok, l3_ok])])
        launch = (score >= 85) and l0_ok # Threshold Institucional
        
        return {
            'score': score, 'launch': launch, 'atr': atr, 'hfd': hfd, 'r2': r2, 
            'poc': poc_p, 'dens': dens, 'lag': lag, 'z_vol': z_v, 'z_price': z_p, 
            'ha_str': ha_str, 'ha_bias': 1 if ha_c > ha_o else -1,
            'f0': "|".join(flags['L0']), 'f1': "|".join(flags['L1']), 
            'f2': "|".join(flags['L2']), 'f3': "|".join(flags['L3'])
        }
