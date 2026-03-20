import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime

# =============================================================================
# OMEGA FIDUCIARY AUDIT V5.4.6 — PSA TRANSPARENCY EDITION
# =============================================================================

class SRESimulator:
    def __init__(self, initial_cap=10000.0, spread=2.0):
        self.balance = initial_cap
        self.equity = initial_cap
        self.hwm = initial_cap
        self.spread = spread
        self.pos = None # {'dir': 1/-1, 'entry': float, 'sl': float, 'tp': float, 'lots': float}
        self.trade_log = []
        
    def process_step(self, audit, price, atr):
        # 1. Update Equity
        floating_pnl = 0
        if self.pos:
            floating_pnl = self.pos['dir'] * (price - self.pos['entry']) * self.pos['lots'] * 100
        self.equity = self.balance + floating_pnl
        
        if self.equity > self.hwm: self.hwm = self.equity
        dd = (self.hwm - self.equity) / self.hwm
        
        # 2. Manage Position
        if self.pos:
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl: self._close(self.pos['sl'], "SL")
            elif hit_tp: self._close(self.pos['tp'], "TP")
            elif audit['score'] < 50: self._close(price, "DYNAMIC")

        # 3. New Entry
        if audit['launch'] and not self.pos:
            risk_amt = self.balance * 0.01 # 1% Risk
            sl_pts = max(atr * 2.0, 25.0)
            lots = risk_amt / (sl_pts * 100)
            lots = max(0.01, round(lots, 2))
            
            entry = price + self.spread if audit['direction'] == 1 else price - self.spread
            self.pos = {
                'dir': audit['direction'], 'entry': entry,
                'sl': entry - (audit['direction'] * sl_pts),
                'tp': entry + (audit['direction'] * sl_pts * 3.5), # 1:3.5 RR
                'lots': lots
            }
            
        return self.balance, self.equity, dd

    def _close(self, exit_p, reason):
        pnl = self.pos['dir'] * (exit_p - self.pos['entry']) * self.pos['lots'] * 100
        self.balance += pnl
        self.trade_log.append(pnl)
        self.pos = None

def run_fiduciary_audit():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path):
        print("Data not found.")
        return
    
    df = pd.read_csv(data_path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = SRESimulator()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    print("🚀 INICIANDO AUDITORIA FIDUCIÁRIA V5.4.6...")
    for i in range(150, len(df)):
        window = ohlcv[i-140:i+1]
        audit = engine.execute_full_audit(window)
        bal, eq, dd = sim.process_step(audit, ohlcv[i, 3], audit['atr'])
        
        row = {
            'TS': df.iloc[i]['time'], 'PRICE': ohlcv[i, 3], 'SCORE': audit['score'],
            'LAUNCH': int(audit['launch']), 'HFD': round(audit['layers']['L0']['hfd'], 4),
            'HFD_R2': round(audit['layers']['L0']['r2'], 4),
            'L1_DENSITY': round(audit['layers']['L1']['density'], 4),
            'L2_ZVOL': round(audit['layers']['L2']['z_vol'], 4),
            'L3_STR': round(audit['layers']['L3']['strength'], 4),
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 'PNL': round(eq - bal, 2),
            'DRAWDOWN': round(dd*100, 2), 'FLAGS': "|".join(audit['flags'])
        }
        results.append(row)
        if i % 2500 == 0: print(f"[*] Bar {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V546_FINAL.csv"
    res_df.to_csv(out_path, index=False)
    
    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    
    # Independent KPI Summary
    final_ret = ((sim.balance / 10000.0) - 1) * 100
    trades = np.array(sim.trade_log)
    win_rate = (len(trades[trades > 0]) / len(trades) * 100) if len(trades) > 0 else 0
    pf = (trades[trades > 0].sum() / abs(trades[trades < 0].sum())) if len(trades[trades<0]) > 0 else 0
    
    print("\n" + "="*60)
    print("📊 CERTIFICADO DE AUDITORIA OMEGA V5.4.6")
    print("="*60)
    print(f"📄 Arquivo: {os.path.basename(out_path)}")
    print(f"🔐 SHA256: {sha}")
    print(f"📈 Retorno Total: {final_ret:+.2f}%")
    print(f"📉 Max Drawdown:  {res_df['DRAWDOWN'].max():.2f}%")
    print(f"🎯 Profit Factor: {pf:.2f} | Win Rate: {win_rate:.2f}%")
    print(f"⚡ Eventos:      {res_df['LAUNCH'].sum()}")
    print("="*60)

if __name__ == "__main__":
    run_fiduciary_audit()
