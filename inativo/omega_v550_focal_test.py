import pandas as pd
import numpy as np
import hashlib
from datetime import datetime

class OmegaV550Engine:
    def __init__(self):
        self.HOLD_LOCK_SEC = 60
        self.Z_GUARD_THRESHOLD = 0.5
        self.DEBOUNCE_SEC = 120
        self.CB_LIMIT = 5 # Aumentado para cadência real de 2026
        self.SPREAD_PTS = 20
        self.current_pos = None
        self.last_exit_time = datetime(2010, 1, 1)
        self.minute_window = []
        self.trades = []
        self.balance = 0.0

    def process_tick(self, ts, price, score, z_price):
        self.minute_window = [t for t in self.minute_window if (ts - t).total_seconds() < 60]
        if self.current_pos is None:
            # Score de entrada reduzido para simular agressividade manual (80 vs 85)
            if score >= 80:
                if (ts - self.last_exit_time).total_seconds() < self.DEBOUNCE_SEC: return
                if len(self.minute_window) >= self.CB_LIMIT: return
                self.current_pos = {'ts_open': ts, 'price_open': price}
                self.minute_window.append(ts)
        else:
            duration = (ts - self.current_pos['ts_open']).total_seconds()
            # Saída mais sensível para scalping
            if score < 60:
                if duration < self.HOLD_LOCK_SEC: return
                if abs(z_price) > self.Z_GUARD_THRESHOLD: return
                pnl = (price - self.current_pos['price_open']) * 1000 # Multiplicador lote maior
                self.balance += (pnl - self.SPREAD_PTS*10)
                self.trades.append({'ts_open': self.current_pos['ts_open'], 'ts_close': ts, 'duration': duration, 'pnl': pnl})
                self.last_exit_time = ts
                self.current_pos = None

def run_focal():
    input_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_RECONCILED_V590.csv"
    df = pd.read_csv(input_path)
    df['TS'] = pd.to_datetime(df['TS'])
    mask = (df['TS'] >= '2026-03-09') & (df['TS'] <= '2026-03-11 23:59:59')
    df_focal = df.loc[mask]
    
    engine = OmegaV550Engine()
    for i, row in df_focal.iterrows():
        engine.process_tick(row['TS'], row['PRICE'], row['SCORE'], row['L2_ZVOL'])
        
    df_trades = pd.DataFrame(engine.trades)
    print(f"--- FOCAL TEST (09-11/03/2026) ---")
    print(f"PnL Estimado (Lote Escalonado): ${engine.balance:.2f}")
    print(f"Total Trades: {len(df_trades)}")
    print(f"Churn <= 3s: {len(df_trades[df_trades['duration'] <= 3])}")
    if len(df_trades) > 0:
        print(f"Avg Duration: {df_trades['duration'].mean():.2f}s")
    
if __name__ == "__main__":
    run_focal()
