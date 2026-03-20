import pandas as pd
import numpy as np
import hashlib
from datetime import datetime
import os
import sys

# Importar o Kernel de Auditoria Real
sys.path.append(r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND")
from omega_parr_f_engine import OmegaParrFEngine

class NASA_Engine_V550:
    def __init__(self, spread_pts, slippage_pts):
        self.HOLD_LOCK = 60
        self.Z_GUARD = 0.5
        self.DEBOUNCE = 120
        self.CB_LIMIT = 15
        self.SPREAD_PTS = spread_pts
        self.SLIPPAGE_PTS = slippage_pts
        
        self.current_pos = None
        self.last_exit = datetime(2010,1,1)
        self.min_window = []
        self.trades = []
        
        # Stats
        self.total_pnl = 0.0
        self.max_equity = 0.0
        self.drawdown = 0.0
        self.churn_count = 0

    def process(self, ts, price, score, zp):
        self.min_window = [t for t in self.min_window if (ts-t).total_seconds() < 60]
        if self.current_pos is None:
            if score >= 50: 
                if (ts - self.last_exit).total_seconds() < self.DEBOUNCE: return
                if len(self.min_window) >= self.CB_LIMIT: return
                self.current_pos = {'entry_ts': ts, 'entry_price': price, 'zp_entry': zp}
                self.min_window.append(ts)
        else:
            duration = (ts - self.current_pos['entry_ts']).total_seconds()
            if score < 50:
                if duration < self.HOLD_LOCK or abs(zp) > self.Z_GUARD: return
                self.close(ts, price, zp)

    def close(self, ts, price, zp):
        p = self.current_pos
        duration = (ts - p['entry_ts']).total_seconds()
        pts = (price - p['entry_price']) * 100
        net_pts = pts - self.SPREAD_PTS - self.SLIPPAGE_PTS
        
        self.total_pnl += net_pts
        if self.total_pnl > self.max_equity: self.max_equity = self.total_pnl
        dd = self.max_equity - self.total_pnl
        if dd > self.drawdown: self.drawdown = dd
        
        if duration <= 3: self.churn_count += 1
        
        self.trades.append({'net_pts': net_pts, 'duration': duration})
        self.last_exit = ts
        self.current_pos = None

def run_nasa_stress_test():
    m1_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M1.csv"
    df = pd.read_csv(m1_path)
    df['time'] = pd.to_datetime(df['time'])
    df_focal = df[(df['time'] >= '2026-03-09') & (df['time'] <= '2026-03-11 23:59:59')].copy()
    
    engine_audit = OmegaParrFEngine()
    audit_res = engine_audit.run_forensic_audit(df_focal)
    metrics_df = pd.DataFrame(audit_res)
    metrics_df['time'] = df_focal['time'].iloc[210:].values
    data = pd.merge(df_focal, metrics_df, on='time', how='inner')
    
    results = []
    # Matriz: Spread de 2.0 a 4.0 pips
    for spread in [20, 30, 40]:
        for slippage in [5, 15]:
            engine = NASA_Engine_V550(spread, slippage)
            for i, row in data.iterrows():
                engine.process(row['time'], row['close'], row['score_final'], row['z_vol_log'])
            
            pnl = engine.total_pnl
            pf = pd.DataFrame(engine.trades)['net_pts'][pd.DataFrame(engine.trades)['net_pts']>0].sum() / \
                 abs(pd.DataFrame(engine.trades)['net_pts'][pd.DataFrame(engine.trades)['net_pts']<0].sum()) if len(engine.trades) > 0 else 0
            
            results.append({
                'Spread_Pts': spread,
                'Slippage_Pts': slippage,
                'PnL_Net_Pts': pnl,
                'Max_Drawdown_Pts': engine.drawdown,
                'Profit_Factor': pf,
                'Churn_Count': engine.churn_count,
                'Total_Trades': len(engine.trades)
            })
    
    df_res = pd.DataFrame(results)
    target_path = r"C:\OMEGA_PROJETO\Auditoria PARR-F\NASA_STRESS_TEST_V550.csv"
    df_res.to_csv(target_path, index=False)
    
    print("\n--- NASA-LEVEL SENSITIVITY MATRIX ---")
    print(df_res.to_string(index=False))
    print(f"\nReport salvo em: {target_path}")
    print(f"Input Hash: {hashlib.sha256(open(m1_path, 'rb').read()).hexdigest()}")

if __name__ == "__main__":
    run_nasa_stress_test()
