import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from collections import deque
import hashlib
import os
from datetime import datetime

# =============================================================================
# OMEGA SUPREME V5.7.0 — ULTIMATE PSA AUDITOR (FORENSIC CERTIFIED)
# =============================================================================
# Objeto: Homologação Final PSA com Telemetria Atômica Total
# Mandato: SEI por Evento | Flags L0-L3 | MDD HWM | Estatísticas de Calmar
# =============================================================================

class OmegaParrFEngine:
    def __init__(self, config: Dict = None):
        self.cfg = {
            'hfd_window': 50,          
            'hfd_threshold': 0.82,     # Rigoroso para evitar ruído
            'hfd_r2_min': 0.85,         
            'poc_window': 100,
            'poc_density_min': 0.045,  
            'z_vol_min': 0.60,         
            'z_price_min': 0.85,       
            'ha_strength_min': 0.30,   
            'weights': {'L0': 40, 'L1': 20, 'L2': 20, 'L3': 20}
        }
        if config: self.cfg.update(config)
        self.history = {'poc': deque(maxlen=100)}
        self.prev_ha = None

    def _compute_hfd(self, series: np.ndarray) -> Tuple[float, float]:
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
        tr = np.maximum(ohlcv[1:, 1]-ohlcv[1:, 2], np.maximum(abs(ohlcv[1:, 1]-c[:-1]), abs(ohlcv[1:, 2]-c[:-1])))
        atr = float(np.mean(tr[-14:]))
        
        flags = []
        # L0: Fractal
        hfd, r2 = self._compute_hfd(c[-self.cfg['hfd_window']:])
        l0_ok = (hfd < self.cfg['hfd_threshold']) and (r2 >= self.cfg['hfd_r2_min'])
        if hfd >= self.cfg['hfd_threshold']: flags.append("L0_HIGH_HFD")
        if r2 < self.cfg['hfd_r2_min']: flags.append("L0_LOW_R2")
        
        # L1: POC
        hist, edges = np.histogram(ohlcv[-self.cfg['poc_window']:, 3], bins=30, weights=v[-self.cfg['poc_window']:])
        poc_price = (edges[np.argmax(hist)] + edges[np.argmax(hist)+1]) / 2.0
        density = np.max(hist) / (np.sum(v[-self.cfg['poc_window']:]) + 1e-10)
        lag = abs(poc_price - self.history['poc'][-1]) / max(atr, 0.01) if self.history['poc'] else 0.0
        self.history['poc'].append(poc_price)
        l1_ok = (lag < 1.0) and (density > self.cfg['poc_density_min'])
        if lag >= 1.0: flags.append("L1_LAG_SAT")
        if density <= self.cfg['poc_density_min']: flags.append("L1_LOW_DENS")
        
        # L2: V-Flow
        z_price = (c[-1] - np.mean(c[-30:])) / (np.std(c[-30:]) + 1e-10)
        log_vols = np.log(np.where(v[-60:] <= 0, 1.0, v[-60:]))
        z_vol = (np.log(max(v[-1], 1.0)) - np.mean(log_vols)) / (np.std(log_vols) + 1e-10)
        l2_ok = (z_vol > self.cfg['z_vol_min']) and (abs(z_price) > self.cfg['z_price_min'])
        if z_vol <= self.cfg['z_vol_min']: flags.append("L2_LOW_VOL")
        if abs(z_price) <= self.cfg['z_price_min']: flags.append("L2_NO_THRUST")
        
        # L3: Inércia
        ha_c = (ohlcv[-1,0] + ohlcv[-1,1] + ohlcv[-1,2] + ohlcv[-1,3]) / 4.0
        ha_o = (ohlcv[-2,0] + ohlcv[-2,3]) / 2.0
        strength = abs(ha_c - ha_o) / (atr + 1e-10)
        l3_ok = (strength > self.cfg['ha_strength_min'])
        if not l3_ok: flags.append("L3_WEAK_CMD")
        
        score = sum([self.cfg['weights'][f'L{i}'] if ok else 0 for i, ok in enumerate([l0_ok, l1_ok, l2_ok, l3_ok])])
        launch = (score >= 80) and l0_ok
        
        return {
            'score': score, 'launch': launch, 'dir': 1 if ha_c > ha_o else -1, 'atr': atr,
            'hfd': hfd, 'hfd_r2': r2, 'l1_dens': density, 'z_vol': z_vol, 'ha_str': strength, 'flags': "|".join(flags)
        }

class UltimatePSASimulator:
    def __init__(self, cap=10000.0, spread=2.0, slip=0.5):
        self.balance = cap
        self.equity = cap
        self.hwm = cap
        self.cost = spread + slip
        self.pos = None
        self.trade_log = []

    def step(self, audit, price):
        floating = 0
        current_sei = 0.0
        if self.pos:
            floating = self.pos['dir'] * (price - self.pos['entry']) * self.pos['lot'] * 100
            self.pos['max_p'] = max(self.pos['max_p'], price)
            self.pos['min_p'] = min(self.pos['min_p'], price)
            
            # Saídas: SL/TP ou Score Crítico
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl or hit_tp or audit['score'] < 40:
                exit_p = self.pos['sl'] if hit_sl else (self.pos['tp'] if hit_tp else price)
                current_sei = self._close(exit_p)
        
        self.equity = self.balance + floating
        if self.equity > self.hwm: self.hwm = self.equity
        dd_pct = ((self.hwm - self.equity) / (self.hwm + 1e-10)) * 100.0
        
        if audit['launch'] and not self.pos:
            lot = (self.balance * 0.01) / (audit['atr'] * 2.0 * 100)
            lot = max(0.01, round(lot, 2))
            entry = price + (audit['dir'] * self.cost / 100.0)
            self.pos = {
                'dir': audit['dir'], 'entry': entry, 'lot': lot,
                'sl': entry - (audit['dir'] * audit['atr'] * 2.0),
                'tp': entry + (audit['dir'] * audit['atr'] * 4.0),
                'max_p': price, 'min_p': price
            }
            
        return self.balance, self.equity, dd_pct, current_sei

    def _close(self, p):
        pnl = self.pos['dir'] * (p - self.pos['entry']) * self.pos['lot'] * 100
        swing = abs(self.pos['max_p'] - self.pos['min_p'])
        sei = (pnl / (swing * self.pos['lot'] * 100 + 1e-10)) if swing > 0.05 else 0.0
        self.balance += pnl
        self.trade_log.append({'pnl': pnl, 'sei': sei})
        self.pos = None
        return sei

def run_ultimate_audit():
    path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    df = pd.read_csv(path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = UltimatePSASimulator()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    print("🚀 EXECUTANDO AUDITORIA SUPREMA V5.7.0 (PSA TOTAL)...")
    for i in range(150, len(df)):
        audit = engine.execute_audit(ohlcv[i-140:i+1])
        bal, eq, dd, sei_evt = sim.step(audit, ohlcv[i, 3])
        
        results.append({
            'TS': df.iloc[i]['time'], 'SCORE': audit['score'], 'LAUNCH': int(audit['launch']),
            'HFD': round(audit['hfd'], 4), 'L1_DENS': round(audit['l1_dens'], 4),
            'Z_VOL': round(audit['z_vol'], 4), 'HA_STR': round(audit['ha_str'], 4),
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 'DD_PCT': round(dd, 4),
            'SEI_EVENT': round(sei_evt, 4), 'FLAGS': audit['flags'], 'RETCODE': 10009 if audit['launch'] else 0
        })
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V570_FINAL.csv"
    res_df.to_csv(out_path, index=False)
    
    # KPIs FINAIS
    ret = (sim.balance / 10000.0 - 1) * 100
    mdd = res_df['DD_PCT'].max()
    trades = [t['pnl'] for t in sim.trade_log]
    seis = [t['sei'] for t in sim.trade_log if t['sei'] != 0]
    pf = sum([t for t in trades if t > 0]) / abs(sum([t for t in trades if t < 0])) if min(trades, default=0) < 0 else 0
    calmar = ret / mdd if mdd > 0 else 0
    
    print("\n" + "="*60)
    print("📈 CERTIFICADO PSA OMEGA V5.7.0 — FORENSIC TOTAL")
    print("="*60)
    print(f"💰 Retorno Líquido: {ret:+.2f}%")
    print(f"📉 Max Drawdown:    {mdd:.2f}%")
    print(f"📊 Calmar Ratio:    {calmar:.2f}")
    print(f"🎯 Profit Factor:   {pf:.2f} | Trades: {len(trades)}")
    print(f"⚡ SEI Médio (Ev):  {np.mean(seis)*100:.2f}% (Capture Efficiency)")
    print(f"🔐 SHA256: {hashlib.sha256(open(out_path, 'rb').read()).hexdigest()}")
    print("="*60)

if __name__ == "__main__":
    run_ultimate_audit()
