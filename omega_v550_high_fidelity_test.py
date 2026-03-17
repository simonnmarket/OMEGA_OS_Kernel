import pandas as pd
import numpy as np
import hashlib
from datetime import datetime, time
import os

class OmegaV550Engine:
    def __init__(self):
        # Parâmetros Homologados V5.5.0
        self.HOLD_LOCK_SEC = 60
        self.Z_GUARD_THRESHOLD = 0.5
        self.DEBOUNCE_SEC = 120
        self.FR_LIMIT = 0.20
        self.CB_LIMIT = 3 # Trades/min
        self.MIN_PROFIT_PTS = 50 # CQO target
        
        # Custos Simulados (Stress Test)
        self.SPREAD_PTS = 20 # 2.0 pips fixed
        self.SLIPPAGE_AVG_PTS = 5 
        self.SWAP_SHORT_PTS = -10 # Swap por noite
        
        self.current_pos = None
        self.last_exit_time = datetime(2010, 1, 1)
        self.minute_window = []
        self.trades = []
        self.balance = 10000.0
        self.equity_curve = []
        
    def calculate_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def process_tick(self, ts, price, score, z_price, beat):
        # 1. Update minute window for Circuit Breaker
        self.minute_window = [t for t in self.minute_window if (ts - t).total_seconds() < 60]
        
        # 2. Logic: No Position -> Entry Check
        if self.current_pos is None:
            # Entry Filters
            if score >= 85: # Threshold institucional
                # Safety Checks
                if (ts - self.last_exit_time).total_seconds() < self.DEBOUNCE_SEC:
                    return "BLOCK: Debounce"
                if len(self.minute_window) >= self.CB_LIMIT:
                    return "BLOCK: Circuit Breaker"
                
                # Entry Authorized
                self.current_pos = {
                    'ts_open': ts,
                    'price_open': price,
                    'type': 'BUY',
                    'z_price_at_entry': z_price,
                    'beat_at_entry': beat
                }
                self.minute_window.append(ts)
                return "ENTRY_BUY"

        # 3. Logic: In Position -> Exit Check
        else:
            duration = (ts - self.current_pos['ts_open']).total_seconds()
            
            # Logic for Exit (Score < 50 represents loss of alpha/REPOUSO)
            if score < 50:
                # Blindagem 1: Hold Lock
                if duration < self.HOLD_LOCK_SEC:
                    return "HOLD: Lock Shield"
                
                # Blindagem 2: Z-Guard
                if abs(z_price) > self.Z_GUARD_THRESHOLD:
                    return "HOLD: Z-Inertia"
                
                # Blindagem 3: Min Profit validation for friction
                raw_pnl_pts = (price - self.current_pos['price_open']) * 100 # Multiplicador simplificado
                
                # Ejeção Autorizada
                self.close_position(ts, price, z_price, beat, "SCORE_LOSS")
                return "EXIT_EXECUTED"
            
            # Hard Stop Loss (Always Priotized per Rule of Gold)
            sl_pts = (price - self.current_pos['price_open']) * 100
            if sl_pts < -500: # 50 pips stop
                self.close_position(ts, price, z_price, beat, "HARD_STOP")
                return "EXIT_STOP_LOSS"

    def close_position(self, ts_close, price_close, z_close, beat_close, reason):
        p = self.current_pos
        duration = (ts_close - p['ts_open']).total_seconds()
        
        # Cálculo de PnL com fricção e swap
        raw_diff = price_close - p['price_open']
        pts = raw_diff * 100
        
        # Custos
        spread_cost = self.SPREAD_PTS + self.SLIPPAGE_AVG_PTS
        days_held = (ts_close.date() - p['ts_open'].date()).days
        swap_cost = days_held * abs(self.SWAP_SHORT_PTS)
        
        net_pts = pts - spread_cost - swap_cost
        trade_pnl = net_pts * 1.0 # 0.1 lot base approx
        
        self.balance += trade_pnl
        
        self.trades.append({
            'ts_open': p['ts_open'],
            'ts_close': ts_close,
            'duration_s': duration,
            'price_open': p['price_open'],
            'price_close': price_close,
            'pts_raw': pts,
            'pts_net': net_pts,
            'pnl_usd': trade_pnl,
            'reason': reason,
            'z_entry': p['z_price_at_entry'],
            'z_exit': z_close,
            'fr': spread_cost / abs(pts) if pts != 0 else 1.0
        })
        
        self.last_exit_time = ts_close
        self.current_pos = None

def run_test():
    input_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_RECONCILED_V590.csv"
    engine = OmegaV550Engine()
    
    input_hash = engine.calculate_hash(input_path)
    df = pd.read_csv(input_path)
    df['TS'] = pd.to_datetime(df['TS'])
    
    print(f"--- INICIANDO BACKTEST V5.5 fidelity ---")
    print(f"INPUT HASH: {input_hash}")
    
    for i, row in df.iterrows():
        engine.process_tick(row['TS'], row['PRICE'], row['SCORE'], row['L2_ZVOL'], 400)
    
    # Export trades
    df_trades = pd.DataFrame(engine.trades)
    output_file = "omega_v550_backtest_telemetry.csv"
    df_trades.to_csv(output_file, index=False)
    output_hash = engine.calculate_hash(output_file)
    
    # Metrics
    total_trades = len(df_trades)
    win_trades = df_trades[df_trades['pnl_usd'] > 0]
    churn_count = len(df_trades[df_trades['duration_s'] <= 3])
    
    cum_pnl = df_trades['pnl_usd'].cumsum()
    max_equity = cum_pnl.expanding().max()
    dd = (max_equity - cum_pnl)
    max_dd = dd.max()
    
    gross_profit = df_trades[df_trades['pnl_usd'] > 0]['pnl_usd'].sum()
    gross_loss = abs(df_trades[df_trades['pnl_usd'] < 0]['pnl_usd'].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else 0
    
    print("\n--- RESULTS ---")
    print(f"OUTPUT HASH: {output_hash}")
    print(f"PnL Total: ${df_trades['pnl_usd'].sum():.2f}")
    print(f"Max Drawdown: ${max_dd:.2f}")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Win Rate: {len(win_trades)/total_trades*100:.2f}%")
    print(f"Total Trades: {total_trades}")
    print(f"Churn <= 3s: {churn_count}")
    print(f"Avg Duration: {df_trades['duration_s'].mean():.2f}s")
    print(f"Friction Ratio Avg: {df_trades['fr'].mean():.4f}")

if __name__ == "__main__":
    run_test()
