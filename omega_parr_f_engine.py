import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
from datetime import datetime

class OmegaParrFEngine:
    def __init__(self, config: Dict = None):
        self.cfg = {
            'hfd_window': 200,
            'hfd_threshold': 1.45,  # Relaxed slightly to find trends
            'hfd_r2_min': 0.60,     # Relaxed to capture more environments
            'poc_window_base': 100,
            'z_vol_threshold': 1.5,
            'z_price_threshold': 1.5,
            'max_leverage': 5.0
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
            return {'poc': 0.0, 'lag': 0.0, 'conc': 0.0, 'price_vs_poc': 0.0, 'ok': False, 'flag': None}

        current_data = ohlcv[-window:]
        hist, bins = np.histogram(current_data[:, 3], bins=50, weights=current_data[:, 4])
        poc_price = bins[np.argmax(hist)]
        vol_conc = np.max(hist) / (np.sum(current_data[:, 4]) + 1e-10)
        
        price_vs_poc = ohlcv[-1, 3] - poc_price
        
        # We consider aligned if volume is somewhat concentrated
        is_aligned = vol_conc > 0.05
        flag = "L1_LOW_VOL_CONC" if vol_conc <= 0.05 else None
        
        return {'poc': poc_price, 'lag': 0.0, 'conc': vol_conc, 'price_vs_poc': price_vs_poc, 'ok': is_aligned, 'flag': flag}

    def analyze_l2_propulsion(self, closes: np.ndarray, volumes: np.ndarray) -> Dict:
        if len(closes) < 100:
            return {'zp': 0.0, 'zv_log': 0.0, 'ok': False, 'flag': None}
        
        log_vols = np.log(volumes[-100:] + 1e-10)
        z_vol_log = (np.log(volumes[-1] + 1e-10) - np.mean(log_vols)) / (np.std(log_vols) + 1e-10)
        z_price = (closes[-1] - np.mean(closes[-100:])) / (np.std(closes[-100:]) + 1e-10)
        
        is_pumping = abs(z_price) > self.cfg['z_price_threshold'] and z_vol_log > self.cfg['z_vol_threshold']
        flag = "L2_NO_PUMP" if not is_pumping else None
        
        return {'zp': z_price, 'zv_log': z_vol_log, 'ok': is_pumping, 'flag': flag}

    def analyze_l3_avionics(self, ohlcv: np.ndarray) -> Dict:
        if len(ohlcv) < 10:
            return {'strength': 0.0, 'latency': 0, 'dir': 0, 'ok': False, 'flag': "L3_NO_DATA"}
            
        opens = ohlcv[-10:, 0]
        highs = ohlcv[-10:, 1]
        lows = ohlcv[-10:, 2]
        closes = ohlcv[-10:, 3]
        
        ha_c = (opens + highs + lows + closes) / 4.0
        ha_o = np.zeros_like(ha_c)
        ha_o[0] = (opens[0] + closes[0]) / 2.0
        for i in range(1, len(ha_o)):
            ha_o[i] = (ha_o[i-1] + ha_c[i-1]) / 2.0
            
        ha_bias = np.where(ha_c > ha_o, 1, -1)
        
        wick_range = highs[-1] - lows[-1] + 1e-10
        body = abs(ha_c[-1] - ha_o[-1])
        strength = body / wick_range
        
        # Calculate latency: how many consecutive bars has this bias been held?
        current_bias = ha_bias[-1]
        latency = 0
        for b in reversed(ha_bias):
            if b == current_bias:
                latency += 1
            else:
                break
                
        is_ignited = strength > 0.4 and latency <= 5  # Too late if lat >= 5
        flag = "L3_STALE" if latency > 5 else None
        
        return {'strength': strength, 'latency': latency, 'dir': current_bias, 'ok': is_ignited, 'flag': flag}

    def run_forensic_audit(self, df_ohlcv: pd.DataFrame):
        vol_col = 'tick_volume' if 'tick_volume' in df_ohlcv.columns else 'volume'
        ohlcv_array = df_ohlcv[['open', 'high', 'low', 'close', vol_col]].values
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
            l3 = self.analyze_l3_avionics(ohlcv_array[:i])
            
            score = (l0['ok']*25) + (l1['ok']*25) + (l2['ok']*25) + (l3['ok']*25)
            
            # Directional Confluence
            dir_vote = 0
            if l1['price_vs_poc'] > 0: dir_vote += 1
            elif l1['price_vs_poc'] < 0: dir_vote -= 1
            
            if l2['zp'] > 0: dir_vote += 1
            elif l2['zp'] < 0: dir_vote -= 1
            
            if l3['dir'] > 0: dir_vote += 1
            elif l3['dir'] < 0: dir_vote -= 1
            
            signal = 'neutral'
            if score >= 50:
                # Require strong Z-Score thrust to confirm direction
                if dir_vote >= 2 and l2['zp'] > self.cfg['z_price_threshold']:
                    signal = 'buy'
                elif dir_vote <= -2 and l2['zp'] < -self.cfg['z_price_threshold']:
                    signal = 'sell'
            
            metrics = {
                'score_final': score, 
                'signal': signal,
                'dir_vote': dir_vote,
                'hfd_r2': l0['r2'], 
                'hfd_value': l0['hfd'],
                'z_vol_log': l2['zv_log'],
                'z_price': l2['zp'],
                'ha_strength': l3['strength'],
                'latency_bars': l3['latency'],
                'flags': [f for f in [l0['flag'], l1['flag'], l2['flag'], l3['flag']] if f]
            }
            results.append(metrics)
            
        return results

    def execute_audit(self, df_ohlcv: pd.DataFrame):
        return self.run_forensic_audit(df_ohlcv)
