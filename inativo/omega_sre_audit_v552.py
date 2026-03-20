import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime
from scipy import stats

# =============================================================================
# OMEGA SRE AUDITOR V5.5.2 — PSA FINAL CERTIFICATION
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
        
        # DRAWDOWN CORRETO: (HWM - Equity) / HWM * 100
        dd_pct = ((self.hwm - self.equity) / (self.hwm + 1e-10)) * 100.0
        
        if self.pos:
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl: self._close(self.pos['sl'], "SL")
            elif hit_tp: self._close(self.pos['tp'], "TP")
            elif audit['score'] < 30: self._close(price, "DY") # Saída adaptativa

        if audit['launch'] and not self.pos:
            risk_amt = self.balance * 0.01 
            sl_pts = max(atr * 1.5, 25.0) 
            lots = risk_amt / (sl_pts * 100)
            lots = max(0.01, round(lots, 2))
            
            entry = price + self.cost if audit['direction'] == 1 else price - self.cost
            self.pos = {
                'dir': audit['direction'], 'entry': entry,
                'sl': entry - (audit['direction'] * sl_pts),
                'tp': entry + (audit['direction'] * sl_pts * 3.0), 
                'lots': lots, 'max_p': price, 'min_p': price
            }
            
        return self.balance, self.equity, dd_pct

    def _close(self, exit_p, reason):
        raw_diff = self.pos['dir'] * (exit_p - self.pos['entry'])
        pnl = raw_diff * self.pos['lots'] * 100
        # SEI: Pnl / Range do period
        swing = (self.pos['max_p'] - self.pos['min_p'])
        sei = (raw_diff / swing) if swing > 0.1 else 0.0
        self.balance += pnl
        self.trade_history.append({'pnl': pnl, 'sei': sei})
        self.pos = None

def run_audit_v552():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path): return
    
    df = pd.read_csv(data_path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = SRESimulator()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    print("🚀 EXECUTANDO AUDITORIA FINAL V5.5.2 (SRE CERTIFIED)...")
    for i in range(150, len(df)):
        window = ohlcv[i-140:i+1]
        audit = engine.execute_full_audit(window)
        bal, eq, dd = sim.step(audit, ohlcv[i, 3], audit['atr'])
        
        row = {
            'TS': df.iloc[i]['time'], 'SCORE': audit['score'], 'LAUNCH': int(audit['launch']),
            'HFD': round(audit['layers']['L0']['hfd'], 4),
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 
            'PNL': round(eq - bal, 2), 'DD_PCT': round(dd, 4),
            'FLAGS': "|".join(audit['flags'])
        }
        results.append(row)
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V552_PSA.csv"
    res_df.to_csv(out_path, index=False)
    
    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    
    # KPIs DIRETOS
    trades = [t['pnl'] for t in sim.trade_history]
    seis = [t['sei'] for t in sim.trade_history]
    net_ret = ((sim.balance / 10000.0) - 1) * 100
    mdd = res_df['DD_PCT'].max()
    pf = (sum([t for t in trades if t > 0]) / abs(sum([t for t in trades if t < 0]))) if len([t for t in trades if t < 0]) > 0 else 0
    sei_mean = np.mean(seis) if seis else 0
    
    print("\n" + "="*60)
    print("📈 CERTIFICADO DE AUDITORIA OMEGA V5.5.2")
    print("="*60)
    print(f"📄 Arquivo: {os.path.basename(out_path)}")
    print(f"🔐 SHA256: {sha}")
    print(f"💰 Retorno Líquido: {net_ret:+.2f}%")
    print(f"📉 Max Drawdown:    {mdd:.2f}%")
    print(f"🎯 Win Rate:        {(len([t for t in trades if t > 0])/len(trades)*100 if trades else 0):.2f}%")
    print(f"📊 Profit Factor:   {pf:.2f}")
    print(f"⚡ SEI Médio (Ev):  {sei_mean*100:.2f}%")
    print(f"🚀 Trades Totais:   {len(trades)}")
    print("="*60)

if __name__ == "__main__":
    run_audit_v552()
