import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine

# =============================================================================
# OMEGA SRE RECONCILIATOR V5.9.0 — UNIFIED TRUTH SCRIPT
# =============================================================================

class SRESimulator:
    def __init__(self, cap=10000.0, spr=2.0, slp=0.5):
        self.bal = cap
        self.hwm = cap
        self.cost = (spr + slp) / 100.0 # em pontos de preço
        self.pos = None
        self.trades = []

    def step(self, audit, price):
        floating = 0
        sei_val = 0.0
        if self.pos:
            floating = self.pos['dir'] * (price - self.pos['entry']) * self.pos['lots'] * 100
            self.pos['max_p'] = max(self.pos['max_p'], price)
            self.pos['min_p'] = min(self.pos['min_p'], price)
            
            # Saídas SRE
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl or hit_tp or audit['score'] < 35:
                exit_p = self.pos['sl'] if hit_sl else (self.pos['tp'] if hit_tp else price)
                sei_val = self._close(exit_p)

        equity = self.bal + floating
        if equity > self.hwm: self.hwm = equity
        dd = ((self.hwm - equity) / (self.hwm + 1e-10)) * 100.0
        
        if audit['launch'] and not self.pos:
            sl_pts = max(audit['atr'] * 2.0, 25.0)
            lot = max(0.01, round((self.bal * 0.01) / (sl_pts * 100), 2))
            entry = price + (audit['ha_bias'] * self.cost)
            self.pos = {
                'dir': audit['ha_bias'], 'entry': entry, 'lots': lot,
                'sl': entry - (audit['ha_bias'] * sl_pts),
                'tp': entry + (audit['ha_bias'] * sl_pts * 3.5),
                'max_p': price, 'min_p': price
            }
        return self.bal, equity, dd, sei_val

    def _close(self, p):
        pnl = self.pos['dir'] * (p - self.pos['entry']) * self.pos['lots'] * 100
        swing = abs(self.pos['max_p'] - self.pos['min_p'])
        sei = (abs(p - self.pos['entry']) / swing * 100.0) if swing > 0.1 else 0.0
        self.bal += pnl
        self.trades.append({'pnl': pnl, 'sei': sei})
        self.pos = None
        return sei

def run_reconciliation():
    path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    df = pd.read_csv(path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = SRESimulator()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    print("🚀 RECONCILIANDO DADOS OMEGA V5.9.0 (PSA FINAL)...")
    for i in range(150, len(df)):
        audit = engine.execute_audit(ohlcv[i-140:i+1])
        bal, eq, dd, sei = sim.step(audit, ohlcv[i, 3])
        results.append({
            'TS': df.iloc[i]['time'], 'PRICE': ohlcv[i, 3], 'SCORE': audit['score'], 'LAUNCH': int(audit['launch']),
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 'DD_PCT': round(dd, 4), 'SEI_EVENT': round(sei, 2),
            'HFD': round(audit['hfd'], 4), 'L1_LAG': round(audit['lag'], 4), 'L2_ZVOL': round(audit['z_vol'], 4),
            'F0': audit['f0'], 'F1': audit['f1'], 'F2': audit['f2'], 'F3': audit['f3']
        })
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_RECONCILED_V590.csv"
    res_df.to_csv(out_path, index=False)
    
    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    trades_pnl = [t['pnl'] for t in sim.trades]
    net_ret = (sim.bal / 10000.0 - 1) * 100
    mdd = res_df['DD_PCT'].max()
    pf = sum([p for p in trades_pnl if p > 0]) / abs(sum([p for p in trades_pnl if p < 0])) if min(trades_pnl, default=0) < 0 else 0
    
    print("\n" + "="*60)
    print("📊 CERTIFICADO RECONCILIADO OMEGA V5.9.0 (PSA)")
    print("="*60)
    print(f"💰 Retorno Líquido Final: {net_ret:+.2f}%")
    print(f"📉 Max Drawdown (HWM):    {mdd:.2f}%")
    print(f"🎯 Profit Factor:        {pf:.2f}")
    print(f"⚡ SEI Médio (Evento):   {np.mean([t['sei'] for t in sim.trades if t['sei']>0]):.2f}%")
    print(f"🚀 Trades Totais:        {len(sim.trades)}")
    print(f"🔐 SHA256: {sha}")
    print("="*60)

if __name__ == "__main__":
    run_reconciliation()
