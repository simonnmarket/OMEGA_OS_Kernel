import pandas as pd
import numpy as np
import os
from modules.omega_parr_f_engine import OmegaParrFEngine, ParrFMetrics

def run_historical_resonance_audit():
    # Caminho dos dados extraídos
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M1.csv"
    if not os.path.exists(data_path):
        print(f"Erro: Arquivo {data_path} não encontrado.")
        return

    print(f"🚀 Iniciando Auditoria Forense de Ressonância: XAUUSD (Histórico M1)")
    df = pd.read_csv(data_path)
    
    # Inicializa o Motor PARR-F V5.3
    engine = OmegaParrFEngine()
    
    # Executa a auditoria barra por barra
    # Para performance, vamos focar nos últimos 3 dias (onde ocorreu a grande movimentação)
    # 10.000 barras M1 = aprox 7 dias.
    audit_results = engine.run_forensic_audit(df)
    
    # Converter resultados em DataFrame para análise estatística
    res_df = pd.DataFrame([vars(m) for m in audit_results])
    
    # 1. Identificação de "Oportunidades Perdidas" (Grandes Movimentos)
    df['amplitude_30'] = df['close'].diff(30).abs() # Amplitude em 30 min
    big_moves_idx = df[df['amplitude_30'] > 5000].index # Movimentos > 5000 pts
    
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE RESSONÂNCIA FORENSE - XAUUSD")
    print("="*60)
    
    # Estatísticas de Camada
    print(f"Média HFD R²: {res_df['hfd_r2'].mean():.4f}")
    print(f"Saturação Z-Vol (>4.0): {(res_df['z_vol_log'] > 4.0).mean()*100:.2f}%")
    print(f"Lag Médio de POC: {res_df['poc_lag'].mean():.2f}")
    
    # Flags de Falha Detectadas
    all_flags = [flag for sublist in res_df['flags'] for flag in sublist]
    flag_counts = pd.Series(all_flags).value_counts()
    
    print("\n🚩 INCIDÊNCIA DE FALHAS SISTÊMICAS (PARAFUSOS SOLTOS):")
    for flag, count in flag_counts.items():
        print(f"- {flag}: {count} ocorrências")

    # Análise Cirúrgica do Evento de Sexta-Feira (Final do Arquivo)
    last_event = res_df.iloc[-1]
    print("\n[OPS EVENT - FECHAMENTO SEXTA-FEIRA]")
    print(f"Score Final: {last_event['score_final']}")
    print(f"Regime: {last_event['regime']}")
    print(f"Flags no Evento: {last_event['flags']}")
    print(f"HFD: {last_event['hfd_value']:.4f} | R2: {last_event['hfd_r2']:.4f}")
    print(f"Z-Vol Log: {last_event['z_vol_log']:.2f}")
    print(f"POC Lag: {last_event['poc_lag']:.2f}")
    
    # Conclusão da Ressonância
    sei_estimado = (res_df['score_final'] >= 90).mean() * 100
    print("\n🎯 CONCLUSÃO DE EFICIÊNCIA:")
    print(f"SEI Potencial com PARR-F V5.3: {sei_estimado:.2f}%")
    print(f"Status de Ressonância: {'NOMINAL' if sei_estimado > 15 else 'CRÍTICO - NECESSITA CALIBRAGEM'}")
    print("="*60)

if __name__ == "__main__":
    run_historical_resonance_audit()
