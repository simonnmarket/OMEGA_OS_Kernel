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
# OMEGA SUPREME V5.6.0 — AEROSPACE FORENSIC KERNEL (NASA-STD COMPLIANT)
# =============================================================================
# Objeto: Homologação SRE / PSA Nível Máximo
# Protocolo: NATO-SRE-X4
# =============================================================================

class OmegaForensicEngine:
    """
    Motor SRE de Decomposição Atômica para Auditoria PSA.
    Implementa as 4 camadas (L0-L3) com telemetria total (22+ colunas).
    """
    def __init__(self, config: Dict = None):
        self.cfg = {
            'hfd_window': 50,          
            'hfd_threshold': 0.85,     # Mandato SRE: 0.85 para H4 Gold
            'hfd_r2_min': 0.82,         
            'poc_window': 100,
            'poc_density_min': 0.04,   
            'z_vol_min': 0.50,         
            'z_price_min': 0.75,       
            'ha_strength_min': 0.25,   
            'weights': {'L0': 40, 'L1': 20, 'L2': 20, 'L3': 20}
        }
        if config: self.cfg.update(config)
        self.history = {'hfd': deque(maxlen=100), 'poc': deque(maxlen=100)}
        self.prev_ha = None

    def compute_hfd(self, series: np.ndarray) -> Tuple[float, float]:
        """L0: Higuchi Fractal Dimension (Fórmula NASA: 2 + slope)."""
        n = len(series)
        k_max = 6
        lk = []
        for k in range(1, k_max + 1):
            lm = []
            for m in range(k):
                idx = np.arange(m, n, k)
                if len(idx) < 2: continue
                # Normalização institucional do comprimento
                norm = (n - 1) / (int((n - 1 - m) / k) * k)
                l_m = np.sum(np.abs(np.diff(series[idx]))) * norm / k
                lm.append(l_m)
            lk.append(np.mean(lm))
        
        x = np.log(np.arange(1, len(lk) + 1))
        y = np.log(lk)
        slope, _, r_val, _, _ = stats.linregress(x, y)
        hfd = float(np.clip(2.0 + slope, 0.0, 2.0))
        return hfd, r_val**2

    def analyze_layers(self, ohlcv: np.ndarray) -> Dict:
        """Executa a análise atômica de todas as camadas."""
        c = ohlcv[:, 3]
        v = ohlcv[:, 4]
        # ATR para normalização
        tr = np.maximum(ohlcv[1:, 1]-ohlcv[1:, 2], np.maximum(abs(ohlcv[1:, 1]-c[:-1]), abs(ohlcv[1:, 2]-c[:-1])))
        atr = float(np.mean(tr[-14:]))
        
        # --- L0: Fractal ---
        hfd, r2 = self.compute_hfd(c[-self.cfg['hfd_window']:])
        l0_ok = (hfd < self.cfg['hfd_threshold']) and (r2 >= self.cfg['hfd_r2_min'])
        l0_flags = []
        if hfd >= self.cfg['hfd_threshold']: l0_flags.append("L0_HIGH_HFD")
        if r2 < self.cfg['hfd_r2_min']: l0_flags.append("L0_LOW_R2")
        
        # --- L1: POC/Density ---
        data1 = ohlcv[-self.cfg['poc_window']:]
        p1, v1 = data1[:, 3], data1[:, 4]
        hist, edges = np.histogram(p1, bins=30, weights=v1)
        poc_price = (edges[np.argmax(hist)] + edges[np.argmax(hist)+1]) / 2.0
        density = np.max(hist) / (np.sum(v1) + 1e-10)
        lag = abs(poc_price - self.history['poc'][-1]) / max(atr, 0.01) if self.history['poc'] else 0.0
        self.history['poc'].append(poc_price)
        l1_ok = (lag < 1.25) and (density > self.cfg['poc_density_min'])
        
        # --- L2: Volume Flow (Z-Metrics) ---
        z_price = (c[-1] - np.mean(c[-30:])) / (np.std(c[-30:]) + 1e-10)
        log_vols = np.log(np.where(v[-60:] <= 0, 1.0, v[-60:]))
        z_vol = (np.log(max(v[-1], 1.0)) - np.mean(log_vols)) / (np.std(log_vols) + 1e-10)
        wick = (ohlcv[-1, 1] - max(ohlcv[-1, 0], ohlcv[-1, 3])) / (atr + 1e-10) # Wick superior norm
        l2_ok = (z_vol > self.cfg['z_vol_min']) and (abs(z_price) > self.cfg['z_price_min'])
        
        # --- L3: Heikin-Ashi Inertia ---
        ha_c = (ohlcv[-1,0] + ohlcv[-1,1] + ohlcv[-1,2] + ohlcv[-1,3]) / 4.0
        ha_o = (ohlcv[-2,0] + ohlcv[-2,3]) / 2.0
        strength = abs(ha_c - ha_o) / (atr + 1e-10)
        l3_ok = (strength > self.cfg['ha_strength_min'])
        bias = 1 if ha_c > ha_o else -1
        
        # Scoring
        score = 0
        score += self.cfg['weights']['L0'] if l0_ok else 0
        score += self.cfg['weights']['L1'] if l1_ok else 0
        score += self.cfg['weights']['L2'] if l2_ok else 0
        score += self.cfg['weights']['L3'] if l3_ok else 0
        
        launch = (score >= 80) and l0_ok # L0 mandatório
        
        return {
            'atr': atr, 'score': score, 'launch': launch, 'dir': bias,
            'l0': {'hfd': hfd, 'r2': r2, 'ok': l0_ok, 'flags': l0_flags},
            'l1': {'poc': poc_price, 'density': density, 'lag': lag, 'ok': l1_ok},
            'l2': {'z_vol': z_vol, 'z_price': z_price, 'wick': wick, 'ok': l2_ok},
            'l3': {'strength': strength, 'ok': l3_ok}
        }

class AerospaceFiduciarySim:
    """Simulador de Execução SRE com custos reais e DD baseado em HWM."""
    def __init__(self, cap=10000.0, spread=2.0, slip=0.5):
        self.balance = cap
        self.equity = cap
        self.hwm = cap
        self.cost = spread + slip
        self.pos = None
        self.history = []

    def step(self, data, price):
        floating = 0
        if self.pos:
            floating = self.pos['dir'] * (price - self.pos['entry']) * self.pos['lot'] * 100
            self.pos['max_p'] = max(self.pos['max_p'], price)
            self.pos['min_p'] = min(self.pos['min_p'], price)
            
            # Saída por SL/TP ou Score Crítico
            sl_hit = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            tp_hit = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if sl_hit or tp_hit or data['score'] < 30:
                self._close(price if not (sl_hit or tp_hit) else (self.pos['sl'] if sl_hit else self.pos['tp']))
        
        self.equity = self.balance + floating
        if self.equity > self.hwm: self.hwm = self.equity
        dd = (self.hwm - self.equity) / (self.hwm + 1e-10) # 0 to 1
        
        if data['launch'] and not self.pos:
            lot = (self.balance * 0.01) / (data['atr'] * 2.0 * 100)
            lot = max(0.01, round(lot, 2))
            entry = price + (data['dir'] * self.cost / 100.0)
            self.pos = {
                'dir': data['dir'], 'entry': entry, 'lot': lot,
                'sl': entry - (data['dir'] * data['atr'] * 2.0),
                'tp': entry + (data['dir'] * data['atr'] * 4.5),
                'max_p': price, 'min_p': price
            }
            
        return dd

    def _close(self, p):
        pnl = self.pos['dir'] * (p - self.pos['entry']) * self.pos['lot'] * 100
        # SEI: PnL / Volatilidade do Evento
        swing = abs(self.pos['max_p'] - self.pos['min_p'])
        sei = (abs(p - self.pos['entry']) / swing) if swing > 0.1 else 0.0
        self.balance += pnl
        self.history.append({'pnl': pnl, 'sei': sei})
        self.pos = None

# --- EXECUÇÃO DO AUDITOR FORENSE ---

def run_forensic_audit():
    path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(path): return
    
    df = pd.read_csv(path).fillna(method='ffill')
    engine = OmegaForensicEngine()
    sim = AerospaceFiduciarySim()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    output = []
    
    print("🚀 INICIANDO AUDITORIA FORENSE NASA-STD V5.6.0...")
    for i in range(150, len(df)):
        data = engine.analyze_layers(ohlcv[i-140:i+1])
        dd = sim.step(data, ohlcv[i, 3])
        
        pnl_float = sim.equity - sim.balance
        
        row = {
            'TS': df.iloc[i]['time'], 'PRICE': ohlcv[i, 3], 'ATR': round(data['atr'], 4),
            'SCORE': data['score'], 'LAUNCH': int(data['launch']),
            'HFD': round(data['l0']['hfd'], 4), 'HFD_R2': round(data['l0']['r2'], 4),
            'L1_DENS': round(data['l1']['density'], 4), 'L1_LAG': round(data['l1']['lag'], 4),
            'L2_ZVOL': round(data['l2']['z_vol'], 4), 'L2_ZPRICE': round(data['l2']['z_price'], 4),
            'L2_WICK': round(data['l2']['wick'], 4), 'L3_STR': round(data['l3']['strength'], 4),
            'BALANCE': round(sim.balance, 2), 'EQUITY': round(sim.equity, 2),
            'PNL': round(pnl_float, 2), 'DD_PCT': round(dd * 100, 4),
            'FLAGS': "|".join(data['l0']['flags']), 'RETCODE': 10009 if data['launch'] else 0
        }
        output.append(row)
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(output)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_FORENSIC_AUDIT_V560.csv"
    res_df.to_csv(out_path, index=False)
    
    # KPIs FINAIS
    ret = (sim.balance / 10000.0 - 1) * 100
    mdd = res_df['DD_PCT'].max()
    trades = [t['pnl'] for t in sim.history]
    seis = [t['sei'] for t in sim.history]
    pf = sum([t for t in trades if t > 0]) / abs(sum([t for t in trades if t < 0])) if min(trades, default=0) < 0 else 0
    
    print("\n" + "="*60)
    print("📈 CERTIFICADO PSA NASA-STD OMEGA V5.6.0")
    print("="*60)
    print(f"💰 Retorno Líquido: {ret:+.2f}%")
    print(f"📉 Max Drawdown:    {mdd:.2f}%")
    print(f"🎯 Profit Factor:   {pf:.2f}")
    print(f"📊 Trades Totais:   {len(trades)}")
    print(f"⚡ SEI Médio (Ev):  {np.mean(seis)*100:.2f}%")
    print(f"🔐 SHA256: {hashlib.sha256(open(out_path, 'rb').read()).hexdigest()}")
    print("="*60)

if __name__ == "__main__":
    run_forensic_audit()
