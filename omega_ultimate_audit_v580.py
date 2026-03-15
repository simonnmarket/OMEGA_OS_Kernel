import pandas as pd
import numpy as np
import os
import hashlib
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime
from scipy import stats

# =============================================================================
# OMEGA SRE ULTIMATE AUDITOR V5.8.0 — PSA FINAL HOMOLOGATION
# =============================================================================

class SREAerospaceSim:
    def __init__(self, cap=10000.0, spread=2.0, slip=0.5):
        self.balance = cap
        self.initial_balance = cap
        self.equity = cap
        self.hwm = cap
        self.cost = (spread + slip) # pips/points direct cost
        self.pos = None
        self.log = []

    def handle(self, audit, price):
        current_sei = 0.0
        if self.pos:
            # Pnl based on floating points
            floating_pnl = self.pos['dir'] * (price - self.pos['entry']) * self.pos['lots'] * 100
            self.equity = self.balance + floating_pnl
            
            # Tracking for SEI
            self.pos['max_swing_p'] = max(self.pos['max_swing_p'], price)
            self.pos['min_swing_p'] = min(self.pos['min_swing_p'], price)
            
            # Logic for Exits
            hit_sl = (self.pos['dir'] == 1 and price <= self.pos['sl']) or (self.pos['dir'] == -1 and price >= self.pos['sl'])
            hit_tp = (self.pos['dir'] == 1 and price >= self.pos['tp']) or (self.pos['dir'] == -1 and price <= self.pos['tp'])
            
            if hit_sl or hit_tp or audit['score'] < 30:
                exit_price = self.pos['sl'] if hit_sl else (self.pos['tp'] if hit_tp else price)
                current_sei = self._exit_trade(exit_price)
        else:
            self.equity = self.balance
            
        if self.equity > self.hwm: self.hwm = self.equity
        
        # NASA STANDARD DRAWDOWN: (HWM - Equity)/HWM
        dd_pct = ((self.hwm - self.equity) / (self.hwm + 1e-10)) * 100.0
        
        # New Entry
        if audit['launch'] and not self.pos:
            risk = self.balance * 0.01 
            sl_pts = max(audit['atr'] * 2.0, 25.0)
            lot = max(0.01, round(risk / (sl_pts * 100), 2))
            
            # Entry with Cost (Spread/Slippage)
            entry = price + (audit['ha_bias'] * self.cost / 100.0)
            self.pos = {
                'dir': audit['ha_bias'], 'entry': entry, 'lots': lot,
                'sl': entry - (audit['ha_bias'] * sl_pts),
                'tp': entry + (audit['ha_bias'] * sl_pts * 4.0),
                'max_swing_p': price, 'min_swing_p': price
            }
            
        return self.balance, self.equity, dd_pct, current_sei

    def _exit_trade(self, out_p):
        pnl = self.pos['dir'] * (out_p - self.pos['entry']) * self.pos['lots'] * 100
        
        # SEI: Captura de Swing (%) = Realized Diff / Total Swing Amplitude
        swing_range = abs(self.pos['max_swing_p'] - self.pos['min_swing_p'])
        capt_diff = abs(out_p - self.pos['entry'])
        sei = (capt_diff / swing_range * 100.0) if swing_range > 0.1 else 0.0
        
        self.balance += pnl
        self.log.append({'pnl': pnl, 'sei': sei})
        self.pos = None
        return sei

def run_auditoria_psa_v580():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path): return
    
    df = pd.read_csv(data_path).fillna(method='ffill')
    engine = OmegaParrFEngine()
    sim = SREAerospaceSim()
    ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    results = []
    
    print("🚀 EXECUTANDO AUDITORIA FINAL NASA-STD V5.8.0...")
    for i in range(150, len(df)):
        audit = engine.execute_audit(ohlcv[i-140:i+1])
        bal, eq, dd, sei_v = sim.handle(audit, ohlcv[i, 3])
        
        results.append({
            'TS': df.iloc[i]['time'], 'PRICE': ohlcv[i,3], 'ATR': round(audit['atr'], 4),
            'SCORE': audit['score'], 'LAUNCH': int(audit['launch']),
            'HFD': round(audit['hfd'], 4), 'HFD_R2': round(audit['hfd_r2'], 4),
            'L1_POC': round(audit['poc'], 2), 'L1_DENS': round(audit['l1_dens'], 4), 'L1_LAG': round(audit['l1_lag'], 4),
            'L2_ZVOL': round(audit['z_vol'], 4), 'L2_ZPRICE': round(audit['z_price'], 4), 'L2_WICK': round(audit['wick_norm'], 4),
            'L3_STR': round(audit['ha_str'], 4), 'L3_BIAS': audit['ha_bias'],
            'BALANCE': round(bal, 2), 'EQUITY': round(eq, 2), 'PNL': round(eq-bal, 2), 
            'DD_PCT': round(dd, 4), 'SEI_EVENT': round(sei_v, 2),
            'L0_FLAGS': audit['flags_l0'], 'L1_FLAGS': audit['flags_l1'],
            'L2_FLAGS': audit['flags_l2'], 'L3_FLAGS': audit['flags_l3'],
            'RETCODE': 10009 if audit['launch'] else 0
        })
        if i % 2500 == 0: print(f"[*] Progresso: {i}/{len(df)}...")

    res_df = pd.DataFrame(results)
    out_dir = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "FULL_HISTORICAL_AUDIT_V580_FINAL.csv")
    res_df.to_csv(out_path, index=False)
    
    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    
    # KPIs DE ELITE
    pnl_trades = [t['pnl'] for t in sim.log]
    sei_trades = [t['sei'] for t in sim.log if t['sei'] > 0]
    net_ret = ((sim.balance / 10000.0) - 1) * 100
    mdd = res_df['DD_PCT'].max()
    pf = sum([p for p in pnl_trades if p > 0]) / abs(sum([p for p in pnl_trades if p < 0])) if min(pnl_trades, default=0) < 0 else 0
    calmar = net_ret / mdd if mdd > 0 else 0
    
    # Sharpe Simples (H4 barras)
    returns = res_df['PNL'].diff().fillna(0)
    sharpe = returns.mean() / (returns.std() + 1e-10) * np.sqrt(9850/4.5) # Anualizado aprox.

    print("\n" + "="*60)
    print("📈 CERTIFICADO PSA NASA-STD OMEGA V5.8.0")
    print("="*60)
    print(f"📊 Retorno Líquido: {net_ret:+.2f}%")
    print(f"📉 Max Drawdown:    {mdd:.2f}% (HWM Normalized)")
    print(f"⚖️ Sharpe Ratio:    {sharpe:.2f} | Calmar: {calmar:.2f}")
    print(f"🎯 Profit Factor:   {pf:.2f} | Trades: {len(sim.log)}")
    print(f"⚡ SEI Médio (Ev):  {np.mean(sei_trades):.2f}% (Capture Efficiency)")
    print(f"🔐 SHA256: {sha}")
    print("⚠️ NOTA: RETCODE 10009 é MOCK para fins de simulação de custo real.")
    print("="*60)

if __name__ == "__main__":
    run_auditoria_psa_v580()
