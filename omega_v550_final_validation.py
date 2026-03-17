import pandas as pd
import numpy as np
import hashlib
from datetime import datetime
import os
import sys

# Importar o Kernel de Auditoria Real
sys.path.append(r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND")
from omega_parr_f_engine import OmegaParrFEngine

class OmegaV550AtomicShield:
    def __init__(self):
        self.HOLD_LOCK_SEC = 60
        self.Z_GUARD = 0.5
        self.DEBOUNCE = 120 # 2 MIN
        self.CB_LIMIT = 10 # Permitindo maior cadência focal
        self.SPREAD_PTS = 25 
        
        self.current_pos = None
        self.last_exit = datetime(2010,1,1)
        self.min_window = []
        self.trades = []
        self.balance = 50000.0 

    def process(self, ts, price, score, zp, beat=450):
        self.min_window = [t for t in self.min_window if (ts-t).total_seconds() < 60]
        
        # Entrada
        if self.current_pos is None:
            if score >= 50: # Threshold ajustado para M1
                if (ts - self.last_exit).total_seconds() < self.DEBOUNCE: return
                if len(self.min_window) >= self.CB_LIMIT: return
                
                self.current_pos = {'entry_ts': ts, 'entry_price': price, 'zp': zp, 'score_entry': score}
                self.min_window.append(ts)
        # Saída
        else:
            duration = (ts - self.current_pos['entry_ts']).total_seconds()
            if score < 50:
                # Blindagem: Só sai se passar as travas
                if duration < self.HOLD_LOCK_SEC: return
                if abs(zp) > self.Z_GUARD: return
                
                # Close
                pnl = (price - self.current_pos['entry_price']) * 100 
                net_pnl = pnl - self.SPREAD_PTS
                self.balance += net_pnl
                self.trades.append({
                    'ts_open': self.current_pos['entry_ts'],
                    'ts_close': ts,
                    'duration_s': duration,
                    'pts_net': net_pnl,
                    'price_open': self.current_pos['entry_price'],
                    'price_close': price,
                    'z_exit': zp,
                    'score_at_exit': score,
                    'fr': self.SPREAD_PTS / abs(pnl) if pnl != 0 else 1.0
                })
                self.last_exit = ts
                self.current_pos = None

def run_final_cadence_validation():
    m1_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M1.csv"
    df = pd.read_csv(m1_path)
    df['time'] = pd.to_datetime(df['time'])
    
    # Focal Period 09-11
    df_focal_raw = df[(df['time'] >= '2026-03-09') & (df['time'] <= '2026-03-11 23:59:59')].copy()
    
    # Engine for Score generation
    print("Generating M1 Metrics...")
    engine_audit = OmegaParrFEngine()
    audit_results = engine_audit.run_forensic_audit(df_focal_raw)
    metrics_df = pd.DataFrame(audit_results)
    metrics_df['time'] = df_focal_raw['time'].iloc[210:].values
    df_merged = pd.merge(df_focal_raw, metrics_df, on='time', how='inner')
    
    shield = OmegaV550AtomicShield()
    for i, row in df_merged.iterrows():
        shield.process(row['time'], row['close'], row['score_final'], row['z_vol_log'])
        
    df_trades = pd.DataFrame(shield.trades)
    if df_trades.empty:
        print("No trades triggered. Check thresholds.")
        return

    output_file = "omega_v550_m1_focal_provenance.csv"
    df_trades.to_csv(output_file, index=False)
    
    sha_in = hashlib.sha256(open(m1_path, 'rb').read()).hexdigest()
    sha_out = hashlib.sha256(open(output_file, 'rb').read()).hexdigest()
    
    # Standard performance metrics
    win_rate = len(df_trades[df_trades['pts_net'] > 0]) / len(df_trades)
    cum_pnl = df_trades['pts_net'].cumsum()
    max_equity = cum_pnl.expanding().max()
    max_dd = (max_equity - cum_pnl).max()
    pf = df_trades[df_trades['pts_net'] > 0]['pts_net'].sum() / abs(df_trades[df_trades['pts_net'] < 0]['pts_net'].sum())
    
    print("\n--- FINAL CADENCE EVIDENCE (09-11/03/2026) ---")
    print(f"INPUT SHA256: {sha_in}")
    print(f"OUTPUT SHA256: {sha_out}")
    print(f"Total Trades: {len(df_trades)} (~10/day)")
    print(f"Churn <= 3s: {len(df_trades[df_trades['duration_s'] <= 3])}")
    print(f"PnL Net Points: {df_trades['pts_net'].sum():.1f}")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Max Drawdown: {max_dd:.1f} pts")
    print(f"Win Rate: {win_rate*100:.2f}%")
    print(f"Avg Friction Ratio: {df_trades['fr'].mean():.4f}")

if __name__ == "__main__":
    run_final_cadence_validation()
