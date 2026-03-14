import pandas as pd
import numpy as np
import os
from modules.omega_parr_f_engine import OmegaParrFEngine, ParrFMetrics

def run_surgical_resonance_audit():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M1.csv"
    if not os.path.exists(data_path):
        print(f"Erro: Arquivo {data_path} não encontrado.")
        return

    print(f"🚀 Iniciando Auditoria Cirúrgica de Ressonância: XAUUSD (Foco na Queda)")
    df = pd.read_csv(data_path)
    
    # Focar nas últimas 1440 barras (últimas 24h de trading da sexta)
    df_focus = df.tail(1440).copy()
    
    engine = OmegaParrFEngine()
    audit_results = engine.run_forensic_audit(df_focus)
    
    res_df = pd.DataFrame([vars(m) for m in audit_results])
    
    print("\n" + "="*60)
    print("📊 RELATÓRIO CIRÚRGICO PARR-F - EVENTO 13/03")
    print("="*60)
    
    # 1. Análise de Bloqueios Indevidos
    l0_fails = res_df['flags'].apply(lambda x: 'L0_FAIL_R2' in x).sum()
    l1_fails = res_df['flags'].apply(lambda x: 'L1_DEFASADO' in x).sum()
    l2_sats = res_df['flags'].apply(lambda x: 'L2_SATURADO' in x).sum()
    
    print(f"Bloqueios L0 (R² insuficiente): {l0_fails} barras")
    print(f"Cegueira L1 (POC Defasada): {l1_fails} barras")
    print(f"Saturação L2 (Z-Vol > 4.0): {l2_sats} barras")
    
    # 2. Identificação do Ponto de Ignição Perdido
    # Vamos procurar onde o Score tentou subir mas foi barrado
    print("\n🧐 ANÁLISE DE RESSONÂNCIA POR CAMADA (MÉDIAS NO EVENTO):")
    print(f"HFD Médio: {res_df['hfd_value'].mean():.4f}")
    print(f"R² Médio: {res_df['hfd_r2'].mean():.4f}")
    print(f"Z-Vol Log Médio: {res_df['z_vol_log'].mean():.2f}")
    print(f"POC Lag Médio: {res_df['poc_lag'].mean():.2f}")
    
    # Flags Frequentes
    all_flags = [flag for sublist in res_df['flags'] for flag in sublist]
    flag_dist = pd.Series(all_flags).value_counts()
    print(f"\nDistribuição de Falhas: \n{flag_dist}")

    # Ponto de Falha Crítica
    print("\n❗ VEREDITO TÉCNICO:")
    if l1_fails > l0_fails:
        print("CAUSA RAIZ: L1 (Navegação). A POC ficou 'ancorada' no topo enquanto o preço derretia.")
        print("AÇÃO: Ativar DYNAMIC_POC_WINDOW (Seção 5.2 do Protocolo).")
    elif l0_fails > 0:
        print("CAUSA RAIZ: L0 (Estrutural). HFD falso-caótico bloqueou a ignição.")
        print("AÇÃO: Implementar FALLBACK_HFD_R2 (Seção 5.1 do Protocolo).")
    else:
        print("CAUSA RAIZ: L3/Execução. O sistema viu mas não teve 'coragem' de disparar.")
        print("AÇÃO: Ativar MULTI-STAGE REENTRY (Seção 4 do Protocolo).")

    print("="*60)

if __name__ == "__main__":
    run_surgical_resonance_audit()
