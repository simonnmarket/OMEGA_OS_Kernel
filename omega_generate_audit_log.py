
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def generate_full_audit_log():
    # PATHS
    m15_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    
    # LOAD
    df = pd.read_csv(m15_path)
    df['time'] = pd.to_datetime(df['time'])
    df.sort_values('time', inplace=True)
    
    engine = OmegaParrFEngine()
    
    # SIMULADOR DE AUDITORIA FORENSE
    ohlcv = df[['open','high','low','close','tick_volume']].values
    times = df['time'].values
    
    audit_data = []
    
    print(f"🕵️ GERANDO RELATÓRIO FORENSE DE OPERAÇÕES OMEGA V5.22.0...")
    
    for i in range(20, len(ohlcv)):
        slice_data = ohlcv[i-19:i+1]
        res = engine.execute_audit(slice_data)
        
        # Registramos apenas quando há atividade física (Caminhada, Corrida, Adrenalina)
        if res['state'] != "REPOUSO":
            audit_data.append({
                'TIMESTAMP': times[i],
                'OPEN': ohlcv[i, 0],
                'CLOSE': ohlcv[i, 3],
                'BEAT_POINTS': res['beat'],
                'METABOLIC_STATE': res['state'],
                'SCORE': res['score'],
                'LAUNCH': res['launch'],
                'BIAS': 'BUY' if res['bias'] > 0 else 'SELL',
                'Z_PRICE': res['z_price']
            })
    
    # SALVAR CSV PARA AUDITORIA EXTERNA
    audit_df = pd.DataFrame(audit_data)
    audit_path = 'C:/OMEGA_PROJETO/PROJETO OMEGA QUANTITATIVE FUND/AUDIT_EVIDÊNCIA_CIENTÍFICA/FULL_METABOLIC_AUDIT_V522.csv'
    audit_df.to_csv(audit_path, index=False)
    
    # GERAR O DOCUMENTO DE RESUMO PARA O USUÁRIO
    print(f"✅ Arquivo de auditoria gerado em: {audit_path}")
    
    # Exibir o cabeçalho e as operações mais impactantes (Março/2026)
    mar_data = audit_df[audit_df['TIMESTAMP'] >= '2026-03-09']
    
    print("\n" + "="*120)
    print(f"📜 MEMORIAL DE AUDITORIA FORENSE — OMEGA V5.22.0 (METABOLIC SNIPER)")
    print("="*120)
    print(mar_data.head(50).to_string(index=False))
    print("\n" + "="*120)
    print(f"📊 TOTAL DE EVENTOS AUDITADOS NO PERÍODO: {len(audit_df)}")
    print(f"🚀 TOTAL DE GATILHOS DISPARADOS (LAUNCH): {len(audit_df[audit_df['LAUNCH'] == True])}")
    print("="*120)

if __name__ == "__main__":
    generate_full_audit_log()
