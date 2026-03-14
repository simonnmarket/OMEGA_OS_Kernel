import numpy as np
import pandas as pd
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from scipy import stats
from modules.omega_parr_f_engine import OmegaParrFEngine

# =============================================================================
# OMEGA MFA (MASSIVE FORENSIC AUDITOR) - TIER-0
# INTEGRANDO EXECUÇÃO MT5, LATÊNCIA E GRID SEARCH
# =============================================================================

class OmegaForensicAuditor:
    def __init__(self, data_path: str, timeframe: str):
        self.df = pd.read_csv(data_path)
        self.timeframe = timeframe
        self.results_log = []
        self.execution_stats = {
            'attempts': 0, 'success': 0, 'slippage_pips': [], 'rejections': {},
            'latency_ms': [], 'margin_fails': 0
        }
        
    def simulate_execution(self, signal_type: str, atr: float, spread: float, equity: float):
        """Simulador de Execução Institucional MT5"""
        self.execution_stats['attempts'] += 1
        latency = np.random.uniform(20, 150) # ms
        self.execution_stats['latency_ms'].append(latency)
        
        # Simulação de Margin - Usando lote de 0.1 como base institucional
        margin_required = 1000 # Valor estático aproximado para simulação
        if margin_required > (equity * 0.5): # Cap de margem (50% do equity)
            self.execution_stats['margin_fails'] += 1
            return {"status": "FAIL", "retcode": 10044, "reason": "No Money"}
            
        slippage = (atr * 0.05) * (latency / 1000)
        self.execution_stats['slippage_pips'].append(slippage)
        
        if np.random.random() < 0.005:
            return {"status": "FAIL", "retcode": 10027, "reason": "Timeout"}
            
        self.execution_stats['success'] += 1
        return {"status": "DONE", "retcode": 10009, "slippage": slippage}

    def grid_search_optimization(self, param_grid: Dict):
        """Grid Search de SEI e Acurácia por Componente"""
        summary = []
        subset = self.df.tail(1500)
        for h_win in param_grid['hfd_window']:
            for p_win in param_grid['poc_window']:
                engine = OmegaParrFEngine({'hfd_window': h_win, 'poc_window_base': p_win})
                sei, acc = self._quick_backtest(engine, subset)
                summary.append({'hfd_w': h_win, 'poc_w': p_win, 'sei': sei, 'acc': acc})
        return pd.DataFrame(summary)

    def _quick_backtest(self, engine, subset):
        audit = engine.run_forensic_audit(subset)
        if not audit: return 0.0, 0.0
        scores = [m['score_final'] for m in audit]
        # SEI = Média de captura normalizada
        sei = np.mean([s for s in scores if s >= 60]) / 1.5 if any(s >= 60 for s in scores) else 0.0
        acc = len([s for s in scores if s >= 90]) / len(scores) * 100
        return sei, acc

    def generate_regime_matrix(self, ohlcv_dataframe: pd.DataFrame):
        """Gera a Matriz de Performance por Regime de Volatilidade"""
        engine = OmegaParrFEngine()
        audit = engine.run_forensic_audit(ohlcv_dataframe)
        ohlcv_array = ohlcv_dataframe[['open', 'high', 'low', 'close', 'tick_volume']].values
        
        shifted_close = np.roll(ohlcv_array[:, 3], 1)
        shifted_close[0] = ohlcv_array[0, 0]
        tr = np.maximum(ohlcv_array[:, 1] - ohlcv_array[:, 2], 
                        np.maximum(abs(ohlcv_array[:, 1] - shifted_close), 
                                   abs(ohlcv_array[:, 2] - shifted_close)))
        
        data = []
        for i, m in enumerate(audit):
            idx = i + 210
            if idx >= len(tr): break
            current_atr = np.mean(tr[max(0, idx-20):idx])
            
            regime = "Low (<50)" if current_atr < 50 else \
                     "Med (50-200)" if current_atr < 200 else \
                     "High (200-500)" if current_atr < 500 else "Extreme (>500)"
            
            data.append({
                'Regime': regime,
                'Avg_Score': m['score_final'],
                'HFD_R2': m['hfd_r2'],
                'POC_Lag': m['poc_lag']
            })
            
        res_df = pd.DataFrame(data)
        return res_df.groupby('Regime').mean()

if __name__ == "__main__":
    h4_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if os.path.exists(h4_path):
        auditor = OmegaForensicAuditor(h4_path, "H4")
        
        print("Iniciando Grid Search Global (P0)...")
        gs_results = auditor.grid_search_optimization({
            'hfd_window': [100, 200, 300, 400, 500],
            'poc_window': [30, 50, 100, 150, 200]
        })
        
        print("Gerando Matriz de Regimes Institucionais...")
        reg_matrix = auditor.generate_regime_matrix(auditor.df.tail(5000))
        
        print("Simulando Fluxo de Execução MT5 (2.500 USD Equity)...")
        for _ in range(1000):
            auditor.simulate_execution("SELL", 220, 0.5, 2500)
            
        # --- OUTPUT FORMATADO PARA O CRO ---
        print("\n\n" + "="*80)
        print("OMEGA MFA REPORT: TIER-0 INSTITUCIONAL DATAFRAME")
        print("="*80)
        
        print("\n1. PARAMETER OPTIMIZATION (GRID SEARCH - NASA-STD)")
        print(gs_results.sort_values(by='sei', ascending=False).to_string(index=False))
        
        print("\n2. PERFORMANCE BY VOLATILITY REGIME (ATR BREAKDOWN)")
        print(reg_matrix)
        
        print("\n3. EXECUTION & ORDER FORENSICS (SIMULATED MT5 LATENCY)")
        stats_ex = auditor.execution_stats
        print(f"Total Order Attempts: {stats_ex['attempts']}")
        print(f"Server Success Rate: {stats_ex['success']/stats_ex['attempts']*100:.2f}%")
        print(f"Avg Network/Broker Latency: {np.mean(stats_ex['latency_ms']):.2f} ms")
        print(f"Avg Realized Slippage: {np.mean(stats_ex['slippage_pips']):.5f} pips")
        print(f"Critical Margin Rejections (MT5 10044): {stats_ex['margin_fails']}")
        print("="*80)
    else:
        print("Arquivo H4 ausente.")
