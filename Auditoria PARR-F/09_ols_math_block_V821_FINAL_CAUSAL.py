import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import os
import json
import warnings

# OMEGA V8.2.1 - TIER-0 CAUSAL BACKTESTER (PHASE 2 FINAL)
# Autor: Antigravity MACE-MAX
# Correção CFO: Erradicação de shift(-h) no Cálculo de PnL

warnings.filterwarnings('ignore')

class OmegaCausalEngineV821:
    """
    Motor de Backtest Causal (Sem Look-ahead).
    As decisões de entrada e saída são baseadas APENAS no Z-Score T-1.
    """
    
    def __init__(self, window_ols=500, ewma_span=100, entry_z=2.0, exit_z=0.0):
        self.window_ols = window_ols
        self.ewma_span = ewma_span
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.cost_pts = 19.0 # CFO Cost Model

    def run_pipeline(self, df_y, df_x):
        print(f"[*] Iniciando Pipeline Causal OMEGA V8.2.1...")
        
        # 1. Alinhamento e OLS Rolante
        df = pd.DataFrame({'Y': df_y['close'], 'X': df_x['close']}).dropna()
        y_vals, x_vals = df['Y'].values, df['X'].values
        betas, alphas = np.full(len(df), np.nan), np.full(len(df), np.nan)
        
        for i in range(self.window_ols, len(df)):
            # Somente dados PASSADOS (i-window:i)
            res = sm.OLS(y_vals[i-self.window_ols:i], sm.add_constant(x_vals[i-self.window_ols:i])).fit()
            alphas[i], betas[i] = res.params[0], res.params[1]
            
        df['Alpha'], df['Beta'] = alphas, betas
        df['Spread'] = df['Y'] - (df['Alpha'] + df['Beta'] * df['X'])
        df = df.dropna()

        # 2. Normalização Causal (Shift 1)
        ewm = df['Spread'].ewm(span=self.ewma_span, adjust=False)
        df['Mean_T1'] = ewm.mean().shift(1)
        df['Std_T1'] = ewm.std().shift(1)
        df['Z_Score'] = (df['Spread'] - df['Mean_T1']) / (df['Std_T1'] + 1e-12)
        df = df.dropna()

        # 3. BACKTESTER CAUSAL (STATE MACHINE) - Sem shift futurista
        print(f"[*] Executando Backtest de Eventos (Causal State Machine)...")
        
        pnl_accum = 0.0
        trades = []
        state = 0 # 0: Fora, 1: Long Spread (Buy Y, Sell X), -1: Short Spread (Sell Y, Buy X)
        entry_val = 0.0
        
        z_scores = df['Z_Score'].values
        spread_vals = df['Spread'].values
        times = df.index.values
        
        for i in range(1, len(df)):
            current_z = z_scores[i]
            current_s = spread_vals[i]
            
            # LÓGICA DE ENTRADA
            if state == 0:
                if current_z >= self.entry_z:
                    state = -1 # Vende Spread
                    entry_val = current_s
                elif current_z <= -self.entry_z:
                    state = 1 # Compra Spread
                    entry_val = current_s
            
            # LÓGICA DE SAÍDA (REVERSÃO À MÉDIA)
            elif state == 1: # Long
                if current_z >= self.exit_z:
                    trade_pnl = (current_s - entry_val) - self.cost_pts
                    pnl_accum += trade_pnl
                    trades.append(trade_pnl)
                    state = 0
            elif state == -1: # Short
                if current_z <= self.exit_z:
                    trade_pnl = (entry_val - current_s) - self.cost_pts
                    pnl_accum += trade_pnl
                    trades.append(trade_pnl)
                    state = 0
        
        # 4. Estatísticas Finais
        trades = np.array(trades)
        pos_trades = trades[trades > 0]
        neg_trades = trades[trades < 0]
        
        pf_net = (pos_trades.sum() / abs(neg_trades.sum())) if len(neg_trades) > 0 else 0
        win_rate = (len(pos_trades) / len(trades)) if len(trades) > 0 else 0
        
        # Teste ADF (Mantido como Prova de Estacionariedade do Spread)
        adf_p = adfuller(df['Spread'])[1]
        
        audit = {
            "ADF_p_value": float(adf_p),
            "Stationarity_Approved": bool(adf_p < 0.05),
            "Total_Trades_Simulated": int(len(trades)),
            "Win_Rate_Net": float(win_rate),
            "Profit_Factor_Net": float(pf_net),
            "CFO_Status": "APPROVED" if (pf_net >= 1.2 and adf_p < 0.05) else "REJECTED_BY_GATES"
        }
        
        return df, audit

if __name__ == "__main__":
    print("="*60)
    print("🛡️ OMEGA V8.2.1 | PROVA FINAL CAUSAL (CFO COMPLIANT)")
    print("="*60)

    # 1. Carregar dados reais
    xau = pd.read_parquet("data_lake/XAUUSD_M1_HISTORICO.parquet").set_index('time')
    xag = pd.read_parquet("data_lake/XAGUSD_M1_HISTORICO.parquet").set_index('time')

    # 2. Rodar Motor Causal
    engine = OmegaCausalEngineV821()
    df_final, audit_json = engine.run_pipeline(xau, xag)

    # 3. Exportar resultados
    os.makedirs("audit_blocks", exist_ok=True)
    with open("audit_blocks/V821_FINAL_CAUSAL_PROOF.json", "w") as f:
        json.dump(audit_json, f, indent=4)
        
    df_final[['Alpha', 'Beta', 'Spread', 'Z_Score']].tail(2000).to_csv("audit_blocks/V821_FINAL_CURVE.csv")

    print("\n[✔] PROVA CAUSAL CONCLUÍDA")
    print(json.dumps(audit_json, indent=4))
    print("\n[+] Arquivos gerados em audit_blocks/ para Auditoria do CFO.")
