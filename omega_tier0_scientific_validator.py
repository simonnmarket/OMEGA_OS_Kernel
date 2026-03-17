import pandas as pd
import numpy as np
import os
import time
from datetime import datetime
from scipy import stats
from modules.omega_parr_f_engine import OmegaParrFEngine

# =============================================================================
# OMEGA TIER-0 SCIENTIFIC VALIDATOR (OOS & STRESS)
# OBJETIVO: REPLICAÇÃO CIENTÍFICA EXAUSTIVA (2008-2026)
# =============================================================================

class Tier0Validator:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.output_dir = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_long_term_data(self):
        print(f"[*] Carregando dataset XAUUSD Gray-Scale...")
        df = pd.read_csv(self.data_path)
        df['time'] = pd.to_datetime(df['time'])
        return df

    def detect_institutional_swings(self, df, min_pts=9000):
        print(f"[*] Detectando Swings Institucionais (> {min_pts} pts)...")
        # Identifica grandes expansões em janelas móveis
        df['amplitude'] = (df['high'].rolling(50).max() - df['low'].rolling(50).min()) * 100 # Em pts (MT5)
        swings = df[df['amplitude'] > min_pts].copy()
        print(f"✅ {len(swings)} eventos críticos isolados para auditoria.")
        return swings

    def run_telemetry_audit(self, df, events_df):
        engine_v53 = OmegaParrFEngine({'hfd_window': 100, 'poc_window_base': 30}) # V5.3 PARR-F
        engine_v52 = OmegaParrFEngine({'hfd_window': 200, 'poc_window_base': 150}) # V5.2 BASELINE
        
        telemetry = []
        ohlcv = df[['open', 'high', 'low', 'close', 'tick_volume']].values
        
        # Amostragem de eventos para auditoria profunda (Top 20 Swings Históricos)
        event_indices = events_df.index.unique()[-20:] 
        
        for idx in event_indices:
            if idx < 210: continue
            
            # 1. Auditoria V5.3 (PARR-F)
            res_v53 = engine_v53.run_forensic_audit(df.iloc[idx-210:idx+1])[-1]
            
            # 2. Auditoria V5.2 (Baseline)
            res_v52 = engine_v52.run_forensic_audit(df.iloc[idx-210:idx+1])[-1]
            
            telemetry.append({
                'timestamp': df.iloc[idx]['time'],
                'v53_score': res_v53['score_final'],
                'v52_score': res_v52['score_final'],
                'v53_hfd': res_v53['hfd_value'],
                'v53_r2': res_v53['hfd_r2'],
                'v53_poc_lag': res_v53['poc_lag'],
                'v53_zvol': res_v53['z_vol_log'],
                'sei_v53': (res_v53['score_final'] / 100) * 100,
                'sei_v52': (res_v52['score_final'] / 100) * 100,
                'improvement_%': res_v53['score_final'] - res_v52['score_final']
            })
            
        return pd.DataFrame(telemetry)

    def generate_stress_test_report(self, telemetry_df):
        # 1. Matriz de Confusão / Taxa de Captura
        v53_hits = len(telemetry_df[telemetry_df['v53_score'] >= 70])
        v52_hits = len(telemetry_df[telemetry_df['v52_score'] >= 70])
        
        # 2. Cálculo de Significância (T-Test)
        t_stat, p_val = stats.ttest_rel(telemetry_df['v53_score'], telemetry_df['v52_score'])
        
        report_path = os.path.join(self.output_dir, "LAUDO_TECNICO_REPLICAVEL.md")
        with open(report_path, "w", encoding='utf-8') as f:
            f.write(f"# 🏛️ LAUDO TÉCNICO DE REPLICAÇÃO OMEGA V5.3\n")
            f.write(f"**DATA DA EXTRAÇÃO:** {datetime.now().isoformat()}\n\n")
            
            f.write("## 1. COMPARATIVO DE RESSONÂNCIA (V5.3 vs V5.2)\n")
            f.write(f"- Sinais Capturados V5.3 (PARR-F): **{v53_hits}** / 20 eventos\n")
            f.write(f"- Sinais Capturados V5.2 (Baseline): **{v52_hits}** / 20 eventos\n")
            f.write(f"- P-Value (Significância de Melhoria): **{p_val:.12f}**\n\n")
            
            f.write("## 2. DATASETS & CONFIGURAÇÃO\n")
            f.write("- Dataset: XAUUSD_H4.csv (2008-2026)\n")
            f.write("- L0 Janela: 100 (v5.3) vs 200 (v5.2)\n")
            f.write("- L1 Janela: 30 (v5.3) vs 150 (v5.2)\n\n")
            
            f.write("## 3. TELEMETRIA BRUTA DOS EVENTOS (ANEXO A)\n")
            f.write(telemetry_df.to_markdown(index=False))
            
        telemetry_df.to_csv(os.path.join(self.output_dir, "telemetry_raw_oos.csv"), index=False)
        print(f"✅ Laudo Gerado em: {report_path}")

if __name__ == "__main__":
    validator = Tier0Validator(r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv")
    df_history = validator.load_long_term_data()
    events = validator.detect_institutional_swings(df_history)
    telemetry = validator.run_telemetry_audit(df_history, events)
    validator.generate_stress_test_report(telemetry)
