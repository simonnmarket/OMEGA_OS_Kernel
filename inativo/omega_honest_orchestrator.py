import pandas as pd
import numpy as np
import hashlib
import os
from datetime import datetime
from omega_parr_f_engine import OmegaParrFEngine
from cost_oracle_v550 import CostOracle, CostSnapshot

def run_honest_backtest(csv_path, output_name, risk_per_trade=0.10, params=None):
    print(f"🚀 Iniciando Backtest Honesto: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    
    p = {
        'HOLD_LOCK': 120,    # Seconds / Bars proxy
        'Z_GUARD': 0.35,
        'ENTRY_SCORE': 50.0, 
        'EXIT_SCORE': 35.0,
        'DEBOUNCE': 600,     # Seconds
        'SL_PTS': 500,       # 50 pips
        'TP_PTS': 1200       # 120 Pips
    }
    if params: p.update(params)
    
    engine = OmegaParrFEngine()
    engine.cfg['z_price_threshold'] = p.get('Z_PRICE_T', 1.5)
    
    oracle = CostOracle()
    # Cost snapshot based on Hantec specifications
    oracle.set_snapshot(CostSnapshot(
        symbol="XAUUSD", spread_points=25, slippage_points=5,
        commission_per_lot=7, swap_long_per_day=-15, swap_short_per_day=5,
        pip_value=1.0, lot_size=100
    ))
    
    metrics_list = engine.execute_audit(df)
    trades = []
    current_pos = None
    last_exit_time = datetime(2010, 1, 1)
    
    # We delay execution by 210 bars for engine burn-in (HFD and Z-Scores)
    for i in range(210, len(df)):
        m = metrics_list[i-210]
        row = df.iloc[i]
        now, price = row['time'], row['close']
        
        if current_pos is None:
            if m['score_final'] >= p['ENTRY_SCORE'] and (now - last_exit_time).total_seconds() >= p['DEBOUNCE']:
                if m['signal'] == 'buy':
                    current_pos = {'dir': 'buy', 'size': risk_per_trade, 'ts_open': now, 'open_price': price}
                elif m['signal'] == 'sell':
                    current_pos = {'dir': 'sell', 'size': risk_per_trade, 'ts_open': now, 'open_price': price}
        else:
            duration = (now - current_pos['ts_open']).total_seconds()
            
            # Calculate PnL Points based on direction
            if current_pos['dir'] == 'buy':
                raw_pnl_pts = (price - current_pos['open_price']) * 100
            else:
                raw_pnl_pts = (current_pos['open_price'] - price) * 100
                
            should_exit = False
            exit_reason = ""
            
            if raw_pnl_pts >= p['TP_PTS']:
                should_exit, exit_reason = True, "TAKE_PROFIT"
            elif raw_pnl_pts <= -p['SL_PTS']:
                should_exit, exit_reason = True, "STOP_LOSS"
            elif duration >= p['HOLD_LOCK'] and m['score_final'] < p['EXIT_SCORE']:
                # Alpha Ejection: eject if logic reversing strongly
                zp = m['z_price']
                reversing = (current_pos['dir'] == 'buy' and zp < -p['Z_GUARD']) or \
                            (current_pos['dir'] == 'sell' and zp > p['Z_GUARD'])
                if reversing or raw_pnl_pts > 40: # Guarantee minimum cover for average entry costs
                    should_exit, exit_reason = True, "ALPHA_EJECT"
            
            if should_exit:
                costs = oracle.effective_cost("XAUUSD", current_pos['dir'], current_pos['size'], duration/(24*3600))
                pnl_gross = raw_pnl_pts * current_pos['size']
                trades.append({
                    'ts_open': current_pos['ts_open'], 'ts_close': now, 'duration_s': duration,
                    'dir': current_pos['dir'], 'size': current_pos['size'], 'open_price': current_pos['open_price'],
                    'close_price': price, 'pnl_gross': round(pnl_gross, 2),
                    'spread_cost': round(costs['breakdown']['spread'], 2), 'slippage_cost': round(costs['breakdown']['slippage'], 2),
                    'commission_cost': round(costs['breakdown']['commission'], 2), 'swap_cost': round(costs['breakdown']['swap'], 2),
                    'total_cost': round(costs['total_cost'], 2), 'pnl_net': round(pnl_gross - costs['total_cost'], 2),
                    'reason_exit': exit_reason, 'z_price': round(m['z_price'], 2), 'state': 'AUDITED'
                })
                current_pos, last_exit_time = None, now
    
    if len(trades) > 0:
        pd.DataFrame(trades).to_csv(output_name, index=False)
        sha = hashlib.sha256(open(output_name, 'rb').read()).hexdigest()
        print(f"✅ {output_name} | Trades: {len(trades)} | SHA: {sha}")
        
        # Breakdown Buy vs Sell
        buys = sum(1 for t in trades if t['dir'] == 'buy')
        sells = sum(1 for t in trades if t['dir'] == 'sell')
        print(f"   Buy Trades: {buys} | Sell Trades: {sells}")
        return sha
    else:
        print(f"⚠️ {output_name} | Trades: 0 | Sem arquivo gerado")
        return None

if __name__ == "__main__":
    h1_path = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\OHLCV_DATA\XAUUSD\XAUUSD_H1.csv"
    
    # Execução para o Estrutural Histórico com Custos Reais
    if os.path.exists(h1_path):
        run_honest_backtest(h1_path, "REPLAY_HONEST_STRUCTURAL_H1.csv", risk_per_trade=0.03, params={
            'HOLD_LOCK': 14400,  # 4 horas
            'ENTRY_SCORE': 80.0, # Muito restrito
            'EXIT_SCORE': 50.0, 
            'SL_PTS': 2000,      
            'TP_PTS': 8000,      
            'Z_GUARD': 1.0,
            'DEBOUNCE': 86400,   # Max 1 trade day
            'Z_PRICE_T': 2.2     
        })
