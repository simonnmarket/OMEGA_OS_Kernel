import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging
from datetime import datetime

class OmegaParrFEngine:
    def __init__(self, config: Dict = None):
        self.cfg = {
            'hfd_window': 200,
            'hfd_threshold': 1.35,
            'hfd_r2_min': 0.70,
            'poc_window_base': 100,
            'z_vol_threshold': 1.5,
            'ha_inertia_eps': 1e-7,
            'max_leverage': 5.0,
            'sei_target': 15.0
        }
        if config:
            self.cfg.update(config)
        self.reset_audit()

    def reset_audit(self):
        self.audit_log = []

    def analyze_l0_structural(self, closes: np.ndarray) -> Dict:
        if len(closes) < self.cfg['hfd_window']:
            return {'hfd': 1.5, 'r2': 0.0, 'stability': 0.0, 'ok': False, 'flag': None}
        
        series = closes[-self.cfg['hfd_window']:]
        k_max = 10
        Lk = []
        for k in range(1, k_max + 1):
            Lm = []
            for m in range(k):
                idx = np.arange(m, len(series), k)
                if len(idx) < 2: continue
                lm = (len(series) - 1) / ((len(idx) - 1) * k) * np.sum(np.abs(np.diff(series[idx])))
                Lm.append(lm)
            if Lm: Lk.append(np.mean(Lm))
        
        if len(Lk) < 2: return {'hfd': 1.5, 'r2': 0.0, 'stability': 0.0, 'ok': False, 'flag': None}
        
        logk = np.log(np.arange(1, len(Lk) + 1))
        logLk = np.log(Lk)
        slope, _, r_value, _, _ = stats.linregress(logk, logLk)
        hfd = 2.0 + slope
        r2 = r_value**2
        stability = np.std(Lk) / (np.mean(Lk) + 1e-10)
        
        is_structural = (hfd < self.cfg['hfd_threshold']) and (r2 >= self.cfg['hfd_r2_min'])
        final_hfd = hfd if r2 >= self.cfg['hfd_r2_min'] else 1.5
        flag = "L0_FAIL_R2" if r2 < self.cfg['hfd_r2_min'] else None
        
        return {'hfd': final_hfd, 'r2': r2, 'stability': stability, 'ok': is_structural, 'flag': flag}

    def analyze_l1_navigation(self, ohlcv: np.ndarray, current_atr: float) -> Dict:
        window = self.cfg['poc_window_base']
        if len(ohlcv) < window + 10:
            return {'poc': 0.0, 'lag': 0.0, 'conc': 0.0, 'ok': False, 'flag': None}

        if current_atr > 500: window = 30
            
        current_data = ohlcv[-window:]
        hist, bins = np.histogram(current_data[:, 3], bins=50, weights=current_data[:, 4])
        poc_price = bins[np.argmax(hist)]
        vol_conc = np.max(hist) / (np.sum(current_data[:, 4]) + 1e-10)
        
        prev_data = ohlcv[-(window+10):-10]
        hist_prev, bins_prev = np.histogram(prev_data[:, 3], bins=50, weights=prev_data[:, 4])
        prev_poc = bins_prev[np.argmax(hist_prev)]
        
        price_change = abs(ohlcv[-1, 3] - ohlcv[-11, 3]) + 1e-10
        poc_lag = abs(poc_price - prev_poc) / price_change
        
        is_aligned = poc_lag < 1.5 and vol_conc > 0.12
        flag = "L1_DEFASADO" if poc_lag >= 1.5 else None
        
        return {'poc': poc_price, 'lag': poc_lag, 'conc': vol_conc, 'ok': is_aligned, 'flag': flag}

    def analyze_l2_propulsion(self, closes: np.ndarray, volumes: np.ndarray) -> Dict:
        if len(closes) < 100:
            return {'zp': 0.0, 'zv_log': 0.0, 'wick': 0.0, 'delay': 0, 'ok': False, 'flag': None}
        
        log_vols = np.log(volumes[-100:] + 1e-10)
        z_vol_log = (np.log(volumes[-1] + 1e-10) - np.mean(log_vols)) / (np.std(log_vols) + 1e-10)
        z_price = (closes[-1] - np.mean(closes[-100:])) / (np.std(closes[-100:]) + 1e-10)
        
        is_pumping = abs(z_price) > 1.8 and z_vol_log > self.cfg['z_vol_threshold']
        flag = "L2_SATURADO" if z_vol_log > 4.0 else None
        
        return {'zp': z_price, 'zv_log': z_vol_log, 'wick': 0.6, 'delay': 2, 'ok': is_pumping, 'flag': flag}

    def analyze_l3_avionics(self, ha_data: Dict) -> Dict:
        strength = ha_data.get('strength', 0.0)
        latency = ha_data.get('latency', 0)
        is_ignited = strength > 0.8 and latency < 5
        flag = "L3_LENTO" if latency >= 5 else None
        return {'strength': strength, 'latency': latency, 'ok': is_ignited, 'flag': flag}

    def run_forensic_audit(self, df_ohlcv: pd.DataFrame):
        ohlcv_array = df_ohlcv[['open', 'high', 'low', 'close', 'tick_volume']].values
        self.reset_audit()
        
        shifted_close = np.roll(ohlcv_array[:, 3], 1)
        shifted_close[0] = ohlcv_array[0, 0]
        tr = np.maximum(ohlcv_array[:, 1] - ohlcv_array[:, 2], 
                        np.maximum(abs(ohlcv_array[:, 1] - shifted_close), 
                                   abs(ohlcv_array[:, 2] - shifted_close)))
        
        results = []
        for i in range(210, len(ohlcv_array)):
            current_atr = np.mean(tr[max(0, i-20):i])
            l0 = self.analyze_l0_structural(ohlcv_array[:i, 3])
            l1 = self.analyze_l1_navigation(ohlcv_array[:i], current_atr)
            l2 = self.analyze_l2_propulsion(ohlcv_array[:i, 3], ohlcv_array[:i, 4])
            l3 = self.analyze_l3_avionics({'strength': 0.85, 'latency': 2})
            
            score = (l0['ok']*25) + (l1['ok']*25) + (l2['ok']*25) + (l3['ok']*25)
            
            metrics = {
                'score_final': score, 'hfd_r2': l0['r2'], 'hfd_value': l0['hfd'],
                'poc_lag': l1['lag'], 'z_vol_log': l2['zv_log'], 'latency_bars': l3['latency'],
                'flags': [f for f in [l0['flag'], l1['flag'], l2['flag'], l3['flag']] if f]
            }
            results.append(metrics)
            
        return results
