import pandas as pd
import numpy as np
import os
import time
from modules.omega_parr_f_engine import OmegaParrFEngine
from datetime import datetime

# =============================================================================
# OMEGA FULL HISTORICAL AUDIT V5.4.2 — BOARD GRADE SRE
# =============================================================================

def run_full_audit():
    data_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_H4.csv"
    if not os.path.exists(data_path):
        print(f"❌ Erro: Arquivo de histórico não encontrado em {data_path}")
        return

    print("🚀 INICIANDO AUDITORIA DE RESSONÂNCIA EM HISTÓRICO COMPLETO (XAUUSD H4)...")
    df = pd.read_csv(data_path)
    print(f"[*] Total de Barras: {len(df)}")
    
    engine = OmegaParrFEngine()
    results = []
    
    # Prepara OHLCV array [open, high, low, close, tick_volume]
    ohlcv_full = df[['open', 'high', 'low', 'close', 'tick_volume']].values
    
    warmup = 150
    start_time = time.time()
    
    # Telemetria de Simulação de Performance (Simplificada)
    balance = 10000.0
    equity_curve = []
    trade_log = []
    active_position = None # {'entry': float, 'dir': int, 'atr': float}

    for i in range(warmup, len(df)):
        window = ohlcv_full[i-warmup:i+1]
        audit = engine.execute_full_audit(window)
        
        # Gestão de Posição SRE
        current_price = window[-1, 3] # Close
        atr = audit['atr']
        
        # 1. Check Exit (Stop/Target ou Reversão Inercial)
        if active_position:
            # Trailing Stop Simples based on ATR
            pnl_points = active_position['dir'] * (current_price - active_position['entry'])
            
            # Se a camada L0 romper ou Score cair abruptamente, ejetamos
            if audit['score'] < 25: 
                profit = pnl_points * 100 * 0.1 # $ per point (notional)
                balance += profit
                trade_log.append({'type': 'EXIT_SCORE', 'pnl': profit})
                active_position = None
            elif abs(pnl_points) > 3 * active_position['atr']: # Target/Stop ATR
                profit = pnl_points * 100 * 0.1
                balance += profit
                active_position = None

        # 2. Check Launch (Ignition V5.4.2)
        if audit['launch'] and not active_position:
            active_position = {
                'entry': current_price,
                'dir': audit['direction'],
                'atr': atr
            }
            trade_log.append({'ts': df.iloc[i]['time'], 'type': 'LAUNCH', 'dir': audit['direction'], 'price': current_price})

        # Coleta de Métricas para Auditoria
        results.append({
            'TS': df.iloc[i]['time'],
            'PRICE': current_price,
            'SCORE': audit['score'],
            'REGIME': audit['regime'],
            'LAUNCH': int(audit['launch']),
            'HFD': audit['layers']['L0']['hfd'],
            'L2_ZVOL': audit['layers']['L2']['z_vol_log'],
            'L3_STR': audit['layers']['L3']['strength'],
            'BALANCE': balance
        })
        
    end_time = time.time()
    res_df = pd.DataFrame(results)
    
    # Exportação de Evidência Científica
    audit_dir = r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA"
    if not os.path.exists(audit_dir): os.makedirs(audit_dir)
    output_path = os.path.join(audit_dir, "FULL_HISTORICAL_AUDIT_V542.csv")
    res_df.to_csv(output_path, index=False)
    
    # Cálculo das Métricas de Performance Final
    total_trades = len(trade_log) // 2
    profit_trades = [t['pnl'] for t in trade_log if 'pnl' in t and t['pnl'] > 0]
    loss_trades = [t['pnl'] for t in trade_log if 'pnl' in t and t['pnl'] < 0]
    
    win_rate = (len(profit_trades) / len(profit_trades + loss_trades)) * 100 if (profit_trades + loss_trades) else 0
    profit_factor = sum(profit_trades) / abs(sum(loss_trades)) if loss_trades else float('inf')
    
    print("\n" + "="*80)
    print("📋 RELATÓRIO DE AUDITORIA HISTÓRICA COMPLETA — OMEGA V5.3.2")
    print("="*80)
    print(f"⏱ Tempo de Processamento: {end_time - start_time:.2f}s")
    print(f"📊 Amostragem: {len(res_df)} barras H4")
    print(f"📈 Performance Simulada (Base $10k): ${balance:,.2f}")
    print(f"🚀 Total de Ignições (Triggers): {res_df['LAUNCH'].sum()}")
    print(f"🎯 Win Rate (Simulado): {win_rate:.2f}%")
    print(f"💎 Profit Factor: {profit_factor:.2f}")
    print(f"🔬 Regime Dominante: {res_df['REGIME'].mode()[0]}")
    print(f"📄 Arquivo de Auditoria Salvo: {output_path}")
    print("="*80)

if __name__ == "__main__":
    run_full_audit()
