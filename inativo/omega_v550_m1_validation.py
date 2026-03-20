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
        self.DEBOUNCE = 120
        self.CB_LIMIT = 5
        self.SPREAD_PTS = 25 # Stress: 2.5 pips
        
        self.current_pos = None
        self.last_exit = datetime(2010,1,1)
        self.min_window = []
        self.trades = []
        self.balance = 50000.0 # Starting from equity after the win

    def process(self, ts, price, score, zp, beat=450):
        self.min_window = [t for t in self.min_window if (ts-t).total_seconds() < 60]
        
        if self.current_pos is None:
            if score >= 85: # Filtro conservador ativado
                if (ts - self.last_exit).total_seconds() < self.DEBOUNCE: return
                if len(self.min_window) >= self.CB_LIMIT: return
                
                self.current_pos = {'entry_ts': ts, 'entry_price': price, 'zp': zp}
                self.min_window.append(ts)
        else:
            duration = (ts - self.current_pos['entry_ts']).total_seconds()
            if score < 50:
                if duration < self.HOLD_LOCK_SEC: return
                if abs(zp) > self.Z_GUARD: return
                
                # Close
                pnl = (price - self.current_pos['entry_price']) * 100 # Lot 1.0 approx
                net_pnl = pnl - self.SPREAD_PTS
                self.balance += net_pnl
                self.trades.append({
                    'ts_open': self.current_pos['entry_ts'],
                    'ts_close': ts,
                    'duration': duration,
                    'pnl_net': net_pnl,
                    'z_exit': zp,
                    'score_at_exit': score
                })
                self.last_exit = ts
                self.current_pos = None

def run_cadence_validation():
    m1_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M1.csv"
    df = pd.read_csv(m1_path)
    df['time'] = pd.to_datetime(df['time'])
    
    # Filter for Focal Period 09-11/03/2026
    mask = (df['time'] >= '2026-03-09') & (df['time'] <= '2026-03-11 23:59:59')
    df_period = df.loc[mask].copy()
    
    if df_period.empty:
        print("Data window not found in M1 file.")
        return

    # 1. Generate PARR-F Metrics (Score, Z-Price)
    print("Generating PARR-F Metrics for M1 data...")
    engine_audit = OmegaParrFEngine()
    # We need to provide enough history for the engine
    start_idx = df[df['time'] < '2026-03-09'].index.max() - 300
    df_calc = df.iloc[max(0, start_idx):df_period.index.max()+1].copy()
    
    # run_forensic_audit performs the loop
    audit_results = engine_audit.run_forensic_audit(df_calc)
    # The run_forensic_audit starts at index 210
    # We need to align results with the Focal period
    metrics_df = pd.DataFrame(audit_results)
    metrics_df['time'] = df_calc['time'].iloc[210:].values
    
    # Merge back to focused df
    df_focal = pd.merge(df_period, metrics_df, on='time', how='inner')
    
    # 2. Run V5.5.0 Shield Simulation
    shield = OmegaV550AtomicShield()
    for i, row in df_focal.iterrows():
        shield.process(row['time'], row['close'], row['score_final'], row['z_vol_log'])
        
    # 3. Deliver proof
    df_trades = pd.DataFrame(shield.trades)
    df_trades.to_csv("omega_v550_m1_cadence_telemetry.csv", index=False)
    
    sha_in = hashlib.sha256(open(m1_path, 'rb').read()).hexdigest()
    sha_out = hashlib.sha256(open("omega_v550_m1_cadence_telemetry.csv", 'rb').read()).hexdigest()
    
    print("\n--- CADENCE VALIDATION (09-11/03/2026) ---")
    print(f"INPUT SHA256 (M1): {sha_in}")
    print(f"OUTPUT SHA256 (CSV): {sha_out}")
    print(f"Total Trades: {len(df_trades)}")
    print(f"Churn <= 3s: {len(df_trades[df_trades['duration'] <= 3])}")
    print(f"PnL Net (Simulated): ${df_trades['pnl_net'].sum():.2f}")
    if not df_trades.empty:
        print(f"Avg Duration: {df_trades['duration'].mean():.2f}s")
        print(f"Trades/Day: {len(df_trades)/3:.1f}")

if __name__ == "__main__":
    run_cadence_validation()
