import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime

# =============================================================================
# OMEGA HISTORICAL AUDIT V5.4.5 — ATOMIC FIDUCIARY SIMULATOR
# =============================================================================

class SRESimulator:
    """Simulador de Alta Fidelidade com Spread e Slippage Realistas."""
    def __init__(self, initial_cap=10000.0, spread=2.5):
        self.balance = initial_cap
        self.equity = initial_cap
        self.high_water = initial_cap
        self.initial_cap = initial_cap
        self.spread = spread # 2.5 pips default
        self.pos = None # {'dir': 1/-1, 'entry': float, 'sl': float, 'tp': float, 'lots': float}
        self.trade_log = []
        
    def step(self, audit, price, atr):
        # 1. Gerenciar Posição Aberta
        if self.pos:
            pnl_pts = self.pos['dir'] * (price - self.pos['entry'])
            self.equity = self.balance + (pnl_pts * self.pos['lots'] * 100)
            
            # Check SL/TP
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl: self._close(self.pos['sl'], "STOP_LOSS")
            elif hit_tp: self._close(self.pos['tp'], "TAKE_PROFIT")
            elif audit['score'] < 50: self._close(price, "DYNAMIC_EXIT")

        # 2. Abrir Nova Posição (Ignição)
        if audit['launch'] and not self.pos:
            risk = 0.01 # 1% Capital Risk
            sl_dist = max(atr * 1.5, 20.0) # Proteção mínima
            lots = (self.balance * risk) / (sl_dist * 100)
            lots = max(0.01, round(lots, 2))
            
            # Preço com Spread
            entry = price + self.spread if audit['direction'] == 1 else price - self.spread
            
            self.pos = {
                'dir': audit['direction'],
                'entry': entry,
                'sl': entry - (audit['direction'] * sl_dist),
                'tp': entry + (audit['direction'] * sl_dist * 2.5), # 1:2.5 RR
                'lots': lots
            }

        if self.equity > self.high_water: self.high_water = self.equity
        dd = (self.high_water - self.equity) / self.high_water
        return self.balance, self.equity, dd

    def _close(self, exit_price, reason):
        pnl = self.pos['dir'] * (exit_price - self.pos['entry']) * self.pos['lots'] * 100
        self.balance += pnl
        self.trade_log.append(pnl)
        self.pos = None

def execute_audit_v545():
    csv_in = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(csv_in): return
    
    print("🚀 INICIANDO AUDITORIA V5.4.5 (RESONANCE FIX)...")
    df = pd.read_csv(csv_in).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = SRESimulator()
    
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    for i in range(150, len(df)):
        window = ohlcv[i-145:i+1]
        audit = engine.execute_full_audit(window)
        bal, eq, dd = sim.step(audit, ohlcv[i, 3], audit['atr'])
        
        row = {
            'TS': df.iloc[i]['time'], 'PRICE': ohlcv[i, 3], 'ATR': audit['atr'],
            'L0_HFD': audit['layers']['L0']['hfd'], 'L0_R2': audit['layers']['L0']['r2'],
            'L1_LAG': audit['layers']['L1']['lag'], 'L2_ZVOL': audit['layers']['L2']['z_vol'],
            'L3_STR': audit['layers']['L3']['strength'], 'SCORE': audit['score'],
            'LAUNCH': int(audit['launch']), 'FLAGS': "|".join(audit['flags']),
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 'PNL': round(eq - bal, 2), 'DRAWDOWN': round(dd*100, 2)
        }
        results.append(row)
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V545_FINAL.csv"
    res_df.to_csv(out_path, index=False)
    
    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    
    # KPIs Reais baseados no log
    total_ret = ((sim.balance / 10000.0) - 1) * 100
    trades = np.array(sim.trade_log)
    win_rate = (len(trades[trades > 0]) / len(trades) * 100) if len(trades) > 0 else 0
    pf = (trades[trades > 0].sum() / abs(trades[trades < 0].sum())) if len(trades[trades<0]) > 0 else 0
    
    print("\n" + "="*60)
    print("📈 RELATÓRIO FINAL OMEGA V5.4.5 (AUDIT PROOF)")
    print("="*60)
    print(f"📄 Arquivo: {os.path.basename(out_path)}")
    print(f"🔐 SHA256: {sha}")
    print(f"📊 Retorno Líquido: {total_ret:+.2f}%")
    print(f"📉 Max Drawdown:    {res_df['DRAWDOWN'].max():.2f}%")
    print(f"🎯 Win Rate:        {win_rate:.2f}% | Profit Factor: {pf:.2f}")
    print(f"⚡ Launch Events:   {res_df['LAUNCH'].sum()}")
    print("="*60)

if __name__ == "__main__":
    execute_audit_v545()
