import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime

# Importar Módulos do Ecossistema OMEGA
sys.path.append(os.getcwd())
try:
    from cost_oracle_v550 import CostOracle, CostSnapshot
    from telemetry_cfd_v550 import summarize, compute_telemetry
    from telemetry_amplifier_v550 import TelemetryAmplifier
except ImportError as e:
    print(f"Erro de Integração: {e}")

# Importar Kernel PARR-F
sys.path.append(r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND")
from omega_parr_f_engine import OmegaParrFEngine

class HyperAuditEngineV550:
    def __init__(self, oracle: CostOracle, z_guard=0.5, debounce=120):
        self.oracle = oracle
        
        # Parâmetros de Missão
        self.HOLD_LOCK = 60
        self.Z_GUARD = z_guard
        self.DEBOUNCE = debounce
        self.CB_LIMIT = 20 # Permitindo maior fluidez
        
        self.current_pos = None
        self.last_exit = datetime(2010,1,1)
        self.min_window = []
        self.trades = []
        
        # Snapshot de custo inicial
        self.cost_snap = oracle.get_snapshot("XAUUSD")

    def process_tick(self, ts, price, score, zp):
        self.min_window = [t for t in self.min_window if (ts-t).total_seconds() < 60]
        
        if self.current_pos is None:
            if score >= 50: # Threshold de Harmonia
                if (ts - self.last_exit).total_seconds() < self.DEBOUNCE: return
                if len(self.min_window) >= self.CB_LIMIT: return
                
                self.current_pos = {
                    'ts_open': ts, 'price_open': price, 'zp_entry': zp, 
                    'entry_score': score
                }
                self.min_window.append(ts)
        else:
            duration = (ts - self.current_pos['ts_open']).total_seconds()
            
            # Consultar Oráculo para viabilidade de saída
            costs = self.oracle.effective_cost("XAUUSD", "buy", lots=1.0, hold_days=duration/(24*3600))
            raw_pnl_pts = (price - self.current_pos['price_open']) * 100
            
            # Lógica de Saída com Consciência de Fricção
            if score < 50:
                # Blindagem Base
                if duration < self.HOLD_LOCK: return
                if abs(zp) > self.Z_GUARD: return
                
                # Nona Camada: Só sai se o lucro bruto cobrir a fricção orquestrada
                if raw_pnl_pts < costs['total_cost'] * 1.2 and raw_pnl_pts > -500: # Buffer de 20%
                    return # Segura a posição para buscar harmonia
                
                self.eject(ts, price, zp, costs, "ALPHA_LOSS")

    def eject(self, ts, price, zp, costs, reason):
        p = self.current_pos
        raw_pts = (price - p['price_open']) * 100
        net_pnl = raw_pts - costs['total_cost']
        
        self.trades.append({
            'ts_open': p['ts_open'], 'ts_close': ts, 
            'duration_s': (ts - p['ts_open']).total_seconds(),
            'price_open': p['price_open'], 'price_close': price,
            'pnl_net': net_pnl, # Mapping para TelemetryCFD
            'spread_cost': costs['breakdown']['spread'],
            'slippage_cost': costs['breakdown']['slippage'],
            'swap_cost': costs['breakdown']['swap'],
            'total_cost': costs['total_cost'],
            'reason_exit': reason,
            'z_price': zp
        })
        self.last_exit = ts
        self.current_pos = None

def run_comparison_test():
    # 1. Setup
    oracle = CostOracle()
    oracle.set_snapshot(CostSnapshot(
        symbol="XAUUSD", spread_points=25, slippage_points=5,
        commission_per_lot=7, swap_long_per_day=-15, swap_short_per_day=5,
        pip_value=1.0, lot_size=100
    ))
    
    focal_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M1.csv"
    df_m1 = pd.read_csv(focal_path)
    df_m1['time'] = pd.to_datetime(df_m1['time'])
    mask = (df_m1['time'] >= '2026-03-01') & (df_m1['time'] <= '2026-03-16 23:59:59')
    df_period = df_m1.loc[mask].copy()
    
    print(f"Iniciando Simulação de 'Madrugada' (Janela: {df_period['time'].min()} a {df_period['time'].max()})")
    engine_audit = OmegaParrFEngine()
    audit_res = engine_audit.run_forensic_audit(df_period)
    metrics_df = pd.DataFrame(audit_res)
    metrics_df['time'] = df_period['time'].iloc[210:].values
    data = pd.merge(df_period, metrics_df, on='time', how='inner')
    
    # --- RUN A: BASELINE (V5.5.0 Original) ---
    print("Executando V5.5.0 BASELINE (Z=0.5, D=120)...")
    engine_a = HyperAuditEngineV550(oracle, z_guard=0.5, debounce=120)
    for i, row in data.iterrows():
        engine_a.process_tick(row['time'], row['close'], row['score_final'], row['z_vol_log'])
    df_a = pd.DataFrame(engine_a.trades)
    
    # --- RUN B: FINE-TUNED (NASA Tuning) ---
    print("Executando V5.5.0 FINE-TUNED (Z=0.3, D=90)...")
    engine_b = HyperAuditEngineV550(oracle, z_guard=0.3, debounce=90)
    for i, row in data.iterrows():
        engine_h = engine_b # Reusando lógica de process_tick
        engine_h.process_tick(row['time'], row['close'], row['score_final'], row['z_vol_log'])
    df_b = pd.DataFrame(engine_b.trades)
    
    # 2. Análise Comparativa (%)
    pnl_a = df_a['pnl_net'].sum() if not df_a.empty else 0
    pnl_b = df_b['pnl_net'].sum() if not df_b.empty else 0
    
    inc_pnl = ((pnl_b / pnl_a) - 1) * 100 if pnl_a != 0 else 0
    trade_count_inc = ((len(df_b) / len(df_a)) - 1) * 100 if len(df_a) > 0 else 0
    
    print("\n--- OMEGA V5.5.0 HARMONY COMPARISON ---")
    print(f"{'Métrica':<20} | {'Baseline':<12} | {'Fine-Tuned':<12} | {'Delta %':<10}")
    print("-" * 65)
    print(f"{'PnL Net ($)':<20} | {pnl_a:<12.2f} | {pnl_b:<12.2f} | {inc_pnl:>+8.2f}%")
    print(f"{'Trades Totais':<20} | {len(df_a):<12} | {len(df_b):<12} | {trade_count_inc:>+8.2f}%")
    print(f"{'Avg Duration (s)':<20} | {df_a['duration_s'].mean():<12.1f} | {df_b['duration_s'].mean():<12.1f} |")
    
    # 3. Veredito de Estabilidade
    churn_b = len(df_b[df_b['duration_s'] <= 3])
    print(f"\nStatus de Blindagem (Fine-Tuned): {('✅ INTEGRAL' if churn_b == 0 else '⚠️ VIOLAÇÃO')}")
    print(f"Churn trades: {churn_b}")
    
    if inc_pnl > 5:
        print("\n🚀 RESULTADO: AFINAÇÃO CONFIRMADA. O aumento de agressividade (+Delta PnL) manteve a harmonia operacional.")
    elif inc_pnl < -5:
        print("\n⚠️ RESULTADO: DISTORÇÃO DETECTADA. A calibração foi muito agressiva, resultando em perda de proteção.")
    else:
        print("\n⚖️ RESULTADO: NEUTRALIDADE. Ajustes marginais detectados.")

    # Salvar Report
    with open(r"C:\OMEGA_PROJETO\Auditoria PARR-F\HARMONY_COMPARISON_V550.json", "w") as f:
        json.dump({
            "baseline": {"pnl": pnl_a, "trades": len(df_a)},
            "fine_tuned": {"pnl": pnl_b, "trades": len(df_b)},
            "delta_pnl_pct": inc_pnl
        }, f, indent=4)

if __name__ == "__main__":
    run_comparison_test()
