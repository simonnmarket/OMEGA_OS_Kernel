import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime

# =============================================================================
# OMEGA FIDUCIARY AUDIT PSA V5.4.4 — INSTITUTIONAL SRE
# =============================================================================

class FiduciarySimulator:
    def __init__(self, initial_balance=10000.0):
        self.balance = initial_balance
        self.equity = initial_balance
        self.high_watermark = initial_balance
        self.initial_cap = initial_balance
        self.active_pos = None
        self.trades = []
        self.last_retcode = 10009 # Initial MT5 Success OK

    def process_logic(self, audit, price, atr):
        retcode = 0
        if self.active_pos:
            dir = self.active_pos['type']
            # Realistic SL/TP Check
            if (dir == 1 and price <= self.active_pos['sl']) or (dir == -1 and price >= self.active_pos['sl']):
                self._close_position(self.active_pos['sl'], "STOP_LOSS")
                retcode = 10009 # TRADE_RETCODE_DONE
            elif (dir == 1 and price >= self.active_pos['tp']) or (dir == -1 and price <= self.active_pos['tp']):
                self._close_position(self.active_pos['tp'], "TAKE_PROFIT")
                retcode = 10009
            elif audit['score'] < 50: # More conservative exit
                self._close_position(price, "DYNAMIC_EXIT")
                retcode = 10009

        if audit['launch'] and not self.active_pos:
            # Sizing based on risk percentage
            risk_pct = 0.01 
            stop_dist = max(atr * 1.5, 25.0) # Adaptive stop
            lot_size = (self.balance * risk_pct) / (stop_dist * 100)
            
            # Spread simulation (Fixed 2.0 pts for audit)
            exec_price = price + 2.0 if audit['direction'] == 1 else price - 2.0
            
            self.active_pos = {
                'type': audit['direction'],
                'entry': exec_price,
                'sl': exec_price - (audit['direction'] * stop_dist),
                'tp': exec_price + (audit['direction'] * stop_dist * 3.0),
                'lots': max(0.01, round(lot_size, 2))
            }
            retcode = 10009 # Order placed successfully

        pnl_active = self.active_pos['type'] * (price - self.active_pos['entry']) * self.active_pos['lots'] * 100 if self.active_pos else 0.0
        self.equity = self.balance + pnl_active
        if self.equity > self.high_watermark: self.high_watermark = self.equity
        dd = (self.high_watermark - self.equity) / self.high_watermark
        return pnl_active, dd, retcode

    def _close_position(self, exit_price, reason):
        pnl = self.active_pos['type'] * (exit_price - self.active_pos['entry']) * self.active_pos['lots'] * 100
        self.balance += pnl
        self.trades.append(pnl)
        self.active_pos = None

def run_fiduciary_audit():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path): return
    
    df = pd.read_csv(data_path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = FiduciarySimulator()
    ohlcv_full = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    for i in range(150, len(df)):
        window = ohlcv_full[i-150:i+1]
        audit = engine.execute_full_audit(window)
        pnl_active, dd_pct, retcode = sim.process_logic(audit, ohlcv_full[i, 3], audit['atr'])
        
        layers = audit['layers']
        row = {
            'TS': df.iloc[i]['time'], 'PRICE': ohlcv_full[i, 3], 'ATR': audit['atr'],
            'L0_HFD': layers['L0']['hfd'], 'L0_R2': layers['L0']['r2'], 'L0_STABILITY': layers['L0']['stability'],
            'L1_LAG': layers['L1']['lag'], 'L2_ZVOL': layers['L2']['z_vol_log'], 'L3_STR': layers['L3']['strength'],
            'SCORE': audit['score'], 'REGIME': audit['regime'], 'LAUNCH': int(audit['launch']),
            'FLAGS': "|".join(audit['flags']),
            'BALANCE': round(sim.balance, 2), 'EQUITY': round(sim.equity, 2), 'PNL': round(pnl_active, 2),
            'DD_PCT': round(dd_pct * 100, 4), 'POS': 1 if sim.active_pos else 0, 'RETCODE': retcode
        }
        results.append(row)

    res_df = pd.DataFrame(results)
    output_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V544_PSA.csv"
    res_df.to_csv(output_path, index=False)
    
    sha_hash = hashlib.sha256(res_df.to_csv().encode()).hexdigest()
    print(f"✅ AUDITORIA CONCLUÍDA: {output_path}")
    print(f"🔐 SHA256: {sha_hash}")

if __name__ == "__main__":
    run_fiduciary_audit()
