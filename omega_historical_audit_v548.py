import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime
from scipy import stats

# =============================================================================
# OMEGA FIDUCIARY AUDIT V5.4.8 — PSA FINAL VALIDATION
# =============================================================================

class SRESimulator:
    """Simulador Fiduciário com custos Reais e métricas PSA."""
    def __init__(self, initial_cap=10000.0, spread=2.0, slippage=0.5):
        self.initial_cap = initial_cap
        self.balance = initial_cap
        self.equity = initial_cap
        self.hwm = initial_cap
        self.cost = (spread + slippage) # Pontos totais de fricção
        self.pos = None 
        self.trade_history = [] # [{'pnl': float, 'sei': float}]
        
    def step(self, audit, price, atr):
        # 1. Update Equity e Drawdown
        floating_pnl = 0
        if self.pos:
            floating_pnl = self.pos['dir'] * (price - self.pos['entry']) * self.pos['lots'] * 100
            # Track Swing Amplitude for SEI
            self.pos['max_p'] = max(self.pos['max_p'], price)
            self.pos['min_p'] = min(self.pos['min_p'], price)
            
        self.equity = self.balance + floating_pnl
        if self.equity > self.hwm: self.hwm = self.equity
        
        # Drawdown: (HWM - Equity) / HWM. Deve ser entre 0 e 1.
        dd = (self.hwm - self.equity) / (self.hwm + 1e-10)
        
        # 2. Gestão de Posição
        if self.pos:
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl: self._close(self.pos['sl'], "SL")
            elif hit_tp: self._close(self.pos['tp'], "TP")
            elif audit['score'] < 40: self._close(price, "DYNAMIC")

        # 3. Lógica de Entrada (LAUNCH)
        if audit['launch'] and not self.pos:
            risk_amt = self.balance * 0.01 
            sl_pts = max(atr * 2.0, 30.0) 
            lots = risk_amt / (sl_pts * 100)
            lots = max(0.01, round(lots, 2))
            
            entry = price + self.cost if audit['direction'] == 1 else price - self.cost
            self.pos = {
                'dir': audit['direction'], 'entry': entry,
                'sl': entry - (audit['direction'] * sl_pts),
                'tp': entry + (audit['direction'] * sl_pts * 3.5),
                'lots': lots, 'max_p': price, 'min_p': price
            }
            
        return self.balance, self.equity, dd

    def _close(self, exit_p, reason):
        raw_diff = self.pos['dir'] * (exit_p - self.pos['entry'])
        pnl = raw_diff * self.pos['lots'] * 100
        
        # SEI: PnL / Amplitude do Move ocorrida durante o trade
        amplitude = (self.pos['max_p'] - self.pos['min_p'])
        sei = (raw_diff / amplitude) if amplitude > 0.1 else 0.0
        
        self.balance += pnl
        self.trade_history.append({'pnl': pnl, 'sei': sei})
        self.pos = None

def execute_audit_v548():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path): return
    
    df = pd.read_csv(data_path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = SRESimulator()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    print("🚀 INICIANDO AUDITORIA FINAL V5.4.8 (PSA COMPLIANT)...")
    for i in range(150, len(df)):
        window = ohlcv[i-140:i+1]
        audit = engine.execute_full_audit(window)
        bal, eq, dd = sim.step(audit, ohlcv[i, 3], audit['atr'])
        
        row = {
            'TS': df.iloc[i]['time'], 'PRICE': ohlcv[i, 3], 'SCORE': audit['score'],
            'LAUNCH': int(audit['launch']), 'HFD': round(audit['layers']['L0']['hfd'], 4),
            'HFD_R2': round(audit['layers']['L0']['r2'], 4),
            'L1_LAG': round(audit['layers']['L1']['lag'], 4),
            'Z_VOL': round(audit['layers']['L2']['z_vol'], 4),
            'HA_STR': round(audit['layers']['L3']['strength'], 4),
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 
            'PNL': round(eq - bal, 2), 'DD_PCT': round(dd * 100, 4),
            'FLAGS': "|".join(audit['flags'])
        }
        results.append(row)
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_HISTORICAL_AUDIT_V548_PSA.csv"
    res_df.to_csv(out_path, index=False)
    
    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    
    # KPI CALCULATION
    trades = [t['pnl'] for t in sim.trade_history]
    seis = [t['sei'] for t in sim.trade_history]
    
    net_ret = ((sim.balance / 10000.0) - 1) * 100
    mdd = res_df['DD_PCT'].max()
    win_rate = (len([t for t in trades if t > 0]) / len(trades) * 100) if trades else 0
    pf = (sum([t for t in trades if t > 0]) / abs(sum([t for t in trades if t < 0]))) if len([t for t in trades if t < 0]) > 0 else 0
    
    # SEI Mean + 95% CI
    sei_mean = np.mean(seis) if seis else 0
    sei_sem = stats.sem(seis) if len(seis) > 1 else 0
    sei_ci = sei_sem * 1.96
    
    print("\n" + "="*60)
    print("📈 CERTIFICADO PSA OMEGA V5.4.8 (FINAL)")
    print("="*60)
    print(f"🔐 SHA256: {sha}")
    print(f"📊 Retorno Líquido: {net_ret:+.2f}%")
    print(f"📉 Max Drawdown:    {mdd:.2f}%")
    print(f"🎯 Win Rate:        {win_rate:.2f}% | Profit Factor: {pf:.2f}")
    print(f"⚡ SEI (Capture):   {sei_mean*100:.2f}% (±{sei_ci*100:.2f}%)")
    print(f"🚀 Lançamentos:     {res_df['LAUNCH'].sum()}")
    print("="*60)

if __name__ == "__main__":
    execute_audit_v548()
