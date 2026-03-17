import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class AntiOuroborosManager:
    def __init__(self):
        # Parâmetros Homologados V5.5.0
        self.HOLD_LOCK_SEC = 60
        self.Z_GUARD_THRESHOLD = 0.5
        self.DEBOUNCE_SEC = 120
        self.FR_LIMIT = 0.20
        self.FR_WARNING = 0.15
        self.CB_LIMIT = 3  # Trades per minute
        
        self.trade_history = []
        self.current_pos = None
        self.last_exit_time = datetime(2010, 1, 1)
        self.minute_window = []

    def should_exit(self, entry_time, current_time, z_price, beat, reason):
        # CAMADA 1: HOLD LOCK (Atomic Shield)
        age = (current_time - entry_time).total_seconds()
        if age < self.HOLD_LOCK_SEC and reason == "REPOUSO":
            return False, "HOLD: Protect Kinetic"
            
        # CAMADA 2: Z-GUARD (Macro Inertia)
        if abs(z_price) > self.Z_GUARD_THRESHOLD and reason == "REPOUSO":
            return False, "HOLD: Z-Inertia Strong"
            
        # CAMADA 3: Rhythmic Hysteresis (Simulada por Beat)
        if beat < 400 and age < 10: # Se for muito cedo e ritmo baixo, ignora oscilação
            return False, "HOLD: Noise Filtered"
            
        return True, "EXIT_AUTHORIZED"

    def can_enter(self, current_time, atr_ratio=1.0):
        # CAMADA 4: DEBOUNCE DINÂMICO (Gold Standard 120s)
        dynamic_debounce = max(30, min(self.DEBOUNCE_SEC, int(30 * atr_ratio)))
        if (current_time - self.last_exit_time).total_seconds() < dynamic_debounce:
            return False, f"BLOCK: Debounce {dynamic_debounce}s"
            
        # CAMADA 5: CIRCUIT BREAKER (Frequency Fuse)
        self.minute_window = [t for t in self.minute_window if (current_time - t).total_seconds() < 60]
        if len(self.minute_window) >= self.CB_LIMIT:
            return False, "BLOCK: Circuit Breaker Active"
            
        return True, "GO"

def run_necromancy_full_backtest():
    path = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_RECONCILED_V590.csv"
    if not os.path.exists(path):
        print(f"Erro: Arquivo não encontrado em {path}")
        return

    df = pd.read_csv(path)
    df['TS'] = pd.to_datetime(df['TS'])
    
    manager = AntiOuroborosManager()
    balance = 10000.0
    equity_curve = []
    trades = []
    
    # Simulação
    for i, row in df.iterrows():
        ts = row['TS']
        price = row['PRICE']
        score = row['SCORE']
        z_price = row['L2_ZVOL'] # Usando ZVOL como proxy de inércia nos dados reconciliados
        
        # Lógica de Entrada
        if manager.current_pos is None:
            can_entry, msg = manager.can_enter(ts)
            if score >= 85 and can_entry:
                manager.current_pos = {'entry_ts': ts, 'entry_price': price, 'type': 'BUY'}
                manager.minute_window.append(ts)
        
        # Lógica de Saída/Hold
        elif manager.current_pos:
            # Saída por perda de Score (REPOUSO)
            if score < 50:
                authorized, reason = manager.should_exit(
                    manager.current_pos['entry_ts'], ts, z_price, 300, "REPOUSO"
                )
                
                if authorized:
                    pnl = (price - manager.current_pos['entry_price']) * 10 # Multiplicador simbólico
                    balance += pnl
                    trades.append({
                        'entry': manager.current_pos['entry_ts'],
                        'exit': ts,
                        'duration': (ts - manager.current_pos['entry_ts']).total_seconds(),
                        'pnl': pnl,
                        'reason': reason
                    })
                    manager.last_exit_time = ts
                    manager.current_pos = None

        equity_curve.append(balance)

    # Métricas Finais
    df_trades = pd.DataFrame(trades)
    churn_count = len(df_trades[df_trades['duration'] <= 3]) if not df_trades.empty else 0
    total_trades = len(df_trades)
    
    print("--- OMEGA V5.5.0 NECROMANCY TEST RESULTS ---")
    print(f"Período: {df['TS'].min()} até {df['TS'].max()}")
    print(f"Capital Final: ${balance:.2f}")
    print(f"Total de Trades: {total_trades}")
    print(f"Hemorragia de Churn (<= 3s): {churn_count} (META: 0)")
    if total_trades > 0:
        print(f"Média Duração: {df_trades['duration'].mean():.2f}s")
        print(f"Win Rate: {len(df_trades[df_trades['pnl'] > 0]) / total_trades * 100:.2f}%")
    
    return trades

if __name__ == "__main__":
    run_necromancy_full_backtest()
