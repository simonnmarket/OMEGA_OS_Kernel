import pandas as pd
import numpy as np
import hashlib
import os
from datetime import datetime
from omega_parr_f_engine import OmegaParrFEngine
from cost_oracle_v550 import CostOracle, CostSnapshot

def run_rigorous_backtest(csv_path, output_name, initial_equity=10000, risk_per_trade=0.10, params=None):
    print(f"🚀 Iniciando Backtest Rigoroso: {csv_path}")
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    
    p = {
        'HOLD_LOCK': 120,
        'Z_GUARD': 0.35,
        'ENTRY_SCORE': 60.0,
        'EXIT_SCORE': 35.0,
        'DEBOUNCE': 600,
        'SL_PTS': 500,
        'TP_PTS': 1200 
    }
    if params: p.update(params)
    
    engine = OmegaParrFEngine()
    oracle = CostOracle()
    oracle.set_snapshot(CostSnapshot(
        symbol="XAUUSD", spread_points=25, slippage_points=5,
        commission_per_lot=7, swap_long_per_day=-15, swap_short_per_day=5,
        pip_value=1.0, lot_size=100
    ))
    
    metrics_list = engine.execute_audit(df)
    trades = []
    current_pos = None
    last_exit_time = datetime(2010, 1, 1)
    
    for i in range(210, len(df)):
        m = metrics_list[i-210]
        row = df.iloc[i]
        now, price = row['time'], row['close']
        
        if current_pos is None:
            if m['score_final'] >= p['ENTRY_SCORE'] and (now - last_exit_time).total_seconds() >= p['DEBOUNCE']:
                current_pos = {'symbol': 'XAUUSD', 'dir': 'buy', 'size': risk_per_trade, 'ts_open': now, 'open_price': price}
        else:
            duration = (now - current_pos['ts_open']).total_seconds()
            zp = m['z_vol_log']
            raw_pnl_pts = (price - current_pos['open_price']) * 100
            should_exit = False
            exit_reason = ""
            
            if raw_pnl_pts >= p['TP_PTS']:
                should_exit, exit_reason = True, "TAKE_PROFIT"
            elif raw_pnl_pts <= -p['SL_PTS']:
                should_exit, exit_reason = True, "STOP_LOSS"
            elif duration >= p['HOLD_LOCK'] and m['score_final'] < p['EXIT_SCORE']:
                inertia_ok = not (raw_pnl_pts > 0 and abs(zp) > p['Z_GUARD'])
                if inertia_ok:
                    should_exit, exit_reason = True, "ALPHA_EJECT"
            
            if should_exit:
                costs = oracle.effective_cost("XAUUSD", "buy", current_pos['size'], duration/(24*3600))
                pnl_gross = raw_pnl_pts * current_pos['size']
                trades.append({
                    'ts_open': current_pos['ts_open'], 'ts_close': now, 'duration_s': duration,
                    'dir': current_pos['dir'], 'size': current_pos['size'], 'open_price': current_pos['open_price'],
                    'close_price': price, 'pnl_gross': round(pnl_gross, 2),
                    'spread_cost': round(costs['breakdown']['spread'], 2), 'slippage_cost': round(costs['breakdown']['slippage'], 2),
                    'commission_cost': round(costs['breakdown']['commission'], 2), 'swap_cost': round(costs['breakdown']['swap'], 2),
                    'total_cost': round(costs['total_cost'], 2), 'pnl_net': round(pnl_gross - costs['total_cost'], 2),
                    'reason_exit': exit_reason, 'z_price': round(m['z_vol_log'], 2), 'state': 'AUDITED'
                })
                current_pos, last_exit_time = None, now
    
    pd.DataFrame(trades).to_csv(output_name, index=False)
    sha = hashlib.sha256(open(output_name, 'rb').read()).hexdigest()
    print(f"✅ {output_name} | Trades: {len(trades)} | SHA: {sha}")
    return sha

if __name__ == "__main__":
    m1_path = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\OHLCV_DATA\XAUUSD\XAUUSD_M1.csv"
    h1_path = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\OHLCV_DATA\XAUUSD\XAUUSD_H1.csv"
    
    # Focal M1: Aggressive Sniper (TP 1.2 pts)
    if os.path.exists(m1_path):
        run_rigorous_backtest(m1_path, "REPLAY_FOCAL_V550_RIGOROUS.csv", risk_per_trade=0.10, params={
            'HOLD_LOCK': 120, 'ENTRY_SCORE': 62.0, 'EXIT_SCORE': 35.0, 'SL_PTS': 500, 'TP_PTS': 1200
        })
    
    # Structural H1: Ultra selective
    if os.path.exists(h1_path):
        run_rigorous_backtest(h1_path, "REPLAY_STRUCTURAL_V550_RIGOROUS.csv", risk_per_trade=0.01, params={
            'HOLD_LOCK': 3600, 'ENTRY_SCORE': 85.0, 'EXIT_SCORE': 45.0, 'SL_PTS': 1000, 'TP_PTS': 5000
        })
