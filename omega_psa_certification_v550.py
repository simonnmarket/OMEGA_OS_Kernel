import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime
from scipy import stats

# =============================================================================
# OMEGA FIDUCIARY AUDITOR V5.5.0 — PSA CERTIFICATION SCRIPT
# =============================================================================

class SRESimulator:
    def __init__(self, initial_cap=10000.0, spread=2.0, slippage=0.5):
        self.initial_cap = initial_cap
        self.balance = initial_cap
        self.equity = initial_cap
        self.hwm = initial_cap
        self.cost = (spread + slippage) 
        self.pos = None 
        self.trade_history = [] 
        
    def step(self, audit, price, atr):
        floating_pnl = 0
        if self.pos:
            floating_pnl = self.pos['dir'] * (price - self.pos['entry']) * self.pos['lots'] * 100
            self.pos['max_p'] = max(self.pos['max_p'], price)
            self.pos['min_p'] = min(self.pos['min_p'], price)
            
        self.equity = self.balance + floating_pnl
        if self.equity > self.hwm: self.hwm = self.equity
        
        # DRAWDOWN CORRETO: (HWM - Equity) / HWM
        dd = (self.hwm - self.equity) / (self.hwm + 1e-10)
        
        if self.pos:
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl: self._close(self.pos['sl'], "SL")
            elif hit_tp: self._close(self.pos['tp'], "TP")
            elif audit['score'] < 40: self._close(price, "DYNAMIC")

        if audit['launch'] and not self.pos:
            risk_amt = self.balance * 0.01 
            sl_pts = max(atr * 2.0, 30.0) 
            lots = risk_amt / (sl_pts * 100)
            lots = max(0.01, round(lots, 2))
            
            entry = price + self.cost if audit['direction'] == 1 else price - self.cost
            self.pos = {
                'dir': audit['direction'], 'entry': entry,
                'sl': entry - (audit['direction'] * sl_pts),
                'tp': entry + (audit['direction'] * sl_pts * 3.5), # RR 1:3.5
                'lots': lots, 'max_p': price, 'min_p': price
            }
            
        return self.balance, self.equity, dd

    def _close(self, exit_p, reason):
        raw_diff = self.pos['dir'] * (exit_p - self.pos['entry'])
        pnl = raw_diff * self.pos['lots'] * 100
        
        # SEI CORRETO POR EVENTO: Pnl Realizado / Amplitude de Swing Capturável
        swing_range = (self.pos['max_p'] - self.pos['min_p'])
        sei = (raw_diff / swing_range) if swing_range > 0.1 else 0.0
        
        self.balance += pnl
        self.trade_history.append({'pnl': pnl, 'sei': sei})
        self.pos = None

def run_certification_v550():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path): return
    
    df = pd.read_csv(data_path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = SRESimulator()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    print("🚀 EXECUTANDO AUDITORIA V5.5.0 (PSA CERTIFICATION)...")
    for i in range(150, len(df)):
        window = ohlcv[i-140:i+1]
        audit = engine.execute_full_audit(window)
        bal, eq, dd = sim.step(audit, ohlcv[i, 3], audit['atr'])
        
        row = {
            'TS': df.iloc[i]['time'], 'SCORE': audit['score'], 'LAUNCH': int(audit['launch']),
            'HFD': round(audit['layers']['L0']['hfd'], 4),
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 
            'PNL': round(eq - bal, 2), 'DD_PCT': round(dd * 100, 4),
            'FLAGS': "|".join(audit['flags'])
        }
        results.append(row)
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V550_PSA.csv"
    res_df.to_csv(out_path, index=False)
    
    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    
    # KPIs DIRETOS DO CSV
    trades = [t['pnl'] for t in sim.trade_history]
    seis = [t['sei'] for t in sim.trade_history]
    net_ret = ((sim.balance / 10000.0) - 1) * 100
    mdd = res_df['DD_PCT'].max()
    win_rate = (len([t for t in trades if t > 0]) / len(trades) * 100) if trades else 0
    pf = (sum([t for t in trades if t > 0]) / abs(sum([t for t in trades if t < 0]))) if len([t for t in trades if t < 0]) > 0 else 0
    sei_mean = np.mean(seis) if seis else 0
    
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE CERTIFICAÇÃO OMEGA V5.5.0")
    print("="*60)
    print(f"📄 Arquivo: {os.path.basename(out_path)}")
    print(f"🔐 SHA256: {sha}")
    print(f"📈 Retorno Líquido: {net_ret:+.2f}%")
    print(f"📉 Max Drawdown:    {mdd:.2f}%")
    print(f"🎯 Profit Factor:   {pf:.2f} | Win Rate: {win_rate:.2f}%")
    print(f"⚡ SEI Médio (Evento): {sei_mean*100:.2f}%")
    print(f"🚀 Lançamentos (Total): {res_df['LAUNCH'].sum()}")
    print("="*60)

if __name__ == "__main__":
    run_certification_v550()
