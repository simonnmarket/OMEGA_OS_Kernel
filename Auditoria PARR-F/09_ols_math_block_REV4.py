import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import os
import json

class PairsTradingMathBlockV2:
    """
    Motor Matemático V8.2.1 (Tier-0) - Fase 2 CORRIGIDA
    Incorpora: ADF Test, Modelo de Custos (19pts), e Z-Score Causal (Lagged).
    """
    
    def __init__(self, asset_y_name="XAUUSD", asset_x_name="XAGUSD", window_ols=500, ewma_span=100):
        self.asset_y = asset_y_name
        self.asset_x = asset_x_name
        self.window_ols = window_ols
        self.ewma_span = ewma_span
        # Custos CFO: 12 spread + 5 slippage + 2 comm = 19 pts
        self.total_cost_pts = 19.0 
        
    def fit_rolling_ols(self, df_y, df_x):
        """Calcula Beta Dinâmico via OLS rolante."""
        print(f"[*] Executando OLS Rolante Causal ({self.window_ols} barras)...")
        df = pd.DataFrame({'Y': df_y['close'], 'X': df_x['close']}).dropna()
        
        y_vals = df['Y'].values
        x_vals = df['X'].values
        betas = np.full(len(df), np.nan)
        alphas = np.full(len(df), np.nan)
        
        for i in range(self.window_ols, len(df)):
            y_win = y_vals[i-self.window_ols:i]
            x_win = x_vals[i-self.window_ols:i]
            X_const = sm.add_constant(x_win)
            res = sm.OLS(y_win, X_const).fit()
            alphas[i] = res.params[0]
            betas[i] = res.params[1]
            
        df['Alpha'] = alphas
        df['Beta'] = betas
        # Spread: Y - (Alpha + Beta * X)
        df['Spread'] = df['Y'] - (df['Alpha'] + df['Beta'] * df['X'])
        return df.dropna()

    def apply_causal_zscore_and_costs(self, df):
        """
        Aplica Z-Score Causal (sem look-ahead) e desconta custos de 19pts.
        """
        print(f"[*] Aplicando Normalização Causal e Modelo de Custos (19pts)...")
        
        # 1. Z-Score Causal: μ e σ calculados até (t-1)
        ewm = df['Spread'].ewm(span=self.ewma_span, adjust=False)
        df['EWMA_Mean'] = ewm.mean().shift(1)
        df['EWMA_Std'] = ewm.std().shift(1)
        
        # Proteção contra divisão por zero (epsilon 1e-12)
        df['Z_Score'] = (df['Spread'] - df['EWMA_Mean']) / (df['EWMA_Std'] + 1e-12)
        
        # 2. Simulação de PnL Crue e Líquida (Simplificada para auditoria)
        # Assumindo reversão de 30 barras para o teste
        horizon = 30
        df['PnL_Gross_Pts'] = (df['Z_Score'].shift(-horizon) - df['Z_Score']) * df['EWMA_Std']
        # Tradução de 19pts para a escala do Spread (aproximado pelo std do spread)
        df['PnL_Net_Pts'] = df['PnL_Gross_Pts'] - self.total_cost_pts
        
        return df.dropna()

    def run_stat_audit(self, df):
        """Executa ADF Test e métricas Tier-0."""
        print(f"[*] Iniciando Auditoria Estatística (ADF / Cointegration)...")
        
        adf_res = adfuller(df['Spread'])
        p_value = adf_res[1]
        t_stat = adf_res[0]
        cv_5 = adf_res[4]['5%']
        
        is_stationary = p_value <= 0.05
        
        # Simulação Profit Factor
        pos_pnl = df[df['PnL_Net_Pts'] > 0]['PnL_Net_Pts'].sum()
        neg_pnl = abs(df[df['PnL_Net_Pts'] < 0]['PnL_Net_Pts'].sum())
        pf_net = pos_pnl / neg_pnl if neg_pnl > 0 else 0
        
        audit_report = {
            "ADF_Statistic": float(t_stat),
            "ADF_p_value": float(p_value),
            "Critical_Value_5%": float(cv_5),
            "Stationarity_Approved": bool(is_stationary),
            "Net_Profit_Factor_Target_1.5": float(pf_net),
            "Transaction_Cost_Applied": "19pts",
            "Status": "VALIDATED" if (is_stationary and pf_net >= 1.5) else "REJECTED_BY_GATES"
        }
        
        return audit_report

if __name__ == "__main__":
    print("="*60)
    print("MACE-MAX TIER-0 | CORREÇÃO DE AUDITORIA CONSELHO (REV4)")
    print("="*60)
    
    # Carregar dados Fase 1
    df_xau = pd.read_parquet("data_lake/XAUUSD_M1_HISTORICO.parquet").set_index('time')
    df_xag = pd.read_parquet("data_lake/XAGUSD_M1_HISTORICO.parquet").set_index('time')
    
    # Motor V2 (Corrigido)
    engine = PairsTradingMathBlockV2()
    
    # 1. Pipeline
    df_calc = engine.fit_rolling_ols(df_xau, df_xag)
    df_calc = engine.apply_causal_zscore_and_costs(df_calc)
    
    # 2. Auditoria
    result = engine.run_stat_audit(df_calc)
    
    # 3. Salvar Artefatos
    os.makedirs("audit_blocks", exist_ok=True)
    with open("audit_blocks/final_math_audit_v82.json", "w") as f:
        json.dump(result, f, indent=4)
        
    df_calc[['Y', 'X', 'Beta', 'Spread', 'Z_Score', 'PnL_Net_Pts']].tail(2000).to_csv("audit_blocks/math_audit_v82_REV4.csv")
    
    print("\n[✔] RELATÓRIO DE AUDITORIA FINALIZADO")
    print(json.dumps(result, indent=4))
    print("\n[+] Artefatos salvos em: audit_blocks/math_audit_v82_REV4.csv")
